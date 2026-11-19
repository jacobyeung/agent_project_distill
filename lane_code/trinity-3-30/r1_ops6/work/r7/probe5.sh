#!/bin/bash
# r1_ops7: read-only debug of torch import inside a 172660 step (no write)
export TZ=UTC; date -u +%FT%TZ
timeout 250 srun --overlap --jobid 172660 -n1 -N1 timeout 220 nice -n 19 bash -s <<'STEP' 2>&1 | cut -c1-300
PID=$(ps -u $(id -u) -o pid=,rss=,comm= --sort=-rss | awk '$3=="python"{print $1; exit}')
grep -E "stack|address|locked" /proc/$PID/limits
NS="nsenter -t $PID -U -m --preserve-credentials --wd=/"
PY=/project/community/jjyeung/c7d31ddd/venvs/rwtrain_torch211_cu129/bin/python
ls -la $PY 2>&1 | cut -c1-200
T='import torch; print("torch", torch.__version__)'
echo "-- host ns, stack 8192"; ( ulimit -s 8192; env -i PATH=/usr/bin:/bin HOME=/tmp CUDA_VISIBLE_DEVICES= timeout 90 $PY -s -B -c "$T" 2>&1 | tail -1 )
echo "-- ns, stack 8192"; ( ulimit -s 8192; $NS env -i PATH=/usr/bin:/bin HOME=/tmp CUDA_VISIBLE_DEVICES= timeout 90 $PY -s -B -c "$T" 2>&1 | tail -1 )
STEP
