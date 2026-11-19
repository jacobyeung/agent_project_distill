#!/usr/bin/env bash
set -euo pipefail
date -u
kit_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false
control_python="${READ228_CONTROL_PYTHON:-/scratch/jjyeung/b01ec87a6f29b/d/v/py}"
exec nice -n 10 "$control_python" -B -I "$kit_dir/runner228.py" "$@"
