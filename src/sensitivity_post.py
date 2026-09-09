"""sensitivity_post.py -- M3 (P1-P3) post-processing.  Ready-when-results-land.

Turns the sweep into (a) a per-sensor uncertainty band from each source/wall knob
and (b) an itemised replacement for the lump "model discrepancy" column of
VALIDATION_FINDINGS.md, plus (c) the T3 resolution-vs-wall decomposition that P05
could only bound.

Inputs (drop returned cluster CSVs here, one dir per chid or flat):
  fds/runs/sweep/<chid>[/<chid>]_devc.csv   chid in:
     s0_base_dx5 s1_hrr15 s2_hrr21 s3_rad20 s4_rad35 s5_wallins s6_walladi
     m2_base_nest20_450
  already on disk (P04):
     fds/runs/nest20/candle_fine_nest20_mpi_devc.csv   (2 mm, 150 s)

Outputs:
  data/processed/sensitivity_bands.csv
  data/processed/sensitivity_tables.md   (paste-ready)
  console summary
"""
from __future__ import annotations
import csv
import os
import numpy as np
import _repro  # noqa: F401
from p05_validation import load_devc, exp_band, TCS, TMPA

RUNS_DIR = os.environ.get("SWEEP_RUNS_DIR", os.path.join(_repro.FDS_RUNS, "sweep"))
N20_150 = os.path.join(_repro.FDS_RUNS, "nest20", "candle_fine_nest20_mpi_devc.csv")

SWEEP = {   # key: (chid, hrr_W, rad_fraction, wall)
    "s0": ("s0_base_dx5",         18, 0.25, "exposed"),
    "s1": ("s1_hrr15",            15, 0.25, "exposed"),
    "s2": ("s2_hrr21",            21, 0.25, "exposed"),
    "s3": ("s3_rad20",            18, 0.20, "exposed"),
    "s4": ("s4_rad35",            18, 0.35, "exposed"),
    "s5": ("s5_wallins",          18, 0.25, "insulated"),
    "s6": ("s6_walladi",          18, 0.25, "adiabatic"),
    "m2": ("m2_base_nest20_450",  18, 0.25, "exposed"),
}
HRR_BAND_W = 3.0                 # +-3 W  ==  the +-15-20% cone source band about 18 W
TIMES = (150.0, 250.0, 450.0)


def _load(chid):
    for p in (os.path.join(RUNS_DIR, chid, f"{chid}_devc.csv"),
              os.path.join(RUNS_DIR, f"{chid}_devc.csv")):
        if os.path.exists(p):
            return load_devc(p)
    return None


def rise(dev, tc, tau):
    if dev is None or tc not in dev:
        return None
    t = dev["Time"]
    if t[-1] + 1.0 < tau:
        return None
    return float(dev[tc][int(np.argmin(np.abs(t - tau)))] - TMPA)


def hrr_slope(D, tc, tau):
    """(slope degC/W, band = |slope|*3W, nonlinearity degC) from s1/s0/s2, or Nones."""
    pts = [(SWEEP[k][1], rise(D[k], tc, tau)) for k in ("s1", "s0", "s2")]
    pts = [(x, y) for x, y in pts if y is not None]
    if len(pts) < 2:
        return None, None, None
    x, y = np.array(pts, float).T
    a1 = np.polyfit(x, y, 1)
    nl = 0.0
    if len(pts) == 3:
        a2 = np.polyfit(x, y, 2)
        nl = abs(np.polyval(a2, 18.0) - np.polyval(a1, 18.0))
    return a1[0], abs(a1[0]) * HRR_BAND_W, nl


def half_range(D, tc, tau, keys):
    vs = [rise(D[k], tc, tau) for k in keys]
    vs = [v for v in vs if v is not None]
    return (max(vs) - min(vs)) / 2 if len(vs) >= 2 else None


