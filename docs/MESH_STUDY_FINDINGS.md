# MESH_STUDY_FINDINGS — P04 numerical-uncertainty study

**Status: FINAL** (2026-09-07). The 1.5 mm run was not restarted past its 24 h
wall — a deliberate stop: the conclusion is already decided by the
coarse→2 mm→1.5 mm trend and the near-fire rake, and a longer 1.5 mm run changes
no finding below. Limitations are named in §6.

---

## 1. Setup

Fixed across every run: geometry, the 18 W paraffin source
(`&SURF HRRPUA` + `TAU_Q=-25`, from CONE_FINDINGS), the sealed acrylic box, and
the 7 thermocouple probes — all from `fds/make_fds.py`, nothing tuned. **Only
δx changes**, which is the P04 rule.

| run | near-fire δx | D\*/δx | cells | meshes | decomposition | t reached |
|---|--:|--:|--:|--:|---|--:|
| coarse | 10 mm | 1.2 | 0.15 M | 1 | single | 150 s ✓ |
| medium | 5 mm | 2.4 | 1.20 M | 1 | single (local) | **35 s only** |
| nest20 | 2.0 mm | 6.1 | 0.82 M | 7 | 1 outer 8 mm + 6 core z-slabs (MPI, Pleiades) | 150 s ✓ |
| nest15 | 1.5 mm | 8.1 | 1.85 M | 7 | 1 outer 6 mm + 6 core z-slabs (MPI, Pleiades) | **65 s** (wall clock) |

D\*(18 W) = 1.21 cm. **Even the finest run reaches only D\*/δx ≈ 8.** The FDS
convention for a resolved plume (D\*/δx = 10–16) would need ≈ 1.2 mm over the
whole plume volume — on the order of 90 M cells — which is out of scope for this
study. That under-resolution is itself a P04 result and is carried explicitly in
the uncertainty band, not hidden.

Embedded-nest history (full chain in PROJECT_STATE.md): the 3-level nest and the
10-outer/12-core split both crash or hang FDS 6.11.1. The working form is **1
undivided outer mesh + 6 core horizontal z-slabs**, 4:1 refinement, launched with
`mpiexec` (Intel MPI — `srun` does not wire PMI on Pleiades).

---

## 2. HRR — converged and exact

`_hrr.csv` column `HRR` = **0.01800 kW on every mesh**, coarse through 1.5 mm,
flat after the 25 s ramp. The split-mesh decomposition conserves the source term
exactly; numerical uncertainty on the delivered fire power is zero.

> The whole-domain `HRR` **DEVC** in the nested decks reads ≈ 0.038 kW — it
> double-counts the outer ∩ core overlap volume. Use `_hrr.csv`, which FDS sums
> correctly per mesh.

---

## 3. Temperature ladder

Rise above ambient (25 °C), matched at a common time. `t = 65 s` is the latest
time reached by a fine mesh; `t = 35 s` adds the 5 mm point. The experiment is
still warming at 65 s (§5), so its 65 s column is **not** its final value.

### At t = 65 s

| station | measured R1–R3 | coarse 10 mm | nest20 2.0 mm | nest15 1.5 mm |
|---|--:|--:|--:|--:|
| **T1** plume root (x 0.12, z 0.05) | **+49.2 ± 6.7** | +1.4 | +0.6 | +0.4 |
| **T2** mid column (x 0.12, z 0.16) | **+12.6 ± 1.3** | +2.9 | +2.1 | +1.2 |
| **T3** ceiling over fire (x 0.12, z 0.225) | **+20.2 ± 5.0** | +0.0 | +16.4 | +19.9 |
| **T5** ceiling mid-room (x 0.35, z 0.225) | **+1.1 ± 0.3** | +0.0 | +3.8 | +2.7 |
| T9 doorway low (x 0.70, z 0.015) | +0.0 ± 0.1 | +0.1 | +0.0 | +0.0 |
| T10 doorway mid (x 0.70, z 0.075) | +0.2 ± 0.1 | +1.5 | +0.2 | +0.2 |
| T11 doorway high (x 0.70, z 0.14) | +2.0 ± 0.4 | +0.9 | +1.7 | +0.5 |

