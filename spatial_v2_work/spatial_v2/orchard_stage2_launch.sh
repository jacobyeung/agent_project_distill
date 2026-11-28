#!/usr/bin/env bash
#SBATCH --job-name=a15_cot_aps2v2
#SBATCH --partition=advanced
#SBATCH --qos=adv_4gpu_qos
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=32
#SBATCH --mem=256G
#SBATCH --time=18:00:00
#SBATCH --output=/tmp/a15_cot_aps2v2_%j.out
#SBATCH --error=/tmp/a15_cot_aps2v2_%j.err
# ==============================================================================
# Orchard 4x H100 80GB Launcher for Spatial-V2 Stage-2 Full 9B Training
# ------------------------------------------------------------------------------
# Usage:
#   # Launch winning Arm C (da3_nested) or Arm B (corresp_stem) on 4x H100 advanced:
#   sbatch -J a15_cot_aps2c01 spatial_v2/orchard_stage2_launch.sh da3_nested /tmp/stage1a_winner.pt
#   sbatch -J a15_cot_aps2b01 spatial_v2/orchard_stage2_launch.sh corresp_stem /tmp/stage1a_winner.pt
#
#   # Launch on preempt queue:
#   sbatch -J a15_cot_aps2p01 -p preempt --qos=preempt_qos spatial_v2/orchard_stage2_launch.sh da3_nested
#
# Storage hygiene:
#   /project/community has only ~9.0 GiB free. ALL staging, caches, and checkpoints
#   live strictly on compute-node /tmp (~6.0 TB free) and sync directly to GCS:
#     gs://cmu-gpucloud-jjyeung/spatial_v2/<RUN_ID>/
# ==============================================================================

set -euo pipefail

FRONTEND="${1:-${FRONTEND:-da3_nested}}"
STAGE1A_CKPT="${2:-${STAGE1A_CKPT:-}}"
STEPS="${STEPS:-2000}"
BATCH_SIZE="${BATCH_SIZE:-1}"
GRAD_ACCUM="${GRAD_ACCUM:-4}"
NUM_VIEWS="${NUM_VIEWS:-16}"
GRID_H="${GRID_H:-20}"
GRID_W="${GRID_W:-20}"
SEQ_LEN="${SEQ_LEN:-512}"
LM_LR="${LM_LR:-1e-5}"
FRONTEND_LR="${FRONTEND_LR:-5e-5}"
HEAD_LR="${HEAD_LR:-2e-4}"
SHARDING="${SHARDING:-fsdp2}"
USE_VLA_AUX="${USE_VLA_AUX:-0}"

JOB_TAG="${SLURM_JOB_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
RUN_ID="${RUN_ID:-s2_${FRONTEND}_${JOB_TAG}}"
WORK_ROOT="/tmp/a15_s2_${JOB_TAG}"
CACHE_ROOT="${WORK_ROOT}/cache"
STAGE_ROOT="${WORK_ROOT}/stage"
OUT_DIR="${WORK_ROOT}/out/${RUN_ID}"
GCS_BUCKET_PREFIX="${GCS_BUCKET_PREFIX:-gs://cmu-gpucloud-jjyeung/spatial_v2/${RUN_ID}}"

mkdir -p "${CACHE_ROOT}" "${STAGE_ROOT}" "${OUT_DIR}"

# 1. Redirect all caches & tmp dirs strictly to node-local /tmp (0 B written to /home or /project)
export TMPDIR="${CACHE_ROOT}/tmp"
export XDG_CACHE_HOME="${CACHE_ROOT}/xdg"
export HF_HOME="${CACHE_ROOT}/hf"
export HUGGINGFACE_HUB_CACHE="${CACHE_ROOT}/hf/hub"
export TORCH_HOME="${CACHE_ROOT}/torch"
export TRITON_CACHE_DIR="${CACHE_ROOT}/triton"
export PIP_CACHE_DIR="${CACHE_ROOT}/pip"
export CLOUDSDK_CONFIG="${CLOUDSDK_CONFIG:-/project/community/jjyeung/gcloud}"
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=8
export NCCL_DEBUG=WARN
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"
mkdir -p "${TMPDIR}" "${XDG_CACHE_HOME}" "${HUGGINGFACE_HUB_CACHE}" "${TORCH_HOME}" "${TRITON_CACHE_DIR}" "${PIP_CACHE_DIR}"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting Spatial-V2 Stage-2 on $(hostname -s) (Job=${JOB_TAG}, Frontend=${FRONTEND})"
df -h /tmp

# 2. Verify >= 250 GiB free on node-local /tmp before staging weights
FREE_TMP_GIB=$(df -BG /tmp | awk 'NR==2 {gsub("G","",$4); print $4}')
if [ "${FREE_TMP_GIB:-0}" -lt 250 ]; then
  echo "FATAL: /tmp has only ${FREE_TMP_GIB} GiB free (< 250 GiB required)" >&2
  exit 1
