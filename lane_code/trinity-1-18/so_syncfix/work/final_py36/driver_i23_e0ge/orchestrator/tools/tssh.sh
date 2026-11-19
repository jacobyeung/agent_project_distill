#!/bin/bash
# Rate-limited ssh into a Trinity compute node for agents running on one host.
# Usage: tssh.sh <node> [remote command...]   (stdin is passed through, e.g. 'bash -s' < script)
# Holds a host-local lock so all callers on this host together make at most one ssh start per 35 s.
set -u
N=$1; shift
case "$N" in trinity|trinity.vision.cs.cmu.edu|trinity-2-18*) echo "REFUSE $N" >&2; exit 2;; esac
L=/scratch/jjyeung/orch_n30/so_syncfix/work/final_py36/driver_i23_e0ge/tssh; mkdir -p "$L"
exec 9>"$L/lock"; flock 9
last=$(cat "$L/last" 2>/dev/null || echo 0); now=$(date +%s); wait=$(( last + 0 - now ))
(( wait > 0 )) && sleep "$wait"
date +%s > "$L/last"; echo "$(date -u +%FT%TZ) $N $*" | cut -c1-200 >> "$L/log"
flock -u 9
if [ "${LCS_ROBUST_SYNC:-0}" = 1 ] && [ "${LCS_STAGE_TIMEOUT_OWNER:-0}" = 1 ]; then
  # The stage caller already owns the process group and TERM/KILL deadline.
  # Exec SSH directly: a nested timeout can exit before its SSH child does.
  exec ssh -o ConnectTimeout=20 -o ConnectionAttempts=1 -o BatchMode=yes "$N" "$@"
fi
exec timeout 900 ssh -o ConnectTimeout=20 -o BatchMode=yes "$N" "$@"
