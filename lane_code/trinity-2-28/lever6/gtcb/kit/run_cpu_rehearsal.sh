#!/bin/bash
# CPU rehearsal of track.py (arm b): nice 10, 8 threads, no CUDA device, caches under gtcb/work. Usage: bash run_cpu_rehearsal.sh <out> [track.py args...]
set -u
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; W="$(dirname "$KIT")/work/cache"
export CUDA_VISIBLE_DEVICES='' PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export XDG_CACHE_HOME="$W/xdg" HF_HOME="$W/hf" TORCH_HOME="$W/torch" TRITON_CACHE_DIR="$W/triton" MPLCONFIGDIR="$W/mpl" TMPDIR="$W/tmp" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
mkdir -p "$TMPDIR"; OUT="$1"; shift
cd "$KIT" && exec nice -n 10 /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python -B track.py --device cpu --threads 8 --out "$OUT" "$@"
