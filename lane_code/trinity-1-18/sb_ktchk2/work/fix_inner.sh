#!/usr/bin/env bash
set -uo pipefail
W=/scratch/jjyeung/orch_n30/sb_ktchk2/work
K=/scratch/jjyeung/orch_n30/sb_ktfix2
mount --bind $W/fixtry $K
cd $K
date -u +%T; bash scripts/cpu.sh code/test_kit.py > $W/fixtry_tests.log 2>&1; echo "fixtry tests exit $?"
date -u +%T; PLANT_OUT=$W/fixtry_plant_results.json bash scripts/cpu.sh $W/plant2.py > $W/fixtry_plant.log 2>&1; echo "fixtry plant exit $?"
date -u +%T
