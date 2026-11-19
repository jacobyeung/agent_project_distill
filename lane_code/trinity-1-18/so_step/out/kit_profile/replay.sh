#!/usr/bin/env bash
# Disposable continuation acceptance on the already admitted four-GPU host.
set -euo pipefail
date -u
: "${TREE:?Set TREE to the sealed reviewed tree}"
: "${CONFIG:?Set CONFIG to its admitted configuration}"
: "${RESUME_PIN:?Pin the exact continuation checkpoint manifest, never latest}"
: "${PLAN:?Set PLAN to the audited 10-update continuation plan}"
: "${AUDIT_DIR:?Set AUDIT_DIR to the eight completed CPU audits}"
: "${OUT:?Set OUT to a fresh scratch directory}"
: "${PYTHON:?Set PYTHON to the production Python interpreter}"
KIT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
export PYTHONDONTWRITEBYTECODE=1
for leg in off1:off off2:off on:prefetch; do
  name=${leg%%:*}
  arm=${leg##*:}
  date -u
  args=(--tree "$TREE" --config "$CONFIG" --out "$OUT/$name" --mode replay
        --resume "$RESUME_PIN" --plan "$PLAN" --arm "$arm" --batch-metrics "${REPLAY_METRICS:-0}")
  if [[ -n ${RESUME_CONFIG:-} ]]; then args+=(--resume-config "$RESUME_CONFIG"); fi
  nice -n 10 timeout --signal=TERM --kill-after=5s 3600s "$PYTHON" -m torch.distributed.run \
    --standalone --nproc_per_node=4 "$KIT/launch.py" "${args[@]}" 2>&1 | "$PYTHON" "$KIT/privacy.py"
done
nice -n 10 "$PYTHON" "$KIT/../kit_timing/replay_compare.py" --out "$OUT" --audit-dir "$AUDIT_DIR"
