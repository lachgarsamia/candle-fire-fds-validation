"""exponat_loader.py -- parser for the Exponat compartment-fire runs.

Format (verified in RECON.md Part B / section B.4):
  * plain ASCII, comma-delimited, '.'-decimal, CRLF line endings;
  * one leading comment line ``# ExpName: <name>`` then an 89-column header row;
  * ``csv.reader`` reads it directly -- no encoding or dialect tricks needed.

Only a handful of the 89 columns carry signal. Everything else is a dead /
sentinel channel (RECON B.4.2):
  * ``mass_loadcell`` is constant -999999.0 in every row of every run;
  * all 10 ``HFG_*_raw`` are constant -59.3 and all 10 calibrated ``HFG_*``
    are constant large negatives -- every heat-flux gauge is dead;
  * 33 of 40 thermocouples sit at the DAQ open-channel sentinel
    3276.6999511719;
  * ``PLC_PRG.rRTC[*]`` and the ``*_serialnr`` columns are metadata / dead.

So this loader keeps: ``date``, ``exp_time`` (the real, NON-UNIFORM time axis
in integer seconds), ``event_number`` (a 0..4 operator step function), and the
7 live thermocouples TC_01/02/03/05/09/10/11.

Three quirks handled here (RECON B.4.4):
  1. ``exp_time`` is non-uniform (~1.02 s, drifting) and uses -1 for the
     pre-roll / post-roll rows -- those rows are flagged (``in_window``) so the
     caller can drop them; analysis must use the ``exp_time`` vector, never a
     fixed sample rate.
  2. 1-7 "split-write" row pairs per file: one acquisition frame flushed as two
     rows ~1 ms apart, one carrying the sensor columns (``exp_time`` blank), the
     next carrying ``exp_time``/``event_number`` (sensors blank). These are
     coalesced back into one record.
  3. ``event_number`` is treated as a step function (forward-filled through the
     split-write blanks).

Returns an ``ExponatRun`` with plain numpy arrays -- Qt-free, matplotlib-free.
"""
from __future__ import annotations

import csv
import datetime as _dt
from dataclasses import dataclass, field

import numpy as np

# --- channel map (RECON B.4.2 / B.4.3) -------------------------------------

DEAD_TC_SENTINEL = 3276.6999511719      # DAQ open-channel value
LOADCELL_DEAD = -999999.0
HFG_RAW_DEAD = -59.3
EXP_TIME_OUT_OF_WINDOW = -1             # pre-roll / post-roll marker

LIVE_TC_COLUMNS = ["TC_01", "TC_02", "TC_03", "TC_05", "TC_09", "TC_10", "TC_11"]

# Physical positions from FDS_geometry_reference.md (authoritative). Coordinates
# (x, y=0.15 depth-centre, z) in metres; candle at x=0.09, z=0 (floor); room is
# 0.70 x 0.30 x 0.23 m. VERIFIED against the data in exponat_analysis.py --
# TC_01 sits 3 cm behind the candle at floor level, i.e. in the flame/plume, so
# the back-wall "column" is non-monotonic in height (plume low, layer high).
TC_POSITION = {
    #        group             x     z      role
    "TC_01": ("back-wall column", 0.12, 0.05, "3 cm behind candle, floor -> flame/plume"),
    "TC_02": ("back-wall column", 0.12, 0.16, "mid height"),
    "TC_03": ("back-wall column", 0.12, 0.23, "at ceiling, near fire"),
    "TC_05": ("ceiling centre",   0.35, 0.23, "mid-room ceiling"),
    "TC_09": ("doorway",          0.70, 0.015, "vent, floor level (inflow)"),
    "TC_10": ("doorway",          0.70, 0.075, "vent, mid height"),
    "TC_11": ("doorway",          0.70, 0.14, "vent, top (outflow)"),
}

BACK_WALL_COLUMN = ["TC_01", "TC_02", "TC_03"]     # z = 0.05 / 0.16 / 0.23 m
DOORWAY_COLUMN = ["TC_09", "TC_10", "TC_11"]       # z = 0.015 / 0.075 / 0.14 m
CEILING = "TC_05"

TC_THRESHOLDS_C = (60.0, 100.0, 300.0)             # devices.TC_THRESHOLDS


