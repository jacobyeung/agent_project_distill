#!/usr/bin/env bash
set -uo pipefail
W=/scratch/jjyeung/orch_n30/sb_ktchk/work
K=/scratch/jjyeung/orch_n30/sb_ktfix2
mount --bind $W/plant $K
cd $K
date -u +%T; bash scripts/cpu.sh $W/plant.py > $W/plant.log 2>&1; echo "plant exit $?"
date -u +%T
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export XDG_CACHE_HOME="$K/runtime/cache" HF_HOME="$K/runtime/hf" TRITON_CACHE_DIR="$K/runtime/triton" MPLCONFIGDIR="$K/runtime/mpl" TMPDIR="$K/runtime/tmp"
export TORCH_HOME="$K/runtime/torch" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export GEO_BAKEOFF_ROOT="$K" GEO_BAKEOFF_OUTPUT_ROOT="$K/out" GEO_BAKEOFF_ASSETS=/scratch/jjyeung/geo_bakeoff_kit/assets
export PYTHONPATH=/scratch/jjyeung/geo_bakeoff_kit/runtime/site:/scratch/jjyeung/geo_bakeoff_kit/assets/da3-src/Depth-Anything-3-3d835ec1a5802d64a8b8b15f817a1ab54809bfe4/src
mkdir -p "$TMPDIR"
nice -n 10 /scratch/jjyeung/envs/sam3_scipy_ovl/bin/python -B $W/trace_new.py > $W/trace_new.log 2>&1; echo "trace exit $?"
date -u +%T
