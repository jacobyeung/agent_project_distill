#!/bin/bash
# Start only on trinity-3-30, in tmux, with LCS_ENABLE_SYNC_HEALTH=1.
# Ordinary check errors are logged; a signal exit stops for owner investigation.
set -euo pipefail
[ "${LCS_ENABLE_SYNC_HEALTH:-0}" = 1 ] || { echo 'REFUSED: set LCS_ENABLE_SYNC_HEALTH=1' >&2; exit 2; }
[ "$(hostname -s)" = trinity-3-30 ] || { echo 'REFUSED: health loop runs only on trinity-3-30' >&2; exit 2; }
while true; do
    if bash "$(dirname -- "$0")/sync_health.sh" >> "${LCS_S:-/scratch/jjyeung/distill_sync}/health.log" 2>&1; then
        :
    else
        rc=$?
        echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) health check failed exit=$rc" >> "${LCS_S:-/scratch/jjyeung/distill_sync}/health.log"
        # Cluster rules forbid rerunning a killed process without the user's answer.
        [ "$rc" -lt 128 ] || exit "$rc"
    fi
    sleep 600
done
