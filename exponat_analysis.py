"""exponat_analysis.py -- thermal structure + event timeline for the three
Exponat compartment runs (Prompt 02).

SCOPE: temperature + event timing ONLY. Every heat-flux gauge and the
compartment load cell are dead (RECON B.4 / PROJECT_STATE). No flux, no mass.

Outputs (all under ./figures and ./results):
  figures/exponat_<run>_histories.png     7-TC history, ignition-aligned, events
  figures/exponat_<run>_structure.png     back-wall column / doorway / ceiling
  figures/exponat_overlay_plume.png       TC_01 & TC_03, 3 runs, ignition-aligned
  figures/exponat_structure_overlay.png   dT stratification metrics, 3 runs
  figures/exponat_repeatability.png       per-sensor peak rise, mean +/- std
  results/exponat_<run>_timeseries.csv    tidy per-run table (write_series_csv)
  results/exponat_events.csv              event transitions, all runs
  results/exponat_per_run_summary.csv     per-run / per-sensor metrics
  results/exponat_cross_run_summary.csv   repeatability (mean +/- std, CoV)

Reuse (RECON Part B): timeseries.write_series_csv as-is; devices.TC_THRESHOLDS;
the crossing-time helper mirrors summary_stats._first_threshold_time but indexes
the real (non-uniform) exp_time vector instead of assuming a fixed fps.
"""
from __future__ import annotations

import json

import numpy as np
import _repro  # noqa: F401  (headless mpl + FireScope path)
import matplotlib.pyplot as plt

from timeseries import write_series_csv          # FireScope, reused as-is
from devices import TC_THRESHOLDS                 # (60, 100, 300) degC

from exponat_loader import (
    load_exponat, LIVE_TC_COLUMNS, BACK_WALL_COLUMN, DOORWAY_COLUMN,
    CEILING, TC_POSITION,
)

RUNS = {
    "R1": f"{_repro.DATA_DIR}/2026-08-27_exponat_R1.txt",
    "R2": f"{_repro.DATA_DIR}/2026-08-27_exponat_R2.txt",
    "R3": f"{_repro.DATA_DIR}/2026-08-27_exponat_R3.txt",
}

TC_COLOR = {
    "TC_01": "#d1495b", "TC_02": "#edae49", "TC_03": "#66a182",
    "TC_05": "#2e4057", "TC_09": "#8d96a3", "TC_10": "#00798c", "TC_11": "#003d5b",
}


# --------------------------------------------------------------------------
# helpers (Qt-free, unit-tested-shape)
# --------------------------------------------------------------------------
def baseline(t, y, pre_s=10.0):
    """Median of y over the first `pre_s` seconds of record (pre-ignition)."""
    m = t < (t[0] + pre_s)
    return float(np.nanmedian(y[m])) if m.any() else float(y[0])


def first_crossing(t, y, thr):
    """First time (s) y exceeds thr. Mirrors summary_stats._first_threshold_time
    but returns the real timestamp t[idx] rather than idx/fps -- the exp_time
    axis is non-uniform (RECON B.4.5)."""
    hits = np.flatnonzero(np.asarray(y) > thr)
    return float(t[hits[0]]) if hits.size else None


def sustained_onset(t, y, base, delta=2.0, hold_s=15.0, floor=1.0):
    """First time y rises `delta` degC above `base` and stays >= base+floor for
    at least `hold_s` seconds afterwards -- the empirical thermal-onset instant."""
    thr = base + delta
    for i in range(len(t)):
        if y[i] > thr:
            w = (t >= t[i]) & (t < t[i] + hold_s)
            if w.sum() >= 3 and np.all(y[w] > base + floor):
                return float(t[i])
    return None


