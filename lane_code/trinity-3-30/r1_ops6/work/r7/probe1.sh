#!/bin/bash
# r1_ops7: read-only liveness probe inside 172660 (no write, CPU only)
export TZ=UTC
date -u +%FT%TZ
timeout 90 srun --overlap --jobid 172660 -n1 -N1 timeout 60 nice -n 19 bash -c '
nvidia-smi --query-gpu=index,memory.used,utilization.gpu,power.draw --format=csv,noheader
echo "== ps"; ps -u $(id -u) -o pid,ppid,etimes,pcpu,rss,stat,comm --sort=pid | awk "\$4>1 || /bwrap|python|torchrun/" | head -40
echo "== tools"; command -v nsenter bwrap; nsenter --version 2>&1 | head -1
echo "== load"; cat /proc/loadavg; free -g | head -2; df -h /tmp | tail -1
' < /dev/null 2>&1 | cut -c1-200
echo "srun rc=$?"
