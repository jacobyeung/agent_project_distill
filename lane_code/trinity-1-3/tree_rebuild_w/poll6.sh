#!/bin/bash
# poll build n1 (package suite) and build 9fix (Codex, workspace W/w9f); returns early when either meta.json appears (unseen) or an ORCH file is newer than W/work/.orch_seen
W=/scratch/jjyeung/orch_n30/tree_rebuild_w; RC=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs
R1=$RC/20261117T151717Z_tree_rebuild_n1; R9=$RC/20261117T214715Z_tree_rebuild9fix
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/tree_rebuild
end=$((SECONDS+${1:-570}))
while [ $SECONDS -lt $end ]; do
 [ -f $R1/meta.json ] && [ ! -f $W/work/.n1_seen ] && break
 [ -f $R9/meta.json ] && [ ! -f $W/work/.b9f_seen ] && break
 [ -n "$(find $E -maxdepth 1 -name '*_ORCH_*' -newer $W/work/.orch_seen 2>/dev/null)" ] && break
 sleep 30; done
echo "$(date -u +%H:%MZ) n1: $(ls $R1 | tr '\n' ' ')$(pgrep -f 'label tree_rebuild_n1 ' >/dev/null && echo alive || echo GONE) legacy=$(cut -c1-30 $W/work/build_n1/proofs/suite_tree/legacy/progress.json 2>/dev/null) | 9f: $(ls $R9 | tr '\n' ' ')$(pgrep -f 'label tree_rebuild9fix' >/dev/null && echo alive || echo GONE) tlog=$(stat -c %s $R9/transcript.log 2>/dev/null) | new: $(find $E -maxdepth 1 -newer $W/work/.orch_seen -type f | xargs -r -n1 basename | tr '\n' ' ')"
grep -v "^$" $W/w9f/work/build9fix/STATUS.md 2>/dev/null | tail -3 | cut -c1-300
