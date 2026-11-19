#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
bash $P/poll118u.sh
L=/scratch/jjyeung/orch_n30/so_launch/out; echo "=== launch REPORT"; head -c 1500 $L/REPORT.md; echo; echo "=== NOTE"; head -c 3500 $L/NOTE_FOR_TREE_REBUILD.md; echo; sha256sum $L/patches/*.diff | cut -c1-100
