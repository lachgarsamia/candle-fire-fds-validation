"""make_fds.py -- candle-compartment FDS deck generator (P03 baseline + P04 mesh study).

Geometry, source term and the 7 validation probes are FIXED from:
  FDS_geometry_reference.md   (authoritative geometry)
  CONE_FINDINGS.md            (18 W/candle, HRRPUA ~17 kW/m2, constant/linear burn,
                               paraffin dHc, +-15-20% source uncertainty)
  EXPONAT_FINDINGS.md 9       (the 7 TC targets; TEMPERATURE + timing only)
  PROJECT_STATE.md            (settled facts)

Nothing here is tuned to match the experiment. Only `--dx` (and the nested
`--fine-dx`) change between P04 mesh variants; everything else is identical.

BOUNDARY CONDITION -- USER CORRECTION (2026-09-02), overrides the P03 prompt text:
  The whole system is SEALED. The outer acrylic box is closed on ALL faces; the
  room breathes only through its doorway into the closed outer box. There are NO
  OPEN domain boundaries. The fire has only the air trapped in the box at t=0.
  (The P03 prompt says "Open the domain boundaries" -- this is the conflict
  flagged in FDS_BASELINE_NOTES.md; the later explicit user instruction wins.)

Usage:
  python make_fds.py --dx 0.010 --t-end 150 --chid candle_coarse_dx10
  python make_fds.py --dx 0.005 --t-end 250 --chid candle_medium_dx5
  python make_fds.py --dx 0.010 --fine-dx 0.0025 --t-end 250 --chid candle_fine_nested25

M3 source/wall sweep knobs (defaults reproduce the P03/P04/P05 baseline deck):
  --hrr-w 15 / 21           per-candle HRR, W  (source band 15-21)
  --rad-fraction 0.20/0.35  RADIATIVE_FRACTION
  --soot-yield 0.02         SOOT_YIELD
  --dhc 38000               HEAT_OF_COMBUSTION, kJ/kg
  --wall {pmma,pmma-insulated,inert}   wall model preset
M2 smoke: LAYER HEIGHT + UPPER/LOWER TEMPERATURE at x = 0.12 / 0.35 / 0.66, plus
  MASS FRACTION(SOOT) + VISIBILITY centre-plane slices -- ON by default
  (--no-smoke for a P04-era deck). Verified on Pleiades FDS 6.11.1 (2026-09-08)
  with a trivial probe deck: LAYER HEIGHT, UPPER/LOWER TEMPERATURE, VISIBILITY and
  MASS FRACTION+SPEC_ID='SOOT' all parse; 'SOOT VOLUME FRACTION' and 'SOOT
  DENSITY' do NOT exist in this build (ERROR 1042).

Run every deck through fds/run_fds.sh -- meshes finer than 10 mm SIGSEGV in
init_mp_initialize unless OMP_STACKSIZE=200M and ulimit -s are raised.

Fuel: the REAC carries FORMULA='C25H52' directly. Do NOT also add a standalone
&SPEC ID='PARAFFIN' -- the double-declaration crashes FDS 6.11.x species setup
(`malloc: corrupted top size`, confirmed on Pleiades 2026-09-02).

Nested meshes -- the fixes that make FDS 6.11.1 accept a nested candle deck
(each isolated by bisection, 2026-09-02/03):
  1. fuel via `&REAC FUEL='PARAFFIN', FORMULA='C25H52'` -- a standalone
     `&SPEC ID='PARAFFIN'` double-declares and corrupts species setup.
  2. TWO levels only: core(fine_dx) inside outer(4*fine_dx), 4:1. A 3-level
     nest (core<mid<outer) hangs FDS 6.11.1 in read_input on this stack.
  3. every core face snapped to the outer grid (_snap_region); cluster
     sub-meshes split on shared hierarchical cut-planes so no core mesh
     straddles an outer-mesh boundary (check_nesting.py verifies both).
  4. core mesh z-max = 0.24 so it fully contains the ceiling OBST (0.23-0.24) --
     a partly-overlapping OBST just above the core z-max mis-snaps to zero
     thickness -> malloc corruption.
  5. the burner is a VENT on top of a 1-outer-cell INERT block, NOT a floor
     vent (rejected where it overlaps the sealed ZMIN wall) and NOT a burning
     OBST (ERROR 607 BURN_AWAY on the coarse mesh).
Any of 1-5 wrong -> `malloc(): corrupted top size` or a hang at read_input /
init. Run check_nesting.py on every nested deck before submitting.
"""
from __future__ import annotations
import argparse
import math
import os
import re
import textwrap

# --- fixed geometry (m) -- FDS_geometry_reference.md ----------------------
DOMAIN = (0.0, 1.00, 0.0, 0.30, 0.0, 0.50)      # outer acrylic box INTERIOR
ROOM_X, ROOM_Z = 0.70, 0.23
WALL_TH = 0.010                                  # 10 mm acrylic
DOOR = dict(x=0.70, y0=0.125, y1=0.175, h=0.15)  # left wall, floor level, 0.05 w x 0.15 h
CANDLE = dict(x=0.09, y=0.15, cup_d=0.036, cup_h=0.010)

# --- source term -- CONE_FINDINGS.md ------------------------------------
HRR_W = 18.0                    # per candle (band 16-20; +-15-20% total uncertainty)
RAD_FRACTION = 0.25             # small clean candle flame (literature; NOT tuned)
DHC_KJKG = 42000.0             # paraffin net
SOOT_YIELD = 0.008            # candle flame is clean (RECON: cone soot ~ 0)
IGNITION_RAMP_S = 25.0         # P03: 20-30 s ignition transient to the steady value

# --- ambient -- EXPONAT R1 pre-ignition TC median ~25.1 C ---------------
TMPA = 25.0                    # (cone rig metadata says 26.8 C; the compartment
                              #  air at the start of exponat R1 was ~25 C -- use that)

# --- 7 thermocouples (x, y, z) -- geometry ref / EXPONAT_FINDINGS 9 -----
# T3/T5 nominal z is 0.23 ("at ceiling"); placed at 0.225 here -- 5 mm below the
# ceiling underside -- so the probe is in the ceiling-jet GAS and not inside the
# snapped ceiling OBST at any mesh resolution. Documented; P05 pairs 1:1 anyway.
TCS = {
    "T1": (0.12, 0.15, 0.05),   # 3 cm behind candle, near floor -> in flame/plume
    "T2": (0.12, 0.15, 0.16),
    "T3": (0.12, 0.15, 0.225),  # ceiling-jet, near the fire  (nominal 0.23)
    "T5": (0.35, 0.15, 0.225),  # ceiling-jet, mid-room        (nominal 0.23)
    "T9": (0.70, 0.15, 0.015),  # doorway, floor (inflow)
    "T10": (0.70, 0.15, 0.075),
    "T11": (0.70, 0.15, 0.14),  # doorway, top (outflow)
}
TC_BEAD_D = 0.0010            # 1 mm bead (bare fine wire, assumed)
TC_BEAD_EMIS = 0.85           # oxidised metal bead


def dstar(q_w: float, tmpa: float = TMPA) -> float:
    rho, cp, t_inf, g = 1.18, 1005.0, tmpa + 273.15, 9.81
    return (q_w / (rho * cp * t_inf * math.sqrt(g))) ** 0.4


