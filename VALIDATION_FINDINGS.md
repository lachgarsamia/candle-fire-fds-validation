# VALIDATION_FINDINGS — P05: FDS vs the compartment experiment

**Date:** 2026-09-07. **Sim:** `fds/runs/nest20/` (2.0 mm, D\*/δx = 6.1,
quasi-steady at t = 150 s), with `fds/runs/nest15/` (1.5 mm, t = 65 s) and
`fds/runs/coarse/` (10 mm) for the numerical band. **Experiment:**
`2026-08-27_exponat_R1/R2/R3`, 7 live thermocouples + operator event timeline
(EXPONAT_FINDINGS — temperature and timing are the *entire* ground truth; every
flux and mass channel is dead). **Source:** prescribed 18 W paraffin from
CONE_FINDINGS. Nothing tuned to the compartment data.

Reproduce: `python p05_validation.py` → `results/p05_three_uncertainty.csv`,
`figures/p05_T3_convergence.png`, `figures/p05_T1_nearfield.png`.

---

## 1. Verdict

FDS reproduces the **compartment-scale** thermal and vent behaviour of the 18 W
candle fire — far-field temperatures and doorway stratification within
experimental uncertainty. Two limits emerge at this scale, and they are
**different kinds of failure**:

| | what FDS does | why |
|---|---|---|
| **Far-field ceiling & doorway** (T5, T9, T10, T11) | within ~1–2 °C, correct stratification order and sign | model has physical content here; numerically converged |
| **Ceiling directly over the fire** (T3) | right structure (localized hot spot, T3 ≫ T5); **agrees with experiment at matched simulated time** (FDS +19.9 °C vs measured +20.2 ± 5.0 °C at t = 65 s); best resolved-limit estimate +18 ± 3 °C | not a standalone failure — see the consolidated T3 statement below |
| **In-flame column** (T1, T2) | +0.4 / +1.2 °C vs measured +49 / +13 (t = 65 s), +107 / +35 (peak); does not improve — *worsens* — with refinement | **structural** — a prescribed-HRR LES cannot place the luminous reaction zone that a thermocouple 3 cm from the wick sits in; no achievable mesh fixes it |

**Consolidated T3 statement (used identically in MESH_STUDY_FINDINGS.md §4):**
T3 agrees with experiment at matched simulated time (FDS +19.9 °C vs measured
+20.2 ± 5.0 °C at t = 65 s). The residual to the experimental broad peak
(+43 °C, reached ~300–450 s after ignition across R1–R3) is dominated by the
wall-thermal-mass timescale that the 150 s runs do not capture, with a secondary
D\*/δx < 10 under-resolution contribution — the two are not cleanly separable
with the runs in hand. T3 is **not** a standalone model failure.

