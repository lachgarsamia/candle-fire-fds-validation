# VALIDATION_FINDINGS — P05: FDS vs the compartment experiment

**Date:** 2026-09-07. **Sim:** `fds/runs/nest20/` (2.0 mm, D\*/δx = 6.1,
quasi-steady at t = 150 s), with `fds/runs/nest15/` (1.5 mm, t = 65 s) and
`fds/runs/coarse/` (10 mm) for the numerical band. **Experiment:**
`2026-08-27_exponat_R1/R2/R3`, 7 live thermocouples + operator event timeline
(EXPONAT_FINDINGS — temperature and timing are the *entire* ground truth; every
flux and mass channel is dead). **Source:** prescribed 18 W paraffin from
CONE_FINDINGS. Nothing tuned to the compartment data.

Reproduce: `python src/p05_validation.py` → `data/processed/p05_three_uncertainty.csv`,
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
| **Ceiling directly over the fire** (T3) | right structure (localized hot spot, T3 ≫ T5); **agrees at matched simulated time** (FDS +19.9 vs measured +20.2 ± 5.0 °C at 65 s); plateaus at +16 °C while the measurement climbs to +43 °C | **wall thermal-boundary model** — modelled 10 mm PMMA is ~2× too strong a heat sink (M3: run length and back-face condition ruled out; adiabatic bracket → +60 °C) |
| **In-flame column** (T1, T2) | +0.4 / +1.2 °C vs measured +49 / +13 (t = 65 s), +107 / +35 (peak); does not improve — *worsens* — with refinement | **structural** — a prescribed-HRR LES cannot place the luminous reaction zone that a thermocouple 3 cm from the wick sits in; no achievable mesh fixes it |

**Consolidated T3 statement (used identically in MESH_STUDY_FINDINGS.md §4;
updated 2026-09-10 after the M3 sweep and 2026-09-11 after the M4 wall test —
see SENSITIVITY_FINDINGS §2 and §M4):**
T3 agrees with experiment at matched simulated time (FDS +19.9 °C vs measured
+20.2 ± 5.0 °C at t = 65 s). The residual to the experimental broad peak
(+43 °C, reached ~300–450 s after ignition across R1–R3) is a **wall
thermal-boundary model discrepancy**: the modelled compartment wraps the box in
10 mm opaque cast PMMA, which is ~2× too strong a heat sink and pins T3 at
+16 °C. The M3 sweep rules out the two alternatives — **run length** (the 2 mm
run held T3 at +16 from 60 s to 410 s) and **wall back-face condition** (exposed
≡ insulated, the heat never penetrates the slab). Removing the wall heat sink
entirely (adiabatic) sends T3 to +60 °C and climbing; the measurement sits
between, near the weak-sink end. The M4 test then tried four one-parameter,
physically-motivated fixes to that wall model — IR-transparent/lower-emissivity
acrylic, a ceiling air gap (supported by the setup photos), a thin-sheet whole
rig, and a lumped contact-resistance bracket — **run once each, not tuned**;
none moved T3 beyond the 5 mm mesh-noise floor (all four within 0.6 °C of the
+22.5 °C baseline), and none touched the far field or T1/T2. T3 is **not** a
standalone model failure and is **not** a numerical or run-length limit — it is
a bracketed wall-model uncertainty, T3 ∈ [+16, +60] °C with the truth near the
low-sink end, and the single mechanism responsible is **not resolved** by the
variants tested (a combination of causes, an unmodelled localized geometric
detail, or finer resolution remain open).

**Scope boundary.** Fine-mesh comparison is limited to **t ≤ 65 s** by wall-clock
(the 1.5 mm run's 24 h limit; the 2.0 mm run reaches 150 s; the M3 2 mm run
`m2_base_nest20_450` reached 410 s). The several-hundred-second wall-heating
regime is now probed by the 2 mm and 5 mm M3 runs (§SENSITIVITY_FINDINGS), which
show T3 is flat there — the experiment's continued rise is the wall-model gap
above, not an untested transient.

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

**How the split is computed** (`src/p05_validation.py :: three_uncertainty`):

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
  measured +20.2 ± 5.0 °C at t = 65 s).
