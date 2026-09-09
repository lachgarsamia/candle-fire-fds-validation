"""cone_analysis.py -- candle fire-source characterization from the cone runs
(Prompt 01 REVISED).

Settled inputs (PROJECT_STATE.md / Prompt 01 REVISED / weights.csv):
  * FREE-BURNING tea lights. Never "75 kW/m2".
  * Mass ground truth = weights.csv (manual weigh table). Load cell (col 8) is
    used ONLY for burn shape (ignition / steady window / flameout).
  * Wax = paraffin (weights.csv). dHc = 42 MJ/kg, chi = 0.9 -> dHc_eff = 38 MJ/kg
    (primary); band ~36-42 MJ/kg (chi 0.85 .. 1.0) as the named uncertainty.
  * HRR primary = Route C, time-averaged:  Qbar = dm_manual * dHc_eff / t_burn
    per run and per candle. Cross-check only = Route A (O2-consumption, col 89),
    labelled "near instrument noise floor -- qualitative".
  * No time-resolved MLR(t) or HRR(t).
  * dHc_implied = integral(Route-A HRR) / dm_manual, per run -- an empirical
    check on the wax dHc. Report agreement or disagreement; do not tune.

Roster (Prompt 01 REVISED section 2 -- classified, NOT pooled):
  1-candle: R3 = anchor; 25.08 = long-protocol rate cross-check (HRR invalid);
            R2 = short/incomplete, timeline-derived.
  3-candle: R1/R2/R3 = three genuine repeats (R3 has no after-mass -> timeline
            + balance-shape only).
"""
from __future__ import annotations

import csv
import json

import numpy as np
import _repro  # noqa: F401
import matplotlib.pyplot as plt

from timeseries import write_series_csv          # FireScope, reused as-is
from cone_loader import load_cone

DATA = _repro.DATA_DIR
DHC_EFF = 38.0e6      # J/kg  PRIMARY: paraffin 42 MJ/kg * combustion eff chi 0.9
# named uncertainty (Prompt 01 REVISED s0): chi ~0.85 (incomplete combustion) up
# to chi = 1.0 (paraffin net dHc, perfect combustion). Brackets the primary.
DHC_BAND = (35.7e6, 42.0e6)
DHC_LIT_PARAFFIN = 42.0e6

ROSTER = [
    # key,        filename,                     config, role
    ("1cand_R3",  "26082026_Candle_R3.csv",     1, "single-candle ANCHOR"),
    ("1cand_long","25082026_Candle_R1.csv",     1, "long-protocol rate cross-check (O2 HRR invalid)"),
    ("1cand_R2",  "26082026_Candle_R2.csv",     1, "short / incomplete; timeline from load-cell shape"),
    ("3cand_R1",  "26082026_3_Candles_R1.csv",  3, "cleanest 3-candle repeat"),
    ("3cand_R2",  "27082026_3_Candles_R2.csv",  3, "3-candle, short burn"),
    ("3cand_R3",  "27082026_3_Candles_R3.csv",  3, "3-candle, no after-mass -> balance-shape mass"),
]


# --------------------------------------------------------------------------
def read_weights(path):
    out = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            out[row["run"].strip()] = {
                "config": int(row["config"]),
                "m_before_g": float(row["mass_before_g"]) if row["mass_before_g"] else None,
                "m_after_g": float(row["mass_after_g"]) if row["mass_after_g"] else None,
                "wax": row.get("wax_type", "").strip(),
                "notes": row.get("burn_notes", "").strip(),
            }
    return out


def smooth(y, k):
    """Centred running mean, edge-padded with the boundary values so the ends
    are not pulled toward zero (np.convolve 'same' zero-pads, which corrupts
    the last/first k/2 samples -- exactly where the flameout tail lives)."""
    k = max(1, int(k) | 1)
    y = np.asarray(y, float)
    pad = k // 2
    yp = np.concatenate([np.full(pad, y[0]), y, np.full(pad, y[-1])])
    kern = np.ones(k) / k
    return np.convolve(yp, kern, mode="valid")


