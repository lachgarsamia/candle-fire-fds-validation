"""m4_post.py -- M4 wall-hypothesis test.

For {baseline, and each physically-motivated wall variant} report T3 AND all 7
sensors vs the measurement. A variant that fixes T3 but pushes a far-field
residual past 1 C is NOT a fix.

Variants (each a physical claim about the rig, one line each -- see WALL_HYP):
  w1_ir       cast-PMMA emissivity ~0.85 + near-IR semi-transparency
  w2_thinceil inner-room ceiling = 4 mm sheet + air gap (setup photo)
  w3_thinall  whole rig is ~4 mm sheet acrylic
  w4_contact  assembled panels -> lumped joint contact resistance (bracket)

Inputs: fds/runs/sweep/{s0_base_dx5,w1_ir,w2_thinceil,w3_thinall,w4_contact}/*_devc.csv
Output: data/processed/m4_wall_test.md  + console
"""
from __future__ import annotations
import csv
import os
import numpy as np
import _repro  # noqa: F401
from p05_validation import exp_band, TCS, TMPA

SW = os.path.join(_repro.FDS_RUNS, "sweep")
WALL_HYP = {
    "s0_base_dx5": "baseline — 10 mm opaque cast PMMA, exposed backing",
    "w1_ir":       "V1 · PMMA emissivity 0.85 (datasheet low end) + near-IR semi-transparency",
    "w2_thinceil": "V2 · inner-room ceiling = 4 mm sheet + 20 mm air gap (setup photo)",
    "w3_thinall":  "V3 · whole rig is ~4 mm sheet acrylic, not 10 mm slabs",
    "w4_contact":  "V4 · assembled panels — joint contact resistance as reduced k=0.10 (bracket)",
}
FARFIELD = ("T5", "T9", "T10", "T11")
TIMES = (150.0, 250.0, 350.0)


def load(chid):
    p = os.path.join(SW, chid, f"{chid}_devc.csv")
    if not os.path.exists(p):
        return None
    r = list(csv.reader(open(p)))
    n = [x.strip() for x in r[1]]
    d = np.array([[float(x) for x in row] for row in r[2:] if len(row) == len(n)])
    return {k: d[:, i] for i, k in enumerate(n)}


def rise(dev, tc, tau):
    if dev is None or tc not in dev:
        return None
    t = dev["Time"]
    if t[-1] + 1 < tau:
        return None
    return float(dev[tc][int(np.argmin(np.abs(t - tau)))] - TMPA)


