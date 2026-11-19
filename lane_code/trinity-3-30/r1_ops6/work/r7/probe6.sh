#!/bin/bash
# r1_ops7: read-only debug of torch import inside a 172660 step (no write)
export TZ=UTC; date -u +%FT%TZ
timeout 250 srun --overlap --jobid 172660 -n1 -N1 timeout 220 nice -n 19 bash -s <<'STEP' 2>&1 | cut -c1-260
PID=$(ps -u $(id -u) -o pid=,rss=,comm= --sort=-rss | awk '$3=="python"{print $1; exit}')
PY=/project/community/jjyeung/c7d31ddd/venvs/rwtrain_torch211_cu129/bin/python
L=/project/community/jjyeung/c7d31ddd/venvs/rwtrain_torch211_cu129/lib/python3.12/site-packages/torch/lib/libtorch_cpu.so
echo "-- trainer maps of libtorch_cpu:"; grep -m2 libtorch_cpu /proc/$PID/maps | awk '{print $6}'
echo "-- ns -r -w, LD_DEBUG"; nsenter -t $PID -U -m -r -w --preserve-credentials env -i PATH=/usr/bin:/bin HOME=/tmp CUDA_VISIBLE_DEVICES= LD_DEBUG=files timeout 90 $PY -s -B -c "import ctypes; ctypes.CDLL('$L'); print('dlopen ok')" 2>&1 | grep -v -E "calling init|calling fini" | grep -i -E "error|cannot|fail|ok|mkl|file=" | tail -25
STEP
