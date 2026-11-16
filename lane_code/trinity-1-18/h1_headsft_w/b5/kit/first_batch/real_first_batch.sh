#!/bin/bash
# Unrun entry point. Every referenced asset must already be staged on this CPU node.
set -euo pipefail
K=/scratch/jjyeung/orch_n30/h1_headsft/kit
if [[ $# -lt 5 || $# -gt 6 || ( $# -eq 6 && "$6" != --force-pose-own ) ]]; then
  echo "Usage: bash $0 CONFIG LOCAL_MODEL_MANIFEST LOCAL_PREPARATION_RECEIPT STEP544_ARTIFACT OUTPUT_IN_K [--force-pose-own]" >&2
  exit 2
fi
exec bash "$K/cpu.sh" "$K/first_batch/real_first_batch.py" --config "$1" --manifest "$2" --receipt "$3" --artifact "$4" --output "$5" --world 4 "${@:6}"
