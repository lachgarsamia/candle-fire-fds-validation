"""fds_post.py -- post-process the candle-compartment FDS runs (P03 baseline
comparison + P04 mesh study).

Reads each run's FDS <chid>_devc.csv and <chid>_hrr.csv, aligns the model to the
experiment (model t=0 <-> Exponat R1 inferred ignition), and produces:
  * per-run: modelled TCs (bead + gas) vs measured R1, same metrics as P02;
  * a "did the plume sustain?" check (HRR realized vs prescribed; T1 response);
  * cross-mesh comparison table + convergence assessment (Richardson/GCI, or an
    explicit non-convergence finding).

Numerical uncertainty (mesh) is reported as an explicit +- band, per P04.
It bounds discretization error only -- NOT physical correctness (that is P05).
"""
from __future__ import annotations
import csv
import glob
import json
import os

import numpy as np
import _repro  # noqa: F401
import matplotlib.pyplot as plt

TCS = ["T1", "T2", "T3", "T5", "T9", "T10", "T11"]
# FDS probe name -> column name in data/processed/exponat_R1_timeseries.csv
EXP_COL = {"T1": "TC_01_C", "T2": "TC_02_C", "T3": "TC_03_C", "T5": "TC_05_C",
           "T9": "TC_09_C", "T10": "TC_10_C", "T11": "TC_11_C"}
TC_Z = {"T1": 0.05, "T2": 0.16, "T3": 0.225, "T5": 0.225, "T9": 0.015, "T10": 0.075, "T11": 0.14}
HRR_PRESCRIBED_W = 18.0
RUNS_DIR = _repro.FDS_RUNS

# experimental targets (EXPONAT_FINDINGS.md, R1, ignition-aligned) --------
EXP_R1 = {
    "T1": dict(base=25.2, peak=136.6, rise=111.4, t60=37, t100=142, t2peak=463),
    "T2": dict(base=24.9, peak=51.4, rise=26.5),
    "T3": dict(base=25.05, peak=64.0, rise=38.9, t60=212),
    "T5": dict(base=25.1, peak=29.3, rise=4.2),
    "T9": dict(base=25.0, peak=25.2, rise=0.2),
    "T10": dict(base=24.9, peak=25.8, rise=0.9),
    "T11": dict(base=25.2, peak=29.7, rise=4.5),
}
EXP_STRUCT = dict(col_nonmonotonic="T1>>T3>T2", dT_T3_T2_peak=32.8, dT_T3_T1=-72.6,
                  ceiling_horiz_T3_T5=36.4, doorway_T11_T9=4.6)
EXP_SCATTER = dict(plume_peak=7, layer_dT=3, doorway_dT=0.4, time_to_peak=27)


def read_devc(path):
    rows = list(csv.reader(open(path)))
    # FDS: row0 = units, row1 = names, then data
    names = [n.strip() for n in rows[1]]
    data = np.array([[float(x) for x in r] for r in rows[2:] if len(r) == len(names)])
    return {n: data[:, i] for i, n in enumerate(names)}


def read_hrr(path):
    rows = list(csv.reader(open(path)))
    names = [n.strip() for n in rows[1]]
    data = np.array([[float(x) for x in r] for r in rows[2:] if len(r) == len(names)])
    return {n: data[:, i] for i, n in enumerate(names)}


def load_run(run_dir):
    chid = os.path.basename(glob.glob(os.path.join(run_dir, "*_devc.csv"))[0])[:-len("_devc.csv")]
    d = read_devc(os.path.join(run_dir, f"{chid}_devc.csv"))
    h = {}
    hp = os.path.join(run_dir, f"{chid}_hrr.csv")
    if os.path.exists(hp):
        h = read_hrr(hp)
    t = d["Time"]
    return dict(chid=chid, dir=run_dir, t=t, devc=d, hrr=h,
               t_end_reached=float(t[-1]))


