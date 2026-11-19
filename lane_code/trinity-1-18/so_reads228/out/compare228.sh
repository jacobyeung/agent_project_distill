#!/usr/bin/env bash
set -euo pipefail
date -u
kit_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false
control_python="${READ228_CONTROL_PYTHON:-/scratch/jjyeung/envs/p1cpu/bin/python}"
exec nice -n 10 "$control_python" -I -s -B "$kit_dir/compare228.py" "$@"
