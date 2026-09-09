# FDS_BASELINE_NOTES — P03 baseline deck

**Deck:** `fds/candle_baseline.fds` (= `fds/runs/candle_medium_dx5.fds`).
**Generator:** `fds/make_fds.py` — every input traces to a source; only `--dx` /
`--fine-dx` / `--t-end` change between P04 mesh variants.
**FDS:** 6.11.1. **Launch every run through `fds/run_fds.sh`** — the plain `fds`
binary is single-threaded (`fds_openmp` + `OMP_NUM_THREADS=5` gives ~3x), and
**every mesh finer than 10 mm SIGSEGVs in `init_mp_initialize` with the default
8 MB stack** — `OMP_STACKSIZE=200M` + `ulimit -s 65532` fixes it. The script sets
both. (Found the hard way: the 5 mm baseline crashed silently on first launch.)

---

## ⚠ Two things that need your confirmation

### 1. Boundary condition — I followed your correction, which contradicts the P03 prompt

* **P03 prompt says:** *"Open the domain boundaries (OPEN vents) so the room
  breathes through the doorway into an open exterior."*
* **Your message right before P03 arrived says:** *"the OUTER box is CLOSED too…
  The whole system is sealed… the domain boundaries are NOT open… model the outer
  box as closed acrylic walls (PMMA SURF), all faces. The only air the fire ever
  gets is what's trapped in the box at t=0."*

**The deck is SEALED** (all 6 domain faces = `ACRYLIC_WALL`, no `OPEN`) — the
later, explicit instruction wins. Consequences baked in:

* the fire draws only the ~0.13 m³ of air trapped at t=0. An 18 W flame consumes
  ~0.8 % of that O₂ over 250 s (~3.7 % over a full 900 s burn) — **not enough to
  self-extinguish in the baseline window**, but real vitiation over a long burn;
* the box **pressurises** as the gas heats — FDS solves this (single pressure
  zone); `p_box` DEVC tracks it (a few hundred Pa expected);
* no cross-ventilation: the only flow is the buoyant exchange through the doorway
  between room and the closed plenum.

If the box actually has a small leak / port, say so and I'll add one `OPEN` patch.

### 2. T_END = 250 s, not the full R1 burn (546 s post-ignition)

P03 says *"T_END = the primary run's burn duration."* R1's post-ignition record
is 546 s (EXPONAT_FINDINGS §6). **I set 250 s** because:

* the validation-relevant physics is all developed by then — ignition ramp,
  stratification onset (+30–90 s), T1 crossing 60 °C (+37 s) and 100 °C (+140 s),
  the non-monotonic column, the localized ceiling layer;
* the experiment has **no steady state** — just a broad maximum at +430 s then a
  slow decline. Matching the +430 s peak roughly **doubles** the runtime (5 mm
  medium: ~5 h → ~10 h) for a slowly-drifting tail that adds little to the
  numerical-uncertainty question P04 asks;
* P03 says *"Do NOT run huge cases here — a baseline that completes is the goal."*

P05 can extend the winning mesh to 550 s if the tail matters. **Tell me if you
want the full 546 s baseline instead.**

---

## Mesh — D\* and the resolution problem (this is the crux)

**Characteristic fire diameter** D\* = (Q̇ / (ρ∞ c_p T∞ √g))^(2/5), with
ρ∞ = 1.18 kg/m³, c_p = 1005 J/kg·K, T∞ = 298 K, g = 9.81 m/s²:

| fire | Q̇ | **D\*** | D\*/δx @ 10 mm | @ 5 mm | @ 2.5 mm | @ 1.25 mm |
|---|---|---|---|---|---|---|
| 1 candle (baseline) | 18 W | **1.21 cm** | 1.2 | **2.4** | 4.9 | 9.7 |
| 3 candles | 54 W | 1.88 cm | 1.9 | 3.8 | 7.5 | 15 |

**FDS convention wants D\*/δx ≈ 10–16.** For an 18 W candle that means **~1.2 mm
cells** — 833 × 250 × 417 ≈ **87 million** cells over the full domain. Infeasible
here. **This is the headline weak point of the whole FDS effort and it is the
reason P04 exists.** A candle is right at / below FDS's validated envelope; the
study's job is to quantify that, not hide it.

**Baseline = 5 mm uniform** (1.20 M cells, D\*/δx = 2.4). Coarse for the plume by
design — it is the P04 *medium*. The 1 cm smoke-test already showed the symptom:
the plume is 1–2 cells wide and the near-fire probe (T1) sat outside the resolved
plume core while the ceiling heated first — the reverse of the experiment. 5 mm
should be better but is not expected to be converged.

**P04 ladder (2× refinement, near-fire δx):**

| case | deck | near-fire δx | D\*/δx | cells | ~runtime (250 s, this Mac) |
|---|---|---|---|---|---|
| COARSE | `candle_coarse_dx10.fds` | 10 mm uniform | 1.2 | 0.15 M | ~25 min (150 s) — *running now* |
| **MEDIUM (baseline)** | `candle_medium_dx5.fds` | 5 mm uniform | 2.4 | 1.20 M | ~5 h |
| FINE | `candle_fine_nested25.fds` | 2.5 mm nested block + 10 mm plenum | 4.9 | 1.08 M | ~5–8 h |

