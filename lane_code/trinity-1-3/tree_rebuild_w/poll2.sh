#!/bin/bash
W=/scratch/jjyeung/orch_n30/tree_rebuild_w; R=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261116T231636Z_tree_rebuild7
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/tree_rebuild
sleep ${1:-540}
echo "$(date -u +%H:%MZ) $(ls $R | tr '\n' ' ') $(kill -0 841040 2>/dev/null && echo alive || echo GONE)"
grep -v "^$" $W/work/build7/STATUS.md | tail -2 | cut -c1-200
ls -l --time-style=+%H:%M $R/transcript.log | cut -d" " -f5-6
ls -t $E | grep ORCH | head -1; ls $W/inbox | tr '\n' ' '