@dataclass
class ExponatRun:
    name: str
    source_path: str
    # time axes -----------------------------------------------------------
    exp_time: np.ndarray            # (n,) int seconds, may contain -1 rows
    wall_time: np.ndarray           # (n,) float seconds since first row's timestamp
    datetimes: list                 # (n,) datetime objects
    in_window: np.ndarray           # (n,) bool -- exp_time != -1
    event_number: np.ndarray        # (n,) int step function (forward-filled)
    # channels ----------------------------------------------------------
    tc: dict                        # {name: (n,) float array, NaN where sentinel}
    # provenance ------------------------------------------------------
    n_rows_raw: int = 0
    n_split_writes: int = 0
    n_out_of_window: int = 0
    dead_channels: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)

    # -- convenience --------------------------------------------------------
    def window(self):
        """Boolean mask of the in-experiment rows (exp_time >= 0)."""
        return self.in_window

    def t(self):
        """exp_time (s) for the in-window rows, as float, ignition NOT yet applied."""
        return self.exp_time[self.in_window].astype(float)

    def trace(self, tc_name: str):
        """One TC trace (deg C, NaN-cleaned) over the in-window rows."""
        return self.tc[tc_name][self.in_window]

    def event_transitions(self):
        """[(from_event, to_event, exp_time_s, wall_time_s), ...] over in-window rows."""
        ev = self.event_number[self.in_window]
        et = self.exp_time[self.in_window].astype(float)
        wt = self.wall_time[self.in_window]
        out = []
        for i in range(1, len(ev)):
            if ev[i] != ev[i - 1]:
                out.append((int(ev[i - 1]), int(ev[i]), float(et[i]), float(wt[i])))
        return out


def _to_float(s: str):
    s = s.strip()
    if s == "":
        return np.nan
    try:
        return float(s)
    except ValueError:
        return np.nan


def _clean_tc(raw: np.ndarray) -> np.ndarray:
    """Map the DAQ open-channel sentinel to NaN."""
    out = raw.astype(float).copy()
    out[np.isclose(out, DEAD_TC_SENTINEL, atol=1e-2)] = np.nan
    return out


