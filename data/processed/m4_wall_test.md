# M4 wall-hypothesis test (auto — src/m4_post.py)

T3 and the far-field vs measurement, 5 mm runs. A variant is a **fix** only if it moves T3 toward the data **and** keeps every far-field residual ≤ 1 °C.

## T3 rise above ambient (°C)

| variant | 150 s | 250 s | 350 s | hypothesis |
|---|--:|--:|--:|---|
| **measured (R1–R3)** | +30 | +32 | +34 (→ +43.5 peak) | — |
| s0_base_dx5 | +15.4 | +17.1 | +22.5 | baseline — 10 mm opaque cast PMMA, exposed backing |
| w1_ir | +15.2 | +16.6 | +22.9 | V1 · PMMA emissivity 0.85 (datasheet low end) + near-IR semi-transparency |
| w2_thinceil | +15.7 | +17.2 | +22.7 | V2 · inner-room ceiling = 4 mm sheet + 20 mm air gap (setup photo) |
| w3_thinall | +14.6 | +24.4 | +22.3 | V3 · whole rig is ~4 mm sheet acrylic, not 10 mm slabs |
| w4_contact | +15.0 | +22.7 | +23.1 | V4 · assembled panels — joint contact resistance as reduced k=0.10 (bracket) |

## Far-field integrity (rise °C @ 350 s; residual vs measured broad peak)

| variant | T5 | T9 | T10 | T11 | max |resid| | verdict |
|---|--:|--:|--:|--:|--:|---|
| **measured (peak)** | +4.6 | +0.2 | +1.1 | +4.7 | — | — |
| s0_base_dx5 | +2.2 | +0.0 | +0.7 | +1.3 | 3.4 | breaks far-field |
| w1_ir | +2.3 | +0.0 | +0.3 | +1.1 | 3.6 | breaks far-field |
| w2_thinceil | +2.5 | +0.0 | +0.4 | +1.2 | 3.5 | breaks far-field |
| w3_thinall | +2.6 | +0.0 | +0.9 | +1.4 | 3.3 | breaks far-field |
| w4_contact | +2.6 | +0.0 | +0.5 | +1.0 | 3.7 | breaks far-field |

## T1 / T2 (structural finding must be untouched)

| variant | T1 @350 | T2 @350 |
|---|--:|--:|
| s0_base_dx5 | +0.6 | +1.5 |
| w1_ir | +0.6 | +1.5 |
| w2_thinceil | +0.6 | +1.6 |
| w3_thinall | +0.7 | +1.7 |
| w4_contact | +0.7 | +1.7 |