# --- wall presets -- the "how much of the late T3 climb is the wall model?" axis.
#   pmma            : 10 mm cast PMMA, outer face EXPOSED to lab air (baseline).
#   pmma-insulated  : same slab, INSULATED backing -- walls still absorb heat but
#                     do not leak it to the lab -> upper bound on retained heat.
#   inert           : ADIABATIC walls, no absorption, no loss -> gas-only ceiling
#                     (removes wall thermal mass entirely; brackets the other end).
WALL_PRESETS = {
    "pmma": dict(
        matl="&MATL ID='PMMA', CONDUCTIVITY=0.19, SPECIFIC_HEAT=1.47, DENSITY=1180.0, EMISSIVITY=0.90 /",
        surf=f"&SURF ID='ACRYLIC_WALL', MATL_ID='PMMA', THICKNESS={WALL_TH:.3f}, BACKING='EXPOSED',\n"
             f"      COLOR='SKY BLUE', TRANSPARENCY=0.2 /",
        note="10 mm cast PMMA, EXPOSED backing (loses to lab air at TMPA)"),
    "pmma-insulated": dict(
        matl="&MATL ID='PMMA', CONDUCTIVITY=0.19, SPECIFIC_HEAT=1.47, DENSITY=1180.0, EMISSIVITY=0.90 /",
        surf=f"&SURF ID='ACRYLIC_WALL', MATL_ID='PMMA', THICKNESS={WALL_TH:.3f}, BACKING='INSULATED',\n"
             f"      COLOR='SKY BLUE', TRANSPARENCY=0.2 /",
        note="10 mm cast PMMA, INSULATED backing (no loss to lab -> retains more heat)"),
    "inert": dict(
        matl="! (no MATL -- ADIABATIC surface)",
        surf="&SURF ID='ACRYLIC_WALL', ADIABATIC=.TRUE., COLOR='SKY BLUE', TRANSPARENCY=0.2 /",
        note="ADIABATIC walls (no thermal mass, no loss) -- brackets out the wall model"),

    # --- M4 wall-hypothesis variants (each = one physical claim about the RIG,
    #     NOT a knob tuned to hit a T3 target). See docs/SENSITIVITY_FINDINGS.
    "pmma-ir": dict(   # V1
        matl="&MATL ID='PMMA', CONDUCTIVITY=0.19, SPECIFIC_HEAT=1.47, DENSITY=1180.0, EMISSIVITY=0.85 /",
        surf=f"&SURF ID='ACRYLIC_WALL', MATL_ID='PMMA', THICKNESS={WALL_TH:.3f}, BACKING='EXPOSED',\n"
             f"      COLOR='SKY BLUE', TRANSPARENCY=0.2 /",
        note="cast-PMMA hemispherical emissivity ~0.85 (datasheet low end) + near-IR "
             "semi-transparency: not all hot-layer radiation is absorbed at the wall surface"),
    "thin-ceiling": dict(   # V2 -- photo-supported
        matl="&MATL ID='PMMA', CONDUCTIVITY=0.19, SPECIFIC_HEAT=1.47, DENSITY=1180.0, EMISSIVITY=0.90 /\n"
             "    &SURF ID='ROOM_CEILING', MATL_ID='PMMA', THICKNESS=0.004, BACKING='INSULATED',\n"
             "          COLOR='SKY BLUE', TRANSPARENCY=0.2 /",
        surf=f"&SURF ID='ACRYLIC_WALL', MATL_ID='PMMA', THICKNESS={WALL_TH:.3f}, BACKING='EXPOSED',\n"
             f"      COLOR='SKY BLUE', TRANSPARENCY=0.2 /",
        room_surf="ROOM_CEILING",
        note="setup photo: the inner-room ceiling is a ~4 mm acrylic sheet backed by "
             "stagnant plenum air (a near-insulator with negligible heat capacity), "
             "not a solid 10 mm slab against a fixed-temperature reservoir"),
    "thin-all": dict(   # V3
        matl="&MATL ID='PMMA', CONDUCTIVITY=0.19, SPECIFIC_HEAT=1.47, DENSITY=1180.0, EMISSIVITY=0.90 /\n"
             "    &SURF ID='ROOM_CEILING', MATL_ID='PMMA', THICKNESS=0.004, BACKING='INSULATED',\n"
             "          COLOR='SKY BLUE', TRANSPARENCY=0.2 /",
        surf="&SURF ID='ACRYLIC_WALL', MATL_ID='PMMA', THICKNESS=0.004, BACKING='EXPOSED',\n"
             "      COLOR='SKY BLUE', TRANSPARENCY=0.2 /",
        room_surf="ROOM_CEILING",
        note="the whole rig is thin-sheet acrylic construction (~4 mm), inner ceiling "
             "air-backed, outer box lab-backed -- not 10 mm slabs"),
    "contact": dict(   # V4 -- explicit bracket
        matl="&MATL ID='PMMA', CONDUCTIVITY=0.10, SPECIFIC_HEAT=1.47, DENSITY=1180.0, EMISSIVITY=0.90 /",
        surf=f"&SURF ID='ACRYLIC_WALL', MATL_ID='PMMA', THICKNESS={WALL_TH:.3f}, BACKING='EXPOSED',\n"
             f"      COLOR='SKY BLUE', TRANSPARENCY=0.2 /",
        note="assembled from taped/bracketed acrylic panels, not monolithic -- joint "
             "contact resistance lumped into a reduced effective conductivity (bracket, not measured)"),
}


def snap(v, dx):
    return round(round(v / dx) * dx, 6)


# Nominal fine-core extents (m) -- must contain the candle (x=0.09), the
# back-wall column probes T1/T2/T3 (x=0.12, y=0.15, z up to 0.225) and the full
# plume rise, with room to lean toward the doorway (+x). Snapped to the OUTER
# grid at build time so every core face lands on an outer cell line.
#
# 2-LEVEL nest (core inside outer, 4:1).  A 3-level nest (core<mid<outer) hangs
# /crashes FDS 6.11.1 during read_input on this stack (verified with trivial
# decks 2026-09-03: 2-level embedded runs, 3-level does not). 4:1 is inside
# FDS's supported range (a trivial 4:1 sealed nest steps cleanly); the interface
# sits ~5 cm from the plume in a low-gradient region, so the coarser interface
# ratio is acceptable and is itself part of what P04 quantifies.
#
# Core z-max = 0.24 (not 0.228): the ceiling OBST spans z 0.23-0.24. If the core
# mesh stopped at 0.228 the ceiling OBST would overlap the core's x,y footprint
# while sitting just above its z-max -> FDS 6.11.1 mis-snaps it to a
# zero-thickness OBST on the core -> malloc corruption (isolated 2026-09-03).
# Extending the core to 0.24 puts the whole ceiling OBST inside the core.
CORE_XB_NOMINAL = (0.00, 0.168, 0.102, 0.198, 0.00, 0.240)


def _ijk(xb, dx):
    return (int(round((xb[1]-xb[0])/dx)), int(round((xb[3]-xb[2])/dx)),
            int(round((xb[5]-xb[4])/dx)))


def _prod(t):
    return t[0] * t[1] * t[2]


