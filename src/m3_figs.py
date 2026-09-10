"""m3_figs.py -- M3 figures:
  figures/m3_T3_wall_bracket.png   T3(t): measured band vs PMMA(2mm/5mm) vs adiabatic
  figures/m3_tracer_fill.png       modelled fog-analogue: layer ratio + room fill vs time

Inputs: fds/runs/sweep/{s0..s6,s7_tracer,m2_base_nest20_450}/*_devc.csv
        data/processed/exponat_{R1,R2,R3}_timeseries.csv
"""
from __future__ import annotations
import csv
import numpy as np
import _repro  # noqa: F401
import matplotlib.pyplot as plt
from p05_validation import EXP, ECOL, TMPA, COOL, EMBER

SW = f"{_repro.FDS_RUNS}/sweep"


def load(p):
    r = list(csv.reader(open(p)))
    n = [x.strip() for x in r[1]]
    d = np.array([[float(x) for x in row] for row in r[2:] if len(row) == len(n)])
    return {k: d[:, i] for i, k in enumerate(n)}


def meas_T3_band(tg):
    runs = []
    for c in EXP.values():
        ti = c["time_from_ignition_s"]; y = c[ECOL["T3"]]
        base = np.nanmedian(y[ti < -5])
        runs.append(np.interp(tg, ti, y - base, left=np.nan, right=np.nan))
    a = np.vstack(runs)
    return np.nanmean(a, 0), np.nanmin(a, 0), np.nanmax(a, 0)


def fig_wall_bracket():
    tg = np.linspace(0, 430, 431)
    m, lo, hi = meas_T3_band(tg)
    fig, ax = plt.subplots(figsize=(8.4, 5.2))
    ax.fill_between(tg, lo, hi, color=COOL, alpha=0.18, lw=0)
    ax.plot(tg, m, color=COOL, lw=2.4, label="measured R1–R3 (mean, range)")

    series = [
        ("m2_base_nest20_450", "FDS 2.0 mm — PMMA walls (baseline)", EMBER, "-", 2.2),
        ("s0_base_dx5", "FDS 5 mm — PMMA, exposed backing", "#e0a53b", "-", 1.4),
        ("s5_wallins", "FDS 5 mm — PMMA, insulated backing", "#9c6b1e", "--", 1.4),
        ("s6_walladi", "FDS 5 mm — adiabatic walls (no heat sink)", "#7a1f6b", "-", 2.0),
    ]
    for chid, lab, col, ls, lw in series:
        c = load(f"{SW}/{chid}/{chid}_devc.csv")
        ax.plot(c["Time"], c["T3"] - TMPA, color=col, ls=ls, lw=lw, label=lab)

    ax.annotate("modelled PMMA walls pin T3 at ~+16 °C\n(heat sink too strong)",
                (300, 16), xytext=(210, 4), fontsize=8.5, color=EMBER,
                arrowprops=dict(arrowstyle="->", color=EMBER, lw=0.8))
    ax.annotate("no heat sink → T3 runs away\n(non-physical upper bound)",
                (360, 61), xytext=(150, 55), fontsize=8.5, color="#7a1f6b",
                arrowprops=dict(arrowstyle="->", color="#7a1f6b", lw=0.8))
    ax.set_xlabel("time from ignition  (s)")
    ax.set_ylabel("T3 rise above ambient  (°C)")
    ax.set_title("Ceiling-over-fire temperature: the residual is the wall heat-sink model\n"
                 "run length ruled out (2 mm run flat to 410 s); backing condition irrelevant (exposed ≡ insulated)",
                 fontsize=10.5)
    ax.set_xlim(0, 430); ax.set_ylim(-2, 66)
    ax.grid(alpha=0.3); ax.legend(fontsize=8.3, loc="upper left")
    fig.tight_layout()
    p = f"{_repro.FIG_DIR}/m3_T3_wall_bracket.png"
    fig.savefig(p, dpi=140); plt.close(fig)
    return p


def fig_tracer():
    c = load(f"{SW}/s7_tracer/s7_tracer_devc.csv")
    t = c["Time"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.8))

    a1.plot(t, c["tr_uppermean"] / np.clip(c["tr_lowermean"], 1e-30, None), color=EMBER, lw=2)
    a1.axhline(1.0, color="0.5", lw=1, ls=":")
    a1.axvspan(140, 200, color=COOL, alpha=0.12, lw=0)
    a1.text(170, a1.get_ylim()[1]*0.7, "fog first\nvisible in\nvideo\n(~+150 s)", ha="center", fontsize=8, color=COOL)
    a1.set_xlabel("time from ignition  (s)"); a1.set_ylabel("upper-room / lower-room tracer  (–)")
    a1.set_title("(a) stratification: starts in the ceiling layer,\nmixes to near-uniform by ~250 s", fontsize=9.5)
    a1.set_xlim(0, 350); a1.grid(alpha=0.3)

    for k, lab, col in (("tr_uppermean", "upper room", "#bf3d10"),
                        ("tr_lowermean", "lower room", "#e0a53b"),
                        ("tr_plenummean", "plenum (through doorway)", COOL)):
        a2.plot(t, c[k], color=col, lw=2, label=lab)
    a2.set_yscale("log"); a2.set_xlabel("time from ignition  (s)")
    a2.set_ylabel("mean tracer mass fraction  (–)")
    a2.set_title("(b) fill: gradual over minutes; almost nothing\nreaches the plenum (weak doorway flow)", fontsize=9.5)
    a2.set_xlim(0, 350); a2.set_ylim(1e-9, 1e-4); a2.grid(alpha=0.3, which="both"); a2.legend(fontsize=8.5)

    fig.suptitle("Modelled fog-analogue tracer (s7_tracer, passive, released at the candle cup) — "
                 "transport shape + timing only, not concentration", fontsize=10.5, y=1.02)
    fig.tight_layout()
    p = f"{_repro.FIG_DIR}/m3_tracer_fill.png"
    fig.savefig(p, dpi=140, bbox_inches="tight"); plt.close(fig)
    return p


if __name__ == "__main__":
    print(fig_wall_bracket())
    print(fig_tracer())
