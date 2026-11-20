#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ $# -lt 1 || ! "$1" =~ ^[0-9]+$ ]]; then
  echo 'Usage: bash run_funnel.sh GPU_INDEX [--dry-run] [MANIFEST.json]' >&2
  exit 2
fi
gpu="$1"
shift
# CPU preflight never imports torch or touches a GPU.
exec /usr/bin/python3 -s preflight.py --gpu "$gpu" "$@"
