#!/bin/bash
# Started by launch_gpu.sh under the kit's pinned vnice.sh (arguments arrive in MC_* variables because vnice drops quoting).
# Every cache and temporary file goes under the track directory MC_OUT, so the pass writes only there.
set -u
cd "$MC_KIT"
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES="$MC_GPU"
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$MC_KIT"
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
W="$MC_OUT/cache"
export XDG_CACHE_HOME="$W/xdg" HF_HOME="$W/hf" TORCH_HOME="$W/torch" TRITON_CACHE_DIR="$W/triton" TORCHINDUCTOR_CACHE_DIR="$W/inductor"
export CUDA_CACHE_PATH="$W/nv" MPLCONFIGDIR="$W/mpl" TMPDIR="$W/tmp" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
mkdir -p "$TMPDIR"
RESUME=(); [ "${MC_RESUME_AFTER_STOP:-0}" = 1 ] && RESUME=(--resume-after-stop)
exec timeout -k 30 "$MC_TIMEOUT" "$MC_PY" -B mc_track_pass.py --device cuda --out "$MC_OUT" --hard-stop "$MC_HARD_STOP" "${RESUME[@]}"