def metrics(run):
    t = run["t"]
    d = run["devc"]
    m = {"chid": run["chid"], "t_end_reached_s": round(run["t_end_reached"], 1)}

    # HRR realized vs prescribed (plume-sustained check)
    if run["hrr"] and "HRR" in run["hrr"]:
        hrr_w = run["hrr"]["HRR"] * 1000.0
        tail = run["hrr"]["Time"] > 0.6 * run["hrr"]["Time"][-1]
        m["HRR_realized_W_mean_tail"] = round(float(np.mean(hrr_w[tail])), 2)
        m["HRR_realized_frac_of_prescribed"] = round(float(np.mean(hrr_w[tail]) / HRR_PRESCRIBED_W), 3)
    elif "HRR" in d:
        hrr_w = d["HRR"] * 1000.0
        tail = t > 0.6 * t[-1]
        m["HRR_realized_W_mean_tail"] = round(float(np.mean(hrr_w[tail])), 2)
        m["HRR_realized_frac_of_prescribed"] = round(float(np.mean(hrr_w[tail]) / HRR_PRESCRIBED_W), 3)

    tail = t > (t[-1] - 40)          # last 40 s ~ quasi-plateau at 250 s
    for tc in TCS:
        for suf, lbl in [("", "bead"), ("_gas", "gas")]:
            key = tc + suf
            if key not in d:
                continue
            y = d[key]
            base = float(np.median(y[t < 15])) if (t < 15).any() else float(y[0])
            m[f"{tc}_{lbl}_base_C"] = round(base, 2)
            m[f"{tc}_{lbl}_end_C"] = round(float(np.mean(y[tail])), 1)
            m[f"{tc}_{lbl}_end_rise_C"] = round(float(np.mean(y[tail]) - base), 1)
            m[f"{tc}_{lbl}_peak_C"] = round(float(np.max(y)), 1)
            # first crossings (bead only, primary)
            if suf == "":
                for thr in (60.0, 100.0):
                    hits = np.flatnonzero(y > thr)
                    m[f"{tc}_t_over_{int(thr)}C_s"] = round(float(t[hits[0]]), 1) if hits.size else None

    # structure metrics (bead)
    def endrise(tc):
        return m.get(f"{tc}_bead_end_rise_C")
    if all(endrise(x) is not None for x in ("T1", "T2", "T3")):
        m["col_T1_T2_T3_end_rise_C"] = [endrise("T1"), endrise("T2"), endrise("T3")]
        m["col_nonmonotonic_like_exp"] = bool(endrise("T1") > endrise("T3") > endrise("T2"))
        m["dT_T3_minus_T1_C"] = round(endrise("T3") - endrise("T1"), 1)
        m["dT_T3_minus_T2_C"] = round(endrise("T3") - endrise("T2"), 1)
    if endrise("T3") is not None and endrise("T5") is not None:
        m["ceiling_horiz_T3_minus_T5_C"] = round(endrise("T3") - endrise("T5"), 1)
    if endrise("T11") is not None and endrise("T9") is not None:
        m["doorway_T11_minus_T9_C"] = round(endrise("T11") - endrise("T9"), 1)

    # box behaviour
    if "p_box" in d:
        m["p_box_end_Pa"] = round(float(np.mean(d["p_box"][tail])), 1)
    if "O2_room" in d:
        m["O2_room_end_frac"] = round(float(np.mean(d["O2_room"][tail])), 4)
        m["O2_room_depletion_pct"] = round(float((d["O2_room"][t < 15].mean() - np.mean(d["O2_room"][tail])) * 100), 4)
    return m


def gci(f_coarse, f_med, f_fine, r=2.0):
    """Grid Convergence Index (Roache) for a 3-mesh monotone sequence.
    r = refinement ratio (near-fire dx ratio). Returns dict or a reason string."""
    e21 = f_med - f_fine
    e32 = f_coarse - f_med
    if abs(e21) < 1e-9:
        return {"note": "fine and medium identical -> converged", "gci_fine_pct": 0.0}
    ratio = e32 / e21
    if ratio <= 0:
        return {"note": "NON-MONOTONIC (e32/e21 <= 0) -- GCI not defined", "e32_over_e21": round(ratio, 3)}
    p = np.log(abs(ratio)) / np.log(r)
    f_ext = f_fine + e21 / (r ** p - 1)
    gci_fine = 1.25 * abs(e21 / f_fine) / (r ** p - 1) * 100
    gci_med = 1.25 * abs(e32 / f_med) / (r ** p - 1) * 100
    return {"observed_order_p": round(float(p), 2),
            "richardson_extrap": round(float(f_ext), 2),
            "gci_fine_pct": round(float(gci_fine), 2),
            "gci_medium_pct": round(float(gci_med), 2),
            "e32_over_e21": round(float(ratio), 3)}


