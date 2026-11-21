#!/bin/bash
# Copy of the kit's b/e.sh; the only difference: the rank script is u2.py beside this file.
set -eu
export PYTHONDONTWRITEBYTECODE=1
HERE="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
PY="$1"
shift
exec "$PY" -B -s "$HERE/u2.py" "$@"