10 / 5 / 2.5 mm all divide the room dimensions (0.23, 0.30, 0.70) exactly, so the
room height/length don't drift between meshes. The FINE case uses a nested
2.5 mm block over the candle + full plume path (x 0–0.30, y 0.06–0.24, z 0–0.27)
with a 10 mm plenum — P04 tracks the near-fire metric, per its own rules.
Even FINE only reaches D\*/δx ≈ 5 — **none of the affordable meshes are in the
FDS-recommended band**, and MESH_STUDY_FINDINGS.md must say so plainly.

---

## Fixed physical inputs (from the data — NOT tuned to the compartment)

| input | value | source |
|---|---|---|
| domain | 1.00 × 0.30 × 0.50 m | FDS_geometry_reference.md |
| room | 0.70 × 0.30 × 0.23 m, on the floor at x = 0 | geometry ref |
| walls | 10 mm PMMA — `&MATL` k = 0.19 W/m·K, ρ = 1180 kg/m³, c = 1.47 kJ/kg·K, ε = 0.9; `BACKING='EXPOSED'` (outer face loses heat to lab at T∞) | geometry ref + standard cast-PMMA properties |
| doorway | left wall x = 0.70, floor level, 0.05 (y) × 0.15 (z), depth-centred | geometry ref |
| candle | x = 0.09, y = 0.15, floor; 37 mm cup (10.8 cm²) → grid-snapped square (12.25–12.96 cm²) | geometry ref |
| **HRR** | **18 W/candle**, constant, `TAU_Q = −25 s` ignition ramp; HRRPUA = 18 W ÷ snapped area ≈ 14 kW/m² | CONE_FINDINGS §0/§6 (18 ± 2 W; burn linear r² > 0.999 → constant source, not a fabricated HRR(t)) |
| fuel | paraffin C₂₅H₅₂, ΔH_c = 42 MJ/kg, soot yield 0.008, CO yield 0.001 | CONE_FINDINGS (clean flame; cone soot ≈ 0) |
| radiative fraction | 0.25 (small clean candle flame — literature) | assumption, stated; FDS default is 0.35 |
| ambient | 25 °C | Exponat R1 pre-ignition TC median ≈ 25.1 °C (cone rig metadata says 26.8 °C — the *compartment* air was ~25 °C) |
| TC probes | modelled bead (`QUANTITY='THERMOCOUPLE'`, `&PROP DIAMETER = 1 mm, EMISSIVITY = 0.85`) **and** gas `TEMPERATURE`, at the 7 measured (x, y, z); names `T1..T11` match the experiment 1:1 | geometry ref; P03 (bead model for radiation/inertia error, esp. at the in-flame T1) |
| comparison anchor | model t = 0 ↔ experiment inferred ignition (R1), ± 2 s | EXPONAT_FINDINGS §5 |

**T3 / T5** are placed at z = 0.225 (5 mm below the nominal 0.23 ceiling) so the
probe is in ceiling-jet gas, not inside the snapped ceiling OBST, at every mesh.

**3-candle case:** not built here — the Exponat compartment has one candle, so the
baseline is single-candle. `make_fds.py --n-candles 3` emits three separate
burners (CONE_FINDINGS: independent sources) if P05 wants it.

---

## Known weak points (carry into P04 / P05)

1. **D\*/δx ≈ 2–5** across all affordable meshes — far below the FDS-recommended
   10–16. The plume is barely resolved; the in-flame T1 will be the most
   mesh-sensitive quantity. *This is the main numerical-uncertainty driver.*
2. **Tiny-fire / low-Q\* regime.** An 18 W buoyant plume has very low velocities
   (~0.3–0.5 m/s); LES sub-grid models and the FDS combustion model are least
   tested here. Flag every result accordingly.
3. **Wall properties approximate.** "Cast PMMA" generic values; the real acrylic
   grade, and whether the base is acrylic or the wooden table, are not pinned.
   The floor is modelled as acrylic too (per "all faces"). Over a long low-power
   burn the wall heat sink materially sets the compartment temperature — P05
   sensitivity candidate.
4. **Sealed-box assumption** (see above) — if there is any leakage the plenum
   pressure and the long-burn vitiation are both wrong.
5. **Ignition timing / ramp.** `TAU_Q = −25 s` is a plausible-but-assumed candle
   ignition transient; the experiment's real ramp is unknown. ±2 s anchor
   uncertainty (video↔DAQ) sits on top.
6. **Radiative fraction 0.25** is an assumed input, not measured. Affects the
   convective/radiative split that drives the plume vs heats the walls.
7. **Bead diameter 1 mm** assumed for the TC model — the real bead size is not
   documented; matters most at T1.
8. **Cup thermal model:** the aluminium cup is modelled with acrylic side/bottom
   SURFs (tiny object, ~1 cm). Minor.

## What P04 must test
* Does a coherent candle plume even survive at 10 mm? (expected: no)
* Do the **point temperatures** converge with δx — and at what observed order?
* Does the **structure** converge (non-monotonic column T1≫T3>T2; localized
  ceiling layer T3≫T5; doorway stack) or only some of it?
* Is the prescribed 18 W HRR conserved on every mesh (not lost to a starved
  plume)?
* Report GCI for peak-plume-T, ceiling-T, and the T3−T1 gradient — or, if the
  coarse plume collapses / convergence is non-monotonic, report **that** as the
  result and give the discretization-uncertainty band another way.
