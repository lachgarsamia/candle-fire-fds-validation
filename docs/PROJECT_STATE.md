# PROJECT STATE — Candle compartment fire: experiment + FDS validation

Single source of truth for the agent. Read this first, every session. It records
what is SETTLED (do not re-litigate), what is IN PROGRESS, and what is NEXT.

## The study in one sentence
Characterize a free-burning tea-light fire from cone-calorimeter data, reconstruct
the compartment experiment in FDS, and quantify where simulation agrees and
disagrees with the measured temperature and smoke evolution — separating
numerical, experimental, and model uncertainty rather than tuning to match.

## SETTLED FACTS (do not re-derive, do not re-ask the human)

### Fire source
- Tea lights are FREE-BURNING (cone heater OFF; HFM≈0). Never cite "75 kW/m²".
- Wax = paraffin. ΔHc = 42 MJ/kg, combustion efficiency χ = 0.9 → ΔHc_eff ≈ 38 MJ/kg.
- Per-candle steady output ≈ 18 ± 2 W (Route C: manual Δm × ΔHc_eff / burn time).
  [CONFIRMED — CONE_FINDINGS.md. Single-candle anchor 20.0 W; 3-candle per-candle
  18.2 ± 1.5 W (CoV 8.5%); long-protocol rate cross-check +14%. Working FDS value
  18 W/candle, HRRPUA ≈ 17 kW/m². Total source-term uncertainty ±15-20% (wax
  ΔHc/χ is the dominant unresolved term — O₂ data could NOT pin it empirically:
  ΔHc_implied scattered 25-110 MJ/kg). Burn is LINEAR (r²>0.999) → constant
  source, step on at ignition / off at flameout, no HRR(t) curve.]
- Candle cup: aluminium, diameter ≈ 37 mm, ~1 cm wax depth.
  Burner area ≈ 1.08e-3 m² → HRRPUA ≈ 17 kW/m² at 18 W.
- Mass is ground-truth from the manual weigh table (data/raw/cone/weights.csv), NOT load cells.
- 3 candles behave ≈ independently: superposition ratio (3-cand total / 1-cand)
  = 2.73 vs 3.0 ideal → ~9% per-candle suppression (within the 8.5% run scatter).
  MODEL 3 CANDLES AS SEPARATE BURNERS (~18 W each), not one merged source.
  [CONFIRMED from cone — CONE_FINDINGS.md §4.3.]

### Compartment geometry (see FDS_geometry_reference.md — authoritative)
- Domain 1.00 (x) × 0.30 (y) × 0.50 (z) m.
- Room 0.70 × 0.30 × 0.23 m, on the domain floor at the back wall (x=0).
  Walls acrylic (PMMA), 10 mm thick — NOT thermally inert, needs real SURF props.
- Doorway: left wall (x=0.70), floor level, 0.15 m high × 0.05 m wide, depth-centered.
- Candle at x=0.09, y=0.15, floor.
- 7 thermocouples, all at depth-center y=0.15:
  T1/T2/T3 on back wall at x=0.12, z=0.05/0.16/0.23
  T5 ceiling center x=0.35, z=0.23
  T9/T10/T11 doorway x=0.70, z=0.015/0.075/0.14

### Smoke tracer (Phase 4 only)
- Glycerinum 85% on the candle cup BEFORE lighting; vaporizes with the flame,
  rises with the plume. Order: glycerin → light → smoke develops from ignition.
- Model in FDS as a passive tracer at the candle, from t=0 of the burn. Not soot.
- Video clock and DAQ clock NOT synced → align on candle-lighting; carry sync
  uncertainty (~±3 s). event_number in the Exponat data is likely the event log.

### What the Exponat data actually contains (from RECON §B.4)
- 7 live thermocouples + exp_time + event_number. THAT IS ALL.
- Every heat-flux gauge dead (sentinel). mass_loadcell dead (-999999).
- CONSEQUENCE: compartment-side validation is TEMPERATURE + EVENT TIMING ONLY.
  Do not design comparisons around flux or compartment mass — they don't exist.
- exp_time is non-uniform (~1.02 s, skips, -1 for pre/post-roll). Use the real
  time vector, never a fixed-fps assumption. Merge split-write row pairs.
- event_number 0→4 at operator times (R1 213/303/334/489; R2 24/73/371/772;
  R3 17/47/303/403 s) — meaning to be mapped to real events by the human.

