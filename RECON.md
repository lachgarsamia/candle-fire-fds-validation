# RECON — Phase 0 Read-Only Investigation

**Study:** experimental + FDS validation of a candle fire in a small compartment
**Date of recon:** 2026-08-28
**Mode:** strictly read-only. No analysis code, no pipeline, no scaffold. The only
files written this phase are `/tmp/cone_recon*.py` (throwaway inspection scripts)
and this `RECON.md`.

**Primary cone file inspected:** `/Users/samialachgar/Desktop/experiments/26082026_3_Candles_R1.csv`
(1,981,318 bytes)

**Sibling files in the same folder (not deeply analysed):**

| file | bytes | data rows | notes from metadata |
|---|---|---|---|
| `26082026_3_Candles_R1.csv` | 1,981,318 | 3,241 | **target file.** desc `Candle_R3`, spec `R3`, init mass `11,61 g`, area `88,36 cm²`, HF `75`, ignit `23`, flameout `2427` |
| `25082026_Candle_R1.csv` | 8,833,244 | 14,523 | desc `Candle`, spec `R1`, init mass `11,25 g`, area `11,09 cm²`, HF `75`, ignit `(blank)`, flameout `13845` — ~4 h run |
| `26082026_Candle_R2.csv` | 2,099,212 | 3,476 | desc `Candle_R2`, init mass `11,22 g`, area `10,47 cm²`, **HF `0`**, ignit `(blank)`, flameout `(blank)` — looks like a cold/blank run |
| `26082026_Candle_R3.csv` | 2,017,641 | 3,299 | desc `Candle_R3`, init mass `11,61 g`, area `10,64 cm²`, HF `75`, ignit `30`, flameout `3115` |
| `27082026_3_Candles_R2.csv` | 592,580 | 975 | desc `3_Candles_R2`, init mass `38,13 g`, area `88,36 cm²`, HF `75`, ignit `12`, flameout `856` |
| `27082026_3_Candles_R3.csv` | 1,249,321 | 2,065 | desc `3_Candles_R3`, init mass `34,20 g`, area `88,36 cm²`, HF `75`, ignit `32`, flameout `1757` |
| `2026-08-27_exponat_R1/R2/R3.txt` | 1.2–1.4 MB | ~860 lines | compartment ("Exponat") runs — **different format**, see Part C |

All six CSVs share the identical 100-column layout and the `999998,00` TE-placeholder
convention, so a single cone parser covers all of them.

---

## Part A — Cone data map (`26082026_3_Candles_R1.csv`)

### A.0 Format — verified against the bytes

| property | claim | verified? | evidence |
|---|---|---|---|
| Encoding | ISO-8859-1 / Latin-1 | **yes** | `file(1)` → `ISO-8859 text`; decodes cleanly as `iso-8859-1`; units row contains `kW/m²`, `g/(s*m²)`, `°C`, `m²/kg` (byte `0xB2` = `²`, `0xB0` = `°`) |
| Line terminator | CRLF | **yes** | 3,243 `\r\n`, 0 lone `\n` |
| Delimiter | semicolon `;` | **yes** | header row splits on `;` into 100 fields; first bytes `General information;;time (s);O2;CO2;CO;Pdiff;Light;Mass;…` |
| Decimal separator | comma | **yes** | e.g. `18,73`, `1636,4501`, `0,0431`; every numeric field uses `,` |
| Locale | German/EU | **yes** | date `26.08.2026`, `Relative hunidity`/`colelcted` (German-operator typos), `Teelicht` |
| Row 0 | channel names (~100 cols) | **yes** — but note **names first, units second** | row 0 = names, row 1 = units. (The existing FDS reader assumes the opposite order — units first.) |
| Row 1 | units row | **yes** | row 1 = `;;;%;%;%;Pa;-;g;g/s;Pa;%;kW/m²;°C;…` |
| Data | starts row 2 | **yes** | row 2 = `…;;0;20,954;0,052;-0,008;…` (time = 0) |
| Columns 0–1 | metadata key/value block, not data | **yes** | col 0 = key, col 1 = value, rows 0–71 (see A.1). From row 2 onward columns 0–1 are **empty** on data rows. |
| Time axis | `time (s)` ≈ col 2, 1 s sampling | **yes** — it is exactly **col 2** | values `0,1,2,…,3240`; `Sampling interval (s);1`; 3,241 rows spanning 0–3240 s |
| Duplicate `Mass` | two columns, not interchangeable | **yes** — cols **8** and **88** | see A.3 |
| Duplicate `HRR` | more than one representation | **yes** — `HRR` col **89** (kW) and `HRR/a` col **67** (kW/m²); also `ARHE` col 87 (kW/m², "average RHE") | see A.3 |
| Duplicate `CO`, `CO2` | — | also true: `CO` at cols 5 (%) and 24 (ppm, empty); `CO2` at cols 4 (%) and 25 (%, empty) |

Shape: **100 columns × 3,243 rows** (row 0 names, row 1 units, rows 2–3242 = 3,241 data
records). Every row has exactly 100 fields (no ragged rows).

### A.1 Metadata key/value block (columns 0–1, verbatim)

Values are quoted exactly as stored (decimal comma preserved). Blank value = empty cell.

```
General information
  (section header rows carry an empty value; listed here for structure)

Test
  Standard used                         ISO 5660-1
  Date of test                          26.08.2026
  Time of test                          15:09
  Heat flux (kW/m²)                     75
  Nominal duct flow rate (l/s)          24,0
  Sampling interval (s)                 1
  Separation (mm)                       25
  Orientation                           hor
  Edge frame?                           N
  Grid?                                 N
  Non-scrubbed?                         (blank)
  Substrate used? {Y/N}                 (blank)
  Substrate                             (blank)
  Additional preparation details        (blank)

Specimen
  Sample description                    Candle_R3
  Material name/ID                      Candle / Teelicht
  Specimen number                       R3
  E (MJ/kg)                             13,10
  Initial mass (g)                      11,61
  Thickness (mm)                        13,03
  Surface area (cm²)                    88,36
  Sponsor                               (blank)
  Manufacturer                          (blank)
  Test start time (s)                   60
  Time to ignition (s)                  23
  Time to flameout (s)                  2427
  End of test criteria                  User end of test
  User EOT time (s)                     3240
  MLR EOT mass (g/m²)                   (blank)
  MLR time period (s)                   (blank)
  Truncate graphs at EOT                (blank)
  Smooth data?                          (blank)
  Correct O2 for pressure?              (blank)

Apparatus
  C-factor (SI units)                   0,0431
  OD correction factor                  1
  Duct diameter (m)                     0,114
  O2 delay time (s)                     12
  CO2 delay time (s)                    10
  CO delay time (s)                     10

Laboratory
  Laboratory name                       FZJ IAS-7
  Operator                              Clara
  Filename                              26082026_3_Candles_R1,csv
  Report name                           (blank)

Pre-test conditions
  Ambient temperature (°C)              26,8
  Barometric pressure (Pa)              100556
  Relative hunidity (%)                 41,5

Conditioning
  Conditionet ? (Y/N)                   N
  Conditioning temperature (°C)         (blank)
  Conditioning RH (%)                   (blank)

Data collected
  CO/CO2 data collected?                Yes
  Mass data collected?                  Yes
  Smoke data collected                  Yes
  Soot mass data colelcted              (blank)
  Soot mass ratio (1:x)                 (blank)
  Soot mass (g)                         (blank)

Comments
  (blank)
```

