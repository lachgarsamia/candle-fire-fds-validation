"""report_figs.py -- the report/paper figure set that the analysis scripts don't
already produce, in the shared figstyle:

  figures/report_cone_characterization.png   Phase-1 story (source term)
  figures/report_compartment_structure.png   Phase-2 story (thermal structure)
  figures/report_study_schematic.png         geometry + 7 TCs + 3 verdict zones

Existing data only (data/processed/*, data/raw/*). No new computation.
"""
from __future__ import annotations
import csv
import json
import os
import numpy as np
import _repro  # noqa: F401
import figstyle as fs
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch

fs.apply()
CONE = json.load(open(f"{_repro.RESULT_DIR}/cone_digest.json"))
EXPO = json.load(open(f"{_repro.RESULT_DIR}/exponat_digest.json"))


def _cone_ts(key):
    rows = [r for r in csv.reader(open(f"{_repro.RESULT_DIR}/cone_{key}_timeseries.csv"))
            if r and not r[0].startswith("#")]
    n = rows[0]; a = np.array([[float(x) for x in r] for r in rows[1:] if len(r) == len(n)])
    return {c: a[:, i] for i, c in enumerate(n)}


def _expo_ts(run):
    rows = [r for r in csv.reader(open(f"{_repro.RESULT_DIR}/exponat_{run}_timeseries.csv"))
            if r and not r[0].startswith("#")]
    n = rows[0]; a = np.array([[float(x) for x in r] for r in rows[1:] if len(r) == len(n)])
    return {c: a[:, i] for i, c in enumerate(n)}


# ------------------------------------------------------------------ fig 1
def fig_cone():
    fig, ax = plt.subplots(1, 3, figsize=(13.5, 4.3))

    # (a) mass-loss linearity over the steady window
    for key, col, lab in (("1cand_R3", fs.EMBER, "1 candle (anchor)"),
                          ("3cand_R1", fs.COOL, "3 candles (÷3)")):
        run = next(r for r in CONE["runs"] if r["key"] == key)
        w = run["steady_window"]["window_s"]
        ts = _cone_ts(key)
        t, m = ts["time_s"], ts["mass_lost_since_ignition_g"]
        sel = (t >= w[0]) & (t <= w[1]) & np.isfinite(m)
        tt, mm = t[sel], m[sel]
        ncand = run["config"]
        mm = (mm - mm[0]) / ncand
        p = np.polyfit(tt, mm, 1)
        r2 = 1 - np.sum((mm - np.polyval(p, tt))**2) / np.sum((mm - mm.mean())**2)
        ax[0].plot((tt - tt[0]) / 60, mm * 1000, ".", ms=3, color=col, alpha=0.5)
        ax[0].plot((tt - tt[0]) / 60, np.polyval(p, tt) * 1000, "-", color=col, lw=1.8,
                   label=f"{lab}:  {p[0]*6e4:.0f} mg/min·candle,  r² = {r2:.4f}")
    ax[0].set_xlabel("time in steady window  (min)")
    ax[0].set_ylabel("mass lost per candle  (mg)")
    ax[0].set_title("(a)  the burn is constant-rate")
    ax[0].legend(loc="upper left")

    # (b) per-candle HRR, all six runs, with the dHc band as the error bar
    runs = CONE["runs"]
    x = np.arange(len(runs))
    hi = [r["routeC_mean_HRR"]["high_dHc42"]["HRR_per_candle_W"] for r in runs]
    lo = [r["routeC_mean_HRR"]["low_dHc36"]["HRR_per_candle_W"] for r in runs]
    mid = [r["routeC_mean_HRR"]["primary_dHc38"]["HRR_per_candle_W"] for r in runs]
    cols = [fs.EMBER if r["config"] == 1 else fs.COOL for r in runs]
    ax[1].axhspan(16, 20, color=fs.GOLD, alpha=0.18, lw=0, label="working band 18 ± 2 W")
    ax[1].axhline(18, color=fs.GOLD, lw=1.3)
    for i in x:
        ax[1].plot([i, i], [lo[i], hi[i]], color=cols[i], lw=2.5, solid_capstyle="round")
        ax[1].plot(i, mid[i], "o", color=cols[i], ms=7, mec="white", mew=1)
    ax[1].set_xticks(x)
    ax[1].set_xticklabels([r["key"].replace("cand_", "c·") for r in runs], rotation=35, ha="right", fontsize=8)
    ax[1].set_ylabel("HRR per candle  (W)")
    ax[1].set_title("(b)  per-candle HRR — mass-loss route")
    ax[1].set_ylim(12, 27)
    ax[1].legend(loc="upper right")
    ax[1].text(0.02, 0.03, "bar = ΔHc 36–42 MJ/kg · marker = 38 MJ/kg\nember = 1-candle · teal = 3-candle",
               transform=ax[1].transAxes, fontsize=7.5, va="bottom")

    # (c) O2 route vs mass-loss route -- the disqualification
    rc = np.array([r["routeC_mean_HRR"]["primary_dHc38"]["HRR_per_candle_W"] * r["config"] for r in runs])
    ra = np.array([r["routeA_O2_HRR_crosscheck"]["mean_HRR_total_W"] for r in runs])
    ax[2].plot([0.01, 300], [0.01, 300], "-", color=fs.GREY, lw=1, label="1:1 (if O₂ agreed)")
    ax[2].scatter(rc, ra, c=cols, s=60, zorder=5, edgecolor="white")
    for i, r in enumerate(runs):
        ax[2].annotate(r["key"].replace("cand_", "c·"), (rc[i], ra[i]), fontsize=7,
                       xytext=(4, 3), textcoords="offset points")
    ax[2].set_xscale("log"); ax[2].set_yscale("log")
    ax[2].set_xlim(10, 90); ax[2].set_ylim(0.01, 300)
    ax[2].set_xlabel("HRR from mass loss  (W, total)")
    ax[2].set_ylabel("HRR from O₂ consumption  (W, total)")
    ax[2].set_title("(c)  O₂-consumption HRR is unusable at this scale")
    ax[2].legend(loc="lower right")

    fig.suptitle("Phase 1 — a single tea light is a free-burning 18 ± 2 W paraffin source, "
                 "anchored on manually weighed mass loss", fontsize=12, y=1.02)
    fig.tight_layout()
    p = f"{_repro.FIG_DIR}/report_cone_characterization.png"
    fig.savefig(p); plt.close(fig)
    return p


