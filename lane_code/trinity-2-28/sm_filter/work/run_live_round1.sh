#!/bin/bash
set -u
cd /scratch/jjyeung/orch_n30
L=/scratch/jjyeung/orch_n30/sm_filter
export CUDA_VISIBLE_DEVICES="" LCS_ROBUST_SYNC=1
start=$(date +%s)
nice -n 10 timeout 600 /usr/bin/python3 -I -s -B - trinity-2-28 < "$L/in/tools/lane_code_filter.py" > /dev/null 2> "$L/work/dry-old-round1.stats"
rc=$?
printf 'old_exit=%s old_seconds=%s\n' "$rc" "$(( $(date +%s) - start ))" > "$L/work/live-round1.status"
if [ "$rc" -ne 0 ]; then exit "$rc"; fi
start=$(date +%s)
nice -n 10 timeout 600 /usr/bin/python3 -I -s -B "$L/out/tests/meter_scan.py" "$L/out/tools/lane_code_filter.py" trinity-2-28 "$L/work/dry-new-round1-lanes.json" > /dev/null 2> "$L/work/dry-new-round1.stats"
rc=$?
printf 'new_exit=%s new_seconds=%s\n' "$rc" "$(( $(date +%s) - start ))" >> "$L/work/live-round1.status"
exit "$rc"
