#!/bin/bash
# Usage: r3_all.sh BASE_TREE PATCHED_TREE   (A C | A2 C2); runs prod then mixed compositions sequentially.
set -euo pipefail
cd "$(dirname "$0")"
PY="nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 /scratch/jjyeung/envs/p1cpu/bin/python -B"
X=$1; Y=$2; O=compose
for K in prod mixed; do
  S=$O/same_${K}_${X}
  $PY r3_run.py $X absent $K $S > $O/${X}_${K}_absent.log 2>&1
  mv $S $O/${X}_${K}_absent; mv $S.filters.json $O/${X}_${K}_absent.filters.json
  $PY r3_run.py $Y absent $K $S > $O/${Y}_${K}_absent.log 2>&1
  mv $S $O/${Y}_${K}_absent; mv $S.filters.json $O/${Y}_${K}_absent.filters.json
  $PY r3_run.py $Y on $K $O/${Y}_${K}_on > $O/${Y}_${K}_on.log 2>&1
done
echo DONE $X $Y
