#!/bin/bash
cd /scratch/jjyeung/orch_n30/cont_ops/work/h1orch
for i in $(seq 1 ${1:-60}); do
  echo "=== cycle $i $(date -u +%TZ)" >> m1_hist.txt
  bash cyc5.sh > cyc5_last.txt 2>&1
  sleep ${2:-5}
done
