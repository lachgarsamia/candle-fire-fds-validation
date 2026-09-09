# MESH_STUDY_STRATEGY — P04 (in progress)

This is the working plan + interim results for the numerical-uncertainty study.
It becomes `MESH_STUDY_FINDINGS.md` once the runs complete. **Mesh convergence
bounds discretization error only — it says nothing about physical correctness
(that is P05).**

---

## The mesh ladder

| case | deck | near-fire δx | D\*/δx | cells | status |
|---|---|---|---|---|---|
| COARSE | `candle_coarse_dx10.fds` | 10 mm uniform | **1.2** | 0.15 M | ✅ done (150 s) |
| MEDIUM (baseline) | `candle_medium_dx5.fds` | 5 mm uniform | **2.4** | 1.20 M | ⏳ running (t ≈ 30/250 s; ~17 h to go) |
| FINE-2.0 | `candle_fine_nest20.fds` | 2.0 mm nested | **6.1** | 0.97 M (3 ranks) | deck ready, not launched |
| FINE-1.5 | `candle_fine_nest15.fds` | 1.5 mm nested | **8.1** | 2.30 M (3 ranks) | deck ready, **multi-day run** |

D\* = 1.21 cm for an 18 W flame. **FDS wants D\*/δx ≈ 10–16 → ~1.2 mm cells →
~90 M cells over the domain.** Not remotely feasible on a workstation. *Every*
mesh we can run is undersampled; the study measures how badly.

**Refinement:** the two uniform meshes (10 → 5 mm) are a clean 2× pair. The
nested meshes break the constant ratio, so GCI (if used) is computed on whichever
monotone triplet exists, with Roache's general (non-integer-r) formula. If the
sequence is non-monotone or the coarse case is qualitatively broken, P04's own
rules say report **that**, not a forced GCI.

Everything except δx is byte-identical across decks (same `make_fds.py`, same
source term / geometry / SURF / ambient / T_END). Confirmed by diffing.

---

## The nested fine-mesh design (FINE-1.5 / FINE-2.0)

