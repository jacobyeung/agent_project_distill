#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || "$1" != "smoke" ]]; then
    printf '%s\n' 'Usage: bash scripts/gpu_batch.sh smoke /data2/path/to/supervisor_gpu_lease.json [--manifest PATH] [--output PATH]' >&2
    exit 2
fi
lease="$2"
shift 2
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
pilot="$(dirname -- "$repo")"
export CUDA_VISIBLE_DEVICES=1
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$repo/.tmp"
export XDG_CACHE_HOME="$repo/.cache"
export HF_HOME="$repo/.cache/huggingface"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HUB_DISABLE_TELEMETRY=1
export TOKENIZERS_PARALLELISM=false
export WANDB_DISABLED=true
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
cd -- "$repo"
exec "$pilot/venv/bin/python" -u -m student_pilot.cli smoke --lease "$lease" "$@"
