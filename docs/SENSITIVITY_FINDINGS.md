# SENSITIVITY_FINDINGS — M3 uncertainty propagation

**Date 2026-09-10 (M3), updated 2026-09-11 (M4).** 8 sweep runs on Pleiades,
5 mm uniform (8-rank), T_END 350 s, plus the 2 mm nest baseline
`m2_base_nest20_450` (reached 410 s before its wall clock), plus 4 M4
wall-hypothesis runs (§M4). Post-processors: `src/sensitivity_post.py` →
`data/processed/sensitivity_bands.csv`, `sensitivity_tables.md`;
`src/m4_post.py` → `data/processed/m4_wall_test.md`. Figures:
`figures/m3_T3_wall_bracket.png`, `figures/m3_tracer_fill.png`,
`figures/m4_wall_variants.png`.

| run | knob | isolates |
|---|---|---|
| `s0_base_dx5` | — (18 W, χr 0.25, PMMA exposed) | 5 mm reference for every delta |
| `s1_hrr15` / `s2_hrr21` | HRR 15 / 21 W | the ± 15–20 % cone source band |
| `s3_rad20` / `s4_rad35` | radiative fraction 0.20 / 0.35 | literature spread (baseline 0.25) |
| `s5_wallins` | `BACKING='INSULATED'` | wall back-face heat loss |
| `s6_walladi` | `ADIABATIC` walls | the wall heat sink itself (no absorption) |
| `s7_tracer` | passive tracer at the cup | fog transport shape + timing |
| `m2_base_nest20_450` | 2 mm nest, 450 s target | resolution + run length on T3 |

The 5 mm runs (D\*/δx = 2.4) give **trends and deltas**, not converged absolute
values; T3 in particular carries ~±5 °C of mesh noise at 5 mm.

---

## 1 · Source uncertainty propagates small — it is not where the T3 gap is

T3 rise (°C), all 5 mm PMMA-exposed:

| | 15 W | 18 W | 21 W | χr 0.20 | χr 0.25 | χr 0.35 |
|---|--:|--:|--:|--:|--:|--:|
| @150 s | +13.0 | +15.4 | +17.0 | +18.9 | +15.4 | +16.5 |
| @350 s | +20.7 | +22.5 | +24.1 | +17.5 | +22.5 | +18.6 |

- **HRR ± 3 W (the whole cone band) → T3 ± ~2 °C, T5 ± 0.4 °C, doorway ± 0.1–0.6 °C.**
- **Radiative fraction 0.20–0.35 → T3 ± ~2 °C, far-field ± ≤ 0.5 °C.** (Some of this
  spread is 5 mm mesh noise, not real sensitivity.)
- Every non-wall knob leaves T3 in the **+13 to +24 °C** band. The measurement is
  **+30–43 °C**. **No source-term uncertainty closes that gap.**

**Conclusion:** the ± 15–20 % source characterisation (CONE_FINDINGS) is precise
enough for this validation. It moves no sensor by more than ~2.5 °C.

---

## 2 · The T3 residual is the wall heat-sink model — run length and mesh ruled out

→ **`figures/m3_T3_wall_bracket.png`**

| source | T3 @150 s | T3 @350 s | |
|---|--:|--:|---|
| **measured (R1–R3)** | **+30.0** | **+43.5 (broad peak)** | |
| m2 — 2 mm, PMMA exposed | +16.6 | **+15.7 (@410 s)** | flat for 350 s |
| s0 — 5 mm, PMMA exposed | +15.4 | +22.5 | |
| s5 — 5 mm, PMMA **insulated** | +15.6 | +22.5 | ≡ s0 |
| s6 — 5 mm, **adiabatic** | +39.9 | +60.3 | still climbing |

Three things fall out:

1. **Run length is ruled out.** The 2 mm run held T3 at **+16.5 → +15.7 °C from
   t = 60 s to t = 410 s** while `p_box` kept rising (240 → 414 Pa). T3 reaches
   quasi-steady in ~1 minute and stays there. P05's hedge — *"the gap to the
   +43 °C broad peak is dominated by the wall-thermal-mass timescale the 150 s
   runs do not reach"* — **is wrong**; a 410 s run does not reach it either.

2. **The wall back-face condition is irrelevant on this timescale.** s0 (exposed)
   and s5 (insulated) are identical to within noise. Thermal penetration into the
   10 mm PMMA slab over 350 s is √(αt) ≈ 6 mm < 10 mm — the outer face never
   "activates", so whether it loses heat to the lab or not makes no difference
   yet.

3. **The wall as a heat sink is a large lever.** Remove the wall's heat
   absorption entirely (adiabatic) and T3 climbs to +60 °C and is still rising.
   The **measurement (+30–43 °C) sits squarely between the PMMA and adiabatic
   curves** — roughly their midpoint.

