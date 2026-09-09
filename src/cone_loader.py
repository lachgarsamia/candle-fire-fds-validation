"""cone_loader.py -- parser for the FZJ cone-calorimeter exports.

Format (verified in RECON.md Part A):
  * encoding ISO-8859-1 (Latin-1); line terminator CRLF;
  * field delimiter ';'  ;  decimal separator ','  (German locale);
  * row 0 = channel names, row 1 = units, data from row 2;
  * columns 0-1 are NOT data -- they hold a key/value metadata block down
    the first ~70 rows;
  * duplicate channel names: 'Mass' at cols 8 AND 88, 'HRR' vs 'HRR/a', etc.
    -> this loader addresses every channel by an explicit column index, never
    by name lookup;
  * dead sentinels: 'Infinity' / '-Infinity' tokens (col 73 mostly), the
    constant 999998 placeholder (TEext2..15), empty cells -> all mapped to NaN
    and counted.

Returns a ConeRun with a ``channels`` dict {canonical_name: np.ndarray} -- the
same shape as FireScope's ``summary_stats.read_hrr_table`` return -- plus the
parsed ``meta`` dict, the ``time`` vector, and provenance.

SETTLED (PROJECT_STATE / Prompt 01 REVISED):
  * these are FREE-BURNING candle tests; metadata 'Heat flux 75' and
    'E 13,10' are template defaults -- never surfaced by this loader;
  * the physical balance is column 8 (~1600 g gross on the 3-candle runs, or a
    near-zero tared reading on some single-candle runs). Column 88 'Mass' is a
    non-physical derived channel and is NOT loaded.
  * mass is used only in DELTA form from a reference time (helper ``mass_delta``)
    -- absolute magnitude comes from the manual weigh table, not this file.
"""
from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass, field

import numpy as np

# --- explicit column map (RECON Part A, section A.2) ----------------------
# canonical_name -> (column_index, unit)
CHANNELS = {
    "time_s":              (2,  "s"),
    "O2_pct":              (3,  "%"),
    "CO2_pct":             (4,  "%"),
    "CO_pct":              (5,  "%"),
    "Pdiff_Pa":            (6,  "Pa"),
    "mass_balance_g":      (8,  "g"),      # THE physical balance (not col 88)
    "HFM_kW_m2":           (12, "kW/m2"),  # heat-flux meter -> ~0 (free burning)
    "TC_cone1_C":          (19, "degC"),
    "TC_cone2_C":          (20, "degC"),
    "TC_cone3_C":          (21, "degC"),
    "HRR_per_area_kW_m2":  (67, "kW/m2"),  # = HRR_kW / specimen area
    "EHC_MJ_kg":           (68, "MJ/kg"),
    "MLR_g_s":             (70, "g/s"),    # RECON: garbage (+-900 g/s) -- see note
    "THR_per_area_MJ_m2":  (74, "MJ/m2"),
    "MFR_g_s":             (75, "g/s"),    # duct mass-flow rate
    "HRR_kW":              (89, "kW"),     # O2-consumption HRR, total
    "O2_shifted_pct":      (90, "%"),
    "phi":                 (93, ""),
}

# metadata keys we care about (verbatim from cols 0-1)
META_KEYS = [
    "Standard used", "Date of test", "Time of test",
    "Sampling interval (s)", "Nominal duct flow rate (l/s)",
    "Sample description", "Material name/ID", "Specimen number",
    "Initial mass (g)", "Thickness (mm)", "Surface area (cm²)",
    "Test start time (s)", "Time to ignition (s)", "Time to flameout (s)",
    "End of test criteria", "User EOT time (s)",
    "Laboratory name", "Operator", "Filename",
    "Ambient temperature (°C)", "Barometric pressure (Pa)",
    "Relative hunidity (%)",
    # deliberately NOT surfaced as physical: "Heat flux (kW/m²)", "E (MJ/kg)"
]

INF_TOKENS = {"infinity", "-infinity", "inf", "-inf", "nan"}
PLACEHOLDER = 999998.0


def _to_float(s: str):
    s = s.strip()
    if s == "":
        return math.nan, "blank"
    low = s.lower().replace(",", ".")
    if low in INF_TOKENS:
        return math.nan, "inf"
    try:
        v = float(s.replace(",", "."))
    except ValueError:
        return math.nan, "unparsable"
    if abs(v - PLACEHOLDER) < 1e-3:
        return math.nan, "placeholder"
    return v, "ok"


