#!/bin/bash
# At most one Orchard call a minute from this subagent: serialize on a lock, wait until 62 s have
# passed since the last call started, then run the script given on stdin through the shared connection.
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
L=/scratch/jjyeung/orch_n30/tree_rebuild27/work/fix6/rd/.oq
mkdir -p "$L"
exec 9>"$L/lock"
flock 9
last=$(cat "$L/last" 2>/dev/null || echo 0)
now=$(date +%s)
w=$(( last + 62 - now ))
if (( w > 0 )); then sleep "$w"; fi
date +%s > "$L/last"
timeout 300 bash "$B/tools/ossh.sh" 'bash -s'