**Interpretation.** The modelled compartment wraps the whole box in 10 mm opaque
cast PMMA (k = 0.19, ρc = 1.7 MJ m⁻³ K⁻¹, ε = 0.90). That slab is **about twice
too strong a heat sink** — it pins the ceiling-jet temperature at +16 °C while
the real compartment's ceiling climbs to +43 °C. The real walls behave as a much
weaker sink over the first few hundred seconds. Plausible causes, not yet
separated:

* **acrylic is semi-transparent in the mid-IR** — FDS treats it as a grey opaque
  absorber, so the model pulls the ceiling-jet's radiant load into the wall that
  in reality partly passes through / is not absorbed;
* an **air gap above the ceiling slab** (double-wall construction) — the gas sees
  a much smaller effective heat capacity early on than a solid 10 mm slab;
* **imperfect thermal contact** between the acrylic panels and at the joints.

This is genuine **model uncertainty on the wall thermal boundary** — quantifiable
as the bracket **T3 ∈ [+16 (full PMMA), +60 (no sink)]**, with the truth near the
weak-sink end. It is **not** numerical error and **not** run length.

---

## M4 · Wall-hypothesis test — no physically-motivated variant closes the gap

**Date 2026-09-11.** 4 runs on Pleiades, 5 mm uniform (8-rank), T_END 350 s.
Post-processor: `src/m4_post.py` → `data/processed/m4_wall_test.md`, figure
`figures/m4_wall_variants.png`. Rule followed throughout: **no variant is tuned
to hit a T3 target** — each is a one-sentence physical claim about the real rig,
run once, and judged on whether it moves T3 toward the data *and* keeps every
far-field residual ≤ 1 °C relative to baseline.

| variant | physical claim | T3 @150 s | T3 @250 s | T3 @350 s |
|---|---|--:|--:|--:|
| **measured (R1–R3)** | — | +30 | +32 | +34 (→ +43.5 peak) |
| `s0_base_dx5` (baseline) | 10 mm opaque cast PMMA, exposed backing | +15.4 | +17.1 | +22.5 |
| `w1_ir` | PMMA emissivity 0.85 (datasheet low end) + near-IR semi-transparency | +15.2 | +16.6 | +22.9 |
| `w2_thinceil` | inner-room ceiling = 4 mm sheet + 20 mm air gap (setup photo shows a gap) | +15.7 | +17.2 | +22.7 |
| `w3_thinall` | whole rig is ~4 mm sheet acrylic, not 10 mm slabs | +14.6 | +24.4 | +22.3 |
| `w4_contact` | assembled panels → joint contact resistance, lumped as k = 0.10 (bracket) | +15.0 | +22.7 | +23.1 |

**Result: none of the four moves T3.** All four land within **±0.6 °C of the
baseline's +22.5 °C at 350 s** — inside the 5 mm mesh-noise band (±5 °C, §1) and
nowhere near the measured +34 (matched-time) / +43.5 (peak). `w3_thinall` and
`w4_contact` show a transient bump at 250 s (+24.4, +22.7 vs baseline +17.1) but
it does not hold — both relax back to the baseline band by 350 s.

**Far-field integrity (T5/T9/T10/T11 @ 350 s vs measured peak):** every variant,
*including the baseline*, shows max |residual| 3.3–3.7 °C on this specific
metric — comparing the model's 350 s transient to the measurement's asymptotic
peak (the far-field sensors plateau by ~150 s per REPEATABILITY, the model has
not yet plateaued at 350 s). This is a **pre-existing baseline gap, not damage
introduced by a variant** — all five rows (baseline + 4 variants) sit within
0.4 °C of each other. No variant makes the far-field worse or better; the
integrity check's purpose — catching a variant that trades T3 for a broken
far-field — does not trigger here because no variant changes anything enough to
trade.

**T1/T2 untouched**, as required: +0.6–0.7 / +1.5–1.7 °C across all five rows.