### At t = 35 s (adds the 5 mm point)

| station | measured R1–R3 | 10 mm | 5 mm | 2.0 mm | 1.5 mm |
|---|--:|--:|--:|--:|--:|
| T1 | +32.0 ± 2.6 | +0.7 | +0.6 | +0.3 | +0.2 |
| T3 | +16.9 ± 2.5 | +0.0 | **+23.7** | +14.1 | +20.0 |
| T5 | +1.1 ± 0.1 | +0.0 | +1.0 | +3.1 | +2.5 |

---

## 4. Reading the ladder

**T5, T9, T10 (far-field): converged, and within experimental uncertainty.**
The coarse mesh has no plume at all, so it misses T5 entirely and puts a spurious
+1.5 °C at the doorway. From 2 mm to 1.5 mm the far-field values move by ≤ 1.3 °C
and straddle the measurement (T5: 2.7–3.8 vs +1.1 ± 0.3; T10: +0.2 vs +0.2).
Numerical band here is ≈ ±1.5 °C.

**T3 (ceiling over the fire): needs the plume resolved, then grid-sensitive.**
10 mm → nothing (D\*/δx = 1.2 collapses the plume). 5 / 2 / 1.5 mm → a localized
ceiling-jet warming of +14 to +24 °C — the model reproduces the *localized hot
spot over the fire* (T3 ≫ T5), which is the demanding structural feature from
P02. But the three resolved meshes do **not** form a monotone Richardson
sequence (35 s: 23.7 → 14.1 → 20.0; 65 s: — → 16.4 → 19.9). A formal GCI is not
meaningful at D\*/δx = 2–8. **Best estimate: ΔT₃ ≈ +18 ± 3 °C** at the resolved
limit, from the 2 mm and 1.5 mm runs.
→ **Figure:** `figures/p05_T3_convergence.png`.

**Consolidated T3 statement (P04 draft — SUPERSEDED by the M3 sweep, 2026-09-10;
see SENSITIVITY_FINDINGS §2 and VALIDATION_FINDINGS §4 for the current version):**
T3 agrees with experiment at matched simulated time (FDS +19.9 °C vs measured
+20.2 ± 5.0 °C at t = 65 s). P04 attributed the residual to the +43 °C broad peak
to a wall-thermal-mass *timescale* the short runs did not reach. **M3 refuted
that:** a 2 mm run held T3 flat at +16 °C to 410 s, and the wall back-face
condition makes no difference. The residual is the **wall heat-sink *model*** —
the modelled 10 mm opaque PMMA is ~2× too absorptive; adiabatic walls overshoot
to +60 °C; T3 ∈ [+16, +60] °C with the truth near the low-sink end. T3 is not a
standalone model failure and not a numerical limit.

**T1 and T2 (back-wall column): do NOT converge toward the data.**
10 → 5 → 2 → 1.5 mm gives T1 = +1.4, +0.6, +0.6, +0.4 °C — flat at ambient, and
if anything *decreasing* with refinement. The numerical uncertainty on T1 is
≈ ±1 °C. The 48 °C gap to the experiment at 65 s (110 °C at the peak) is **not
discretization error.** §5 shows why.

---

## 5. The near-fire rake decides "under-resolved" vs "model-structural" → structural

The fine decks carry a 6-x × 5-z rake of gas-temperature probes straddling the
candle (x = 0.09) and the T1/T2 vertical line (x = 0.12). Rise above ambient at
the last frame:

```
                x=7.5cm  x=9.0cm  x=10.5cm  x=12.0cm(T1/T2)  x=13.5cm
nest20 2.0 mm  (t=150 s)
  z = 2.0 cm      50      166       10          1               0
  z = 5.0 cm      29       92        4          1               1
  z = 10  cm      35       47        4          1               1
  Tmax_core = 317 °C

nest15 1.5 mm  (t=65 s, FINER)
  z = 2.0 cm      26      210        5          0               0
  z = 5.0 cm      20      126        4          0               0
  z = 10  cm      24       78        4          1               0
  Tmax_core = 320 °C
```

