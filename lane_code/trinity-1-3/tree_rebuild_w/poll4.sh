#!/bin/bash
W=/scratch/jjyeung/orch_n30/tree_rebuild_w; R=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261117T114352Z_tree_rebuild9
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/tree_rebuild
end=$((SECONDS+${1:-570}))
while [ $SECONDS -lt $end ]; do [ -f $R/meta.json ] && break; sleep 30; done
echo "$(date -u +%H:%MZ) $(ls $R | tr '\n' ' ') $(kill -0 4079963 2>/dev/null && echo alive || echo GONE) tlog=$(stat -c %s $R/transcript.log) orch=$(ls -t $E | grep ORCH | head -1) inbox=$(ls $W/inbox | wc -l)"
tail -c 20000 $R/transcript.log | grep -o '"CPU-reachable unresolved": [0-9]*' | tail -1
grep -v "^$" $W/work/build9/STATUS.md 2>/dev/null | tail -1 | cut -c1-200
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B $W/work/build9/monitor_status.py 2>&1 | cut -c1-400
