#!/bin/bash
sleep ${1:-0}
cd /scratch/jjyeung/orch_n30/cont_ops/work/h1orch; date -u +%TZ
grep -v '^1706' m5.out | grep -E 'RUNNING|PENDING|COMPLETED|FAILED|CANCEL' | tail -1 | cut -c1-260
grep -E '^== (err|metrics)' -A3 m5.out | cut -c1-400 | head -8
grep -E 'gcs_|H1_STOP' m5.out | tail -1
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops; ls -t $E | grep -E '_ORCH_' | head -1; ls /scratch/jjyeung/orch_n30/cont_ops/inbox
ls -t /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918 | grep INBOX_TO_DISTILL | head -1
tmux ls 2>/dev/null | grep -c cont10_watch
