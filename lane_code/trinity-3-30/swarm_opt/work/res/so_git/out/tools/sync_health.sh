#!/bin/bash
# Local owner monitor. LCS_ENABLE_SYNC_HEALTH=1 enables it; default OFF.
set -euo pipefail
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false
exec nice -n 10 "${LCS_PYTHON:-python3}" -I -s -B "$(dirname -- "$0")/sync_health.py" "$@"