def load_exponat(path: str) -> ExponatRun:
    with open(path, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))

    # drop leading '# ...' comment line(s)
    i = 0
    name = path.split("/")[-1]
    while i < len(rows) and rows[i] and rows[i][0].lstrip().startswith("#"):
        line = ",".join(rows[i])
        if "ExpName:" in line:
            name = line.split("ExpName:", 1)[1].strip()
        i += 1
    header = rows[i]
    data_rows = [r for r in rows[i + 1:] if r and len(r) == len(header)]
    n_raw = len(data_rows)

    col = {h: j for j, h in enumerate(header)}
    for required in ("date", "exp_time", "event_number", *LIVE_TC_COLUMNS):
        if required not in col:
            raise ValueError(f"{name}: expected column {required!r} not in header")

    # --- raw pull -------------------------------------------------------
    def _parse_dt(s: str):
        return _dt.datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f")

    date_raw = [r[col["date"]].strip() for r in data_rows]
    dt_raw = [_parse_dt(d) for d in date_raw]
    exp_raw = np.array([_to_float(r[col["exp_time"]]) for r in data_rows])
    ev_raw = np.array([_to_float(r[col["event_number"]]) for r in data_rows])
    tc_raw = {name_: np.array([_to_float(r[col[name_]]) for r in data_rows])
              for name_ in LIVE_TC_COLUMNS}

    # --- quirk 2: coalesce split-write row pairs ------------------------
    # At some 1 Hz boundaries the logger flushes ONE acquisition frame as two
    # rows ~1 ms apart, each carrying a DISJOINT subset of the live channels
    # (e.g. TC_01..03 on the first row, TC_05/09/10/11 + exp_time/event on the
    # second) -- so neither row is all-blank. Detect the pair by the sub-10 ms
    # timestamp gap and merge field-by-field (non-NaN wins; for exp_time /
    # event_number the populated value wins), keeping the later row's
    # timestamp. This is the only source of blank cells in the file.
    SPLIT_GAP_S = 0.010
    merge_into = {}   # later_row_idx -> earlier_row_idx it absorbs
    for k in range(1, n_raw):
        if (dt_raw[k] - dt_raw[k - 1]).total_seconds() < SPLIT_GAP_S:
            merge_into[k] = k - 1
    drop = np.zeros(n_raw, dtype=bool)
    for later, earlier in merge_into.items():
        for c in LIVE_TC_COLUMNS:
            if np.isnan(tc_raw[c][later]) and not np.isnan(tc_raw[c][earlier]):
                tc_raw[c][later] = tc_raw[c][earlier]
        if np.isnan(exp_raw[later]) and not np.isnan(exp_raw[earlier]):
            exp_raw[later] = exp_raw[earlier]
        if np.isnan(ev_raw[later]) and not np.isnan(ev_raw[earlier]):
            ev_raw[later] = ev_raw[earlier]
        drop[earlier] = True
    n_split = int(drop.sum())

    keep = ~drop
    date_raw = [d for d, k in zip(date_raw, keep) if k]
    dt_raw = [d for d, k in zip(dt_raw, keep) if k]
    exp_raw = exp_raw[keep]
    ev_raw = ev_raw[keep]
    tc_raw = {c: v[keep] for c, v in tc_raw.items()}
    n = keep.sum()

    # --- time axes -----------------------------------------------------
    datetimes = dt_raw
    t0 = datetimes[0]
    wall_time = np.array([(d - t0).total_seconds() for d in datetimes])

    exp_time = np.where(np.isnan(exp_raw), EXP_TIME_OUT_OF_WINDOW, exp_raw).astype(int)
    in_window = exp_time != EXP_TIME_OUT_OF_WINDOW

    # --- quirk 3: event_number as a forward-filled step function ------
    ev = ev_raw.copy()
    last = 0.0
    for k in range(len(ev)):
        if np.isnan(ev[k]):
            ev[k] = last
        else:
            last = ev[k]
    event_number = ev.astype(int)

    # --- channels ----------------------------------------------------
    tc = {c: _clean_tc(tc_raw[c]) for c in LIVE_TC_COLUMNS}

    dead = {
        "TC_sentinel_3276.7": [h for h in header if h.startswith("TC_") and h not in LIVE_TC_COLUMNS],
        "HFG_raw_const_-59.3": [h for h in header if h.startswith("HFG_") and h.endswith("_raw")],
        "HFG_calibrated_const_negative": [h for h in header
                                          if h.startswith("HFG_") and not h.endswith("_raw")
                                          and not h.endswith("_serialnr")],
        "mass_loadcell_const_-999999": ["mass_loadcell"],
        "loadcell_stable_const_False": ["loadcell_stable"],
        "PLC_rRTC_const_sentinel": [h for h in header if h.startswith("PLC_PRG")],
        "serialnr_metadata": [h for h in header if h.endswith("_serialnr")],
        "camera_trigger_const_False": ["camera_trigger"],
    }

    run = ExponatRun(
        name=name, source_path=path,
        exp_time=exp_time, wall_time=wall_time, datetimes=datetimes,
        in_window=in_window, event_number=event_number, tc=tc,
        n_rows_raw=n_raw, n_split_writes=int(n_split),
        n_out_of_window=int((~in_window).sum()), dead_channels=dead,
    )
    run.notes.append(
        f"{n_raw} raw data rows -> {int(n)} after coalescing {int(n_split)} split-write pair(s); "
        f"{run.n_out_of_window} row(s) out of experiment window (exp_time == -1)."
    )
    # median sample spacing (in-window)
    et = exp_time[in_window].astype(float)
    if et.size > 5:
        d = np.diff(et)
        run.notes.append(
            f"exp_time spans {et[0]:.0f}-{et[-1]:.0f} s over {et.size} samples; "
            f"step median {np.median(d):.2f} s, mean {np.mean(d):.3f} s, "
            f"{int((d > 1).sum())} skipped-second gap(s)."
        )
    return run


def load_all(paths: dict) -> dict:
    """paths: {run_key: filepath}. Returns {run_key: ExponatRun}."""
    return {k: load_exponat(p) for k, p in paths.items()}


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        r = load_exponat(p)
        print(f"\n=== {r.name} ===")
        for note in r.notes:
            print("  ", note)
        print("   event transitions (from,to,exp_time_s,wall_s):")
        for tr in r.event_transitions():
            print("     ", tr)
        for c in LIVE_TC_COLUMNS:
            tr = r.trace(c)
            print(f"   {c}: peak {np.nanmax(tr):6.1f} C   rise {np.nanmax(tr)-np.nanmin(tr):5.1f} C   "
                  f"NaN {np.isnan(tr).sum():d}")