def local_slope(t, y, win_s=20.0):
    """Centred finite-difference dT/dt (degC/s) on the real time axis, smoothed
    by a running mean of half-width win_s."""
    dydt = np.gradient(y, t)
    # box smooth on the (nearly) 1 s grid, edge-padded (mode="same" zero-pads
    # and would corrupt the ends)
    k = max(1, int(win_s)) | 1
    pad = k // 2
    dp = np.concatenate([np.full(pad, dydt[0]), dydt, np.full(pad, dydt[-1])])
    return np.convolve(dp, np.ones(k) / k, mode="valid")


def quasi_steady_window(t, y, base, t_ign, slope_tol=0.03, min_len_s=60.0,
                        elevated_frac=0.5):
    """Longest POST-IGNITION interval where |smoothed dT/dt| < slope_tol degC/s
    AND y is elevated to at least `elevated_frac` of its peak rise above base --
    so the cold pre-ignition baseline is never mistaken for a plateau. Returns
    (t_start, t_end, mean, std) or None. Detected from the data, not hardcoded."""
    peak_rise = float(np.nanmax(y) - base)
    elevated = (y - base) > elevated_frac * peak_rise
    s = np.abs(local_slope(t, y))
    calm = (s < slope_tol) & elevated & (t > t_ign)
    best = None
    i, n = 0, len(t)
    while i < n:
        if not calm[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and calm[j + 1]:
            j += 1
        if t[j] - t[i] >= min_len_s:
            if best is None or (t[j] - t[i]) > (best[1] - best[0]):
                best = (float(t[i]), float(t[j]),
                        float(np.nanmean(y[i:j + 1])), float(np.nanstd(y[i:j + 1])))
        i = j + 1
    return best


# --------------------------------------------------------------------------
# per-run analysis
# --------------------------------------------------------------------------
def analyse_run(key, run):
    t = run.t()                        # exp_time (s), in-window only
    traces = {c: run.trace(c) for c in LIVE_TC_COLUMNS}
    base = {c: baseline(t, traces[c]) for c in LIVE_TC_COLUMNS}

    # -- thermal onset from the plume sensor, and event cross-reference -----
    onset = sustained_onset(t, traces["TC_01"], base["TC_01"])
    transitions = run.event_transitions()   # (from, to, exp_time, wall_time)
    # nearest event transition to the onset
    ign_event = None
    if onset is not None and transitions:
        ign_event = min(transitions, key=lambda tr: abs(tr[2] - onset))
    t_ign = onset if onset is not None else (ign_event[2] if ign_event else 0.0)
    tau = t - t_ign                     # ignition-aligned time

    # -- per-sensor metrics ----------------------------------------------
    per_sensor = {}
    for c in LIVE_TC_COLUMNS:
        y = traces[c]
        pk = int(np.nanargmax(y))
        rise = y - base[c]
        # mean rise over the post-onset record
        post = tau >= 0
        per_sensor[c] = {
            "group": TC_POSITION[c][0],
            "x_m": TC_POSITION[c][1],
            "z_m": TC_POSITION[c][2],
            "baseline_C": round(base[c], 2),
            "peak_C": round(float(y[pk]), 1),
            "peak_rise_C": round(float(y[pk] - base[c]), 1),
            "time_to_peak_from_ign_s": round(float(t[pk] - t_ign), 1),
            "mean_rise_post_ign_C": round(float(np.nanmean(rise[post])), 1) if post.any() else None,
            "t_over_60C_from_ign_s": (lambda v: round(v - t_ign, 1) if v is not None else None)(
                first_crossing(t, y, 60.0)),
            "t_over_100C_from_ign_s": (lambda v: round(v - t_ign, 1) if v is not None else None)(
                first_crossing(t, y, 100.0)),
        }

    # -- thermal structure ----------------------------------------------
    T1, T2, T3 = (traces[c] for c in BACK_WALL_COLUMN)
    T9, T10, T11 = (traces[c] for c in DOORWAY_COLUMN)
    T5 = traces[CEILING]

    # upper-layer stratification strength (above the plume-contaminated z=0.05):
    dT_layer = T3 - T2                       # z=0.23 minus z=0.16
    dT_door = T11 - T9                       # vent top minus vent bottom
    dT_ceiling_horiz = T3 - T5               # ceiling near-fire minus ceiling-centre

    # stratification onset: dT_layer rising a sustained margin above its OWN
    # pre-ignition baseline (the two sensors carry a small static offset).
    dT_layer_base = float(np.nanmedian(dT_layer[t < t_ign])) if (t < t_ign).any() else 0.0
    strat_onset = None
    margin = 3.0
    for i in range(len(t)):
        if t[i] <= t_ign:
            continue
        if dT_layer[i] > dT_layer_base + margin:
            w = (t >= t[i]) & (t < t[i] + 30)
            if w.sum() >= 3 and np.all(dT_layer[w] > dT_layer_base + 0.5 * margin):
                strat_onset = float(t[i]); break

    quasi = quasi_steady_window(t, traces["TC_01"], base["TC_01"], t_ign)

    # broad-maximum characterization (a candle plume in this box has a broad
    # peak, not a flat plateau): mean +/- std of TC_01 within +/-60 s of its peak,
    # and the post-peak cooling rate.
    tpk = float(t[int(np.nanargmax(traces["TC_01"]))])
    near = (t >= tpk - 60) & (t <= tpk + 60)
    nearpeak_mean = float(np.nanmean(traces["TC_01"][near]))
    nearpeak_std = float(np.nanstd(traces["TC_01"][near]))
    postpk = t > tpk + 30
    decline_rate = None
    if postpk.sum() > 20:
        decline_rate = float(np.polyfit(t[postpk], traces["TC_01"][postpk], 1)[0]) * 60.0  # degC/min

    structure = {
        "back_wall_column_peak_C": {c: round(float(np.nanmax(traces[c])), 1) for c in BACK_WALL_COLUMN},
        "column_is_non_monotonic_in_height":
            bool(np.nanmax(T1) > np.nanmax(T3) > np.nanmax(T2)),
        "upper_layer_dT_T3_minus_T2_peak_C": round(float(np.nanmax(dT_layer)), 1),
        "upper_layer_dT_T3_minus_T2_mean_post_ign_C":
            round(float(np.nanmean(dT_layer[tau >= 0])), 1) if (tau >= 0).any() else None,
        "stratification_onset_from_ign_s":
            round(strat_onset - t_ign, 1) if strat_onset is not None else None,
        "doorway_orders_by_height": bool(np.nanmax(T11) > np.nanmax(T10) >= np.nanmax(T9) - 0.5),
        "doorway_dT_T11_minus_T9_peak_C": round(float(np.nanmax(dT_door)), 1),
        "ceiling_horizontal_dT_T3_minus_T5_peak_C": round(float(np.nanmax(dT_ceiling_horiz)), 1),
        "ceiling_horizontal_dT_T3_minus_T5_mean_post_ign_C":
            round(float(np.nanmean(dT_ceiling_horiz[tau >= 0])), 1) if (tau >= 0).any() else None,
        "hot_layer_localized_over_fire":
            bool(np.nanmax(T3) - np.nanmax(T5) > 10.0),
    }

    char_times = {
        "record_start_exp_time_s": float(t[0]),
        "record_end_exp_time_s": float(t[-1]),
        "thermal_onset_exp_time_s": round(onset, 1) if onset is not None else None,
        "nearest_event_transition": (
            f"{ign_event[0]}->{ign_event[1]} @ {ign_event[2]:.0f}s" if ign_event else None),
        "onset_minus_nearest_event_s": (
            round(onset - ign_event[2], 1) if (onset is not None and ign_event) else None),
        "t_ignition_used_s": round(t_ign, 1),
        "post_ignition_record_s": round(float(t[-1] - t_ign), 1),
        "time_to_stratification_from_ign_s":
            round(strat_onset - t_ign, 1) if strat_onset is not None else None,
        "time_to_plume_peak_from_ign_s": round(tpk - t_ign, 1),
        "quasi_steady_window_from_ign_s": (
            [round(quasi[0] - t_ign, 1), round(quasi[1] - t_ign, 1)] if quasi else None),
        "quasi_steady_TC01_mean_C": round(quasi[2], 1) if quasi else None,
        "quasi_steady_TC01_std_C": round(quasi[3], 2) if quasi else None,
        "broad_peak_TC01_mean_C": round(nearpeak_mean, 1),
        "broad_peak_TC01_std_C": round(nearpeak_std, 2),
        "post_peak_cooling_rate_C_per_min": round(decline_rate, 2) if decline_rate is not None else None,
    }

    # -- noise-floor estimate from the pre-ignition segment --------------
    pre = tau < -10
    noise = {}
    if pre.sum() > 10:
        for c in LIVE_TC_COLUMNS:
            noise[c] = round(float(np.nanstd(traces[c][pre])), 3)

    return {
        "run": key,
        "name": run.name,
        "loader_notes": run.notes,
        "n_split_writes": run.n_split_writes,
        "n_out_of_window": run.n_out_of_window,
        "event_transitions": [
            {"from": a, "to": b, "exp_time_s": round(et, 1), "wall_time_s": round(wt, 1)}
            for a, b, et, wt in transitions
        ],
        "t_ignition_s": round(t_ign, 1),
        "per_sensor": per_sensor,
        "structure": structure,
        "characteristic_times": char_times,
        "pre_ignition_noise_std_C": noise,
        # arrays kept for plotting / CSV, not JSON-dumped
        "_t": t, "_tau": tau, "_traces": traces, "_dT_layer": dT_layer,
        "_dT_door": dT_door, "_dT_ceiling": dT_ceiling_horiz, "_run": run,
    }


# --------------------------------------------------------------------------
# plotting
# --------------------------------------------------------------------------
def _mark_events(ax, res):
    run = res["_run"]
    t_ign = res["t_ignition_s"]
    for a, b, et, wt in run.event_transitions():
        ax.axvline(et - t_ign, color="0.6", ls=":", lw=0.9)
        ax.text(et - t_ign, ax.get_ylim()[1], f" e{a}->{b}", rotation=90,
                va="top", ha="left", fontsize=6, color="0.4")
    ax.axvline(0.0, color="k", ls="--", lw=1.0)
    ax.text(0.0, ax.get_ylim()[1], " ignition", rotation=90, va="top",
            ha="right", fontsize=7)


def plot_histories(res):
    fig, ax = plt.subplots(figsize=(9, 5))
    tau, tr = res["_tau"], res["_traces"]
    for c in LIVE_TC_COLUMNS:
        g, x, z, _role = TC_POSITION[c]
        ax.plot(tau, tr[c], color=TC_COLOR[c], lw=1.3,
                label=f"{c}  ({g}, z={z} m)")
    ax.set_xlabel("time from inferred ignition  (s)")
    ax.set_ylabel("temperature  (deg C)")
    ax.set_title(f"Exponat {res['run']} - thermocouple histories "
                 f"(ignition-aligned; TEMPERATURE-only run)")
    ax.legend(fontsize=7, ncol=2, loc="upper left")
    ax.grid(alpha=0.3)
    _mark_events(ax, res)
    fig.tight_layout()
    p = f"{_repro.FIG_DIR}/exponat_{res['run']}_histories.png"
    fig.savefig(p, dpi=130)
    plt.close(fig)
    return p


def plot_structure(res):
    tau, tr = res["_tau"], res["_traces"]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.3), sharex=True)

    ax = axes[0]
    for c in BACK_WALL_COLUMN:
        ax.plot(tau, tr[c], color=TC_COLOR[c], lw=1.3,
                label=f"{c}  z={TC_POSITION[c][2]} m")
    ax.set_title("back-wall column (x=0.12 m)\nplume low, layer high -> non-monotonic")
    ax.set_ylabel("temperature (deg C)")
    ax.legend(fontsize=7)

    ax = axes[1]
    for c in DOORWAY_COLUMN:
        ax.plot(tau, tr[c], color=TC_COLOR[c], lw=1.3,
                label=f"{c}  z={TC_POSITION[c][2]} m")
    ax.set_title("doorway stack (x=0.70 m)\nhot high (outflow) / cool low (inflow)")
    ax.legend(fontsize=7)

    ax = axes[2]
    ax.plot(tau, tr["TC_03"], color=TC_COLOR["TC_03"], lw=1.3, label="TC_03 ceiling @ fire (x=0.12)")
    ax.plot(tau, tr["TC_05"], color=TC_COLOR["TC_05"], lw=1.3, label="TC_05 ceiling centre (x=0.35)")
    ax.plot(tau, tr["TC_02"], color=TC_COLOR["TC_02"], lw=1.0, ls="--", label="TC_02 mid column (ref)")
    ax.set_title("ceiling: near-fire vs centre\nhot layer localized over the fire?")
    ax.legend(fontsize=7)

    for ax in axes:
        ax.set_xlabel("time from ignition (s)")
        ax.grid(alpha=0.3)
    fig.suptitle(f"Exponat {res['run']} - thermal structure", y=1.02)
    fig.tight_layout()
    p = f"{_repro.FIG_DIR}/exponat_{res['run']}_structure.png"
    fig.savefig(p, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return p


def plot_overlays(results):
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
    for res in results:
        k = res["run"]
        axes[0].plot(res["_tau"], res["_traces"]["TC_01"], lw=1.4, label=f"{k}  TC_01 (plume)")
        axes[1].plot(res["_tau"], res["_traces"]["TC_03"], lw=1.4, label=f"{k}  TC_03 (ceiling @ fire)")
    for ax, ttl in zip(axes, ["TC_01 plume sensor", "TC_03 ceiling-near-fire sensor"]):
        ax.axvline(0, color="k", ls="--", lw=1)
        ax.set_xlabel("time from inferred ignition (s)")
        ax.set_ylabel("temperature (deg C)")
        ax.set_title(ttl)
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
    fig.suptitle("Exponat - cross-run overlay, ignition-aligned "
                 "(operator event clock is NOT common; alignment is per-run)", y=1.02)
    fig.tight_layout()
    p = f"{_repro.FIG_DIR}/exponat_overlay_plume.png"
    fig.savefig(p, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return p


def plot_structure_overlay(results):
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
    for res in results:
        k = res["run"]
        axes[0].plot(res["_tau"], res["_dT_layer"], lw=1.3, label=f"{k}")
        axes[1].plot(res["_tau"], res["_dT_door"], lw=1.3, label=f"{k}")
    axes[0].set_title("upper-layer stratification  T3 - T2  (z: 0.23 - 0.16 m)")
    axes[1].set_title("doorway stratification  T11 - T9  (z: 0.14 - 0.015 m)")
    for ax in axes:
        ax.axhline(0, color="0.7", lw=0.8)
        ax.axvline(0, color="k", ls="--", lw=1)
        ax.set_xlabel("time from ignition (s)")
        ax.set_ylabel("delta T (deg C)")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
    fig.suptitle("Exponat - stratification metrics, cross-run", y=1.02)
    fig.tight_layout()
    p = f"{_repro.FIG_DIR}/exponat_structure_overlay.png"
    fig.savefig(p, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return p


def plot_repeatability(results):
    sensors = LIVE_TC_COLUMNS
    means, stds = [], []
    for c in sensors:
        vals = [r["per_sensor"][c]["peak_rise_C"] for r in results]
        means.append(np.mean(vals))
        stds.append(np.std(vals, ddof=1) if len(vals) > 1 else 0.0)
    x = np.arange(len(sensors))
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(x, means, yerr=stds, capsize=4,
           color=[TC_COLOR[c] for c in sensors])
    for i, (m, s) in enumerate(zip(means, stds)):
        ax.text(i, m + s + 1, f"{m:.0f}±{s:.0f}", ha="center", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{c}\n{TC_POSITION[c][0].split()[0]} z={TC_POSITION[c][2]}"
                        for c in sensors], fontsize=7)
    ax.set_ylabel("peak temperature rise above baseline (deg C)")
    ax.set_title("Exponat - per-sensor peak rise, mean ± std across R1/R2/R3 "
                 "(each run aligned to its own ignition)")
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    p = f"{_repro.FIG_DIR}/exponat_repeatability.png"
    fig.savefig(p, dpi=130)
    plt.close(fig)
    return p


# --------------------------------------------------------------------------
# CSV writers (reuse write_series_csv)
# --------------------------------------------------------------------------
def write_run_csv(res):
    run = res["_run"]
    t = res["_t"]
    ev = run.event_number[run.in_window].astype(float)
    series = [("exp_time_s", t.astype(float)),
              ("event_number", ev)]
    for c in LIVE_TC_COLUMNS:
        series.append((f"{c}_C", res["_traces"][c]))
    series.append(("dT_upperlayer_T3_T2_C", res["_dT_layer"]))
    series.append(("dT_doorway_T11_T9_C", res["_dT_door"]))
    meta = {
        "run": res["name"],
        "scope": "TEMPERATURE + event timing only (flux/mass channels dead)",
        "t_ignition_exp_time_s": res["t_ignition_s"],
        "x_axis": "time_from_ignition_s = exp_time_s - t_ignition_exp_time_s",
        "tc_positions_m": "; ".join(f"{c}:(x={TC_POSITION[c][1]},z={TC_POSITION[c][2]})"
                                    for c in LIVE_TC_COLUMNS),
        "source": "exponat_analysis.py",
    }
    p = f"{_repro.RESULT_DIR}/exponat_{res['run']}_timeseries.csv"
    write_series_csv(p, "time_from_ignition_s", res["_tau"], series, metadata=meta)
    return p


def write_events_csv(results):
    import csv
    p = f"{_repro.RESULT_DIR}/exponat_events.csv"
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run", "from_event", "to_event", "exp_time_s", "wall_time_s",
                    "t_from_ignition_s", "note"])
        for res in results:
            tign = res["t_ignition_s"]
            for tr in res["event_transitions"]:
                note = ""
                ct = res["characteristic_times"]
                if ct["nearest_event_transition"] and \
                   ct["nearest_event_transition"].startswith(f"{tr['from']}->{tr['to']} "):
                    note = f"nearest to thermal onset (dt={ct['onset_minus_nearest_event_s']} s)"
                w.writerow([res["run"], tr["from"], tr["to"], tr["exp_time_s"],
                            tr["wall_time_s"], round(tr["exp_time_s"] - tign, 1), note])
    return p


