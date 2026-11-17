#!/bin/bash
# Two nvidia-smi readings 5+ min apart on card 3; launch the 5-key smoke only if both show the card empty.
L=/dev/shm/jjyeung/b04/host2/b04_e2ehook; LOG=$L/work/gpu_launch.log
read_card() { echo "$(date -u +%FT%TZ) $(nvidia-smi -i 3 --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader) procs=$(nvidia-smi -i 3 --query-compute-apps=pid --format=csv,noheader | wc -l)" >> $LOG; nvidia-smi -i 3 --query-gpu=memory.used --format=csv,noheader,nounits | tr -d ' '; }
m1=$(read_card); p1=$(nvidia-smi -i 3 --query-compute-apps=pid --format=csv,noheader | wc -l)
sleep 310
m2=$(read_card); p2=$(nvidia-smi -i 3 --query-compute-apps=pid --format=csv,noheader | wc -l)
if [ "$m1" -le 10 ] && [ "$m2" -le 10 ] && [ "$p1" -eq 0 ] && [ "$p2" -eq 0 ]; then
  echo "$(date -u +%FT%TZ) LAUNCH smoke card 3" >> $LOG
  bash $L/parity_kit/gpu_113.sh 3 own_depth smoke /scratch/jjyeung/b04shm/b04/host2/b04_e2ehook/parity_kit/keys_smoke.txt > $L/work/gpu_smoke.log 2>&1
  echo "$(date -u +%FT%TZ) SMOKE_EXIT $?" >> $LOG
else
  echo "$(date -u +%FT%TZ) NOT_EMPTY m1=$m1 m2=$m2 p1=$p1 p2=$p2; no launch" >> $LOG
fi
