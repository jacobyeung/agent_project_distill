#!/bin/bash
# Write the kit's STOP file 13,800 s after launch, so the phase stops at a capture boundary before the watchdog's 14,400 s cap.
OUT=/scratch/jjyeung/k1/run_tower_sam_2; sleep 13800
grep -q '"event": "complete"' $OUT/PROGRESS.jsonl 2>/dev/null && exit 0
grep -q '^EXIT' /scratch/jjyeung/k1/RUN2.log 2>/dev/null && exit 0
echo STOP > $OUT/STOP; echo "$(date -u +%FT%TZ) STOP written by stop_timer_2" >> /scratch/jjyeung/k1/RUN2.log
