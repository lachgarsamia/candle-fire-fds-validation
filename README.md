# Candle-fire FDS validation

**Characterising a free-burning tea-light fire from cone-calorimeter data,
reconstructing a compartment experiment in Fire Dynamics Simulator (FDS), and
quantifying where the simulation agrees and disagrees with the measured
temperature and smoke evolution — separating numerical, experimental and model
uncertainty rather than tuning the model to match.**

This repository holds the full analysis chain for that study: the raw
measurements, the processing pipeline, the FDS decks and mesh study, the
validation, and the write-ups.

---

## Why this study

A tea light is about the smallest self-sustaining flame you can buy — on the
order of **18 W**. It sits far below the fire sizes FDS is normally validated
against, and at that scale two things are hard: the cone calorimeter's
oxygen-consumption calorimetry is out of its calibrated range, and the FDS
plume needs a mesh finer than is practical. Rather than paper over either, this
work measures both limits and reports them.

The physical experiment is a candle burning inside a small sealed acrylic
compartment (a "room" that vents only through a doorway into a closed outer
box), instrumented with thermocouples and visualised with a laser-sheet smoke
technique.

---

## Key results

### 1 · The fire source (cone calorimetry)

* A single tea light is a **free-burning 18 ± 2 W source**, anchored on the
  *manually weighed* mass loss (× an assumed paraffin heat of combustion, with
  combustion efficiency 0.85–1.0 carried as the uncertainty).
* The burn is **constant-rate** — a straight-line fit of mass vs time gives
  r² > 0.999 — so a steady mean is the right representation, not a curve.
* **Oxygen-consumption HRR is not usable here.** Whole-run O₂ depletion is
  0.01–0.03 % absolute; the O₂→kW conversion overshoots the mass-loss result by
  ≈ 3× and scatters by a factor of 2–3 between runs. Documented, not tuned away.
* Overall source uncertainty carried downstream: **± 15–20 %**.

### 2 · The compartment (thermocouples + event timeline)

Seven of the compartment's forty thermocouple channels were live; every
heat-flux gauge and the load cell returned sentinel values. Within that limit the
picture is clear and repeatable across three runs (≈ 6 % CoV on the plume peak):

* A **hot, localized plume** — the thermocouple above the wick rises
  **107 ± 7 °C** above ambient.
* A **shallow hot layer that hugs the fire** — the ceiling directly over the
  plume rises ≈ 43 °C; an identical sensor 23 cm away rises only ≈ 5 °C. The
  room is **not** well mixed.
* A **weak, well-ordered doorway flow** — monotonic by height, ≈ 5 °C top-to-
  bottom, neutral plane low.
* **No steady state** — every channel drifts to a broad maximum several hundred
  seconds after ignition.

### 3 · FDS validation

The model is a sealed acrylic box with the measured geometry, an 18 W
prescribed-heat-release source, and probes at the seven measured positions.
**Nothing was adjusted to match the compartment data.** A four-resolution mesh
study (10 / 5 / 2.0 / 1.5 mm) frames the numerical uncertainty.

| region | outcome | nature of the limit |
|---|---|---|
| **Far-field ceiling & doorway** (4 sensors) | validated — residual ≤ 1 °C after experimental + numerical uncertainty; correct stratification | model has physical content; numerically converged |
| **Ceiling over the fire** (T3) | agrees at matched simulated time (+19.9 vs +20.2 ± 5.0 °C at 65 s); then plateaus at +16 °C while the measurement climbs to +43 °C | **wall thermal-boundary model** — the M3 sweep ruled out run length (2 mm run flat to 410 s) and the back-face condition; the modelled 10 mm opaque acrylic is ~2× too strong a heat sink (adiabatic walls → +60 °C; measurement sits between) |
| **In-flame column** (T1, T2) | +0.4 / +1.2 °C vs +49 / +13 °C measured; *worsens* with mesh refinement | **structural** — a prescribed-HRR LES has no luminous reaction zone; a thermocouple 3 cm from the wick is outside what the model can represent at any resolution |

The near-fire rake shows why: the modelled plume is a narrow hot column locked
over the wick that gets *narrower* as the mesh is refined, never reaching the
probe. Separating this **structural** limit from the **numerical** one at T3 —
rather than tuning the source until the near-fire numbers agree — is the study's
central contribution.

### 4 · Uncertainty propagation and smoke (M2 / M3)

* **Source uncertainty is small.** A sweep over HRR (15/18/21 W) and radiative
  fraction (0.20–0.35) moves **no sensor by more than ~2.5 °C** — the ± 15–20 %
  cone characterisation is not where the T3 gap comes from.
* **The T3 residual is the wall model.** A wall sweep (exposed / insulated /
  adiabatic) plus a 2 mm run to 410 s show the gap to +43 °C is **not** run
  length and **not** the wall back-face condition — the modelled 10 mm opaque
  acrylic is ~2× too strong a heat sink. T3 ∈ [+16 (full PMMA), +60 (no sink)];
  the measurement sits near the weak-sink end.
* **Smoke.** A passive tracer released at the candle cup reproduces the video:
  gradual room-fill over minutes, near-uniform by ~250 s, weak doorway flow, no
  sharp descending interface. The FDS compartment *flow* model is sound. (The
  glycerin fog is a seeded passive tracer — the comparison is transport shape
  and timing only, never concentration.)

---

## Repository layout