def _snap_region(nom, grid, x0_ref=0.0):
    """Low bounds DOWN, high bounds UP to `grid` (from x0_ref): the snapped box
    contains the nominal one and every face lands on a grid line."""
    f = [math.floor, math.ceil]
    return tuple(round(x0_ref + f[i & 1](round((nom[i] - x0_ref) / grid, 6)) * grid, 6)
                 for i in range(6))


# --- cluster decomposition: hierarchical cut-planes ----------------------
# One cut-coordinate list per axis per level (m). Cuts are snapped to the OUTER
# grid at build time (_grid_snap); outer_dx = 4*core_dx so every outer line is
# also a core line -> no straddle, every face on the parent grid.
#
# DECOMPOSITION: outer stays ONE mesh; only the core is split (2x1x3 = 6 pieces).
# The 6 core meshes sit entirely inside the single outer mesh -- no embedded-mesh
# interface ever crosses an internal outer-outer boundary. Splitting the OUTER
# too (the old 10-outer/12-core "22-mesh" set) wedged FDS 6.11.1 in init on
# Pleiades: ~6 GB/rank, 7 min, no timestep -- almost certainly the embedded core
# meshes coupling across the internal outer boundaries. 1 outer + 6 core = 7
# ranks, the expensive plume core is cut 6 ways, and the connectivity stays a
# simple star (outer <- each core). Re-test on a debug node before the big slot.
CLUSTER_CUTS = {
    "outer": {"x": [], "y": [], "z": []},                          # outer undivided -> 1 mesh
    "core":  {"x": [], "y": [], "z": [0.036, 0.072, 0.114, 0.156, 0.198]},  # 6 horizontal slabs
}


def _grid_snap(v, g):
    return round(round(v / g) * g, 6)


def _mesh_grid(name, xb, dx, cuts, rank0):
    """Mesh one level on the sub-grid of {its bounds} + {`cuts` strictly inside
    it}. Returns (lines, next_rank)."""
    edges = {}
    for ax, (lo, hi) in zip("xyz", ((xb[0], xb[1]), (xb[2], xb[3]), (xb[4], xb[5]))):
        planes = sorted({lo, hi} | {c for c in cuts[ax] if lo + 1e-9 < c < hi - 1e-9})
        for p in planes:
            n = (p - lo) / dx
            if abs(n - round(n)) > 1e-6:
                raise ValueError(f"{name}: cut {p} = {n:.3f} cells from {lo} (dx={dx}) -- misaligned")
        edges[ax] = planes
    lines, r = [], rank0
    xs, ys, zs = edges["x"], edges["y"], edges["z"]
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            for k in range(len(zs) - 1):
                X0, X1, Y0, Y1, Z0, Z1 = xs[i], xs[i+1], ys[j], ys[j+1], zs[k], zs[k+1]
                lines.append(
                    f"&MESH ID='{name}_{i}{j}{k}', MPI_PROCESS={r}, "
                    f"IJK={round((X1-X0)/dx)},{round((Y1-Y0)/dx)},{round((Z1-Z0)/dx)}, "
                    f"XB={X0:.4f},{X1:.4f},{Y0:.4f},{Y1:.4f},{Z0:.4f},{Z1:.4f} / {name} dx={dx*1000:.2f}mm")
                r += 1
    return lines, r


