#!/bin/bash
set -eu
export PYTHONDONTWRITEBYTECODE=1
PY="$1"
shift
exec "$PY" -B -s /tmp/a15_dbg_174134/u2.py "$@"
