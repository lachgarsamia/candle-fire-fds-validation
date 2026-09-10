# Sensitivity tables (auto -- sensitivity_post.py)

## 1. Per-sensor uncertainty from each source/wall knob

Rise above ambient (°C). `base` = s0 (5 mm, 18 W, χr 0.25, PMMA-exposed). `±HRR` = |dT/dHRR|·3 W. `±rad` = half-range over χr 0.20–0.35. `wall→ins/adi` = Δ from exposed to insulated / adiabatic backing.

| TC | t (s) | meas | base | ±HRR | ±rad | wall→ins | wall→adi |
|----|------|------|------|------|------|----------|----------|
| T1 | 150 | 76.3 | 0.4 | 0.1 | 0.0 | +0.0 | +23.1 |
| T1 | 250 | 92.1 | 0.5 | 0.1 | 0.0 | +0.0 | +34.8 |
| T1 | 350 | 95.9 | 0.6 | 0.1 | 0.0 | +0.0 | +45.6 |
| T2 | 150 | 9.6 | 1.4 | 0.2 | 0.1 | -0.0 | +27.5 |
| T2 | 250 | 12.6 | 1.5 | 0.3 | 0.2 | +0.0 | +39.4 |
| T2 | 350 | 17.4 | 1.5 | 0.3 | 0.2 | -0.0 | +50.1 |
| T3 | 150 | 30.0 | 15.4 | 2.0 | 1.7 | +0.1 | +24.5 |
| T3 | 250 | 32.1 | 17.1 | 2.0 | 1.1 | +0.0 | +33.1 |
| T3 | 350 | 33.9 | 22.5 | 1.7 | 2.5 | -0.0 | +37.8 |
| T5 | 150 | 2.2 | 2.3 | 0.2 | 0.4 | -0.1 | +26.5 |
| T5 | 250 | 2.8 | 1.7 | 0.6 | 0.1 | -0.3 | +40.0 |
| T5 | 350 | 2.9 | 2.2 | 0.4 | 0.2 | +0.0 | +49.7 |
| T9 | 150 | 0.0 | 0.0 | 0.0 | 0.0 | -0.0 | +9.2 |
| T9 | 250 | 0.1 | 0.0 | 0.0 | 0.0 | +0.0 | +19.9 |
| T9 | 350 | 0.1 | 0.0 | 0.0 | 0.0 | -0.0 | +31.3 |
| T10 | 150 | 0.3 | 0.5 | 0.1 | 0.2 | +0.0 | +22.4 |
| T10 | 250 | 0.3 | 0.2 | 0.0 | 0.1 | +0.1 | +33.9 |
| T10 | 350 | 0.5 | 0.7 | 0.1 | 0.2 | -0.3 | +42.9 |
| T11 | 150 | 2.8 | 0.5 | 0.1 | 0.3 | -0.1 | +27.7 |
| T11 | 250 | 3.5 | 0.9 | 0.3 | 0.2 | +0.6 | +39.2 |
| T11 | 350 | 3.4 | 1.3 | 0.1 | 0.4 | -0.4 | +48.8 |

## 2. Itemised model discrepancy at t = 150 s (replaces the lump 'residual' in VALIDATION_FINDINGS §2)

| TC | meas–base | ±HRR | ±rad | wall (exp→ins→adi) | residual after knobs |
|----|-----------|------|------|--------------------|----------------------|
| T1 | +75.9 | 0.1 | 0.0 | 0.4→0.4→23.5 | +52.7 |
| T2 | +8.1 | 0.2 | 0.1 | 1.4→1.4→29.0 | +0.0 |
| T3 | +14.6 | 2.0 | 1.7 | 15.4→15.6→39.9 | +0.0 |
| T5 | -0.1 | 0.2 | 0.4 | 2.3→2.3→28.8 | -0.0 |
| T9 | +0.0 | 0.0 | 0.0 | 0.0→0.0→9.2 | +0.0 |
| T10 | -0.2 | 0.1 | 0.2 | 0.5→0.5→22.8 | -0.0 |
| T11 | +2.3 | 0.1 | 0.3 | 0.5→0.4→28.2 | +0.0 |

## 3. T3 — resolution vs wall vs run-length (the P05 hedge, resolved)

| source | T3 @150 s | T3 @350 s | note |
|--------|-----------|-----------|------|
| measured (R1–R3) | +30.0 | +43.5 (peak) | broad peak ~300–450 s |
| P04 nest20 (2 mm, 150 s) | +16.4 | -- | prior baseline |
| m2_base_nest20_450 (2 mm) | +16.6 | +15.6 | **does T3 climb 150→350 s?** |
| s0 (5 mm, exposed) | +15.4 | +22.5 | coarser mesh |
| s5 (5 mm, insulated) | +15.6 | +22.5 | no loss to lab |
| s6 (5 mm, adiabatic) | +39.9 | +60.3 | no wall thermal mass (upper bound) |

**Run-length effect (2 mm): T3 moves -0.9 °C from 150 → 350 s.** Does NOT support run-length as the main cause — revisit the P05 wording.
- wall BC span at 150 s (5 mm): exposed +15.4 → adiabatic +39.9  (Δ +24.5 °C)