def write_summaries(results):
    import csv
    # per-run / per-sensor
    p1 = f"{_repro.RESULT_DIR}/exponat_per_run_summary.csv"
    with open(p1, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run", "sensor", "group", "x_m", "z_m", "baseline_C", "peak_C",
                    "peak_rise_C", "time_to_peak_from_ign_s", "mean_rise_post_ign_C",
                    "t_over_60C_from_ign_s", "t_over_100C_from_ign_s"])
        for res in results:
            for c in LIVE_TC_COLUMNS:
                s = res["per_sensor"][c]
                w.writerow([res["run"], c, s["group"], s["x_m"], s["z_m"],
                            s["baseline_C"], s["peak_C"], s["peak_rise_C"],
                            s["time_to_peak_from_ign_s"], s["mean_rise_post_ign_C"],
                            s["t_over_60C_from_ign_s"], s["t_over_100C_from_ign_s"]])

    # cross-run repeatability
    p2 = f"{_repro.RESULT_DIR}/exponat_cross_run_summary.csv"
    with open(p2, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["quantity", "unit", "R1", "R2", "R3", "mean", "std", "CoV_percent"])

        def row(label, unit, vals):
            vals = [v for v in vals if v is not None]
            if not vals:
                w.writerow([label, unit, "", "", "", "", "", ""])
                return
            m = np.mean(vals)
            s = np.std(vals, ddof=1) if len(vals) > 1 else 0.0
            cov = 100 * s / m if m else 0.0
            padded = (vals + [None, None, None])[:3]
            w.writerow([label, unit,
                        *[f"{v:.1f}" if v is not None else "" for v in padded],
                        f"{m:.1f}", f"{s:.1f}", f"{cov:.1f}"])

        for c in LIVE_TC_COLUMNS:
            row(f"{c} peak rise", "degC", [r["per_sensor"][c]["peak_rise_C"] for r in results])
        row("TC_01 time-to-peak", "s", [r["per_sensor"]["TC_01"]["time_to_peak_from_ign_s"] for r in results])
        row("upper-layer dT T3-T2 (peak)", "degC",
            [r["structure"]["upper_layer_dT_T3_minus_T2_peak_C"] for r in results])
        row("doorway dT T11-T9 (peak)", "degC",
            [r["structure"]["doorway_dT_T11_minus_T9_peak_C"] for r in results])
        row("ceiling horiz dT T3-T5 (peak)", "degC",
            [r["structure"]["ceiling_horizontal_dT_T3_minus_T5_peak_C"] for r in results])
        row("post-ignition record length", "s",
            [r["characteristic_times"]["post_ignition_record_s"] for r in results])
    return p1, p2