The prescribed-HRR plume is a **narrow hot column locked to the burner centreline
(x = 0.09)**. It decays to within 5 °C of ambient by x = 0.105 (1.5 cm away) and
to within 1 °C by x = 0.12, where T1 and T2 sit. Refining 2.0 → 1.5 mm makes the
column **hotter and narrower** (peak 166 → 210 °C at z = 2 cm; `Tmax_core`
converging to ≈ 320 °C) — it does not spread toward the probe.

- **Hypothesis (a), under-resolution:** would show T1 *rising* toward ~100 °C as
  δx → 1.5 mm, the hot core broadening to reach the probe. **The opposite is
  observed.**
- **Hypothesis (b), model-structural:** a prescribed-HRR LES of an 18 W source
  releases heat into a thin buoyant column mixed only by (weak, low-Reynolds)
  resolved + SGS turbulence. It cannot represent the finite-width luminous
  reaction zone and its soot radiation that heat a bare thermocouple bead 3 cm
  away in the real candle. `Tmax_core` converging while confined to 1–2 cells at
  the burner is the signature. **This is what the data show.**

→ **Figure:** `figures/p05_T1_nearfield.png` (horizontal + vertical rake profiles,
both meshes).

A second-order contributor: in a 3 cm gradient of ~100 °C/cm, the ±few-mm
uncertainty in the physical candle position and the probe rake location dominates
any model comparison at T1/T2. The near-fire column is not a defensible
validation target for this setup at any mesh.

---

## 6. Numerical-uncertainty band — the P04 deliverable

| quantity | converged? | numerical band | basis |
|---|---|---|---|
| delivered HRR | yes | ±0 (exact) | `_hrr.csv` identical on all meshes |
| T5 / T9 / T10 (far-field ΔT) | yes | ±1.5 °C | 2 mm vs 1.5 mm spread; needs a resolved plume (≥ 5 mm) |
| T3 (near-ceiling ΔT) | partial | **±3 °C** on a resolved value of ≈ +18 °C | 2 mm & 1.5 mm; D\*/δx < 10, non-monotone, no GCI |
| T11 (doorway high ΔT) | partial | ±1 °C | small absolute values, 2 mm vs 1.5 mm |
| T1 / T2 (column ΔT) | N/A | **not a numerical band** — model-structural | rake: plume never reaches x = 0.12; refinement diverges from data |
| box pressurisation | not assessed | — | p_box still rising at end of every run; no measurement to compare |

### Named limitations

1. **One primary FDS run per configuration.** No ensemble; LES run-to-run
   scatter at this near-laminar scale is not quantified.
2. **2.0 mm is the only fine mesh run to quasi-steady** (t = 150 s). 1.5 mm
   stopped at 65 s; 5 mm at 35 s. The 4-point ladder exists only at t = 35 s.
3. **D\*/δx ≤ 8 everywhere.** Below the FDS-recommended 10–16. T3 is reported as
   grid-sensitive, not converged.
4. **Prescribed-HRR source, not pyrolysis.** The fire power is imposed from the
   cone data; the model has no flame chemistry, so the luminous reaction zone
   (the thing T1 sits in) is outside its representation by construction.
5. **Box pressurisation unvalidated** — the sealed-box `p_box` rise (180–380 Pa
   across runs, still climbing) has no experimental counterpart (no pressure or
   load-cell channel survived in the exponat data).

---

## 7. What P05 should take from this

- Validate on **T3, T5, and the doorway stack (T9–T11)** — where the model has
  physical content and a defined numerical band.
- Carry the bands from §6.
- Report **T1 and T2 as a documented model-structure limitation**, quantified by
  the rake, and do **not** tune the source to close the gap.
- Reproducer: `python src/p05_validation.py` (writes the table and both figures from
  `fds/runs/*/` + `data/processed/exponat_R*_timeseries.csv`).
