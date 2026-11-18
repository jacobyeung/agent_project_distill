#!/bin/bash
W=/scratch/jjyeung/orch_n30/tree_rebuild_w; E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events
V1=$E/tree_rebuild/REVIEW_VERDICT_TREE11.md; V2=$E/tree_rebuild/REVIEW_VERDICT_TREE_N1C3.md
end=$((SECONDS+${1:-570}))
while [ $SECONDS -lt $end ]; do
 [ -f $V1 ] && [ ! -f $W/work/.v11_seen ] && break
 [ -f $V2 ] && [ ! -f $W/work/.vn1c3_seen ] && break
 [ -n "$(find $E/tree_rebuild -maxdepth 1 -name '*_ORCH_*' -newer $W/work/.orch_seen 2>/dev/null)" ] && break
 sleep 30; done
echo "$(date -u +%H:%MZ) T11: $([ -f $V1 ] && echo VERDICT || echo none) $(pgrep -f 'briefs/review_tree11.md' >/dev/null && echo alive || echo GONE) | N1C3: $([ -f $V2 ] && echo VERDICT || echo none) $(pgrep -f 'review_treen1c3.md' >/dev/null && echo alive || echo GONE) | new ORCH: $(find $E/tree_rebuild -maxdepth 1 -name '*_ORCH_*' -newer $W/work/.orch_seen -type f | xargs -r -n1 basename | tr '\n' ' ')"
