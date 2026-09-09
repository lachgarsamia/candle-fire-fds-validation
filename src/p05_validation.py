"""p05_validation.py -- numbers + figures for MESH_STUDY_FINDINGS.md and
VALIDATION_FINDINGS.md.

Outputs
  data/processed/p05_three_uncertainty.csv      three-way split per thermocouple
  figures/p05_T3_convergence.png         ceiling-over-fire T3 vs mesh + vs time
  figures/p05_T1_nearfield.png           near-fire gas-T field (rake) -- why T1 fails

Inputs
  fds/runs/{coarse,medium,nest20,nest15}/*_devc.csv   (10 / 5 / 2.0 / 1.5 mm)
  data/processed/exponat_{R1,R2,R3}_timeseries.csv
"""
from __future__ import annotations
import csv
import numpy as np
import _repro  # noqa: F401
import matplotlib.pyplot as plt
from scipy.interpolate import griddata

EMBER = "#bf3d10"; COOL = "#2f5766"; INK = "#211c17"
DSTAR_CM = 1.21
R = _repro.FDS_RUNS
MESHES = [   # label, near-fire dx (cm), devc path, colour
    ("10 mm", 1.00, f"{R}/coarse/candle_coarse_dx10_devc.csv", "#9c9c9c"),
    ("5 mm",  0.50, f"{R}/medium/candle_medium_dx5_devc.csv",  "#e0a53b"),
    ("2.0 mm", 0.20, f"{R}/nest20/candle_fine_nest20_mpi_devc.csv", EMBER),
    ("1.5 mm", 0.15, f"{R}/nest15/candle_fine_nest15_mpi_devc.csv", "#7a1f6b"),
]
TCS = ["T1", "T2", "T3", "T5", "T9", "T10", "T11"]
ECOL = {"T1": "TC_01_C", "T2": "TC_02_C", "T3": "TC_03_C", "T5": "TC_05_C",
        "T9": "TC_09_C", "T10": "TC_10_C", "T11": "TC_11_C"}
TMPA = 25.0


def load_devc(path):
    r = list(csv.reader(open(path)))
    n = [x.strip() for x in r[1]]
    d = np.array([[float(x) for x in row] for row in r[2:] if len(row) == len(n)])
    return {k: d[:, i] for i, k in enumerate(n)}


def load_exp(run):
    r = list(csv.reader(open(f"{_repro.RESULT_DIR}/exponat_{run}_timeseries.csv")))
    hi = next(i for i, x in enumerate(r) if x and x[0] == "time_from_ignition_s")
    nm = r[hi]
    a = np.array([[float(x) for x in row] for row in r[hi + 1:] if len(row) == len(nm)])
    return {k: a[:, i] for i, k in enumerate(nm)}


EXP = {run: load_exp(run) for run in ("R1", "R2", "R3")}
DEV = {}
for lab, dx, path, _ in MESHES:
    try:
        DEV[lab] = load_devc(path)
    except FileNotFoundError:
        pass


def exp_band(tc, tau):
    """(mean, sample-std) rise across R1/R2/R3 at time-from-ignition tau (None=peak)."""
    vs = []
    for c in EXP.values():
        t = c["time_from_ignition_s"]; y = c[ECOL[tc]]
        base = np.nanmedian(y[t < -5])
        vs.append((np.nanmax(y[t >= 0]) if tau is None
                   else y[int(np.nanargmin(np.abs(t - tau)))]) - base)
    return float(np.mean(vs)), float(np.std(vs, ddof=1))


def fds_rise(lab, tc, tau):
    c = DEV[lab]; t = c["Time"]
    if tc not in c or t[-1] + 1 < tau:
        return None
    return float(c[tc][int(np.argmin(np.abs(t - tau)))] - TMPA)


