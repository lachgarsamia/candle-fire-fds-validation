# EXPONAT FINDINGS — compartment thermal structure & event timeline

**Phase 02.** Inputs: `2026-08-27_exponat_R1/R2/R3.txt`. Code: `src/exponat_loader.py`,
`src/exponat_analysis.py`. Figures in `figures/`, tables in `data/processed/`.

---

## 0. Scope — read this first

**The Exponat runs contain temperature and event timing. Nothing else.**
Every one of the 10 heat-flux gauges is dead (constant sentinel), the compartment
load cell is dead (`-999999` every row), and 33 of 40 thermocouple channels are
unconnected (sentinel `3276.7`). See RECON §B.4. **Do not expect, request, or
design any comparison around compartment heat flux or compartment mass loss — that
data does not exist.** The FDS validation on the compartment side is:

* **7 thermocouple histories**, and
* **an operator event timeline** (`event_number` 0→4).

That is the entire ground truth this phase can produce.

---

## 1. Headline answer

**The compartment fire is a small, localized, buoyancy-dominated plume that does
not mix the room.** A tea-light (~18 W) 3 cm in front of the back wall drives:

* a **hot, repeatable plume** — TC_01 rises **107 ± 7 °C** above ambient
  (peak 127–137 °C), reproducible to **6 % CoV** across three runs;
* a **weak, shallow, spatially localized hot layer** — strong right above the
  fire (TC_03, +43 °C at the ceiling near the plume) but almost gone 23 cm away
  (TC_05, +5 °C at the ceiling centre). **Horizontal ceiling gradient ≈ 41 °C.**
  The room is *not* well-mixed;
* a **clear but small doorway stratification** — vent top +4.7 °C (outflow),
  vent floor +0.2 °C (undisturbed inflow), monotonically ordered by height in
  every run.

**Once each run is aligned to its own inferred ignition, the three runs
superimpose closely** (see `figures/exponat_overlay_plume.png`) — the experiment
is repeatable. The `event_number` channel is **not** a common clock (its
transition times differ 10-fold between runs), but in every run sustained heating
begins within **1–2 s of one `event_number` transition**, which gives a solid
empirical ignition anchor.

**No quasi-steady plateau exists.** The plume climbs for ~400 s to a broad
maximum (~117–130 °C) then slowly declines as the wax depletes
(R3: −1.9 °C/min post-peak). Validation targets are the *transient* growth curve
and the *spatial structure*, not a steady value.

