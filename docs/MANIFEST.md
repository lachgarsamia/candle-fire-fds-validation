# MANIFEST — decks, runs, figures, reproducers

Everything needed to re-run the study from the record. Job IDs are Pleiades
(Bergische Universität Wuppertal, account `cobra`, FDS 6.11.1).

---

## 1 · FDS decks (`fds/`)

Every deck is emitted by `fds/make_fds.py`; only the flags below change.

| deck | mesh | walls / source | generator command |
|---|---|---|---|
| `runs/coarse/candle_coarse_dx10.fds` | 10 mm uniform | baseline | `python fds/make_fds.py --dx 0.010 --t-end 150 --chid candle_coarse_dx10 --no-smoke` |
| `runs/medium/candle_medium_dx5.fds` | 5 mm uniform | baseline | `python fds/make_fds.py --dx 0.005 --t-end 250 --chid candle_medium_dx5 --no-smoke` |
| `cluster/candle_fine_nest20_mpi.fds` | 2.0 mm nest (7 mesh) | baseline | `python fds/make_fds.py --dx 0.008 --fine-dx 0.002 --cluster --t-end 150 --chid candle_fine_nest20_mpi --no-smoke` |
| `cluster/candle_fine_nest15_mpi.fds` | 1.5 mm nest (7 mesh) | baseline | `python fds/make_fds.py --dx 0.006 --fine-dx 0.0015 --cluster --t-end 250 --chid candle_fine_nest15_mpi --no-smoke` |
| `sweep/s0_base_dx5.fds` | 5 mm split 4×1×2 | baseline | `bash fds/sweep/make_sweep.sh` (writes s0–s7 + m2) |
| `sweep/s1_hrr15` / `s2_hrr21` | 5 mm | HRR 15 / 21 W | `--hrr-w 15` / `--hrr-w 21` |
| `sweep/s3_rad20` / `s4_rad35` | 5 mm | χr 0.20 / 0.35 | `--rad-fraction 0.20` / `0.35` |
| `sweep/s5_wallins` | 5 mm | PMMA, INSULATED backing | `--wall pmma-insulated` |
| `sweep/s6_walladi` | 5 mm | ADIABATIC walls | `--wall inert` |
| `sweep/s7_tracer` | 5 mm | + passive fog-analogue tracer | `--tracer` |
| `sweep/m2_base_nest20_450.fds` | 2.0 mm nest | baseline, T_END 450 s | `--dx 0.008 --fine-dx 0.002 --cluster --t-end 450` (+ hand-add `DT_RESTART=7200`) |
| `sweep/w1_ir.fds` | 5 mm | PMMA ε 0.85 (M4) | `--wall pmma-ir` |
| `sweep/w2_thinceil.fds` | 5 mm | 4 mm air-backed ceiling (M4) | `--wall thin-ceiling` |
| `sweep/w3_thinall.fds` | 5 mm | whole rig 4 mm sheet (M4) | `--wall thin-all` |
| `sweep/w4_contact.fds` | 5 mm | k = 0.10 lumped contact (M4) | `--wall contact` |

Launch on the cluster: `module --force purge && module load FDS/6.11.1 ;
export OMP_NUM_THREADS=4 OMP_STACKSIZE=200M ; mpiexec fds <deck>` with
`--ntasks` = mesh count (7 for the nests, 8 for the `sweep/*` decks, 1 for
`coarse`). See `fds/sweep/submit_sweep.sh` and `fds/cluster/candle_fine.batch`.

---

## 2 · Completed runs

| CHID | mesh | T_END | reached | ranks | job ID | status | feeds |
|---|---|--:|--:|--:|---|---|---|
| `candle_coarse_dx10` | 10 mm | 150 s | 150 s | 1 | (local) | ✓ complete | P04 mesh ladder |
| `candle_medium_dx5` | 5 mm | 250 s | **35 s** | 1 | (local) | ⚠ wall-clock stop | P04 ladder (transient only) |
| `candle_fine_nest20_mpi` | 2.0 mm | 150 s | 150 s | 7 | (Pleiades) | ✓ complete | **P05 validation baseline**, T3/T1 figures, rake |
| `candle_fine_nest15_mpi` | 1.5 mm | 250 s | **65 s** | 7 | 21818195 | ⚠ TIMEOUT (24 h) | P04 ladder (4th point), T3 convergence |
| `s0_base_dx5` | 5 mm | 350 s | 350 s | 8 | 21913120 | ✓ complete | M3 reference for all deltas |
| `s1_hrr15` / `s2_hrr21` | 5 mm | 350 s | 350 s | 8 | 21913122 / 21913124 | ✓ complete | M3 HRR band |
| `s3_rad20` / `s4_rad35` | 5 mm | 350 s | 350 s | 8 | 21913125 / 21913126 | ✓ complete | M3 radiative-fraction band |
| `s5_wallins` | 5 mm | 350 s | 350 s | 8 | 21900243 | ✓ complete | M3 wall — insulated |
| `s6_walladi` | 5 mm | 350 s | 350 s | 8 | 21900244 | ✓ complete | M3 wall — adiabatic bracket |
| `s7_tracer` | 5 mm | 350 s | 350 s | 8 | 21913128 | ✓ complete | M2 smoke (tracer transport) |
| `m2_base_nest20_450` | 2.0 mm | 450 s | **417 s** | 7 | 21899510 | ⚠ TIMEOUT (48 h), checkpointed | M3 T3-vs-run-length (the decisive flat curve) |
| `w1_ir` | 5 mm | 350 s | — | 8 | 21935051 | ⏳ running | M4 wall test |
| `w2_thinceil` | 5 mm | 350 s | — | 8 | 21935344 | ⏳ running | M4 wall test |
| `w3_thinall` | 5 mm | 350 s | — | 8 | 21935345 | ⏳ running | M4 wall test |
| `w4_contact` | 5 mm | 350 s | — | 8 | 21935052 | ⏳ running | M4 wall test |

