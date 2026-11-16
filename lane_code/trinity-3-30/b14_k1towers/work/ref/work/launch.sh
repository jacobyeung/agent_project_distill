#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$(realpath -- "${BASH_SOURCE[0]}")")/kit_env.sh"
arm="${1:?arm required}"
shift
python="$GEO_BAKEOFF_ROOT/runtime/base/bin/python3"
exec "$python" "$GEO_BAKEOFF_ROOT/work/run_arm.py" --arm "$arm" "$@"
