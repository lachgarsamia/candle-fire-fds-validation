# NUMBERS_AUDIT — headline-figure cross-check (2026-09-10)

Every headline number traced to its source of truth and to the docs that cite it.
**No values were changed.** Discrepancies are flagged, not fixed.

Source-of-truth ranking: `data/processed/*_digest.json` and `*_summary.csv`
(computed from raw) > the findings doc that owns that phase > everything else.

---

## Consistent — no action

| quantity | value | source of truth | cited consistently in |
|---|---|---|---|
| per-candle HRR | **18 ± 2 W** (band 16.5–20.0 W, ΔHc 36–42 MJ/kg) | `cone_digest.json` (Route C, 6 runs; 3-candle repeatability 18.2 ± 1.5 W) | CONE_FINDINGS, REPORT_SUMMARY, README, FDS_geometry_reference, VALIDATION, SENSITIVITY |
| source uncertainty | **± 15–20 %** | CONE_FINDINGS §6 | CONE, REPORT_SUMMARY, README, M2_M3_PLAN, SENSITIVITY |
| burn linearity | r² ≥ 0.999 (30 / 28 mg·min⁻¹·candle) | `report_figs.fig_cone` recompute from `cone_*_timeseries.csv` over `steady_window` | CONE_FINDINGS, README, REPORT_SUMMARY |
| O₂-route disqualification | O₂ HRR = 11–161 W for a mass-loss HRR of 17–58 W | `cone_digest.routeA_O2_HRR_crosscheck` | CONE_FINDINGS, README |
| far-field residual | **≤ 1 °C** (T5, T9, T10, T11 at the P05 matched time, 2 mm) | `p05_three_uncertainty.csv` | VALIDATION §1/§2, REPORT_SUMMARY, README, PROJECT_STATE |
| T3 at matched time | FDS +19.9 vs measured **+20.2 ± 5.0 °C** @ 65 s | `p05_validation.py` output | VALIDATION §1/§4, MESH_STUDY §4, REPORT_SUMMARY |
| T3 wall bracket | **T3 ∈ [+16 (PMMA), +60 (adiabatic)] °C** | `sensitivity_bands.csv`, `sensitivity_tables.md §3` | SENSITIVITY §2, VALIDATION §1/§4, MESH_STUDY §4, REPORT_SUMMARY, README, PROJECT_STATE |
| source-knob band | **≤ 2.5 °C on any sensor** (HRR ± 3 W ⊕ χr 0.20–0.35) | `sensitivity_tables.md §1` | SENSITIVITY §1/§5, README, PROJECT_STATE |
| m2 T3 flatness | +16.5 (60 s) → +15.7 (410 s) | `fds/runs/sweep/m2_base_nest20_450_devc.csv` | SENSITIVITY §2, VALIDATION §4, REPORT_SUMMARY, README |
| T1 in-flame gap | measured +49.2 @ 65 s, +107 peak; FDS +0.4–1.4 (every mesh) | `p05_three_uncertainty.csv`, `fds_post_digest.json` | VALIDATION §1/§2/§3, MESH_STUDY §3, SENSITIVITY §3, README |

---

## Discrepancies — flagged, not fixed

### 1 · Plume peak rise: **107 vs 111 °C**
- **Truth:** TC_01 peak rise = **107.0 ± 6.6 °C** (R1/R2/R3 = 111.4 / 110.2 / 99.4;
  `exponat_digest.json`, EXPONAT_FINDINGS §4.1/§7).
- **+111 °C** (the R1-only value) is used throughout **`MESH_STUDY_STRATEGY.md`**
  (lines 84, 131, 160, 192) and **`PROJECT_STATE.md:98`**.
- `MESH_STUDY_FINDINGS.md` (the actual P04 findings doc) uses the correct
  ignition-aligned values (+49.2 @ 65 s etc.) — no error there.
- **Assessment:** `MESH_STUDY_STRATEGY.md` is the superseded pre-P04 planning
  doc; the +111 is a single-run figure never reconciled to the 3-run mean.
  Mark the strategy doc SUPERSEDED or update its numbers.

### 2 · Horizontal ceiling gradient (T3 − T5): **41 vs 40 vs 36.4 °C**
- **`EXPONAT_FINDINGS.md` is internally inconsistent:** "≈ 41 °C" (line 33) and
  "≈ 40 °C" (line 305).
