#!/bin/bash
# poll confirmation verdict N1C and build 10; returns early on verdict (unless W/work/.vn1c_seen), build 10 meta.json (unless W/work/.b10_seen) or a new ORCH file
W=/scratch/jjyeung/orch_n30/tree_rebuild_w; R10=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261118T000253Z_tree_rebuild10
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events
V=$E/tree_rebuild/REVIEW_VERDICT_TREE_N1C.md
end=$((SECONDS+${1:-570}))
while [ $SECONDS -lt $end ]; do
 [ -f $V ] && [ ! -f $W/work/.vn1c_seen ] && break
 [ -f $R10/meta.json ] && [ ! -f $W/work/.b10_seen ] && break
 [ -n "$(find $E/tree_rebuild $E/review_treen1 -maxdepth 1 -name '*_ORCH_*' -newer $W/work/.orch_seen 2>/dev/null)" ] && break
 sleep 30; done
echo "$(date -u +%H:%MZ) N1C: $([ -f $V ] && echo VERDICT || echo none) rev:$(pgrep -f 'review_treen1c.md' >/dev/null && echo alive || echo GONE) | b10: $(ls $R10 | tr '\n' ' ')$(pgrep -f 'label tree_rebuild10' >/dev/null && echo alive || echo GONE) | new ORCH: $(find $E/tree_rebuild -maxdepth 1 -name '*_ORCH_*' -newer $W/work/.orch_seen -type f | xargs -r -n1 basename | tr '\n' ' ')"
grep -v "^$" $W/w10/work/build10/STATUS.md 2>/dev/null | tail -2 | cut -c1-300
ls -t $E/review_treen1/ 2>/dev/null | head -2
