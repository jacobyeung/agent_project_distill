#!/bin/bash
# Owner runs this only when real local Git is authorized; no production repo/network is used.
set -euo pipefail
printf 'LCS_REVIEW2_FIXES=%s\n' "${LCS_REVIEW2_FIXES-<unset>}"
[ "${LCS_RUN_REAL_GIT_TESTS:-0}" = 1 ] || { echo 'REFUSED: set LCS_RUN_REAL_GIT_TESTS=1' >&2; exit 2; }
: "${LCS_REAL_GIT_WORK:?Set LCS_REAL_GIT_WORK to an existing throwaway /scratch directory}"
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false
cd "$(dirname -- "$0")/.."
exec nice -n 10 "${LCS_PYTHON:-python3}" -I -s -B -m unittest discover -s tests -p test_real_git_owner.py -v
