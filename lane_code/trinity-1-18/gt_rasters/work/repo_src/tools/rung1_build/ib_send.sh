#!/bin/bash
# Send a local directory from this node to trinity-0-13 over InfiniBand with one short ssh that obeys the shared Trinity
# rate limiter (same lock, stamp and log as lanes/tools/trinity_ssh.sh: one call per rolling 60 s per host), opens no
# ControlMaster (the coordinator forbids persistent sessions to Trinity nodes) and checks the host key recorded for
# trinity-0-13: tar cf - -C SRC_PARENT NAME | ssh trinity-0-13.ib "tar xf - -C DEST_PARENT".
# usage: ib_send.sh SRC_DIR DEST_PARENT
set -euo pipefail
src=$1 dest=$2
LOCK=/tmp/jjyeung_trinity_ssh.lock
STAMP=/tmp/jjyeung_trinity_ssh.last
LOG=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/tools/trinity_ssh.log
exec 9>>"$LOCK"
flock 9
last=$(cat "$STAMP" 2>/dev/null || echo 0)
now=$(date +%s)
wait=$(( last + 60 - now ))
if [ "$wait" -gt 0 ]; then sleep "$wait"; fi
date +%s > "$STAMP"
printf '%s %s %s\n' "$(TZ=America/Los_Angeles date '+%F %T')" "trinity-0-13.ib" "rung1_build_ib_send" >> "$LOG" 2>/dev/null || true
flock -u 9
tar chf - -C "$(dirname "$src")" "$(basename "$src")" | \
  timeout 300 ssh -o ConnectTimeout=10 -o BatchMode=yes -o ControlMaster=no -o HostKeyAlias=trinity-0-13 \
    trinity-0-13.ib "mkdir -p $dest && tar xf - -C $dest && echo IB_RECEIVED"
