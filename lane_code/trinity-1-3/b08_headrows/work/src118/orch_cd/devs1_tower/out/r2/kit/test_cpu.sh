#!/usr/bin/env bash
set -euo pipefail
ulimit -f 204800
KIT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
: "${CPU_PYTHON:?node-local Python with numpy, Pillow and torch}"
: "${TEST_TMP:?temporary directory under your work/tmp}"
mkdir -p "$TEST_TMP"
export TMPDIR="$TEST_TMP" DEVS1_KIT="$KIT" CUDA_VISIBLE_DEVICES= PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
exec "$CPU_PYTHON" -B "$KIT/tests/test_devs1.py"