### VERIFIED temperature findings (R1, checked directly against the data)
Column indices (R1): TC_01=2, TC_02=3, TC_03=4, TC_05=6, TC_09=10, TC_10=11,
TC_11=12; exp_time=63. TC mapping CONFIRMED by physics:
- TC_01 (back wall z=0.05, plume) = HOTTEST, peak 136.6 °C. It's the plume sensor.
- Back-wall column is NON-MONOTONIC in height: T1(136) ≫ T3(64, ceiling) >
  T2(51, middle). Plume-dominated low, layer-dominated high. FDS must reproduce
  this non-monotonic column — not just "hotter near ceiling".
- Ceiling is NOT uniform: TC_03 (ceiling near fire) 64 °C vs TC_05 (ceiling center)
  29 °C — strong horizontal gradient, hot layer localized over the fire. Room is
  NOT well-mixed. A demanding, specific validation target.
- Doorway stack orders correctly by height: TC_09 (floor, z=0.015) ~cool inflow
  25 °C; TC_11 (top, z=0.14) warm outflow 30 °C. Classic vent signature — working.
- These are R1 peaks; P02 must repeat per run and align to inferred ignition.

## STATUS

| phase | prompt | status |
|---|---|---|
| Cone recon | P00 | DONE (RECON.md) |
| Cone analysis | P01 REVISED + data/raw/cone/weights.csv | **DONE** (CONE_FINDINGS.md, src/cone_loader.py, src/cone_analysis.py, figures/cone_*, data/processed/cone_*) |
| Exponat recon | (folded into RECON §B.4) | DONE |
| Exponat analysis | P02 | **DONE** (EXPONAT_FINDINGS.md, src/exponat_loader.py, src/exponat_analysis.py, figures/exponat_*, data/processed/exponat_*) |
| FDS baseline | P03 | **DECK DONE + RUN**. Sealed box, T_END=150-250. coarse(10mm) + nest20(2mm) complete; nest15(1.5mm) partial. FDS_BASELINE_FINDINGS.md TODO. |
| Mesh study | P04 | **DONE — MESH_STUDY_FINDINGS.md FINAL** (2026-09-07). 1.5 mm restart deliberately skipped (conclusion independent of it). T1/T2 gap = MODEL-STRUCTURAL (hyp. b): rake shows prescribed-HRR plume is a column locked to x=0.09, gets narrower+hotter as dx→1.5mm, never reaches T1 at x=0.12. T5/T9/T10 converged, within exp uncertainty (±1.5 °C band). T3 right structure, grid-sensitive (non-monotone 10→5→2→1.5 mm), best est +18±3 °C; matches measurement at t=65 s, gap to +43 peak is wall-storage timescale. HRR=0.018 kW exact on all meshes. |
| Validation | P05 | **DONE — VALIDATION_FINDINGS.md** (2026-09-07, rigor pass). Verdict: compartment-scale (far-field T + doorway) validated within experimental uncertainty (≤1 °C residual); T3 agrees at matched sim time (+19.9 vs +20.2±5.0 at 65 s), gap to +43 peak = wall-thermal-mass timescale + secondary D*/δx<10, not separable — NOT a standalone failure; T1/T2 structural (prescribed-HRR LES, no reaction zone). Fine-mesh scope bounded t≤65 s. TC_03 data trace raw→EXPONAT→VALIDATION verified consistent. Three-uncertainty split: data/processed/p05_three_uncertainty.csv. Figs: figures/p05_T3_convergence.png, figures/p05_T1_nearfield.png. Repro: src/p05_validation.py. |
| Report summary | — | **DONE — REPORT_SUMMARY.md** (2026-09-07). 2-3 pp supervisor-facing synthesis of P01/P02/P05 + future work (smoke, 1.5 mm restart, longer runs, pyrolysis source). |
| Post-M1 roadmap | — | **M2_M3_PLAN.md is canonical** (re-sequenced 2026-09-08). Order: P1 T3-wall-heating (2mm→450s) → P2 T3 wall-attribution (insulated/adiabatic) → P3 source-uncertainty sweep (HRR/χr) → P4 smoke (gated on video) → P5 numerical finalization. |
| P1-P3 M3 sweep | — | **DONE (2026-09-10) → docs/SENSITIVITY_FINDINGS.md**. 8 runs completed on Pleiades. Result: source knobs (HRR ±3W, χr 0.20-0.35) move no sensor >2.5 C. **T3 residual = wall heat-sink model** — m2 (2mm) held T3 flat +16 C from 60s to 410s (run length RULED OUT, refutes the P05 hedge); s0≡s5 (back-face condition irrelevant, heat penetrates only ~6mm of the 10mm slab); s6 adiabatic → T3 +60 C climbing. Modelled 10mm opaque PMMA ~2x too strong a sink; T3 ∈ [+16,+60], truth near low-sink end. T1/T2 structural unchanged (adiabatic only heats the whole room). Figures: figures/m3_T3_wall_bracket.png. VALIDATION_FINDINGS §1/§4/§8 + MESH_STUDY §4 + REPORT_SUMMARY updated. |
| P4 smoke | — | **DONE (2026-09-10) → docs/SMOKE_FINDINGS.md COMPLETE**. Passive tracer s7_tracer (cup-side `&SURF FOG_SRC`, MASS_FLUX=1e-5; NOT on the HRRPUA burner — scales off heat release, 1.5e10 kg/s/m2 bug). Model reproduces the video: gradual fill over minutes, tr_upper/tr_lower → 1.3 by ~100s (near-uniform), weak plenum leakage, no sharp interface. In the observable window (fog visible +150s) model+video agree. FDS compartment FLOW model sound. Figure: figures/m3_tracer_fill.png. Frame-level fog_digitize optional, not done. |
| M4 wall test | — | **DONE (2026-09-11) → docs/SENSITIVITY_FINDINGS.md §M4**. 4 runs (w1_ir emissivity+IR-transp., w2_thinceil air-gap ceiling, w3_thinall whole-rig thin sheet, w4_contact lumped contact-resistance bracket), each a one-sentence physical hypothesis, run once, not tuned. **Result: none moved T3** — all four land +22.3 to +23.1 °C at 350s, within 0.6 °C of baseline +22.5 °C (inside the 5mm mesh-noise band); far field and T1/T2 untouched. Reported as a negative result per the no-tuning rule — the wall-model mechanism is NOT resolved to a single cause (combination / unmodelled geometric detail / resolution remain open). T3 stays the bracket [+16,+60] °C. Figure: figures/m4_wall_variants.png. VALIDATION_FINDINGS §1/§4 updated. |
| multi-session | — | 2026-09-08: peers firescope-f3 / firescope-68 active — NO collision with experiments/. This session owns cluster + make_fds.py + fds/sweep/*. |

### P03/P04 decisions (CONFIRMED by user 2026-09-02)
- SEALED box (overrides P03 prompt's "open boundaries"). T_END = 250 s.
- Run COARSE + MEDIUM first; decide FINE only after seeing whether they converge.
- FDS launch: `fds/run_fds.sh` -- meshes <10 mm SIGSEGV without OMP_STACKSIZE=200M.

### P04 progress -- see MESH_STUDY_STRATEGY.md
- COARSE (10 mm, D*/dx=1.2): DONE. PLUME FULLY COLLAPSED. HRR conserved (18 W),
  but T1 +1.3 C (exp +111), T3 +0.0 C (exp +39). No plume, no ceiling layer.