# --------------------------------------------------------------- 1. table
def three_uncertainty(tau_match=65.0):
    """Split the sim-vs-measurement gap into experimental / numerical / model."""
    rows = []
    for tc in TCS:
        em, es = exp_band(tc, tau_match)
        fds = {lab: fds_rise(lab, tc, tau_match) for lab, *_ in MESHES if lab in DEV}
        resolved = [v for lab, v in fds.items() if lab in ("5 mm", "2.0 mm", "1.5 mm") and v is not None]
        best = fds.get("1.5 mm") or fds.get("2.0 mm")          # finest available
        num_band = (max(resolved) - min(resolved)) / 2 if len(resolved) >= 2 else float("nan")
        gap = em - best if best is not None else float("nan")
        # model discrepancy = gap not covered by (experimental sd + numerical band)
        covered = es + (num_band if np.isfinite(num_band) else 0.0)
        model = np.sign(gap) * max(abs(gap) - covered, 0.0)
        rows.append(dict(tc=tc, meas=em, meas_sd=es,
                         fds_best=best, fds_coarse=fds.get("10 mm"),
                         num_band=num_band, gap=gap, model=model))
    # write csv
    tag = "" if abs(tau_match - 65.0) < 1e-6 else f"_t{int(tau_match)}"
    p = f"{_repro.RESULT_DIR}/p05_three_uncertainty{tag}.csv"
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["thermocouple", "measured_rise_C", "experimental_sd_C",
                    "fds_finest_rise_C", "fds_10mm_rise_C",
                    "numerical_halfband_C", "sim_minus_meas_C", "residual_model_C"])
        for r in rows:
            w.writerow([r["tc"], f"{r['meas']:.1f}", f"{r['meas_sd']:.1f}",
                        "" if r["fds_best"] is None else f"{r['fds_best']:.1f}",
                        "" if r["fds_coarse"] is None else f"{r['fds_coarse']:.1f}",
                        "" if not np.isfinite(r["num_band"]) else f"{r['num_band']:.1f}",
                        "" if r["gap"] is None or not np.isfinite(r['gap']) else f"{r['gap']:.1f}",
                        f"{r['model']:.1f}"])
    print(f"\n  matched at t = {tau_match:.0f} s (finest mesh common window)")
    print(f"  {'TC':<4}{'meas±sd':>13}{'FDSfine':>9}{'FDS10mm':>9}{'±num':>7}{'sim-meas':>10}{'residual':>10}")
    for r in rows:
        fb = "  --" if r["fds_best"] is None else f"{r['fds_best']:.1f}"
        fc = "  --" if r["fds_coarse"] is None else f"{r['fds_coarse']:.1f}"
        print(f"  {r['tc']:<4}{r['meas']:>8.1f}±{r['meas_sd']:<3.0f}{fb:>9}{fc:>9}"
              f"{r['num_band']:>7.1f}{r['gap']:>10.1f}{r['model']:>10.1f}")
    return rows