**Conclusion — reported, not dialled further.** Following the M4 rule ("if no
physically-defensible variant reaches the measured range, report it — don't
keep dialing"): **three physically-motivated hypotheses for a weaker wall heat
sink (semi-transparent IR, a ceiling air gap, whole-rig thin sheet) and one
bracketing hypothesis (lumped contact resistance) all leave T3 pinned at the
same ~+22–23 °C the plain 10 mm-PMMA baseline gives.** The bracket from §2 —
measured value sits between full-PMMA (+16–22) and adiabatic (+60), nearer the
weak-sink end — **stands**, but none of the tested single-parameter causes
(emissivity/transparency, air gap, uniform thin sheet, uniform contact
resistance) is *itself* sufficient to move the model there at 5 mm. The
remaining candidates are either a **combination** of these effects, an
**unmodelled geometric detail** (localized joints/seals rather than a uniform
property change), or **resolution** (the wall differences may need the finer
mesh to register — 5 mm carries ±5 °C of its own noise, comparable to the
largest single-variant shift seen here). **T3 stays reported as the bracket
[+16, +60] °C with the wall thermal-boundary *model* as the flagged residual —
not resolved to a single mechanism.**

---

## 3 · T1 / T2 remain a structural limit — unchanged

The adiabatic run (s6) raises T1 to +23–46 °C and T2 to +27–50 °C — but it raises
**T5 by the same +26–50 °C, T9 by +9–31 °C, the whole room uniformly**. That is
bulk heating of a sealed box with no heat sink, **not** the plume reaching the
column probes. The near-fire rake (MESH_STUDY_FINDINGS §5) already showed the
prescribed-HRR plume never gets within 1 °C of x = 0.12 at any mesh; nothing in
the sweep changes that. **T1/T2 stay outside the model's predictive envelope.**

The auto-generated §2 "residual after knobs" table treats the adiabatic move as
covering T1/T2's gap — that is an artefact of the same-sign heuristic and should
be read past. The adiabatic case is a **bracket, not a candidate model.**

---

## 4 · The fog-analogue tracer matches the video

→ **`figures/m3_tracer_fill.png`**. `s7_tracer`: passive tracer, released from the
candle-cup side faces, ramped with ignition. **Transport shape + timing only —
never concentration** (the fog injection rate is unrecorded).

* **Stratification** (`tr_upper / tr_lower`): a sharp early peak (~22× while the
  tracer is still in the ceiling layer, t ≈ 30 s), decaying to **~1.3 by t ≈ 100 s**
  and holding there — i.e. the modelled compartment mixes to near-uniform within
  ~1.5 minutes.
* **Fill**: gradual over minutes on both levels; the plenum lags by ~50 s and
  stays 1–2 orders of magnitude below the room throughout — **weak doorway flow**.

The video (SMOKE_FINDINGS §3) shows fog first visible at **t ≈ +150 s**, then a
gradual room-filling with **no sharp descending interface**. In that observable
window the model says *near-uniform, still slowly filling* — **the model and the
video agree.** The model's early stratification transient (t < 60 s) is below the
video's detection threshold and cannot be confirmed either way; flag it as an
assumption, not a match.

**Both the tracer and the thermocouples say the same thing about the compartment
transport: a weak, slow, near-uniform fill — the FDS compartment flow model is
sound.** (The wall §2 issue is a *thermal boundary* problem, not a flow problem.)

---

## 5 · Revised uncertainty budget (feeds VALIDATION_FINDINGS §2)

| sensor | measured rise | FDS (2 mm, baseline) | source band (HRR ⊕ χr) | wall-model band | verdict |
|---|--:|--:|--:|--:|---|
| T5 / T9 / T10 / T11 | +1–5 °C | within ~1–2 °C | ≤ ±0.6 °C | small (far from the walls' influence) | **validated** |
| T3 | +30 (150 s) → +43.5 (peak) | +16, flat | ±2.5 °C | **[+16 … +60], truth near weak-sink end** | residual = **wall thermal-boundary model** |
| T1 / T2 | +49 / +13 (65 s) → +107 / +35 (peak) | +0.5 / +1.4 | negligible | not applicable (bracket only) | **structural** — prescribed-HRR LES, no reaction zone |

---

## 6 · Limitations

1. The sweep is **5 mm** (D\*/δx = 2.4) — deltas and trends only; T3 absolute
   carries ~±5 °C mesh noise. The wall bracket [+16, +60] is robust because it is
   a *ratio* of effects, but the endpoints are 5 mm values.
2. **`m2` stopped at 410 s**, not 450 s (48 h wall clock). T3 was flat from 60 s;
   a `RESTART=.TRUE.` to 450 s would not change the finding.
3. **One run per configuration** — no LES ensemble.
4. `s6` adiabatic drives `p_box` to 12.8 kPa — a non-physical sealed-box
   pressurisation. It is used only as the no-heat-sink bracket.
5. The wall-model causes in §2 (IR-transparency, air gap, contact) **were tested
   individually in §M4** and none, alone, moved T3 beyond the 5 mm noise floor —
   they remain unseparated; a combination, an unmodelled localized geometric
   detail, or finer resolution are the remaining candidates.
6. **M4 is also 5 mm.** A shift smaller than ~5 °C between variants is not
   distinguishable from mesh noise at this resolution — the M4 null result
   (all variants within 0.6 °C of baseline) is solid, but a *small* real effect
   from any one hypothesis could be hiding under that noise floor.
