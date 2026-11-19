#!/bin/bash
# Run the full differential battery on each tree at one shared absolute TMP path.
set -u
cd "$(dirname "$0")"
PY=/scratch/jjyeung/envs/p1cpu/bin/python
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
mkdir -p results tmp_runs
for t in "$@"; do
  if [ -e tmp/cur ]; then echo "tmp/cur exists" >&2; exit 1; fi
  timeout 3600 nice -n 10 $PY -B harness.py "$t" "$t" tmp/cur "results/$t.json" > "results/$t.log" 2>&1
  echo "$t exit=$?" | tee -a results/run_all.log
  mv tmp/cur "tmp_runs/$t.$(date +%s)"
done
