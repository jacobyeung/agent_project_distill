#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
source scripts/env.sh
# The caller sets the authorized physical UUID and supplies the bound GO arguments.
exec /data3/shared/scripts/vnice/vnice.sh nice -n 10 "$GEO_BAKEOFF_ROOT/runtime/base/bin/python3" -B scripts/gpu_run.py --stage all "$@"
