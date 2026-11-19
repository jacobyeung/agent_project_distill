#!/bin/bash
# n_ops2 tick: wait $1 s (default 540), then print watcher state, new alerts, new events since stamp file
L=/scratch/jjyeung/orch_n30/n_ops1; L2=/scratch/jjyeung/orch_n30/n_ops2; E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events
sleep ${1:-540}; date -u +%T
tail -1 $L/work/mon/hist.txt | cut -c1-700
since=$(cat $L2/work/tick.since 2>/dev/null || echo 20261119T2041Z)
for d in n_ops tree_rebuild n_review cont_ops; do ls $E/$d 2>/dev/null | grep -E '^2026' | awk -v s=$since -v d=$d '$0>s{print d"/"$0}'; done | tail -15
ls -t $L2/inbox $L/inbox | head -6; tail -3 $L/work/mon/ALERTS.txt 2>/dev/null | cut -c1-300
tmux has-session -t nops_mon || echo WATCHER_DEAD
date -u +%Y%m%dT%H%MZ > $L2/work/tick.since
