#!/usr/bin/env bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/sb_ktow
: "${CUDA_VISIBLE_DEVICES:?Set the single GPU assigned by the orchestrator}"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export XDG_CACHE_HOME="$PWD/runtime/cache" HF_HOME="$PWD/runtime/hf" TRITON_CACHE_DIR="$PWD/runtime/triton" MPLCONFIGDIR="$PWD/runtime/mpl" TMPDIR="$PWD/runtime/tmp"
export TORCH_HOME="$PWD/runtime/torch" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export GEO_BAKEOFF_ROOT="$PWD" GEO_BAKEOFF_OUTPUT_ROOT="$PWD/out" GEO_BAKEOFF_ASSETS=/scratch/jjyeung/geo_bakeoff_kit/assets
export PYTHONPATH=/scratch/jjyeung/geo_bakeoff_kit/runtime/site:/scratch/jjyeung/geo_bakeoff_kit/assets/da3-src/Depth-Anything-3-3d835ec1a5802d64a8b8b15f817a1ab54809bfe4/src
mkdir -p "$TMPDIR"
ulimit -d 39062500
exec /scratch/jjyeung/envs/sam3_scipy_ovl/bin/python -B code/runner.py "$@"
