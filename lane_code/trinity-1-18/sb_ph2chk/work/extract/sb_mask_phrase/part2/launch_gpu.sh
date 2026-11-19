#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export OPENSSL_CONF="$PWD/../payload/environment/ssl/openssl.cnf" PATH=/usr/bin:/bin
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
unset PYTHONPATH PYTHONHOME
exec nice -n 10 "$PWD/../payload/environment/bin/python" -B part2/launch_gpu.py "$@"
