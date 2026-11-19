#!/bin/bash
# r1_ops9: one 10-minute tick: local job summary (w.sh waits up to 9 min), new ORCH events, inbox, watcher states
cd /scratch/jjyeung/orch_n30/r1_ops6; E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events
bash work/r7/waitev.sh ${2:-9} >/dev/null 2>&1; bash work/r8/c1.sh
since=${1:-20261119T1100Z}
ls $E/r1_ops/ $E/tree_rebuild/ $E/cont_ops/ 2>/dev/null | grep '_ORCH_' | awk -v s=$since '$0>=s' | sort -u
ls inbox/ 2>/dev/null | tail -2
echo "m600: $(cat work/r7/m600/exq.last 2>/dev/null | head -2 | tr '\n' ' ' | cut -c1-200) | pbw: $(cat work/r9/pbw.last 2>/dev/null | cut -c1-120) $(ls work/r9/ | grep -E 'pbw\.(alarm|final)')"
tmux ls 2>/dev/null | grep -oE '^(r1mon6|r7node|r7m600|r9pbw)' | tr '\n' ' '; echo
