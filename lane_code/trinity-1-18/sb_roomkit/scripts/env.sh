#!/usr/bin/env bash
set -euo pipefail
export ROOMKIT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source /scratch/jjyeung/geo_bakeoff_kit/work/kit_env.sh
export TMPDIR="$ROOMKIT_ROOT/tmp" GEO_BAKEOFF_OUTPUT_ROOT="$ROOMKIT_ROOT/out"
export XDG_CACHE_HOME="$ROOMKIT_ROOT/cache" XDG_CONFIG_HOME="$ROOMKIT_ROOT/cache/config" MPLCONFIGDIR="$ROOMKIT_ROOT/cache/matplotlib"
export HF_HOME="$ROOMKIT_ROOT/cache/hf" TORCH_HOME="$ROOMKIT_ROOT/cache/torch" TRITON_CACHE_DIR="$ROOMKIT_ROOT/cache/triton"
export TORCH_EXTENSIONS_DIR="$ROOMKIT_ROOT/cache/extensions" NUMBA_CACHE_DIR="$ROOMKIT_ROOT/cache/numba" CUDA_CACHE_PATH="$ROOMKIT_ROOT/cache/cuda"
export PYTHONPATH="$ROOMKIT_ROOT/scripts:$ROOMKIT_ROOT/vendor:$PYTHONPATH"
export OMP_NUM_THREADS=6 MKL_NUM_THREADS=6 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"
