#!/bin/bash
W=/scratch/jjyeung/orch_n30/tree_rebuild_w; E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events
R3=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261118T045631Z_tree_rebuild_n1fix3; V=$E/tree_rebuild/REVIEW_VERDICT_TREE11.md
end=$((SECONDS+${1:-570}))
while [ $SECONDS -lt $end ]; do
 [ -f $R3/meta.json ] && [ ! -f $W/work/.n1f3_seen ] && break
 [ -f $V ] && [ ! -f $W/work/.v11_seen ] && break
 [ -n "$(find $E/tree_rebuild -maxdepth 1 -name '*_ORCH_*' -newer $W/work/.orch_seen 2>/dev/null)" ] && break
 sleep 30; done
echo "$(date -u +%H:%MZ) n1f3: $(ls $R3 | tr '\n' ' ')$(pgrep -f 'label tree_rebuild_n1fix3' >/dev/null && echo alive || echo GONE) | T11: $([ -f $V ] && echo VERDICT || echo none) $(pgrep -f 'briefs/review_tree11.md' >/dev/null && echo alive || echo GONE) | new ORCH: $(find $E/tree_rebuild -maxdepth 1 -name '*_ORCH_*' -newer $W/work/.orch_seen -type f | xargs -r -n1 basename | tr '\n' ' ')"
grep -v "^$" $W/wn3/work/n1fix3/STATUS.md 2>/dev/null | tail -1 | cut -c1-200