# ------------------------------------------------------------------ fig 2
def fig_compartment():
    fig, ax = plt.subplots(1, 3, figsize=(13.5, 4.3))
    T = {r: _expo_ts(r) for r in ("R1", "R2", "R3")}
    tg = np.linspace(0, 500, 501)

    def band(col):
        A = np.vstack([np.interp(tg, T[r]["time_from_ignition_s"], T[r][col],
                                 left=np.nan, right=np.nan) for r in T])
        b = np.nanmedian(A[:, tg < 0]) if (tg < 0).any() else 25.0
        return np.nanmean(A, 0) - b, np.nanmin(A, 0) - b, np.nanmax(A, 0) - b

    # (a) back-wall column: T1 >> T3 > T2
    for col, c, lab in (("TC_01_C", fs.V_STRUCT, "T1  z = 0.05 m (in flame)"),
                        ("TC_02_C", "#5c6b73", "T2  z = 0.16 m (mid)"),
                        ("TC_03_C", fs.V_WALL, "T3  z = 0.23 m (ceiling)")):
        m, l, h = band(col)
        ax[0].fill_between(tg, l, h, color=c, alpha=0.15, lw=0)
        ax[0].plot(tg, m, color=c, lw=2, label=lab)
    ax[0].set_xlabel("time from ignition  (s)"); ax[0].set_ylabel("ΔT above ambient  (°C)")
    ax[0].set_title("(a)  back-wall column: non-monotonic (T1 > T3 > T2)")
    ax[0].legend(loc="upper left"); ax[0].set_xlim(0, 500)

    # (b) horizontal ceiling gradient: T3 (over fire) vs T5 (mid-room)
    for col, c, lab in (("TC_03_C", fs.V_WALL, "T3  ceiling over the fire (x = 0.12 m)"),
                        ("TC_05_C", fs.V_FAR, "T5  ceiling mid-room (x = 0.35 m)")):
        m, l, h = band(col)
        ax[1].fill_between(tg, l, h, color=c, alpha=0.15, lw=0)
        ax[1].plot(tg, m, color=c, lw=2, label=lab)
    ax[1].set_xlabel("time from ignition  (s)"); ax[1].set_ylabel("ΔT above ambient  (°C)")
    ax[1].set_title("(b)  the hot layer is localized over the fire  (ΔT ≈ 41 °C across 23 cm)")
    ax[1].legend(loc="upper left"); ax[1].set_xlim(0, 500)

    # (c) doorway vent profile -- peak rise vs height, R1-R3
    ps = {d["TC_09"]: d for d in []}  # placeholder
    zs = {"TC_09": 0.015, "TC_10": 0.075, "TC_11": 0.14}
    per = {r: {k: v["peak_rise_C"] for k, v in
               next(x for x in EXPO["runs"] if x["run"] == r)["per_sensor"].items()}
           for r in ("R1", "R2", "R3")}
    for r, mk in zip(("R1", "R2", "R3"), ("o", "s", "^")):
        y = [zs[k] * 100 for k in ("TC_09", "TC_10", "TC_11")]
        xv = [per[r][k] for k in ("TC_09", "TC_10", "TC_11")]
        ax[2].plot(xv, y, mk + "-", color=fs.V_FAR, ms=6, label=f"{r}")
    ax[2].axhline(2, color=fs.GREY, ls=":", lw=1)
    ax[2].text(2.6, 0.7, "neutral plane low  (z ≈ 2 cm)", fontsize=7.5, color=fs.GREY)
    ax[2].set_xlabel("peak ΔT above ambient  (°C)")
    ax[2].set_ylabel("height in the doorway  (cm)")
    ax[2].set_title("(c)  doorway vent: weak, monotonic by height")
    ax[2].legend(loc="upper left", title="run")
    ax[2].set_ylim(0, 16); ax[2].set_xlim(-0.3, 5.8)

    fig.suptitle("Phase 2 — a hot, repeatable plume; a shallow hot layer that hugs the fire; "
                 "a weak ordered doorway flow; no steady state", fontsize=12, y=1.02)
    fig.tight_layout()
    p = f"{_repro.FIG_DIR}/report_compartment_structure.png"
    fig.savefig(p); plt.close(fig)
    return p