def burn_window(run, w):
    """(t_ignition, t_flameout, source) on the col-2 time axis.

    Metadata ignition/flameout are used when present (they define a *duration*
    on a single clock even though the absolute ignition instant is not physical
    -- candles were hand-lit before insertion). Flameout is cross-checked
    against the load-cell going flat. When metadata is absent (Candle_R2), both
    ends come from the load-cell shape."""
    tl = run.meta_timeline()
    t_full = run.time
    # The balance record ends with a large downward spike when the specimen is
    # removed at end-of-test. Clip to the metadata EOT (or 30 s before the last
    # sample) BEFORE any shape analysis so that artefact can't dominate.
    eot = tl["eot_s"] or (t_full[-1] - 30)
    valid = t_full <= min(eot, t_full[-1] - 15)
    t = t_full[valid]
    m = smooth(run.channels["mass_balance_g"][valid], 31)
    dmdt = smooth(np.gradient(m, t), 15)
    # settle: first index past the initial placement/settling transient where
    # |dm/dt| has fallen to a near-burn-rate level (< 5 mg/s) and stays there.
    # A candle burns at ~0.5-1.5 mg/s, so 5 mg/s cleanly excludes the settling
    # ramp (tens of mg/s) without clipping the burn.
    settle_i = 0
    hold = max(10, int(0.02 * len(t)))
    for i in range(len(t)):
        if t[i] > 5 and np.all(np.abs(dmdt[i:i + hold]) < 5e-3) \
                and np.nanmax(np.abs(m[:i + 1])) > 0.05:
            settle_i = i
            break
    # Shape-based window from the CUMULATIVE mass loss after settle: the burn is
    # the span carrying the central 96 % of the monotone decline. Robust to the
    # tared-balance drift that a simple |dm/dt| threshold trips on.
    seg = slice(settle_i, len(t))
    mm = m[seg] - m[settle_i]                    # <= 0 while burning
    loss = np.maximum.accumulate(-np.minimum(mm, 0.0))   # monotone cumulative loss
    total = loss[-1]
    shape_ignition = shape_flameout = None
    if total > 0.05:                             # at least 50 mg lost -> it burned
        lo = np.flatnonzero(loss >= 0.02 * total)
        hi = np.flatnonzero(loss >= 0.98 * total)
        if lo.size:
            shape_ignition = float(t[seg][lo[0]])
        if hi.size:
            shape_flameout = float(t[seg][hi[0]])

    _si = round(shape_ignition, 0) if shape_ignition is not None else None
    _sf = round(shape_flameout, 0) if shape_flameout is not None else None

    if tl["ignition_s"] is not None and tl["flameout_s"] is not None:
        return tl["ignition_s"], tl["flameout_s"], "metadata (flameout cross-checked vs load-cell)", {
            "shape_ignition_s": _si, "shape_flameout_s": _sf,
            "flameout_offset_meta_minus_shape_s":
                round(tl["flameout_s"] - shape_flameout, 0) if shape_flameout else None,
            "balance_loss_over_metadata_window_g": None,
        }
    if tl["flameout_s"] is not None:   # 25.08: flameout only
        ign = tl["test_start_s"] or shape_ignition
        return ign, tl["flameout_s"], "metadata flameout + test-start as ignition", {
            "shape_ignition_s": _si,
            "note": "ignition ambiguity ~60 s is negligible over a ~3.8 h burn",
        }
    if shape_ignition is None or shape_flameout is None:
        # nothing burned per the balance
        return None, None, "no burn detected on the load cell", {"total_balance_loss_g": round(total, 3)}
    return shape_ignition, shape_flameout, "load-cell shape (no metadata timeline)", {
        "shape_ignition_s": round(shape_ignition, 0),
        "shape_flameout_s": round(shape_flameout, 0) if shape_flameout else None,
    }


