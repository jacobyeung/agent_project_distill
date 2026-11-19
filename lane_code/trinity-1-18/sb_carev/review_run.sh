#!/bin/bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/sb_carev
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export XDG_CACHE_HOME="$PWD/cache" HF_HOME="$PWD/cache/hf" TORCH_HOME="$PWD/cache/torch" TRITON_CACHE_DIR="$PWD/cache/triton"
export MPLCONFIGDIR="$PWD/cache/mpl" TMPDIR="$PWD/tmp" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
mkdir -p "$TMPDIR" logs
ulimit -v 39000000
case "$1" in
  sam3) PY=/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python ;;
  p1cpu) PY=/scratch/jjyeung/envs/p1cpu/bin/python ;;
esac
shift
exec nice -n 10 "$PY" -B "$@"
