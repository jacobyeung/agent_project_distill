#!/usr/bin/env bash
# CPU startup pre-stage inside the image (lane startup_cpu_prestage). For each frozen preparation the spec names,
# prestage.py build runs the trainer's own startup verification once and writes the ready cache that the chained GPU
# job attaches; a preparation whose cache already exists returns at once. The environment matches mn_train_inner.sh,
# so both compute the same cache key.
# Spec field: "prestage": [FROZEN_NAME, ...]
set -euo pipefail
: "${ANYHOST_JOBS:?}" "${ANYHOST_SPEC:?}" "${R1_MOUNT:?}" "${R1_TRAINER:?}"
bash "$ANYHOST_JOBS/venv_build.sh" > /dev/null  # prints the receipt when the environment already exists
root="$R1_MOUNT/runs/aws128p_20261025"
export TRAINER="$R1_TRAINER" PILOT_VENV="$R1_MOUNT/venvs/rwtrain_torch211_cu129"
export PATH="$ANYHOST_JOBS/provenance_bin:$PILOT_VENV/bin:/usr/bin:/bin"
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 PYTHONPATH="$ANYHOST_JOBS/site_alias"
export STUDENT_ORCHARD=1 STUDENT_SLURM_SITE=code-aws CUDA_VISIBLE_DEVICES=
export STUDENT_MODEL_ROOT="$root/models"
export STUDENT_FRAME_ROOT_MAP="{\"/data2\": \"$R1_MOUNT/data2root\"}"
export HF_HOME="$root/cache/huggingface" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false STUDENT_IO_THREADS=8
export ANYHOST_NEUTRAL_RUNTIME="${R1_RUNTIME_RECORD:-$R1_MOUNT/anyhost/NEUTRAL_RUNTIME.json}"  # spec may name its tree's record
export R1_STUDENT_HEX="${R1_STUDENT_HEX:-}"  # from the spec (entry.sh); empty means the default student
test "$(command -v git)" = "$ANYHOST_JOBS/provenance_bin/git"
cd "$TRAINER"
mapfile -t names < <(python -I -c 'import json, sys; print("\n".join(json.load(open(sys.argv[1])).get("prestage", [])))' \
    "$ANYHOST_SPEC" | sed '/^$/d')
(( ${#names[@]} ))
for name in "${names[@]}"; do
    [[ "$name" =~ ^[A-Za-z0-9_]+$ && -d "$root/frozen/$name" ]]
    printf '%s | prestage %s\n' "$(date -u +%FT%TZ)" "$name"
    python -B "$ANYHOST_JOBS/prestage.py" build "$root/frozen/$name"
done
printf '%s | prestage complete\n' "$(date -u +%FT%TZ)"