Superseded (cancelled): `s5/s6` first attempt 21899511 / 21899512 (2-rank,
CPU-starved — resubmitted 8-rank); stage-2 first attempt 21913104–108 (submitted
with `--ntasks=2`, MPI-process error in 8 s).

Device CSVs committed under `fds/runs/<name>/<chid>_devc.csv` (+ `_hrr.csv`);
bulky `.s3d/.sf/.bf` and per-step `.out` logs are git-ignored.

---

## 3 · Figures → what they feed

| figure | script | reproducer | used by |
|---|---|---|---|
| `cone_*` (6) | `src/cone_analysis.py` | `python src/cone_analysis.py` | CONE_FINDINGS |
| `report_cone_characterization.png` | `src/report_figs.py` | `python src/report_figs.py` | report Phase-1 |
| `exponat_*` (9) | `src/exponat_analysis.py` | `python src/exponat_analysis.py` | EXPONAT_FINDINGS |
| `report_compartment_structure.png` | `src/report_figs.py` | `python src/report_figs.py` | report Phase-2 |
| `report_study_schematic.png` | `src/report_figs.py` | `python src/report_figs.py` | report / talk opener |
| `fds_baseline_vs_R1.png` | `src/fds_post.py` | `python src/fds_post.py` | MESH_STUDY |
| `p05_T3_convergence.png`, `p05_T1_nearfield.png` | `src/p05_validation.py` | `python src/p05_validation.py` | VALIDATION §3/§4, MESH_STUDY |
| `validation_7TC_grid.png` | `src/fig_validation_grid.py` | `python src/fig_validation_grid.py` | VALIDATION, report |
| `m3_T3_wall_bracket.png`, `m3_tracer_fill.png` | `src/m3_figs.py` | `python src/m3_figs.py` | SENSITIVITY §2/§4 |
| `m4_wall_variants.png` | `src/m4_post.py` | `python src/m4_post.py` (after M4 lands) | SENSITIVITY §M4 |
| `fog_3276_calibcheck.png` | `src/fog_digitize.py` | (manual; needs the video) | SMOKE_FINDINGS |

---

## 4 · Analysis reproducers (one command each)

```bash
python src/cone_analysis.py        # -> data/processed/cone_*,   figures/cone_*
python src/exponat_analysis.py     # -> data/processed/exponat_*, figures/exponat_*
python src/fds_post.py             # cross-mesh table -> data/processed/fds_post_digest.json
python src/p05_validation.py       # three-uncertainty split -> data/processed/p05_three_uncertainty.csv
python src/fig_validation_grid.py  # figures/validation_7TC_grid.png
python src/sensitivity_post.py     # M3 -> data/processed/sensitivity_{bands.csv,tables.md}
python src/m3_figs.py              # figures/m3_*
python src/m4_post.py              # M4 -> data/processed/m4_wall_test.md  (needs the w* runs)
python src/report_figs.py          # figures/report_*
```

Environment: `numpy scipy matplotlib imageio` + the FireScope IO helpers
(`FIRESCOPE_SRC=/path/to/FireScope/src`). All paths resolve from the repo root
via `src/_repro.py`.

---

## 5 · Data provenance

| file | contents |
|---|---|
| `data/raw/compartment/2026-08-27_exponat_R{1,2,3}.txt` | 40-channel DAQ export, 7 thermocouples live + `event_number` |
| `data/raw/cone/{25,26,27}082026_*Candle*_R*.csv` | cone-calorimeter runs (heater off, free-burning) |
| `data/raw/cone/weights.csv` | manual before/after candle weigh table (the HRR anchor) |
| laser-sheet fog footage | `/Volumes/room_corner/Samia/7L5A{3276,3277,3278}.MP4` — **not in the repo**; ignition anchors in SMOKE_FINDINGS §2 |
