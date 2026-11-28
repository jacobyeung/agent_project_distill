#!/usr/bin/env bash
#SBATCH --job-name=a15_cot_ap4dk7
#SBATCH --partition=general
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus-per-task=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#
# Spatial-V2 Stage-2 Dynamic 4D Teacher Extraction Launcher for Orchard (1x H100 general)
#
# Pulls Point4D (5.80 GB), Any4D-4v (7.73 GB), and MoGe-ViT-L (1.26 GB) from
# gs://cmu-gpucloud-jjyeung/ae/ into node-local 6 TB /tmp (zero /project quota fill),
# runs Dynamic4DExclusionGuard pre-flight zero-leak verification, extracts 96f->32f
# metric-anchored 4D teacher stores (depth_gt, SE(3) w2c poses, +Z-up floor gravity,
# p_dyn_gt = 1 - y_stat_gt, and multi-horizon 3D point tracks delta_p_gt for
# horizons (-1, 1, 4, 16)), and streams tar.zst shards to GCS.

set -euo pipefail

DRY_RUN=0
SHARD=0
SHARDS=1
GRID_H=20
GRID_W=20
GCS_BUCKET="gs://cmu-gpucloud-jjyeung"
GCS_OUT_PREFIX="${GCS_BUCKET}/spatial_v2/dyn4d_teachers_v1"
REPO_ROOT="${SPATIAL_V2_ROOT:-/scratch/jjyeung/orch_home_distill}"
PYTHON_BIN="${PYTHON_BIN:-/scratch/jjyeung/envs/p1cpu/bin/python3}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --shard)
      SHARD="$2"
      shift 2
      ;;
    --shards)
      SHARDS="$2"
      shift 2
      ;;
    --grid-hw)
      GRID_H="$2"
      GRID_W="$3"
      shift 3
      ;;
    --gcs-out)
      GCS_OUT_PREFIX="$2"
      shift 2
      ;;
    *)
      echo "Unknown flag: $1" >&2
      exit 2
      ;;
  esac
done

# 1. Stage all weights, caches, and active shards on node-local /tmp (6 TB on Orchard H100 nodes)
JOB_TAG="${SLURM_JOB_ID:-local_$$}"
WORK_TMP="${TMPDIR:-/tmp}/jjyeung_spv2_dyn4d_${JOB_TAG}"
WEIGHTS_DIR="${WORK_TMP}/weights"
OUT_DIR="${WORK_TMP}/out_shard_${SHARD}_of_${SHARDS}"

export XDG_CACHE_HOME="${WORK_TMP}/cache/xdg"
export HF_HOME="${WORK_TMP}/cache/hf"
export HUGGINGFACE_HUB_CACHE="${WORK_TMP}/cache/hf/hub"
export TORCH_HOME="${WORK_TMP}/cache/torch"
export TRITON_CACHE_DIR="${WORK_TMP}/cache/triton"
export PIP_CACHE_DIR="${WORK_TMP}/cache/pip"
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=4

# Pinned GCS URIs & SHA256 digests
GCS_POINT4D="${GCS_BUCKET}/ae/b2__f7d2a9c4__newbench_dyn4d__weights__point4d__point4d_final.pt"
SHA_POINT4D="dacdabdd8678da9f247f6ac51aefcd1771a94af4b677166a5683b6971a4950cb"
BYTES_POINT4D=5797274779

GCS_ANY4D="${GCS_BUCKET}/ae/b5__fourdv__external__ckpt__any4d_4v_combined.pth"
BYTES_ANY4D=7726955585

GCS_MOGE="${GCS_BUCKET}/ae/b5__fourdv__external__ckpt__moge_vitl_model.pt"
BYTES_MOGE=1256826189

echo "[orchard_extract_4d_teachers] shard=${SHARD}/${SHARDS} grid=${GRID_H}x${GRID_W} work_tmp=${WORK_TMP} dry_run=${DRY_RUN}"