```
├── README.md
├── data/
│   ├── raw/
│   │   ├── cone/            cone-calorimeter runs + weights.csv (the manual
│   │   │                    before/after weigh table — the HRR anchor)
│   │   └── compartment/     compartment runs (2026-08-27_exponat_R{1,2,3}.txt)
│   └── processed/           derived time series, summaries, digests (CSV/JSON)
│
├── docs/
│   ├── RECON.md                    data-format map + reusable-component inventory
│   ├── CONE_FINDINGS.md            §1 above, in full
│   ├── EXPONAT_FINDINGS.md         §2 above, in full
│   ├── FDS_geometry_reference.md   authoritative compartment geometry
│   ├── MESH_STUDY_FINDINGS.md      numerical-uncertainty study
│   ├── VALIDATION_FINDINGS.md      §3 above, in full
│   ├── SENSITIVITY_FINDINGS.md     §4, the M3 uncertainty sweep
│   ├── SMOKE_FINDINGS.md           §4, smoke / fog-analogue tracer
│   ├── M2_M3_PLAN.md               forward roadmap
│   ├── REPORT_SUMMARY.md           2–3 pp supervisor-facing synthesis
│   └── PROJECT_STATE.md            running settled-facts + status record
│
├── src/
│   ├── _repro.py                          shared paths + headless-plot setup
│   ├── cone_loader.py / cone_analysis.py            cone-calorimeter pipeline
│   ├── exponat_loader.py / exponat_analysis.py      compartment thermocouple pipeline
│   ├── fds_post.py                        cross-mesh comparison + convergence
│   ├── p05_validation.py                  three-uncertainty split + validation figures
│   ├── fig_validation_grid.py             the consolidated 7-thermocouple figure
│   ├── sensitivity_post.py                M3 per-knob bands + T3 decomposition
│   ├── m3_figs.py                         T3 wall-bracket + tracer-fill figures
│   └── fog_digitize.py                    laser-sheet smoke-layer extraction
│
├── fds/
│   ├── make_fds.py          single source of truth for every FDS deck
│   ├── check_nesting.py     verifies embedded-mesh alignment
│   ├── sweep/               M2/M3 source-, wall- and tracer-sweep decks
│   ├── cluster/             SLURM batch templates (Pleiades)
│   └── runs/                deck copies + device CSVs + solver logs
│
├── figures/                generated figures
└── media/                  setup photos + smoke-footage frame montages
```

---

## Method, in one paragraph each

**Cone.** Six free-burning candle tests (single and three-candle), cone heater
off. Mass loss from a manual before/after weigh table; the load cell is trusted
for *shape* only. HRR = Δm × effective ΔHc / burn duration. The O₂ channel is
used to confirm ignition/flameout timing, not to quantify.

**Compartment.** Three repeat runs. Each aligned to its own inferred ignition
(the thermal onset falls within 1–2 s of an operator event transition — the
candle-lighting step). Peak rises, upper-layer and doorway ΔT, and
characteristic times are reported with the run-to-run spread.

**FDS.** Geometry and source term are fixed from the two analyses above; only
the near-fire cell size changes between mesh variants. Sealed on all outer
faces. The burner is a prescribed-HRRPUA vent on a one-cell inert block, with a
25 s ignition ramp. `make_fds.py` emits every deck so each input traces to a
source.

**Validation.** Simulation and measurement are compared at matched simulated
time. The gap at each sensor is split into experimental scatter (R1–R3),
numerical uncertainty (mesh spread), and residual model discrepancy.

---

## Reproducing

The analysis scripts need a scientific Python stack (`numpy`, `scipy`,
`matplotlib`, `imageio`) and the FireScope plotting/IO helpers — point
`FIRESCOPE_SRC` at that checkout if it isn't at the default location. `_repro.py`
resolves every path from the repo root, so the scripts run from anywhere.

```bash
python src/cone_analysis.py        # -> data/processed/cone_*,   figures/cone_*
python src/exponat_analysis.py     # -> data/processed/exponat_*, figures/exponat_*
python src/fds_post.py             # cross-mesh table + convergence assessment
python src/p05_validation.py       # three-uncertainty split + p05 figures
python src/fig_validation_grid.py  # the 7-thermocouple figure
python src/sensitivity_post.py     # M2/M3 knob bands + T3 decomposition (needs the sweep runs)
```

FDS decks:

```bash
python fds/make_fds.py --dx 0.005 --t-end 250 --chid candle_medium_dx5
cd fds/sweep && bash make_sweep.sh       # the M2/M3 sweep set
```

Cluster runs (Pleiades / Bergische Universität Wuppertal) use the templates in
`fds/cluster/` and `fds/sweep/submit_sweep.sh`.

---

## Status

| phase | state |
|---|---|
| Cone-calorimeter characterisation (P01) | complete |
| Compartment thermocouple analysis (P02) | complete |
| FDS baseline + mesh study (P03–P04) | complete |
| Validation + three-uncertainty split (P05) | complete |
| Uncertainty-propagation sweep (M3) | complete — T3 residual localised to the wall heat-sink model |
| Smoke / fog-analogue tracer (M2) | complete — FDS reproduces the slow near-uniform fill; frame-level digitization optional |

`docs/PROJECT_STATE.md` is the authoritative running record.

---

## Data provenance

* `data/raw/compartment/2026-08-27_exponat_R{1,2,3}.txt` — compartment runs,
  40-channel DAQ export (7 thermocouples live).
* `data/raw/cone/{25,26,27}082026_*Candle*_R*.csv` — cone-calorimeter runs.
* `data/raw/cone/weights.csv` — the manual before/after candle weigh table.
* Laser-sheet smoke footage is stored separately (not in this repository);
  frame timings and the ignition anchor are recorded in `docs/SMOKE_FINDINGS.md`.

Fire Dynamics Simulator 6.11.1 (NIST). Cluster: Pleiades, Bergische Universität
Wuppertal.
