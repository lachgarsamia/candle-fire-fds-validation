"""figstyle.py -- one visual identity for every report figure.
Import and call `apply()`; use the named colours."""
import matplotlib as mpl

# palette (matches the earlier p05 / m3 figures)
INK    = "#211c17"   # near-black text / axes
EMBER  = "#bf3d10"   # the fire / primary model line
COOL   = "#2f5766"   # measurement / experiment
GOLD   = "#e0a53b"   # secondary model line
PLUM   = "#7a1f6b"   # tertiary / bracket
GREY   = "#9c9c9c"   # collapsed / null case
PAPER  = "#faf8f4"   # panel background tint (use sparingly)

# verdict colours -- used in the schematic and anywhere zones are named
V_FAR    = "#2f7d4f"   # far-field validated       (green)
V_WALL   = "#c98b3a"   # T3 wall-model limit       (amber)
V_STRUCT = "#a1352b"   # T1/T2 structural limit    (red)

TC_ROLE = {"T1": V_STRUCT, "T2": V_STRUCT, "T3": V_WALL, "T5": V_FAR,
           "T9": V_FAR, "T10": V_FAR, "T11": V_FAR}


def apply():
    mpl.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "axes.titlecolor": INK,
        "axes.linewidth": 0.9,
        "axes.grid": True,
        "grid.color": "#d9d4cc",
        "grid.linewidth": 0.6,
        "grid.alpha": 0.7,
        "text.color": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "legend.frameon": False,
        "legend.fontsize": 8.5,
        "figure.dpi": 140,
        "savefig.dpi": 140,
        "savefig.bbox": "tight",
    })
