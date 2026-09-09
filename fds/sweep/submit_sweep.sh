#!/bin/bash -l
# Submit the M2/M3 sweep on Pleiades, in the re-sequenced priority order.
# Adjust ACCOUNT / PART / TIME to your allocation (as in candle_fine.batch).
#
#   scp fds/sweep/*.fds fds/sweep/submit_sweep.sh  cobra:/beegfs/lachgar/candle_fds/sweep/
#   ssh cobra ; cd /beegfs/lachgar/candle_fds/sweep
#   module --force purge && module load FDS/6.11.1
#
#   # ---- PARSE CHECK FIRST (new namelists: LAYER HEIGHT, UPPER/LOWER TEMPERATURE,
#   #      SOOT VOLUME FRACTION, VISIBILITY; and the 2-way z-split). 1 min each: ----
#   export OMP_STACKSIZE=200M OMP_NUM_THREADS=4
#   mpiexec -n 7 fds m2_base_nest20_450.fds   # PASS: "Number of MPI Processes: 7",
#   mpiexec -n 2 fds s5_wallins.fds           #   no ERROR, reaches "Time Step 1"
#   mpiexec -n 2 fds s6_walladi.fds           #   within ~1-2 min -> Ctrl-C, submit.
#   mpiexec -n 8 fds s7_tracer.fds            #   new: &SPEC ID='TRACER' + a standalone non-burning
#   #                                             &SURF ID='FOG_SRC' (MASS_FLUX=1e-5) on the cup SIDES
#   #                                             (NOT the burner -- MASS_FLUX on a HRRPUA SURF gets
#   #                                             scaled off the heat release), MASS FRACTION SPEC_ID=
#   #                                             'TRACER' DEVCs/SLCF. transport shape/timing only.
#   # If a smoke DEVC errors ("must be within a single mesh" / unknown QUANTITY):
#   #   regenerate that deck with --no-smoke and rely on m2_base for layer height.
#
#   bash submit_sweep.sh 1     # priority 1+2 only (T3 decomposition, needs nothing from anyone)
#   bash submit_sweep.sh 2     # the rest (HRR / radiative-fraction bands) -- after P1/P2 land
set -e
ACCOUNT=cobra ; PART=normal ; TIME=24:00:00
STAGE=${1:-all}

submit () {  # $1 deck (no .fds)   $2 ntasks   $3 time
  sbatch --job-name="cs_$1" --account=$ACCOUNT --partition=$PART \
         --nodes=1 --ntasks=$2 --cpus-per-task=4 --time=${3:-$TIME} \
         --output="stdout.%j" --error="stderr.%j" \
         --wrap="module --force purge; module load FDS/6.11.1; \
                 export OMP_NUM_THREADS=4 OMP_STACKSIZE=200M; mpiexec fds $1.fds"
}

if [ "$STAGE" = "1" ] || [ "$STAGE" = "all" ]; then
  submit m2_base_nest20_450 7 48:00:00     # PRIORITY 1 -- 2 mm to 450 s (wall-heating regime)
  submit s5_wallins        2 24:00:00      # PRIORITY 2 -- insulated walls
  submit s6_walladi        2 24:00:00      # PRIORITY 2 -- adiabatic walls
fi
if [ "$STAGE" = "2" ] || [ "$STAGE" = "all" ]; then
  submit s0_base_dx5 2 ; submit s1_hrr15 2 ; submit s2_hrr21 2     # HRR band
  submit s3_rad20 2   ; submit s4_rad35 2                          # radiative-fraction band
  submit s7_tracer 2                                              # M2 (a) fog-analogue tracer (same 4x1x2 deck as s0-s4)
fi
squeue --me
