#!/usr/bin/env bash
# bash part2/launch_part2.sh MODE: MODE is capture (after the GPU pass) or fixture-capture (CPU dry run); 8 shard processes under run.sh.
set -euo pipefail
cd /scratch/jjyeung/orch_n30/sb_mask_phrase
mode=$1
case "$mode" in capture|fixture-capture) ;; *) echo "mode: capture | fixture-capture" >&2; exit 2;; esac
mkdir -p work/logs
pids=()
for s in 0 1 2 3 4 5 6 7; do
  bash run.sh part2/price.py "$mode" "$s" 8 > "work/logs/part2_${mode}_${s}.log" 2>&1 &
  pids+=($!)
done
rc=0
for p in "${pids[@]}"; do wait "$p" || rc=1; done
echo "{\"mode\": \"part2 $mode\", \"returncode\": $rc}" >> work/logs/stages.log
exit $rc
