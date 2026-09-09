# FINE-mesh runs for the cluster (P04)

The workstation can't resolve an 18 W candle plume in a sensible time (5 mm ≈ 19 h;
1.5 mm ≈ days). These decks are for a real MPI cluster. Geometry, source term
(18 W paraffin, sealed box) and the 7 TC probes are identical to the local
`candle_coarse_dx10` / `candle_medium_dx5` runs — **only δx changes** (P04 rule).

## Files

| file | δx (near-fire) | D\*/δx | cells | &MESH | how to run |
|---|---|---|---|---|---|
| **`candle_fine_nest15.fds`** | 1.5 mm | 8.1 | 1.85 M | 2 | `mpirun -n 2` + heavy OpenMP — **validated locally, steps cleanly** |
| **`candle_fine_nest20.fds`** | 2.0 mm | 6.1 | 0.81 M | 2 | same, 5× cheaper — run this first |
| `candle_fine_nest15_mpi.fds` | 1.5 mm | 8.1 | 1.85 M | 22 | `-n 22` (10 outer + 12 core) — pure MPI, **re-test first** (see below) |
| `candle_fine_nest20_mpi.fds` | 2.0 mm | 6.1 | 0.81 M | 22 | same |
| `candle_fine.batch` | — | — | — | — | SLURM template (edit the marked lines) |
| `../check_nesting.py` | — | — | — | — | verifies face-alignment **and** single-parent containment |

**2-LEVEL embedded nest**, 4:1: `outer` (6–8 mm, whole box) ⊃ `core`
(1.5–2 mm near-fire block, x 0–0.168, y 0.102–0.198, **z 0–0.24** m — candle +
column T1/T2/T3 + plume rise + the ceiling slab). `outer_dx = 4·fine_dx`.
A **3-level** nest (core<mid<outer) **hangs FDS 6.11.1** in `read_input` on this
build — verified with trivial decks — so the mid level is gone; 4:1 is inside
FDS's supported range and a trivial 4:1 sealed nest steps cleanly.

Every core face is snapped to the outer grid, and the cluster sub-meshes are
split on a **shared hierarchical cut-plane set** so no core mesh straddles an
outer-mesh boundary. `check_nesting.py` verifies both — run it on every deck.

The chain of FDS-6.11.1 fixes that got a nested candle deck to run (each isolated
by bisection): (1) fuel on the `&REAC` not a separate `&SPEC`; (2) 2 levels not
3; (3) faces snapped to the outer grid; (4) core z-max = 0.24 so it fully
contains the ceiling OBST (a partly-overlapping OBST above the core → zero-
thickness → malloc corruption); (5) burner = a VENT on a 1-cell INERT block, not
a floor vent (rejected against the sealed ZMIN wall) and not a burning OBST
(ERROR 607). All five are baked into `make_fds.py`.

### 2-mesh vs 22-mesh