**Metadata-consistency red flags (see Part C):**

- The specimen block is templated from a **single-candle R3** run: `Sample description = Candle_R3`,
  `Specimen number = R3`, `Initial mass = 11,61 g` (one tea light), `Surface area = 88,36 cm²`,
  `Thickness = 13,03 mm`, `E = 13,10 MJ/kg`. The filename says `3_Candles_R1`. The sibling
  `27082026_3_Candles_*` files carry `Initial mass = 34–38 g` (≈ 3 tea lights). So for the
  **target file the "Initial mass" almost certainly does not describe what was on the balance.**
- `E (MJ/kg) = 13,10` is not paraffin's heat of combustion (~42–46 MJ/kg) — looks like a leftover
  default.
- `Heat flux (kW/m²) = 75` is contradicted by the data: `HFM` (col 12) reads `0` for the entire
  run (max 0.005 kW/m²) and the cone thermocouples read near ambient. **The conical heater was
  effectively off** — this is a free-burning candle test, not a forced-flux test. Treat `75` as a
  template value.
- `Filename` value `26082026_3_Candles_R1,csv` has the extension dot rendered as a comma (locale
  artifact in the string) — cosmetic.

### A.2 Channel table (columns of scientific interest)

`t=0` → row 2 (time 0 s); `t=mid` → time 1620 s; `t=end` → last **populated** row
(time 3239–3240 s; several derived channels are blank on the final row 3242).
Values shown with decimal point (converted from the file's comma).

| col | header | units row | value @t=0 | value @t=mid | value @t=end | min | max | notes |
|---|---|---|---|---|---|---|---|---|
| 2 | `time (s)` | *(none)* | 0 | 1620 | 3240 | 0 | 3240 | the real time axis, 1 s step, 3241 samples |
| 3 | `O2` | `%` | 20.954 | 20.923 | 20.938 | 20.916 | 20.955 | **total depletion over the whole run ≈ 0.039 % abs** — see A.4 |
| 4 | `CO2` | `%` | 0.052 | 0.058 | 0.049 | 0.048 | 0.070 | rises only ~0.01–0.02 % over baseline; near noise |
| 5 | `CO` | `%` | −0.008 | −0.037 | −0.005 | −0.039 | 0.032 | oscillates around 0, frequently negative → **at/below analyzer resolution**, no real CO signal in % units |
| 6 | `Pdiff` | `Pa` | 130.55 | 129.63 | 128.18 | 120.2 | 137.0 | duct orifice ΔP, stable |
| 7 | `Light` | `-` | 100.03 | 100.03 | 100.08 | 100.0 | 100.1 | smoke-beam transmission ~100 % → no measurable obscuration (clean flame) |
| 8 | `Mass` | `g` | 0 → settles 1636.4 | 1634.17 | 1633.01 | 0 | 1637.95 | **PHYSICAL BALANCE — raw load in grams** (specimen + holder + pan). 0 until t=11 s, ramps t=12–14 s (156.8 → 1557.6 → 1636.4), then a slow monotone decline. See A.3. |
| 12 | `HFM` | `kW/m²` | 0 | 0 | 0 | 0 | 0.005 | heat-flux meter reads zero → **no external radiant flux applied** |
| 13 | `TC stack` | `°C` | 299.25 | ~300.8 | 299.75 | 299.1 | 301.1 | **pinned ~300 °C, span 2 °C — not tracking the fire** (offset/failed channel or thermostatically held duct) |
| 14 | `TC smoke` | `°C` | 298.75 | ~300.6 | 299.25 | 298.8 | 300.9 | pinned ~300 °C, as above |
| 15 | `TC amb.` | `°C` | 26.8 | 27.0 | 27.1 | 26.8 | 27.2 | real lab ambient, matches metadata `Ambient temperature 26,8` |
| 16 | `TC cone` | `°C` | 299.15 | 301.68 | 301.52 | 299.1 | 302.5 | pinned ~300 °C — **cone heater NOT at 75 kW/m² setpoint** (would be ~750 °C) |
| 17 | `T PK` | `°C` | 263.15 | 263.15 | 263.15 | 263.1 | 263.2 | pinned ~263 °C, constant → dead/offset |
| 19 | `TC cone1` | `°C` | 25.8 | 28.9 | 28.4 | 25.8 | 29.9 | **responsive real TC near specimen** — rises ~4 °C over the burn, decays after flameout |
| 20 | `TC cone2` | `°C` | 26.5 | 28.8 | 28.7 | 26.4 | 29.5 | responsive real TC, ~3 °C rise |
| 21 | `TC cone3` | `°C` | 25.7 | 27.9 | 28.0 | 25.7 | 28.7 | responsive real TC, ~3 °C rise |
| 22 | `TC aux` | `°C` | 301.75 | 301.85 | 302.15 | 301.8 | 302.1 | pinned ~302 °C, constant → dead/offset |
| 67 | `HRR/a` | `kW/m²` | 2.067 | 19.24 | 10.25 | 0 | 24.48 | **= `HRR`(col 89) ÷ specimen area (0.008836 m²)** — identical signal, just per-area scaled. Inherits col 89's noise. 1 blank cell (final row). |
| 68 | `EHC` | `MJ/kg` | *(blank)* | 0 | 0 | 0 | 3.285 | effective heat of combustion — **24 blank cells**, mostly 0; unusable (denominator MLR ≈ 0) |
| 70 | `MLR` | `g/s` | 0 | 0 | *(blank last row)* | **−902.0** | 70.72 | mass-loss rate — **garbage: ±hundreds g/s spikes** from differentiating a quantised balance. 1 blank cell. |
| 71 | `MLR/a` | `g/(s*m²)` | 0 | 0 | *(blank)* | −902.0 | 70.72 | same garbage, per-area |
| 74 | `THR/a` | `MJ/m²` | 0.0021 | 29.33 | 52.86 | 0.0021 | 52.86 | monotone cumulative integral of `HRR/a`; **absolute value is unreliable** because it integrates a noise-dominated HRR |
| 75 | `MFR` | `g/s` | 28.47 | 28.29 | 28.18 | 27.24 | 29.08 | duct mass-flow rate, stable ~28 g/s |
| 76 | `K` | `1/m` | ~0 | ~0 | −0.0005 | −0.00065 | 0.00026 | smoke extinction coefficient ≈ 0 → no measurable smoke |
| 77 | `Vstack` | `l/s` | 24.12 | 24.10 | 23.92 | 23.20 | 24.77 | volumetric duct flow, matches `Nominal duct flow rate 24,0 l/s` |
| 78 | `Vsmoke` | `l/s` | 24.08 | 24.08 | 23.88 | 23.17 | 24.76 | as above |
| 85 | `O2C` | `g/s` | 0.04 | 1.17 | — | −0.03 | 1.37 | O2 consumption rate — noisy, spans zero |
| 87 | `ARHE` | `kW/m²` | *(blank)* | 18.10 | — | 0.78 | 18.12 | averaged rate of heat emission; 2 blank cells |
| 88 | `Mass` | `g` | 1.60 (t=1 s) | 18.13 | 16.33 | 0.95 | 18.14 | **DERIVED / NORMALISED "mass" — NOT the physical balance.** Non-physical shape: rises 1 → 8 → 18 g over 0–2400 s then falls to ~16 g. A candle cannot gain mass; basis unknown (possibly an internal reconstruction from MFR/O2C). **Do not use as specimen mass.** 1 blank cell. |
| 89 | `HRR` | `kW` | 0.0183 | 0.170 | 0.091 | 0 | 0.216 | **total heat release rate, kW.** Magnitude (~0.02–0.22 kW) is plausible order for 3 tea lights (~0.12–0.2 kW), **but it is derived from a 0.039 %-O2 signal — noise-dominated, not quantitatively trustworthy** (see A.4). 1 blank cell (final row). |
| 90 | `O2/sh` | `[%]` | 20.953 | 20.921 | 20.938 | 20.916 | 20.955 | "shifted"/delay-corrected O2 — essentially identical to col 3 |
| 91 | `CO2/sh` | `[%]` | 0.051 | 0.059 | 0.049 | 0.048 | 0.070 | delay-corrected CO2 |
| 92 | `CO/sh` | `%` | −0.011 | −0.009 | −0.005 | −0.039 | 0.032 | delay-corrected CO, still noise |
| 93 | `phi` | *(none)* | 0.000215 | 0.00202 | 0.00107 | −7.1e-5 | 0.00254 | equivalence ratio ≈ 0.001–0.002 → combustion is a negligible perturbation on the 28 g/s airflow; consistent with the tiny O2 depletion |

**Populated temperature channels:** only `TC amb.` (15) and `TC cone1/2/3` (19–21) carry
real, fire-responsive signal. `TC stack`/`TC smoke`/`TC cone`/`TC aux`/`T PK` are pinned
near a constant (≈300 °C / 263 °C) and do not respond — treat as offset/failed.

### A.3 Which duplicate to use — explicit guidance for downstream consumers

**`Mass` — use column 8 (raw balance, g). Column 88 is not physical.**

Evidence:
- Col 8: `0` for t=0–11 s (balance not yet engaged), then `156.75 → 1557.56 → 1636.44 g` at
  t=12–14 s (balance settling), then a smooth monotone decrease `1636.45 → 1633.01 g` across
  the run. Absolute load ≈ 1636 g = tea light(s) + sample holder + pan. This is the balance
  reading in grams.
- Col 88: t=1 s = `1.604`, noisy, **rises** to `18.14 g` by t≈2400 s, then **falls** to
  `16.33 g`. A burning candle loses mass monotonically; a rise-then-fall of a "mass" channel
  is non-physical. Values (1–18 g) also do not match any candidate specimen mass
  (11.61 g single, ~35 g triple). Basis undocumented. **Downstream should ignore col 88** and,
  if a net specimen mass / MLR is needed, derive it from col 8 minus a measured tare
  (tare unknown — Part C item 3), with heavy smoothing before differentiation.
- Related: col 95 (`FU28`) ≈ col 8 + 11.61 (it holds `11,61` during balance startup then
  tracks `balance + 11.61`); col 96 (`FU29`) is a duplicate of the time axis. The `FU27/FU30/FU31`
  columns are empty. Treat all `FU*` columns as non-data.

**`HRR` — two representations of ONE signal; pick by need, but treat both as
qualitative for this test:**
- Col 89 `HRR` (kW, total) — use this for an absolute heat-output number.
- Col 67 `HRR/a` (kW/m², per specimen area) — exactly `HRR / 0.008836 m²`
  (checked: 0.018267 kW / 0.008836 = 2.067 kW/m² = col 67 @ t=0; 0.17002 / 0.008836 = 19.24 = col 67 @ t=mid).
  Only meaningful if the `Surface area = 88,36 cm²` basis is correct (Part C item 11).
- `ARHE` (col 87, kW/m²) is a running-average version of `HRR/a`.
- **Recommendation:** for a candle, HRR from oxygen-consumption calorimetry here is
  noise-dominated (A.4). The defensible HRR is `ṁ_loss × ΔH_c,eff` from the col-8 balance
  trend, once tare and ΔH_c are pinned (Part C items 3, 7). Carry col 89 only as a
  cross-check / upper-bound sanity number, clearly labelled "OC-calorimetry, near noise floor".

### A.4 Data-quality flags

**Dead / placeholder / constant channels (exclude from analysis):**

| col(s) | header | state |
|---|---|---|
| 9 | `Methane` | constant `0` |
| 18 | `Soot` | constant `0` (and `Soot mass data collected` blank) |
| 23–26 | `CH4`, `CO`, `CO2`, `Ethene` (FTIR block) | **entirely empty** (3,241 blank cells each) — gas analysis not exported here |
| 27 | `H2O` | constant `0` |
| 28, 29 | `n.u.` | constant `0` |
| 30 | `UOX Bin` | integer 1–3 (instrument bin/mode, not a measurement) |
| 31 | `n.u.` | 12.4–17.0 (unlabelled, slow drift — unknown quantity) |
| 32 | `UOX Hum.` | ~15 % (sensor internal humidity) |
| 33 | `UOX Temp` | ~25.8–26.5 °C (sensor internal temperature) |
| 34 | `n.u.` | ~0.57–0.62 (unlabelled) |
| 35 | `TEext1` | ~0.56–0.61 — reads ~0.6 °C, i.e. a disconnected/zeroed thermocouple; effectively dead |
| 36–49 | `TEext2` … `TEext15` | **constant `999998,00` placeholder** (verified: row 5 col 36 = `999998,00` in all six CSVs) — dead channels, do **not** treat as data |
| 50 | `n.u.` | constant `999998` placeholder |
| 51–66 | `n.u.` ×16 | **entirely empty** |
| 81 | `TSP` | constant `0` (total smoke production) |
| 94, 97, 98 | `FU27`, `FU30`, `FU31` | **entirely empty** |
| 99 | *(unnamed)* | **entirely empty** |
| 13, 14, 16, 17, 22 | `TC stack/smoke/cone/aux`, `T PK` | pinned near a constant (≈300 / 263 °C), span ≤ 3 °C — not responsive; treat as failed/offset |

**`Infinity` / `-Infinity` entries:**

- Col 73 `CO2Y/sh` (`[kg/kg]`, CO2 yield): **1,739 of 3,241 cells are `Infinity` / `-Infinity`**
  (`t=0` = `-Infinity`, `t=mid` = `Infinity`) — division by a ~zero fuel-mass-loss or ~zero
  CO2 delta. **Channel is unusable.**
- Col 72 `COY` (CO yield): no infinities, but oscillates in `[-0.0089, +0.0089]` around zero —
  no real CO-yield signal (consistent with col 5 `CO` being at the noise floor).
- The prompt's expectation of "`Infinity` in COY early on" — in this file the infinities are in
  **`CO2Y/sh` (col 73)**, not `COY` (col 72). `COY` early values are small finite negatives
  (`-0.00181`, `-0.00205`, …).

**Empty cells:**

- The **final data row (time 3240 s, row index 3242)** has blank values for every derived
  channel: cols 67, 68, 70, 71, 72, 73, 74, 88, 89 (and col 87 blank on the last 2 rows).
  A consumer must tolerate a short blank tail, not assume a rectangular numeric block.
- `EHC` (col 68): 24 blank cells scattered through the run (leading + wherever the flaming
  denominator collapses).

**O2 depletion magnitude / noise floor:**

- O2 goes from **20.955 % → 20.916 % → 20.938 %**; total swing across the entire 54-minute
  run is **≈ 0.039 percentage points absolute**.
- A paramagnetic / zirconia O2 analyzer's short-term noise + drift is typically
  ~0.01–0.02 % abs. The observed depletion is therefore only **~2–4× the instrument floor**,
  and individual-sample noise is a large fraction of the signal.
- `phi ≈ 0.001–0.002` and `CO`, `CO2` sitting on their own noise floors corroborate this: the
  fire is a near-negligible perturbation on a 28 g/s dilution flow.
- **Consequence:** the oxygen-consumption `HRR` (col 89) and everything integrated from it
  (`HRR/a`, `THR/a`, `EHC`, `ARHE`, yields) are **qualitative at best for this test**. Mass-loss
  calorimetry from the balance (col 8) is the physically sound route for candle HRR.

### A.5 Burn timeline (from metadata + data)

| quantity | value | source / note |
|---|---|---|
| Test date / time | 26.08.2026, 15:09 | metadata |
| Standard | ISO 5660-1 (cone calorimeter) | metadata |
| Acquisition span | t = 0 … 3240 s (3,241 samples @ 1 s) | col 2 |
| Balance engaged / settled | t ≈ 12–14 s (col 8: 0 → 156.8 → 1557.6 → 1636.4 g) | col 8 |
| Test start time | 60 s | metadata `Test start time (s)` |
| Time to ignition | 23 s | metadata — **precedes "test start" (60 s) and balance settle (14 s); clock basis unclear, likely operator stopwatch or carried over — see Part C** |
| Time to flameout | 2427 s | metadata |
| End-of-test criterion | "User end of test", User EOT = 3240 s | metadata |
| Nominal duct flow | 24.0 l/s (measured `Vstack` ~24.1 l/s) | metadata + col 77 |
| External heat flux | nominally 75 kW/m²; **measured `HFM` ≈ 0** → heater effectively off | metadata vs col 12 |
| **Mass consumed, ignition→flameout** | **1636.45 g (t=23 s) − 1632.93 g (t=2427 s) = 3.52 g** | col 8 |
| Mass consumed, test-start→EOT (t=60→3240) | 1636.40 g − 1633.01 g = **3.39 g** | col 8 |
| Mean mass-loss rate during burn | ≈ 3.5 g / 2404 s ≈ **1.5 mg/s (≈ 0.088 g/min)** total | col 8 (whatever number of candles that represents — Part C) |
| Post-flameout mass | ~flat at 1633.0 g (t=2427 → 3240), within balance noise | col 8 |

---

## Part B — FireScope / FDS Visualizer parser & component inventory

Codebase: `/Users/samialachgar/Desktop/FireScope`, package `fdsvis` v6.0.0
(`src/`, PyQt5 + matplotlib + numpy + scipy + scikit-learn). ~90 modules in `src/`.

### B.1 Can the existing parser read the cone file? — **No. A new cone parser is required.**

The only CSV-reading data parser in the codebase is
`src/summary_stats.py :: _read_hrr_csv()` / `read_hrr_table()` (plus a thin re-use in
`src/energy_panel.py`). It targets the **FDS `*_hrr.csv`** output and assumes:

| assumption in `read_hrr_csv` | cone file reality |
|---|---|
| comma `,` delimiter (default `csv.reader`) | semicolon `;` |
| `.` decimal point → `float(row[i])` | `,` decimal (`float("18,73")` raises) |
| exactly 2 prelude rows, **units first then names** | names first, units second; **plus a ~60-row key/value metadata block in cols 0–1** |
| plain ASCII, `open(path, newline="")` (platform default encoding) | ISO-8859-1 with `°`, `²`, `µ` bytes → `UnicodeDecodeError` or mojibake on a strict UTF-8 read |
| unique column names, `header.index("HRR")` | **duplicate names** (`Mass`×2, `HRR`/`HRR/a`, `CO`×2, `CO2`×2, `n.u.`×21) — `.index()` silently returns the first |
| clean numeric rectangle | `Infinity`/`-Infinity` tokens, `999998` placeholders, blank trailing cells, blank interior cells |

`csv.reader` cannot be pointed at the cone file with a config tweak — the metadata-in-columns,
the decimal comma, and the duplicate-name resolution all need bespoke logic.
**Deliverable for a later phase: a dedicated `cone` parser** that (a) reads Latin-1 → UTF-8,
(b) splits the cols-0/1 metadata block from the channel block, (c) maps duplicate names to
explicit column indices, (d) parses decimal-comma floats with `Infinity`/blank/`999998`
sentinels → `NaN`, (e) returns `{channel: np.ndarray}` + a metadata dict + the time vector.
`read_hrr_table`'s return shape (`{name: ndarray}`) is a good template to mirror so the
existing plotting/metrics code can consume it.

### B.2 Component inventory

Verdict legend: **as-is** = usable unchanged · **changes** = usable with modification ·
**n/a** = FDS-field-specific, not applicable to 1-D cone/exponat time series.

#### FDS output parsing

| file | function / class | one-line description | reuse verdict |
|---|---|---|---|
| `src/fds/slice/slice.py` | `Slice`, `SliceCollection`, `readMeshes`, `combineSlices`, `combineSliceGeometry`, `findSlices` | FDS binary `.sf` slice-file reader (mesh stitching, time vectors) | **as-is** for the FDS side of the validation; **n/a** to cone/exponat |
| `src/fds/s3d/s3d.py` | `extract_volume_plane`, `volume_plane_geometry` | FDS `.s3d` volumetric-file plane extraction | **as-is** (FDS side) / **n/a** to cone |
| `src/load_data.py` | `load_data`, `load_slice_geometry`, `check_scenario_count` | wraps the slice/s3d readers into a quantity/direction/offset API; resolves `fds/sim_stage1_prep/` | **changes** (FDS side); **n/a** to cone |
| `src/summary_stats.py` | `_read_hrr_csv`, `read_hrr_table` | FDS `*_hrr.csv` reader → `(times, hrr)` / `{name: ndarray}` | **changes** — wrong dialect for cone (see B.1); mirror its return shape in the new cone parser |
| `src/manifest.py` | `get_manifest`, `scan_study`, `data_matrix_from_manifest`, `_resolve_scenario_path` | discovers FDS scenario folders, builds a case-index matrix from factor levels | **changes** — the folder-scan / manifest pattern is a good basis for indexing R1/R2/R3 repeats + FDS cases |
| `src/figure_export.py` | `parse_fds_revision`, `input_file_hash`, `provenance_line` | reads the FDS `.out` revision string + hashes the `.fds` deck for a figure provenance footer | **changes** — write an analogous cone-metadata / file-hash provenance line |
| `src/scenario_store.py` | `ScenarioStore`, `list_scenario_folders`, `build_data_matrix` | lazy per-scenario load + LRU cache of slice arrays | **changes** — caching pattern reusable for parsed cone tables (much smaller, so caching is optional) |

#### Data loading / organisation

| file | function / class | one-line description | reuse verdict |
|---|---|---|---|
| `src/data_provider.py` | `ScenarioSource` (Protocol), `SimulationData`, `DataLoadError`, demo-fallback | GUI-agnostic data handle + user-facing load-error type + synthetic fallback when real data absent | **changes** — clone the pattern for an `ExperimentDataProvider` (cone + exponat) |
| `src/experiment.py` | `Experiment` dataclass + JSON repo (`experiment_status`, baseline, tags, shared params) | groups related runs into one named study, reports each run `ready`/`missing` | **changes** — good fit for grouping candle repeats and pairing experiment↔FDS |
| `src/session_store.py` | `slugify`, `now_iso`, `make_metadata` | slug / timestamp / provenance-dict helpers | **as-is** |
| `src/config.py` | `N_CANDLES`, `FRAMES_PER_SECOND`, cache sizes | study constants | **changes** — add cone/exponat constants |
| `src/cli.py` | `main` (`fdsvis-cli stats|export|report|session-render`) | headless entrypoint | **changes** — a `cone`/`validate` subcommand could hang off the same argparse structure |

#### Time-series processing

| file | function / class | one-line description | reuse verdict |
|---|---|---|---|
| `src/timeseries.py` | `write_series_csv` | writes `x_label + series[]` to CSV with optional `# key,value` provenance header | **as-is** — generic, already the app's standard export |
| `src/timeseries.py` | `point_series`, `region_series`, `line_profile`, `phys_to_index` | reductions of a 3-D `(t,row,col)` slice array to 1-D | **n/a** (2-D-field oriented) |
| `src/summary_stats.py` | `fit_growth_alpha` | least-squares α for `Q = α(t−t₀)²` with unknown ignition delay t₀ (closed-form α per t₀ candidate) | **as-is** — directly applicable to a cone/FDS HRR growth curve |
| `src/summary_stats.py` | `_first_threshold_time`, `_first_threshold` | first time a series crosses a threshold | **as-is** |
| `src/summary_stats.py` | `compute_scenario_summary`, `ScenarioSummary`, `build_summary_index` | per-run scalar summary (peak, energy, α, threshold times) + freshness-checked cache | **changes** — the "one dataclass of computed scalars per run, cached" pattern transfers to cone runs |
| `src/analytics/features.py` | `_downsample`, `_first_crossing_seconds`, `compute_scenario_features` | resample curves to fixed length + crossing times → feature vector | **as-is** (`_downsample`, `_first_crossing_seconds`); **changes** (feature set) |
| `src/derived_quantities.py` | `peak_series`, `hazard_fraction_series` | per-frame max / fraction-over-threshold of a field | **changes** (`peak_series` is trivially 1-D-adaptable) |
| `src/derived_quantities.py` | `display_ceiling` | robust percentile-based axis ceiling with a floor | **as-is** |
| `src/field_calculator.py` | `validate`, `dependencies`, `evaluate`, `_fn_gradient`, `_fn_rate`, `infer_unit`, `CalculatedField` | **safe** AST expression engine over named quantities (`rate()`, `gradient()`, arithmetic; whitelist, never `eval`) | **changes** — could power user-defined derived cone channels (e.g. `rate(Mass)`, smoothed HRR); `_fn_rate`/`_fn_gradient` (finite diff w/ fps) usable **as-is** |
| `src/time_window.py` | interval-averaging helpers | average a series/field over a `[t0,t1]` window | **changes** |

#### Numerical utilities

| file | function / class | one-line description | reuse verdict |
|---|---|---|---|
| `src/study_analytics.py` | `build_table`, `factor_influence`, `influence_ranking`, `correlation_matrix`, `outlier_scores`, `study_statistics`, `normalized_axes` | treats a set of runs as a parameter×response table: factor effects, correlations, standardized-distance outliers, parallel-coords normalisation | **changes** — highly relevant for comparing repeats and experiment-vs-FDS responses (swap the "factors" for run identity / model) |
| `src/analytics/clustering.py` | `run_pca`, `run_clustering`, `_standardize`, `cluster_alignment` | PCA projection + KMeans over feature vectors (fixed seed) | **changes** — useful for a multi-run overview; likely overkill for a handful of runs |
| `src/measure.py` | `probe_value`, `rect_stats`, `_fractional_index` | bilinear interpolation + box stats on a 2-D field | **n/a** |
| `src/tenability.py` | `fed_heat_dose`, `fed_gas_dose`, `full_fed`, `time_to_*` | ISO 13571 / Purser FED dose integrals | **n/a** for cone; **changes** if the compartment (exponat) analysis wants occupant tenability |
| `src/zone_stats.py` | `zone_bundle`, thermal-dose integral, first-crossing | named-rectangle field reductions | **n/a** (field) — the first-crossing / dose-integral maths is trivially portable |
| `src/layer_height.py` | `smoke_layer_height_series` (gradient / half-integral methods) | thermal-interface height from a vertical temperature profile | **n/a** to cone; **changes** could apply to the compartment TC rake |
| `src/derived_quantities.py` | `dynamic_pressure`, `temperature_rise` | ½ρ|v|², T−ambient | **n/a** |

#### Plotting

| file | function / class | one-line description | reuse verdict |
|---|---|---|---|
| `src/widgets.py` | `MplCanvas` (FigureCanvas subclass, blitting, DPI scale, fixed white plot bg) | the app's standard embedded matplotlib canvas | **as-is** (GUI) |
| `src/widgets.py` | `MplCanvas` theme hook `_PLOT_THEME`, `PLOT_BG` | consistent light/dark-aware figure chrome | **as-is** |
| `src/energy_panel.py` | `energy_metrics`, `EnergyBudgetPanel` | plots HRR + Q_* components + MLR from a `{name: ndarray}` table; static, CSV-driven, not tied to playback | **changes** — the **closest existing analog to a cone HRR/MLR panel**; retarget `read_hrr_table` → cone parser, relabel channels |
| `src/figure_export.py` | `figure_png_bytes`, `_build_publication_figure`, `save_figure`, `preset_extension`, `PublicationExportDialog`, `export_figure_interactive` | journal-preset (size/DPI) SVG/PDF/PNG export with axes, colorbar, provenance footer | **changes** — built for heatmaps, but the preset/DPI/save/dialog plumbing and provenance footer are generic to any figure |
| `src/timeseries.py` | `TimeSeriesPanel` (Qt) | XY-over-time / profile-over-distance panel with multi-run overlay + CSV export | **changes** — UI scaffold (overlay picker, export button, plot placeholder) reusable; data plumbing is slice-array-specific |
| `src/report_builder.py` | `build_scenario_report`, `build_comparison_report`, `_document`, `_png_data_uri`, `write_report` | assembles a self-contained HTML report (figures as base64) with a print-to-PDF stylesheet | **changes** — pure string assembly; retarget the stats-table rows |
| `src/auto_summary.py` | `generate_summary`, `narrate_frame`, `export_markdown` | deterministic templated prose — every number comes from a computed summary, none generated | **changes** — reuse the "fixed template + computed numbers only" pattern for cone-run summaries |
| `src/branding.py` | `build_logo_widget`, `build_partner_logos_widget`, `PartnerLogosWidget` | FZJ / Wuppertal logo widgets | **as-is** (chrome) |
| `src/theme.py` | `Palette`, `apply_card_shadow`, theme tokens | light/dark palette + Qt styling | **as-is** |
| `src/widgets.py` | `LabeledSlider`, `Card`, `CollapsibleSection` (etc.) | common Qt widgets | **as-is** |

#### Other

| file | function / class | one-line description | reuse verdict |
|---|---|---|---|
| `src/evidence_notebook.py` / `evidence_notebook_panel.py` | `EvidenceNotebook` | append-only log of traceable findings with provenance | **changes** — good home for validation observations |
| `src/history.py`, `src/session.py`, `src/session_store.py` | undo stack / session (de)serialisation | app state persistence | **changes** |
| `src/export.py` | `AnimationExporter` | offscreen frame-sequence → video | **n/a** |
| `src/devices.py` | `Device`, `compute_thermocouple`, `export_csv` | virtual instruments on an FDS field; `export_csv` reuses `write_series_csv` | **n/a** (needs a field); `export_csv`'s metadata-header pattern is a nice model |
| `src/registry.py` | `QUANTITY_REGISTRY`, gating, units, `AMBIENT_C` | central quantity metadata (name→unit→display) | **changes** — a cone-channel registry (col index, canonical name, unit, "dead?" flag, downstream-preferred duplicate) would mirror this well |
| `src/quantity_provider.py` | `QuantityProvider` | resolves a quantity name → array, applying derived/calculated/gated logic | **changes** — same idea for resolving a cone channel name → cleaned series |

### B.3 Summary of the cleanest reuse targets

- **`write_series_csv`** (`timeseries.py`) — as-is, for all cone/derived exports.
- **`fit_growth_alpha`**, **`_first_threshold_time`**, **`_downsample`**, **`_first_crossing_seconds`**,
  **`display_ceiling`**, **`_fn_rate`/`_fn_gradient`** — as-is numeric helpers.
- **`EnergyBudgetPanel` / `energy_metrics`** (`energy_panel.py`) — the template for a cone
  HRR/MLR panel; change only the data source (new parser) and channel labels.
- **`study_analytics.py`** — as-is maths for a repeats + experiment-vs-FDS comparison table.
- **`figure_export.py`** + **`report_builder.py`** + **`auto_summary.py`** — the
  figure→stats→prose→HTML/PDF reporting chain, retargeted at cone-run summaries.
- **`experiment.py`** + **`manifest.py`** — organising R1/R2/R3 repeats and pairing each cone
  run with its FDS case.
- **`registry.py` / `quantity_provider.py`** — the pattern for a cone-channel registry that
  encodes column index, canonical name, unit, dead-channel flag, and which duplicate to prefer.
- **New code required:** the cone CSV parser (B.1), an exponat `.txt` parser (B.4), and a
  channel registry for the ~30 live cone channels.

### B.4 Exponat compartment `.txt` — format map + parser specification

Files: `2026-08-27_exponat_R1.txt` (864 data rows), `_R2.txt` (806), `_R3.txt` (975), all in
`/Users/samialachgar/Desktop/experiments/`. All three share one identical 89-column layout.

**A separate parser is required — it has nothing in common with the cone dialect.** But it is a
much simpler file: plain delimited ASCII, `.` decimal, one header row.

#### B.4.1 Format — verified against the bytes

| property | value | evidence |
|---|---|---|
| Encoding | **ASCII / UTF-8** (not Latin-1) | 0 bytes > 0x7F in any of the three files |
| Line terminator | **CRLF, with exactly one lone `\n`** — inside line 0, right after the `# ExpName:` comment (`…exponat_R1\ndate,time,…`); every real record ends CRLF, file ends CRLF | byte scan: `lone LF at byte 32`, `CRLF 865`, `CR 0` |
| Line 0 | comment: `# ExpName: 2026-08-27_exponat_R1` | must skip any leading `#` line |
| Line 1 | header, **89 comma-separated names** | — |
| Data | line 2 onward, `,`-delimited, `.`-decimal | every row has exactly 89 fields — **no ragged rows** |
| Numeric format | full-precision float repr of a float32 (`25.200000762939453`) | cast with `float()`, then optionally round |
| Booleans | literal `True` / `False` (cols `camera_trigger`, `loadcell_stable`) | — |
| Blank cells | present, `,,` — see B.4.4 | — |
| Sampling | **not exactly 1 Hz**: median Δt ≈ 1.02–1.03 s, drifts; wallclock span 883 s / 821 s / 992 s. No gaps > 2 s (apart from the B.4.4 split-writes at ~1 ms). | timestamp diff scan |

`csv.reader` with default dialect reads it directly (after skipping the `#` line). No encoding
argument needed beyond `encoding="utf-8"`.

#### B.4.2 Column map (89 cols)

| cols | header(s) | what it is | live? |
|---|---|---|---|
| 0 | `date` | full timestamp `YYYY-MM-DD HH:MM:SS.mmm` | **use** (fallback time base) |
| 1 | `time` | time-of-day only `HH:MM:SS.mmmmmm` — redundant with `date` | ignore |
| 2–41 | `TC_01` … `TC_40` | 40 thermocouple channels | **only 7 live** — see B.4.3 |
| 42–51 | `HFG_01_raw` … `HFG_10_raw` | heat-flux-gauge raw signal | **all dead** — constant `-59.3` in every row/run |
| 52 | `camera_trigger` | bool | dead — always `False`/blank |
| 53–62 | `HFG_01` … `HFG_10` | calibrated heat flux (kW/m²?) | **all dead** — each a constant large negative (`-452 … -524`), i.e. the calibration applied to the dead `-59.3` raw |
| 63 | `exp_time` | **experiment clock, integer seconds** — see B.4.4 | **use — this is the primary time axis** |
| 64 | `event_number` | operator/PLC phase marker, integer `0→1→2→3→4` step function | **use** (phase segmentation) |
| 65–74 | `HFG_10_serialnr` … `HFG_07_serialnr` (note: **out of order** — 10,2,1,9,4,3,5,6,8,7) | gauge serial numbers (`15211`–`15222`), constant | metadata only |
| 75 | `mass_loadcell` | compartment mass | **DEAD — constant `-999999.0` in every row of every run.** No compartment mass-loss data exists. |
| 76 | `loadcell_stable` | bool | dead — always `False` |
| 77–88 | `PLC_PRG.rRTC[1]` … `[12]` | PLC real-time-clock array | **dead** — constant `3276.6999511719` sentinel |

**Dead-value sentinels in this format:** `3276.6999511719` (open/unassigned DAQ channel — the
exponat equivalent of the cone's `999998`), `-999999.0` (loadcell), `-59.3` (HFG raw),
`-1.0` (`exp_time` out-of-window). A parser should map all of these to `NaN` per-column and
count them.

#### B.4.3 The only live channels

Across **all three runs**, exactly **7 of 40 thermocouples carry signal** — the same 7 every
time (consistent instrumentation):

| channel | role (inferred from magnitude) | R1 range °C | R2 range °C | R3 range °C |
|---|---|---|---|---|
| `TC_01` | plume / directly above flame — the hot one | 25 → 137 | 27 → 137 | 27 → 127 |
| `TC_02` | secondary (upper layer near fire?) | 25 → 51 | 26 → 57 | 26 → 72 |
| `TC_03` | secondary | 25 → 64 | 27 → 74 | 29 → 75 |
| `TC_05` | near-field, weak response | 25 → 29 | 26 → 31 | 27 → 31 |
| `TC_09` | far-field / ambient | 25 → 25 | 25 → 26 | 26 → 26 |
| `TC_10` | far-field / ambient | 25 → 26 | 25 → 27 | 26 → 27 |
| `TC_11` | far-field, weak response | 25 → 30 | 26 → 31 | 26 → 31 |

`TC_04`, `TC_06`, `TC_07`, `TC_08`, `TC_12`–`TC_40` (33 channels) are pinned at the
`3276.7` sentinel — **not connected**.

**Consequence for the study:** the compartment runs give a **7-point temperature history and an
event timeline — and nothing else**. No heat flux (all 10 HFG dead), no compartment mass
(loadcell dead). Any experiment↔FDS compartment comparison is limited to those 7 TC traces +
the event markers. TC rake geometry (which of the 7 is at what height/position) is **not in the
file** — Part C item 14.

#### B.4.4 Data-quality handling the parser must implement

1. **`exp_time` (col 63) is the time axis, not the row index and not the wallclock.**
   Integer seconds, monotonic non-decreasing. Starts at `0` (R1, R2) or is preceded by a few
   `-1` rows (R3 has 3 leading `-1`s, then `0` at row 3). `-1` = "outside the experiment
   window": R1 and R2 also carry a single trailing `-1` row (logging continued a beat past the
   defined end); R3 runs clean to `990`. It occasionally **skips a second** (e.g. R3 `…985, 987,
   988…`) — because the rows that would carry the skipped second are the split-writes below.
   Treat `-1` as NaN / "pre-roll / post-roll"; do not plot those rows on the experiment axis.
   `exp_time` tracks `date − date[first exp_time==0]` to within ~1 s over the whole run.

2. **`event_number` (col 64) is a step function `0→1→2→3→4`** — five operator/PLC phases.
   The transition times differ between runs (they are event-triggered, not clock-triggered):
   R1 → 213 / 303 / 334 / 489 s; R2 → 24 / 73 / 371 / 772 s; R3 → 17 / 47 / 303 / 403 s
   (in `exp_time` seconds). **What the 5 phases mean is undocumented** — Part C item 15. Use
   them to segment each run, but do not assume phase *k* is the same physical state across runs
   without confirmation.

3. **Split-write rows (the "1 ms" pairs).** A handful of times per file (R1: 1, R2: 4, R3: 7)
   the logger flushes one acquisition frame as **two rows ~1 ms apart**: the first row has the
   sensor columns populated but `exp_time` / `event_number` **blank**; the second row has
   `date`/`time` + `exp_time` + `event_number` populated but **all sensor columns blank** (and
   its tail columns are all the `3276.7` sentinel). This is the sole source of blank cells in
   the file (blank-cell count per column == number of split-writes: 1 / 4 / 7). Verified
   example, R1: `12:24:31.672` → `TC_01=86.8, exp_time=<blank>`; `12:24:31.673` →
   `TC_01=<blank>, exp_time=442`.
   **Parser options:** (a) merge each pair into one record (take the non-blank value from
   whichever half has it), or (b) forward-fill `exp_time`/`event_number` onto the sensor row and
   drop the all-blank companion. Either way the file loses ≤ 7 samples out of 800–975.

4. **Duplicate time base.** Drop `time` (col 1); keep `date` (col 0) only as a cross-check /
   fallback for `exp_time`.

5. **Dead-channel dropping.** Per B.4.2, drop or NaN-fill: all 20 `HFG*` columns, all 10
   `*_serialnr`, `mass_loadcell`, `loadcell_stable`, `camera_trigger`, all 12 `PLC_PRG.rRTC[*]`,
   and the 33 flat `TC_*` channels. What remains: `date`, `exp_time`, `event_number`, 7 TCs.

#### B.4.5 Reuse for the exponat parser

| need | reuse | verdict |
|---|---|---|
| read + skip comment + header row + `{name: ndarray}` | mirror `summary_stats.read_hrr_table` structure (not its dialect) | **changes** |
| tidy CSV export of the cleaned 7-TC table | `timeseries.write_series_csv` | **as-is** |
| TC history metrics (peak, peak rate, time-to-threshold 60/100/300 °C) | `devices.compute_thermocouple` operates on exactly this shape (a 1-D temperature history + fps) — feed it the measured trace instead of a probed field | **changes** (bypass the field-probe front end, keep the metrics core) |
| first-crossing / growth helpers | `summary_stats._first_threshold_time`, `analytics.features._first_crossing_seconds` | **as-is** |
| event-segmented windows | `time_window.py` interval helpers | **changes** |
| channel registry (col index, canonical name, unit, dead flag) | `registry.py` pattern | **changes** — one registry entry per live TC + `event_number` |
| non-uniform time base | none exist — the whole app assumes fixed fps (`FRAMES_PER_SECOND`); the exponat's ~1.02 s drifting Δt and skipped seconds mean **any rate-based helper (`_fn_rate`, `fed_*`, `compute_thermocouple`) must be given the real `exp_time` vector, or the traces resampled to a uniform grid first** | **new code** — a resample-to-1 Hz step, or pass explicit `dt` |

---

## Part C — Open questions for the human

1. **"3 Candles" vs. metadata.** The target file's specimen block (`Initial mass 11,61 g`,
   `Surface area 88,36 cm²`, `Thickness 13,03 mm`, `E 13,10 MJ/kg`, `Sample description Candle_R3`,
   `Specimen number R3`) is templated from a single-tea-light R3 run, yet the filename is
   `3_Candles_R1` and the siblings `27082026_3_Candles_R2/R3` carry `Initial mass 34–38 g`.
   **How many tea lights were on the balance in `26082026_3_Candles_R1`, and what was their
   true combined initial mass?**

