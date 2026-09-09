"""check_nesting.py -- verify a nested cluster deck for FDS 6.11.1:

  (a) every mesh face lands on the next-coarser level's cell grid, and
  (b) every finer mesh is fully contained in exactly ONE coarser mesh
      (no fine mesh straddles a coarser-mesh boundary).

Either failure -> `malloc(): corrupted top size` at mesh setup on FDS 6.11.1
(isolated on Pleiades 2026-09-02 / -03). Run before submitting a cluster job:

    python check_nesting.py fds/cluster/candle_fine_nest15_mpi.fds
"""
import re
import sys


def load(path):
    ms = []
    for ln in open(path):
        m = re.search(r"&MESH\b.*?IJK=\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,"
                      r"\s*XB=\s*([-\d.eE,\s]+?)\s*/", ln)
        if not m:
            continue
        idm = re.search(r"ID='([^']+)'", ln)
        name = idm.group(1) if idm else "single"
        ijk = tuple(int(x) for x in m.group(1, 2, 3))
        xb = tuple(float(x) for x in m.group(4).split(","))
        lvl = next((k for k in ("outer", "mid", "core") if name.startswith(k)), "single")
        dx = ((xb[1]-xb[0])/ijk[0], (xb[3]-xb[2])/ijk[1], (xb[5]-xb[4])/ijk[2])
        ms.append(dict(name=name, lvl=lvl, ijk=ijk, xb=xb, dx=dx))
    return ms


def _inside(child, parent, tol=1e-6):
    c, p = child["xb"], parent["xb"]
    return all(p[2*a] - tol <= c[2*a] and c[2*a+1] <= p[2*a+1] + tol for a in range(3))


def _overlaps(a, b, tol=1e-6):
    x, y = a["xb"], b["xb"]
    return all(x[2*i] < y[2*i+1] - tol and y[2*i] < x[2*i+1] - tol for i in range(3))


def main(path):
    ms = load(path)
    levels = {k: [m for m in ms if m["lvl"] == k] for k in ("outer", "mid", "core", "single")}
    print(f"{path}: {len(ms)} &MESH  "
          f"(outer {len(levels['outer'])}, mid {len(levels['mid'])}, core {len(levels['core'])})")
    if not levels["mid"] and not levels["core"]:
        print("  single-level deck -- nothing to check."); return 0

    odx = levels["outer"][0]["dx"][0]
    fdx = levels["core"][0]["dx"][0]
    has_mid = bool(levels["mid"])
    mdx = levels["mid"][0]["dx"][0] if has_mid else None
    if has_mid:
        print(f"  dx: outer {odx*1000:.3f}  mid {mdx*1000:.3f}  core {fdx*1000:.3f} mm "
              f"(ratios {odx/mdx:.2f}, {mdx/fdx:.2f})")
        pairs = (("mid", "outer", odx), ("core", "mid", mdx))
    else:
        print(f"  dx: outer {odx*1000:.3f}  core {fdx*1000:.3f} mm  (ratio {odx/fdx:.2f}, 2-level)")
        pairs = (("core", "outer", odx),)

    problems = []

    # cell size uniform & exactly the target
    for m in ms:
        want = {"outer": odx, "mid": mdx, "core": fdx, "single": m["dx"][0]}[m["lvl"]]
        if want is None or max(abs(d - want) for d in m["dx"]) > 1e-6:
            problems.append(f"{m['name']}: non-uniform/off cells {tuple(round(d*1e3,4) for d in m['dx'])} mm")

    # (a) face alignment + (b) single-parent containment
    for childlvl, parentlvl, pdx in pairs:
        for c in levels[childlvl]:
            for v, ax in zip(c["xb"], "xxyyzz"):
                if abs(v / pdx - round(v / pdx)) > 1e-6:
                    problems.append(f"{c['name']}: face {v:.4f} not on {pdx*1e3:.1f} mm {parentlvl} grid")
            parents = [p for p in levels[parentlvl] if _overlaps(c, p)]
            containing = [p for p in parents if _inside(c, p)]
            if len(containing) != 1:
                problems.append(
                    f"{c['name']} XB={tuple(round(x,3) for x in c['xb'])}: "
                    f"overlaps {len(parents)} {parentlvl} mesh(es), contained in {len(containing)} "
                    f"-- must be exactly 1 (STRADDLE)")

    if problems:
        print(f"  ✗ {len(problems)} PROBLEM(S):")
        for p in problems[:40]:
            print("     " + p)
        return 1
    print("  ✓ all cells exact dx; every child face on the parent grid; "
          "every child mesh in exactly one parent. OK for FDS 6.11.1.")
    return 0


if __name__ == "__main__":
    sys.exit(sum(main(p) for p in sys.argv[1:]) if len(sys.argv) > 1
             else (print(__doc__) or 2))
