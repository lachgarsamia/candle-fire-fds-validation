# SMOKE_FINDINGS — M2, compartment fog visualisation

**Status: PRELIMINARY.** The qualitative video finding (§3) is a real result and
stands on its own. The quantitative tracer↔fog transport comparison (§5) is
pending the passive-tracer FDS run (`s7_tracer`) and validation of the video
digitization (`src/fog_digitize.py`).

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

## 5. Pending — tracer↔fog transport comparison

FDS run `fds/sweep/s7_tracer.fds` (5 mm, 8-rank, baseline source, T_END 350 s,
`--tracer`): passive tracer released from the **candle-cup side faces** (a
standalone `&SURF FOG_SRC`, `MASS_FLUX = 1e-5 kg/m²/s`, ramped with ignition
`TAU_MF = -25`) and entrained into the plume. **Not** on the burner vent — a
species `MASS_FLUX` on a `HRRPUA` surface makes FDS scale it off the heat
release (parse-check 2026-09-08 saw `TRACER Mass Flux 1.5e10 kg/s/m²` for both
the unindexed and indexed forms). Probes: `tr_{fire,mid,door}_z{03..22}` column
profiles, `tr_{room,upper,lower,plenum}mean` volume means, centre-plane
`MASS FRACTION(TRACER)` slice.

**Comparison (shape + timing only):**
1. **Time-to-fill** — does the modelled tracer take **minutes** to fill the room
   like the fog, or ~30 s like the thermal layer? (This is the key test of
   whether the fog tracks temperature.)
2. **Spatial accumulation pattern** — uniform fill vs descending front; room vs
   plenum partition (`tr_roommean` vs `tr_plenummean`).
3. **Absence of a sharp interface** — does `tr_upper/tr_lower` stay near 1
   (mixed) rather than showing a clean two-layer split?

`zint_*` goes in the **same figure as a separate, labelled thermal-reference
line** — not the comparison target.

Do not build §5 until `s7_tracer` completes **and** `src/fog_digitize.py` output is
validated against hand-picked frames.