def plot_vs_exp(runs, exp_path):
    exp = read_devc.__wrapped__ if False else None
    # measured R1
    er = list(csv.reader(open(exp_path)))
    hdr_i = next(i for i, r in enumerate(er) if r and r[0] == "time_from_ignition_s")
    en = er[hdr_i]
    ed = np.array([[float(x) for x in r] for r in er[hdr_i + 1:] if len(r) == len(en)])
    ecol = {n: ed[:, i] for i, n in enumerate(en)}
    etau = ecol["time_from_ignition_s"]

    fig, axes = plt.subplots(2, 4, figsize=(18, 8), sharex=True)
    axes = axes.ravel()
    colors = {"candle_coarse_dx10": "#e07a5f", "candle_medium_dx5": "#3d5a80",
              "candle_fine_nested25": "#81b29a", "candle_fine_nest15_mpi": "#81b29a", "candle_fine_nest20_mpi": "#c98b3a", "candle_medium_dx5_mpi": "#3d5a80"}
    for ax, tc in zip(axes, TCS):
        ecolname = EXP_COL.get(tc, f"{tc}_C")
        if ecolname in ecol:
            ax.plot(etau, ecol[ecolname], "k-", lw=2, label="exp R1 (measured)", alpha=0.8)
        for run in runs:
            d = run["devc"]
            if tc in d:
                ax.plot(run["t"], d[tc], lw=1.4,
                        color=colors.get(run["chid"], None),
                        label=f"{run['chid'].replace('candle_','')} (bead)")
            if tc + "_gas" in d:
                ax.plot(run["t"], d[tc + "_gas"], lw=0.8, ls=":",
                        color=colors.get(run["chid"], None), alpha=0.7)
        ax.set_title(f"{tc}  (z={TC_Z[tc]} m)")
        ax.grid(alpha=0.3)
        ax.set_xlabel("time from ignition (s)")
        if tc == "T1":
            ax.legend(fontsize=7)
    axes[-1].axis("off")
    fig.suptitle("FDS candle-compartment baseline vs measured Exponat R1 "
                 "(model t=0 <-> inferred ignition; SEALED box; solid=bead, dotted=gas T)", y=1.01)
    fig.tight_layout()
    p = f"{_repro.FIG_DIR}/fds_baseline_vs_R1.png"
    fig.savefig(p, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return p


def main():
    run_dirs = sorted(d for d in glob.glob(os.path.join(RUNS_DIR, "*"))
                      if os.path.isdir(d) and glob.glob(os.path.join(d, "*_devc.csv")))
    if not run_dirs:
        print("no FDS runs with _devc.csv found under", RUNS_DIR)
        return
    runs = [load_run(d) for d in run_dirs]
    mets = [metrics(r) for r in runs]

    exp_path = f"{_repro.RESULT_DIR}/exponat_R1_timeseries.csv"
    fig = plot_vs_exp(runs, exp_path) if os.path.exists(exp_path) else None

    # cross-mesh table + GCI where we have coarse/medium/fine
    order = ["candle_coarse_dx10", "candle_medium_dx5", "candle_fine_nested25"]
    by = {m["chid"]: m for m in mets}
    conv = {}
    have = [c for c in order if c in by and by[c]["t_end_reached_s"] >= 100]
    if len(have) == 3:
        for q in ["T1_bead_end_rise_C", "T3_bead_end_rise_C", "T5_bead_end_rise_C",
                  "dT_T3_minus_T1_C", "dT_T3_minus_T2_C", "HRR_realized_frac_of_prescribed"]:
            try:
                fc, fm, ff = (by[order[0]][q], by[order[1]][q], by[order[2]][q])
                conv[q] = gci(fc, fm, ff)
            except (KeyError, TypeError):
                pass

    out = {
        "runs": mets,
        "experiment_R1_targets": EXP_R1,
        "experiment_structure": EXP_STRUCT,
        "experiment_scatter_to_beat": EXP_SCATTER,
        "convergence": conv,
        "figure": fig,
        "note": "mesh convergence bounds NUMERICAL error only; physical validity is P05.",
    }
    with open(f"{_repro.RESULT_DIR}/fds_post_digest.json", "w") as f:
        json.dump(out, f, indent=2, default=str)

    # ---- compact table: temperature RISE above ambient, model vs measured ----
    exp = {k: v["rise"] for k, v in EXP_R1.items()}
    probes = ["T1", "T2", "T3", "T5", "T9", "T10", "T11"]
    w = 22
    print(f"\n{'RISE above ambient (C)':<{w}}" + "".join(f"{p:>8}" for p in probes))
    print(f"{'measured R1':<{w}}" + "".join(f"{exp[p]:>8.1f}" for p in probes))
    for m in mets:
        row = m["chid"].replace("candle_", "")
        cells = []
        for p in probes:
            v = m.get(f"{p}_bead_end_rise_C")
            cells.append(f"{v:>8.1f}" if v is not None else f"{'-':>8}")
        tag = f"  (t={m['t_end_reached_s']:.0f}s"
        hrr = m.get("HRR_realized_frac_of_prescribed")
        if hrr and abs(hrr - 1) > 0.15:
            tag += f", HRR devc x{hrr:.1f} -- see _hrr.csv"
        tag += ")"
        print(f"{row:<{w}}" + "".join(cells) + tag)
    print(f"\nnon-monotonic column (exp: T1 >> T3 > T2): "
          + ", ".join(f"{m['chid'].split('_')[-1]}={m.get('col_nonmonotonic_like_exp')}" for m in mets))
    if conv:
        print("\n=== CONVERGENCE (numerical uncertainty only) ===")
        print(json.dumps(conv, indent=2, default=str))
    print(f"\nfull detail -> data/processed/fds_post_digest.json   figure -> {fig}")


if __name__ == "__main__":
    main()
