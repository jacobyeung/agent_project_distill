#!/usr/bin/env bash
set -euo pipefail
ulimit -f 204800
KIT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
: "${TOWER_PYTHON:?Set TOWER_PYTHON to the node-local GPU Python executable}"
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 OPENSSL_CONF=/dev/null
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1
export PYTHONPATH="$KIT${PYTHONPATH:+:$PYTHONPATH}"
exec "$TOWER_PYTHON" -B "$KIT/devs1_run.py" "$@"
