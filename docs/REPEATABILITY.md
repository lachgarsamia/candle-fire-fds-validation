# REPEATABILITY — the experimental band (n = 3)

Cross-run scatter from R1/R2/R3, each aligned to its own inferred ignition
(IGNITION_ANCHOR.md). This is the source of the **experimental** column in the
three-uncertainty split (VALIDATION_FINDINGS §2). Data:
`data/processed/exponat_cross_run_summary.csv`, `exponat_per_run_summary.csv`.
Figure: `figures/report_repeatability.png`.

---

## Per-sensor peak rise

| sensor | R1 | R2 | R3 | mean ± σ (°C) | CoV | quality |
|---|--:|--:|--:|--:|--:|---|
| T1 (plume, z 0.05) | 111.4 | 110.2 | 99.4 | **107.0 ± 6.6** | 6.2 % | excellent |
| T2 (mid-column, z 0.16) | 26.5 | 31.7 | 46.0 | 34.7 ± 10.1 | **29.1 %** | poor — see below |
| T3 (ceiling@fire, z 0.23) | 38.9 | 46.6 | 44.8 | **43.4 ± 4.0** | 9.3 % | good |
| T5 (ceiling mid-room) | 4.2 | 5.0 | 4.7 | 4.6 ± 0.4 | 8.7 % | good (near DAQ floor) |
| T9 (doorway floor) | 0.2 | 0.2 | 0.2 | 0.2 ± 0.0 | — | at the resolution floor |
| T10 (doorway mid) | 0.9 | 1.2 | 1.2 | 1.1 ± 0.2 | 15.7 % | ±0.2 °C on ~1 °C — DAQ-limited |
| T11 (doorway top) | 4.5 | 4.9 | 4.8 | 4.7 ± 0.2 | 4.4 % | excellent |

## Structure metrics

| quantity | mean ± σ | CoV |
|---|--:|--:|
| upper-layer ΔT (T3 − T2), peak | 30.1 ± 2.8 °C | 9.1 % |
| ceiling horizontal ΔT (T3 − T5), peak | 40.8 ± 3.8 °C | 9.4 % |
| doorway ΔT (T11 − T9), peak | 5.0 ± 0.4 °C | 7.2 % |
| T1 time-to-peak from ignition | 431 ± 27 s | 6.4 % |

---

## Reading it

- **The physics is repeatable to ≈ 6–9 % on every sensor that carries a real
  signal** (T1, T3, T5, T11) and on every structure metric. This is a *tight*
  experiment for a hand-lit tea light.
- **T2 is the exception (CoV 29 %).** It sits at z = 0.16 m on the back-wall
  column — above the ~1–2 cm flame but below the ceiling jet, in the flickering
  plume/entrainment boundary. Its peak swings 26 → 46 °C across the three runs.
  T2 carries a large experimental band by nature; it is not a modelling target.
- **T10 CoV 16 % is a resolution artefact** — ±0.2 °C on a ~1 °C rise, at the DAQ
  quantisation (~0.1 °C). T9 (CoV "0 %") is pinned at the floor. The doorway
  sensors are validated as *trends*, not to 0.1 °C.
- **Time-to-peak is only meaningful for T1** (431 ± 27 s). The other sensors are
  near-flat past ~150 s, so their "time-to-peak" is dominated by late noise
  (e.g. T10: 500 / 710 / 268 s — meaningless) and is not used.
- **R3 ran cooler** — T1 peak 126 °C vs 137 °C for R1/R2, more post-peak decline.
  A slightly weaker candle set or wax depletion within the record; consistent
  with the cone-side per-candle spread of 16.5–20 W. The plume peak is a **band
  (≈ 110–137 °C absolute)**, not a point.

## Caveat on the σ itself

n = 3, one configuration, same TC set and DAQ for all three runs → the σ
captures **run-to-run repeatability**, not instrument bias. There is no
independent bias estimate. The three-uncertainty split uses this σ as the
experimental band and does not claim it bounds systematic error.

## How it enters the validation

`src/p05_validation.py :: exp_band(tc, tau)` computes the sample std across
R1/R2/R3 **at the matched comparison time** (65 s), not at the peak — so the
band used in VALIDATION §2 is generally tighter than the peak-rise σ above
(e.g. T3: ±5.0 °C at 65 s vs ±4.0 °C at the peak; T2: ±1.3 °C at 65 s vs
±10.1 °C at the peak, because the runs diverge only later).