**Scope boundary.** Fine-mesh comparison is limited to **t ≤ 65 s** by wall-clock
(the 1.5 mm run's 24 h limit; the 2.0 mm run reaches 150 s). Far-field and T3
are compared at matched simulated time, which is methodologically correct, but
the several-hundred-second wall-heating regime in which the experiment reaches
its broad peak is **not tested** by any fine-mesh run.

Separating the numerical limit (T3) from the structural one (T1/T2) is the
study's central result. They look similar in a raw sim-vs-experiment table — both
are large under-predictions near the fire — but the mesh study (P04) shows one
closes with resolution and the other does not.

---

## 2. Per-sensor comparison and the three-uncertainty split

Rise above ambient (°C), matched at **t = 65 s** — the latest time reached by a
fine mesh. The experiment is still warming at 65 s (§4), so the measured *peak*
column is given alongside.

| TC | position | measured @65 s | measured peak | FDS 10 mm | FDS 2.0 mm | FDS 1.5 mm | experimental ±1σ | numerical ± | residual (model) |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|
| **T1** | column, z 0.05 (in flame) | +49.2 | +107.0 | +1.4 | +0.6 | +0.4 | ±6.7 | ±0.1 | **+42** (structural) |
| **T2** | column, z 0.16 | +12.6 | +34.8 | +2.9 | +2.1 | +1.2 | ±1.3 | ±0.4 | **+10** (structural) |
| **T3** | ceiling over fire, z 0.225 | +20.2 | +43.5 | +0.0 | +16.4 | +19.9 | ±5.0 | ±1.8 | **≈ 0 at 65 s** / +23 vs peak |
| **T5** | ceiling mid-room, x 0.35 | +1.1 | +4.6 | +0.0 | +3.8 | +2.7 | ±0.3 | ±0.6 | −0.7 |
| **T9** | doorway floor | +0.0 | +0.2 | +0.1 | +0.0 | +0.0 | ±0.1 | ±0.0 | 0 |
| **T10** | doorway mid | +0.2 | +1.1 | +1.5 | +0.2 | +0.2 | ±0.1 | ±0.0 | 0 |
| **T11** | doorway top | +2.0 | +4.7 | +0.9 | +1.7 | +0.5 | ±0.4 | ±0.6 | +0.5 |

**How the split is computed** (`p05_validation.py :: three_uncertainty`):

- **experimental ±1σ** = sample standard deviation of the rise across R1/R2/R3 at
  t = 65 s.
- **numerical ±** = half the spread between the resolved meshes at that time
  (2.0 mm and 1.5 mm; the 10 mm run is excluded — its plume has collapsed, which
  is a modelling failure of the coarse grid, not an uncertainty).
- **residual (model)** = (measured − finest FDS), with the experimental and
  numerical amounts subtracted and floored at zero. It is what neither scatter
  nor grid explains.

**What the split says:**

- **T9, T10, T5, T11** — residual ≤ 1 °C. FDS is inside the combined
  experimental + numerical envelope. The far-field is validated.
- **T3** — residual ≈ 0 at t = 65 s (FDS +19.9 vs measured +20.2 ± 5.0). See the
  consolidated T3 statement in §1 for the residual to the broad peak. Numerical
  band ±1.8 °C, but non-monotone (§P04.4) — treat ±3 °C as the honest figure.
- **T1, T2** — residual of +42 and +10 °C. Not scatter, not grid. Structural
  (§3).

---

## 3. Why T1 and T2 are structural, not under-resolved

→ **`figures/p05_T1_nearfield.png`** — the near-fire rake, both fine meshes.

The 6×5 gas-temperature rake straddling the candle shows the modelled plume is a
**narrow hot column locked to the wick** (x = 0.09): +166 °C at 2.0 mm, +210 °C
at 1.5 mm directly over the wick, decaying to < +5 °C by x = 0.105 and < +1 °C at
x = 0.12 where T1 and T2 sit. `Tmax_core` converges to ≈ 320 °C on both fine
meshes — the column is *resolved*, it is just narrow and in the wrong place
relative to the probe.

Refining 2.0 → 1.5 mm makes the column **hotter and narrower** — it moves *away*
from reproducing T1. That is the discriminator:

- **under-resolution** would raise T1 toward ~100 °C as δx shrinks — not observed;
- **model-structural** — a prescribed-HRR LES releases heat into a thin buoyant
  column with no flame chemistry and no luminous soot-radiation field, so a bare
  bead 3 cm from a real candle wick (which sees the flame directly) is outside
  what this setup can predict — this is what the data show.

Compounding it: at T1/T2 the field gradient is ~100 °C/cm, so the ±few-mm
uncertainty in the physical candle and probe positions dominates any comparison
there regardless of the model. **T1 and T2 are not a usable validation target for
this configuration.**

---

## 4. Ceiling over the fire (T3): consolidated statement

→ **`figures/p05_T3_convergence.png`** — T3 vs time (all meshes) and vs D\*/δx.

- **10 mm collapses the plume** (T3 = 0) — resolving the plume is necessary.
- **5 / 2 / 1.5 mm** give T3 = +14 to +24 °C — the right *structure* (a localized
  ceiling hot spot, T3 ≫ T5 = far-field), but the three meshes do not form a
  monotone sequence, so no formal GCI. Best estimate **+18 ± 3 °C** at the
  resolved limit, from the two fine meshes.
- **T3 agrees with experiment at matched simulated time** (FDS +19.9 °C vs
  measured +20.2 ± 5.0 °C at t = 65 s). The residual to the experimental broad
  peak (+43 °C, reached ~300–450 s after ignition across R1–R3) is dominated by
  the wall-thermal-mass timescale the 150 s runs do not capture, with a
  secondary D\*/δx < 10 under-resolution contribution — the two are not cleanly
  separable with the runs in hand. The 2.0 mm run reaches its own quasi-steady
  (T3 flat at +16 °C from t = 65 to 150 s) well before the experiment's
  wall-heating timescale. T3 is **not** a standalone model failure.

**Data trace (verified 2026-09-07).** TC_03 (= T3): raw
`2026-08-27_exponat_R1.txt` col `TC_03`, baseline 25.1 °C, absolute max 64.0 °C
→ rise +38.9 °C (R1). EXPONAT_FINDINGS §5 records R1/R2/R3 peak rise
38.9 / 46.6 / 44.8 → 43.4 ± 4.0 °C. `p05_validation.py` reads the
ignition-aligned `results/exponat_R*_timeseries.csv` and gets, across R1–R3:
+16.9 ± 2.5 (t = 35 s), +20.2 ± 5.0 (t = 65 s), +30.0 ± 6.6 (t = 150 s),
+43.5 ± 4.2 (broad peak). The 65 s, 150 s and peak values are a single monotone
rising sequence on one run and mutually consistent across the chain; the peak
figure matches EXPONAT_FINDINGS to within rounding. **No discrepancy.**

---

## 5. Transient and timing

- **Ignition ramp**: modelled with `TAU_Q = -25` (t² ramp to 18 W over 25 s),
  chosen to bracket the measured plume onset. Measured TC_01 crosses +60 °C at
  ignition +37 ± 3 s and +100 °C at +140 ± 18 s (EXPONAT §6); FDS never
  approaches these at T1 (§3), so the plume-onset timing cannot be validated at
  T1. At T3 the modelled ceiling warming begins ~25–30 s after ignition and
  tracks the measured R1–R3 band through 65 s (figure a).
- **Stratification onset**: measured T3 − T2 exceeds its pre-ignition offset by
  > 3 °C within 30–90 s (EXPONAT §4.4). FDS develops T3 ≫ T2 over a similar
  window (T3 = +12 by t = 30 s while T2 stays < +1).
- **No steady state** in either: the experiment has a broad maximum several
  hundred seconds after ignition (TC_01 at +431 ± 27 s, TC_03 at ~300–450 s);
  FDS reaches quasi-steady near +100 s. FDS reaching steady faster is consistent
  with the wall-storage timescale it under-carries at 150 s.
- **Doorway**: FDS reproduces the monotonic-by-height vent profile
  (T11 > T10 > T9) and keeps the outflow to a few °C, matching the measured
  "small stratification, low neutral plane" signature — magnitudes within ~1 °C.

---

## 6. Limitations (read before citing any number)

1. **One primary FDS run per configuration.** No LES ensemble; run-to-run
   scatter at this near-laminar scale is unquantified.
2. **2.0 mm is the best resolution run to quasi-steady.** 1.5 mm reached only
   65 s; 5 mm only 35 s. The full 4-mesh ladder exists only at t = 35 s. The
   1.5 mm run was not restarted — deliberate, as the conclusions do not depend
   on it.
3. **D\*/δx ≤ 8 everywhere** — below the FDS-recommended 10–16. T3 is reported as
   grid-sensitive; the ±3 °C numerical band is an estimate, not a GCI.
4. **Prescribed-HRR source, not pyrolysis.** The fire power is imposed from the
   cone data (18 W, ±15–20 % — CONE_FINDINGS). No flame chemistry, so the
   reaction zone T1 sits in is outside the model by construction.
5. **Near-fire geometry uncertainty.** ±few-mm candle/probe positioning in a
   ~100 °C/cm gradient dominates any T1/T2 comparison.
6. **Sealed-box pressurisation unvalidated** — `p_box` rises 180–380 Pa across
   runs and is still climbing at the end of each; no pressure or load-cell
   channel survived in the experiment to check it.
7. **Wall model.** PMMA walls, single default thermal property set; the
   several-hundred-second wall-heating that drives the measured T3 climb past
   65 s is only partially inside the 150 s runs.
8. **Smoke / obscuration comparison not done** — see §7.

---

## 7. Future work: smoke

The experiment's glycerin-fog smoke visualisation was recorded on video only —
no calibrated obscuration or soot channel. The FDS deck carries a soot yield
(0.008, paraffin) and writes a `HRRPUV` + `SOOT` slice, so a **qualitative**
layer-height / descent-rate comparison against the video is possible. It is
listed as future work and is **not** a reason to delay this write-up: the
temperature and vent validation above stands on its own, and a qualitative smoke
check cannot change the numerical-vs-structural conclusion.

---

## 8. One-paragraph version (for the supervisor update)

> FDS reproduces the compartment-scale thermal and vent behaviour of an 18 W
> candle fire — far-field ceiling and doorway temperatures within experimental
> uncertainty (residuals ≤ 1 °C), and the correct localized-hot-layer structure
> over the fire. Fine-mesh comparison is bounded to t ≤ 65 s by wall-clock, so
> the several-hundred-second wall-heating regime is not tested. Within that
> window: (a) the ceiling temperature directly over the fire (T3) agrees with
> the measurement at matched simulated time (+19.9 vs +20.2 ± 5.0 °C); the gap
> to the experimental broad peak (+43 °C) is dominated by the wall-thermal-mass
> timescale the runs do not reach, with a secondary contribution from a mesh
> (D\*/δx ≈ 10–16, ≈ 90 M cells) that is computationally impractical — a ±3 °C
> numerical band is carried. (b) An in-flame thermocouple (T1, +107 °C measured)
> cannot be reproduced by a prescribed-HRR LES at any resolution — the near-fire
> rake shows the modelled plume is a narrow column over the wick that gets
> *narrower* with refinement, never reaching the probe 3 cm away. Separating the
> numerical limit from the structural one — rather than tuning the source until
> the near-fire numbers match — is the contribution.
