#!/usr/bin/env bash
set -uo pipefail
W=/scratch/jjyeung/orch_n30/sb_ktchk3/work
export TMPDIR=$W/tmp OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
for step in "run4 tests" "plant4 probes" "run4 a0"; do date -u +%T; unshare -rm bash $W/ns_inner.sh $step; echo "ns $step exit $?"; done
date -u +%T; echo CHAIN_DONE
