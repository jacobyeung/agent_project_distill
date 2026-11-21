#!/bin/bash
# n_ops10 periodic check: watch health + new inbox/events since last call
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; O=/scratch/jjyeung/orch_n30; S=$O/n_ops10/work/chk.since
[[ -e $S ]] || touch -d '2026-11-21 06:10 UTC' $S
date -u +%FT%TZ
sed -n 3,6p $B/events/n_ops/N_WATCH_STATUS.md | cut -c1-400
echo "hk.log $(stat -c %s $O/n_ops1/work/mon/hk.log) B; HOSTKEY_ALERT $(ls $O/n_ops8/work/HOSTKEY_ALERT 2>/dev/null || echo none); job $(cat $O/n_ops1/work/mon/job) sleep $(cat $O/n_ops1/work/mon/sleep)"
tail -3 $B/events/n_ops/N_WATCH_ALERTS.txt 2>/dev/null | cut -c1-300
echo "--- new files:"
find $O/n_ops10/inbox $O/n_ops9/inbox $B/events/n_ops $B/events/tree_rebuild $B/events/n_review -maxdepth 1 -type f -newer $S ! -name 'N_WATCH_*' ! -name PROJECT_FS_FREE.txt 2>/dev/null
ls /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918 | grep -E '^INBOX_(TO_DISTILL|FROM_NONTRAIN)' | sort | tail -1
touch $S