* **2-mesh (`candle_fine_nest15.fds`, default):** `MPI_PROCESS = 0/1`. Parallelism
  is OpenMP (give the core rank most of the node's threads). **Validated locally
  end-to-end** — the full deck (all OBSTs, HOLE, DEVCs, SLCF, sealed box, raised
  burner) steps cleanly on FDS 6.11.1. Load is core-bound (1.15 M cells).
* **22-mesh (`_mpi`):** `outer_*`×10 + `core_*`×12, `MPI_PROCESS = 0..21`, for
  proper MPI parallelism. `check_nesting.py` ✓. This Mac cannot run 22 ranks
  (11 cores — the oversubscribed init collective aborts), so **confirm it
  reaches "Time Step 1" on a Pleiades debug node before the big slot.** If it
  fails there too, fall back to the 2-mesh + OpenMP form (proven).

> Local validation: single-mesh decks and the **2-mesh nest** both step cleanly.
> The 22-rank decks can't be run on this 11-core Mac; they are validated by
> `check_nesting.py` + the fact that they are the 2-mesh geometry cut into
> valid, non-straddling pieces. Final "reaches Time Step 1" check is on Pleiades.

Even 1.5 mm only reaches D\*/δx ≈ 8 — the FDS-recommended 10–16 needs ~90 M cells
(full-domain 1.2 mm), out of scope. Report this in MESH_STUDY_FINDINGS.

## Run

```
mkdir run_nest15 && cd run_nest15
cp ../candle_fine_nest15.fds ../candle_fine.batch .
# edit candle_fine.batch: account, partition, nodes, time, FDS module
sbatch candle_fine.batch
```

Repeat for `nest20`. Do `nest20` first (5× cheaper, tells you if the plume
develops before committing days to `nest15`).

## Runtime expectation

The timestep is CFL-limited by the resolved plume updraft (~0.9 m/s at 5 mm,
faster when better resolved). Rough scaling from the local runs:

| δx | ~dt | steps to 250 s | note |
|---|---|---|---|
| 2.0 mm | ~2 ms | ~125 k | feasible in <24 h on ~48 cores |
| 1.5 mm | ~1.5 ms | ~165 k | may need a 48 h slot or a restart (`&DUMP RESTART`) |

If your slot is shorter than the run: add `&DUMP … DT_RESTART=1800 /` to the deck
and resubmit with `RESTART=.TRUE.` — or just set `T_END=120` (enough to see
whether T1/the plume develops; the experiment's T1 crosses 60 °C at +37 s,
100 °C at +140 s).

## To change the decomposition

The 3-mesh deck is fixed (one rank per level). For a pure-MPI split:
`python ../make_fds.py --dx 0.006 --fine-dx 0.0015 --t-end 250 --chid <name> \
  --split "Ox,Oy,Oz  Mx,My,Mz  Cx,Cy,Cz"` — e.g. `--split "3,1,2 3,1,2 3,2,2"`
gives the 24-rank `_mpi24` deck. Every split plane is forced onto a whole number
of parent cells (`fds/check_alignment.py` verifies). Tell me the Pleiades node
core-count and I'll pick sensible factors.

## What to send back for P05

Per run, just the CSVs (small):

```
<chid>_devc.csv     # T1..T11 (bead + _gas), HRR, p_box, O2_room  -- the validation data
<chid>_hrr.csv      # HRR budget, MLR -- confirms the 18 W is conserved
<chid>.out          # CFL history, timestep, any warnings -- for the numerical record
```

`fds_post.py` (in the parent dir) already reads `fds/runs/<name>/<chid>_devc.csv`
— drop the returned files into `fds/runs/nest15/` etc. and it produces the
cross-mesh table + convergence assessment automatically.

## What this run decides (not just "an error bar on T1")

T1 reads +111 °C in the experiment; FDS gives ~+1 °C at 5–10 mm. T1 sits in the
flame/plume root. The fine run distinguishes:

* **(a) under-resolution** — T1 *rises* toward ~100 °C as δx → 1.5 mm; the rake /
  `Tmax_T1cell` show a hot core reaching the probe → the T1 gap is *numerical*.
* **(b) model-structural** — T1 *stays low* even at 1.5 mm because a
  prescribed-HRR LES can't place the thin luminous reaction zone; `Tmax_core`
  high but confined to 1–2 cells at the burner → T1 is *outside what this model
  can predict*, and P05 validates on T2/T3/T5/doorway only.

The added instrumentation (`rk_*` rake, `Tmax_core`, `Tmax_T1cell`, HRRPUV +
x = 0.12 slices) is there to read this off. Send the slice files back too if the
run produces them (`*_1_*.sf`) — the plume/reaction-zone picture is the clincher.

## FDS version compatibility (confirm before submitting)

All namelists used are ≥ FDS 6.7.0 vintage, so **6.7.1 should parse it**, but
run the 1-min check below on the actual cluster module first. On FDS 6.11.1
(local) the deck fully parses, all 3 nested meshes align, and every DEVC / SLCF
is accepted (`.smv` written, no ERROR). Watch for on an older FDS:

| namelist | since | risk on 6.7.x |
|---|---|---|
| `&REAC FUEL='PARAFFIN', FORMULA='C25H52'` | 6.3 | none. **Do NOT add a standalone `&SPEC ID='PARAFFIN'`** — the double-declaration crashes FDS 6.11.x species setup (`malloc: corrupted top size`, seen on Pleiades 2026-09-02; fixed 2026-09-02). |
| `&REAC RADIATIVE_FRACTION` | 6.0 | none |
| `&DEVC SPATIAL_STATISTIC='MAX' / 'VOLUME INTEGRAL'` | 6.7.0 | OK at 6.7.1; fails on 6.6 |
| `&SLCF CELL_CENTERED` | 6.0 | none |
| `TAU_Q < 0` (t² ramp) | 6.0 | none |
| `&MESH MPI_PROCESS` | 6.0 | none |
| `! &PROP` / `! &DEVC _bead` lines | — | ignored (FDS skips lines whose first non-blank char isn't `&`) — the modelled-bead TCs are OFF by default; gas `TEMPERATURE` is the primary probe |

If the cluster FDS is < 6.7.0, tell me and I'll swap `SPATIAL_STATISTIC` for
explicit point DEVCs.

## Sanity checks on the cluster before the long run

1. **Parse test:** `fds candle_fine_nest20.fds` for ~1 min on a
   login/debug node — must reach "Time Step 1" with no ERROR. (The local Mac
   needed `OMPI_MCA_btl=self,vader`; a real cluster MPI won't.)
2. **Mesh alignment:** FDS prints "ERROR: MESH … not aligned" if a nest interface
   is off — there should be none (generator enforces 2:1).
3. **HRR conserved:** `_hrr.csv` column `HRR` ≈ 0.018 kW after the 25 s ramp. If
   it sags, the plume is starved (a coarse-mesh failure mode) — note it.
4. **First-hour check:** look at `_devc.csv` — `Tmax_core` should climb within
   the first ~30 s. If nothing anywhere in the core heats up, something is wrong
   with the source term on the split meshes.
