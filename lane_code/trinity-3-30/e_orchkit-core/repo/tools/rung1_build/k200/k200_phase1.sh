#!/bin/bash
# Phase 1 (after inodes free): queue the K200 frozen-dir action (the closure install is already pending), run one poll,
# print the install and K200 results.
R=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/rung1_build_20261027
PY=/home/jjyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/bin/python3.12
D=/scratch/jjyeung/rung1_push/k200
cd $R/tools || exit 1
$PY -B r1actions.py sh k200_make $D/k200_make.sh >/dev/null
for t in 1 2 3; do timeout 600 env R1_MIN_INTERVAL=55 $PY -B r1aws.py run 2>&1 | tail -1 | cut -c1-100; ls $R/actions/sent | grep -q "_k200_make.json" && break; sleep 60; done
f=$(grep -l "_k200_make BEGIN" $(ls -t $R/polls/poll_*.txt | head -3) | head -1)
grep -h "CLOSURE_INSTALLED\|CLOSURE_PRESENT\|^K200\|Error\|error" $f | cut -c1-200