fi

# 3. Stage step-544 Qwen3.5-9B backbone checkpoint into /tmp
INIT_CKPT="${INIT_CKPT:-${STAGE_ROOT}/step544}"
STEP544_TAR="${STEP544_TAR:-/project/community/jjyeung/okh7/i_bb09a77d/m.tar}"
if [ ! -d "${INIT_CKPT}" ] && [ -f "${STEP544_TAR}" ]; then
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Extracting step-544 backbone from ${STEP544_TAR} -> ${INIT_CKPT}"
  mkdir -p "${INIT_CKPT}"
  tar xf "${STEP544_TAR}" -C "${INIT_CKPT}" --strip-components=1 || tar xf "${STEP544_TAR}" -C "${INIT_CKPT}"
fi

# 4. Stage DA3-Nested & optional Point4D 4D dynamic teacher weights from GCS into /tmp
DA3_CKPT="${DA3_CKPT:-${STAGE_ROOT}/da3/model.safetensors}"
if [ ! -f "${DA3_CKPT}" ] && [ -n "${GCS_DA3_URI:-}" ]; then
  mkdir -p "$(dirname "${DA3_CKPT}")"
  gcloud storage cp "${GCS_DA3_URI}" "${DA3_CKPT}"
fi

POINT4D_CKPT="${POINT4D_CKPT:-${STAGE_ROOT}/point4d/point4d_final.pt}"
if [ "${STAGE_POINT4D:-0}" = "1" ] && [ ! -f "${POINT4D_CKPT}" ]; then
  mkdir -p "$(dirname "${POINT4D_CKPT}")"
  gcloud storage cp "gs://cmu-gpucloud-jjyeung/ae/b2__f7d2a9c4__newbench_dyn4d__weights__point4d__point4d_final.pt" "${POINT4D_CKPT}" || true
fi

# 5. Stage winning KT-6 Stage-1A front-end checkpoint from GCS if a gs:// URI was provided
if [[ "${STAGE1A_CKPT}" == gs://* ]]; then
  LOCAL_S1A="${STAGE_ROOT}/stage1a_winner.pt"
  gcloud storage cp "${STAGE1A_CKPT}" "${LOCAL_S1A}"
  STAGE1A_CKPT="${LOCAL_S1A}"
fi

# 6. Resolve Python / torchrun environment
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"
TORCHRUN_BIN="${TORCHRUN_BIN:-$(command -v torchrun)}"
CODE_ROOT="${CODE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
export PYTHONPATH="${CODE_ROOT}:${PYTHONPATH:-}"

EXTRA_ARGS=()
if [ -n "${STAGE1A_CKPT}" ] && [ -f "${STAGE1A_CKPT}" ]; then
  EXTRA_ARGS+=(--stage1a-ckpt "${STAGE1A_CKPT}")
fi
if [ "${USE_VLA_AUX}" = "1" ]; then
  EXTRA_ARGS+=(--use-vla-aux)
fi
if [ "${SYNTHETIC_SMOKE:-0}" = "1" ]; then
  EXTRA_ARGS+=(--synthetic-data --init-ckpt synthetic)
else
  EXTRA_ARGS+=(--init-ckpt "${INIT_CKPT}" --da3-ckpt "${DA3_CKPT}")
fi

# 7. Launch 4x H100 FSDP2 Stage-2 training with automatic GCS checkpoint sync
"${TORCHRUN_BIN}" \
  --standalone \
  --nproc_per_node="${NGPUS:-4}" \
  -m spatial_v2.train_stage2 \
  --frontend "${FRONTEND}" \
  --sharding "${SHARDING}" \
  --out-dir "${OUT_DIR}" \
  --steps "${STEPS}" \
  --batch-size "${BATCH_SIZE}" \
  --grad-accum "${GRAD_ACCUM}" \
  --num-views "${NUM_VIEWS}" \
  --grid-h "${GRID_H}" \
  --grid-w "${GRID_W}" \
  --seq-len "${SEQ_LEN}" \
  --lm-lr "${LM_LR}" \
  --frontend-lr "${FRONTEND_LR}" \
  --head-lr "${HEAD_LR}" \
  --save-every "${SAVE_EVERY:-250}" \
  --gcs-sync-uri "${GCS_BUCKET_PREFIX}" \
  --random-subsample \
  "${EXTRA_ARGS[@]}"

# 8. Final sync of logs & run_summary.json to GCS
if command -v gcloud >/dev/null 2>&1; then
  gcloud storage cp "${OUT_DIR}/run_summary.json" "${OUT_DIR}/train_log.jsonl" "${OUT_DIR}/config_summary.json" "${GCS_BUCKET_PREFIX}/" || true
fi

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Spatial-V2 Stage-2 complete. Artifacts synced to ${GCS_BUCKET_PREFIX}"