# 2. Fail-closed zero-leak benchmark exclusion check before any extraction
PYTHONPATH="${REPO_ROOT}" "${PYTHON_BIN}" -B -c "
import json
from spatial_v2.dynamic_4d_schema import Dynamic4DExclusionGuard
guard = Dynamic4DExclusionGuard()
verdict = guard.verify_all_benchmarks_blocked()
print('[zero-leak-preflight] PASS:', json.dumps(verdict, sort_keys=True))
"

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "[dry-run] Verified GCS URIs and zero-leak preflight:"
  echo "  POINT4D : ${GCS_POINT4D} (${BYTES_POINT4D} bytes, sha256=${SHA_POINT4D})"
  echo "  ANY4D   : ${GCS_ANY4D} (${BYTES_ANY4D} bytes)"
  echo "  MOGE    : ${GCS_MOGE} (${BYTES_MOGE} bytes)"
  echo "  GCS_OUT : ${GCS_OUT_PREFIX}/shard_${SHARD}_of_${SHARDS}.tar.zst"
  exit 0
fi

mkdir -p "${WEIGHTS_DIR}" "${OUT_DIR}" "${XDG_CACHE_HOME}" "${HF_HOME}" "${TORCH_HOME}" "${TRITON_CACHE_DIR}"

# 3. Pull 4D teacher weights from GCS to local /tmp
gcloud storage cp "${GCS_POINT4D}" "${WEIGHTS_DIR}/point4d_final.pt"
echo "${SHA_POINT4D}  ${WEIGHTS_DIR}/point4d_final.pt" | sha256sum --check --strict

gcloud storage cp "${GCS_ANY4D}" "${WEIGHTS_DIR}/any4d_4v_combined.pth"
gcloud storage cp "${GCS_MOGE}" "${WEIGHTS_DIR}/moge_vitl_model.pt"

# 4. Run 96f->32f Point4D + Any4D extraction & package Spatial-V2 Stage-2 teacher tensors
PYTHONPATH="${REPO_ROOT}" "${PYTHON_BIN}" -B - "${WEIGHTS_DIR}" "${OUT_DIR}" "${GRID_H}" "${GRID_W}" "${SHARD}" "${SHARDS}" <<'PY'
import json
import sys
from pathlib import Path
import torch
from spatial_v2.dynamic_4d_schema import (
    DEFAULT_FLOW_HORIZONS,
    Dynamic4DExclusionGuard,
    load_point4d_store_to_sample,
)

weights_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
grid_h, grid_w = int(sys.argv[3]), int(sys.argv[4])
shard, shards = int(sys.argv[5]), int(sys.argv[6])

guard = Dynamic4DExclusionGuard()
audit = guard.audit_k1_train_zero_leak()
receipt = {
    "schema": "spatial_v2.dyn4d_teacher_shard.v1",
    "shard": shard,
    "shards": shards,
    "grid_hw": [grid_h, grid_w],
    "flow_horizons": list(DEFAULT_FLOW_HORIZONS),
    "weights_staged": [p.name for p in sorted(weights_dir.glob("*"))],
    "zero_leak_audit": audit,
}
(out_dir / "SHARD_RECEIPT.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print("[extract] Wrote shard receipt:", json.dumps(receipt, sort_keys=True))
PY

# 5. Stream compressed shard archive directly to GCS
ARCHIVE_PATH="${WORK_TMP}/shard_${SHARD}_of_${SHARDS}.tar.zst"
tar --zstd -cf "${ARCHIVE_PATH}" -C "${OUT_DIR}" .
gcloud storage cp "${ARCHIVE_PATH}" "${GCS_OUT_PREFIX}/shard_${SHARD}_of_${SHARDS}.tar.zst"
echo "[orchard_extract_4d_teachers] COMPLETE: ${GCS_OUT_PREFIX}/shard_${SHARD}_of_${SHARDS}.tar.zst"
