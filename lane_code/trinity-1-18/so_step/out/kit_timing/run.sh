#!/usr/bin/env bash
# Run once per explicitly admitted production comparison. Stops on the first error.
set -euo pipefail
date -u
: "${TREE:?Set TREE to the patched trainer checkout}"
: "${CONFIG:?Set CONFIG to the admitted runtime configuration}"
: "${OUT:?Set OUT to a fresh scratch comparison directory}"
KIT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false
export PYTHONDONTWRITEBYTECODE=1
resume=()
if [[ -n ${RESUME_PIN:-} ]]; then resume=(--resume "$RESUME_PIN"); fi
for arm in off prefetch cache metrics; do
  date -u
  plan=()
  if [[ $arm != off ]]; then plan=(--plan "$OUT/off/rank0/plan.json"); fi
  nice -n 10 "${PYTHON:-python}" -m torch.distributed.run --standalone --nproc_per_node=4 \
    "$KIT/../kit_profile/launch.py" --tree "$TREE" --config "$CONFIG" --out "$OUT/$arm" \
    --mode timing --arm "$arm" "${plan[@]}" "${resume[@]}"
done
nice -n 10 "${PYTHON:-python}" "$KIT/summarize.py" "$OUT"
