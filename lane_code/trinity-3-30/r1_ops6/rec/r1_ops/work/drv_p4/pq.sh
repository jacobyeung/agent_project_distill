#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
O=/project/community/jjyeung/okh7
BUN=$O/i_69d2930d
H=$O/x_3fdda0fb
OLD=$O/i_1be16f28
KH=$O/x_69d2930d
private() { [[ -d "$1" && ! -L "$1" && $(stat -c %a "$1") == 700 ]] || { echo "REFUSED: private directory required: $1" >&2; exit 3; }; }
fresh() { [[ ! -e "$1" && ! -L "$1" ]] || { echo "REFUSED: already exists: $1" >&2; exit 3; }; }
private "$O"
squeue -u "$USER" -o '%i|%j|%P|%T|%M|%R'