def main():
    D = {k: _load(cid) for k, (cid, *_ ) in SWEEP.items()}
    D["n20_150"] = load_devc(N20_150) if os.path.exists(N20_150) else None
    have = [SWEEP[k][0] for k in SWEEP if D[k] is not None]
    miss = [SWEEP[k][0] for k in SWEEP if D[k] is None]
    print(f"loaded : {have or '(none yet)'}")
    if miss:
        print(f"missing: {miss}  -> run + copy to fds/runs/sweep/")
    if D["s0"] is None:
        print("\nno s0_base_dx5 yet; nothing to compute. Re-run when the sweep lands.")
        return

    md = ["# Sensitivity tables (auto -- sensitivity_post.py)\n"]

    # ---------- 1. per-sensor knob bands ----------
    md.append("## 1. Per-sensor uncertainty from each source/wall knob\n")
    md.append("Rise above ambient (°C). `base` = s0 (5 mm, 18 W, χr 0.25, PMMA-exposed). "
              "`±HRR` = |dT/dHRR|·3 W. `±rad` = half-range over χr 0.20–0.35. "
              "`wall→ins/adi` = Δ from exposed to insulated / adiabatic backing.\n")
    hdr = f"| TC | t (s) | meas | base | ±HRR | ±rad | wall→ins | wall→adi |"
    md += [hdr, "|----|------|------|------|------|------|----------|----------|"]
    band_rows = []
    for tc in TCS:
        for tau in TIMES:
            meas = exp_band(tc, None if tau >= 400 else tau)[0]
            base = rise(D["s0"], tc, tau)
            _, hb, nl = hrr_slope(D, tc, tau)
            rb = half_range(D, tc, tau, ("s3", "s0", "s4"))
            wi = (rise(D["s5"], tc, tau) - base) if (D["s5"] and base is not None
                                                    and rise(D["s5"], tc, tau) is not None) else None
            wa = (rise(D["s6"], tc, tau) - base) if (D["s6"] and base is not None
                                                    and rise(D["s6"], tc, tau) is not None) else None
            f = lambda v: "--" if v is None else f"{v:+.1f}" if isinstance(v, float) and abs(v) < 100 else f"{v:.1f}"
            g = lambda v: "--" if v is None else f"{v:.1f}"
            md.append(f"| {tc} | {int(tau)} | {meas:.1f} | {g(base)} | {g(hb)} | {g(rb)} | {f(wi)} | {f(wa)} |")
            band_rows.append([tc, int(tau), meas, base, hb, rb, wi, wa, nl])
    md.append("")

    # ---------- 2. itemised three-uncertainty (t matched to P05, 150 s) ----------
    md.append("## 2. Itemised model discrepancy at t = 150 s "
              "(replaces the lump 'residual' in VALIDATION_FINDINGS §2)\n")
    md += ["| TC | meas–base | ±HRR | ±rad | wall (exp→ins→adi) | residual after knobs |",
           "|----|-----------|------|------|--------------------|----------------------|"]
    for tc in TCS:
        base = rise(D["s0"], tc, 150.0)
        if base is None:
            continue
        meas = exp_band(tc, 150.0)[0]
        _, hb, _ = hrr_slope(D, tc, 150.0)
        rb = half_range(D, tc, 150.0, ("s3", "s0", "s4"))
        wi = rise(D["s5"], tc, 150.0); wa = rise(D["s6"], tc, 150.0)
        wtxt = f"{base:.1f}→{wi:.1f}→{wa:.1f}" if (wi is not None and wa is not None) else "--"
        # residual = gap not covered by (HRR band + rad band + best wall move toward meas)
        gap = meas - base
        wall_move = 0.0
        for w in (wi, wa):
            if w is not None and np.sign(w - base) == np.sign(gap):
                wall_move = max(wall_move, abs(w - base))
        covered = (hb or 0) + (rb or 0) + wall_move
        resid = np.sign(gap) * max(abs(gap) - covered, 0.0)
        md.append(f"| {tc} | {gap:+.1f} | {(hb or 0):.1f} | {(rb or 0):.1f} | {wtxt} | {resid:+.1f} |")
    md.append("")

    # ---------- 3. T3 resolution vs wall decomposition ----------
    md.append("## 3. T3 — resolution vs wall vs run-length (the P05 hedge, resolved)\n")
    md.append("| source | T3 @150 s | T3 @450 s | note |")
    md.append("|--------|-----------|-----------|------|")
    def r3(dev, tau):
        v = rise(dev, "T3", tau); return "--" if v is None else f"{v:+.1f}"
    md.append(f"| measured (R1–R3) | {exp_band('T3',150)[0]:+.1f} | {exp_band('T3',None)[0]:+.1f} (peak) | broad peak ~300–450 s |")
    md.append(f"| P04 nest20 (2 mm, 150 s) | {r3(D['n20_150'],150)} | -- | prior baseline |")
    md.append(f"| m2_base_nest20_450 (2 mm) | {r3(D['m2'],150)} | {r3(D['m2'],450)} | **does T3 climb 150→450 s?** |")
    md.append(f"| s0 (5 mm, exposed) | {r3(D['s0'],150)} | {r3(D['s0'],450)} | coarser mesh |")
    md.append(f"| s5 (5 mm, insulated) | {r3(D['s5'],150)} | {r3(D['s5'],450)} | no loss to lab |")
    md.append(f"| s6 (5 mm, adiabatic) | {r3(D['s6'],150)} | {r3(D['s6'],450)} | no wall thermal mass (upper bound) |")
    md.append("")
    m2_150, m2_450 = rise(D["m2"], "T3", 150.0), rise(D["m2"], "T3", 450.0)
    if m2_150 is not None and m2_450 is not None:
        climb = m2_450 - m2_150
        md.append(f"**Run-length effect (2 mm): T3 moves {climb:+.1f} °C from 150 → 450 s.** "
                  + ("Confirms the wall-thermal-mass explanation." if climb > 5
                     else "Does NOT support run-length as the main cause — revisit the P05 wording."))
    if D["s0"] and D["s6"]:
        for tau in (150.0, 450.0):
            a, b = rise(D["s0"], "T3", tau), rise(D["s6"], "T3", tau)
            if a is not None and b is not None:
                md.append(f"- wall BC span at {int(tau)} s (5 mm): exposed {a:+.1f} → adiabatic {b:+.1f}  (Δ {b-a:+.1f} °C)")
    md.append("")

    # ---------- write ----------
    mdp = os.path.join(_repro.RESULT_DIR, "sensitivity_tables.md")
    open(mdp, "w").write("\n".join(md))
    csvp = os.path.join(_repro.RESULT_DIR, "sensitivity_bands.csv")
    with open(csvp, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tc", "time_s", "measured_C", "base_s0_C", "hrr_band_pm3W_C",
                    "rad_band_halfrange_C", "wall_ins_delta_C", "wall_adi_delta_C", "hrr_nonlinearity_C"])
        for r in band_rows:
            w.writerow([r[0], r[1]] + [("" if v is None else f"{v:.2f}") for v in r[2:]])
    print(f"wrote {mdp}\nwrote {csvp}\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
