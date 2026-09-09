"""fog_digitize.py -- extract the glycerin-fog layer signal from the compartment
video for the M2 comparison.

Framing (LOCKED, see M2_M3_PLAN §P4): the fog is a SEEDED passive tracer, not
candle soot. This script measures LAYER DYNAMICS ONLY -- the height of the
fog/clear boundary and the fill timescale -- never concentration.

Two products per clip:
  data/processed/fog_layer_<clip>.csv     interface height z(t) at x = 0.12 / 0.35 / 0.66
                                   + room-mean obscuration, ignition-aligned
  figures/fog_<clip>_montage.png   frames with the detected interface drawn

STEP 0 -- calibration. The pixel<->metre map below is a FIRST GUESS from
media/frames/3276_calib_guides.png. Run  `python fog_digitize.py --calib 3276`
to dump a frame with the physical grid drawn on it, eyeball it, and adjust CALIB.
Anchors: inner-room floor z=0, ceiling underside z=0.23 m (ROOM_Z); candle at
x=0.09 m; left inner wall = doorway = x=0.70 m (VERIFY -- there may be a plenum
gap). x increases RIGHT->LEFT in the image (candle/back-wall on the right).
"""
from __future__ import annotations
import argparse
import csv
import os
import numpy as np
import imageio
import _repro  # noqa: F401
from PIL import Image, ImageDraw

SRC = "/Volumes/room_corner/Samia"
ROOM_Z = 0.23
FDS_X = {"fire": 0.12, "mid": 0.35, "door": 0.66}

# clip -> dict(tign, and pixel anchors on the 1920x1080 frame)
CALIB = {
    "3276": dict(tign=120.0,
                 px_x0=1630, px_x070=570,      # image-x of physical x=0 and x=0.70
                 py_z0=880,  py_zTop=490,      # image-y of z=0 (floor) and z=ROOM_Z (ceiling underside)
                 lights="on"),
    "3278": dict(tign=30.0,
                 px_x0=1600, px_x070=560,
                 py_z0=915,  py_zTop=505,
                 lights="off"),
    "3277": dict(tign=None, px_x0=1620, px_x070=570, py_z0=890, py_zTop=495, lights="on"),
}


def phys_to_px(clip, x_phys, z_phys):
    c = CALIB[clip]
    px = c["px_x0"] + (x_phys / 0.70) * (c["px_x070"] - c["px_x0"])
    py = c["py_z0"] + (z_phys / ROOM_Z) * (c["py_zTop"] - c["py_z0"])
    return int(round(px)), int(round(py))


def calib_frame(clip):
    c = CALIB[clip]
    vt = (c["tign"] or 30) - 20
    rd = imageio.get_reader(f"{SRC}/7L5A{clip}.MP4", "ffmpeg",
                            input_params=["-ss", str(max(vt, 1))], output_params=["-frames:v", "1"])
    fr = rd.get_next_data(); rd.close()
    im = Image.fromarray(fr); d = ImageDraw.Draw(im)
    for xf in (0.0, 0.12, 0.35, 0.66, 0.70):
        p0 = phys_to_px(clip, xf, 0.0); p1 = phys_to_px(clip, xf, ROOM_Z)
        d.line([p0, p1], fill=(255, 60, 60), width=2)
        d.text((p0[0] + 3, p0[1] + 4), f"x={xf}", fill=(255, 200, 0))
    for zf in (0.0, 0.115, ROOM_Z):
        a = phys_to_px(clip, 0.0, zf); b = phys_to_px(clip, 0.70, zf)
        d.line([a, b], fill=(0, 220, 255), width=2)
        d.text((b[0] - 60, b[1] - 14), f"z={zf}", fill=(0, 220, 255))
    out = f"{_repro.FIG_DIR}/fog_{clip}_calibcheck.png"
    im.resize((1400, 788)).save(out)
    print(f"wrote {out} -- eyeball the grid vs the inner room, adjust CALIB[{clip!r}]")


def interface_z(col_green, zaxis, base, thresh_frac=0.35):
    """col_green: green intensity along a vertical line, index 0 = ceiling.
    Fog scatters the laser -> brighter. Interface = highest z where the running
    signal first exceeds base + thresh_frac*(peak-base). Returns z (m) or nan."""
    s = col_green.astype(float)
    rng = np.nanmax(s) - base
    if rng < 8:                       # no meaningful fog on this line
        return np.nan
    thr = base + thresh_frac * rng
    above = s > thr
    # from the ceiling (top) down, first sustained run of 'above'
    for i in range(len(above) - 3):
        if above[i] and above[i + 1] and above[i + 2]:
            return float(zaxis[i])
    return np.nan


