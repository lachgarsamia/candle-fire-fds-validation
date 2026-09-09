# FDS Geometry Reference — candle compartment (Phase 2)

Coordinate convention: x = length (0 at back wall, +x toward doorway),
y = depth (0 to 0.30 m), z = height (0 at floor). All TCs depth-centered y = 0.15 m.

## Domain & room — CONFIRMED

| element | x | y (depth) | z (height) | confidence |
|---|---|---|---|---|
| Simulation domain (outer box) | 0 – 1.00 m | 0 – 0.30 m | 0 – 0.50 m | confirmed |
| Instrumented room (interior) | 0 – 0.70 m | 0 – 0.30 m | 0 – **0.23 m** | confirmed (height corrected from 0.30) |
| Room walls | acrylic (PMMA), **10 mm thick** | — | — | confirmed |

Room shares width (depth) with the box; differs in length and height.
Room height 0.23 m; box height 0.50 m → 0.27 m open plenum above the room.

## Doorway — CONFIRMED (geometry) 

| element | position | size | confidence |
|---|---|---|---|
| Doorway | left wall (x = 0.70 m), floor level | 0.15 m high × 0.05 m wide | confirmed |
| — depth position across y | **centered, y = 0.125–0.175 m** | confirmed |

## Fire source

| element | x | y | z | confidence |
|---|---|---|---|---|
| Candle | 0.09 m from back wall | 0.15 m (depth center) | floor (0) | confirmed |
| Candle cup | aluminium, ~1 cm wax depth, **diameter ≈ 37 mm** | | | confirmed |
| Burner area | π(0.0185)² ≈ 1.08e-3 m² → **HRRPUA ≈ 17 kW/m²** at 18 W | | | derived |
| Source term | ~18 W per candle (Route C) | | | confirmed from cone data |

## Thermocouples — 7 total, all at y = 0.15 m (depth center)

| TC | location | x | z (height) | confidence |
|---|---|---|---|---|
| T1 | back-wall support, 0.12 m | 0.12 m | 0.05 m | confirmed |
| T2 | back-wall support, 0.12 m | 0.12 m | 0.16 m | confirmed |
| T3 | back-wall support, 0.12 m | 0.12 m | 0.23 m (at ceiling) | confirmed |
| T5 | ceiling center | 0.35 m | 0.23 m | confirmed |
| T9 | doorway | 0.70 m | 0.015 m | confirmed |
| T10 | doorway | 0.70 m | 0.075 m | confirmed |
| T11 | doorway | 0.70 m | 0.14 m | confirmed |

### T1/T2/T3 horizontal position — RESOLVED
- T1–T3 sit **0.12 m from the wall opposite the doorway** (= the back/fire-end
  wall at x = 0), i.e. **x = 0.12 m**, mounted on a support at that line,
  depth-centered y = 0.15 m, heights 5 / 16 / 23 cm.
- This is 3 cm behind the candle (x = 0.09 m), toward the back wall.
- All three descriptions now agree: "attached to the wall" (on a support at the
  0.12 m line), "12 cm from the right wall opposite the doorway", and the
  diagram's "interior column — 0.12 m" are the same position. No conflict.

## Still open (only one item — not geometry)
1. Confirm wax is paraffin (assumed) — sets ΔHc for the cone HRR. If the cone
   agent's O₂-integrated energy ÷ manual Δm lands near 40 MJ/kg, paraffin is
   confirmed empirically and no separate confirmation is needed.

Geometry is otherwise COMPLETE: domain, room (10 mm PMMA walls), doorway
(centered), candle (37 mm, HRRPUA ~17 kW/m²), all 7 TCs, and the smoke tracer
are all pinned.

## Notes for the FDS model
- Free-burning ~18 W source; model 3 candles (when relevant) as separate burners.
- Acrylic walls are NOT thermally inert over a multi-minute burn — specify PMMA
  SURF (conductivity, density, specific heat), not the default cold wall.
- Photo orientation is left-right mirrored vs the diagram (candle end on the
  right in the photo, doorway on the left). Orientation only, not a conflict.
- Mesh: an ~18 W fire has a very small characteristic diameter D* — the mesh
  study (Phase 3) is decisive; sub-cm cells likely needed near the plume.

## Smoke tracer (Exponat visualization only — NOT part of the fire)
- Tracer = Glycerinum 85% (85% glycerol / 15% water, pharmacy grade).
- Introduction: a few DROPS placed on the metal cup/plate ON TOP of the candle,
  MID-experiment. Vaporized by the flame heat and rose WITH the plume — a hot,
  buoyant tracer co-located with the fire (NOT a cold fogger).
- Implication (good for validation): smoke and heat share a source and buoyancy,
  so smoke transport should track the thermal field closely. A divergence is
  informative, not automatically FDS error.
- It is a PASSIVE flow tracer for transport, not a combustion soot product.
  Candle flame is otherwise clean (cone soot ≈ 0).
- Timing: one-time mid-run addition → smoke exists only AFTER introduction. Time
  all smoke-layer events from the "glycerin added" moment, read from the video,
  NOT from ignition. (Small TC bump possible at introduction as glycerin flashes.)
- FDS: represent as a passive tracer/scalar released at the candle top, starting
  at the introduction time — not as combustion soot, not from t=0.
