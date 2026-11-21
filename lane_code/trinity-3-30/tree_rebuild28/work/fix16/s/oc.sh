#!/bin/bash
# One Orchard call: oc.sh <script> <outfile>. Waits until 125 s have passed since the end of my previous call.
set -u
F=/scratch/jjyeung/orch_n30/tree_rebuild28/work/fix16
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
last=$(cat "$F/s/.last" 2>/dev/null || echo 0); now=$(date +%s); w=$(( last + 125 - now ))
(( w > 0 )) && sleep "$w"
echo "$(date -u +%FT%TZ) start $1" >> "$F/s/calls.log"
timeout 300 bash "$B/tools/ossh.sh" 'bash -s' < "$1" > "$2" 2>&1; rc=$?
date +%s > "$F/s/.last"
echo "$(date -u +%FT%TZ) end $1 rc=$rc bytes=$(stat -c %s "$2")" >> "$F/s/calls.log"
echo "rc=$rc bytes=$(stat -c %s "$2")"
