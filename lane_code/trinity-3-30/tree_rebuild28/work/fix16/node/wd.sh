#!/bin/bash
# fix16: at the given UTC time today (HH:MM:SS), stop walk w1 with stop.sh. Runs in its own srun --overlap step.
set -u
export TZ=UTC
D=/tmp/a15_f16_174198
T=$(date -u -d "today ${1:?}" +%s); N=$(date +%s)
echo "$(date -u +%FT%TZ) watchdog pid $$: stop of w1 at $1 UTC, in $((T-N)) s" >> $D/w1/log/stop.log
if (( T > N )); then sleep $(( T - N )); fi
bash $D/n/stop.sh watchdog > /dev/null 2>&1