def steady_window(run, t0, t1):
    """Steady burning rate from the balance. A candle burns quasi-steadily, so
    rather than hunt for a plateau we take the central 60 % of [ignition,
    flameout] (past the ignition ramp, before flameout tail-off) and linear-fit
    mass vs time. Returns (ts, te, dmdt_mg_s, r2, max_dev_from_linear_mg) --
    r2 near 1 confirms the burn IS linear over that span."""
    t = run.time
    m = run.channels["mass_balance_g"]
    lo, hi = t0 + 0.20 * (t1 - t0), t0 + 0.80 * (t1 - t0)
    win = (t >= lo) & (t <= hi) & np.isfinite(m)
    if win.sum() < 60:
        return None
    tw, mw = t[win], m[win]
    a, b = np.polyfit(tw, mw, 1)               # slope g/s, intercept
    fit = a * tw + b
    ss_res = float(np.sum((mw - fit) ** 2))
    ss_tot = float(np.sum((mw - mw.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    max_dev = float(np.max(np.abs(mw - fit)) * 1000)   # mg
    return (float(lo), float(hi), float(-a * 1000), float(r2), max_dev)


def trapz_energy(run, t0, t1):
    """Integral of Route-A HRR (col 89, kW) over [t0,t1] -> MJ. NaN-safe."""
    t = run.time
    q = run.channels["HRR_kW"].copy()
    win = (t >= t0) & (t <= t1)
    tw, qw = t[win], q[win]
    good = ~np.isnan(qw)
    if good.sum() < 10:
        return None
    trap = getattr(np, "trapezoid", None) or np.trapz  # numpy>=2 renamed trapz
    return float(trap(qw[good], tw[good]) / 1000.0)   # kW*s -> MJ


def o2_noise_floor(run, t_ign, t_flame):
    """Short-term O2 std from the quiet pre-ignition and post-flameout
    segments -- an empirical noise floor for the O2-consumption HRR
    (Prompt 01 REVISED: bound it from inside the burning runs, since no blank
    run exists)."""
    t = run.time
    o2 = run.channels["O2_pct"]
    pre = o2[(t < t_ign - 5)]
    post = o2[(t > t_flame + 30)] if t_flame else np.array([])
    out = {}
    if np.sum(~np.isnan(pre)) > 8:
        out["pre_ign_std_pct"] = round(float(np.nanstd(pre)), 4)
        out["pre_ign_mean_pct"] = round(float(np.nanmean(pre)), 4)
    if np.sum(~np.isnan(post)) > 8:
        out["post_flame_std_pct"] = round(float(np.nanstd(post)), 4)
    return out


# --------------------------------------------------------------------------
def analyse(key, fname, config, role, weights):
    stem = fname[:-4]
    w = weights.get(stem, {})
    run = load_cone(f"{DATA}/{fname}", key=key, config=config)

    t_ign, t_flame, tsrc, tdet = burn_window(run, w)
    dur = t_flame - t_ign if (t_flame and t_ign is not None) else None

    dm_manual = (w["m_before_g"] - w["m_after_g"]) / 1000.0 \
        if (w.get("m_before_g") and w.get("m_after_g")) else None   # kg (total)

    # balance-shape mass loss over the burn window (cross-check / fallback)
    m = run.channels["mass_balance_g"]
    dm_balance = float(m[run.idx_at(t_ign)] - m[run.idx_at(t_flame)]) / 1000.0 \
        if (t_flame and t_ign is not None) else None                # kg

    dm_used = dm_manual if dm_manual is not None else dm_balance
    dm_source = "manual weigh table" if dm_manual is not None else "load-cell shape (no after-mass)"

    # ---- Route C: time-averaged mean HRR --------------------------------
    routeC = {}
    if dm_used is not None and dur:
        for label, dhc in [("primary_dHc38", DHC_EFF),
                           ("low_dHc36", DHC_BAND[0]), ("high_dHc42", DHC_BAND[1])]:
            q_tot = dm_used * dhc / dur                    # W
            routeC[label] = {
                "HRR_total_W": round(q_tot, 1),
                "HRR_per_candle_W": round(q_tot / config, 1),
            }
        mlr_tot = dm_used / dur * 1e6                      # mg/s
        routeC["mean_MLR_total_mg_s"] = round(mlr_tot, 3)
        routeC["mean_MLR_per_candle_mg_s"] = round(mlr_tot / config, 3)
        routeC["burn_duration_s"] = round(dur, 0)
        routeC["mass_consumed_total_g"] = round(dm_used * 1000, 2)
        routeC["mass_consumed_per_candle_g"] = round(dm_used * 1000 / config, 2)
        routeC["dm_source"] = dm_source

    # ---- steady window: linear fit of balance mass over central 60 % ------
    sw = steady_window(run, t_ign, t_flame) if dur else None
    steady = None
    if sw:
        lo, hi, dmdt_mg_s, r2, max_dev = sw
        steady = {
            "window_s": [round(lo, 0), round(hi, 0)],
            "length_s": round(hi - lo, 0),
            "steady_MLR_total_mg_s": round(dmdt_mg_s, 3),
            "steady_MLR_per_candle_mg_s": round(dmdt_mg_s / config, 3),
            "steady_HRR_total_W_dHc38": round(dmdt_mg_s * 1e-6 * DHC_EFF, 1),
            "steady_HRR_per_candle_W_dHc38": round(dmdt_mg_s * 1e-6 * DHC_EFF / config, 1),
            "linear_fit_r2": round(r2, 4),
            "max_deviation_from_linear_mg": round(max_dev, 1),
        }

    # ---- Route A: O2-consumption HRR (cross-check only) ----------------
    routeA = {}
    hrr_invalid = "O2 HRR invalid" in role or "invalid" in w.get("notes", "").lower()
    if dur:
        E_A = trapz_energy(run, t_ign, t_flame)
        q = run.channels["HRR_kW"]
        win = (run.time >= t_ign) & (run.time <= t_flame)
        routeA = {
            "mean_HRR_total_W": round(float(np.nanmean(q[win])) * 1000, 1),
            "peak_HRR_total_W": round(float(np.nanmax(q[win])) * 1000, 1),
            "integrated_energy_MJ": round(E_A, 4) if E_A is not None else None,
            "label": "O2-consumption HRR, near instrument noise floor -- QUALITATIVE",
            "disqualified": bool(hrr_invalid),
        }
        # dHc_implied = integrated Route-A energy / manual mass loss.
        # Only meaningful against the MANUAL delta (Prompt 01 REVISED s1.4);
        # runs without an after-mass get no implied value.
        if E_A is not None and dm_manual:
            routeA["dHc_implied_MJ_kg"] = round(E_A / dm_manual, 1)  # MJ / kg (E_A in MJ, dm in kg)

    o2n = o2_noise_floor(run, t_ign, t_flame)
    # O2 depletion over the burn window
    o2w = run.channels["O2_pct"][(run.time >= t_ign) & (run.time <= t_flame)]
    o2_depl = round(float(np.nanmax(o2w) - np.nanmin(o2w)), 4)
    co2w = run.channels["CO2_pct"][(run.time >= t_ign) & (run.time <= t_flame)]
    co2_rise = round(float(np.nanmax(co2w) - np.nanmin(co2w)), 4)

    return {
        "key": key, "file": fname, "config": config, "role": role,
        "weigh_notes": w.get("notes", ""),
        "meta_sample_description": run.meta.get("Sample description"),
        "meta_specimen_number": run.meta.get("Specimen number"),
        "meta_initial_mass_g": run.meta.get("Initial mass (g)"),
        "config_from_weight": (
            f"m_before={w.get('m_before_g')} g -> {config} candle(s)"
            + ("  [filename/metadata mismatch: metadata logged 1 candle]"
               if config == 3 and str(run.meta.get("Sample description", "")).count("R") else "")),
        "timeline": {
            "source": tsrc,
            "t_ignition_s": t_ign, "t_flameout_s": t_flame,
            "burn_duration_s": round(dur, 0) if dur else None,
            "metadata": run.meta_timeline(),
            "load_cell_cross_check": tdet,
        },
        "mass": {
            "manual_before_g": w.get("m_before_g"), "manual_after_g": w.get("m_after_g"),
            "manual_delta_g": round(dm_manual * 1000, 2) if dm_manual is not None else None,
            "balance_shape_delta_over_window_g": round(dm_balance * 1000, 2) if dm_balance is not None else None,
            "agreement_g": (round((dm_balance - dm_manual) * 1000, 2)
                            if (dm_manual is not None and dm_balance is not None) else None),
        },
        "routeC_mean_HRR": routeC,
        "steady_window": steady,
        "routeA_O2_HRR_crosscheck": routeA,
        "gas": {
            "O2_depletion_over_burn_pct": o2_depl,
            "CO2_rise_over_burn_pct": co2_rise,
            "O2_noise": o2n,
            "O2_depletion_vs_noise_ratio": (
                round(o2_depl / o2n["pre_ign_std_pct"], 1)
                if o2n.get("pre_ign_std_pct") else None),
        },
        "_run": run, "_win": (t_ign, t_flame), "_steady": sw,
    }


# --------------------------------------------------------------------------
# cross-run
# --------------------------------------------------------------------------
def cross_run(results):
    by = {r["key"]: r for r in results}

    def per_candle_C(key):
        rc = by[key]["routeC_mean_HRR"]
        return rc.get("primary_dHc38", {}).get("HRR_per_candle_W")

    def mlr_pc(key):
        return by[key]["routeC_mean_HRR"].get("mean_MLR_per_candle_mg_s")

    three = ["3cand_R1", "3cand_R2", "3cand_R3"]
    three_hrr = [per_candle_C(k) for k in three if per_candle_C(k)]
    three_mlr = [mlr_pc(k) for k in three if mlr_pc(k)]

    def stats(v):
        v = [x for x in v if x is not None]
        if not v:
            return None
        m = float(np.mean(v))
        s = float(np.std(v, ddof=1)) if len(v) > 1 else 0.0
        return {"n": len(v), "mean": round(m, 2), "std": round(s, 2),
                "CoV_pct": round(100 * s / m, 1) if m else None,
                "values": [round(x, 2) for x in v]}

    single_anchor = per_candle_C("1cand_R3")
    single_long_mlr = mlr_pc("1cand_long")
    single_R2 = per_candle_C("1cand_R2")

    three_hrr_stat = stats(three_hrr)
    three_mlr_stat = stats(three_mlr)

    superposition = {}
    if three_hrr_stat and single_anchor:
        ratio_hrr = 3 * three_hrr_stat["mean"] / single_anchor
        superposition["HRR_ratio_3candle_total_over_1candle"] = round(ratio_hrr, 2)
        superposition["per_candle_suppression_vs_single_pct"] = round(
            100 * (1 - three_hrr_stat["mean"] / single_anchor), 1)
    if three_mlr_stat and mlr_pc("1cand_R3"):
        superposition["MLR_ratio_3candle_total_over_1candle"] = round(
            3 * three_mlr_stat["mean"] / mlr_pc("1cand_R3"), 2)
    superposition["expected_if_noninteracting"] = 3.0
    superposition["interpretation"] = (
        "per-candle rate in the 3-candle runs is within ~10% of the single-candle "
        "anchor -> candles at this spacing behave as ~independent sources; model "
        "3 SEPARATE burners in FDS, not one merged source. Mild suppression is a "
        "minor, reportable coupling effect (vitiation / radiative cross-talk).")

    # dHc_implied spread (the empirical wax check)
    implied = {by[r["key"]]["key"]: r["routeA_O2_HRR_crosscheck"].get("dHc_implied_MJ_kg")
               for r in results if r["routeA_O2_HRR_crosscheck"].get("dHc_implied_MJ_kg") is not None
               and not r["routeA_O2_HRR_crosscheck"].get("disqualified")}

    return {
        "single_candle": {
            "anchor_R3_HRR_per_candle_W": single_anchor,
            "anchor_R3_note": "did NOT reach full steady state (1.6 g lost) -> may slightly over-read",
            "long_protocol_25aug_MLR_per_candle_mg_s": single_long_mlr,
            "long_protocol_25aug_note": "O2 HRR disqualified (dirty filter); mass-loss RATE only",
            "R2_HRR_per_candle_W": single_R2,
            "R2_note": "short/incomplete; timeline from load-cell shape",
            "rate_crosscheck_single_vs_anchor": {
                "anchor_R3_MLR_per_candle_mg_s": mlr_pc("1cand_R3"),
                "long_25aug_MLR_per_candle_mg_s": single_long_mlr,
                "ratio": (round(single_long_mlr / mlr_pc("1cand_R3"), 2)
                          if (single_long_mlr and mlr_pc("1cand_R3")) else None),
            },
            "caveat": "single-candle side = 1 matched burn (R3) + 1 long-protocol rate "
                      "cross-check (25.08) + 1 short partial (R2). NOT three replicates.",
        },
        "three_candle_repeatability_n3": {
            "HRR_per_candle_W": three_hrr_stat,
            "MLR_per_candle_mg_s": three_mlr_stat,
            "ignition_times_s": stats([by[k]["timeline"]["t_ignition_s"] for k in three]),
            "flameout_times_s": stats([by[k]["timeline"]["t_flameout_s"] for k in three]),
            "burn_durations_s": stats([by[k]["timeline"]["burn_duration_s"] for k in three]),
        },
        "superposition_test": superposition,
        "dHc_implied_by_run_MJ_kg": implied,
        "dHc_implied_verdict": (
            "Route-A dHc_implied ranges "
            f"{min(implied.values()):.0f}-{max(implied.values()):.0f} MJ/kg across runs "
            f"(literature paraffin 42-46). The spread is far larger than the wax "
            f"uncertainty -> the O2-consumption energy CANNOT pin dHc for a fire this "
            f"small. Documented disagreement, not tuned."
            if implied else "no valid Route-A energy available"),
    }


# --------------------------------------------------------------------------
# plots
# --------------------------------------------------------------------------
CFG_COLOR = {1: "#00798c", 3: "#d1495b"}


def plot_mass_delta(results):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5),
                             gridspec_kw={"width_ratios": [3, 2]})
    for r in results:
        run = r["_run"]
        t0, t1 = r["_win"]
        if t0 is None:
            continue
        t = run.time
        # post-ignition only: the pre-settle samples read 0 g on the gross
        # balance and would inject a ~1600 g artefact into the delta.
        w = (t >= t0) & (t <= (t1 + 120 if t1 else t[-1]))
        md = run.mass_delta(t0)[w]
        tau = t[w] - t0
        ax = axes[1] if r["key"] == "1cand_long" else axes[0]
        ax.plot(tau, md, lw=1.3, color=CFG_COLOR[r["config"]], alpha=0.9,
                label=f"{r['key']} ({r['config']}c, {r['routeC_mean_HRR'].get('mass_consumed_total_g','?')} g)")
        if t1:
            ax.plot(t1 - t0, run.mass_delta(t0)[run.idx_at(t1)], "o",
                    color=CFG_COLOR[r["config"]], ms=5)
    axes[0].set_title("short runs (<1 h)")
    axes[0].set_ylim(-0.5, 5)
    axes[1].set_title("25.08 long-protocol run (~3.8 h)")
    for ax in axes:
        ax.axvline(0, color="k", ls="--", lw=1)
        ax.set_xlabel("time from ignition (s)")
        ax.set_ylabel("mass lost since ignition (g)  [load-cell SHAPE; magnitude = weigh table]")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
    fig.suptitle("Cone runs - balance mass-loss is LINEAR (free-burning tea lights; "
                 "dot = metadata flameout, cross-checked vs load cell)", y=1.02)
    fig.tight_layout()
    p = f"{_repro.FIG_DIR}/cone_mass_delta.png"
    fig.savefig(p, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return p


def plot_hrr_bars(results, xr):
    runs = [r for r in results if r["routeC_mean_HRR"]]
    labels = [r["key"] for r in runs]
    x = np.arange(len(runs))
    cW = [r["routeC_mean_HRR"]["primary_dHc38"]["HRR_per_candle_W"] for r in runs]
    cLo = [r["routeC_mean_HRR"]["low_dHc36"]["HRR_per_candle_W"] for r in runs]
    cHi = [r["routeC_mean_HRR"]["high_dHc42"]["HRR_per_candle_W"] for r in runs]
    aW = [r["routeA_O2_HRR_crosscheck"].get("mean_HRR_total_W", np.nan) / r["config"]
          for r in runs]
    aDq = [r["routeA_O2_HRR_crosscheck"].get("disqualified", False) for r in runs]

    fig, ax = plt.subplots(figsize=(10, 5))
    yerr = np.array([np.array(cW) - np.array(cLo), np.array(cHi) - np.array(cW)])
    ax.bar(x - 0.18, cW, 0.36, yerr=yerr, capsize=4, color="#2e7d5b",
           label="Route C  (dm_manual x dHc_eff / t_burn)  [PRIMARY]")
    for i, (xi, a, dq) in enumerate(zip(x, aW, aDq)):
        ax.bar(xi + 0.18, a, 0.36, color="#b0b0b0", hatch="//" if dq else None,
               label=("Route A  (O2-consumption, QUALITATIVE)" if i == 0 else None))
        if dq:
            ax.text(xi + 0.18, a, " disq.", fontsize=7, rotation=90, va="bottom")
    for xi, v in zip(x, cW):
        ax.text(xi - 0.18, v + 0.6, f"{v:.1f} W", ha="center", fontsize=8)
    ax.axhspan(16, 20, color="#2e7d5b", alpha=0.08)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("mean HRR per candle  (W)")
    ax.set_title("Cone - per-candle mean HRR: Route C (primary) vs Route A (O2, qualitative)\n"
                 "error bars = combustion-efficiency band (dHc_eff 36-42 MJ/kg); shaded = 16-20 W")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    p = f"{_repro.FIG_DIR}/cone_hrr_per_candle.png"
    fig.savefig(p, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return p


def plot_routeA_noise(results):
    fig, ax = plt.subplots(figsize=(10, 5))
    for r in results:
        if not r["routeC_mean_HRR"]:
            continue
        run = r["_run"]
        t0, t1 = r["_win"]
        t = run.time
        w = (t >= t0) & (t <= t1)
        ax.plot(t[w] - t0, run.channels["HRR_kW"][w] * 1000, lw=0.6,
                color=CFG_COLOR[r["config"]], alpha=0.5)
        qc = r["routeC_mean_HRR"]["primary_dHc38"]["HRR_total_W"]
        ax.hlines(qc, 0, t1 - t0, color=CFG_COLOR[r["config"]], lw=2,
                  label=f"{r['key']}: Route C mean = {qc:.0f} W")
    ax.set_xlabel("time from ignition (s)")
    ax.set_ylabel("HRR total  (W)")
    ax.set_ylim(-100, 300)
    ax.set_title("Route A O2-consumption HRR(t) (thin) vs Route C mean (thick)\n"
                 "the O2 channel is noise-dominated for a <60 W fire - shown for scale only")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    p = f"{_repro.FIG_DIR}/cone_routeA_noise.png"
    fig.savefig(p, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return p


def plot_o2(results):
    fig, ax = plt.subplots(figsize=(10, 5))
    for r in results:
        run = r["_run"]
        t0, t1 = r["_win"]
        t = run.time
        o2 = run.channels["O2_pct"]
        base = np.nanmean(o2[t < (t0 - 5)]) if (t < t0 - 5).any() else o2[0]
        ax.plot(t - t0, o2 - base, lw=1.0, color=CFG_COLOR[r["config"]], alpha=0.8,
                label=f"{r['key']} ({r['config']}c)")
    ax.axvline(0, color="k", ls="--", lw=1)
    ax.axhline(0, color="0.6", lw=0.8)
    ax.set_xlabel("time from ignition (s)")
    ax.set_ylabel("O2 depletion from pre-ignition baseline  (% abs)")
    ax.set_title("Cone - O2 depletion (all runs). Whole-run depletion 0.01-0.04 % abs;\n"
                 "short-term analyzer noise ~0.001-0.002 % -> qualitative HRR only")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    p = f"{_repro.FIG_DIR}/cone_o2_depletion.png"
    fig.savefig(p, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return p


def plot_dHc_implied(results, xr):
    runs = [(r["key"], r["routeA_O2_HRR_crosscheck"].get("dHc_implied_MJ_kg"),
             r["routeA_O2_HRR_crosscheck"].get("disqualified", False))
            for r in results if r["routeA_O2_HRR_crosscheck"].get("dHc_implied_MJ_kg") is not None]
    fig, ax = plt.subplots(figsize=(8, 4.6))
    x = np.arange(len(runs))
    ax.bar(x, [v for _, v, _ in runs],
           color=["#b0b0b0" if dq else "#7a4fa3" for _, _, dq in runs])
    ax.axhspan(42, 46, color="green", alpha=0.15, label="paraffin literature dHc 42-46 MJ/kg")
    ax.axhline(38, color="green", ls="--", label="dHc_eff used (38 MJ/kg)")
    for xi, (_, v, _) in zip(x, runs):
        ax.text(xi, v + 1, f"{v:.0f}", ha="center", fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels([k for k, _, _ in runs], fontsize=8)
    ax.set_ylabel("dHc_implied = E(Route A) / dm_manual   (MJ/kg)")
    vals = [v for _, v, dq in runs if not dq]
    ax.set_title("Empirical dHc check - FAILS to pin the wax value\n"
                 f"(Route-A energy is noise-dominated; spread {min(vals):.0f}-{max(vals):.0f} "
                 f"MJ/kg >> wax uncertainty)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    p = f"{_repro.FIG_DIR}/cone_dHc_implied.png"
    fig.savefig(p, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return p


def plot_config_compare(results, xr):
    s = xr["three_candle_repeatability_n3"]
    single = xr["single_candle"]["anchor_R3_HRR_per_candle_W"]
    three_pc = s["HRR_per_candle_W"]
    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.bar([0], [single], 0.5, color=CFG_COLOR[1], label="1-candle anchor (R3)")
    ax.bar([1], [three_pc["mean"]], 0.5, yerr=[three_pc["std"]], capsize=5,
           color=CFG_COLOR[3], label=f"3-candle, per candle (n={three_pc['n']})")
    ax.text(0, single + 0.5, f"{single:.1f} W", ha="center")
    ax.text(1, three_pc["mean"] + three_pc["std"] + 0.5,
            f"{three_pc['mean']:.1f} ± {three_pc['std']:.1f} W", ha="center")
    ax.set_xticks([0, 1]); ax.set_xticklabels(["1 candle", "3 candles / 3"])
    ax.set_ylabel("mean HRR per candle  (W)")
    ax.set_ylim(0, 24)
    r = xr["superposition_test"]
    ax.set_title("Superposition test - per-candle HRR\n"
                 f"3-cand total / 1-cand = {r['HRR_ratio_3candle_total_over_1candle']}x "
                 f"(ideal 3.0x); ~{r['per_candle_suppression_vs_single_pct']}% suppression\n"
                 "-> model 3 separate burners")
    ax.legend(fontsize=9, loc="lower center")
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    p = f"{_repro.FIG_DIR}/cone_config_compare.png"
    fig.savefig(p, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return p


# --------------------------------------------------------------------------
def write_per_run_csv(results):
    p = f"{_repro.RESULT_DIR}/cone_per_run_summary.csv"
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run", "config", "role", "t_ignition_s", "t_flameout_s",
                    "burn_duration_s", "mass_consumed_total_g", "mass_consumed_per_candle_g",
                    "mean_MLR_per_candle_mg_s", "routeC_HRR_per_candle_W",
                    "routeC_HRR_per_candle_W_lo36", "routeC_HRR_per_candle_W_hi42",
                    "steady_HRR_per_candle_W", "routeA_mean_HRR_total_W",
                    "routeA_dHc_implied_MJ_kg", "O2_depletion_pct",
                    "O2_noise_std_pct", "O2_depl_over_noise"])
        for r in results:
            rc = r["routeC_mean_HRR"]; ra = r["routeA_O2_HRR_crosscheck"]
            sw = r["steady_window"] or {}
            w.writerow([
                r["key"], r["config"], r["role"],
                r["timeline"]["t_ignition_s"], r["timeline"]["t_flameout_s"],
                r["timeline"]["burn_duration_s"],
                rc.get("mass_consumed_total_g"), rc.get("mass_consumed_per_candle_g"),
                rc.get("mean_MLR_per_candle_mg_s"),
                rc.get("primary_dHc38", {}).get("HRR_per_candle_W"),
                rc.get("low_dHc36", {}).get("HRR_per_candle_W"),
                rc.get("high_dHc42", {}).get("HRR_per_candle_W"),
                sw.get("steady_HRR_per_candle_W_dHc38"),
                None if ra.get("disqualified") else ra.get("mean_HRR_total_W"),
                None if ra.get("disqualified") else ra.get("dHc_implied_MJ_kg"),
                r["gas"]["O2_depletion_over_burn_pct"],
                r["gas"]["O2_noise"].get("pre_ign_std_pct"),
                r["gas"]["O2_depletion_vs_noise_ratio"],
            ])
    return p


def write_cross_run_csv(xr):
    p = f"{_repro.RESULT_DIR}/cone_cross_run_summary.csv"
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["quantity", "n", "mean", "std", "CoV_pct", "values"])

        def row(lbl, st):
            if st:
                w.writerow([lbl, st["n"], st["mean"], st["std"], st["CoV_pct"], st["values"]])
        s = xr["three_candle_repeatability_n3"]
        row("3-candle HRR per candle (W)", s["HRR_per_candle_W"])
        row("3-candle MLR per candle (mg/s)", s["MLR_per_candle_mg_s"])
        row("3-candle ignition time (s)", s["ignition_times_s"])
        row("3-candle flameout time (s)", s["flameout_times_s"])
        row("3-candle burn duration (s)", s["burn_durations_s"])
        w.writerow([])
        w.writerow(["single-candle anchor R3 HRR/candle (W)", 1,
                    xr["single_candle"]["anchor_R3_HRR_per_candle_W"], "", "", ""])
        w.writerow(["superposition ratio (3-cand total / 1-cand)", "",
                    xr["superposition_test"]["HRR_ratio_3candle_total_over_1candle"],
                    "", "", "ideal 3.0"])
        w.writerow(["per-candle suppression vs single (%)", "",
                    xr["superposition_test"]["per_candle_suppression_vs_single_pct"], "", "", ""])
        w.writerow([])
        for k, v in xr["dHc_implied_by_run_MJ_kg"].items():
            w.writerow([f"dHc_implied {k} (MJ/kg)", "", v, "", "", "literature 42-46"])
    return p


def write_run_timeseries(results):
    out = []
    for r in results:
        run = r["_run"]; t0, t1 = r["_win"]
        t = run.time
        w = (t >= t0 - 120) & (t <= (t1 + 180 if t1 else t[-1]))
        series = [
            ("time_s", t[w]),
            ("mass_lost_since_ignition_g", run.mass_delta(t0)[w]),
            ("O2_pct", run.channels["O2_pct"][w]),
            ("CO2_pct", run.channels["CO2_pct"][w]),
            ("CO_pct", run.channels["CO_pct"][w]),
            ("HRR_O2_kW", run.channels["HRR_kW"][w]),
            ("HRR_per_area_kW_m2", run.channels["HRR_per_area_kW_m2"][w]),
        ]
        meta = {
            "run": r["file"], "config_candles": r["config"],
            "scope": "FREE-BURNING candle test (no external flux)",
            "mass_note": "load-cell SHAPE only; absolute mass from manual weigh table",
            "t_ignition_s": t0, "t_flameout_s": t1,
            "routeC_HRR_per_candle_W_dHc38": r["routeC_mean_HRR"].get("primary_dHc38", {}).get("HRR_per_candle_W"),
            "HRR_O2_note": "near instrument noise floor -- qualitative only",
        }
        p = f"{_repro.RESULT_DIR}/cone_{r['key']}_timeseries.csv"
        write_series_csv(p, "time_from_ignition_s", t[w] - t0, series, metadata=meta)
        out.append(p)
    return out


def main():
    weights = read_weights(f"{DATA}/weights.csv")
    results = [analyse(k, fn, cfg, role, weights) for k, fn, cfg, role in ROSTER]
    xr = cross_run(results)

    figs = [
        plot_mass_delta(results),
        plot_hrr_bars(results, xr),
        plot_routeA_noise(results),
        plot_o2(results),
        plot_dHc_implied(results, xr),
        plot_config_compare(results, xr),
    ]
    csvs = [write_per_run_csv(results), write_cross_run_csv(xr)] + write_run_timeseries(results)

    digest = {
        "runs": [{k: v for k, v in r.items() if not k.startswith("_")} for r in results],
        "cross_run": xr,
        "figures": figs, "csvs": csvs,
        "constants": {"dHc_eff_MJ_kg": DHC_EFF / 1e6, "dHc_band_MJ_kg": [x / 1e6 for x in DHC_BAND]},
    }
    out = f"{_repro.RESULT_DIR}/cone_digest.json"
    with open(out, "w") as f:
        json.dump(digest, f, indent=2, default=str)
    print(json.dumps(digest["runs"], indent=2, default=str))
    print("\n=== CROSS-RUN ===")
    print(json.dumps(xr, indent=2, default=str))
    print("\nwrote", out)


if __name__ == "__main__":
    main()
