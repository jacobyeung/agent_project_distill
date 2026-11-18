#!/bin/bash
# poll combined review review_treen1 and build 10; returns early on verdict (unless W/work/.vn1_seen), build 10 meta.json (unless W/work/.b10_seen) or a new ORCH file (newer than W/work/.orch_seen)
W=/scratch/jjyeung/orch_n30/tree_rebuild_w; R10=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261118T000253Z_tree_rebuild10
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events
end=$((SECONDS+${1:-570}))
while [ $SECONDS -lt $end ]; do
 [ -f $E/tree_rebuild/REVIEW_VERDICT_TREE_N1.md ] && [ ! -f $W/work/.vn1_seen ] && break
 [ -f $R10/meta.json ] && [ ! -f $W/work/.b10_seen ] && break
 [ -n "$(find $E/tree_rebuild -maxdepth 1 -name '*_ORCH_*' -newer $W/work/.orch_seen 2>/dev/null)" ] && break
 sleep 30; done
echo "$(date -u +%H:%MZ) rev: $(pgrep -f 'prompt-file .*review_treen1' >/dev/null && echo alive || echo GONE) verdict=$(ls $E/tree_rebuild/REVIEW_VERDICT_TREE_N1.md 2>/dev/null | wc -l) res=$(ls $E/review_treen1 2>/dev/null | tr '\n' ' ') | b10: $(ls $R10 | tr '\n' ' ')$(pgrep -f 'label tree_rebuild10' >/dev/null && echo alive || echo GONE) | new: $(find $E/tree_rebuild -maxdepth 1 -newer $W/work/.orch_seen -type f | xargs -r -n1 basename | tr '\n' ' ')"
grep -v "^$" $W/w10/work/build10/STATUS.md 2>/dev/null | tail -2 | cut -c1-300
