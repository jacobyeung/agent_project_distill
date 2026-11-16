#!/bin/bash
# In-job stall guard (USER ruling 128). usage: stall_watch.sh PID TRACE ALERT_DIR [STALL_MIN] [GRACE_MIN]
# While PID lives: if TRACE has not changed for STALL_MIN minutes (GRACE_MIN before the first trace line), write
# ALERT_DIR/STALL_ALERT_<utc>.txt with GPU state and log tails, once per stall. Never touches the job.
pid=$1 trace=$2 A=$3 stall=${4:-20} grace=${5:-45}; mkdir -p $A; t0=$(date +%s); alerted=0
while kill -0 $pid 2>/dev/null; do
  now=$(date +%s); m=$(stat -c %Y $trace 2>/dev/null || echo 0)
  if [ $m = 0 ]; then age=$(( (now - t0) / 60 )); lim=$grace; else age=$(( (now - m) / 60 )); lim=$stall; fi
  if [ $age -ge $lim ] && [ $alerted != $m ]; then
    f=$A/STALL_ALERT_$(date -u +%Y%m%dT%H%MZ).txt
    { echo "trace $trace unchanged for $age min (limit $lim); pid $pid alive; host $(hostname)"; nvidia-smi --query-gpu=index,utilization.gpu,memory.used --format=csv 2>&1; tail -20 $(dirname $trace)/train.log 2>/dev/null; } > $f
    alerted=$m
  fi
  sleep 60
done
