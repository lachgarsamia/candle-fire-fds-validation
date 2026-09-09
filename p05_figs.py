"""p05_figs.py -- the two figures the validation write-up needs:
  figures/p05_T3_convergence.png   : ceiling-over-fire temperature vs mesh resolution
  figures/p05_T1_nearfield.png     : near-fire gas-temperature field (from the rake)
                                     showing the hot plume column and T1's position
Data: fds/runs/*/*_devc.csv  +  results/exponat_{R1,R2,R3}_timeseries.csv
"""
from __future__ import annotations
import csv
import numpy as np
import _repro  # noqa: F401
import matplotlib.pyplot as plt
from matplotlib import cm
from scipy.interpolate import griddata

C = "#bf3d10"; COOL = "#2f5766"; INK = "#1e1b17"


def load_devc(path):
    r = list(csv.reader(open(path)))
    n = [x.strip() for x in r[1]]
    d = np.array([[float(x) for x in row] for row in r[2:] if len(row) == len(n)])
    return {k: d[:, i] for i, k in enumerate(n)}


def exp_rise_band(tc_col, tau):
    """(mean, std) of the rise at time-from-ignition tau across R1/R2/R3."""
    vals = []
    for run in ("R1", "R2", "R3"):
        r = list(csv.reader(open(f"{_repro.RESULT_DIR}/exponat_{run}_timeseries.csv")))
        hi = next(i for i, x in enumerate(r) if x and x[0] == "time_from_ignition_s")
        nm = r[hi]
        arr = np.array([[float(x) for x in row] for row in r[hi + 1:] if len(row) == len(nm)])
        c = {k: arr[:, i] for i, k in enumerate(nm)}
        t = c["time_from_ignition_s"]; y = c[tc_col]
        base = np.nanmedian(y[t < -5]) if (t < -5).any() else y[0]
        if tau is None:
            vals.append(np.nanmax(y[t >= 0]) - base)
        else:
            vals.append(y[int(np.nanargmin(np.abs(t - tau)))] - base)
    return float(np.mean(vals)), float(np.std(vals, ddof=1))


# ---------------------------------------------------------------- figure 1
def fig_T3_convergence():
    DSTAR = 1.21  # cm
    meshes = [
        ("10 mm", 1.0, "fds/runs/coarse/candle_coarse_dx10_devc.csv"),
        ("5 mm", 0.5, "fds/runs/medium/candle_medium_dx5_devc.csv"),
        ("2.0 mm", 0.2, "fds/runs/nest20/candle_fine_nest20_mpi_devc.csv"),
        ("1.5 mm", 0.15, "fds/runs/nest15/candle_fine_nest15_mpi_devc.csv"),
    ]
    dsx, T3, labels, tend = [], [], [], []
    for name, dx_cm, path in meshes:
        try:
            c = load_devc(path)
        except FileNotFoundError:
            continue
        t = c["Time"]
        tt = min(65.0, t[-1])          # common window (1.5 mm only reached ~76 s)
        i = int(np.argmin(np.abs(t - tt)))
        dsx.append(DSTAR / dx_cm)
        T3.append(c["T3"][i] - 25.0)
        labels.append(name)
        tend.append(t[-1])

    exp_m, exp_s = exp_rise_band("TC_03_C", 65.0)
    exp_pk_m, exp_pk_s = exp_rise_band("TC_03_C", None)

    fig, ax = plt.subplots(figsize=(7.6, 5))
    ax.axhspan(exp_m - exp_s, exp_m + exp_s, color=COOL, alpha=0.16, lw=0)
    ax.axhline(exp_m, color=COOL, lw=1.6, label=f"measured, t = 65 s  ({exp_m:.0f} ± {exp_s:.0f} °C, R1–R3)")
    ax.axhline(exp_pk_m, color=COOL, lw=1.2, ls=":", label=f"measured, broad peak  ({exp_pk_m:.0f} ± {exp_pk_s:.0f} °C)")

    ax.plot(dsx, T3, "o-", color=C, lw=2, ms=9, zorder=5)
    for x, y, l, te in zip(dsx, T3, labels, tend):
        note = l + (f"\n(only t={te:.0f} s)" if te < 60 else "")
        ax.annotate(note, (x, y), textcoords="offset points", xytext=(8, -4 if l != "1.5 mm" else 10),
                    fontsize=9, color=INK)

    ax.axvspan(10, 16, color="0.5", alpha=0.12, lw=0)
    ax.text(12.7, ax.get_ylim()[1]*0.05, "FDS-recommended\nD*/δx  (≈ 90 M cells)",
            fontsize=8.5, ha="center", color="0.35")

    ax.set_xscale("log")
    ax.set_xticks([1, 2, 4, 6, 8, 10, 16])
    ax.set_xticklabels(["1", "2", "4", "6", "8", "10", "16"])
    ax.set_xlabel("resolution near the fire,  D* / δx   (D* = 1.21 cm)")
    ax.set_ylabel("T3 temperature rise above ambient  (°C)")
    ax.set_title("Ceiling-over-fire temperature (T3) vs mesh resolution\n"
                 "coarse plume collapses; refinement recovers it but does not reach the measurement",
                 fontsize=11)
    ax.set_ylim(-3, max(exp_pk_m + exp_pk_s + 4, 46))
    ax.grid(alpha=0.3, which="both")
    ax.legend(fontsize=8.5, loc="lower right")
    fig.tight_layout()
    p = f"{_repro.FIG_DIR}/p05_T3_convergence.png"
    fig.savefig(p, dpi=140)
    plt.close(fig)
    return p


