#!/bin/bash
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; M=/scratch/jjyeung/orch_n30/n_ops1/work/mon
while [ ! -f /scratch/jjyeung/orch_n30/n_ops5/work/dflog.stop ]; do
  l=$(tail -1 $M/last.line); t=${l%% *}; g=$(echo "$l" | sed -n 's/.*"proj_free_G":\([0-9]*\).*/\1/p')
  echo "$(date -u +%H:%M:%SZ) watcher_read=$t free_GiB=$g" >> $B/events/n_ops/PROJECT_FS_FREE.txt
  sleep 300; done