@dataclass
class ConeRun:
    key: str                      # (config, repeat) key, e.g. "1cand_R3"
    config: int                   # 1 or 3 candles (set by caller from weigh table)
    source_path: str
    meta: dict
    time: np.ndarray              # (n,) seconds, the col-2 axis
    channels: dict                # {canonical_name: (n,) float array, NaN-cleaned}
    units: dict
    n_rows: int = 0
    nan_counts: dict = field(default_factory=dict)   # {name: {"blank":k,"inf":k,...}}
    notes: list = field(default_factory=list)

    # -- helpers --------------------------------------------------------
    def area_m2(self):
        a = self.meta.get("Surface area (cm²)")
        try:
            return float(str(a).replace(",", ".")) * 1e-4
        except (TypeError, ValueError):
            return None

    def idx_at(self, t_s):
        return int(np.nanargmin(np.abs(self.time - t_s)))

    def mass_delta(self, t_ref_s):
        """Balance reading minus its value at t_ref_s (g). Sign: positive =
        mass lost since t_ref. Absolute magnitude is NOT trusted -- use the
        manual weigh table -- but the shape/trend is (RECON A.3)."""
        m = self.channels["mass_balance_g"]
        ref = m[self.idx_at(t_ref_s)]
        return ref - m

    def meta_timeline(self):
        def g(k):
            v = self.meta.get(k, "")
            try:
                return float(str(v).replace(",", "."))
            except ValueError:
                return None
        return {
            "test_start_s": g("Test start time (s)"),
            "ignition_s": g("Time to ignition (s)"),
            "flameout_s": g("Time to flameout (s)"),
            "eot_s": g("User EOT time (s)"),
        }


def load_cone(path: str, key: str = "", config: int = 0) -> ConeRun:
    raw = open(path, "rb").read().decode("iso-8859-1")
    text = raw.replace("\r\n", "\n")
    rows = list(csv.reader(io.StringIO(text), delimiter=";"))
    if len(rows) < 3:
        raise ValueError(f"{path}: fewer than 3 rows")
    names, units_row = rows[0], rows[1]
    data = rows[2:]
    # keep only well-formed data rows (>= as many fields as the widest channel)
    max_idx = max(i for i, _ in CHANNELS.values())
    data = [r for r in data if len(r) > max_idx]
    n = len(data)

    # --- metadata block (cols 0-1) -----------------------------------
    meta = {}
    for r in rows[2:80]:
        if len(r) >= 2 and r[0].strip():
            k = r[0].strip()
            if k in META_KEYS:
                meta[k] = r[1].strip()

    # --- channels by explicit index --------------------------------
    channels, units, nan_counts = {}, {}, {}
    for name, (ci, unit) in CHANNELS.items():
        col = np.empty(n)
        counts = {"blank": 0, "inf": 0, "placeholder": 0, "unparsable": 0}
        for k in range(n):
            v, tag = _to_float(data[k][ci])
            col[k] = v
            if tag != "ok":
                counts[tag] += 1
        channels[name] = col
        units[name] = unit
        nan_counts[name] = {kk: vv for kk, vv in counts.items() if vv}

    run = ConeRun(
        key=key or path.split("/")[-1], config=config, source_path=path,
        meta=meta, time=channels["time_s"], channels=channels, units=units,
        n_rows=n, nan_counts=nan_counts,
    )

    # provenance notes
    dt = np.diff(channels["time_s"])
    run.notes.append(
        f"{n} data rows; time {channels['time_s'][0]:.0f}-{channels['time_s'][-1]:.0f} s, "
        f"median step {np.nanmedian(dt):.2f} s"
    )
    m = channels["mass_balance_g"]
    mmin, mmax = np.nanmin(m), np.nanmax(m)
    kind = ("gross balance (sample+holder+pan)" if mmax > 500
            else "tared (near-zero) balance reading")
    run.notes.append(f"mass_balance_g range [{mmin:.2f}, {mmax:.2f}] g -> {kind}")
    if any(nan_counts.get("HRR_kW", {}).values()):
        run.notes.append(f"HRR_kW NaNs: {nan_counts['HRR_kW']}")
    bad_mlr = np.nanmin(channels["MLR_g_s"]), np.nanmax(channels["MLR_g_s"])
    if bad_mlr[0] < -50 or bad_mlr[1] > 50:
        run.notes.append(
            f"MLR_g_s spans [{bad_mlr[0]:.0f}, {bad_mlr[1]:.0f}] g/s -- differentiated-"
            f"balance garbage (RECON A.2); NOT used for MLR, kept for record only")
    return run


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        r = load_cone(p)
        print(f"\n=== {p.split('/')[-1]} ===")
        for k in ("Sample description", "Specimen number", "Initial mass (g)",
                  "Surface area (cm²)", "Time to ignition (s)", "Time to flameout (s)"):
            print(f"   {k}: {r.meta.get(k)!r}")
        for note in r.notes:
            print("  ", note)
        tl = r.meta_timeline()
        print("   timeline:", tl)
        o2 = r.channels["O2_pct"]
        print(f"   O2 %: {np.nanmin(o2):.4f} .. {np.nanmax(o2):.4f}  (depletion {np.nanmax(o2)-np.nanmin(o2):.4f})")