- `fds_post.py` `EXP_STRUCT` carries **36.4 °C** (R1-only).
- Peak-to-peak (T3ₚₖ − T5ₚₖ) = 43.4 − 4.6 = **38.8 °C**; instantaneous-peak of
  (T3 − T5) ≈ **40.8 ± 3.8 °C**.
- **Assessment:** four numbers for one quantity because "gradient" is computed
  three ways (R1-only, peak-to-peak, instantaneous-peak-of-difference). Pick one
  definition and state it. The headline "≈ 40 °C" is defensible for all three.

### 3 · TC_03 peak rise: **43.4 vs 43.5 °C**
- `exponat_digest.json` per-sensor peak = **43.4 ± 4.0 °C** (R1/R2/R3 =
  38.9 / 46.6 / 44.8).
- `p05_validation.py` (interpolated ignition-aligned grid, `nanmax`) =
  **+43.5 °C**, used in SENSITIVITY §2/§5.
- **Assessment:** 0.1 °C, two computation methods (per-sensor max vs grid max).
  Harmless; note the method where quoted.

### 4 · Tracer "near-uniform" timing: **~100 s vs ~250 s**  ← genuine slip
- **`SMOKE_FINDINGS.md §5`** and **`SENSITIVITY_FINDINGS.md §4`**: "`tr_upper /
  tr_lower` ≈ 1.3 **by t ≈ 100 s**".
- **`REPORT_SUMMARY.md`**: "near-uniform **by ~250 s**".
- **Data** (`s7_tracer_devc.csv`): ratio ≈ 19 (30 s) → 3.4 (60 s) → **1.6 (100 s)**
  → 1.4 (180 s) → **1.3 (250 s)**.
- **Assessment:** SMOKE_FINDINGS / SENSITIVITY are **wrong** — the ratio is ~1.6
  at 100 s, ~1.3 at 250 s. REPORT_SUMMARY's "~250 s" is right. The conclusion
  (slow fill, ends near-uniform) is unaffected, but the "100 s" figure should be
  corrected to "≈ 1.6 by 100 s, ≈ 1.3 by 250 s".

### 5 · HRRPUA: **≈ 17 vs 14.7 vs 14 kW/m²**
- **17 kW/m²** = 18 W ÷ π(0.0185)² (the ideal 37 mm cup) — CONE_FINDINGS,
  FDS_geometry_reference.
- **14.7 kW/m²** = 18 W ÷ the grid-snapped **square** burner (larger area) —
  P03_PLAN, and the value actually in the decks.
- **14 kW/m²** — FDS_BASELINE_NOTES, a rounded reference to the same.
- **Assessment:** not an error — two areas (circle vs grid-snapped square). The
  **delivered power is 18 W either way** (`_hrr.csv` = 0.01800 kW on every mesh).
  State "HRRPUA ≈ 15–17 kW/m² depending on the snapped burner area" once.

### 6 · MESH_STUDY_FINDINGS mixes P04 and M3 framing
- §4 was updated (2026-09-10) to the M3 wall-bracket conclusion, but §4 line ~91
  ("best estimate ΔT₃ ≈ +18 ± 3 °C") and §6 table ("±3 °C on a resolved value of
  ≈ +18 °C") still carry the P04 numerical-band framing.
- **Assessment:** not contradictory — the ±3 °C is the mesh scatter on the
  *resolved* T3, which is a separate quantity from the wall bracket on the
  *residual*. But a reader will trip over "+18 ± 3" next to "[+16, +60]". Add one
  clause distinguishing them, or move the ±3 °C into an explicit "numerical vs
  model" split.

### 7 · Cone "5 runs" vs 6
- CONE_FINDINGS §254: "Route C, **5 runs**, 16.5–20.0 W".
- `cone_digest.json` has **6** (the 6th, `1cand_long`, at 22.9 W).
- **Assessment:** the "5" excludes `1cand_long` (a mass-loss-**rate** cross-check
  from the long 25.08 protocol, not a matched burn). Defensible but the exclusion
  should be stated where "5 runs" appears.

---

## Not audited (no committed data)

M4 wall-variant results (`w1_ir`, `w2_thinceil`, `w3_thinall`, `w4_contact`) —
running on Pleiades; `src/m4_post.py` + `docs/SENSITIVITY_FINDINGS §M4` will fold
them in with the same far-field-integrity check.