# ------------------------------------------------------------------ fig 3
def fig_schematic():
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    # outer box + plenum + room (cross-section at y = 0.15 m)
    ax.add_patch(Rectangle((0, 0), 1.00, 0.50, fill=False, ec=fs.INK, lw=1.5))
    ax.add_patch(Rectangle((0, 0), 0.70, 0.23, fc="#f3efe8", ec=fs.INK, lw=1.3))
    ax.text(0.35, 0.36, "sealed plenum", ha="center", fontsize=8.5, style="italic", color="#7a7267")
    ax.text(0.35, 0.115, "instrumented room", ha="center", fontsize=9, color="#7a7267")
    # doorway
    ax.add_patch(Rectangle((0.695, 0.0), 0.02, 0.15, fc="white", ec=fs.INK, lw=1))
    ax.annotate("doorway\n0.05 × 0.15 m", (0.71, 0.075), xytext=(0.80, 0.10), fontsize=8,
                arrowprops=dict(arrowstyle="->", lw=0.8))
    # candle + plume hint
    ax.add_patch(Rectangle((0.078, 0), 0.024, 0.012, fc="#8a8a8a", ec=fs.INK, lw=0.6))
    ax.plot(0.09, 0.02, marker="^", ms=10, color=fs.EMBER, zorder=7)
    ax.annotate("", (0.10, 0.215), (0.093, 0.03),
                arrowprops=dict(arrowstyle="-|>", lw=2.4, color=fs.EMBER, alpha=0.35))
    ax.annotate("candle  18 W  (x = 0.09 m)", (0.09, 0.0), xytext=(0.055, -0.052),
                fontsize=8, ha="center", color=fs.EMBER,
                arrowprops=dict(arrowstyle="->", lw=0.8, color=fs.EMBER))
    # 7 TCs
    TCXY = {"T1": (0.12, 0.05), "T2": (0.12, 0.16), "T3": (0.12, 0.225),
            "T5": (0.35, 0.225), "T9": (0.70, 0.015), "T10": (0.70, 0.075), "T11": (0.70, 0.14)}
    for name, (x, z) in TCXY.items():
        ax.plot(x, z, "o", ms=10, mfc=fs.TC_ROLE[name], mec="white", mew=1.4, zorder=8)
        col_side = name in ("T1", "T2", "T3")
        dx, dy = (0.022, 0.0) if col_side else (0.014, 0.008)
        ax.text(x + dx, z + dy, name, fontsize=8.5, fontweight="bold", va="center", ha="left")

    # verdict legend box
    items = [(fs.V_FAR, "far-field ceiling + doorway (T5, T9–T11)", "VALIDATED — residual ≤ 1 °C"),
             (fs.V_WALL, "ceiling over the fire (T3)", "wall thermal-boundary model  (T3 in [+16, +60] C)"),
             (fs.V_STRUCT, "in-flame column (T1, T2)", "STRUCTURAL — prescribed-HRR LES, no reaction zone")]
    box = FancyBboxPatch((0.02, -0.235), 0.96, 0.17, boxstyle="round,pad=0.006",
                         fc="white", ec=fs.INK, lw=0.8, clip_on=False)
    ax.add_patch(box)
    for i, (c, what, verdict) in enumerate(items):
        yy = -0.09 - i * 0.052
        ax.plot(0.055, yy, "o", ms=10, mfc=c, mec="white", mew=1, clip_on=False)
        ax.text(0.085, yy, what, fontsize=8.5, va="center", fontweight="bold", clip_on=False)
        ax.text(0.55, yy, verdict, fontsize=8.5, va="center", clip_on=False)

    ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.26, 0.52)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("The 18-watt fire — geometry, seven thermocouples, and where FDS agrees with the measurement",
                 fontsize=11.5, pad=12)
    p = f"{_repro.FIG_DIR}/report_study_schematic.png"
    fig.savefig(p, facecolor="white"); plt.close(fig)
    return p


