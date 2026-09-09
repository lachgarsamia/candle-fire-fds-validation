# A tea-light fire, measured and simulated — summary

*Supervisor-facing synthesis, 2026-09-07. Detail and data traces are in
CONE_FINDINGS.md, EXPONAT_FINDINGS.md, MESH_STUDY_FINDINGS.md and
VALIDATION_FINDINGS.md; this document does not re-derive them.*

---

## Abstract

A single tea-light was characterized from cone-calorimeter tests as a
free-burning ≈ 18 W paraffin source, anchored on manually weighed mass loss
because oxygen-consumption calorimetry is not trustworthy at this scale. The same
candle was then run in a small sealed compartment instrumented with seven
thermocouples, which showed a hot, repeatable buoyant plume, a shallow hot layer
localized directly over the fire, and a weak but clearly ordered doorway
stratification. An FDS model built entirely from the cone source term and the
measured geometry — with nothing tuned to the compartment data — reproduces the
far-field ceiling and doorway temperatures to within about 1 °C and captures the
localized-hot-layer structure. Two discrepancies near the fire remain, and the
mesh study shows they are *different* problems: the ceiling temperature over the
fire is limited by affordable grid resolution, while the in-flame thermocouple is
outside what a prescribed-heat-release model can represent at any resolution.

---

## 1. The fire source (Phase 01)

The cone data give a consistent, transferable number in one specific form: a
steady mean heat-release rate per candle. A tea-light burns at a constant rate —
a straight-line fit of mass against time has r² > 0.999 over every burn — so a
steady mean is the correct representation, not a curve. Taking that mass-loss
rate with an assumed effective heat of combustion (paraffin 42 MJ/kg, combustion
efficiency 0.85–1.0), the single-candle anchor is 20 W and the three-candle runs
give 16.5–19.5 W per candle; the combined working value carried into the
simulation is **18 ± 2 W per candle** (≈ 17 kW/m² over the 37 mm cup).

Oxygen-consumption calorimetry was not usable. Whole-run O₂ depletion is only
0.01–0.03 % absolute — the channel *detects* ignition and flameout but its
conversion to kW overshoots the mass-loss result by roughly 3× and scatters by
a factor of two to three between runs, because the instrument's calibration
constants are meant for 1–50 kW fires, not a 20 W one. The implied heat of
combustion from the O₂ energy scatters across 25–110 MJ/kg, an order of magnitude
wider than the wax uncertainty, so it cannot pin that quantity either. This
disagreement is documented, not tuned away: every downstream heat-release number
carries a **±15–20 %** source uncertainty from the combustion-efficiency range
and the run-to-run spread. Three candles together produce about 2.7× one
candle's output, so a multi-candle case is modelled as separate burners rather
than one scaled source.

## 2. Compartment thermal structure (Phase 02)

Seven of the compartment's forty thermocouple channels were live; every
heat-flux gauge and the compartment load cell returned sentinel values, so the
experimental ground truth is temperature histories plus an operator event
timeline. Within that limit the picture is clear and repeatable across three
runs (6 % coefficient of variation on the plume peak):

- **A hot, localized plume.** The thermocouple just above the wick rises
  107 ± 7 °C above ambient. The compartment never reaches steady state — every
  channel shows a slow rise to a broad maximum several hundred seconds after
  ignition, then a gentle decline.
- **A shallow hot layer that hugs the fire.** The ceiling thermocouple directly
  over the plume rises about 43 °C; an identical sensor at the ceiling 23 cm away
  rises only about 5 °C. The horizontal temperature difference along the ceiling
  is ≈ 41 °C — the room is *not* well mixed, and any model that produces a
  uniform upper layer is wrong for this compartment.
- **A weak, well-ordered doorway vent flow.** The three doorway sensors are
  monotonic by height in every run: floor undisturbed, top about 5 °C above
  ambient (warm outflow), neutral plane low in the opening.
- **A non-monotonic back-wall column** — plume root ≫ ceiling > mid-height —
  because the mid-height sensor sits above the short flame but below the ceiling
  jet.

