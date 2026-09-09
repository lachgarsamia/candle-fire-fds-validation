# CONE FINDINGS — candle fire-source characterization

**Phase 01 (REVISED).** Inputs: 6 cone-calorimeter CSVs + `data/raw/cone/weights.csv` (manual
weigh table). Code: `src/cone_loader.py`, `src/cone_analysis.py`. Figures in `figures/`,
tables in `data/processed/`. Settled facts from `PROJECT_STATE.md` / Prompt 01 REVISED
are used as given and not re-litigated.

---

## 0. The honest answer

**Yes — the cone data gives a consistent, transferable characterization of the
candle fire, in one specific form: a steady mean heat-release rate per candle,
anchored on the manually-weighed mass loss.**

> **A single tea light is a free-burning ~18–20 W source** (working value for
> FDS: **18 ± 2 W per candle**).
> Route C (manual Δm × ΔHc_eff / burn time), ΔHc_eff = 38 MJ/kg (paraffin
> 42 MJ/kg × χ 0.9):
> * single-candle anchor (26.08 R3): **20.0 W** (band 18.7–22.1 W for χ = 0.85–1.0)
> * 3-candle runs, per candle: **18.6 / 16.5 / 19.5 W**, mean **18.2 ± 1.5 W**
> * long-protocol cross-check (25.08, mass-loss rate only): **22.9 W-equivalent**
> * Combined working value for FDS: **18 ± 2 W per candle**, `HRRPUA ≈ 17 kW/m²`
>   on the 37 mm cup (1.08 × 10⁻³ m²).

Three things make this defensible rather than a fitted number:

1. **The manual mass and the load-cell trend agree.** In every run with a
   recorded after-mass, the balance drop over the burn window matches the
   manual Δm to **within 0.01–0.08 g** (table §3). The load cell is trusted for
   *shape*, the scale for *magnitude* — and they are consistent.
2. **The burn is linear.** A straight-line fit of balance mass vs time over the
   central 60 % of every burn has **r² = 0.999+** (max deviation < 30 mg). The
   candle is genuinely a *constant-rate* source — a steady mean is the right
   representation, not a curve.
3. **The rate is reproducible.** Per-candle mass-loss rate across five
   independent burns spans **0.41–0.63 mg/s** (CoV ~13 % including the
   long-protocol outlier; ~8.5 % among the three 3-candle repeats).

**What the cone data canNOT give** (and we do not pretend otherwise):

* **A trustworthy oxygen-consumption HRR.** Whole-run O₂ depletion is
  0.012–0.031 % absolute. The O₂ channel *detects* the fire (the depletion
  tracks ignition and flameout, §5) but the O₂→kW conversion **overshoots
  Route C by ~3× for the 3-candle runs and is erratic (0.5–3×) for single
  candles**. The cone's calorimetry constants are calibrated for 1–50 kW fires,
  not a 20–60 W one.
* **An empirical ΔHc.** `ΔHc_implied = E(Route A) / Δm_manual` ranges **25–110
  MJ/kg** across runs (literature paraffin 42–46). The spread is an order of
  magnitude wider than the wax uncertainty → the O₂ energy **cannot pin ΔHc**.
  This is a documented disagreement, not something tuned away. We proceed with
  the assumed paraffin ΔHc_eff = 38 MJ/kg and carry χ = 0.85–1.0 (≈ 36–42 MJ/kg)
  as the named uncertainty on every HRR number.
* **A time-resolved MLR(t) or HRR(t).** The load cell resolves ~0.01 g against a
  ~1600 g gross load; its derivative (`MLR`, col 70) is ±800 g/s garbage. Not
  produced, per the brief.

**These were free-burning candle tests.** The cone heater was off: `HFM ≈ 0`,
cone thermocouples near ambient. The metadata `Heat flux 75` and `E 13,10 MJ/kg`
are leftover template defaults and appear nowhere in this analysis. The absence
of external flux is correct and intended.

---

## 1. Configuration keyed off the manual before-weight

Per Prompt 01 REVISED §1.3 — config comes from the weighed mass, not the
filename or the internal metadata.

