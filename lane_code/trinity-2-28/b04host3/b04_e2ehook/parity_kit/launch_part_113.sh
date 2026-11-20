#!/bin/bash
# usage: launch_part_113.sh CARD ARM PART   (PART in 0,1,2; keys_part{PART}of3.txt)
CARD=$1; ARM=$2; PART=$3
L=/dev/shm/jjyeung/b04/host2/b04_e2ehook; LOG=$L/work/gpu_launch.log; P=$L/parity_kit
m=$(nvidia-smi -i $CARD --query-gpu=memory.used --format=csv,noheader,nounits | tr -d ' '); n=$(nvidia-smi -i $CARD --query-compute-apps=pid --format=csv,noheader | wc -l)
echo "$(date -u +%FT%TZ) card$CARD mem=$m procs=$n before ${ARM}_p$PART" >> $LOG
if [ "$m" -le 10 ] && [ "$n" -eq 0 ]; then
  echo "$(date -u +%FT%TZ) LAUNCH ${ARM}_p$PART card $CARD" >> $LOG
  bash $P/gpu_113.sh $CARD $ARM ${ARM}_p$PART /scratch/jjyeung/b04shm/b04/host2/b04_e2ehook/parity_kit/keys_part${PART}of3.txt > $L/work/gpu_${ARM}_p$PART.log 2>&1
  echo "$(date -u +%FT%TZ) ${ARM}_p${PART}_EXIT $?" >> $LOG
else echo "$(date -u +%FT%TZ) NOT_EMPTY card $CARD; no launch" >> $LOG; fi
