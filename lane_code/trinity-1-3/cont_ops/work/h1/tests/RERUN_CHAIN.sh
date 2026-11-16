#!/bin/bash
set -euo pipefail
umask 077
H="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
[[ "$(hostname -s)" == trinity-1-3 ]] || { echo 'Run on trinity-1-3.' >&2; exit 3; }
[[ ! -e "$H/chain_r1" ]] || { echo 'chain_r1 already exists; preserve it and inspect its results. No rerun.' >&2; exit 3; }
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
exec /scratch/jjyeung/envs/p1cpu/bin/python -B "$H/tests/review/prepare_chain.py"