def digitize(clip, fps=1.0, t0=-20.0, t1=None):
    c = CALIB[clip]
    if c["tign"] is None:
        raise SystemExit(f"CALIB[{clip!r}]['tign'] not set -- find ignition first")
    tign = c["tign"]
    # vertical sample lines (physical), 60 points ceiling->floor
    z_axis = np.linspace(ROOM_Z - 0.005, 0.01, 60)
    cols_px = {k: [phys_to_px(clip, xv, zz) for zz in z_axis] for k, xv in FDS_X.items()}
    x0px, _ = phys_to_px(clip, 0.02, 0.0); x1px, _ = phys_to_px(clip, 0.68, 0.0)
    ztop_y = phys_to_px(clip, 0.35, ROOM_Z - 0.01)[1]
    zbot_y = phys_to_px(clip, 0.35, 0.02)[1]
    xlo, xhi = sorted((x0px, x1px))

    rd = imageio.get_reader(f"{SRC}/7L5A{clip}.MP4", "ffmpeg", fps=fps)
    rows, montage = [], []
    base = {k: None for k in FDS_X}
    for i, fr in enumerate(rd):
        vt = i / fps
        at = vt - tign
        if at < t0:
            continue
        if t1 and at > t1:
            break
        G = fr[..., 1].astype(float)
        rec = {"t": at}
        for k, pts in cols_px.items():
            line = np.array([G[min(py, G.shape[0]-1), min(px, G.shape[1]-1)] for px, py in pts])
            if at < -3:
                base[k] = line.mean() if base[k] is None else 0.7*base[k] + 0.3*line.mean()
            b = base[k] if base[k] is not None else line.min()
            rec[f"zint_{k}"] = interface_z(line, z_axis, b)
        room = G[ztop_y:zbot_y, xlo:xhi]
        rec["room_mean_G"] = float(room.mean())
        rows.append(rec)
        if abs((at % 15)) < (1.0/fps)/2 or at in (0,):
            im = Image.fromarray(fr); d = ImageDraw.Draw(im)
            for k, pts in cols_px.items():
                zi = rec[f"zint_{k}"]
                if not np.isnan(zi):
                    p = phys_to_px(clip, FDS_X[k], zi)
                    d.line([(p[0]-40, p[1]), (p[0]+40, p[1])], fill=(255, 80, 0), width=3)
                for px, py in pts[::6]:
                    d.point((px, py))
            d.text((20, 20), f"t_ign {at:+.0f}s", fill=(255, 220, 0))
            montage.append(im.resize((760, 428)))
    rd.close()

    cp = f"{_repro.RESULT_DIR}/fog_layer_{clip}.csv"
    with open(cp, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["t_from_ignition_s", "zint_fire_m", "zint_mid_m",
                                       "zint_door_m", "room_mean_green"])
        for r in rows:
            w.writerow([f"{r['t']:.1f}"] + [f"{r.get(k, float('nan')):.3f}" for k in
                       ("zint_fire", "zint_mid", "zint_door")] + [f"{r['room_mean_G']:.1f}"])
    if montage:
        cols = 4; rw = -(-len(montage) // cols)
        sheet = Image.new("RGB", (cols*760, rw*428))
        for j, im in enumerate(montage):
            sheet.paste(im, ((j % cols)*760, (j // cols)*428))
        mp = f"{_repro.FIG_DIR}/fog_{clip}_montage.png"; sheet.save(mp, quality=84)
        print(f"wrote {mp}")
    print(f"wrote {cp}  ({len(rows)} rows)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--calib", metavar="CLIP", help="dump a calibration-grid frame and exit")
    ap.add_argument("--clip", default="3278")
    ap.add_argument("--fps", type=float, default=1.0)
    ap.add_argument("--t1", type=float, default=None, help="stop at this t_from_ignition (s)")
    a = ap.parse_args()
    if a.calib:
        calib_frame(a.calib)
    else:
        digitize(a.clip, fps=a.fps, t1=a.t1)
