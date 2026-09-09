# M2 / M3 plan — the canonical roadmap after M1

*Drafted 2026-09-07, re-sequenced 2026-09-08. This is the forward reference for
the project. There is no separate numbered plan doc — "M1/M2" is informal
shorthand; keep this file current.*

M1 (cone → compartment → FDS validation) is closed. It left three gaps. They are
addressed in this order, chosen so the cluster runs that **need nothing from
anyone** go first:

| # | work | gate | status |
|---|---|---|---|
| **P1** | T3 wall-heating test — 2 mm run to 450 s | none | **RUNNING** — job 21899510, 28 cores, ~0.9 s/step → ~27 h, DT_RESTART=7200 |
| **P2** | T3 wall-model attribution — insulated / adiabatic walls | none | 2-rank decks were CPU-starved (1.9 s/step on 8 cores); **regenerated as 8-rank `--split 4,1,2`, T_END 350 s**; parse-check job 21900128, then resubmit `--ntasks=8` |
| **P3** | Source-uncertainty propagation — HRR / radiative-fraction sweep | none | 8-rank decks ready (s0–s4); submit after P2 |
| **P4** | Smoke / layer-dynamics validation | fog video **IN HAND** (`/Volumes/room_corner/Samia/`) | ignition times found; digitization plan below |
| P5 | Numerical finalization — 1.5 mm restart, archive | none | low priority |

**Provisioning lesson (2026-09-08):** the sweep's 5 mm/2-mesh decks max out at 2 MPI
ranks; on `--ntasks=2 --cpus-per-task=4` (8 cores) FDS ran ~1.9 s/step → 26 h for
350 s. Fix: `make_fds.py --split NX,NY,NZ` (uniform-mesh general MPI split, guards
the layer columns; NZ≤2). `--split 4,1,2` = 8 ranks, ~150 k cells each. Submit
`--ntasks=8 --cpus-per-task=4`.

**Retrieval when a run finishes:** `scp cobra:/beegfs/lachgar/candle_fds/sweep/run/<chid>/<chid>_devc.csv`
→ `fds/runs/sweep/<chid>/`, then `python sensitivity_post.py`.

## P4 — fog video: what's established

| clip | = | ignition (video-time) | analysis offset |
|---|---|---|---|
| `7L5A3276` | fog experiment 1, lights on | ~120 s | `t = video − 120` |
| `7L5A3277` | fog experiment 2, lights on | TBD | — |
| `7L5A3278` | fog experiment 2, **lights off** (cleanest) | ~30 s | `t = video − 30` |

25 fps, 1920×1080. No on-screen clock → ignition anchored on first-flame frame
(±1–2 s). Fog develops slowly (weak 18 W fire): gradual top-down fill of the inner
compartment over minutes, strongest structure in the plenum. Primary metric =
descending fog-front / layer height vs ignition-aligned time from **3278**
(dark), cross-checked on **3276**; compare to FDS `zint_*` from
`m2_base_nest20_450`.

---

## P1 — Does T3 climb toward +43 °C as the walls store heat?

**The claim being tested.** P05 says the T3 gap to the measured broad peak is
"dominated by the wall-thermal-mass timescale the 150 s runs do not capture, with
a secondary D\*/δx contribution — not separable with the runs in hand." That is
the study's weakest sentence. This run makes it separable.

**Run:** `fds/sweep/m2_base_nest20_450.fds` — the P04 nest20 geometry (2 mm core,
D\*/δx = 6.1), baseline source, **T_END = 450 s**. Identical to
`candle_fine_nest20_mpi.fds` except T_END and the smoke DEVCs (`check_nesting.py`
✓; diff is additive-only).

**Read:** T3(t) from 150 → 450 s. If it climbs from +16 toward +30–40 °C, the
wall-timescale explanation is **confirmed** and the P05 hedge is replaced with a
number. If it stays flat at +16, the gap is resolution / model, not run length —
a different and more serious finding.

---

## P2 — How much of the T3 late-climb is the wall model?

**Runs:** `s5_wallins` (PMMA slab, `BACKING='INSULATED'` — walls absorb but do
not leak to the lab) and `s6_walladi` (`ADIABATIC` — no wall thermal mass at
all). Both 5 mm uniform, 450 s. Compare against `s0_base_dx5` (5 mm baseline).

**Read:** T3 at 150 s and 450 s across {exposed, insulated, adiabatic}. If
removing wall loss lifts T3 toward the measured +43 °C, the wall boundary
condition is the lever and its uncertainty is quantified. If T3 barely moves, the
walls are not where the missing energy goes.

**Caveat to state in the findings:** `s6_walladi` is a sealed **adiabatic** box
with constant 18 W for 450 s — gas temperature and `p_box` will run away. It is a
bracket, not a physical case; report it as the upper bound only.

---

## P3 — Source-uncertainty propagation

Turns "±15–20 % source uncertainty" (a statement) into a °C band on every
predicted thermocouple.

| deck | knob | vs baseline |
|---|---|---|
| `s1_hrr15` / `s2_hrr21` | HRR 15 / 21 W | the cone source band (18 ± ~3 W) |
| `s3_rad20` / `s4_rad35` | radiative fraction 0.20 / 0.35 | literature spread (baseline 0.25) |
| `s0_base_dx5` | — | 5 mm reference for the deltas |

**Reads:** `d(T_i)/d(HRR)` from s1/s2 → propagate ±3 W to ±°C on
T5/T9/T10/T11 (expect small — far-field ≈ linear in a small HRR at fixed
geometry). s3/s4 → mostly the near-fire convective/radiative split, second-order
far-field.

