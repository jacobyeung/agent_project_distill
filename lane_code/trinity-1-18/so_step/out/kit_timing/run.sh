#!/usr/bin/env bash
# Run only on an allocated, admitted production host. Stop on any failure.
set -euo pipefail
date -u
: "${TREE:?Set TREE to the sealed patched trainer checkout}"
: "${CONFIG:?Set CONFIG to its admitted runtime configuration}"
: "${OUT:?Set OUT to a fresh scratch comparison directory}"
: "${CUDA_CACHE_PATH:?Set the production-equivalent scratch cache path}"
: "${TRITON_CACHE_DIR:?Set the production-equivalent scratch cache path}"
: "${TORCHINDUCTOR_CACHE_DIR:?Set the production-equivalent scratch cache path}"
KIT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
export PYTHONDONTWRITEBYTECODE=1
# Inherit thread counts and tokenizer settings from the production environment.
REPEATS=${REPEATS:-3}
WARMUP=${WARMUP:-20}
MEASURE=${MEASURE:-20}
ARM_SECONDS=${ARM_SECONDS:-10800}
[[ $REPEATS =~ ^[0-9]+$ && $REPEATS -ge 3 && $REPEATS -le 30 ]]
[[ $WARMUP =~ ^[0-9]+$ && $WARMUP -ge 10 && $WARMUP -le 100 ]]
[[ $MEASURE =~ ^[0-9]+$ && $MEASURE -ge 10 && $MEASURE -le 100 ]]
[[ $ARM_SECONDS =~ ^[0-9]+$ && $ARM_SECONDS -ge 60 && $ARM_SECONDS -le 43200 ]]
mkdir "$OUT"
resume=()
if [[ -n ${RESUME_PIN:-} ]]; then resume=(--resume "$RESUME_PIN"); fi
if [[ -n ${RESUME_CONFIG:-} ]]; then resume+=(--resume-config "$RESUME_CONFIG"); fi
for ((repeat=0; repeat<REPEATS; repeat++)); do
  # Bracket each ON arm with OFF; reverse ON order on alternate repeats.
  order=(off prefetch off cache off metrics off)
  if ((repeat % 2)); then order=(off metrics off cache off prefetch off); fi
  leg=0
  for arm in "${order[@]}"; do
    label="r${repeat}_l${leg}_${arm}"
    plan=()
    if ((repeat != 0 || leg != 0)); then plan=(--plan "$OUT/r0_l0_off/rank0/plan.json"); fi
    nice -n 10 "${PYTHON:-python}" "$KIT/cache_state.py" "$OUT/${label}_cache_before.json"
    nice -n 10 timeout --signal=TERM --kill-after=10s "${ARM_SECONDS}s" \
      "${PYTHON:-python}" -m torch.distributed.run --standalone --nproc_per_node=4 \
      "$KIT/../kit_profile/launch.py" --tree "$TREE" --config "$CONFIG" --out "$OUT/$label" \
      --mode timing --arm "$arm" --warmup "$WARMUP" --measure "$MEASURE" \
      "${plan[@]}" "${resume[@]}" 2>&1 | "${PYTHON:-python}" "$KIT/../kit_profile/privacy.py"
    nice -n 10 "${PYTHON:-python}" "$KIT/cache_state.py" "$OUT/${label}_cache_after.json"
    leg=$((leg+1))
  done
  nice -n 10 "${PYTHON:-python}" "$KIT/summarize.py" "$OUT"
done
