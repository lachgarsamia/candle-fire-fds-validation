"""fig_validation_grid.py -- the consolidated 7-thermocouple validation figure
for the report: measured R1-R3 envelope vs FDS (10 mm / 2.0 mm / 1.5 mm) for
every probe, one panel each, grouped by role.

  figures/validation_7TC_grid.png

Reuses the loaders / EXP / DEV from p05_validation.py.
"""
from __future__ import annotations
import numpy as np
import _repro  # noqa: F401
import matplotlib.pyplot as plt
from p05_validation import EXP, DEV, ECOL, TMPA, COOL

# probe -> (row group label, short position)
LAYOUT = [
    ("T1",  "column",  "z 0.05 m — in flame"),
    ("T2",  "column",  "z 0.16 m — mid"),
    ("T3",  "ceiling", "over the fire (x 0.12)"),
    ("T5",  "ceiling", "mid-room (x 0.35)"),
    ("T9",  "doorway", "floor (inflow)"),
    ("T10", "doorway", "mid"),
    ("T11", "doorway", "top (outflow)"),
]
FDS_SHOW = [("10 mm", "#9c9c9c"), ("2.0 mm", "#bf3d10"), ("1.5 mm", "#7a1f6b")]
TMAX = 250.0


def meas_envelope(tc, tgrid):
    runs = []
    for c in EXP.values():
        ti = c["time_from_ignition_s"]; y = c[ECOL[tc]]
        base = np.nanmedian(y[ti < -5])
        runs.append(np.interp(tgrid, ti, y - base, left=np.nan, right=np.nan))
    a = np.vstack(runs)
    return np.nanmean(a, 0), np.nanmin(a, 0), np.nanmax(a, 0)


def main():
    tg = np.linspace(0, TMAX, 501)
    fig, axes = plt.subplots(2, 4, figsize=(15, 7.2), sharex=True)
    axes = axes.ravel()

    for ax, (tc, grp, pos) in zip(axes, LAYOUT):
        m, lo, hi = meas_envelope(tc, tg)
        ax.fill_between(tg, lo, hi, color=COOL, alpha=0.18, lw=0)
        ax.plot(tg, m, color=COOL, lw=2.2, label="measured R1–R3", zorder=5)
        for lab, col in FDS_SHOW:
            if lab not in DEV:
                continue
            c = DEV[lab]
            ax.plot(c["Time"], c[tc] - TMPA, color=col, lw=1.7, label=f"FDS {lab}")
        ax.set_title(f"{tc} · {grp} · {pos}", fontsize=9.5)
        ax.grid(alpha=0.3)
        ax.margins(x=0)
        peak = np.nanmax(hi)
        ax.set_ylim(min(-2, np.nanmin(lo) - 2), max(6, peak * 1.15))
        if tc in ("T1", "T2"):   # FDS lines pinned to the axis floor -- say so
            fmax = max((DEV[l][tc].max() - TMPA) for l, _ in FDS_SHOW if l in DEV)
            ax.annotate(f"all FDS meshes ≤ +{fmax:.1f} °C", (0.5, 0.06), xycoords="axes fraction",
                        ha="center", fontsize=8.5, color="#7a1f6b",
                        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#7a1f6b", lw=0.7))

    # legend / notes panel
    lp = axes[7]; lp.axis("off")
    h, l = axes[0].get_legend_handles_labels()
    lp.legend(h, l, loc="upper left", fontsize=10, frameon=False)
    lp.text(0.0, 0.42,
            "Rise above ambient (25 °C) vs time from ignition.\n"
            "Measured band = min–max of R1/R2/R3.\n"
            "FDS 10 mm & 2.0 mm to 150 s; 1.5 mm to 65 s.\n\n"
            "T1/T2: structural limit (prescribed-HRR plume,\n"
            "no reaction zone) — see VALIDATION_FINDINGS §3.\n"
            "T3: agrees at matched time; measured keeps\n"
            "climbing (wall heat storage) — §4.\n"
            "T5/T9/T10/T11: within experimental uncertainty.",
            fontsize=8.7, va="top", family="monospace")

    for ax in axes[4:7]:
        ax.set_xlabel("time from ignition  (s)")
    for ax in (axes[0], axes[4]):
        ax.set_ylabel("ΔT above ambient  (°C)")

    fig.suptitle("FDS vs compartment experiment — all seven thermocouples", fontsize=13, y=0.99)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    p = f"{_repro.FIG_DIR}/validation_7TC_grid.png"
    fig.savefig(p, dpi=140)
    plt.close(fig)
    print(p)


if __name__ == "__main__":
    main()
