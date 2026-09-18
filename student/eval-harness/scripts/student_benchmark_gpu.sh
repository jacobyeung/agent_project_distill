#!/usr/bin/env bash
set -euo pipefail

repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
case "$repo" in
    /data2/*) ;;
    *) printf '%s\n' 'GPU entrypoint requires the landed /data2 trainer repository, not a workspace copy.' >&2; exit 2 ;;
esac
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:?Supervisor must select one leased physical GPU}"
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export HF_HOME=/data2/jjyeung/cache/huggingface
export HUGGINGFACE_HUB_CACHE=/data2/jjyeung/cache/huggingface/hub
export TORCH_HOME=/data2/jjyeung/cache/torch
export PIP_CACHE_DIR=/data2/jjyeung/cache/pip
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HUB_DISABLE_TELEMETRY=1
export TOKENIZERS_PARALLELISM=false
export WANDB_DISABLED=true
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
export AGENT_COORD_DIR=/data2/jjyeung/agent_project/.coord
artifact_root="$repo/artifacts/paper_eval"
export TMPDIR="$artifact_root/cache/tmp"
export XDG_CACHE_HOME="$artifact_root/cache/xdg"
export CUDA_CACHE_PATH="$artifact_root/cache/cuda"
export TRITON_CACHE_DIR="$artifact_root/cache/triton"
export TORCHINDUCTOR_CACHE_DIR="$artifact_root/cache/torchinductor"
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME" "$CUDA_CACHE_PATH" "$TRITON_CACHE_DIR" "$TORCHINDUCTOR_CACHE_DIR"
cd -- "$repo"
exec "$repo/../venv/bin/python" -B -u -m student_pilot.benchmark_eval generate \
    --artifact-root "$artifact_root" --model-root "$HUGGINGFACE_HUB_CACHE" \
    --coord-root "$AGENT_COORD_DIR" "$@"
