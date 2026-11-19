#!/usr/bin/env bash
# Tower-frames driver on trinity-0-13 (swarm_build3; ORCH GO 1030Z): parts A, B, C in series on one card, with a watchdog.
set -u
K=/scratch/jjyeung/orch_n30/sb_ktfix; CARD=${CARD:-6}; LOG=$K/out/tower_frames/DRIVER.log
mkdir -p $K/out/tower_frames; cd $K
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=$CARD OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
uuid=$(nvidia-smi --query-gpu=index,uuid --format=csv,noheader | awk -F', ' -v c=$CARD '$1==c{print $2}')
log(){ echo "$(date -u +%FT%TZ) $*" | tee -a $LOG; }
log "start card=$CARD uuid=$uuid host=$(hostname -s)"
for P in ${PARTS:-A B C}; do
  [ -e $K/inbox/STOP ] && { log "STOP file present; not starting $P"; break; }
  nice -n 10 python3 $K/inbox/grant.py open $P $CARD >> $LOG 2>&1 || { log "grant open failed for $P"; break; }
  setsid bash scripts/run_$P.sh >> $K/out/tower_frames/run_$P.log 2>&1 & JP=$!
  log "part $P started pid $JP"
  why=""
  while kill -0 $JP 2>/dev/null; do
    sleep 60
    for pid in $(nvidia-smi --query-compute-apps=gpu_uuid,pid --format=csv,noheader | awk -F', ' -v u=$uuid '$1==u{print $2}'); do
      u=$(ps -o user= -p $pid 2>/dev/null | tr -d ' '); [ -n "$u" ] && [ "$u" != "$USER" ] && why="other user $u pid $pid on card $CARD"
    done
    [ -e $K/inbox/STOP ] && why="STOP file"
    if [ -n "$why" ]; then log "stopping part $P: $why"; kill -TERM -- -$JP 2>/dev/null; sleep 20; kill -KILL -- -$JP 2>/dev/null; break; fi
  done
  wait $JP; rc=$?
  log "part $P exit $rc; peak/receipts in out/tower_frames"
  nice -n 10 python3 $K/inbox/grant.py close $P $CARD >> $LOG 2>&1
  [ -n "$why" ] && break
  [ $rc -ne 0 ] && { log "part $P failed rc=$rc; no further parts, no rerun"; break; }
done
log "driver end"
