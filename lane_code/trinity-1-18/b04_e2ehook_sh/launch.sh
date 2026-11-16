#!/bin/bash
cd /scratch/jjyeung/orch_n30/b04_e2ehook_sh/harness
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export PYTHONDONTWRITEBYTECODE=1 E3_SKIP_GT=1
export XDG_CACHE_HOME="$PWD/.cache" HF_HOME="$PWD/.cache/hf" TRITON_CACHE_DIR="$PWD/.cache/triton" MPLCONFIGDIR="$PWD/.cache/matplotlib" TMPDIR="$PWD/tmp"
date -u +%FT%TZ > ../sh_run.start
nice -n 10 /scratch/jjyeung/envs/planner_local_v1/bin/python -B sh_heldout.py ../sh_scales_heldout.json > ../sh_run.log 2>&1
echo "EXIT $?" >> ../sh_run.log; date -u +%FT%TZ > ../sh_run.end
