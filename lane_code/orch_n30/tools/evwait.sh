#!/usr/bin/env bash
# Orchestrator watcher. Exits at once on a new lane QUESTION or BLOCKER or on a new INBOX_TO_DISTILL_ORCH file;
# exits on new RESULT events once the first of them is 5 minutes old (batching); exits after <seconds> (default 900).
# It opens no ssh connection.
R=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918; B=$R/orch_n30; SEEN=$B/tools/seen.txt; PLOG=$B/tools/probe_2_28.log
touch "$SEEN" "$PLOG"
END=$(( $(date +%s) + ${1:-900} )); T0=0
flush() { echo NEW:; echo "$1"; echo "$1" >> "$SEEN"; exit 0; }
while [[ $(date +%s) -lt $END ]]; do
  new=$( { ls -1d $B/events/*/*_RESULT_* $B/events/*/*_QUESTION_* $B/events/*/*_BLOCKER_* 2>/dev/null; ls -1d $R/INBOX_TO_DISTILL_ORCH_* 2>/dev/null; } | grep -v -x -F -f "$SEEN")
  if [[ -n "$new" ]]; then
    if echo "$new" | grep -q -E '_QUESTION_|_BLOCKER_|INBOX_TO_DISTILL_ORCH_'; then flush "$new"; fi
    (( T0 == 0 )) && T0=$(date +%s)
    (( $(date +%s) - T0 >= 300 )) && flush "$new"
  fi
  sleep 30
done
if [[ -n "${new:-}" ]]; then flush "$new"; fi
echo "TICK $(date -u +%FT%TZ), no new event"