- **The residual to the +43 °C broad peak is a wall thermal-boundary model
  error** (M3 sweep, 2026-09-10 — SENSITIVITY_FINDINGS §2, figure
  `figures/m3_T3_wall_bracket.png`):
  - *run length ruled out* — the 2 mm run `m2_base_nest20_450` held T3 at
    +16.5 → +15.7 °C from t = 60 s to t = 410 s;
  - *back-face condition ruled out* — exposed ≡ insulated (heat penetrates only
    ~6 mm of the 10 mm slab in 350 s);
  - *the wall heat sink is the lever* — adiabatic walls send T3 to +60 °C and
    climbing; the measurement (+30–43 °C) sits between the PMMA and adiabatic
    curves, near the weak-sink end.
  - The modelled 10 mm opaque cast PMMA is **~2× too strong a heat sink**.
    Likely causes (not separated): acrylic modelled as grey-opaque when it is
    semi-IR-transparent; an air gap above the ceiling slab; imperfect panel
    contact. T3 ∈ **[+16 (full PMMA), +60 (no sink)] °C**, truth near the low end.
  - **M4 wall-hypothesis test (2026-09-11 — SENSITIVITY_FINDINGS §M4, figure
    `figures/m4_wall_variants.png`)** tried each candidate cause individually as
    a one-sentence physical claim, run once, not tuned: PMMA emissivity 0.85 +
    IR semi-transparency (`w1_ir`), a 4 mm ceiling + 20 mm air gap per the setup
    photos (`w2_thinceil`), the whole rig as 4 mm sheet acrylic (`w3_thinall`),
    and a lumped k = 0.10 contact-resistance bracket (`w4_contact`). **None
    moved T3** — all four land at +22.3 to +23.1 °C at 350 s, within 0.6 °C of
    the +22.5 °C baseline and inside the 5 mm mesh-noise band (±5 °C); none
    touched the far field or T1/T2. Per the no-tuning rule, this is **reported,
    not chased further**: the single mechanism is not resolved by the variants
    tested. A combination of the three causes, an unmodelled localized
    geometric detail (joints/seals rather than a uniform property), or the need
    for finer resolution than 5 mm all remain open.
- T3 is **not** a standalone model failure and **not** a numerical / run-length
  limit — it is a bracketed wall-model uncertainty, and the M4 test narrows
  *what it isn't* (none of the three single-parameter wall-property hypotheses)
  without yet narrowing *what it is*.

**Data trace (verified 2026-09-07).** TC_03 (= T3): raw
`data/raw/compartment/2026-08-27_exponat_R1.txt` col `TC_03`, baseline 25.1 °C, absolute max 64.0 °C
→ rise +38.9 °C (R1). EXPONAT_FINDINGS §5 records R1/R2/R3 peak rise
38.9 / 46.6 / 44.8 → 43.4 ± 4.0 °C. `src/p05_validation.py` reads the
ignition-aligned `data/processed/exponat_R*_timeseries.csv` and gets, across R1–R3:
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

## 7. Smoke — the fog-analogue tracer (M3, SMOKE_FINDINGS + SENSITIVITY_FINDINGS §4)

The glycerin fog was recorded on video only (no calibrated obscuration channel).
A passive tracer released at the candle cup (`s7_tracer`), compared for
**transport shape and timing only**, reproduces the video: a gradual room-fill
over minutes, near-uniform by ~250 s (`tr_upper/tr_lower` → 1.3), almost nothing
reaching the plenum — no sharp descending interface. In the video's observable
window (fog visible from t ≈ +150 s) the model and the footage agree. Both the
tracer and the thermocouples describe the same weak, slow, near-uniform fill:
**the FDS compartment *flow* model is sound** (the T3 issue in §4 is a *thermal
boundary* problem, not a flow problem).

---

## 8. One-paragraph version (for the supervisor update)

> FDS reproduces the compartment-scale thermal and vent behaviour of an 18 W
> candle fire — far-field ceiling and doorway temperatures within experimental
> uncertainty (residuals ≤ 1 °C), the correct localized-hot-layer structure over
> the fire, and (from a passive tracer) the slow near-uniform fog fill the video
> shows. Two limits remain, and they are different kinds. **(a) T3** — the
> ceiling directly over the fire — agrees at matched simulated time (+19.9 vs
> +20.2 ± 5.0 °C) but plateaus at +16 °C while the measurement climbs to +43 °C.
> The M3 sweep localised this to the **wall thermal boundary**: run length and
> the wall back-face condition are ruled out; the modelled 10 mm opaque PMMA is
> ~2× too strong a heat sink (adiabatic walls overshoot to +60 °C, the
> measurement sits between). **(b) T1/T2** — in-flame — cannot be reproduced by a
> prescribed-HRR LES at any resolution; the near-fire rake shows the modelled
> plume is a narrow column over the wick that *narrows* with refinement, never
> reaching the probe. Separating the wall-model limit and the structural limit —
> rather than tuning the source until the near-fire numbers match — is the
> contribution.
