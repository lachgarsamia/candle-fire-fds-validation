"""Shared setup for the analysis scripts: headless matplotlib, FireScope on the
path, and the canonical repository paths (all derived from the repo root so the
scripts run from anywhere)."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLBACKEND", "Agg")

# FireScope plotting/IO helpers (timeseries.write_series_csv, etc.).
# Override with FIRESCOPE_SRC=/path/to/FireScope/src if it lives elsewhere.
FIRESCOPE_SRC = os.environ.get("FIRESCOPE_SRC", "/Users/samialachgar/Desktop/FireScope/src")
if os.path.isdir(FIRESCOPE_SRC) and FIRESCOPE_SRC not in sys.path:
    sys.path.insert(0, FIRESCOPE_SRC)

import matplotlib
matplotlib.use("Agg")

# --- repository layout -------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))          # src/
ROOT = os.path.dirname(HERE)                               # repo root

DATA_RAW = os.path.join(ROOT, "data", "raw")
CONE_DIR = os.path.join(DATA_RAW, "cone")
COMPARTMENT_DIR = os.path.join(DATA_RAW, "compartment")
RESULT_DIR = os.path.join(ROOT, "data", "processed")
FIG_DIR = os.path.join(ROOT, "figures")
FDS_RUNS = os.path.join(ROOT, "fds", "runs")

# back-compat alias (older scripts referred to DATA_DIR for the cone files)
DATA_DIR = CONE_DIR

os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)