def main():
    D = {k: load(k) for k in WALL_HYP}
    got = [k for k, v in D.items() if v is not None]
    miss = [k for k, v in D.items() if v is None]
    print("loaded :", got or "(none yet)")
    if miss:
        print("missing:", miss)
    if D["s0_base_dx5"] is None:
        print("no baseline yet — rerun when the M4 runs land"); return

    md = ["# M4 wall-hypothesis test (auto — src/m4_post.py)\n",
          "T3 and the far-field vs measurement, 5 mm runs. A variant is a **fix** only "
          "if it moves T3 toward the data **and** keeps every far-field residual ≤ 1 °C.\n"]

    # --- T3 table ---
    md.append("## T3 rise above ambient (°C)\n")
    md.append("| variant | 150 s | 250 s | 350 s | hypothesis |")
    md.append("|---|--:|--:|--:|---|")
    mt3 = {tau: exp_band("T3", None if tau >= 400 else tau)[0] for tau in TIMES}
    md.append(f"| **measured (R1–R3)** | {mt3[150]:+.0f} | {mt3[250]:+.0f} | "
              f"{mt3[350]:+.0f} (→ +43.5 peak) | — |")
    for k in WALL_HYP:
        if D[k] is None:
            continue
        vals = " | ".join(f"{rise(D[k],'T3',t):+.1f}" if rise(D[k],'T3',t) is not None else "--" for t in TIMES)
        md.append(f"| {k} | {vals} | {WALL_HYP[k]} |")
    md.append("")

    # --- far-field integrity check at 350 s ---
    md.append("## Far-field integrity (rise °C @ 350 s; residual vs measured broad peak)\n")
    md.append("| variant | " + " | ".join(FARFIELD) + " | max |resid| | verdict |")
    md.append("|---|" + "--:|" * (len(FARFIELD) + 1) + "---|")
    meas_ff = {tc: exp_band(tc, None)[0] for tc in FARFIELD}
    md.append("| **measured (peak)** | " + " | ".join(f"{meas_ff[tc]:+.1f}" for tc in FARFIELD) + " | — | — |")
    for k in WALL_HYP:
        if D[k] is None:
            continue
        row, resid = [], []
        for tc in FARFIELD:
            v = rise(D[k], tc, 350.0)
            row.append(f"{v:+.1f}" if v is not None else "--")
            if v is not None:
                resid.append(abs(v - meas_ff[tc]))
        mr = max(resid) if resid else float("nan")
        t3_350 = rise(D[k], "T3", 350.0)
        moves = t3_350 is not None and t3_350 > rise(D["s0_base_dx5"], "T3", 350.0) + 3
        verdict = ("FIX" if (moves and mr <= 1.0) else
                   "breaks far-field" if mr > 1.0 else
                   "no T3 improvement" if not moves else "—")
        md.append(f"| {k} | " + " | ".join(row) + f" | {mr:.1f} | {verdict} |")
    md.append("")

    # --- T1/T2 unchanged check ---
    md.append("## T1 / T2 (structural finding must be untouched)\n")
    md.append("| variant | T1 @350 | T2 @350 |")
    md.append("|---|--:|--:|")
    for k in WALL_HYP:
        if D[k] is None:
            continue
        md.append(f"| {k} | {rise(D[k],'T1',350):+.1f} | {rise(D[k],'T2',350):+.1f} |")

    p = os.path.join(_repro.RESULT_DIR, "m4_wall_test.md")
    open(p, "w").write("\n".join(md))
    print("\n".join(md))
    print(f"\nwrote {p}")
    fig(D)


def fig(D):
    import matplotlib.pyplot as plt
    from p05_validation import EXP, ECOL, COOL
    tg = np.linspace(0, 350, 351)
    runs = []
    for c in EXP.values():
        ti = c["time_from_ignition_s"]; y = c[ECOL["T3"]]
        b = np.nanmedian(y[ti < -5])
        runs.append(np.interp(tg, ti, y - b, left=np.nan, right=np.nan))
    a = np.vstack(runs)
    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    ax.fill_between(tg, np.nanmin(a, 0), np.nanmax(a, 0), color=COOL, alpha=0.18, lw=0)
    ax.plot(tg, np.nanmean(a, 0), color=COOL, lw=2.4, label="measured R1–R3")
    style = {"s0_base_dx5": ("#3b3b3b", "-", "baseline · 10 mm opaque PMMA"),
             "w1_ir": ("#e0a53b", "-", "V1 · emissivity 0.85 + IR semi-transp."),
             "w2_thinceil": ("#bf3d10", "-", "V2 · 4 mm ceiling + air gap (photo)"),
             "w3_thinall": ("#7a1f6b", "-", "V3 · whole rig 4 mm sheet"),
             "w4_contact": ("#2f7d4f", "--", "V4 · lumped contact resistance (bracket)")}
    for k, (col, ls, lab) in style.items():
        if D.get(k) is None:
            continue
        c = D[k]
        ax.plot(c["Time"], c["T3"] - TMPA, color=col, ls=ls, lw=1.8, label=lab)
    s6 = load("s6_walladi")
    if s6 is not None:
        ax.plot(s6["Time"], s6["T3"] - TMPA, color="0.6", ls=":", lw=1.4,
                label="adiabatic (no sink — bracket)")
    ax.set_xlabel("time from ignition (s)"); ax.set_ylabel("T3 rise above ambient (°C)")
    ax.set_title("M4 — which physically-motivated wall model matches the data?\n"
                 "(no variant tuned to a T3 target; far-field integrity checked separately)", fontsize=10)
    ax.set_xlim(0, 350); ax.set_ylim(-2, 62); ax.grid(alpha=0.3); ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    pth = os.path.join(_repro.FIG_DIR, "m4_wall_variants.png")
    fig.savefig(pth, dpi=140); plt.close(fig)
    print("wrote", pth)


if __name__ == "__main__":
    main()
