#!/bin/bash
# n_ops1 tick: wait $1 s (default 540), then print watcher state, new alerts, new events since stamp file
L=/scratch/jjyeung/orch_n30/n_ops1; E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events
sleep ${1:-540}; date -u +%T
tail -1 $L/work/mon/hist.txt | cut -c1-500
since=$(cat $L/work/tick.since 2>/dev/null || echo 20261119T1755Z)
ls $E/n_ops $E/tree_rebuild $E/cont_ops 2>/dev/null | grep -E '^2026' | awk -v s=$since '$0>s' | sort -u | tail -12
ls -t $L/inbox | head -3; tail -2 $L/work/mon/ALERTS.txt 2>/dev/null | cut -c1-300
date -u +%Y%m%dT%H%MZ > $L/work/tick.since
