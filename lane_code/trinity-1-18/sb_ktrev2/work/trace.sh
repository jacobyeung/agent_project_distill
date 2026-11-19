#!/usr/bin/env bash
# Same interpreter, PYTHONPATH and GEO_BAKEOFF_* as scripts/gpu_environment.sh; CUDA hidden; caches in this workspace.
set -euo pipefail
W=/scratch/jjyeung/orch_n30/sb_ktrev2/work
K=/scratch/jjyeung/orch_n30/sb_ktfix
cd "$W"
mkdir -p "$W/trace" "$W/trace_rt/tmp"
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export XDG_CACHE_HOME="$W/trace_rt/cache" HF_HOME="$W/trace_rt/hf" TRITON_CACHE_DIR="$W/trace_rt/triton" MPLCONFIGDIR="$W/trace_rt/mpl" TMPDIR="$W/trace_rt/tmp"
export TORCH_HOME="$W/trace_rt/torch" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export GEO_BAKEOFF_ROOT="$K" GEO_BAKEOFF_OUTPUT_ROOT="$K/out" GEO_BAKEOFF_ASSETS=/scratch/jjyeung/geo_bakeoff_kit/assets
export PYTHONPATH=/scratch/jjyeung/geo_bakeoff_kit/runtime/site:/scratch/jjyeung/geo_bakeoff_kit/assets/da3-src/Depth-Anything-3-3d835ec1a5802d64a8b8b15f817a1ab54809bfe4/src
exec nice -n 10 /scratch/jjyeung/envs/sam3_scipy_ovl/bin/python -B "$W/trace_reads.py" "$1"
