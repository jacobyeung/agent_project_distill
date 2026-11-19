#!/usr/bin/env bash
set -uo pipefail
W=/scratch/jjyeung/orch_n30/sb_ktchk2/work
K=/scratch/jjyeung/orch_n30/sb_ktfix2
mount --bind $W/plant3 $K
cd $K
date -u +%T; bash scripts/cpu.sh $W/plant2.py > $W/plant2.log 2>&1; echo "plant2 exit $?"
date -u +%T