Three embedded meshes, every interface exactly 2:1 (FDS's preferred ratio):

| mesh | δx | extent (m) | role |
|---|---|---|---|
| `outer` | dx (6–8 mm) | full domain 1.00 × 0.30 × 0.50 | room + plenum + walls |
| `mid` | 2× core | 0.30 × 0.18 × 0.30 (x 0–0.30, y 0.06–0.24, z 0–0.30) | plume shell, buffers the interface |
| `core` | 1.5 / 2.0 mm | **0.165 × 0.09 × 0.228** (x 0–0.165, y 0.105–0.195, z 0–0.228) | candle + back-wall column T1/T2/T3 + full plume rise to the ceiling jet |

The core is kept as tight as possible — it still must contain the candle
(x = 0.09), the three column probes (x = 0.12, z up to 0.225) and room for the
plume to lean toward the doorway (+x). T5 (ceiling centre, x = 0.35) and the
doorway stack (x = 0.70) sit in low-gradient regions and stay on `outer`.

Launch (multi-mesh → one MPI rank per mesh):
`fds/run_fds.sh fds/runs/candle_fine_nest15.fds` (auto-detects 3 meshes →
`mpirun -n 3`, sets `OMP_STACKSIZE`, `OPAL_PREFIX`, `ulimit`).

---

## ⚠ The compute reality (this is itself a P04 finding)

Measured on this Mac (11 cores, `fds_openmp` / `mpirun`, 5–6 threads):

| mesh | timestep (CFL-limited) | ~steps to 250 s | measured s/step | **wall time to 250 s** |
|---|---|---|---|---|
| 10 mm | 0.014 s | 10 k | 0.2 s | **33 min** ✅ |
| 5 mm | 0.0054 s | 46 k | 1.5 s | **~19 h** |
| 2.0 mm nested | ~0.002 s (est.) | ~125 k | ~1–2 s (est.) | **~2–4 days** |
| 1.5 mm nested | ~0.0015 s (est.) | ~165 k | ~2–3 s (est.) | **~4–7 days** |

The timestep collapses under refinement because the resolved plume develops real
~0.9 m/s updrafts (CFL is pinned at 0.92 on the 5 mm run, at a cell in the plume
near the ceiling). Cells scale ~8× per halving, timestep ~2–3×, so each
refinement is ~15–25× more expensive. **A properly-resolved (D\*/δx ≈ 10) candle
compartment simulation is an HPC-scale job, not a workstation one.** For a study
whose whole point is numerical sensitivity of tiny fires, that is a headline
result, not an inconvenience.

---

## Interim results

### COARSE (10 mm, D\*/δx = 1.2) — plume fully collapsed

HRR conserved (18.00 W = 100 % of prescribed), but at t = 150 s:

| probe | exp R1 rise | FDS 10 mm rise |
|---|---|---|
| T1 (plume, z = 0.05) | **+111 °C** | **+1.3 °C** — never crosses 60 °C (exp: +37 s) |
| T2 (z = 0.16) | +26 °C | +3.7 °C |
| T3 (ceiling @ fire) | +39 °C | **+0.0 °C** |

The non-monotonic column is absent; nothing reaches the ceiling. At D\*/δx = 1.2
FDS cannot sustain a coherent candle plume. p_box +374 Pa (sealed).

### MEDIUM (5 mm, D\*/δx = 2.4) — ceiling layer forms, plume column still cold

At t = 30 s (ignition ramp just ending; run continues):

| probe | FDS 5 mm rise | vs 10 mm |
|---|---|---|
| T1 (plume, z = 0.05) | **+0.5 °C** | still cold |
| T2 (z = 0.16) | +0.3 °C | still cold |
| T3 (ceiling @ fire) | **+21 °C** (bead) / +26 °C (gas) | **was +0.0 → big improvement** |
| T5 (ceiling centre) | +0.6 °C | — |

**Refinement 10 → 5 mm rescued the ceiling hot layer (T3) but NOT the near-source
column (T1, T2).** The FDS plume at 5 mm is a thin fast jet that reaches the
ceiling without the wide floor-level flame/plume region the experiment's T1 sits
in. T1 is 1.2 cm (≈ 2.4 cells) from the burner edge — right in the plume shear
layer — so it is the single most mesh-sensitive probe, exactly as the baseline
notes predicted. **The model's structure (T3 ≫ T1 ≈ T2) is still qualitatively
opposite to the experiment (T1 ≫ T3 > T2).** Whether finer meshes fix this — by
widening the resolved plume so T1 enters it — is the open question the FINE runs
would answer.

---

## Recommended path (needs your call)

The full ladder as specified is not achievable here in a sensible time. Options,
best first:

1. **Let MEDIUM finish (~17 h), then run FINE-2.0 to a short T_END (120 s, ~1–2
   days).** 120 s is enough to see whether a better-resolved plume develops T1
   (exp T1 crosses 60 °C at +37 s, 100 °C at +140 s). Gives a 3-point sequence
   (10 / 5 / 2 mm) for the near-fire metric — likely non-monotone for T1, which
   is a legitimate reported result. Skip FINE-1.5 (4–7 days) unless FINE-2.0
   shows T1 is still climbing with refinement.
2. **Stop MEDIUM at 150 s** (it will have shown the stable T1/T3 pattern by then;
   ~9 h from now), free the machine sooner for FINE-2.0.
3. **Accept 5 mm as the finest feasible.** Report the numerical uncertainty as
   *"not converged"*: the ceiling/layer structure is plausibly within tens of %
   between 5 mm and finer; **T1 (plume) is not mesh-converged and the model
   value there is unreliable — the 10→5 mm change was +0.5 °C vs an experimental
   +111 °C, and the trend does not point at the measurement.** Carry that into
   P05 as a hard caveat rather than a ± band.
4. **Move the fine runs to a cluster** ← **CHOSEN (user, 2026-09-02).**

## Cluster package (`fds/cluster/`)

| file | δx | D\*/δx | cells | ranks |
|---|---|---|---|---|
| `candle_fine_nest20_cluster.fds` | 2.0 mm | 6.1 | 0.97 M | 24 (one mesh/rank) |
| `candle_fine_nest15_cluster.fds` | 1.5 mm | 8.1 | 2.30 M | 24 |
| `candle_fine.batch` | — | — | — | SLURM template |
| `README.md` | — | — | — | run steps, restart, what to send back |

3-level embedded nest (outer 6–8 mm ⊃ mid ⊃ core), every interface 2:1. Each
level pre-split into sub-meshes (`outer_*` ×6, `mid_*` ×6, `core_*` ×12),
`MPI_PROCESS = 0..23`. Byte-identical to the local decks except δx.

Local validation: the deck passes FDS `read_input` + mesh setup and writes its
`.smv` (the 2:1 nest interfaces are accepted). The Mac's bundled Open MPI aborts
in an init Allreduce unless `OMPI_MCA_btl=self,vader` — a Mac quirk, not a deck
bug; a cluster MPI won't hit it. `fds/run_fds.sh` carries the workaround.

**Still need from the user to finalize:** cluster scheduler (SLURM assumed),
cores per node + target rank count (24 is the default split), FDS module/version
(6.7.1 on the FireScope cluster is old — confirm namelist compatibility),
account + partition + max wall-time.

## The fine run's job: DISCRIMINATE two hypotheses about T1

T1 (0.12, 0.15, 0.05) reads **+111 °C** in the experiment; FDS gives +1.3 °C
(10 mm) → +0.5 °C (5 mm, at t = 35 s). T1 sits ~1.2 cm behind the candle at
floor level — in the real fire that is **inside the luminous flame / plume
root**, not in the free buoyant plume above it. Two distinct explanations, both
legitimate and publishable:

| | hypothesis (a) — **under-resolution** | hypothesis (b) — **model-structural** |
|---|---|---|
| claim | the plume/flame *is* hot at T1, but at ≥ 5 mm the resolved plume is a thin fast jet 2–3 cells wide that misses the probe | T1 sits in the thin luminous reaction zone; a **prescribed-HRR LES spreads that heat over the burner cell volume** and cannot reproduce the peak flame temperature there **at any affordable mesh** |
| fine-run signature | **T1 rises** toward ~100+ °C as δx → 1.5 mm; `Tmax_T1cell` and the rake show a hot core reaching the probe | **T1 stays low** (tens of °C) even at 1.5 mm; `Tmax_core` may be high but confined to a 1–2 cell layer right at the burner, with the rake cold a few mm above |
| consequence for P05 | T1 is recoverable with mesh → the gap is numerical, extrapolate | T1 (and the non-monotonic column) is **outside what this modelling approach can predict** — report as a model limitation, compare only T2/T3/T5/doorway |

**Instrumentation added to the fine decks for this** (`--discriminate`, auto-on
for nested runs):
* a 6 × 5 **rake** of `TEMPERATURE` DEVCs, x ∈ {0.075…0.150}, z ∈ {0.02…0.10} —
  maps the local field so we can see whether T1 is at the *edge* of a hot region
  (a) or in a *broadly cold* one (b);
* `Tmax_core` and `Tmax_T1cell` — peak gas T over the core block and over the T1
  neighbourhood;
* `HRRPUV` slice at y = 0.15 and a `TEMPERATURE` slice at x = 0.12 (through the
  column probes) — shows where the reaction zone actually is relative to T1.

The fine run is **not** just an error bar on T1 — it decides which of (a)/(b)
holds. **Regardless of outcome, P05 treats T1 as not-mesh-converged** (do not
extrapolate a validation metric from it); the (a)/(b) verdict determines whether
T1 is *reported as a numerical gap* or *as a model limitation*.

## Numerical-uncertainty statement so far (interim, pre-fine)

* T3 / ceiling layer: +0.0 → +21 °C (10 → 5 mm) — improving fast, plausibly
  within tens of % of a resolved value by ~2 mm. This is where a GCI-style band
  is meaningful.
* T1 / plume column: +1.3 → +0.5 °C vs experiment +111 °C — not converging;
  hypothesis (a)/(b) pending the fine runs.
* Doorway (T9/T10/T11): all near ambient in both the experiment and FDS so far;
  low signal, low sensitivity.
