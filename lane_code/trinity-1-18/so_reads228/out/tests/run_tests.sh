#!/usr/bin/env bash
set -euo pipefail
date -u
test_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false
export READ228_TEST_WORK="${READ228_TEST_WORK:-/scratch/jjyeung/orch_n30/so_reads228/work/round3/test_runs}"
export READ228_CONTROL_ROOT="$READ228_TEST_WORK/control"
source "$test_dir/../control_environment228.sh"
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
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$test_dir/test_stage2.py"

date -u
# Bare control path: do not let p1cpu site-packages hide missing operator imports.
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -S -B "$test_dir/test_review3.py"