# --------------------------------------------------------------------------
def recommend_primary(results):
    """Cleanest validation reference: longest post-ignition record, clearest
    stratification, fewest split-write dropouts."""
    scored = []
    for r in results:
        ct = r["characteristic_times"]
        strat = r["structure"]["upper_layer_dT_T3_minus_T2_mean_post_ign_C"] or 0.0
        score = (ct["post_ignition_record_s"] / 100.0) + strat - 0.5 * r["n_split_writes"]
        scored.append((score, r["run"], {
            "post_ignition_record_s": ct["post_ignition_record_s"],
            "mean_upper_layer_dT_C": strat,
            "n_split_writes": r["n_split_writes"],
            "quasi_steady_window_s": ct["quasi_steady_window_from_ign_s"],
        }))
    scored.sort(reverse=True)
    return scored[0][1], scored


def main():
    runs = {k: load_exponat(p) for k, p in RUNS.items()}
    results = [analyse_run(k, r) for k, r in runs.items()]

    figs = []
    for res in results:
        figs.append(plot_histories(res))
        figs.append(plot_structure(res))
        write_run_csv(res)
    figs.append(plot_overlays(results))
    figs.append(plot_structure_overlay(results))
    figs.append(plot_repeatability(results))
    ev_csv = write_events_csv(results)
    s1, s2 = write_summaries(results)
    primary, scoreboard = recommend_primary(results)

    digest = {
        "runs": [{k: v for k, v in res.items() if not k.startswith("_")} for res in results],
        "recommended_primary_run": primary,
        "primary_scoreboard": [{"run": s[1], "score": round(s[0], 2), **s[2]} for s in scoreboard],
        "figures": figs,
        "csvs": [ev_csv, s1, s2] + [f"{_repro.RESULT_DIR}/exponat_{r['run']}_timeseries.csv"
                                    for r in results],
    }
    out = f"{_repro.RESULT_DIR}/exponat_digest.json"
    with open(out, "w") as f:
        json.dump(digest, f, indent=2, default=str)
    print(json.dumps(digest["runs"], indent=2, default=str))
    print("\nRECOMMENDED PRIMARY RUN:", primary)
    for s in digest["primary_scoreboard"]:
        print("  ", s)
    print("\nwrote", out)


if __name__ == "__main__":
    main()