# --------------------------------------------------------------- 2. fig T3
def fig_T3():
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(12.4, 5.1))

    # -- (A) time history
    for lab, dx, path, col in MESHES:
        if lab not in DEV:
            continue
        c = DEV[lab]; t = c["Time"]
        axA.plot(t, c["T3"] - TMPA, color=col, lw=2,
                 label=f"FDS {lab}  (D*/δx = {DSTAR_CM/dx:.1f})")
    # measured envelope
    tg = np.linspace(0, 150, 151)
    lo, hi, mn = [], [], []
    for tt in tg:
        m, s = [], 0
        vals = []
        for c in EXP.values():
            ti = c["time_from_ignition_s"]; y = c[ECOL["T3"]]
            base = np.nanmedian(y[ti < -5])
            vals.append(y[int(np.nanargmin(np.abs(ti - tt)))] - base)
        mn.append(np.mean(vals)); lo.append(np.min(vals)); hi.append(np.max(vals))
    axA.fill_between(tg, lo, hi, color=COOL, alpha=0.18, lw=0)
    axA.plot(tg, mn, color=COOL, lw=2.2, label="measured R1–R3 (mean, range)")
    axA.set_xlabel("time from ignition  (s)")
    axA.set_ylabel("T3 rise above ambient  (°C)")
    axA.set_title("(a)  ceiling-over-fire T3 — time history", fontsize=10.5)
    axA.set_xlim(0, 150); axA.set_ylim(-2, 34)
    axA.grid(alpha=0.3); axA.legend(fontsize=8, loc="upper left")

    # -- (B) T3 vs resolution at a matched time
    TAU = 35.0
    xs, ys, cs, labs = [], [], [], []
    for lab, dx, path, col in MESHES:
        v = fds_rise(lab, "T3", TAU)
        if v is None:
            continue
        xs.append(DSTAR_CM / dx); ys.append(v); cs.append(col); labs.append(lab)
    axB.plot(xs, ys, "-", color="0.6", lw=1, zorder=1)
    axB.scatter(xs, ys, c=cs, s=90, zorder=3, edgecolor="w")
    for x, y, l in zip(xs, ys, labs):
        axB.annotate(l, (x, y), textcoords="offset points", xytext=(7, 5), fontsize=9)
    m35, s35 = exp_band("T3", TAU)
    axB.axhspan(m35 - s35, m35 + s35, color=COOL, alpha=0.16, lw=0)
    axB.axhline(m35, color=COOL, lw=1.8, label=f"measured t={TAU:.0f}s  ({m35:.0f}±{s35:.0f} °C)")
    mp, sp = exp_band("T3", None)
    axB.axhline(mp, color=COOL, ls=":", lw=1.3, label=f"measured broad peak  ({mp:.0f}±{sp:.0f} °C)")
    axB.axvspan(10, 16, color="0.5", alpha=0.12, lw=0)
    axB.text(12.6, 32, "FDS target\nD*/δx 10–16\n(≈90 M cells)", ha="center", fontsize=8, color="0.4")
    axB.set_xscale("log")
    axB.set_xticks([1, 2, 4, 6, 8, 10, 16]); axB.set_xticklabels([1, 2, 4, 6, 8, 10, 16])
    axB.set_xlabel("near-fire resolution  D*/δx")
    axB.set_ylabel(f"T3 rise at t = {TAU:.0f} s  (°C)")
    axB.set_title("(b)  T3 vs mesh resolution — grid-sensitive, not converged", fontsize=10.5)
    axB.set_ylim(-3, 50); axB.grid(alpha=0.3, which="both")
    axB.legend(fontsize=8, loc="upper left")

    fig.suptitle("Numerical uncertainty on the ceiling-over-fire temperature (T3)", fontsize=12.5, y=1.02)
    fig.tight_layout()
    p = f"{_repro.FIG_DIR}/p05_T3_convergence.png"
    fig.savefig(p, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return p


# --------------------------------------------------------------- 3. fig T1
def fig_T1():
    """The rake is only 6x5 points -- show it as profiles, not a false-detail
    contour. Left: T rise vs x across the fire at T1's height. Right: T rise vs
    height in the wick column vs on T1's vertical line."""
    xs = [75, 90, 105, 120, 135, 150]
    zs = [20, 35, 50, 70, 100]
    runs = [("2.0 mm", f"{R}/nest20/candle_fine_nest20_mpi_devc.csv", EMBER),
            ("1.5 mm", f"{R}/nest15/candle_fine_nest15_mpi_devc.csv", "#7a1f6b")]
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(12.4, 5.2))

    for lab, path, col in runs:
        c = load_devc(path); t = c["Time"]
        # -- left: horizontal profile at z = 0.05 m (T1 height) and z = 0.02 m
        for zz, ls, mk in ((50, "-", "o"), (20, "--", "s")):
            row = [c.get(f"rk_x{x:03d}_z{zz:03d}", [np.nan])[-1] - TMPA for x in xs]
            axL.plot([x / 10 for x in xs], row, ls, color=col, marker=mk, ms=5,
                     label=f"FDS {lab},  z = {zz/10:.0f} cm")
        # -- right: vertical profile at x = 0.09 (wick) and x = 0.12 (T1 line)
        for xx, ls, mk in ((90, "-", "o"), (120, "--", "s")):
            coln = [c.get(f"rk_x{xx:03d}_z{z:03d}", [np.nan])[-1] - TMPA for z in zs]
            axR.plot(coln, [z / 10 for z in zs], ls, color=col, marker=mk, ms=5,
                     label=f"FDS {lab},  x = {xx/10:.0f} cm")

    axL.axvline(9.0, color="0.4", ls=":", lw=1); axL.text(9.0, axL.get_ylim()[1], " wick", fontsize=8, va="top")
    axL.axvline(12.0, color=COOL, lw=1.4); axL.text(12.0, 150, " T1 / T2\n line", color=COOL, fontsize=8.5)
    m65, s65 = exp_band("T1", 65.0); mp, sp = exp_band("T1", None)
    axL.errorbar(12.0, m65, yerr=s65, fmt="D", color=COOL, ms=7, capsize=4,
                 label=f"measured T1, t=65 s  ({m65:.0f}±{s65:.0f} °C)")
    axL.plot(12.0, mp, "*", color=COOL, ms=14, label=f"measured T1, peak  ({mp:.0f} °C)")
    axL.set_xlabel("x  (cm)   —  candle wick at 9.0")
    axL.set_ylabel("gas-temperature rise above ambient  (°C)")
    axL.set_title("(a)  horizontal profile across the fire\nmodelled plume decays to ambient 1–2 cm from the wick",
                  fontsize=10)
    axL.set_ylim(-5, 230); axL.grid(alpha=0.3); axL.legend(fontsize=7.6, loc="upper right")

    axR.axhline(0.5, color=COOL, ls=":", lw=1); axR.text(axR.get_xlim()[1], 0.5, "T1 ", ha="right", fontsize=8, color=COOL)
    axR.axhline(1.6, color=COOL, ls=":", lw=1); axR.text(axR.get_xlim()[1], 1.6, "T2 ", ha="right", fontsize=8, color=COOL)
    axR.set_xlabel("gas-temperature rise above ambient  (°C)")
    axR.set_ylabel("height z  (cm)")
    axR.set_title("(b)  vertical profile: wick column vs T1's vertical line\n"
                  "the hot column is real but sits at x = 9, not x = 12", fontsize=10)
    axR.grid(alpha=0.3); axR.legend(fontsize=7.6, loc="lower right")

    fig.suptitle("Why the in-flame thermocouples (T1, T2) are not reproduced at any mesh\n"
                 "the prescribed-HRR source concentrates the heat in a narrow rising column over the wick; "
                 "refining 2.0 → 1.5 mm makes it hotter and narrower, not wider",
                 fontsize=10.5, y=1.06)
    p = f"{_repro.FIG_DIR}/p05_T1_nearfield.png"
    fig.savefig(p, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return p


if __name__ == "__main__":
    three_uncertainty(65.0)
    three_uncertainty(35.0)
    print("\n", fig_T3())
    print("", fig_T1())
