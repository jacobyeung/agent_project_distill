#!/bin/bash
# r1_ops7: read-only debug of torch import inside a 172660 step (no write)
export TZ=UTC; date -u +%FT%TZ
for MEM in "" "--mem=32G"; do
echo "=== srun $MEM"
timeout 200 srun --overlap --jobid 172660 -n1 -N1 $MEM timeout 150 nice -n 19 bash -s <<'STEP' 2>&1 | cut -c1-400
PID=$(ps -u $(id -u) -o pid=,rss=,comm= --sort=-rss | awk '$3=="python"{print $1; exit}')
cat /proc/self/cgroup | head -3; CG=$(awk -F: '{print $3}' /proc/self/cgroup | head -1); cat /sys/fs/cgroup$CG/memory.max 2>/dev/null; ulimit -v -s
NS="nsenter -t $PID -U -m --preserve-credentials --wd=/"
PY=/project/community/jjyeung/c7d31ddd/venvs/rwtrain_torch211_cu129/bin/python
L=/project/community/jjyeung/c7d31ddd/venvs/rwtrain_torch211_cu129/lib/python3.12/site-packages/torch/lib/libtorch_cpu.so
$NS env -i PATH=/usr/bin:/bin HOME=/tmp CUDA_VISIBLE_DEVICES= timeout 120 $PY -s -B -c "
import ctypes,os
try: ctypes.CDLL('$L'); print('dlopen ok')
except OSError as e: print('dlopen fail', e)
import torch; print('torch', torch.__version__)
"
echo "rc=$?"
STEP
done
