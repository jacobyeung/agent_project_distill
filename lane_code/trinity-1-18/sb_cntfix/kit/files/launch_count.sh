#!/bin/bash
set -euo pipefail
# One invocation only. A kill or dropped session requires an orchestrator decision.
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1
export COUNT_VNICE_LAUNCH=1
KIT=/scratch/jjyeung/orch_n30/sb_cntfix/kit/files
export XDG_CACHE_HOME=/scratch/jjyeung/orch_n30/sb_cntfix/cache/xdg
export HF_HOME=/scratch/jjyeung/orch_n30/sb_cntfix/cache/hf
export TRITON_CACHE_DIR=/scratch/jjyeung/orch_n30/sb_cntfix/cache/triton
export CONDA_PKGS_DIRS=/scratch/jjyeung/orch_n30/sb_cntfix/cache/conda
: "${VNICE:?Set VNICE to the admin vnice.sh executable, verified by the launch owner}"
[[ -x "$VNICE" ]]
exec "$VNICE" nice -n 10 /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python "$KIT/run_count_teacher.py" "$@"