# ------------------------------------------------------------------ fig 4
def fig_repeatability():
    rows = list(csv.DictReader(open(f"{_repro.RESULT_DIR}/exponat_cross_run_summary.csv")))
    sens = [r for r in rows if r["quantity"].startswith("TC_") and "peak rise" in r["quantity"]]
    struct = [r for r in rows if r["quantity"] not in {s["quantity"] for s in sens}
              and r["quantity"] != "post-ignition record length"]

    fig, ax = plt.subplots(1, 2, figsize=(12, 4.4))

    # (a) per-sensor peak rise: R1/R2/R3 + mean, log-y, CoV annotated
    names = [s["quantity"].split()[0].replace("TC_0", "T").replace("TC_", "T") for s in sens]
    x = np.arange(len(sens))
    for j, run in enumerate(("R1", "R2", "R3")):
        ax[0].plot(x, [float(s[run]) for s in sens], "o", ms=6, color=fs.COOL, alpha=0.55,
                   label="R1 / R2 / R3" if j == 0 else None)
    for i, s in enumerate(sens):
        m, sd = float(s["mean"]), float(s["std"])
        ax[0].plot([i - .2, i + .2], [m, m], color=fs.EMBER, lw=2)
        ax[0].annotate(f"CoV {float(s['CoV_percent']):.0f}%", (i, m), textcoords="offset points",
                       xytext=(0, 9), ha="center", fontsize=7.5,
                       color=fs.V_STRUCT if float(s["CoV_percent"]) > 15 else fs.INK)
    ax[0].set_yscale("log"); ax[0].set_xticks(x); ax[0].set_xticklabels(names)
    ax[0].set_ylabel("peak ΔT above ambient  (°C)")
    ax[0].set_title("(a)  per-sensor peak rise — 3 runs, mean (ember)")
    ax[0].legend(loc="upper right")
    ax[0].text(0.02, 0.03, "T2 CoV 29 % — mid-column sensor in the flickering plume boundary\n"
               "T10 CoV 16 % is ±0.2 °C on a ~1 °C signal (DAQ floor)",
               transform=ax[0].transAxes, fontsize=7.3, va="bottom", color="#7a7267")

    # (b) structure metrics + time-to-peak, mean ± sigma
    labs = [s["quantity"].replace(" (peak)", "").replace("dT ", "ΔT ") for s in struct]
    m = [float(s["mean"]) for s in struct]; sd = [float(s["std"]) for s in struct]
    y = np.arange(len(struct))
    ax[1].barh(y, m, xerr=sd, color=fs.COOL, alpha=0.8, height=0.55,
               error_kw=dict(ecolor=fs.INK, lw=1.2, capsize=4))
    for i, s in enumerate(struct):
        ax[1].text(m[i] + sd[i] + max(m) * 0.02, i, f"{m[i]:.1f} ± {sd[i]:.1f}  (CoV {float(s['CoV_percent']):.0f}%)",
                   va="center", fontsize=8)
    ax[1].set_yticks(y); ax[1].set_yticklabels(labs, fontsize=8.5)
    ax[1].set_xlabel("value  (°C, or s for time-to-peak)")
    ax[1].set_title("(b)  structure metrics — mean ± σ across R1–R3")
    ax[1].set_xlim(0, max(m) * 1.55)

    fig.suptitle("Experimental repeatability (n = 3) — the basis for the experimental band "
                 "in the three-uncertainty split", fontsize=11.5, y=1.02)
    fig.tight_layout()
    p = f"{_repro.FIG_DIR}/report_repeatability.png"
    fig.savefig(p); plt.close(fig)
    return p


if __name__ == "__main__":
    print(fig_cone())
    print(fig_compartment())
    print(fig_schematic())
    print(fig_repeatability())