**Recommended primary validation run: R1** (cleanest data — 1 split-write vs 4/7;
strongest, least-noisy stratification; captures the full ignition→peak ramp),
with **R3 as a long-duration complement** (941 s post-ignition, captures the
slow decline that R1's 546 s record misses).

---

## 2. Parsing (`src/exponat_loader.py`)

Plain ASCII, comma-delimited, `.`-decimal, CRLF, one `# ExpName:` line then an
89-column header — `csv.reader` reads it directly. The loader keeps only the live
channels and handles the three documented quirks:

| run | raw rows | after coalescing | split-write pairs merged | out-of-window rows (`exp_time = -1`) | exp_time span |
|---|---|---|---|---|---|
| R1 | 864 | 863 | 1 | 1 (trailing) | 0–882 s, 862 samples |
| R2 | 806 | 802 | 4 | 1 (trailing) | 0–820 s, 801 samples |
| R3 | 975 | 968 | 7 | 3 (leading) | 0–990 s, 965 samples |

* **Non-uniform time axis.** All analysis is built on the real `exp_time` vector
  (median step 1.00 s, mean 1.02–1.03 s — the DAQ runs slightly slower than 1 Hz
  and skips 20–26 seconds per run). Never a fixed-fps assumption.
* **Split-write pairs** — one acquisition frame flushed as two rows ~1 ms apart,
  each carrying a *disjoint* subset of channels — are detected by the sub-10 ms
  timestamp gap and merged field-by-field (non-NaN wins). This is the only source
  of blank cells; after merging, zero NaNs remain in the in-window traces.
* **`event_number`** is forward-filled through the split-write blanks and treated
  as a step function.

**Reuse:** `timeseries.write_series_csv` (as-is) for every output table;
`devices.TC_THRESHOLDS` for the 60/100/300 °C bands. The crossing-time helper
mirrors `summary_stats._first_threshold_time` but indexes the real `exp_time`
vector rather than `idx/fps` (RECON §B.4.5 — the FireScope helpers assume a fixed
rate, which does not hold here).

---

## 3. Thermocouple → position mapping, verified against the data

Positions from `FDS_geometry_reference.md` (authoritative). All TCs at depth
centre y = 0.15 m. Candle at x = 0.09 m, floor.

| TC | group | x (m) | z (m) | verification verdict |
|---|---|---|---|---|
| **TC_01** | back-wall column | 0.12 | 0.05 | ✅ **hottest by far** (107 °C rise). 3 cm behind the candle at floor level → sits *in the flame/plume*, not in free gas. Confirms position; see the non-monotonicity note. |
| **TC_02** | back-wall column | 0.12 | 0.16 | ✅ position consistent, ⚠️ **high scatter (CoV 29 %)** and spiky trace — it sits at the *edge of the intermittent flame/plume*, reading a fluctuating hot/cool mix. Low mean + high variance is the signature of plume-edge flicker, not a mislabel. |
| **TC_03** | back-wall column | 0.12 | 0.23 | ✅ at ceiling height near the fire; +43 °C rise, smooth. Behaves as a hot-ceiling-jet sensor. |
| **TC_05** | ceiling centre | 0.35 | 0.23 | ✅ same height as TC_03 but 23 cm away → only +5 °C. Consistent with a hot layer localized over the fire (see §4.3). ⚠️ operating near DAQ resolution (~0.1 °C steps, ~0 pre-ignition noise) — the small rise is real but low-SNR. |
| **TC_09** | doorway | 0.70 | 0.015 | ✅ floor of the vent; **+0.2 °C** — undisturbed cool inflow, exactly as a doorway floor sensor should read. At the DAQ resolution floor. |
| **TC_10** | doorway | 0.70 | 0.075 | ✅ mid-vent; +1.1 °C — between inflow and outflow, near the neutral plane. |
| **TC_11** | doorway | 0.70 | 0.14 | ✅ top of the vent; **+4.7 °C** warm outflow. Steps up within ~1 s of ignition then climbs smoothly. |

**No channel contradicts its assigned position.** The two things to carry into
FDS comparison:

1. **TC_01 is a flame/plume sensor.** An FDS `DEVC` at (0.12, 0.15, 0.05) will
   sample the resolved plume and its value will depend strongly on mesh
   resolution near the burner (Phase 04). Compare trends and the 100–130 °C band,
   not a single number.
2. **The back-wall "column" is non-monotonic in height** — T1 (≈107 °C rise) ≫
   T3 (≈43 °C) > T2 (≈35 °C) — because T1 is in the plume while T2→T3 show normal
   thermal stratification above the flame tip. FDS must reproduce this
   non-monotonic column, not merely "hotter near the ceiling."

---

## 4. Thermal structure (per run + cross-run)

Numbers are peak temperature **rise above each sensor's pre-ignition baseline**,
mean ± sample std across R1/R2/R3, each run aligned to its own ignition.
Full per-run values in `data/processed/exponat_per_run_summary.csv`; repeatability in
`data/processed/exponat_cross_run_summary.csv`.

### 4.1 Plume / back-wall column

| sensor | z (m) | R1 | R2 | R3 | mean ± std | CoV |
|---|---|---|---|---|---|---|
| TC_01 (plume) | 0.05 | 111.4 | 110.2 | 99.4 | **107.0 ± 6.6 °C** | 6.2 % |
| TC_02 (mid) | 0.16 | 26.5 | 31.7 | 46.0 | 34.7 ± 10.1 °C | 29.1 % |
| TC_03 (ceiling@fire) | 0.23 | 38.9 | 46.6 | 44.8 | 43.4 ± 4.0 °C | 9.3 % |
| peak absolute TC_01 | | 136.6 | 136.8 | 126.5 | 133.3 ± 5.9 °C | |
| TC_01 time-to-peak (from ign) | | 463 s | 416 s | 415 s | 431 ± 27 s | 6.4 % |

* The plume sensor is the **most repeatable** channel (6 % CoV) — the fire source
  itself is consistent, matching the cone-side finding of ~18 W per candle.
* TC_02's 29 % CoV is **flame-flicker scatter**, not a source-strength difference
  (its trace oscillates 30–50 °C in R1 — `figures/exponat_R1_structure.png`).
* Upper-layer stratification **T3 − T2 = 30.1 ± 2.8 °C** at peak, settling to
  ~20 °C sustained. The thermal interface sits **above z = 0.16 m** (T2 stays
  only ~35 °C over ambient while T3 is ~43 °C) — a shallow hot layer in the top
  ~7 cm of a 23 cm room.

### 4.2 Doorway profile (the vent signature — working)

| sensor | z (m) | mean rise ± std | role |
|---|---|---|---|
| TC_09 | 0.015 | 0.2 ± 0.0 °C | cool inflow, undisturbed (at resolution floor) |
| TC_10 | 0.075 | 1.1 ± 0.2 °C | near the neutral plane |
| TC_11 | 0.14 | 4.7 ± 0.2 °C | warm outflow |
| **T11 − T9** | | **5.0 ± 0.4 °C** peak | doorway stratification |

Ordered by height in **every run**, rises monotonically over ~400 s
(`figures/exponat_structure_overlay.png`), CoV 4–7 %. The **neutral plane sits
between z = 0.015 and z = 0.075 m** — i.e. very low, roughly the bottom third of
the 0.15 m opening. This is a demanding, specific target: FDS must put the
neutral plane low and keep the outflow to only a few °C above ambient.

### 4.3 Ceiling — the room is NOT well mixed

| comparison | mean ± std | meaning |
|---|---|---|
| T3 (ceiling @ fire, x=0.12) − T5 (ceiling centre, x=0.35) | **40.8 ± 3.8 °C** peak, 29.5 °C sustained (R3) | strong horizontal gradient along the ceiling |
| TC_05 rise (ceiling centre) | 4.6 ± 0.4 °C | the hot layer barely reaches mid-room |

The hot gas is confined to a **ceiling jet localized over the plume**; 23 cm away
the ceiling is only ~5 °C above ambient. Any FDS model that produces a uniform
upper layer is wrong for this compartment. Note the mid-room ceiling (TC_05,
+5 °C) is *cooler* than the mid-height back-wall point (TC_02, +35 °C) — the heat
hugs the fire so tightly that "near the ceiling, far from the fire" is colder
than "high up, near the fire but below the ceiling."

### 4.4 Hot-layer / interface behaviour (thermocouple estimate)

With only three back-wall heights — and the lowest (z=0.05) contaminated by the
plume — a formal N-percent or integral interface height is not defensible. What
the data supports:

* **Interface above z = 0.16 m** throughout the burn (T2 stays cool-ish).
* **Stratification onset within ~30–90 s of ignition** (T3 − T2 exceeds its
  pre-ignition offset by >3 °C, sustained): R1 ≈ 30 s, R3 ≈ 93 s. (R2's detector
  fires at +1 s — the clean ceiling sensor T3 responds a beat before the
  flicker-zone T2, so this is a noise-sensitive estimate, not a 1 s physical
  time.) It develops fast, then holds.
* **No measurable layer descent** — the interface does not drop over the burn;
  the shallow layer is stable. Consistent with a small fire and an open doorway
  venting the excess.
* The independent smoke/video-based interface (Phase 4) is the one to use for a
  quantitative descent comparison; this TC estimate only bounds it.

---

## 5. Event timeline & the empirical ignition anchor

`event_number` steps 0→1→2→3→4 at **operator-triggered** times. Full table in
`data/processed/exponat_events.csv`.

| run | 0→1 | 1→2 | 2→3 | 3→4 | thermal onset (TC_01) | onset vs nearest transition |
|---|---|---|---|---|---|---|
| R1 | 213 s | 303 s | **334 s** | 489 s | **336 s** | **2→3, Δ = +2 s** |
| R2 | 24 s | **73 s** | 371 s | 772 s | **74 s** | **1→2, Δ = +1 s** |
| R3 | 17 s | **47 s** | 303 s | 403 s | **49 s** | **1→2, Δ = +2 s** |

* The transition times differ by up to 10× between runs → **`event_number` is not
  a shared protocol clock.** Cross-run time comparison is only valid after
  per-run ignition alignment.
* **But** in every run, sustained TC_01 heating begins within **1–2 s** of one
  transition. That transition is **the candle-lighting event** — it is `2→3` in
  R1 and `1→2` in R2/R3 (the operator logged a different number of pre-ignition
  steps), but thermally it is unambiguous.
* **Ignition anchor used:** the thermal onset instant itself (TC_01 sustained
  rise > baseline + 2 °C, held ≥ 15 s). `t_ign` = 336 / 74 / 49 s exp_time for
  R1 / R2 / R3. Carry ±2 s ignition-timing uncertainty into any sim-vs-exp time
  comparison (and, separately, the ~±3 s video↔DAQ sync from PROJECT_STATE for
  smoke-phase work).
* The **physical meaning of the other transitions** (glycerin added, all candles
  lit, extinguish, …) is for the human to map. What the data shows: `3→4` lands
  at τ = +153 s (R1), +698 s (R2), +354 s (R3) after ignition — no consistent
  thermal feature at `3→4`, so it is probably an end-of-phase / housekeeping
  marker, not a fire event. In R1 the `0→1` and `1→2` steps (τ = −123 s, −33 s)
  are pre-ignition setup.

---

## 6. Characteristic times (from inferred ignition)

| quantity | R1 | R2 | R3 | notes |
|---|---|---|---|---|
| thermal onset Δ vs nearest event | +2 s | +1 s | +2 s | ignition anchor quality |
| TC_01 crosses 60 °C | +37 s | +36 s | +42 s | fast, repeatable |
| TC_01 crosses 100 °C | +142 s | +121 s | +157 s | |
| stratification onset (T3−T2) | +30 s | +1 s* | +93 s | *noise-triggered; see §4.4 |
| time to plume peak | +463 s | +416 s | +415 s | broad maximum |
| broad-peak TC_01 mean ± std (±60 s of peak) | 126.6 ± 5.7 °C | 120.9 ± 7.3 °C | 116.8 ± 5.5 °C | not a plateau — a rounded maximum |
| post-ignition record length | 546 s | 746 s | **941 s** | R1 stops before decay |
| post-peak linear trend | +4.4 °C/min (still rising at record end) | −1.5 °C/min | **−1.9 °C/min** | R1 never reaches decay; R2/R3 show wax depletion |

There is **no flat quasi-steady window** at >50 % of peak rise with |dT/dt| <
0.03 °C/s in any run — the plume is always either climbing or slowly cooling.

---

## 7. Repeatability & its limits

**Within-configuration repeatability (n = 3):**

| metric | mean ± std | CoV | verdict |
|---|---|---|---|
| TC_01 peak rise | 107.0 ± 6.6 °C | 6.2 % | excellent |
| TC_03 peak rise | 43.4 ± 4.0 °C | 9.3 % | good |
| TC_02 peak rise | 34.7 ± 10.1 °C | 29 % | poor — flame flicker |
| TC_05 peak rise | 4.6 ± 0.4 °C | 8.7 % | good (but low-SNR) |
| TC_11 peak rise | 4.7 ± 0.2 °C | 4.4 % | excellent |
| TC_01 time-to-peak | 431 ± 27 s | 6.4 % | good |
| upper-layer ΔT (T3−T2) | 30.1 ± 2.8 °C | 9.1 % | good |
| doorway ΔT (T11−T9) | 5.0 ± 0.4 °C | 7.2 % | good |
| ceiling horiz. ΔT (T3−T5) | 40.8 ± 3.8 °C | 9.4 % | good |

**Caveats:**

* **Timing is not comparable across runs without ignition alignment** — the
  operator event clock differs 10× between runs. All cross-run numbers above use
  per-run ignition alignment.
* **R3 ran cooler** (TC_01 peak 126 °C vs 137 °C for R1/R2; more post-peak
  decline). Likely a slightly weaker set of candles or a longer burn that reached
  wax depletion within the record — consistent with the cone-side spread of
  16.5–20 W per candle. Treat the plume band as **≈ 110–137 °C**, not a point.
* **Record lengths differ 2×** (546–941 s). Only R3 captures the full burn to
  decay; R1 stops near the broad peak.
* **Sensors near ambient (TC_05, TC_09, TC_10, TC_11) sit near the DAQ
  resolution** (~0.1 °C quantisation, ~0 pre-ignition noise). Their few-°C rises
  are real and repeatable but should be validated as *trends*, not to 0.1 °C.
* n = 3 for a single configuration; no independent estimate of instrument bias
  (all three runs share the same TC set and DAQ).

---

## 8. Recommended primary validation run

**R1**, with **R3 as the long-duration complement.**

| criterion | R1 | R2 | R3 |
|---|---|---|---|
| data cleanliness (split-writes) | **1** | 4 | 7 |
| stratification clarity (mean T3−T2) | **20.4 °C** | 18.5 °C | 16.8 °C |
| plume peak (repeatable band) | 137 °C ✅ | 137 °C ✅ | 126 °C |
| captures ignition→peak ramp fully | ✅ | ✅ | ✅ |
| captures post-peak decay | ❌ (ends at peak) | partial | ✅ (941 s) |
| pre-ignition baseline length | 336 s ✅ | 74 s | 49 s |

**Use R1** for the FDS baseline comparison of the growth phase and spatial
structure (0 → ~540 s post-ignition): it has the least missing data, the
strongest and least-noisy stratification signal, the longest clean pre-ignition
baseline, and a plume peak that agrees with R2. **Cross-check the full-burn
behaviour (slow decline, wax depletion) against R3.** R2 is a usable
intermediate but has no unique advantage.

---

## 9. What this hands to Phase 03/05 (FDS validation targets)

1. **Plume:** TC_01 growth curve, ignition-aligned; 60 °C at +37 ± 3 s, 100 °C at
   +140 ± 18 s, broad peak 110–137 °C at +430 ± 30 s. Mesh-sensitive — see P04.
2. **Non-monotonic back-wall column:** T1 ≫ T3 > T2 at all times.
3. **Localized hot layer:** ceiling near-fire (T3, +43 °C) ≫ ceiling centre
   (T5, +5 °C); horizontal ΔT ≈ 40 °C. Room not well-mixed.
4. **Doorway:** monotonic by height, T11 − T9 ≈ 5 °C, neutral plane low
   (z ≈ 0.02–0.05 m).
5. **Shallow, stable interface** above z = 0.16 m; no descent.
6. **Timeline:** ignition anchor good to ±2 s; no steady state — validate the
   transient.
7. **Experimental scatter to beat before blaming FDS:** ±7 °C on the plume peak,
   ±3–4 °C on the layer and doorway ΔTs, ±27 s on time-to-peak.
