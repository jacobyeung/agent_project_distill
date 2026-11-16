#!/bin/bash
W=/scratch/jjyeung/orch_n30/tree_rebuild_w; R=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261116T103023Z_tree_rebuild6
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/tree_rebuild
sleep ${1:-540}
echo "$(date -u +%H:%MZ) $(ls $R | tr '\n' ' ') $(kill -0 3303455 2>/dev/null && echo alive || echo GONE)"
cd $W && /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/build6/progress_final.py 2>&1 | cut -c1-140
tail -c 200 $W/work/build6/STATUS.md | tail -2
ls -t $E | grep ORCH | head -1; ls $W/inbox | tr '\n' ' '
