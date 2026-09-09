"""Shared setup for the analysis scripts: headless matplotlib + FireScope on path."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLBACKEND", "Agg")

FIRESCOPE_SRC = "/Users/samialachgar/Desktop/FireScope/src"
if FIRESCOPE_SRC not in sys.path:
    sys.path.insert(0, FIRESCOPE_SRC)

import matplotlib
matplotlib.use("Agg")

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = HERE
FIG_DIR = os.path.join(HERE, "figures")
RESULT_DIR = os.path.join(HERE, "results")
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)
