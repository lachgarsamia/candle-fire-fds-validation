# Weigh-table mapping — computed results & roster changes

## Per-candle mass loss and mean HRR (Route C, dHc_eff = 38 MJ/kg)

| run | config | total Δm (g) | Δm/candle (g) | burn (s) | **HRR/candle (W)** | usable for HRR? |
|---|---|---|---|---|---|---|
| 26082026_Candle_R3 | 1 | 1.62 | 1.62 | 3085 | **20.0** | yes — but not fully steady |
| 26082026_3_Candles_R1 | 3 | 3.53 | 1.18 | 2404 | **18.6** | yes — cleanest 3-candle run |
| 27082026_3_Candles_R2 | 3 | 1.10 | 0.37 | 844 | **16.5** | yes — short burn |
| 25082026_Candle_R1 | 1 | 8.29 | 8.29 | ~3.8 h | — | **no** — filter drift, HRR invalid |
| 26082026_Candle_R2 | 1 | 1.36 | 1.36 | not logged | — | mass ok, no timeline |
| 27082026_3_Candles_R3 | 3 | — | — | 1725 | — | **no** — after-mass missing |

## Headline findings

1. **A tealight is a ~18 ± 2 W source.** Per-candle HRR clusters at 16.5–20.0 W
   across single- and 3-candle runs. This is your candle source term for FDS,
   and it is robust.

2. **Superposition ≈ linear (slightly suppressed).** 3-candle per-candle rate
   (16.5–18.6 W) ≈ single-candle rate (20.0 W). Candles at this spacing behave
   like ~independent sources → **model 3 separate burners in FDS**, not one
   merged source. The mild suppression (vs 20 W) is a minor, reportable coupling
   effect.

3. **Filename mystery solved:** 3_Candles_R1 = genuinely 3 candles (34.19 g).
   Internal metadata logged only candle 1's mass. Notebook wins.

## Roster changes vs Prompt 01 (act on these)

- **No blank run exists.** Candle_R2 burned (−1.36 g). Bound the O₂ noise floor
  from pre-settle / post-flameout segments *inside* the burning runs instead.
- **25.08 R1 HRR is disqualified** (dirty-filter drift). Keep as a mass-loss
  cross-check only; exclude from all HRR statistics.
- **Candle_R3 is valid but not fully steady** — its 20 W may slightly over-read
  the true steady value; flag it.
- **3_Candles_R3 has no after-mass** → timeline only, no Route C HRR.
- **Metadata ignition times are not physical** — candles were hand-lit before
  insertion. Use load-cell settle + flameout for timing.

## Consistency check vs recon

Recon measured ~3.5 g load-cell drop on 3_Candles_R1; notebook Δm = 3.53 g.
**They agree.** The load cell trend is trustworthy for *shape*, and the manual
mass is trustworthy for *magnitude* — as designed.

## Still open (non-blocking)

- Confirm wax is paraffin (assumed) — sets dHc. If the O₂-integrated energy ÷
  manual Δm lands near 40 MJ/kg, paraffin is confirmed empirically.
- Cup diameter (have thickness ~1 cm, aluminium cup) — for FDS Phase 2 geometry.
