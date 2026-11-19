#!/bin/bash
# Review sb_f64rev3's run_cpu.sh, rooted in this directory and bound to this workspace's kit; outputs go to ../../out/fix3.
set -eu
cd /scratch/jjyeung/orch_n30/sb_f64fix3/work/review3
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TMPDIR="$PWD/tmp" HF_HOME="$PWD/tmp/hf" XDG_CACHE_HOME="$PWD/tmp/cache"
export TORCH_HOME="$PWD/tmp/torch" TRITON_CACHE_DIR="$PWD/tmp/triton" MALLOC_ARENA_MAX=4
export PYTHONPATH=/scratch/jjyeung/orch_n30/sb_f64/work/pyext_tv
mkdir -p "$TMPDIR" ../../out/fix3
ulimit -v 39062500
export F64_TREE=/scratch/jjyeung/orch_n30/sb_f64/pkg/work/tree_f64
export F64_WORK="$PWD/tmp/dryrun" F64_CONFIG=/scratch/jjyeung/orch_n30/sb_f64fix3/kit/configs/r1_config_f64.json
export F64_META=/scratch/jjyeung/orch_n30/sb_f64/in/qwen35_9b_meta
export F64_READER_ROOT=/scratch/jjyeung/orch_n30/sb_f64fix3/work/reader_root
mkdir -p "$F64_WORK"
export PYTHONPATH="$PYTHONPATH:$F64_TREE:/scratch/jjyeung/orch_n30/sb_f64fix3/work/scripts"
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -s -B "$@"
