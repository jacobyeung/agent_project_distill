#!/bin/bash
# usage: chk.sh ; prints watcher state + new events since last run
W=/scratch/jjyeung/orch_n30; B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; L=$W/n_ops4
date -u +%H:%M:%SZ
tmux has-session -t nops_mon 2>/dev/null || echo "WATCHER DEAD"
for m in $W/n_ops1/work/mon $W/n_ops2/work/mon2; do echo "== $(basename $m) job=$(cat $m/job)"; tail -1 $m/last.line | cut -c1-700; [ $m/ALERTS.txt -nt $L/work/chk.since ] && echo "NEW ALERTS" && tail -2 $m/ALERTS.txt | cut -c1-500; done
for d in n_ops tree_rebuild n_review; do find $B/events/$d -maxdepth 1 -newer $L/work/chk.since -name '2026*' -printf "$d/%f\n"; done
find $L/inbox -newer $L/work/chk.since -type f -printf "INBOX %f\n"
touch $L/work/chk.since
