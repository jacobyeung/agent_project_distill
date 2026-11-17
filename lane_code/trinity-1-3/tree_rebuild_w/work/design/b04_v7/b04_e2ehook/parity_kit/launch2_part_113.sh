#!/bin/bash
# First of two readings 5+ min apart, then launch_part_113.sh (which takes the second reading and launches only if empty).
CARD=$1; L=/dev/shm/jjyeung/b04/host2/b04_e2ehook
echo "$(date -u +%FT%TZ) card$CARD first reading: $(nvidia-smi -i $CARD --query-gpu=memory.used,utilization.gpu --format=csv,noheader) procs=$(nvidia-smi -i $CARD --query-compute-apps=pid --format=csv,noheader | wc -l)" >> $L/work/gpu_launch.log
sleep 310
bash $L/parity_kit/launch_part_113.sh "$@"
