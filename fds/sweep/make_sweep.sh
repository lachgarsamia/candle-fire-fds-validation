#!/bin/bash -l
# M2/M3 sweep decks.  Run:  cd fds/sweep && bash make_sweep.sh
#
# Trend runs: 5 mm uniform, split 4x1x2 = 8 MPI ranks (~150 k cells each).
#   * z-split at 0.25 keeps the LAYER HEIGHT / UPPER-LOWER TEMPERATURE columns
#     (integral devices, z 0-0.23) whole in the lower slab.
#   * x-split at 0.25/0.50/0.75 clears the three device columns (x=0.12/0.35/0.66).
#   The generator (_uniform_split) guards both; a bad --split raises.
#   2-rank (--split-z 2) was ~1.9 s/step on 8 cores -> ~26 h to 450 s; the 8-rank
#   split gets real MPI scaling. Submit with --ntasks=8.
#
# T_END = 350 s: reaches the experiment's broad-peak / wall-heating regime
# (~300-450 s) with margin under a 24 h slot at the 8-rank rate.
set -e
cd "$(dirname "$0")"
M=../make_fds.py
T=350
S="--dx 0.005 --split 4,1,2 --t-end $T --out ."

python $M $S --chid s0_base_dx5                        # 5 mm reference for the deltas
python $M $S --chid s1_hrr15   --hrr-w 15              # cone source band, low
python $M $S --chid s2_hrr21   --hrr-w 21              # cone source band, high
python $M $S --chid s3_rad20   --rad-fraction 0.20     # radiative fraction spread
python $M $S --chid s4_rad35   --rad-fraction 0.35
python $M $S --chid s5_wallins --wall pmma-insulated   # T3 late-climb: no loss to lab
python $M $S --chid s6_walladi --wall inert            # T3 late-climb: no wall thermal mass
python $M $S --chid s7_tracer  --tracer                # M2 (a): passive fog-analogue tracer at the cup
                                                      # -- transport SHAPE + TIMING vs the video only, never concentration

# 2 mm nest baseline to 450 s -- M2 smoke run + the clean T3 resolution-vs-wall
# and 150-vs-450 s decomposition.  PRIORITY 1.  (already RUNNING as job 21899510;
# regenerate only if you need to resubmit -- hand-add DT_RESTART=7200 to &DUMP.)
python $M --dx 0.008 --fine-dx 0.002 --cluster --t-end 450 --chid m2_base_nest20_450 --out .

echo; echo "decks in $(pwd):"; ls -1 *.fds
