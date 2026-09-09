"""Quick P04 mesh-ladder read: T1/T2/T3/T5 + the T1 rake, coarse->fine, vs R1."""
import csv, glob, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

RUNS = [
    ("coarse 10mm", "coarse/candle_coarse_dx10_devc.csv",  "coarse/candle_coarse_dx10_hrr.csv"),
    ("medium  5mm", "medium/candle_medium_dx5_devc.csv",   "medium/candle_medium_dx5_hrr.csv"),
    ("nest20  2mm", "nest20/candle_fine_nest20_mpi_devc.csv", "nest20/candle_fine_nest20_mpi_hrr.csv"),
    ("nest15 1.5mm","nest15/candle_fine_nest15_mpi_devc.csv","nest15/candle_fine_nest15_mpi_hrr.csv"),
]

# EXPONAT R1, ignition-aligned, absolute degC (EXPONAT_FINDINGS.md)
EXP = {"T1": 136.0, "T2": 51.0, "T3": 64.0, "T5": 29.0, "T9": 25.0, "T10": 27.0, "T11": 30.0}
TMPA = 25.0

def load(path):
    with open(os.path.join(HERE, path)) as f:
        rows = list(csv.reader(f))
    hdr = [h.strip() for h in rows[1]]
    data = np.array([[float(x) for x in r] for r in rows[2:] if r and r[0].strip()])
    return hdr, data

def col(hdr, data, name):
    return data[:, hdr.index(name)]

def tail_mean(t, y, frac=0.15):
    n = max(3, int(len(y) * frac))
    return float(np.mean(y[-n:])), float(np.std(y[-n:]))

print(f"{'run':13s} {'t_end':>6s}  " + "  ".join(f"{k:>13s}" for k in ["T1","T2","T3","T5"]) + f"  {'HRR_kW':>8s}")
print("-" * 90)
print(f"{'EXPERIMENT R1':13s} {'~430':>6s}  " +
      "  ".join(f"{EXP[k]:8.1f}     " for k in ["T1","T2","T3","T5"]))
print("-" * 90)

ladder = {}
for name, dpath, hpath in RUNS:
    try:
        hdr, d = load(dpath)
    except FileNotFoundError:
        print(f"{name:13s}  (no file)"); continue
    t = d[:, 0]
    vals = {}
    for k in ["T1", "T2", "T3", "T5"]:
        m, s = tail_mean(t, col(hdr, d, k))
        vals[k] = m
    hrr = "?"
    try:
        hh, hd = load(hpath)
        hrr = f"{tail_mean(hd[:,0], hd[:,1])[0]:.4f}"
    except Exception:
        pass
    ladder[name] = (t[-1], vals)
    print(f"{name:13s} {t[-1]:6.1f}  " +
          "  ".join(f"{vals[k]:8.1f} ({vals[k]-TMPA:+5.1f})" for k in ["T1","T2","T3","T5"]) +
          f"  {hrr:>8s}")

# --- T1 rake (fine runs): where is the hot gas? ---
print("\nT1-neighbourhood rake  (degC, tail mean) -- columns = x, rows = z")
for name, dpath, _ in RUNS[2:]:
    try:
        hdr, d = load(dpath)
    except FileNotFoundError:
        continue
    t = d[:, 0]
    print(f"\n  {name}   (t_end={t[-1]:.0f} s)   [candle x=0.09, T1 x=0.12 z=0.05]")
    xs = ["075", "090", "105", "120", "135", "150"]
    zs = ["020", "035", "050", "070", "100"]
    print("        x=" + "  ".join(f"{'.'+x:>7s}" for x in xs))
    for z in zs:
        row = []
        for x in xs:
            nm = f"rk_x{x}_z{z}"
            if nm in hdr:
                m, _ = tail_mean(t, col(hdr, d, nm))
                row.append(f"{m:7.1f}")
            else:
                row.append("   --  ")
        print(f"  z=.{z}  " + "  ".join(row))
    for extra in ["Tmax_core", "Tmax_T1cell"]:
        if extra in hdr:
            m, s = tail_mean(t, col(hdr, d, extra))
            print(f"  {extra:12s} {m:7.1f}  (+/- {s:.0f})")
