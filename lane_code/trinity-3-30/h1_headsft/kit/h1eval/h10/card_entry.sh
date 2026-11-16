#!/bin/bash
set -euo pipefail
cd "$H10_KIT"
if [[ -n ${H10_SETTINGS:-} ]]; then
  exec "${H10_PY:-/scratch/jjyeung/envs/vllm/bin/python}" -B -m h1eval.h10.host_entry
fi
tower_args=()
if [[ -n ${H10_TOWER_FROM:-} ]]; then tower_args=(--tower-from "$H10_TOWER_FROM"); fi
exec "${H10_PY:-/scratch/jjyeung/envs/vllm/bin/python}" -B -m h1eval.h10.launch \
  --items "$H10_ITEMS" --shard "$H10_SHARD" --export "$H10_EXPORT" \
  --artifact-manifest "$H10_ARTIFACT_MANIFEST" --reader-root "$H10_READER_ROOT" \
  --arms "$H10_ARMS" --modes "$H10_MODES" --out "$H10_OUT" --device cuda:0 "${tower_args[@]}"
