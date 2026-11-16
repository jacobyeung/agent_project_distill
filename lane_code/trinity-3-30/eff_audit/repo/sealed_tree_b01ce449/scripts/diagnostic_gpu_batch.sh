#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || ( "$1" != "train" && "$1" != "evaluate" ) ]]; then
    printf '%s\n' 'Usage: bash scripts/diagnostic_gpu_batch.sh train|evaluate supervisor_gpu_lease.json [diagnostic arguments]' >&2
    exit 2
fi
mode="$1"
lease="$2"
shift 2
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
venv="${PILOT_VENV:-/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/venv}"
if [[ ! -x "$venv/bin/python" ]]; then
    printf 'PILOT_VENV has no executable interpreter: %s\n' "$venv/bin/python" >&2
    exit 2
fi
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES-1}"
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export HF_HOME="${HF_HOME:-/data2/jjyeung/cache/huggingface}"
export HUGGINGFACE_HUB_CACHE="$HF_HOME/hub"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HUB_DISABLE_TELEMETRY=1
export TOKENIZERS_PARALLELISM=false
export WANDB_DISABLED=true
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-4}"
cd -- "$repo"
exec "$venv/bin/python" -B -u -m student_pilot.cli diagnostic "$mode" --lease "$lease" "$@"