2. **Was the conical heater on?** `HFM` (col 12) ≈ 0 for the whole run and the cone
   thermocouples read near ambient, contradicting `Heat flux 75 kW/m²`. **Confirm this is a
   free-burning candle test with no external radiant flux** (so `75` is a leftover default).

3. **Balance tare.** Raw load settles at ≈ 1636.4 g. What is the fixed tare (sample holder +
   pan + any fixture) so a net specimen mass and a mass-loss rate can be recovered? Is
   `1636.4 − tare` ≈ 35 g (three tea lights) or ≈ 12 g (one)?

4. **Ignition / flameout clock.** `Time to ignition = 23 s` is *before* `Test start time = 60 s`
   and before the balance stabilises (t ≈ 14 s). Do `23` and `2427` refer to acquisition t=0,
   to a "test start" offset, or to an operator stopwatch? Were they hand-entered post-hoc?
   (Needed to place ignition/flameout on the col-2 time axis.)

5. **Column 88 `Mass` — what is it?** It is not the physical balance (rises 1→18→16 g). Is it a
   software reconstruction (from `MFR`/`O2C`), a mis-scaled channel, or should it simply be
   discarded? Same question for `FU28` (≈ balance + 11.61 g) and `FU29` (= time).

6. **Is the O2-consumption HRR usable at all?** Whole-run O2 depletion is ≈ 0.039 % abs —
   ~2–4× the analyzer noise floor. Should candle HRR be reported **only** from
   `ṁ_loss × ΔH_c,eff` (balance-based), with col 89 shown as a labelled near-noise cross-check?