**Deliverable (P1–P3):** `SENSITIVITY_FINDINGS.md` — per-sensor °C band from each
knob; the "model discrepancy" column in VALIDATION_FINDINGS.md §2 becomes
itemised (wall BC, HRR, χr) instead of a lump residual. Post-processor
`sensitivity_post.py` is written and waiting for the CSVs.

---

## P4 — Smoke / layer-dynamics validation  *(gated on the fog video)*

### Framing — LOCKED, keep front-and-centre in SMOKE_FINDINGS

1. **The glycerin fog is a seeded passive tracer, not candle soot.** The
   comparison is **layer dynamics only** — interface height, descent rate,
   transport timing. **Never** concentration, optical density, or soot yield.
2. `SOOT_YIELD = 0.008` in the deck produces a *combustion-soot* field that is
   physically unrelated to the introduced fog. **Do not compare the two.** The
   `SOOT VOLUME FRACTION` / `VISIBILITY` slices are for qualitative plume *shape*
   only, and even that must be captioned as combustion soot ≠ fog.
3. **The fog was introduced at the candle cup** — hot, buoyant, rising with the
   plume. The correct FDS analogue is a **passive tracer released at that
   location and time**, not combustion soot. If a tracer run is done, add a
   `&SPEC` tracer with a small `MASS_FLUX` on the cup rim VENT starting at
   ignition.
4. **State explicitly which interface is being compared to the video:**
   - the **thermal-stratification interface** (`LAYER HEIGHT` DEVC,
     temperature-integral — the primary metric, needs no tracer), or
   - a **modelled passive-tracer interface** (from a tracer `&SPEC`, if run).
   These are **not guaranteed to be the same surface.** The working assumption —
   *hot fog released at the plume base rises with and marks the thermal layer* —
   is plausible but unverified; flag it as an assumption every time the
   comparison is quoted.

### Metrics
- `zint_{fire,mid,door}` (x = 0.12 / 0.35 / 0.66) interface height vs time.
- Descent rate over the first ~60–120 s; equilibrium height.
- `Tupp_* / Tlow_*` layer temperature split.

### Work when the video is in hand (media disk access now available)
- Note frame rate and any visible clock / timestamp for alignment to the
  ignition anchor (EXPONAT thermal-onset instant, ±2 s).
- Extract frames (~1 fps); digitize the visible fog-interface height vs time —
  edge detection on the fog boundary, or manual click-track if the boundary is
  ambiguous. Output `results/smoke_layer_measured.csv`.
- Overlay against `m2_base_nest20_450` `zint_*`; `SMOKE_FINDINGS.md` + one
  figure + a slice-vs-frame contact sheet.
- **Do not build any of this until the video is in hand.**

---

## P5 — Numerical finalization  *(low priority)*

- `candle_fine_nest15_mpi` restart → 150 s (real 4-point mesh ladder at a common
  time; tightens the T3 ±3 °C numerical band).
- Archive `/beegfs/lachgar/candle_fds/` outputs with a manifest.

---

## Execution mechanics

**Decks:** `cd fds/sweep && bash make_sweep.sh` → 8 decks.
**Submit:** `fds/sweep/submit_sweep.sh` — `bash submit_sweep.sh 1` = P1+P2 only,
`bash submit_sweep.sh 2` = P3. Adjust ACCOUNT/PART/TIME to the allocation.

**Parse-check status (Pleiades FDS 6.11.1, 2026-09-08 — done via `ssh cobra`
with `-i ~/.ssh/pleiades_key`; the `cobra` config alias has a stale
IdentityFile path):**

- Smoke SLCF quantities: `'SOOT VOLUME FRACTION'` and `'SOOT DENSITY'` both give
  `ERROR(1042) not found` on this build. **Fixed** to
  `QUANTITY='MASS FRACTION', SPEC_ID='SOOT'` + `'VISIBILITY'` — both verified with
  a trivial probe deck, along with `LAYER HEIGHT`, `UPPER/LOWER TEMPERATURE`.
- `m2_base_nest20_450` (7 ranks) ✓ steps, no ERROR.
- `s5_wallins` (2 ranks, 2-way z-split at z=0.25, INSULATED backing) ✓ steps.
- `s6_walladi` (ADIABATIC), `s0_base_dx5` — parse-check in progress.

The z-split is at **z = 0.25** on purpose — the layer devices integrate z 0–0.23
and must sit in one mesh; do not `--split-z 4+`. `parsecheck.batch` (on the
cluster) reruns the 1-min-each check.

## Cluster cost (order-of-magnitude)

- 5 mm / 450 s / 1.2 M cells / 2 ranks: expect a few hours to ~half a day each.
- 2 mm nest / 450 s: ~3× the P04 nest20 (150 s in < 24 h) → a 48 h slot or a
  `&DUMP DT_RESTART=` checkpoint.

**Before submitting `m2_base_nest20_450`:** the deck keeps `DT_SLCF=5.0` — over
450 s that is ~90 frames of 4 slice quantities on the 0.5 M-cell core (a few GB).
Either bump to `DT_SLCF=15.0` (hand-edit the `&DUMP` line) or accept the size.
Add `&DUMP ... DT_RESTART=3600 /` and submit with `RESTART=.FALSE.` first if the
48 h slot is uncertain — resubmit `RESTART=.TRUE.` to continue.