| run | file | m_before (g) | ⇒ candles | filename | internal metadata | verdict |
|---|---|---|---|---|---|---|
| 1cand_R3 | `26082026_Candle_R3` | 11.61 | **1** | "Candle_R3" | "Candle_R3", 11.61 g | consistent |
| 1cand_long | `25082026_Candle_R1` | 11.25 | **1** | "Candle_R1" | "Candle", 11.25 g | consistent |
| 1cand_R2 | `26082026_Candle_R2` | 11.22 | **1** | "Candle_R2" | "Candle_R2", 11.22 g | consistent |
| 3cand_R1 | `26082026_3_Candles_R1` | 34.19 | **3** | "3_Candles_R1" | "**Candle_R3**", **11.61 g** | ⚠ **metadata logged only candle 1** — filename & weight win; 3 candles confirmed (11.61 + 11.53 + 11.05 g) |
| 3cand_R2 | `27082026_3_Candles_R2` | 34.13 | **3** | "3_Candles_R2" | "3_Candles_R2", 38.13 g | metadata mass wrong; weight wins |
| 3cand_R3 | `27082026_3_Candles_R3` | 34.20 | **3** | "3_Candles_R3" | "3_Candles_R3", 34.20 g | consistent |

The `26082026_3_Candles_R1` mismatch RECON flagged is resolved: it is genuinely
3 candles; the operator logged only the first candle's mass in the instrument
metadata. Reported once here, not carried further.

---

## 2. Roster (classified — NOT pooled as six repeats)

| run | class | use |
|---|---|---|
| **1cand_R3** | single-candle **anchor** | primary single-candle characterization. Caveat: only 1.62 g lost (14 % of the tea light) — **did not reach full steady state**; its 20.0 W may slightly over-read the true long-term steady value (the steady-window fit gives 19.1 W). |
| **1cand_long** (25.08) | long-protocol **rate cross-check** | ~3.8 h burn, different day. **O₂ HRR disqualified** (dirty filter — visible drift after t ≈ 11 500 s, §5). Used only for its mass-loss *rate*: 0.60 mg/s vs the anchor's 0.525 mg/s (**+14 %**). Broadly consistent → the ~0.5 mg/s single-candle rate is robust to protocol. |
| **1cand_R2** | short / incomplete | **not a blank** — it burned (−1.36 g). No metadata ignition/flameout; window taken from the load-cell shape (94–3216 s, uncertain by ±100 s). Route C: 16.6 W. Reported separately, not pooled with the anchor. |
| **3cand_R1** | 3-candle repeat | **cleanest** — 1.18 g/candle lost, r² 0.9999, flameout confirmed by load cell to 43 s. |
| **3cand_R2** | 3-candle repeat | short burn (844 s, only 0.37 g/candle) — weighing precision (~±0.03 g) is ~8 % of the loss, so this run's HRR carries extra uncertainty. |
| **3cand_R3** | 3-candle repeat | **no after-mass recorded** → mass loss from the load-cell shape only (2.66 g). Timeline + balance-shape Route C: 19.5 W (lower confidence). |

**Consequence:** the single-candle side rests on **one matched burn (R3) + one
long-protocol rate cross-check + one short partial** — *not* three replicates.
The 3-candle side has **three genuine repeats**. There is no blank run; the O₂
noise floor is bounded from the quiet pre-ignition / post-flameout segments
inside the burning runs (§5).

---

## 3. Per-run results

Full table: `data/processed/cone_per_run_summary.csv`. Time series:
`data/processed/cone_<run>_timeseries.csv`.

### 3.1 Timeline — metadata vs load-cell shape

| run | metadata ign / flameout (s) | burn duration (s) | load-cell flameout (s) | Δ(meta − shape) | mass @ign→@flameout confirms? |
|---|---|---|---|---|---|
| 1cand_R3 | 30 / 3115 | 3085 | 3059 | +56 s | ✅ balance −1.54 g vs manual −1.62 g |
| 3cand_R1 | 23 / 2427 | 2404 | 2384 | +43 s | ✅ −3.52 g vs −3.53 g |
| 3cand_R2 | 12 / 856 | 844 | 843 | +13 s | ✅ −1.02 g vs −1.10 g |
| 3cand_R3 | 32 / 1757 | 1725 | 1722 | +35 s | ✅ −2.66 g (no manual) |
| 1cand_long | — / 13845 | 13785 | (linear throughout) | — | ✅ −8.24 g vs −8.29 g |
| 1cand_R2 | — / — | 3122 (shape) | 3216 | — | ✅ −1.32 g vs −1.36 g |

**Clock reconciliation:** the metadata ignition instants are not physical
(candles were hand-lit before insertion), but the metadata *flameout* is
confirmed by the load cell going flat to **within 13–56 s** in every run, and
the metadata *burn duration* is therefore reliable. The load cell first
registers weighable loss ~15–60 s *after* the metadata ignition — expected lag,
not a clock offset. Route C uses the metadata duration (load-cell-confirmed);
where metadata is absent (1cand_R2) the window is the load-cell shape and
carries ±~100 s.

### 3.2 Mass, MLR, and HRR (three ways)