7. **Heat of combustion for the wax.** `E = 13,10 MJ/kg` in metadata is not paraffin
   (~42–46 MJ/kg). What net/effective ΔH_c should the mass-loss HRR use, and is the wax
   paraffin, stearin, or a blend?

8. **Candle specification.** Wick material/size, wax composition, tea-light cup material
   (`Material name/ID = Candle / Teelicht`), and candle geometry (diameter, height) are not in
   the file. Needed for the FDS burner definition.

9. **Which runs are the canonical validation set?** Repeats present: `3_Candles` → R1 (26.08),
   R2 & R3 (27.08); single candle → R1 (25.08, ~4 h), R2 & R3 (26.08). Is
   `26082026_Candle_R2` (HF `0`, no ignition/flameout) a deliberate cold/blank run? Which cone
   runs pair with which `2026-08-27_exponat_R*` compartment runs?

10. **Gas analysis.** The FTIR block (`CH4`, `CO`, `CO2`, `Ethene`, `H2O`, cols 23–27) and the
    `UOX*` channels (30–34) are empty or internal-diagnostic. Was species analysis not run for
    these tests, or exported to a separate file we should also ingest?

11. **Per-area normalisation basis.** `Surface area = 88,36 cm²` — is that the (three) candle
    tops, the sample-holder aperture, or a default? `HRR/a`, `MLR/a`, `THR/a` are meaningless
    until this is pinned. (`88.36 cm²` also happens to be shared verbatim by the two
    genuinely-3-candle files, so it may be a holder aperture, not a specimen surface.)

