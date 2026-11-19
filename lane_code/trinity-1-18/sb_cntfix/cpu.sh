#!/bin/bash
set -euo pipefail
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=
export XDG_CACHE_HOME=/scratch/jjyeung/orch_n30/sb_cntfix/cache/xdg HF_HOME=/scratch/jjyeung/orch_n30/sb_cntfix/cache/hf TRITON_CACHE_DIR=/scratch/jjyeung/orch_n30/sb_cntfix/cache/triton CONDA_PKGS_DIRS=/scratch/jjyeung/orch_n30/sb_cntfix/cache/conda
exec nice -n 10 /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python "$@"
