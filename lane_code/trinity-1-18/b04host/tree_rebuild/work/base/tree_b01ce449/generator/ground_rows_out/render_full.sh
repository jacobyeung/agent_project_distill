#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 RAYON_NUM_THREADS=1
export TOKENIZERS_PARALLELISM=false
export PYTHONPATH="$HERE:$HERE/../work/derivgen_v7"
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B "$HERE/render_full.py" "$@"
