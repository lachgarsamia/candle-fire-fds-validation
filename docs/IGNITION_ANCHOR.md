# IGNITION_ANCHOR — the t = 0 the whole time axis rests on

Every ignition-aligned number in this study (peak rises, crossing times,
sim-vs-experiment comparisons) is measured from a per-run **inferred ignition
instant**. This documents what it is, how it is found, its uncertainty, and why
it must be done per-run.

Code: `src/exponat_loader.py` (`event_transitions`), `src/exponat_analysis.py`
(`sustained_onset`). Data: `data/processed/exponat_events.csv`,
`exponat_digest.json`.

---

## The problem: the `event_number` clock is not common

Each run carries an operator-triggered `event_number` that steps 0 → 1 → 2 → 3 → 4.
The transition times differ by **up to 10×** between runs, and — critically —
**the candle-lighting step is a different transition number in different runs**:

| run | 0→1 | 1→2 | 2→3 | 3→4 | which step is ignition |
|---|--:|--:|--:|--:|---|
| R1 | 213 s | 303 s | **334 s** | 489 s | 2→3 |
| R2 | 24 s | **73 s** | 371 s | 772 s | 1→2 |
| R3 | 17 s | **47 s** | 303 s | 403 s | 1→2 |

The operator logged a different number of pre-ignition setup steps in R1 than in
R2/R3. So "align all runs to `event_number = 3`" would be **wrong** — it would
put R1's ignition at 334 s but R2's at 371 s (a post-ignition marker).

---

## The method: thermal onset, cross-checked to the nearest transition

1. **Primary anchor — `sustained_onset` on TC_01 (the plume sensor).**
   The first time TC_01 rises `Δ = 2 °C` above its pre-ignition baseline **and
   stays ≥ baseline + 1 °C for the next ≥ 15 s** (≥ 3 samples). That instant is
   `t_ignition`. The plume sensor responds within a second or two of the wick
   catching, and the sustained-hold condition rejects electrical spikes.

2. **Cross-check — the nearest `event_number` transition.**
   In all three runs the thermal onset lands **within 1–2 s of one transition**:

   | run | `t_ignition` (thermal onset) | nearest transition | Δ |
   |---|--:|---|--:|
   | R1 | 336 s | 2→3 at 334 s | **2.0 s** |
   | R2 | ~74 s | 1→2 at 73 s | **1.0 s** |
   | R3 | ~49 s | 1→2 at 47 s | **2.0 s** |

   That transition **is** the candle-lighting event (it is `2→3` in R1, `1→2` in
   R2/R3). The agreement to ≤ 2 s in every run confirms the thermal onset is the
   real ignition, not a spurious early rise.

---

## Uncertainty: ± 2 s

The anchor carries **± 2 s** — the largest offset between the thermal onset and
the confirming operator transition. This propagates into every reported time:

- crossing times (T1 to +60 °C at ign + 37 s, to +100 °C at ign + 140 s) carry
  ± 2 s;
- the sim-vs-experiment comparison uses the model's own t = 0 against the
  experiment's inferred ignition, so a ± 2 s slip in the anchor is a ± 2 s slip
  in the matched-time comparison — negligible against the sensors' own response
  times and the 1 s DAQ sampling.

---

## How it is applied

Per-run, independently:

```
t_ignition[run] = sustained_onset(TC_01[run])          # thermal onset
tau[run]        = exp_time[run] - t_ignition[run]        # ignition-aligned axis
```

All cross-run quantities (REPEATABILITY.md, EXPONAT_FINDINGS §4) are computed on
each run's `tau` axis and then combined. The raw `exp_time` and `event_number`
are **never** used to align runs to each other.
