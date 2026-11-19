#!/usr/bin/env bash
set -euo pipefail

: "${NPROC_PER_NODE:?Set the number of genuinely leased GPUs (2 to 8)}"
: "${CUDA_VISIBLE_DEVICES:?List the leased GPU UUIDs or physical indices in rank order}"
: "${LEASE_BUNDLE:?Set the bound DDP lease bundle}"
: "${TRAINING_MANIFEST:?Set the prepared provisional training manifest}"
: "${PROTOCOL:?Set the frozen DDP protocol}"
: "${TRAINING_CONFIG:?Set the matching training configuration JSON}"
: "${RUN_OUTPUT:?Set the node-local training output directory}"
: "${SCRATCH_ROOT:?Set the existing root under /scratch/jjyeung}"
: "${STUDENT:?Set onethinker or qwen35}"
: "${PROVISIONAL_DIAGNOSTIC:?Set the exact accepted provisional label}"
case "$NPROC_PER_NODE" in
    2|3|4|5|6|7|8) ;;
    *) printf '%s\n' 'NPROC_PER_NODE must be between 2 and 8' >&2; exit 2 ;;
esac
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
venv="${PILOT_VENV:-/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/venv}"
if [[ ! -x "$venv/bin/torchrun" ]]; then
    printf 'PILOT_VENV has no executable torchrun: %s\n' "$venv/bin/torchrun" >&2
    exit 2
fi
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
export HF_HOME="${HF_HOME:-/data2/jjyeung/cache/huggingface}"
export HUGGINGFACE_HUB_CACHE="$HF_HOME/hub"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
export TOKENIZERS_PARALLELISM=false WANDB_DISABLED=true
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-2}" MKL_NUM_THREADS="${MKL_NUM_THREADS:-2}"
export CUDA_DEVICE_ORDER=PCI_BUS_ID TORCH_NCCL_ASYNC_ERROR_HANDLING=1
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF-expandable_segments:True}"
export TMPDIR="$SCRATCH_ROOT/ddp_runtime_tmp"
mkdir -p -- "$TMPDIR"
cd -- "$repo"
resume_args=()
if [[ -n "${RESUME_FROM:-}" ]]; then
    resume_args=(--resume-from "$RESUME_FROM")
fi
NNODES="${NNODES:-1}"
case "$NNODES" in
    1) ;;
    2|3|4|5|6|7|8)
        : "${NODE_RANK:?Set the node rank in Slurm hostname order}"
        : "${MASTER_ADDR:?Set the hostname of node zero}"
        : "${MASTER_PORT:?Set the static rendezvous port}"
        if [[ ! "$NODE_RANK" =~ ^[0-7]$ || "$NODE_RANK" -ge "$NNODES" || ! "$MASTER_PORT" =~ ^[0-9]+$ ]] \
            || (( 10#$MASTER_PORT < 1 || 10#$MASTER_PORT > 65535 )); then
            printf '%s\n' 'Invalid multi-node rank or rendezvous port' >&2; exit 2
        fi
        exec "$venv/bin/torchrun" --nnodes="$NNODES" --node_rank="$NODE_RANK" --master_addr="$MASTER_ADDR" --master_port="$MASTER_PORT" \
            --nproc_per_node "$NPROC_PER_NODE" --max_restarts=0 \
            -m student_pilot.cli diagnostic train-ddp --parallel "${PARALLEL:-ddp}" --student "$STUDENT" --manifest "$TRAINING_MANIFEST" \
            --protocol "$PROTOCOL" --training-config "$TRAINING_CONFIG" --lease "$LEASE_BUNDLE" \
            --output "$RUN_OUTPUT" --scratch-root "$SCRATCH_ROOT" --stage-frames \
            --provisional-diagnostic "$PROVISIONAL_DIAGNOSTIC" "${resume_args[@]}"
        ;;
    *) printf '%s\n' 'NNODES must be between 1 and 8' >&2; exit 2 ;;
esac
exec "$venv/bin/torchrun" --standalone --nnodes=1 --nproc_per_node "$NPROC_PER_NODE" --max_restarts=0 \
    -m student_pilot.cli diagnostic train-ddp --parallel "${PARALLEL:-ddp}" --student "$STUDENT" --manifest "$TRAINING_MANIFEST" \
    --protocol "$PROTOCOL" --training-config "$TRAINING_CONFIG" --lease "$LEASE_BUNDLE" \
    --output "$RUN_OUTPUT" --scratch-root "$SCRATCH_ROOT" --stage-frames \
    --provisional-diagnostic "$PROVISIONAL_DIAGNOSTIC" "${resume_args[@]}"
