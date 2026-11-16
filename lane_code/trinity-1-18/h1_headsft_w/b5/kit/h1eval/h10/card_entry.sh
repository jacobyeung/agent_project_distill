#!/bin/bash
set -euo pipefail
cd "$H10_KIT"
tower_args=()
if [[ -n ${H10_TOWER_FROM:-} ]]; then tower_args=(--tower-from "$H10_TOWER_FROM"); fi
exec /scratch/jjyeung/envs/p1cpu/bin/python -B -m h1eval.h10.launch \
  --items "$H10_ITEMS" --shard "$H10_SHARD" --export "$H10_EXPORT" \
  --artifact-manifest "$H10_ARTIFACT_MANIFEST" --reader-root "$H10_READER_ROOT" \
  --arms "$H10_ARMS" --modes "$H10_MODES" --out "$H10_OUT" --device cuda:0 "${tower_args[@]}"
