#!/usr/bin/env bash
export ROOMKIT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
_roomkit_saved_options="$(set +o)"
case $- in *e*) _roomkit_saved_errexit=1;; *) _roomkit_saved_errexit=0;; esac
source /scratch/jjyeung/geo_bakeoff_kit/work/kit_env.sh
 eval "$_roomkit_saved_options"
if [ "$_roomkit_saved_errexit" = 1 ]; then set -e; else set +e; fi
unset _roomkit_saved_options _roomkit_saved_errexit
export TMPDIR="$ROOMKIT_ROOT/tmp" GEO_BAKEOFF_OUTPUT_ROOT="$ROOMKIT_ROOT/out"
export XDG_CACHE_HOME="$ROOMKIT_ROOT/cache" XDG_CONFIG_HOME="$ROOMKIT_ROOT/cache/config" MPLCONFIGDIR="$ROOMKIT_ROOT/cache/matplotlib"
export HF_HOME="$ROOMKIT_ROOT/cache/hf" TORCH_HOME="$ROOMKIT_ROOT/cache/torch" TRITON_CACHE_DIR="$ROOMKIT_ROOT/cache/triton"
export TORCH_EXTENSIONS_DIR="$ROOMKIT_ROOT/cache/extensions" NUMBA_CACHE_DIR="$ROOMKIT_ROOT/cache/numba" CUDA_CACHE_PATH="$ROOMKIT_ROOT/cache/cuda"
export PYTHONPATH="$ROOMKIT_ROOT/scripts:$ROOMKIT_ROOT/vendor:${PYTHONPATH:-}"
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=1
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"