| run | Δm total (g) | Δm/candle (g) | mean MLR/candle (mg/s) | **Route C HRR/candle (W)** [band] | steady-fit HRR/candle (W), r² | Route A mean HRR/candle (W) |
|---|---|---|---|---|---|---|
| **1cand_R3** | 1.62 | 1.62 | 0.525 | **20.0** [18.7–22.1] | 19.1, r²=0.9997 | 48 (2.4× high) |
| 1cand_long | 8.29 | 8.29 | 0.601 | (22.9) rate only | 23.8, r²=0.9984 | *disqualified* |
| 1cand_R2 | 1.36 | 1.36 | 0.436 | 16.6 [15.6–18.3] | 15.4, r²=0.9993 | 11 (0.6× low) |
| **3cand_R1** | 3.53 | 1.18 | 0.489 | **18.6** [17.5–20.6] | 17.7, r²=0.9999 | 54/candle (2.9× high) |
| 3cand_R2 | 1.10 | 0.37 | 0.434 | 16.5 [15.5–18.2] | 16.0, r²=0.9993 | 16/candle (1.0×) |
| 3cand_R3 | 2.66* | 0.89* | 0.514* | 19.5* [18.3–21.6] | 20.5, r²=0.9997 | 7/candle (0.4× low) |

\* from load-cell shape (no manual after-mass).

* **Route B ≡ Route C here.** With no time-resolved MLR, "MLR × ΔHc" evaluated at
  the mean is identical to Route C. There is only one mass-based number per run.
* **Route C and the independent steady-window linear fit agree to ~5 %** in
  every run — the mean over the whole burn ≈ the central-60 % slope, confirming
  the burn has no strong ramp or tail.
* **Route A (O₂) is not usable quantitatively:** per-candle values 7–54 W with no
  pattern; the 3-candle runs sit ~3× above Route C, the single-candle runs
  scatter 0.6–2.4×.

### 3.3 Empirical ΔHc check (Route A energy ÷ manual Δm)

| run | E(Route A) over burn (MJ) | Δm_manual (g) | **ΔHc_implied (MJ/kg)** |
|---|---|---|---|
| 1cand_R3 | 0.149 | 1.62 | **92** |
| 1cand_R2 | 0.034 | 1.36 | **25** |
| 3cand_R1 | 0.387 | 3.53 | **110** |
| 3cand_R2 | 0.040 | 1.10 | **36** |
| *1cand_long* | *0.57* | *8.29* | *69 (disqualified filter)* |

Literature paraffin net ΔHc ≈ 42–46 MJ/kg. **The implied values span 25–110
MJ/kg — a factor of 4.** The O₂-consumption energy cannot pin ΔHc for a fire
this small. **We do not tune to close this.** Primary HRR stays on Route C with
the assumed ΔHc_eff = 38 MJ/kg; the χ = 0.85–1.0 band (~36–42 MJ/kg) is the
stated uncertainty.

---

## 4. Cross-run

### 4.1 3-candle repeatability (n = 3 genuine repeats)

Full table: `data/processed/cone_cross_run_summary.csv`.

| quantity | R1 | R2 | R3 | mean ± std | CoV |
|---|---|---|---|---|---|
| **HRR per candle (W)** | 18.6 | 16.5 | 19.5 | **18.2 ± 1.5** | **8.5 %** |
| **MLR per candle (mg/s)** | 0.49 | 0.43 | 0.51 | 0.48 ± 0.04 | 8.5 % |
| burn duration (s) | 2404 | 844 | 1725 | 1658 ± 782 | 47 % |
| flameout time (s) | 2427 | 856 | 1757 | 1680 ± 788 | 47 % |

* **The per-candle RATE is repeatable to 8.5 %.** That is the transferable
  result.
* **Burn duration / flameout time are NOT repeatable (CoV 47 %)** — but this is
  not measurement scatter: the three runs simply burned for different lengths
  (R2 was a deliberately short 844 s burn; R1 ran to near-completion). Total
  energy released scales with duration and is not a fixed per-run quantity here.
* Excluding the short R2 (whose 0.37 g/candle loss is near weighing precision),
  R1 + R3 give **19.0 ± 0.6 W per candle** (CoV 3 %).

### 4.2 Single-candle

* **Anchor (26.08 R3): 20.0 W** (steady-fit 19.1 W). Not fully steady → treat 20
  W as a mild upper estimate.
* **Long-protocol rate cross-check (25.08):** 0.60 mg/s vs the anchor's 0.525
  mg/s, **ratio 1.14**. A single tea light burns at ≈ 0.5–0.6 mg/s (≈ 19–23
  W-equivalent) regardless of protocol or day → **robust**. The +14 % is real
  (different wax batch / longer quasi-steady burn / rig differences), reported
  not smoothed.
