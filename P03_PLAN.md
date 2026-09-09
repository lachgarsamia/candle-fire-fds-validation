# P03 — FDS baseline: proposed plan (NEEDS SIGN-OFF BEFORE THE FULL RUN)

No P03 prompt was provided, so this is a plan drafted from `PROJECT_STATE.md`,
`FDS_geometry_reference.md`, `CONE_FINDINGS.md` and `EXPONAT_FINDINGS.md`.
**Please confirm it (or paste the real P03 spec) before I launch the multi-hour
baseline run.** The deck generator and a validated draft deck already exist.

## Status of the infrastructure (done, unblocked)

* FDS **6.11.1** is installed and runs (`/Applications/FDS/FDS6/bin/fds`).
* `fds/make_fds.py` — parametric deck generator. Geometry, 18 W source term and
  the 7 TC probes are hard-wired from the findings; everything a study would
  sweep (`--dx`, `--t-end`, `--box-top`, `--n-candles`) is a CLI arg, so P03 and
  the P04/P05 variants come from one source.
* `fds/baseline/candle_base_dx5.fds` — 5 mm baseline deck, generated.
* Validated: a 1 cm / 30 s smoke-test ran clean (deck syntax OK, fire ignites,
  TC probes report). It also **confirmed the mesh sensitivity PROJECT_STATE
  flagged** — at 1 cm the plume at T1 is under-resolved and the near-fire
  ceiling (T3) heated before the plume probe (T1), the reverse of the
  experiment. The baseline must be ≥ 5 mm; P04 is where this gets pinned.

## What P03 delivers (proposed)

One baseline simulation of the **single-candle compartment** (the Exponat
configuration), compared against the **R1** thermocouple record (P02's
recommended primary), producing:

* `fds/baseline/` run + a `p03_baseline.py` post-processor that reads the FDS
  `_devc.csv` and overlays the 7 modelled TCs on the measured R1 traces,
  ignition-aligned;
* the same structural metrics P02 computed for the experiment (non-monotonic
  back-wall column; ceiling horizontal ΔT T3−T5; doorway ΔT T11−T9; time to
  60/100 °C at T1);
* `FDS_BASELINE_FINDINGS.md` — where the baseline agrees and disagrees with the
  measurement, **with the gap decomposed into the three uncertainty sources**
  (numerical / experimental / model), not attributed wholesale to "FDS error".
  No parameter is tuned to close a gap.

## Fixed modelling inputs (from the data — not to be tuned)

| item | value | source |
|---|---|---|
| domain (outer acrylic box interior) | 1.00 × 0.30 × 0.50 m | geometry ref |
| room interior | 0.70 × 0.30 × 0.23 m, on the floor at x = 0 | geometry ref |
| walls | 10 mm acrylic — `MATL` k = 0.19 W/m/K, ρ = 1190, c = 1.42 kJ/kg/K, ε = 0.9; `BACKING='EXPOSED'` (heat leaks to lab) | geometry ref + standard PMMA/acrylic props |
| doorway | left wall x = 0.70, floor level, 0.05 w × 0.15 h, depth-centred | geometry ref |
| candle | x = 0.09, y = 0.15, floor; cup ≈ 37 mm → snapped square ≈ 12.25 cm² at 5 mm | geometry ref |
| **source term** | **18 W**, constant, `TAU_Q = −8 s` ignition ramp; HRRPUA 14.7 kW/m² | CONE_FINDINGS (18 ± 2 W; linear/constant burn) |
| fuel | paraffin C₂₅H₅₂, ΔHc 42 MJ/kg, soot yield 0.008, CO yield 0.001 | CONE_FINDINGS |
| ambient | 25 °C | exponat baselines 25–27 °C |
| TC probes | gas `TEMPERATURE` at the 7 measured (x, y, z) | geometry ref / EXPONAT_FINDINGS §9 |
| comparison anchor | model t = 0 ↔ experiment inferred ignition (R1); carry ± 2 s | EXPONAT_FINDINGS §5 |

## Open decisions — I need your call on these (or the P03 spec)

1. **Baseline mesh.** Proposed **5 mm uniform** (1.20 M cells, D*/dx ≈ 2.4).
   Still coarse for an 18 W plume but the pragmatic baseline; P04 refines to
   2.5 mm (likely nested near the candle). Estimated runtime for 5 mm / 200 s:
   **~8–12 h** on this Mac (single mesh, OpenMP). Alternatives:
   * 5 mm but **T_END = 120 s** (~5–7 h) — captures ignition + structure onset,
     misses the 100 °C crossing at T1 (+140 s);
   * **nested 3 mm** box around the candle + 6 mm elsewhere — better plume, similar
     total cells, needs a 2-mesh deck (I'd add it to the generator);
   * accept 1 cm for a fast first look, knowing T1 will be wrong.
2. **Run duration.** Proposed **200 s** — covers the ignition ramp, stratification
   onset (+30–90 s), and the 60 °C / 100 °C crossings at T1. The experiment's
   broad peak is at +430 s and there is no steady state, so a full-burn match
   (~550–940 s) roughly **doubles-to-quadruples** the runtime for the slowly
   decaying tail. Recommend 200 s for the baseline, longer only in P05 if needed.
3. **Outer-box top boundary.** Proposed **open** (`ZMAX = OPEN`) — the box vents
   to the lab, fire gets unlimited air (matches the 900 s+ steady experimental
   burn). The real box top condition is not documented. A **sealed** variant is
   one flag (`--box-top sealed`); P05 should test both since it affects the
   plenum and, weakly, the room TCs.
4. **Radiative fraction.** Set to **0.25** (small clean candle flame, literature)
   rather than the FDS default 0.35. This is a physical input with a basis, not
   a tuning knob — but flag if you want it left at default.
5. **Validation run.** R1 is the proposed anchor (P02). Compare against R1 only,
   or against the R1/R2/R3 envelope (±7 °C plume, ±3–4 °C ΔT, ±27 s timing)?
6. **3-candle case.** The Exponat compartment has **one** candle, so the baseline
   is 1-candle. Do you also want a 3-candle compartment run in P03, or is that
   out of scope here (cone superposition already answered "3 separate burners")?

## Proposed sequence once signed off

1. Launch `candle_base_dx5.fds` (background, ~8–12 h). Monitor HRR + a few TCs
   for sanity in the first ~30 min; abort early if the fire misbehaves.
2. While it runs: write `p03_baseline.py` (FDS `_devc.csv` → overlay on
   `results/exponat_R1_timeseries.csv`, same metrics as P02).
3. On completion: generate the comparison figures + `FDS_BASELINE_FINDINGS.md`
   with the three-way uncertainty decomposition.
4. Update `PROJECT_STATE.md`; hand P04 (mesh study) the baseline as its
   reference point.
