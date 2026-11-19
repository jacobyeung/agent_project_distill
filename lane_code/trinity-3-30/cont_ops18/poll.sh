#!/bin/bash
# print events newer than marker, chain status, last autosub log lines
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops; L=/scratch/jjyeung/orch_n30/cont_ops18; W=/scratch/jjyeung/orch_n30/cont_ops/work
test -f $L/.mark || touch -d '2026-11-19 04:01' $L/.mark
date -u +%TZ; find $E -maxdepth 1 -newer $L/.mark -type f ! -name STATUS.md -printf '%f\n'; ls $L/inbox; touch $L/.mark
tmux has-session -t chain400 2>/dev/null && echo chain400 alive || echo chain400 GONE; tmux ls 2>/dev/null | grep mon400
for k in h1read7 h1face7 h1vsti7; do for f in $W/$k/autosub400_*.log; do test -f $f && echo "$k: $(tail -1 $f | cut -c1-200)"; done; done
df -h /scratch | awk 'NR==2{print "free",$4}'; cut -d' ' -f1-3 /proc/loadavg
