#!/bin/bash
# Read-only counts. LCS_ENABLE_DRY_COUNT=1 enables this command; default OFF.
set -euo pipefail
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false
exec nice -n 10 "${LCS_PYTHON:-python3}" -I -s -B "$(dirname -- "$0")/dry_count.py" "$@"
