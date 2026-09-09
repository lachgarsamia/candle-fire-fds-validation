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
| **Ceiling over the fire** (T3) | agrees at matched simulated time (+19.9 vs +20.2 ± 5.0 °C at 65 s); gap to the +43 °C broad peak is dominated by the wall-thermal-mass timescale the runs don't reach, with a secondary D\*/δx < 10 contribution | **numerical / run-length** — a converged mesh (D\*/δx ≈ 10–16, ≈ 90 M cells) is impractical |
| **In-flame column** (T1, T2) | +0.4 / +1.2 °C vs +49 / +13 °C measured; *worsens* with mesh refinement | **structural** — a prescribed-HRR LES has no luminous reaction zone; a thermocouple 3 cm from the wick is outside what the model can represent at any resolution |

The near-fire rake shows why: the modelled plume is a narrow hot column locked
over the wick that gets *narrower* as the mesh is refined, never reaching the
probe. Separating this **structural** limit from the **numerical** one at T3 —
rather than tuning the source until the near-fire numbers agree — is the study's
central contribution.

### 4 · In progress (M2 / M3)

* **Uncertainty propagation** — a source/wall sweep (HRR 15/18/21 W, radiative
  fraction 0.20/0.25/0.35, wall boundary exposed / insulated / adiabatic) that
  turns the "± 15–20 %" statement into a per-sensor °C band and decomposes the
  T3 residual.
* **Smoke visualisation** — the laser-sheet fog footage. First finding: **no
  sharp descending interface formed**; the fog filled the compartment gradually
  over minutes, consistent with the weak buoyant circulation of an 18 W fire in
  a sealed box, and corroborating the thermocouple picture (localized layer,
  weak doorway flow, no steady state). The glycerin fog is a *seeded passive
  tracer*, so the FDS comparison is transport shape and timing only — never
  concentration.

---

## Repository layout

```
├── *.md                     findings, plans and the settled-facts record
│   ├── RECON.md              data-format map + reusable-component inventory
│   ├── CONE_FINDINGS.md      §1 above, in full
│   ├── EXPONAT_FINDINGS.md   §2 above, in full
│   ├── FDS_geometry_reference.md   authoritative compartment geometry
│   ├── MESH_STUDY_FINDINGS.md      numerical-uncertainty study
│   ├── VALIDATION_FINDINGS.md      §3 above, in full
│   ├── SMOKE_FINDINGS.md           §4, smoke (preliminary)
│   ├── M2_M3_PLAN.md               forward roadmap
│   ├── REPORT_SUMMARY.md           2–3 pp supervisor-facing synthesis
│   └── PROJECT_STATE.md            running settled-facts + status record
│
├── cone_loader.py / cone_analysis.py         cone-calorimeter pipeline
├── exponat_loader.py / exponat_analysis.py   compartment thermocouple pipeline
├── fds/make_fds.py          single source of truth for every FDS deck
│   ├── check_nesting.py     verifies embedded-mesh alignment
│   ├── sweep/               M2/M3 source-, wall- and tracer-sweep decks
│   ├── cluster/             SLURM batch templates (Pleiades)
│   └── runs/                deck copies + device CSVs + solver logs
├── fds_post.py              cross-mesh comparison + convergence assessment
├── p05_validation.py        the three-uncertainty split + validation figures
├── fig_validation_grid.py   the consolidated 7-thermocouple figure
├── sensitivity_post.py      M2/M3 per-knob bands + T3 decomposition
├── fog_digitize.py          laser-sheet smoke-layer extraction from the video
│
├── results/                derived time series, summaries, digests (CSV/JSON)
├── figures/                generated figures
├── weights.csv             the manual weigh table (the HRR anchor)
└── 2026-08-27_exponat_R*.txt, *_Candle_R*.csv, *_Candles_R*.csv
                            raw measurement files
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

The analysis scripts expect the FireScope plotting/IO helpers on the path
(`_repro.py` handles this) and a scientific Python stack (`numpy`, `scipy`,
`matplotlib`, `imageio`).

```bash
python cone_analysis.py        # -> results/cone_*, figures/cone_*
python exponat_analysis.py     # -> results/exponat_*, figures/exponat_*
python fds_post.py             # cross-mesh table + convergence
python p05_validation.py       # three-uncertainty split + p05 figures
python fig_validation_grid.py  # the 7-thermocouple figure
```

FDS decks:

```bash
cd fds && python make_fds.py --dx 0.005 --t-end 250 --chid candle_medium_dx5
cd sweep && bash make_sweep.sh          # the M2/M3 sweep set
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
| Uncertainty-propagation sweep (M3) | running |
| Smoke / layer-dynamics validation (M2) | preliminary finding recorded; tracer run + digitization pending |

`PROJECT_STATE.md` is the authoritative running record.

---

## Data provenance

* `2026-08-27_exponat_R{1,2,3}.txt` — compartment runs, 40-channel DAQ export
  (7 thermocouples live).
* `{25,26,27}082026_*Candle*_R*.csv` — cone-calorimeter runs.
* `weights.csv` — the manual before/after candle weigh table.
* Laser-sheet smoke footage is stored separately (not in this repository);
  frame timings and the ignition anchor are recorded in `SMOKE_FINDINGS.md`.

Fire Dynamics Simulator 6.11.1 (NIST). Cluster: Pleiades, Bergische Universität
Wuppertal.