Ignition timing is recoverable to about ±2 s: the thermal onset falls within
1–2 s of one operator event transition (the candle-lighting step), which gives
a per-run alignment anchor even though the event clock is not common between
runs.

## 3. FDS validation verdict (Phases 03–05)

The model is a sealed acrylic box with the measured geometry, an 18 W prescribed
heat-release source with a 25 s ignition ramp, and thermocouple probes at the
seven measured positions. Nothing was adjusted to match the compartment data. A
mesh study was run at four near-fire resolutions (10, 5, 2.0, 1.5 mm); the 2.0 mm
run reached quasi-steady at 150 s, the 1.5 mm run reached 65 s before its
wall-clock limit, so fine-mesh comparison is bounded to **t ≤ 65 s** and the
several-hundred-second wall-heating regime is not tested. The delivered fire
power is conserved exactly on every mesh.

**Far-field ceiling and doorway (four sensors): validated.** After accounting for
experimental scatter and the mesh-to-mesh spread, the unexplained residual is
≤ 1 °C at every one of these sensors, and the model reproduces the doorway
stratification order and sign. The coarsest mesh fails here only because it
cannot sustain the plume at all.

**Ceiling directly over the fire: agrees at matched time, with a carried
numerical band.** At t = 65 s the model gives +19.9 °C against a measured
+20.2 ± 5.0 °C. The measurement then continues to climb to a broad peak of about
+43 °C several hundred seconds later, as the acrylic walls store heat over a
timescale the 150 s runs do not reach; a smaller part of that gap is that even
the finest mesh is below the resolution FDS recommends for a fire this small
(which would need on the order of 90 million cells). These two contributions
cannot be cleanly separated with the runs in hand, so a **±3 °C numerical band**
is carried and this sensor is *not* treated as a standalone model failure.
→ *see* `figures/p05_T3_convergence.png`.

**In-flame column (two sensors): a structural limit of the model.** The model
gives +0.4 to +1.2 °C where the experiment measures +49 °C (at 65 s) rising to
+107 °C. Refining the mesh makes this *worse*: a rake of probes around the candle
shows the modelled plume is a narrow hot column locked over the wick — about
+166 °C at 2.0 mm, +210 °C and *narrower* at 1.5 mm — that decays to ambient
within about 1.5 cm and never reaches the thermocouple 3 cm away. A
prescribed-heat-release LES has no flame chemistry and no luminous
soot-radiation field, so a bare bead that in reality sees the flame directly is
outside the model's representation. In addition, the ~100 °C/cm gradient here
makes the comparison dominated by millimetre-scale uncertainty in the candle and
probe positions. These two sensors are not a usable validation target for this
configuration.
→ *see* `figures/p05_T1_nearfield.png`.

The central result is that these last two discrepancies, which look identical in
a raw simulation-versus-experiment table, are distinct: one closes with
resolution and run time, the other does not close at all. Separating them —
rather than tuning the source until the near-fire numbers agree — is the
contribution.

## 4. Future work

- **Smoke comparison.** The glycerin-fog visualisation was recorded on video
  only, with no calibrated obscuration channel. The deck already writes soot and
  heat-release-rate slices, so a qualitative layer-height and descent-rate
  comparison against the video is feasible. It cannot change the
  numerical-versus-structural conclusion and is not a reason to hold the
  write-up.
- **1.5 mm run to quasi-steady.** The finest mesh stopped at 65 s. A restart to
  150 s (or longer) would tighten the T3 numerical band and give a genuine
  four-point resolution ladder at a common time; the conclusions do not depend
  on it.
- **Longer runs into the wall-heating regime.** Reaching the experiment's
  several-hundred-second broad peak would let the wall-thermal-mass and
  resolution contributions to the T3 gap be separated rather than bounded
  together.
- **A pyrolysis source instead of prescribed heat release.** Modelling the wax
  evaporation and a finite-rate flame would be the only route to representing
  the reaction zone that the in-flame thermocouples sit in — a substantially
  larger modelling effort, and the natural next study rather than a fix to this
  one.
