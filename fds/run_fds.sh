#!/bin/bash
# run_fds.sh <deck.fds> [threads]
#
# FDS 6.11.1 on this Mac (11 cores: 5 P + 6 E, 19 GB):
#  * plain `fds` is single-threaded; `fds_openmp` + OMP_NUM_THREADS gives ~3x.
#  * meshes >= 5 mm SIGSEGV in init_mp_initialize with the default 8 MB stack;
#    OMP_STACKSIZE=200M + `ulimit -s 65520` (the hard max here) fixes it.
#  * a deck with >1 &MESH is run with the bundled mpirun, one rank per mesh;
#    the bundled Open MPI needs OPAL_PREFIX + DYLD_LIBRARY_PATH set explicitly
#    (FDS6VARS.sh is a bash script and breaks under zsh).
set -e
DECK="$1"; THREADS="${2:-5}"
DIR="$(cd "$(dirname "$DECK")" && pwd)"; BASE="$(basename "$DECK")"
cd "$DIR"
ulimit -s 65520 2>/dev/null || true
export OMP_STACKSIZE=200M
export OPAL_PREFIX=/Applications/FDS/FDS6/bin/openmpi
export DYLD_LIBRARY_PATH=/Applications/FDS/FDS6/bin/openmpi/lib:${DYLD_LIBRARY_PATH}
# bundled Open MPI 5.0.10 aborts in read_input's Allreduce under the default
# btl auto-select on this Mac; forcing self,vader (shared memory) fixes it.
export OMPI_MCA_btl=self,vader
export OMPI_MCA_rmaps_base_oversubscribe=1

NMESH=$(grep -c '^&MESH\|^ *&MESH' "$BASE" || true)
if [ "${NMESH:-1}" -gt 1 ]; then
  export OMP_NUM_THREADS=$(( THREADS < NMESH ? 1 : THREADS / NMESH ))
  echo "multi-mesh ($NMESH): mpirun -n $NMESH  x  OMP_NUM_THREADS=$OMP_NUM_THREADS"
  exec /Applications/FDS/FDS6/bin/openmpi/bin/mpirun -n "$NMESH" \
       /Applications/FDS/FDS6/bin/fds "$BASE"
else
  export OMP_NUM_THREADS="$THREADS"
  echo "single mesh: fds_openmp  OMP_NUM_THREADS=$THREADS  OMP_STACKSIZE=$OMP_STACKSIZE"
  exec /Applications/FDS/FDS6/bin/fds_openmp "$BASE"
fi
