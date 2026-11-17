#!/bin/bash
set -eu
L=/scratch/jjyeung/orch_n30/tree_rebuild_w
export TMPDIR="$L/work/tmp" OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
ulimit -f 204800
df -BG --output=avail /scratch
bash "$L/work/build8/RUN_PY.sh" "$L/work/lane_stop2/stop_multirank.py"
