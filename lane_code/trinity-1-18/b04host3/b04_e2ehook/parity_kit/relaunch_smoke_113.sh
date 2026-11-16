#!/bin/bash
L=/dev/shm/jjyeung/b04/host2/b04_e2ehook; LOG=$L/work/gpu_launch.log; P=$L/parity_kit
for f in settings_bw.json E2E_MANIFEST_bw.json E2E_MANIFEST_bw.binding.json; do [ -f $P/$f ] && mv $P/$f $P/$f.v1; done
m=$(nvidia-smi -i 3 --query-gpu=memory.used --format=csv,noheader,nounits | tr -d ' '); n=$(nvidia-smi -i 3 --query-compute-apps=pid --format=csv,noheader | wc -l)
echo "$(date -u +%FT%TZ) card3 mem=$m procs=$n (relaunch after audit fix)" >> $LOG
if [ "$m" -le 10 ] && [ "$n" -eq 0 ]; then
  echo "$(date -u +%FT%TZ) LAUNCH smoke2 card 3" >> $LOG
  bash $P/gpu_113.sh 3 own_depth smoke2 /scratch/jjyeung/b04shm/b04/host2/b04_e2ehook/parity_kit/keys_smoke.txt > $L/work/gpu_smoke2.log 2>&1
  echo "$(date -u +%FT%TZ) SMOKE2_EXIT $?" >> $LOG
else echo "$(date -u +%FT%TZ) NOT_EMPTY; no launch" >> $LOG; fi
