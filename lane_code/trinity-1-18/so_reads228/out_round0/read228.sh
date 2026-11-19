#!/usr/bin/env bash
set -euo pipefail
date -u
if [[ $# -ne 2 ]]; then
  echo 'Usage: read228.sh <A4 root or package> <card>' >&2
  exit 2
fi
kit_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false
control_python="${READ228_CONTROL_PYTHON:-/scratch/jjyeung/envs/p1cpu/bin/python}"
exec nice -n 10 "$control_python" -I -s -B "$kit_dir/read228.py" "$1" "$2"