# ---------------------------------------------------------------- figure 2
def fig_T1_nearfield(devc="fds/runs/nest20/candle_fine_nest20_mpi_devc.csv", label="2.0 mm"):
    c = load_devc(devc)
    t = c["Time"]; i = -1
    xs = [0.075, 0.090, 0.105, 0.120, 0.135, 0.150]
    zs = [0.020, 0.035, 0.050, 0.070, 0.100]
    P, V = [], []
    for x in xs:
        for z in zs:
            k = f"rk_x{int(x*1000):03d}_z{int(z*1000):03d}"
            if k in c:
                P.append((x, z)); V.append(c[k][i] - 25.0)
    # add the column probes T1 (0.12,0.05) T2 (0.12,0.16) and the candle-top point
    for k, xz in (("T1", (0.12, 0.05)), ("T2", (0.12, 0.16))):
        if k in c:
            P.append(xz); V.append(c[k][i] - 25.0)
    P = np.array(P); V = np.array(V)

    gx = np.linspace(0.06, 0.17, 160)
    gz = np.linspace(0.0, 0.20, 160)
    GX, GZ = np.meshgrid(gx, gz)
    GT = griddata(P, V, (GX, GZ), method="linear")

    fig, ax = plt.subplots(figsize=(7.4, 5.6))
    lv = [2, 5, 10, 20, 40, 80, 150, 250]
    cf = ax.contourf(GX, GZ, GT, levels=lv, cmap="inferno", extend="max")
    cs = ax.contour(GX, GZ, GT, levels=[10, 40, 100], colors="white", linewidths=.7, alpha=.6)
    ax.clabel(cs, fmt="%d°C", fontsize=7)
    cb = fig.colorbar(cf, ax=ax, pad=0.02)
    cb.set_label("gas temperature rise above ambient  (°C)")

    # candle + wick
    ax.add_patch(plt.Rectangle((0.072, 0.0), 0.036, 0.010, color="#8a8a8a", zorder=6))
    ax.plot(0.09, 0.010, marker="^", color="w", ms=7, zorder=7)
    ax.annotate("candle\nx = 0.09 m", (0.09, 0.0), xytext=(0.09, -0.028), ha="center",
                fontsize=9, color=INK, annotation_clip=False)

    # T1, T2 markers
    for k, xz in (("T1", (0.12, 0.05)), ("T2", (0.12, 0.16))):
        v = c[k][i] - 25.0
        ax.plot(*xz, "o", mfc="none", mec="w", mew=1.8, ms=11, zorder=8)
        ax.annotate(f"{k}\nFDS +{v:.1f} °C", xz, xytext=(xz[0] + 0.012, xz[1]),
                    fontsize=9.5, color="w", va="center", zorder=8)

    ax.annotate("hot plume column\nsits over the wick", (0.092, 0.13), xytext=(0.13, 0.155),
                fontsize=9, color="w",
                arrowprops=dict(arrowstyle="->", color="w", lw=1))

    ax.set_xlim(0.06, 0.17); ax.set_ylim(0, 0.19)
    ax.set_xlabel("x  (m)   — 0 = back wall,  candle at 0.09")
    ax.set_ylabel("height z  (m)")
    ax.set_aspect("equal")
    ax.set_title(f"FDS near-fire temperature field ({label} mesh, t = {t[i]:.0f} s)\n"
                 "the modelled plume is hot but only ~2 cm wide — T1 (3 cm away) stays in ambient gas\n"
                 "measured T1 rise: +111 °C", fontsize=10.5)
    fig.tight_layout()
    p = f"{_repro.FIG_DIR}/p05_T1_nearfield.png"
    fig.savefig(p, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return p


if __name__ == "__main__":
    print(fig_T3_convergence())
    print(fig_T1_nearfield())
