#!/usr/bin/env bash
# An already allocated production host only. Native admission remains mandatory.
set -euo pipefail
date -u
: "${TREE:?Set TREE to the sealed reviewed trainer checkout}"
: "${CONFIG:?Set CONFIG to its admitted runtime configuration}"
: "${OUT:?Set OUT to a fresh scratch directory}"
KIT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
export PYTHONDONTWRITEBYTECODE=1
# Inherit all production thread settings; torchrun records its effective defaults.
args=(--tree "$TREE" --config "$CONFIG" --out "$OUT" --mode profile)
if [[ -n ${RESUME_PIN:-} ]]; then args+=(--resume "$RESUME_PIN"); fi
if [[ -n ${RESUME_CONFIG:-} ]]; then args+=(--resume-config "$RESUME_CONFIG"); fi
# One instrumented step, no separate warmup. Heartbeats and partial phases survive
# the deadline. Exit 124 means INCOMPLETE. Never retry a killed allocation.
nice -n 10 timeout --signal=TERM --kill-after=5s 895s "${PYTHON:-python}" -m torch.distributed.run \
  --standalone --nproc_per_node=4 "$KIT/launch.py" "${args[@]}" 2>&1 | \
  "${PYTHON:-python}" "$KIT/privacy.py"
