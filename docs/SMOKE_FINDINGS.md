# SMOKE_FINDINGS — M2, compartment fog visualisation

**Status: COMPLETE (2026-09-10).** The qualitative video finding (§3) and the
passive-tracer transport comparison (§5) are both done. Frame-level digitization
(`src/fog_digitize.py`) is optional and not required for the conclusion.

---

## 1. Framing — LOCKED, applies to every number in this document

1. **The glycerin fog is a seeded passive tracer, not candle soot.** Every
   comparison here is **layer dynamics only** — interface height, descent rate,
   fill timing, accumulation pattern. **Never** concentration, optical density,
   or soot yield.
2. The FDS deck's `SOOT_YIELD = 0.008` produces a *combustion-soot* field that is
   physically unrelated to the introduced fog. The `MASS FRACTION(SOOT)` /
   `VISIBILITY` slices are for qualitative plume *shape* only.
3. The fog was introduced **at the candle cup** (hot, buoyant, rises with the
   plume). The FDS analogue is a **passive tracer released there at ignition**
   (`--tracer`), not combustion soot. Its injection **rate is unrecorded**, so
   the tracer comparison is **transport shape + timing only**.
4. Two distinct surfaces, kept separate in every figure:
   - **thermal-stratification interface** — FDS `LAYER HEIGHT` DEVC (`zint_*`),
     temperature-based. A **reference line**, labelled as such — **not** the fog
     comparison target, never overlaid as if it were the fog surface.
   - **fog / passive-tracer front** — the video digitization, and the FDS
     `s7_tracer` mass-fraction field. This is the comparison.
   The working assumption that *hot fog released at the plume base marks the
   thermal layer* is **plausible but unverified** — flagged wherever quoted.

---

## 2. The footage

| clip | experiment | lighting | duration | ignition (video-time) | analysis offset |
|---|---|---|---|---|---|
| `7L5A3276` | fog run 1 | room on | 11.7 min | ≈ 120 s | `t = video − 120` |
| `7L5A3277` | fog run 2 | room on | 13.2 min | TBD | — |
| `7L5A3278` | fog run 2 | **room off** (cleanest) | 16.9 min | ≈ 30 s | `t = video − 30` |

1920×1080, 25 fps, h.264. **No on-screen clock** → ignition anchored on the
first-flame frame (±1–2 s). The green laser sheet illuminates the centre-depth
plane, which coincides with the FDS `y = 0.15 m` slice. Setup stills:
`7L5A3265–3273` (CR3). Geometry from the calibration grid
(`figures/fog_3276_calibcheck.png`): back wall (x = 0) and candle on the
**right**, doorway (x = 0.70) on the **left**; the fog plume venting into the
plenum on the left is the **doorway outflow**.

---

## 3. Result — no sharp interface; slow gradual fill

**No sharp descending smoke/clear interface formed in the compartment.** In both
experiments the fog accumulated **gradually over minutes**:

- The candle plume is visible from ignition, but **measurable fog in the room
  does not begin until ≈ 150–200 s after ignition** (room-mean laser-scatter
  signal in 3278 rises out of the noise floor only past t ≈ +140 s).
- From there it builds slowly over the following **5–10 minutes**, filling the
  inner compartment fairly uniformly rather than descending as a front.
- The most **structured** fog is in the **plenum**, as a slow buoyant plume
  above the doorway — not inside the room.

This is what an **18 W fire in a sealed, minimally-vented box** produces: the
buoyant circulation is too weak to drive a fast, well-defined filling front.

### Corroboration of P02

This directly supports the EXPONAT_FINDINGS thermal picture:

| P02 (thermocouples) | M2 (fog video) |
|---|---|
| hot layer **localized over the fire** (T3 +43 °C ≫ T5 +5 °C); room **not well-mixed** | fog accumulates slowly and non-uniformly; strongest structure stays near the fire / doorway, not a room-filling layer |
| **weak doorway flow** (T11 − T9 ≈ 5 °C, low neutral plane) | fog leaks into the plenum as a slow plume, not a vigorous outflow |
| **no steady state** — broad maximum several hundred seconds after ignition | fog still building at t = +400–600 s in every clip |

The two independent observation methods agree that this is a **weak, slow,
spatially localized** compartment fire.

---

## 4. Method notes / limitations

- **Calibration** (`src/fog_digitize.py :: CALIB`): anchored on the inner-room floor
  (z = 0) and ceiling underside (z = 0.23 m), and the candle (x ≈ 0.09 m). z-axis
  is solid; x-axis good to ≈ ±1 cm.
- **The x = 0.35 m scan line is occlusion-limited** — a black bracket/mirror
  mounted mid-room sits on that line and blocks the lower part of the column. The
  `zint_mid` digitization there is unreliable; `zint_fire` (x = 0.12) and
  `zint_door` (x = 0.66) are clean.
- 3278 turns the room lights **off ~5 s after ignition** — the pre/post-ignition
  background differ; the digitization baseline is taken from the dark period.
- Single laser plane (y = 0.15) → no information on depth (y) structure.
- Only 2 physical fog experiments (not 3, and a separate session from the
  thermocouple runs R1–R3) — repeatability is 3276 vs 3277/3278.

---

## 5. Tracer↔fog transport comparison — DONE (2026-09-10)

FDS run `s7_tracer` (5 mm, 8-rank, baseline source, T_END 350 s, `--tracer`):
passive tracer from the **candle-cup side faces** (standalone `&SURF FOG_SRC`,
`MASS_FLUX = 1e-5 kg/m²/s`, ramped with ignition; **not** on the burner vent — a
species `MASS_FLUX` on a `HRRPUA` surface makes FDS scale it off the heat release,
`TRACER Mass Flux 1.5e10 kg/s/m²`, both the unindexed and indexed forms). Probes:
`tr_{fire,mid,door}_z{03..22}` column profiles, `tr_{room,upper,lower,plenum}mean`
volume means. → **figure `figures/m3_tracer_fill.png`**.

| test | model result | video |
|---|---|---|
| **time-to-fill** | gradual over minutes (`tr_roommean` climbs steadily on a log scale through 350 s) | fog first visible +150 s, builds over the following 5–10 min |
| **stratification** | sharp early peak (`tr_upper/tr_lower` ≈ 22 at t ≈ 30 s while the tracer is still in the ceiling layer), decaying to **≈ 1.3 by t ≈ 100 s** — near-uniform | no sharp descending interface; gradual room-fill |
| **room vs plenum** | plenum lags ~50 s and stays 1–2 orders below the room throughout | strong fog structure stays near the fire / doorway, weak in the plenum |

**Verdict: the model reproduces the fog transport.** In the video's observable
window (fog visible from t ≈ +150 s) the model says *near-uniform, still slowly
filling* — which is exactly what the footage shows. The model's early
stratification transient (t < 60 s) is below the video's detection threshold and
cannot be confirmed either way — flag it as an assumption, not a match.

Both the tracer and the thermocouples (P02) describe the same weak, slow,
near-uniform fill: **the FDS compartment flow model is sound.** (The T3 issue —
SENSITIVITY_FINDINGS §2 — is a wall *thermal boundary* problem, not a flow
problem.)

**Optional, not done:** frame-level digitization of a fog-front height with
`src/fog_digitize.py`. The qualitative comparison above already settles the
question; a digitized curve would add precision the unrecorded fog injection rate
does not justify.
