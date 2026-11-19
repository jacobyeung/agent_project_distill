#!/bin/bash
# Start only on trinity-3-30, in tmux, with LCS_ENABLE_SYNC_HEALTH=1.
# A failed/killed monitor stops this loop; the owner investigates before restarting.
set -euo pipefail
[ "${LCS_ENABLE_SYNC_HEALTH:-0}" = 1 ] || { echo 'REFUSED: set LCS_ENABLE_SYNC_HEALTH=1' >&2; exit 2; }
[ "$(hostname -s)" = trinity-3-30 ] || { echo 'REFUSED: health loop runs only on trinity-3-30' >&2; exit 2; }
while true; do
    bash "$(dirname -- "$0")/sync_health.sh" >> "${LCS_S:-/scratch/jjyeung/distill_sync}/health.log" 2>&1
    sleep 600
done
