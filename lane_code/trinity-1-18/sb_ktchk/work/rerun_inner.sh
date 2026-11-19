#!/usr/bin/env bash
set -uo pipefail
W=/scratch/jjyeung/orch_n30/sb_ktchk/work
K=/scratch/jjyeung/orch_n30/sb_ktfix2
mount --bind $W/run $K
cd $K
echo "ROOT_VIEW $(ls $K | tr '\n' ' ')"
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
date -u +%FT%TZ; bash scripts/cpu.sh code/test_kit.py > $W/tests_rerun.log 2>&1; echo "tests exit $?"
date -u +%FT%TZ; bash scripts/cpu.sh code/dryrun.py > $W/dryrun_rerun.log 2>&1; echo "dryrun exit $?"
date -u +%FT%TZ; bash scripts/cpu.sh work/a0_rerun.py > $W/a0_rerun.log 2>&1; echo "a0 exit $?"
date -u +%FT%TZ
