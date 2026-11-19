#!/usr/bin/env bash
set -euo pipefail
date -u
test_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$test_dir/test_kit.py"
date -u
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$test_dir/test_review.py"
date -u
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$test_dir/test_prepare.py"
date -u
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$test_dir/test_bootstrap36.py"

date -u
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$test_dir/test_review2.py"
date -u
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$test_dir/test_stage2.py"
