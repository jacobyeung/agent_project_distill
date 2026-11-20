#!/usr/bin/env bash
# CPU-only reconstruction and registered scoring; all outputs stay in W.
set -euo pipefail
cd /scratch/jjyeung/orch_n30/anchor_kill1
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export CUDA_VISIBLE_DEVICES=''
export XDG_CACHE_HOME="$PWD/cache" HF_HOME="$PWD/cache/hf" TRITON_CACHE_DIR="$PWD/cache/triton"
anchor_python=/scratch/jjyeung/orch_n30/sb_ph2fix/payload/environment/bin/python
"$anchor_python" k1_adapter.py > k1_run.log 2>&1
"$anchor_python" k1_summarize.py > k1_summary.log 2>&1