def _hybrid_core_xb(fine_dx, outer_dx):
    """Core box for the independent-background hybrid (Task 2): snapped to the
    LCM of outer_dx and fine_dx, not outer_dx alone, so the core's own fine_dx
    cells still divide its box evenly (only guaranteed automatically when
    outer_dx is an exact multiple of fine_dx, e.g. the 4:1 nest -- not the case
    here)."""
    o_um, f_um = round(outer_dx * 1e6), round(fine_dx * 1e6)
    lcm = (o_um * f_um // math.gcd(o_um, f_um)) / 1e6
    return _snap_region(CORE_XB_NOMINAL, lcm), lcm


def _nest_geometry(fine_dx, outer_dx=None):
    """(outer_dx, outer_xb, core_xb) for the 2-level nest. outer_dx defaults to
    4*fine_dx (the validated ratio for nest15/nest20); pass an explicit outer_dx
    to decouple background resolution from the core (Task 2 background-variation
    study) -- untested ratio territory, parse-check before trusting. domain
    snapped UP to whole outer cells; core snapped to the outer grid so every
    core face is on an outer cell line."""
    outer_dx = outer_dx or 4 * fine_dx
    x0, z0 = DOMAIN[0], DOMAIN[4]
    outer_xb = (x0,
                x0 + math.ceil(round((DOMAIN[1] - x0) / outer_dx, 6)) * outer_dx,
                DOMAIN[2],
                DOMAIN[2] + math.ceil(round((DOMAIN[3] - DOMAIN[2]) / outer_dx, 6)) * outer_dx,
                z0,
                z0 + math.ceil(round((DOMAIN[5] - z0) / outer_dx, 6)) * outer_dx)
    outer_xb = tuple(round(v, 6) for v in outer_xb)
    core_xb = _snap_region(CORE_XB_NOMINAL, outer_dx)
    return outer_dx, outer_xb, core_xb


# the LAYER HEIGHT / UPPER-LOWER TEMPERATURE device columns (x, y). A uniform-mesh
# split must not put a mesh face on one of these, and must keep the whole z 0-ROOM_Z
# band of each column inside ONE z-slab (integral device -> single mesh only).
LAYER_COLS = ((0.12, 0.15), (0.35, 0.15), (0.66, 0.15))


def _uniform_split(dx, nx, ny, nz):
    """Cut the domain into nx*ny*nz equal boxes (one MPI rank each), guarding the
    layer-device columns. nz in {1,2} only (z1=0.5, band 0-0.23 must stay whole)."""
    x0, x1, y0, y1, z0, z1 = DOMAIN
    I, J, K = _ijk((x0, x1, y0, y1, z0, z1), dx)
    for n, tot, ax in ((nx, I, "I"), (ny, J, "J"), (nz, K, "K")):
        if tot % n:
            raise ValueError(f"split {ax}={n} does not divide {ax}={tot} (dx={dx*1000:.1f} mm)")
    xs = [round(x0 + i * (x1 - x0) / nx, 6) for i in range(nx + 1)]
    ys = [round(y0 + j * (y1 - y0) / ny, 6) for j in range(ny + 1)]
    zs = [round(z0 + k * (z1 - z0) / nz, 6) for k in range(nz + 1)]
    for cx, cy in LAYER_COLS:
        if any(abs(p - cx) < 1.5 * dx for p in xs[1:-1]):
            raise ValueError(f"x-split lands on layer column x={cx}")
        if any(abs(p - cy) < 1.5 * dx for p in ys[1:-1]):
            raise ValueError(f"y-split lands on layer column y={cy}")
    if any(z0 + 1e-6 < p < ROOM_Z - 1e-6 for p in zs[1:-1]):
        raise ValueError("z-split cuts the 0-{:.2f} m layer band (use nz<=2)".format(ROOM_Z))
    lines, r = [], 0
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                ii = int(round((xs[i+1]-xs[i]) / dx))
                jj = int(round((ys[j+1]-ys[j]) / dx))
                kk = int(round((zs[k+1]-zs[k]) / dx))
                lines.append(
                    f"&MESH ID='m{r}', MPI_PROCESS={r}, IJK={ii},{jj},{kk}, "
                    f"XB={xs[i]:.4f},{xs[i+1]:.4f},{ys[j]:.4f},{ys[j+1]:.4f},{zs[k]:.4f},{zs[k+1]:.4f} "
                    f"/ dx={dx*1000:.1f} mm  ({i},{j},{k})")
                r += 1
    lines.append(f"! {r} meshes / MPI ranks  (uniform split {nx}x{ny}x{nz}, {I*J*K/1e6:.2f} M cells)")
    return lines


def _padded_domain(dx):
    """DOMAIN rounded UP to whole dx cells (same convention _nest_geometry uses
    for the outer mesh) -- a no-op when dx already divides DOMAIN exactly (every
    dx used before this), a small extra-air margin when it doesn't (e.g. 7.5mm:
    1.00/0.0075=133.33, needs padding to 134 cells = 1.005 m)."""
    x0, z0 = DOMAIN[0], DOMAIN[4]
    x1 = x0 + math.ceil(round((DOMAIN[1] - x0) / dx, 6)) * dx
    y1 = DOMAIN[2] + math.ceil(round((DOMAIN[3] - DOMAIN[2]) / dx, 6)) * dx
    z1 = z0 + math.ceil(round((DOMAIN[5] - z0) / dx, 6)) * dx
    return (round(x0, 6), round(x1, 6), round(DOMAIN[2], 6), round(y1, 6), round(z0, 6), round(z1, 6))


def _uniform_mult(dx, nx, ny, nz):
    """Uniform full-domain mesh, same guarded split as _uniform_split (layer-
    device columns, ROOM_Z band), but emitted as ONE &MULT-tiled &MESH block
    (the supervisor's FireScope template.fds mechanism) instead of nx*ny*nz
    individually-written &MESH lines. One MULT block = one MPI rank, same as
    _uniform_split; no MPI_PROCESS on the MESH line -- FDS round-robins MULT
    replicas across ranks in creation order, exactly as the template does.
    Domain is padded UP to whole dx cells first (_padded_domain) -- a no-op
    when dx divides DOMAIN exactly."""
    x0, x1, y0, y1, z0, z1 = _padded_domain(dx)
    I, J, K = _ijk((x0, x1, y0, y1, z0, z1), dx)
    for n, tot, ax in ((nx, I, "I"), (ny, J, "J"), (nz, K, "K")):
        if tot % n:
            raise ValueError(f"mult split {ax}={n} does not divide {ax}={tot} (dx={dx*1000:.2f} mm)")
    ti, tj, tk = I // nx, J // ny, K // nz
    tdx, tdy, tdz = ti * dx, tj * dx, tk * dx
    xs = [round(x0 + i * tdx, 6) for i in range(nx + 1)]
    ys = [round(y0 + j * tdy, 6) for j in range(ny + 1)]
    zs = [round(z0 + k * tdz, 6) for k in range(nz + 1)]
    for cx, cy in LAYER_COLS:
        if any(abs(p - cx) < 1.5 * dx for p in xs[1:-1]):
            raise ValueError(f"x-mult-tile lands on layer column x={cx}")
        if any(abs(p - cy) < 1.5 * dx for p in ys[1:-1]):
            raise ValueError(f"y-mult-tile lands on layer column y={cy}")
    if any(z0 + 1e-6 < p < ROOM_Z - 1e-6 for p in zs[1:-1]):
        raise ValueError("z-mult-tile cuts the 0-{:.2f} m layer band".format(ROOM_Z))
    n_blocks = nx * ny * nz
    return [
        f"&MULT ID='m1', DX={tdx:.6f}, DY={tdy:.6f}, DZ={tdz:.6f}, "
        f"I_UPPER={nx-1}, J_UPPER={ny-1}, K_UPPER={nz-1} /",
        f"&MESH IJK={ti},{tj},{tk}, XB={x0:.4f},{x0+tdx:.4f},{y0:.4f},{y0+tdy:.4f},"
        f"{z0:.4f},{z0+tdz:.4f}, MULT_ID='m1' / MULT-tiled dx={dx*1000:.2f}mm, uniform {nx}x{ny}x{nz}",
        f"! {n_blocks} MULT blocks / MPI ranks  ({I*J*K/1e6:.3f} M cells total, "
        f"{(I*J*K)//n_blocks:,} cells/rank)",
    ]


def mesh_block(dx, fine_dx, cluster=False, split_z=1, split_xyz=None, mult_xyz=None,
               outer_dx=None, bg_mult_xyz=None):
    """&MESH line(s): uniform single mesh unless fine_dx is given, else a
    2-level nest core(fine_dx) inside outer(4*fine_dx, or an explicit outer_dx).
    cluster=True splits both levels on the shared hierarchical CLUSTER_CUTS (one
    MPI rank per mesh). bg_mult_xyz=(nx,ny,nz) MULT-tiles the background at
    outer_dx (independent of fine_dx -- Task 2 background-variation study) with
    the fixed nest15-style 6-z-slab core embedded in it; UNTESTED combination
    (MULT auto-ranked meshes + explicit-MPI_PROCESS meshes in one deck) --
    parse-check before trusting. Uniform mesh: mult_xyz=(nx,ny,nz) for a
    &MULT-tiled uniform split (FireScope template.fds mechanism), split_xyz=
    (nx,ny,nz) for the equivalent hand-enumerated &MESH-per-block split, or the
    legacy split_z>1 for equal z-slabs."""
    x0, x1, y0, y1, z0, z1 = DOMAIN
    if not fine_dx:
        I, J, K = _ijk((x0, x1, y0, y1, z0, z1), dx)
        if mult_xyz and tuple(mult_xyz) != (1, 1, 1):
            return _uniform_mult(dx, *mult_xyz)
        if split_xyz and tuple(split_xyz) != (1, 1, 1):
            return _uniform_split(dx, *split_xyz)
        if split_z <= 1:
            return [f"&MESH IJK={I},{J},{K}, XB={x0:.3f},{x1:.3f},{y0:.3f},{y1:.3f},{z0:.3f},{z1:.3f} / whole domain, dx={dx*1000:.1f} mm"]
        return _uniform_split(dx, 1, 1, split_z)

    if bg_mult_xyz:
        # Background and core are on INDEPENDENT grids here (not the 4:1 nest),
        # so the core's outer boundary must land on a line common to BOTH grids
        # -- snap to their LCM, not to outer_dx directly, or the core's own
        # fine_dx cells won't divide its (outer_dx-snapped) box evenly.
        _outer_dx = outer_dx
        core_xb, lcm = _hybrid_core_xb(fine_dx, _outer_dx)
        n_bg = bg_mult_xyz[0] * bg_mult_xyz[1] * bg_mult_xyz[2]
        bg_lines = _uniform_mult(_outer_dx, *bg_mult_xyz)
        # z-cuts are core-internal (core-to-core interfaces only) -- only need
        # to land on the core's OWN fine_dx grid, not the background/LCM grid.
        cuts = {"x": [], "y": [], "z": [_grid_snap(c, fine_dx) for c in CLUSTER_CUTS["core"]["z"]]}
        core_lines, _ = _mesh_grid("core", core_xb, fine_dx, cuts, n_bg)
        n_core = len(core_lines)
        lines = bg_lines + core_lines
        lines.append(f"! background {n_bg} MULT blocks @ {_outer_dx*1000:.2f}mm "
                     f"({bg_mult_xyz[0]}x{bg_mult_xyz[1]}x{bg_mult_xyz[2]}) + "
                     f"core {n_core} @ {fine_dx*1000:.2f}mm (snap grid {lcm*1000:.1f}mm)  "
                     f"({n_bg + n_core} ranks total)")
        return lines

    _outer_dx, dbig, core_xb = _nest_geometry(fine_dx, outer_dx)

    outer_dx = _outer_dx
    if not cluster:
        return [
            f"&MESH ID='outer', MPI_PROCESS=0, IJK={','.join(map(str,_ijk(dbig,outer_dx)))}, "
            f"XB={dbig[0]:.4f},{dbig[1]:.4f},{dbig[2]:.4f},{dbig[3]:.4f},{dbig[4]:.4f},{dbig[5]:.4f} / outer dx={outer_dx*1000:.1f}mm room+plenum",
            f"&MESH ID='core',  MPI_PROCESS=1, IJK={','.join(map(str,_ijk(core_xb,fine_dx)))}, "
            f"XB={core_xb[0]:.4f},{core_xb[1]:.4f},{core_xb[2]:.4f},{core_xb[3]:.4f},{core_xb[4]:.4f},{core_xb[5]:.4f} / core dx={fine_dx*1000:.2f}mm candle+column+plume core",
        ]

    acc = {ax: set() for ax in "xyz"}
    lines, counts = [], {}
    for nm, xb_, d_ in [("outer", dbig, outer_dx), ("core", core_xb, fine_dx)]:
        for ax in "xyz":
            acc[ax] |= {_grid_snap(c, outer_dx) for c in CLUSTER_CUTS[nm][ax]}
        sub, _ = _mesh_grid(nm, xb_, d_, {ax: sorted(acc[ax]) for ax in "xyz"}, len(lines))
        counts[nm] = len(sub)
        lines += sub
    lines = [re.sub(r"MPI_PROCESS=\d+", f"MPI_PROCESS={i}", ln) for i, ln in enumerate(lines)]
    lines.append(f"! {len(lines)} meshes / MPI ranks total  "
                 f"(outer {counts['outer']} @ {outer_dx*1000:.0f}mm + core {counts['core']} @ {fine_dx*1000:.2f}mm)")
    return lines


def deck(dx, fine_dx, t_end, chid, n_candles, cluster=False, discriminate=False, split_z=1,
         hrr_w=HRR_W, rad_fraction=RAD_FRACTION, soot_yield=SOOT_YIELD, dhc=DHC_KJKG,
         tmpa=TMPA, wall="pmma", smoke=True, split_xyz=None, tracer=False, mult_xyz=None,
         dt_restart=None, outer_dx=None, bg_mult_xyz=None):
    x0, x1, y0, y1, z0, z1 = DOMAIN
    near_dx = fine_dx or dx
    Ds = dstar(hrr_w * (1 if n_candles == 1 else n_candles), tmpa)
    cells_across = Ds / near_dx
    if bg_mult_xyz:
        core_xb = _hybrid_core_xb(fine_dx, outer_dx)[0]
    elif fine_dx:
        core_xb = _nest_geometry(fine_dx, outer_dx)[2]
    else:
        core_xb = CORE_XB_NOMINAL
    wp = WALL_PRESETS[wall]
    room_surf = wp.get("room_surf", "ACRYLIC_WALL")   # inner-room ceiling + doorway wall

    # provenance -- every non-baseline knob echoed into the deck header so a swept
    # deck says what it is without cross-referencing the batch script.
    _defaults = dict(hrr_w=HRR_W, rad_fraction=RAD_FRACTION, soot_yield=SOOT_YIELD,
                     dhc=DHC_KJKG, tmpa=TMPA, wall="pmma")
    _now = dict(hrr_w=hrr_w, rad_fraction=rad_fraction, soot_yield=soot_yield,
                dhc=dhc, tmpa=tmpa, wall=wall)
    _swept = {k: v for k, v in _now.items() if v != _defaults[k]}
    prov = ("!  SOURCE/WALL: baseline (CONE_FINDINGS defaults)" if not _swept
            else "!  SOURCE/WALL SWEEP -> " + ", ".join(f"{k}={v}" for k, v in _swept.items()))
    if tracer:
        prov += "\n    !  + PASSIVE TRACER at the candle cup (M2 option a -- transport shape/timing only)"

    # Candle = a FLOOR VENT (z=0) with the measured HRRPUA -- the canonical,
    # robust FDS fire source: a small INERT block (~1 outer cell tall, standing
    # in for the tea-light cup rim) with the burner VENT on its TOP face.
    #  * a burning-OBST-cup (SURF_IDS with HRRPUA) tripped ERROR(607) BURN_AWAY
    #    on the coarse embedded meshes;
    #  * a bare FLOOR vent gets REJECTED where it overlaps the sealed ZMIN wall
    #    ("VENT overlaps VENT ... rejected") -> zero HRR.
    # Raising the burner one outer cell clears both. Cup conduction / wax pool
    # are still not modelled (second-order for the plume).
    odx = 4 * fine_dx if fine_dx else dx
    cw = max(near_dx, snap(CANDLE["cup_d"], near_dx))
    cy0 = snap(CANDLE["y"] - cw / 2, near_dx)
    bh = odx                                   # burner top height = 1 outer cell
    area = cw * cw
    hrrpua = hrr_w / area / 1000.0

    xs = ([CANDLE["x"]] if n_candles == 1
          else [CANDLE["x"] - 0.03, CANDLE["x"] + 0.03, CANDLE["x"] + 0.09][:n_candles])
    # tracer (M2 opt a): the fog enters from the CUP SIDES (SURF_IDS 2 = sides),
    # NOT the burner vent -- MASS_FLUX on a SURF that also carries HRRPUA makes
    # FDS scale the flux off the heat release (parse-check 2026-09-08 saw
    # 1.5e10 kg/s/m2). A standalone non-burning SURF is the clean way.
    cup_surf = "SURF_IDS='INERT','FOG_SRC','INERT'" if tracer else "SURF_ID='INERT'"
    candles = []
    for i, xc in enumerate(xs, 1):
        a0 = snap(xc - cw / 2, near_dx)
        candles.append(
            f"&OBST XB={a0:.4f},{a0+cw:.4f},{cy0:.4f},{cy0+cw:.4f},0.0000,{bh:.4f}, "
            f"{cup_surf}, COLOR='GRAY' / candle {i} cup rim\n"
            f"&VENT XB={a0:.4f},{a0+cw:.4f},{cy0:.4f},{cy0+cw:.4f},{bh:.4f},{bh:.4f}, "
            f"SURF_ID='CANDLE_FLAME', COLOR='RED' / candle {i} burner top ({area*1e4:.1f} cm2, z={bh*1000:.0f} mm)")

    # Room-defining surfaces kept at NOMINAL values (FDS snaps OBST/HOLE faces to
    # the grid itself and reports the actual position; pre-snapping here would
    # drift the room height/length mesh-to-mesh in the P04 study).
    dx0 = DOOR["x"]
    dwall1 = DOOR["x"] + WALL_TH
    dy0, dy1 = DOOR["y0"], DOOR["y1"]
    dh = DOOR["h"]
    rz = ROOM_Z
    rz1 = ROOM_Z + WALL_TH
    rx1 = ROOM_X + WALL_TH

    # PRIMARY probe = gas TEMPERATURE (portable to any FDS >= 6.0; names match
    # the experiment 1:1 for P05 pairing). The modelled-bead THERMOCOUPLE line
    # is emitted commented-out -- the &PROP DIAMETER/EMISSIVITY syntax below is
    # FDS >= ~6.7.4; uncomment both if the target FDS supports it (a bead vs gas
    # difference at T1 is second-order to the plume-vs-flame question -- see the
    # DISCRIMINATION block).
    tc_lines = []
    for name, (px, py, pz) in TCS.items():
        tc_lines.append(f"&DEVC ID='{name}',      XYZ={px:.3f},{py:.3f},{pz:.3f}, QUANTITY='TEMPERATURE' /")
        tc_lines.append(f"! &DEVC ID='{name}_bead', XYZ={px:.3f},{py:.3f},{pz:.3f}, QUANTITY='THERMOCOUPLE', PROP_ID='TCbead' /")

    # T1-discrimination rake (fine runs only): maps the local gas field around
    # T1 so we can tell whether T1 is at the EDGE of a resolved hot plume
    # (hypothesis a -- refine further) or in a broadly cold region because the
    # heat is in a thin flame zone a prescribed-HRR LES can't place (hypothesis b).
    disc_lines = []
    if discriminate:
        for xi in (0.075, 0.090, 0.105, 0.120, 0.135, 0.150):
            for zi in (0.020, 0.035, 0.050, 0.070, 0.100):
                disc_lines.append(
                    f"&DEVC ID='rk_x{int(xi*1000):03d}_z{int(zi*1000):03d}', "
                    f"XYZ={xi:.3f},0.150,{zi:.3f}, QUANTITY='TEMPERATURE' /")
        disc_lines.append("&DEVC ID='Tmax_core', QUANTITY='TEMPERATURE', SPATIAL_STATISTIC='MAX', "
                          f"XB={core_xb[0]:.3f},{core_xb[1]:.3f},{core_xb[2]:.3f},{core_xb[3]:.3f},{core_xb[4]:.3f},{core_xb[5]:.3f} /")
        disc_lines.append("&DEVC ID='Tmax_T1cell', QUANTITY='TEMPERATURE', SPATIAL_STATISTIC='MAX', "
                          "XB=0.09,0.15,0.14,0.16,0.03,0.07 /  ! peak T in the T1 neighbourhood")

    meshes = os.linesep.join(mesh_block(dx, fine_dx, cluster, split_z, split_xyz, mult_xyz,
                                          outer_dx, bg_mult_xyz))
    candle_obst = os.linesep.join(candles)
    tcs = os.linesep.join(tc_lines + ([""] + disc_lines if disc_lines else []))
    disc_slcf = ("&SLCF PBY=0.15, QUANTITY='HRRPUV', CELL_CENTERED=.TRUE. /\n"
                 "    &SLCF PBX=0.12, QUANTITY='TEMPERATURE', CELL_CENTERED=.TRUE. /  ! plane through the column probes"
                 if discriminate else "")

    # --- smoke / layer instrumentation (M2) --------------------------------
    # The experiment's smoke is SEEDED glycerin fog, not candle soot, and its
    # injection rate is unrecorded -- so the transferable comparison is the
    # THERMALLY-defined two-layer interface (LAYER HEIGHT), which needs only the
    # temperature field. Soot/visibility slices are kept for a QUALITATIVE
    # plume-shape / descent comparison against the video.
    if smoke:
        smoke_devc = os.linesep.join(
            f"&DEVC ID='zint_{tag}', QUANTITY='LAYER HEIGHT', XB={sx:.3f},{sx:.3f},0.150,0.150,0.000,{ROOM_Z:.3f} /\n"
            f"&DEVC ID='Tupp_{tag}', QUANTITY='UPPER TEMPERATURE', XB={sx:.3f},{sx:.3f},0.150,0.150,0.000,{ROOM_Z:.3f} /\n"
            f"&DEVC ID='Tlow_{tag}', QUANTITY='LOWER TEMPERATURE', XB={sx:.3f},{sx:.3f},0.150,0.150,0.000,{ROOM_Z:.3f} /"
            for tag, sx in (("fire", 0.12), ("mid", 0.35), ("door", 0.66)))
        smoke_slcf = ("&SLCF PBY=0.15, QUANTITY='MASS FRACTION', SPEC_ID='SOOT', CELL_CENTERED=.TRUE. /\n"
                      "    &SLCF PBY=0.15, QUANTITY='VISIBILITY', CELL_CENTERED=.TRUE. /")
    else:
        smoke_devc = smoke_slcf = ""

    # --- passive tracer released at the candle cup (M2, option a) -------------
    # The experiment's glycerin fog was introduced AT the candle cup and rises
    # with the plume. This models it as a passive, non-buoyant tracer with a tiny
    # mass flux from the burner, ramped in with ignition. The injection RATE is
    # unrecorded, so any tracer comparison is TRANSPORT SHAPE + TIMING ONLY --
    # time-to-fill, accumulation pattern, presence/absence of a sharp interface
    # -- never concentration. zint (thermal) stays a separate reference line.
    tracer_spec = tracer_surf = tracer_devc = tracer_slcf = ""
    if tracer:
        tracer_spec = ("&SPEC ID='TRACER', MASS_FRACTION_0=0.0 /\n"
                       "    &SURF ID='FOG_SRC', SPEC_ID='TRACER', MASS_FLUX=1.0E-5, "
                       f"TAU_MF=-{IGNITION_RAMP_S:.0f}.0, COLOR='GREEN' /  "
                       "! fog enters from the cup sides; MASS_FLUX nominal -- shape/timing only")
        td = ["! passive-tracer transport probes (shape/timing only -- NOT concentration)"]
        for tag, sx in (("fire", 0.12), ("mid", 0.35), ("door", 0.66)):
            for zz in (0.03, 0.08, 0.13, 0.18, 0.22):
                td.append(f"&DEVC ID='tr_{tag}_z{int(zz*100):02d}', QUANTITY='MASS FRACTION', "
                          f"SPEC_ID='TRACER', XYZ={sx:.3f},0.150,{zz:.3f} /")
        for tag, zlo, zhi in (("room", 0.00, ROOM_Z), ("upper", 0.15, ROOM_Z), ("lower", 0.00, 0.10),
                              ("plenum", ROOM_Z, 0.50)):
            td.append(f"&DEVC ID='tr_{tag}mean', QUANTITY='MASS FRACTION', SPEC_ID='TRACER', "
                      f"SPATIAL_STATISTIC='VOLUME MEAN', XB=0.00,0.70,0.00,0.30,{zlo:.3f},{zhi:.3f} /")
        tracer_devc = os.linesep.join(td)
        tracer_slcf = "&SLCF PBY=0.15, QUANTITY='MASS FRACTION', SPEC_ID='TRACER', CELL_CENTERED=.TRUE. /"
    candle_flame_surf = (
        f"&SURF ID='CANDLE_FLAME', HRRPUA={hrrpua:.2f}, TAU_Q=-{IGNITION_RAMP_S:.0f}.0, COLOR='ORANGE' /")

    return textwrap.dedent(f"""\
    &HEAD CHID='{chid}', TITLE='candle compartment -- {n_candles} candle(s), near-fire dx={near_dx*1000:.1f} mm, SEALED box' /
    {prov}

    ! ============================================================
    !  MESH  --  D* = {Ds*100:.2f} cm for a {hrr_w*max(1,n_candles):.0f} W fire
    !  near-fire dx = {near_dx*1000:.1f} mm  ->  D*/dx = {cells_across:.1f}
    !  (FDS convention wants ~10-16; a {hrr_w:.0f} W candle plume is near the
    !   lower edge of FDS's validated envelope -- this is a KNOWN weak point,
    !   quantified by the P04 mesh study, not hidden.)
    ! ============================================================
    {meshes}

    &TIME T_END={t_end:.1f} /
    &MISC TMPA={tmpa:.1f} /           ! exponat R1 pre-ignition TC median ~25 C
    &DUMP DT_DEVC=1.0, DT_HRR=1.0, DT_SLCF=5.0, DT_BNDF=10.0, SIG_FIGS=6{f', DT_RESTART={dt_restart:.0f}' if dt_restart else ''} /

    ! ============================================================
    !  COMBUSTION  --  source term from CONE_FINDINGS.md (NOT calibrated here)
    !  {hrr_w:.0f} W per candle (measured band 16-20 W; total source uncertainty +-15-20%)
    !  paraffin, clean flame (cone soot ~ 0), constant HRR (balance mass-loss
    !  linear to r^2 > 0.999) with a {IGNITION_RAMP_S:.0f} s ignition ramp.
    !  NOTE: fuel composition goes ON THE REAC (FORMULA=). A standalone
    !  &SPEC ID='PARAFFIN' PLUS &REAC FUEL='PARAFFIN' double-declares the species
    !  and corrupts the species setup in FDS 6.11.x (malloc: corrupted top size,
    !  confirmed on Pleiades). FDS defines the fuel species from FORMULA itself.
    ! ============================================================
    &REAC FUEL='PARAFFIN', FORMULA='C25H52', SOOT_YIELD={soot_yield}, CO_YIELD=0.001,
          HEAT_OF_COMBUSTION={dhc:.0f}, RADIATIVE_FRACTION={rad_fraction:.2f} /
    {tracer_spec}

    {candle_flame_surf}
    ! HRRPUA {hrrpua:.2f} kW/m2 x {area*1e4:.2f} cm2 = {area*hrrpua*1000:.1f} W per candle
    ! (target cup area 10.8 cm2 = 37 mm circle; grid-snapped square = {area*1e4:.2f} cm2)

    ! &PROP ID='TCbead', EMISSIVITY={TC_BEAD_EMIS}, DIAMETER={TC_BEAD_D} /  ! for the optional _bead DEVCs; FDS >= ~6.7.4

    ! ============================================================
    !  WALLS  --  {wp['note']}
    !  (the "how much of the late T3 climb is the wall model" axis -- see
    !   VALIDATION_FINDINGS; default 'pmma' is the P03/P04/P05 baseline)
    ! ============================================================
    {wp['matl']}
    {wp['surf']}

    ! ---- SEALED outer box: every domain face is closed acrylic (user correction) ----
    &VENT MB='XMIN', SURF_ID='ACRYLIC_WALL' /
    &VENT MB='XMAX', SURF_ID='ACRYLIC_WALL' /
    &VENT MB='YMIN', SURF_ID='ACRYLIC_WALL' /
    &VENT MB='YMAX', SURF_ID='ACRYLIC_WALL' /
    &VENT MB='ZMIN', SURF_ID='ACRYLIC_WALL' /
    &VENT MB='ZMAX', SURF_ID='ACRYLIC_WALL' /

    ! ============================================================
    !  ROOM  --  0-0.70 x, full depth, 0-0.23 z; 10 mm acrylic walls
    !  (room spans the full box depth, so its side walls ARE the box side walls;
    !   its back wall IS the box XMIN face -- only ceiling + doorway wall are OBSTs)
    ! ============================================================
    &OBST XB=0.000,{rx1:.3f}, {y0:.3f},{y1:.3f}, {rz:.3f},{rz1:.3f}, SURF_ID='{room_surf}', TRANSPARENCY=0.2 / room ceiling
    &OBST XB={dx0:.3f},{dwall1:.3f}, {y0:.3f},{y1:.3f}, 0.000,{rz:.3f}, SURF_ID='{room_surf}', TRANSPARENCY=0.2 / doorway wall
    &HOLE XB={dx0-dx:.3f},{dwall1+dx:.3f}, {dy0:.3f},{dy1:.3f}, -0.001,{dh:.3f} / doorway 0.05 w x 0.15 h, depth-centred

    ! ============================================================
    !  FIRE
    ! ============================================================
    {candle_obst}

    ! ============================================================
    !  DEVICES  --  7 experimental TCs: modelled bead ('T1'..) + gas temp ('T1_gas'..)
    !  Names match the experiment 1:1 for P05 pairing.
    ! ============================================================
    {tcs}
    &DEVC ID='HRR', QUANTITY='HRR', SPATIAL_STATISTIC='VOLUME INTEGRAL', XB={x0:.2f},{x1:.2f},{y0:.2f},{y1:.2f},{z0:.2f},{z1:.2f} /
    &DEVC ID='O2_room', QUANTITY='VOLUME FRACTION', SPEC_ID='OXYGEN', XYZ=0.35,0.15,0.115 /
    &DEVC ID='p_box',  QUANTITY='PRESSURE', XYZ=0.50,0.15,0.40 /

    ! ---- smoke / two-layer structure (M2): thermally-defined interface height +
    !      layer temperatures at 3 x-stations (over fire / mid-room / near door) ----
    {smoke_devc}
    {tracer_devc}

    ! ============================================================
    !  OUTPUT  --  lean: centre-plane temperature + velocity, wall temp
    !  (fine runs add HRRPUV + a plane through the column probes -- see below)
    ! ============================================================
    &SLCF PBY=0.15, QUANTITY='TEMPERATURE', CELL_CENTERED=.TRUE. /
    &SLCF PBY=0.15, QUANTITY='VELOCITY', VECTOR=.TRUE. /
    {smoke_slcf}
    {tracer_slcf}
    {disc_slcf}
    &BNDF QUANTITY='WALL TEMPERATURE' /

    &TAIL /
    """)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dx", type=float, default=0.006, help="domain cell size (m)")
    ap.add_argument("--fine-dx", type=float, default=None, help="nested near-fire cell size (m)")
    ap.add_argument("--t-end", type=float, default=250.0)
    ap.add_argument("--chid", default="candle_medium_dx6")
    ap.add_argument("--n-candles", type=int, default=1)
    ap.add_argument("--cluster", action="store_true",
                    help="split the nest on the shared hierarchical CLUSTER_CUTS "
                         "(~24-30 MPI ranks, one mesh each). Default: 3 meshes "
                         "(outer/mid/core), run -n 3 + heavy OpenMP.")
    ap.add_argument("--discriminate", action="store_true",
                    help="add the T1 plume-vs-flame rake + HRRPUV slice (default on for nested/fine runs)")
    ap.add_argument("--split-z", type=int, default=1,
                    help="uniform mesh only: cut the domain into N equal z-slabs, 1 MPI rank each")
    ap.add_argument("--split", default=None, metavar="NX,NY,NZ",
                    help="uniform mesh only: general MPI split into NX*NY*NZ boxes "
                         "(guards the layer-device columns; NZ<=2). e.g. --split 4,1,2")
    ap.add_argument("--mult", default=None, metavar="NX,NY,NZ",
                    help="uniform mesh only: same split as --split but emitted as ONE "
                         "&MULT-tiled &MESH block (FireScope template.fds mechanism) "
                         "instead of NX*NY*NZ hand-enumerated &MESH lines. e.g. --mult 8,2,4")
    ap.add_argument("--outer-dx", type=float, default=None,
                    help="nested mesh only: explicit background cell size (m), decoupled "
                         "from the default 4*fine_dx ratio (Task 2 background-variation study)")
    ap.add_argument("--bg-mult", default=None, metavar="NX,NY,NZ",
                    help="nested mesh only: MULT-tile the background at --outer-dx (or "
                         "4*fine_dx) into NX*NY*NZ blocks, with the fixed 6-z-slab core "
                         "embedded in it. e.g. --fine-dx 0.0015 --outer-dx 0.0125 --bg-mult 8,2,2")
    ap.add_argument("--dt-restart", type=float, default=None,
                    help="add DT_RESTART=<s> to &DUMP so a wall-clock hit can resume")
    # --- source / wall sweep knobs (M3 uncertainty propagation). Defaults = the
    #     P03/P04/P05 baseline, so omitting them reproduces the baseline deck. ---
    ap.add_argument("--hrr-w", type=float, default=HRR_W,
                    help=f"HRR per candle, W (default {HRR_W:.0f}; source band 15-21)")
    ap.add_argument("--rad-fraction", type=float, default=RAD_FRACTION,
                    help=f"RADIATIVE_FRACTION (default {RAD_FRACTION})")
    ap.add_argument("--soot-yield", type=float, default=SOOT_YIELD,
                    help=f"SOOT_YIELD (default {SOOT_YIELD})")
    ap.add_argument("--dhc", type=float, default=DHC_KJKG,
                    help=f"HEAT_OF_COMBUSTION, kJ/kg (default {DHC_KJKG:.0f})")
    ap.add_argument("--tmpa", type=float, default=TMPA, help=f"ambient T, C (default {TMPA})")
    ap.add_argument("--wall", choices=list(WALL_PRESETS), default="pmma",
                    help="wall model preset (default pmma = baseline)")
    ap.add_argument("--no-smoke", action="store_true",
                    help="omit the LAYER HEIGHT / soot instrumentation (P04-era decks)")
    ap.add_argument("--tracer", action="store_true",
                    help="M2 option (a): passive tracer released at the candle cup + "
                         "transport probes. Comparison is shape/timing only, not concentration.")
    ap.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    disc = a.discriminate or (a.fine_dx is not None)
    sxyz = tuple(int(v) for v in a.split.split(",")) if a.split else None
    mxyz = tuple(int(v) for v in a.mult.split(",")) if a.mult else None
    bgxyz = tuple(int(v) for v in a.bg_mult.split(",")) if a.bg_mult else None
    txt = deck(a.dx, a.fine_dx, a.t_end, a.chid, a.n_candles, a.cluster, disc, a.split_z,
               hrr_w=a.hrr_w, rad_fraction=a.rad_fraction, soot_yield=a.soot_yield,
               dhc=a.dhc, tmpa=a.tmpa, wall=a.wall, smoke=not a.no_smoke, split_xyz=sxyz,
               tracer=a.tracer, mult_xyz=mxyz, dt_restart=a.dt_restart,
               outer_dx=a.outer_dx, bg_mult_xyz=bgxyz)
    path = os.path.join(a.out, f"{a.chid}.fds")
    with open(path, "w") as f:
        f.write(txt)

    near = a.fine_dx or a.dx
    if bgxyz:
        n_bg = bgxyz[0] * bgxyz[1] * bgxyz[2]
        nmesh = n_bg + 6   # fixed 6-z-slab core, see CLUSTER_CUTS["core"]["z"]
        odx = a.outer_dx
        cxb, lcm = _hybrid_core_xb(a.fine_dx, odx)
        nbgc, nc = _prod(_ijk(_padded_domain(odx), odx)), _prod(_ijk(cxb, a.fine_dx))
        cells = (f"background {odx*1000:.2f}mm ~{nbgc/1e6:.2f}M ({n_bg} MULT blocks) + "
                 f"core {a.fine_dx*1000:.1f}mm ~{nc/1e6:.2f}M (6 slabs, snap grid {lcm*1000:.1f}mm) "
                 f"= {(nbgc+nc)/1e6:.2f} M over {nmesh} mesh(es)")
    elif a.fine_dx:
        nmesh = (mxyz[0] * mxyz[1] * mxyz[2]) if mxyz else txt.count("&MESH")
        odx, oxb, cxb = _nest_geometry(a.fine_dx, a.outer_dx)
        no, nc = _prod(_ijk(oxb, odx)), _prod(_ijk(cxb, a.fine_dx))
        cells = (f"outer {odx*1000:.0f}mm ~{no/1e3:.0f}k + core {a.fine_dx*1000:.1f}mm ~{nc/1e6:.2f}M "
                 f"= {(no+nc)/1e6:.2f} M over {nmesh} mesh(es)")
    else:
        nmesh = (mxyz[0] * mxyz[1] * mxyz[2]) if mxyz else txt.count("&MESH")
        cells = f"{_prod(_ijk(DOMAIN, a.dx))/1e6:.2f} M (1 mesh)"
    q = a.hrr_w * max(1, a.n_candles)
    print(f"wrote {path}")
    print(f"  near-fire dx = {near*1000:.1f} mm  |  D* = {dstar(q, a.tmpa)*100:.2f} cm  |  D*/dx = {dstar(q, a.tmpa)/near:.1f}")
    print(f"  {cells}   T_END = {a.t_end:.0f} s")
    sweep = [f"{k}={v}" for k, v in (("hrr_w", a.hrr_w), ("rad_fraction", a.rad_fraction),
             ("soot_yield", a.soot_yield), ("dhc", a.dhc), ("tmpa", a.tmpa), ("wall", a.wall))
             if v != {"hrr_w": HRR_W, "rad_fraction": RAD_FRACTION, "soot_yield": SOOT_YIELD,
                      "dhc": DHC_KJKG, "tmpa": TMPA, "wall": "pmma"}[k]]
    print(f"  source/wall: {'BASELINE' if not sweep else ' '.join(sweep)}"
          f"{'  |  smoke instrumentation OFF' if a.no_smoke else ''}"
          f"{'  |  PASSIVE TRACER (shape/timing only)' if a.tracer else ''}")
    if nmesh > 1:
        print(f"  launch: mpirun -n {nmesh} fds {a.chid}.fds   (one rank per mesh; OMP_STACKSIZE=200M, ulimit -s max)")


if __name__ == "__main__":
    main()
