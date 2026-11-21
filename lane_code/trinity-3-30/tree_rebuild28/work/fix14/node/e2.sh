#!/bin/bash
# fix14 copy of the kit's b/e.sh; the only difference: the rank script runs through uw.py (logged checks of the walk).
set -eu
export PYTHONDONTWRITEBYTECODE=1
PY="$1"
shift
exec "$PY" -B -s /tmp/a15_dbg_174134/tr/uw.py "$@"
