#!/bin/bash
set -eu
export PYTHONDONTWRITEBYTECODE=1
ROOT="$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")"
PY="$1"
shift
exec "$PY" -B -s "$ROOT/b/u.py" "$@"
