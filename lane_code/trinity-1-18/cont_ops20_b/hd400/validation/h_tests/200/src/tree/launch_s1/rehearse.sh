#!/bin/bash
set -euo pipefail
ulimit -f 204800
ROOT="${1:?kit root}"
MODE="${2:?p, c, t, u or x}"
PYTHON="${S1_PYTHON:-/scratch/jjyeung/envs/p1cpu/bin/python}"
export CUDA_VISIBLE_DEVICES=''
export S1_REHEARSAL_ATTEMPT="${S1_REHEARSAL_ATTEMPT:-cpu_$$}"
exec "$PYTHON" -B "$ROOT/b/i.py" "$ROOT" "$MODE" 0
