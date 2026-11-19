#!/bin/bash
set -eu
exec nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 XDG_CACHE_HOME="$PWD/.cache" /scratch/jjyeung/envs/p1cpu/bin/python "$@"
