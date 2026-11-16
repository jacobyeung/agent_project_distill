#!/usr/bin/env bash
set -euo pipefail
if [[ $# != 3 ]]; then
  printf '%s\n' 'Usage: submit_train_ao.sh <setH|setH_e1|fullpool|setH_mb4> <dataset_root> <run_id>' >&2
  exit 2
fi
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
variant="$1"; dataset="$2"; run_id="$3"
case "$variant" in setH|setH_e1|fullpool|setH_mb4) ;; *) echo 'Unknown answer-only variant' >&2; exit 2;; esac
[[ "$dataset" == /* ]] || { echo 'Use an absolute Orchard dataset root' >&2; exit 2; }
[[ "$run_id" =~ ^[A-Za-z0-9][A-Za-z0-9_-]{0,100}$ ]] || { echo 'Use a plain unique run identifier' >&2; exit 2; }
export ORCH="${ORCH:-/project/community/jjyeung/distill}"
export ORCH_BASE_DEPLOY="${ORCH_BASE_DEPLOY:-$ORCH/code/deployment_433d8a1}"
export ORCH_DEPLOY="${ORCH_AO_DEPLOY:-$ORCH/code/deployment_433d8a1_ao27b_${variant}_${run_id}}"
export TRAINER="${TRAINER:-${TRAIN_CODE:-$ORCH/code/orchard_trainer_433d8a1}}"
export TRAINER_COMMIT="${TRAINER_COMMIT:-${TRAIN_COMMIT:-433d8a117bf94bcd8214de9a6d6e149ff6f5f74f}}"
export MODEL_MANIFEST="${MODEL_MANIFEST:-$ORCH/incoming/model_sha256_meta.json}"
export STUDENT_FRAME_ROOT_MAP="${STUDENT_FRAME_ROOT_MAP:-/data2=$ORCH/data2root}"
export PARTITION="${PARTITION:-advanced}" QOS="${QOS:-adv_4gpu_qos}" WORLD_SIZE="${WORLD_SIZE:-4}"
export PARALLEL="${PARALLEL:-fsdp}" CHECKPOINT_EVERY_STEPS="${CHECKPOINT_EVERY_STEPS:-25}"
export STUDENT=qwen36_27b PYTHONDONTWRITEBYTECODE=1
case "$variant" in
  setH|setH_e1|setH_mb4) default_split="$(dirname -- "$dataset")/mix_v25_roomfix_answeronly_20260923/split_trainer.json";;
  fullpool) default_split="$dataset/split_trainer.json";;
esac
export SPLIT_RECORD="${SPLIT_RECORD:-$default_split}"
args=(--account=mt01 --nodes=1 --partition="$PARTITION" --qos="$QOS" --gres="gpu:$WORLD_SIZE" --export=ALL)
case "$PARTITION:$QOS:$WORLD_SIZE" in
  preempt:preempt_qos:8) args+=(--requeue --time=2-00:00:00 --cpus-per-task=64 --mem=512G);;
  advanced:adv_4gpu_qos:4) args+=(--no-requeue --time=1-00:00:00 --cpus-per-task=32 --mem=384G);;
  *) echo 'Use 8/preempt/preempt_qos or 4/advanced/adv_4gpu_qos' >&2; exit 2;;
esac
[[ -z "${DEPENDENCY:-}" ]] || args+=(--dependency="$DEPENDENCY")
[[ "$TRAINER_COMMIT" == 433d8a117bf94bcd8214de9a6d6e149ff6f5f74f ]] || { echo 'Keep the 433d8a1 trainer pin' >&2; exit 2; }
[[ "$PARALLEL" == fsdp && "$CHECKPOINT_EVERY_STEPS" == 25 && "${SMOKE_TRAIN:-0}" != 1 ]] || { echo 'Keep the matched FSDP recipe; smoke is not this stage' >&2; exit 2; }
: "${ROOMFIX_GATE:?Set the existing dataset review verdict path}"
: "${STAGE_MODEL_REVIEWED_SHA256:?Review Orchard stage_model.py for qwen36_27b and export its SHA256}"
[[ -f "$MODEL_MANIFEST" ]] || { echo 'The transferred model manifest is missing' >&2; exit 2; }
head=$(git -C "$TRAINER" rev-parse HEAD)
dirty=$(git --no-optional-locks -C "$TRAINER" status --porcelain --untracked-files=normal)
[[ "$head" == "$TRAINER_COMMIT" && -z "$dirty" ]] || { echo 'The trainer pin differs or the checkout is dirty' >&2; exit 2; }
[[ ! -e "$ORCH/runs/$run_id/publication/PUBLISHED.json" ]] || { echo 'This run is already published; use a new run ID' >&2; exit 5; }
"${STAGE_PYTHON:-python3}" -B "$here/scripts/prepare_deployment.py" \
  --variant "$variant" --base-deploy "$ORCH_BASE_DEPLOY" --deploy "$ORCH_DEPLOY" \
  --dataset-root "$dataset" --split-record "$SPLIT_RECORD" --run-id "$run_id" \
  --stage-model-reviewed-sha256 "$STAGE_MODEL_REVIEWED_SHA256"
printf 'student=%s variant=%s deployment=%s publication=%s\n' "$STUDENT" "$variant" "$ORCH_DEPLOY" "$ORCH/runs/$run_id/publication/"
if [[ "${PREPARE_ONLY:-0}" == 1 ]]; then
  exit 0
fi
if [[ "${DRY:-0}" == 1 ]]; then
  exec sbatch --test-only "${args[@]}" "$ORCH_DEPLOY/slurm/train_qwen36_27b.slurm" "$dataset" "$run_id"
fi
exec bash "$ORCH_DEPLOY/scripts/orchard/submit_train.sh" qwen36_27b "$dataset" "$run_id"
