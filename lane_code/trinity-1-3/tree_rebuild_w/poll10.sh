#!/bin/bash
# poll verdicts N1C and TREE10; returns early on a new verdict (unless W/work/.vn1c_seen / .v10_seen) or new ORCH file
W=/scratch/jjyeung/orch_n30/tree_rebuild_w; E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events
V1=$E/tree_rebuild/REVIEW_VERDICT_TREE_N1C.md; V2=$E/tree_rebuild/REVIEW_VERDICT_TREE10.md
end=$((SECONDS+${1:-570}))
while [ $SECONDS -lt $end ]; do
 [ -f $V1 ] && [ ! -f $W/work/.vn1c_seen ] && break
 [ -f $V2 ] && [ ! -f $W/work/.v10_seen ] && break
 [ -n "$(find $E/tree_rebuild -maxdepth 1 -name '*_ORCH_*' -newer $W/work/.orch_seen 2>/dev/null)" ] && break
 sleep 30; done
echo "$(date -u +%H:%MZ) N1C: $([ -f $V1 ] && echo VERDICT || echo none) $(pgrep -f 'review_treen1c.md' >/dev/null && echo alive || echo GONE) | T10: $([ -f $V2 ] && echo VERDICT || echo none) $(pgrep -f 'briefs/review_tree10.md' >/dev/null && echo alive || echo GONE) | new ORCH: $(find $E/tree_rebuild -maxdepth 1 -name '*_ORCH_*' -newer $W/work/.orch_seen -type f | xargs -r -n1 basename | tr '\n' ' ')"
for l in review_treen1 review_tree10; do echo "$l: $(grep -v '^$' /scratch/jjyeung/orch_n30/$l/STATUS.md 2>/dev/null | tail -1 | cut -c1-200)"; done
