# LIMITATIONS — consolidated

Every limitation from CONE_FINDINGS, EXPONAT_FINDINGS, MESH_STUDY_FINDINGS,
VALIDATION_FINDINGS, SENSITIVITY_FINDINGS and SMOKE_FINDINGS, deduplicated and
grouped. Each conclusion in those docs already carries the relevant subset; this
is the single reference.

---

## Experimental

**E1 · The compartment ground truth is temperature + timing only.**
Of 40 thermocouple channels, 7 are live; all 10 heat-flux gauges and the
compartment load cell return sentinel values. There is no measured heat flux,
mass loss, pressure, or obscuration for the compartment case.

**E2 · n = 3, one configuration, one TC set.**
The σ in REPEATABILITY.md captures run-to-run repeatability, not instrument
bias. No independent bias estimate exists (all runs share the same sensors and
DAQ).

**E3 · Near-ambient sensors are DAQ-resolution-limited.**
T5, T9, T10, T11 rise only a few °C against a ~0.1 °C quantisation with ~0
pre-ignition noise. Their rises are real and repeatable but are validated as
*trends*, not to 0.1 °C.

**E4 · T2 (mid-column) is intrinsically noisy.**
CoV 29 % across the three runs — it sits in the flickering plume/entrainment
boundary. It carries a large experimental band by nature and is not a modelling
target.

**E5 · Record lengths differ 2× (546–941 s).**
Only R3 captures the full burn to decay; R1 stops near the broad peak. Late-time
(> 550 s) behaviour rests on R3 alone.

**E6 · R3 ran cooler** (plume peak 126 °C vs 137 °C).
A weaker candle set or wax depletion within the record. The plume peak is a band
(≈ 110–137 °C), not a point — consistent with the cone-side 16.5–20 W spread.

**E7 · Ignition anchor ± 2 s** (IGNITION_ANCHOR.md). The `event_number` clock is
not common between runs; alignment is by thermal onset cross-checked to the
nearest transition.

**E8 · Cone: the single-candle side is not three replicates.**
It is one matched burn (1cand_R3) + one long-protocol rate cross-check
(1cand_long, O₂ disqualified) + one short partial (1cand_R2). Only the 3-candle
side has three genuine repeats. The anchor run 1cand_R3 lost only 1.6 g (14 % of
the tea light) and did not reach full steady state — its 20.0 W may slightly
over-read (steady-window fit gives 19.1 W).

**E9 · Oxygen-consumption calorimetry is unusable at this scale.**
Whole-run O₂ depletion is 0.01–0.03 % absolute; the O₂→kW result overshoots the
mass-loss HRR by ~3× and scatters 2–3× between runs. Used for ignition/flameout
*timing* only. Carried as the ± 15–20 % source-term uncertainty.

**E10 · Fog is a seeded passive tracer, not candle soot**, and its injection
rate was not recorded. The smoke comparison is transport shape and timing only —
never concentration, optical density, or soot yield.

---

## Numerical

**N1 · D\*/δx ≤ 8 everywhere.**
D\*(18 W) = 1.21 cm. The finest run (1.5 mm) reaches only D\*/δx ≈ 8; the
FDS-recommended 10–16 needs ≈ 1.2 mm over the whole plume (~90 M cells), out of
scope. T3 is reported as grid-sensitive, not converged — a ± 3 °C mesh-scatter
band on the *resolved* value.

**N2 · T3 does not form a monotone Richardson sequence** (35 s: 23.7 → 14.1 →
20.0 across 10/5/2/1.5 mm). No formal GCI at this resolution.

**N3 · Fine-mesh comparison is time-bounded.**
2.0 mm reached 150 s, 1.5 mm 65 s, 5 mm (P04 local) 35 s. The four-point
resolution ladder exists only at t = 35 s. The M3 sweep extends 5 mm and a 2 mm
run to 350–410 s, but the *finest* meshes do not reach the wall-heating regime.

**N4 · One primary FDS run per configuration.**
No LES ensemble; run-to-run solver scatter at this near-laminar scale is not
quantified.

**N5 · The M3 sweep is 5 mm** (D\*/δx = 2.4).
Its deltas and trends are robust (they are ratios of effects) but the absolute
endpoints of the wall bracket [+16, +60] °C are 5 mm values carrying ~± 5 °C
mesh noise.

**N6 · `m2_base_nest20_450` stopped at 417 s** (48 h wall clock), not 450 s. T3
was flat from 60 s; a checkpointed restart would not change the finding.

**N7 · The 2-way / 4×1×2 mesh splits** were required for MPI performance; the
LAYER HEIGHT devices constrain where the z-split can fall (must keep the
0–0.23 m column in one mesh).

---

## Model

**M1 · Prescribed-HRR source, not pyrolysis.**
The fire power is imposed from the cone data (18 W ± 15–20 %). The model has no
flame chemistry, so the luminous reaction zone — which T1 and T2 sit in — is
outside its representation *by construction*. This is why T1/T2 worsen with mesh
refinement (the prescribed-HRR plume narrows) and cannot be fixed at any
resolution. **Do not tune the source to close the T1/T2 gap.**

**M2 · The wall thermal boundary is the T3 residual.**
The modelled 10 mm opaque cast PMMA is ~2× too strong a heat sink (SENSITIVITY
§2). The three candidate causes — acrylic modelled as grey-opaque when it is
semi-IR-transparent, an air gap above the ceiling slab, imperfect panel contact
— are **not yet separated**. The M4 wall-variant sweep (running) tests them;
until it lands, T3 is a bracket [+16, +60] °C, not a single value.

**M3 · Sealed-box pressurisation is unvalidated.**
`p_box` rises 180–380 Pa (PMMA cases) and runs away to ~12.8 kPa (adiabatic
bracket), still climbing at the end of every run. No pressure or load-cell
channel survived in the experiment to check it. The adiabatic case is used only
as the no-heat-sink bracket, never as a candidate model.

**M4 · Near-fire geometry uncertainty dominates T1/T2 regardless of the model.**
In a ~100 °C/cm gradient, the ± few-mm uncertainty in the physical candle and
probe positions swamps any model comparison at x = 0.12 m. T1/T2 are not a
usable validation target for this configuration.

**M5 · Wall properties are a single default set** (k = 0.19 W/mK, ρc = 1.7
MJ/m³K, ε = 0.90). Not measured for the actual acrylic; the cast-PMMA datasheet
range is only ~± 5 %, so this is a minor contributor next to M2's structural
issues (opacity, air gap, contact).

**M6 · The ceiling and doorway-wall OBSTs** carry a fixed-temperature or
insulated backing, not the actual plenum gas temperature. Immaterial for the
150–350 s runs (heat penetrates only ~6 mm of the 10 mm slab) but would matter
for much longer runs.

**M7 · The tracer's early stratification transient (t < 60 s) is unobservable.**
The video cannot see the fog until t ≈ +150 s, by which point the model is
already near-uniform. The "hot fog released at the plume base marks the thermal
layer" assumption is plausible but unverified for the first minute.
