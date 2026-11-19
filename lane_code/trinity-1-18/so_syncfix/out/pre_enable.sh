#!/bin/bash
# Saved owner script. Invoke with: bash -eu /path/to/so_syncfix/pre_enable.sh
date -u
export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1
S=${S:-/scratch/jjyeung/distill_sync}
PYTHON=${LCS_OWNER_PYTHON:-/usr/bin/python3}
PKG=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
[ "$(hostname -s)" = trinity-3-30 ] || { echo 'PRE-ENABLE REFUSED: wrong host' >&2; exit 2; }
nice -n 10 "$PYTHON" -I -s -B "$PKG/owner_checks.py" pre-enable "$S/sync.log"
date -u