- MEDIUM (5 mm, D*/dx=2.4): RUNNING, SLOW. t~30/250 s at 11:20; ~17 h to go
  (CFL pinned at 0.92 -- the 5 mm plume develops real 0.9 m/s updrafts).
  Interim: 10->5 mm RESCUED the ceiling layer (T3 +21 C) but NOT the plume
  column (T1/T2 still ~+0.5 C). Structure still opposite to experiment.
- LOCAL 5 mm run: KILLED per user (cluster supersedes). Partial data kept to
  t=35 s in fds/runs/medium/ (T3 +21 C, T1 +0.5 C -- consistent with the trend).
- FINE: user runs on CLUSTER = **Pleiades**. Package fds/cluster/: nest20
  (2.0 mm, D*/dx 6.1, 0.97M) + nest15 (1.5 mm, D*/dx 8.1, 2.30M), 24-mesh/24-rank
  3-level 2:1 embedded nest + candle_fine.batch (SLURM template) + README.
  Decks FULLY VALIDATED on local FDS 6.11.1 (parse + species setup + 3-mesh align
  + all DEVC/SLCF accepted, .smv written, steps cleanly). Portable TC = gas
  TEMPERATURE (bead model commented, optional).
- FDS-6.11.1 nested-deck fix chain (2026-09-02/03, each isolated by bisection;
  all baked into make_fds.py):
  1. fuel: `&REAC FUEL='PARAFFIN', FORMULA='C25H52'`, NO standalone `&SPEC`.
  2. TWO-LEVEL nest only: core(fine_dx) inside outer(4*fine_dx), 4:1. A 3-level
     nest (core<mid<outer) HANGS FDS 6.11.1 in read_input on this build (proven
     with trivial decks: 2-level embedded runs, 3-level does not). mid removed.
  3. every core face snapped to the outer grid; cluster sub-meshes split on a
     SHARED hierarchical cut set (CLUSTER_CUTS) -> no core mesh straddles an
     outer-mesh face. check_nesting.py verifies alignment + single-parent.
  4. core mesh z-max = 0.24 (was 0.228): the ceiling OBST (z 0.23-0.24) partly
     overlapping the core's x,y but above its z-max mis-snaps to zero thickness
     -> malloc corruption. Core now fully contains the ceiling slab.
  5. burner = VENT on a 1-outer-cell INERT block. Bare floor vent is REJECTED
     where it overlaps the sealed ZMIN wall (-> 0 HRR); burning OBST trips
     ERROR 607 BURN_AWAY on the coarse mesh.
