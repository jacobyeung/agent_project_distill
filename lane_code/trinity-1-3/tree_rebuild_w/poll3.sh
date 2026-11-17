#!/bin/bash
W=/scratch/jjyeung/orch_n30/tree_rebuild_w; R=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261116T231636Z_tree_rebuild7
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/tree_rebuild
end=$((SECONDS+${1:-570}))
while [ $SECONDS -lt $end ]; do [ -f $R/meta.json ] && break; sleep 30; done
echo "$(date -u +%H:%MZ) $(ls $R | tr '\n' ' ') $(kill -0 841040 2>/dev/null && echo alive || echo GONE) tlog=$(stat -c %s $R/transcript.log) orch=$(ls -t $E | grep ORCH | head -1) inbox=$(ls $W/inbox | wc -l)"
tail -c 20000 $R/transcript.log | grep -o '"CPU-reachable unresolved": [0-9]*' | tail -1