12. **Exponat runs pairing.** Do `2026-08-27_exponat_R1/R2/R3` correspond to the three
    27.08 3-candle cone runs, or to a separate compartment experiment on the same day? Do they
    share a trigger / clock with any cone run? (Format and channel inventory now fully mapped in
    **B.4** — this is the only remaining format question.)

13. **Exponat: `mass_loadcell` and all 10 heat-flux gauges are dead** (`-999999.0` and constant
    `-59.3` raw / large-negative calibrated, every row, every run). Was there really no working
    heat-flux or compartment-mass measurement, or do those live in a separate export? As it
    stands the compartment runs yield only 7 TC traces + an event timeline.

14. **Exponat TC geometry.** Which of the 7 live channels (`TC_01`–`03`, `05`, `09`–`11`) sit
    where? `TC_01` is clearly in/just above the plume (→ 130 °C); the rest need a position map
    (rake heights, wall vs. free-stream) before they can be matched to FDS `DEVC` points.

15. **Exponat `event_number` semantics.** What are phases `0/1/2/3/4`? (ignition, all candles
    lit, door/lid closed, steady, extinguish?) Transition times differ per run, so they are
    operator-triggered — a legend is needed to segment the runs consistently.

16. **Exponat `exp_time` origin.** `exp_time = 0` — is that candle ignition, DAQ start, or an
    external trigger? (R3 has 3 pre-roll `-1` rows before `0`; R1/R2 start at `0`. R1/R2 have a
    trailing `-1`.) Needed to align the TC histories to the cone-run ignition.

17. **`Comments` field is empty** in the target cone file. Was anything noted about this run
    (multiple relights, draughts, wick behaviour, which candle went out first)?