- VALIDATED on local FDS 6.11.1: single-mesh decks step; the **2-mesh nest15**
  full deck (sealed box + room OBSTs + HOLE + 37 DEVCs + 4 SLCF + raised burner)
  STEPS CLEANLY, radiation on, 7+ steps, no malloc / ERROR 607 / VENT-reject.
- 22-mesh cluster decks (nest15_mpi, nest20_mpi = 10 outer + 12 core):
  check_nesting.py PASS. Cannot run on this 11-core Mac -- 22 oversubscribed
  ranks hang/abort in the sealed-pressure init collective (fds_IP_initialize
  Allreduce). Hardware limit, not a deck bug (the 2-mesh = same geometry cut
  into valid pieces, and it works). Final "Time Step 1" check is on a Pleiades
  debug node (README sanity-check #1). Fallback: 2-mesh + OpenMP form, proven.
- fds/cluster/: candle_fine_nest15.fds + nest20.fds (2-mesh, mpirun -n 2 + heavy
  OpenMP -- the proven form) + _mpi variants (22-rank) + candle_fine.batch +
  README.md + ../check_nesting.py. make_fds.py flag is `--cluster`.
- PLEIADES jobs 21815302 / 21817576 (candle_fine_nest15_mpi, 22 tasks): WASTED --
  two problems, both now fixed:
  A. `Number of MPI Processes: 1` -- Pleiades FDS/6.11.1 is Intel MPI 2021.15;
     plain `srun fds` does NOT wire up Intel MPI's PMI ("MPI startup(): PMI
     server not found" x22). All 22 meshes ran on ONE rank -> glacial, CFL ~3e-4.
     `srun --mpi=pmi2` did NOT help; there is no libpmi2.so on the system
     (`ls /usr/lib64 | grep pmi` -> only libpmix.so.2). `srun --mpi=list` -> none,
     cray_shasta, pmi2, pmix.
     **FIX (confirmed, official): use `mpiexec fds <deck>`, NOT srun.** The
     FDS-on-Pleiades guide (firedynamics.github.io/LectureFireSimulation
     .../02_hpc/03_parallel_fds.html, same group that builds the module) uses
     `mpiexec fds ./*.fds` -- Intel-MPI Hydra reads the SLURM allocation itself
     and starts one rank per --ntasks. Module: `module use -a ~larnold/modules/`
     then `module load FDS/6.11.1`.
  B. 13k+ "VENT 7 overlaps VENT 5 ... rejected" -- the user had the OLD deck
     (floor burner colliding with the sealed ZMIN wall) -> ~0 HRR. FIXED:
     current decks raise the burner onto a 1-cell INERT block (z=6mm). The deck
     now on Pleiades DOES have "burner top" (verified there: grep -> 1,
     check_nesting.py -> the OK line); the stale-deck VENT-reject spam was from
     runs before the file was refreshed.
  User has account=cobra partition=normal.
- PLEIADES 2026-09-02, working launch found:
  * `module purge && module load FDS/6.11.1` (NOT `module use -a ~larnold/modules/`
    -- that breaks resolution of the "2025" stack meta-module in batch).
  * `mpiexec fds <deck>` -- Intel-MPI Hydra reads the SLURM allocation. srun
    does not. `#!/bin/bash -l` login shell so `module` is defined.
- 22-mesh `_mpi` decks (10 outer + 12 core): confirmed to WEDGE FDS 6.11.1 in
  init on the real cluster too -- job 21817950, ~6.2 GB RSS/rank, 7 min, no
  timestep, then killed. NOT oversubscription (22 ranks on 44 real cores). The
  outer split (embedded core meshes coupling across internal outer boundaries)
  is the suspect. RETIRED.
- 2-mesh decks (candle_fine_nest15/20.fds, MPI_PROCESS 0/1): STEP CLEANLY on
  Pleiades (`mpiexec`, --ntasks=2 --cpus-per-task=32). Jobs 21818071 (2mm) +
  21818091 (1.5mm) running T_END=250. But rate ~0.18 s sim / 2 min wall -> will
  NOT finish 250 s in 48 h; kept as insurance (even t~60-80 s shows plume onset).
- NEW 7-mesh decks (make_fds.py --cluster, CLUSTER_CUTS rewritten):
  1 undivided outer + 6 core HORIZONTAL z-slabs (standard plume decomposition,
  simple star connectivity, no embedded interface across an internal outer face).
  check_nesting.py PASS. T_END=150 (README sanctions 120-150 for the
  discrimination question). md5: nest15_mpi d658abb0..., nest20_mpi 11cb19d0...
  candle_fine.batch -> --ntasks=7 --cpus-per-task=4, mpiexec. TEST on
  partition=short first: need "Number of MPI Processes: 7", zero VENT-rejected,
  "Time Step 1" within ~1-2 min (not 7 min of silence). If it also wedges ->
  the split count is the problem; run the 2-mesh form with reduced T_END.
- Deliverable: fds/cluster_package.tgz (4 decks + check_nesting.py + README).
  md5 nest15_mpi = 5a03a34f4302487881be61aff6d1bda5.
- FINE RUN'S JOB (per user): DISCRIMINATE hypothesis (a) T1 low = under-resolved
  [fine run raises T1] vs (b) T1 low = flame/reaction zone a prescribed-HRR LES
  can't represent [fine run leaves T1 low]. Both publishable. Deck has the
  discrimination rake + Tmax + HRRPUV slices. P05 treats T1 as not-converged
  either way; (a)/(b) decides "numerical gap" vs "model limitation".
- INTERIM: 10->5 mm RESCUED T3/ceiling (+0->+21 C) -- GCI-meaningful there.
  T1/plume +1.3->+0.5 C, not converging. Doorway near-ambient both sides.

### Exponat validation targets (P02 — VERIFIED, EXPONAT_FINDINGS.md)
- TEMPERATURE + event timing ONLY (flux/mass channels all dead). 7 live TCs.
- Plume TC_01: 60 °C at ign+37±3 s, 100 °C at ign+140±18 s, broad peak
  110–137 °C at ign+430±30 s. NO steady state — validate the transient.
- Non-monotonic back-wall column: T1(plume) ≫ T3(ceiling) > T2(mid), all runs.
- Hot layer LOCALIZED over the fire: ceiling near-fire (T3, +43 °C) ≫ ceiling
  centre (T5, +5 °C); horizontal ΔT ≈ 40 °C. Room NOT well-mixed.
- Doorway: monotonic by height, T11−T9 ≈ 5 °C, neutral plane low (z ≈ 0.02–0.05).
- Ignition anchor: thermal onset within 1–2 s of an event_number transition
  (which transition # differs per run — event clock is NOT common). ±2 s.
- Primary validation run: R1 (cleanest); R3 = long-duration complement.
- Experimental scatter to beat before blaming FDS: ±7 °C plume peak, ±3–4 °C
  layer/doorway ΔT, ±27 s time-to-peak.

## Execution order for the agent
1. Finish P01 (cone) → produces the confirmed source term.
2. P02 (Exponat) → produces the validation targets (temperature + event timeline).
   Can run in parallel with P01; it shares no inputs.
3. P03 (FDS baseline) → needs P01's HRR and P02's geometry/target confirmation.
4. P04 (mesh study) → needs P03.
5. P05 (validation) → compares P03/P04 against P02.

## Standing rules (all phases)
- Surface discrepancies; never tune toward a desired answer.
- Every scientific number carries units and, where a mean, a spread.
- Separate the three uncertainties: numerical (mesh/timestep), experimental
  (sensor, repeatability), model (source, walls, ventilation). A sim-vs-exp gap
  is NOT automatically "FDS error".
- Reuse FireScope components per RECON Part B rather than rebuilding.
- If a decision here conflicts with the data, STOP and surface it. Otherwise proceed.
