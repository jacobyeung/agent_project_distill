#!/bin/bash
# Started by launch_gpu.sh under vnice.sh (arguments arrive in MC_* variables because vnice drops quoting).
set -u
cd "$MC_KIT"
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES="$MC_GPU"
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$MC_KIT"
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
W="$(dirname "$MC_KIT")/work/v2"
export XDG_CACHE_HOME="$W/cache" HF_HOME="$W/hf" TORCH_HOME="$W/torch" TRITON_CACHE_DIR="$W/triton" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
RESUME=(); [ "${MC_RESUME_AFTER_STOP:-0}" = 1 ] && RESUME=(--resume-after-stop)
exec timeout -k 30 "$MC_TIMEOUT" "$MC_PY" -B mc_track_pass.py --device cuda --out "$MC_OUT" --hard-stop "$MC_HARD_STOP" ${MC_PASS_ARGS:-} "${RESUME[@]}"
