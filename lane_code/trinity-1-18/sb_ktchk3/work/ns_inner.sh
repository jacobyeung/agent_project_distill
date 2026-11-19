#!/usr/bin/env bash
# Usage: ns_inner.sh <copy> <step>; binds work/<copy> over the kit path inside this private mount namespace.
set -uo pipefail
W=/scratch/jjyeung/orch_n30/sb_ktchk3/work
K=/scratch/jjyeung/orch_n30/sb_ktfix2
mount --bind $W/$1 $K
cd $K
echo "ROOT_VIEW $1: $(ls $K | tr '\n' ' ')"
case "$2" in
 tests) bash scripts/cpu.sh code/test_kit.py > $W/tests_rerun.log 2>&1; echo "tests exit $?";;
 probes)
  bash scripts/cpu.sh $W/plant.py > $W/plant.log 2>&1; echo "plant exit $?"; date -u +%T
  PLANT_OUT=$W/plant2_results.json bash scripts/cpu.sh $W/plant2.py > $W/plant2.log 2>&1; echo "plant2 exit $?"; date -u +%T
  bash scripts/cpu.sh $W/extra_pass.py > $W/extra_pass.log 2>&1; echo "extra exit $?";;
 extra) bash scripts/cpu.sh $W/extra_pass.py > $W/extra_pass.log 2>&1; echo "extra exit $?";;
 a0) bash scripts/cpu.sh work/a0_rerun.py > $W/a0_rerun.log 2>&1; echo "a0 exit $?";;
esac
