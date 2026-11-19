#!/usr/bin/env bash
# An already allocated production host only. No allocation or admission bypass.
set -euo pipefail
date -u
: "${TREE:?Set TREE to the reviewed trainer checkout}"
: "${CONFIG:?Set CONFIG to its admitted runtime configuration}"
: "${OUT:?Set OUT to a fresh scratch directory}"
KIT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false
export PYTHONDONTWRITEBYTECODE=1
args=(--tree "$TREE" --config "$CONFIG" --out "$OUT" --mode profile)
if [[ -n ${RESUME_PIN:-} ]]; then args+=(--resume "$RESUME_PIN"); fi
# Includes load/admission in the hard 15-minute budget. A cold load may exhaust it;
# exit 124 then means INCOMPLETE, not a profile result. No automatic retry.
nice -n 10 timeout --signal=TERM --kill-after=5s 895s "${PYTHON:-python}" -m torch.distributed.run \
  --standalone --nproc_per_node=4 "$KIT/launch.py" "${args[@]}"
