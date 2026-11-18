#!/bin/bash
W=/scratch/jjyeung/orch_n30/tree_rebuild_w; E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events
RB=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261118T060440Z_tree_rebuild12; V=$E/tree_rebuild/REVIEW_VERDICT_TREE12C.md
end=$((SECONDS+${1:-570}))
while [ $SECONDS -lt $end ]; do
 [ -f $RB/meta.json ] && [ ! -f $W/work/.b12_seen ] && break
 [ -f $V ] && [ ! -f $W/work/.v12c_seen ] && break
 [ -n "$(find $E/tree_rebuild -maxdepth 1 -name '*_ORCH_*' -newer $W/work/.orch_seen 2>/dev/null)" ] && break
 sleep 30; done
echo "$(date -u +%H:%MZ) b12: $(ls $RB | tr '\n' ' ')$(pgrep -f 'label tree_rebuild12' >/dev/null && echo alive || echo GONE) | T12C: $([ -f $V ] && echo VERDICT || echo none) $(pgrep -f 'review_tree12c.md' >/dev/null && echo alive || echo GONE) | new ORCH: $(find $E/tree_rebuild -maxdepth 1 -name '*_ORCH_*' -newer $W/work/.orch_seen -type f | xargs -r -n1 basename | tr '\n' ' ')"
grep -v "^$" $W/w12/work/build12/STATUS.md 2>/dev/null | tail -1 | cut -c1-200
