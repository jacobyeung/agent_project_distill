#!/bin/bash
# r1_ops7: read-only look at 172660's node-local run dir (no write)
export TZ=UTC
date -u +%FT%TZ
timeout 90 srun --overlap --jobid 172660 -n1 -N1 timeout 60 nice -n 19 bash -c '
R=/tmp/jjyeung/a_6ed2c7aa/runs/6ed2c7aa
ls -la --time-style=+%T $R | cut -c1-150
ls -la --time-style=+%T $R/checkpoint_* 2>&1 | head -20
for f in $R/metrics_*.jsonl; do wc -l $f; done
ls -la --time-style=+%T /tmp/jjyeung/okit_8865619b/ 2>&1 | head; ls /tmp/jjyeung 2>&1
nvidia-smi --query-gpu=index,utilization.gpu --format=csv,noheader | tr "\n" " "
' < /dev/null 2>&1 | cut -c1-200
echo "srun rc=$?"
