#!/bin/bash
# poll build n1 (Codex) and reviewer review_tree9; returns early when n1's meta.json or the verdict appears
W=/scratch/jjyeung/orch_n30/tree_rebuild_w; R=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261117T151717Z_tree_rebuild_n1
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events
end=$((SECONDS+${1:-570}))
while [ $SECONDS -lt $end ]; do [ -f $R/meta.json ] && break; [ -f $E/tree_rebuild/REVIEW_VERDICT_TREE9.md ] && [ ! -f $W/work/.verdict9_seen ] && break; sleep 30; done
echo "$(date -u +%H:%MZ) n1: $(ls $R | tr '\n' ' ') $(pgrep -f 'label tree_rebuild_n1' >/dev/null && echo alive || echo GONE) tlog=$(stat -c %s $R/transcript.log 2>/dev/null) | rev9: $(pgrep -f 'prompt-file .*review_tree9' >/dev/null && echo alive || echo GONE) verdict=$(ls $E/tree_rebuild/REVIEW_VERDICT_TREE9.md 2>/dev/null | wc -l) res=$(ls $E/review_tree9 2>/dev/null | tr '\n' ' ') | orch=$(ls -t $E/tree_rebuild | grep ORCH | head -1) inbox=$(ls $W/inbox | wc -l)"
grep -v "^$" $W/work/build_n1/STATUS.md 2>/dev/null | tail -2 | cut -c1-300
