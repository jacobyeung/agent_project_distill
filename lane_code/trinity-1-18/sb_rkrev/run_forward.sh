#!/usr/bin/env bash
set -eo pipefail
H=/scratch/jjyeung/orch_n30/sb_rkrev
source /scratch/jjyeung/geo_bakeoff_kit/work/kit_env.sh
export TMPDIR=$H/tmp GEO_BAKEOFF_OUTPUT_ROOT=$H/out XDG_CACHE_HOME=$H/cache XDG_CONFIG_HOME=$H/cache/config MPLCONFIGDIR=$H/cache/mpl
export HF_HOME=$H/cache/hf TORCH_HOME=$H/cache/torch TRITON_CACHE_DIR=$H/cache/triton TORCH_EXTENSIONS_DIR=$H/cache/ext NUMBA_CACHE_DIR=$H/cache/numba CUDA_CACHE_PATH=$H/cache/cuda
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 CUDA_VISIBLE_DEVICES=''
export PYTHONPATH="$PYTHONPATH"
exec nice -n 10 "$GEO_BAKEOFF_ROOT/runtime/base/bin/python3" -B $H/rk_forward.py "$1"