* **1cand_R2:** 16.6 W (short, window uncertain) — consistent with the low end
  of the range.

### 4.3 Superposition — 1 candle vs 3 candles

| quantity | 1-candle (anchor) | 3-candle per candle (mean n=3) | ratio (3-cand total ÷ 1-cand) |
|---|---|---|---|
| mean HRR | 20.0 W | 18.2 W | **2.73** (ideal 3.00) |
| mean MLR | 0.525 mg/s | 0.48 mg/s | **2.74** (ideal 3.00) |

**Per-candle output in the 3-candle configuration is ~9 % below the
single-candle anchor** (18.2 vs 20.0 W). The candles at this spacing behave as
**near-independent sources**:

* **For FDS: model the 3 candles as three separate burners**, each ~18 W, not
  one merged 55 W source. Three burners reproduce the plume structure, the
  candle-to-candle spacing, and the (small) interaction; a single merged source
  would misplace the plume and lose the geometry.
* The ~9 % suppression is a **minor, reportable coupling effect** — mutual
  vitiation and radiative cross-talk slightly slow each flame. It is within the
  8.5 % run-to-run scatter, so it is a soft result: "≤ ~10 % per-candle
  suppression," not a precise coupling coefficient. Against the single-candle
  side resting on one matched burn, do not over-interpret the exact 2.73.

---

## 5. O₂ / CO₂ / CO and the noise floor

* **O₂ depletion over the burn:** 0.012 % (1cand_R3) to 0.031 % (3cand_R1)
  absolute. See `figures/cone_o2_depletion.png`.
* **Short-term analyzer noise** (std of O₂ over quiet pre-ignition +
  post-flameout segments *inside* the burning runs — the bound Prompt 01 REVISED
  asked for, since no blank run exists): **0.0012–0.0031 % absolute**.
* **Depletion / noise ratio:** 4–24. The 3-candle runs clear the short-term
  noise comfortably (≈ 15–24×); the single-candle runs marginally (≈ 4–8×).
* **But the absolute magnitude is not trustworthy:** run-to-run pre-ignition O₂
  baseline varies 20.946–20.955 % (~0.01 % spread), *comparable to the depletion
  itself*, and the O₂→HRR conversion overshoots Route C by ~3× for 3 candles.
  So the O₂ HRR is **qualitative** — good for confirming *when* the fire is on,
  useless for *how big*.
* **CO₂ rise:** 0.005–0.018 % — same regime, same verdict.
* **CO:** at/below its own noise floor (±0.04 % oscillation about zero) in every
  run — no usable CO signal. Candle combustion is clean (RECON: cone soot ≈ 0).
* **25.08 filter drift** is visible directly: O₂ and the O₂-HRR step to a
  spurious offset after t ≈ 11 500 s (`figures/cone_routeA_noise.png`) — the
  reason its O₂ HRR is disqualified. Its *mass loss* is unaffected and stays
  linear throughout.

---

## 6. Recommended FDS source term

| parameter | value | basis / uncertainty |
|---|---|---|
| **per-candle HRR** | **18 W** (use 18 ± 2 W) | Route C, 5 runs, 16.5–20.0 W; ΔHc_eff 38 MJ/kg (χ 0.9 assumed) |
| ΔHc band | 36–42 MJ/kg (χ 0.85–1.0) | O₂ data could not pin it empirically |
| burner area | 1.08 × 10⁻³ m² (37 mm cup) | `FDS_geometry_reference.md` |
| **HRRPUA** | **≈ 17 kW/m²** | 18 W ÷ 1.08 × 10⁻³ m² |
| mass-loss rate | 0.5 mg/s per candle | steady-window fits, 0.41–0.63 mg/s |
| temporal profile | **constant** (step on at ignition, step off at flameout) | balance mass-loss linear to r² > 0.999 |
| 3-candle case | **3 separate burners**, ~18 W each | superposition ratio 2.73/3.0; ≤ ~10 % per-candle suppression |
| what NOT to use | O₂-consumption HRR (col 89), metadata ignition times, "75 kW/m²", ΔHc = 13.1 MJ/kg | §0, §3.3, §5 |

**Uncertainty budget for the FDS source term:**
* wax ΔHc / combustion efficiency: **±~10 %** (dominant, unresolved)
* run-to-run experimental scatter: **±8.5 %** (3-candle repeats)
* single vs 3-candle coupling: **~9 %** (one-directional, small)
* mass-weighing / window: **±3–5 %** (small, except the short 3cand_R2)

Combined, **±15–20 % on the per-candle HRR** — carry this into the FDS baseline
comparison (Phase 03) rather than treating an 18 W input as exact.
