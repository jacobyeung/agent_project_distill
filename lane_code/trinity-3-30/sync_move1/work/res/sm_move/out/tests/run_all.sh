#!/bin/bash
set -euo pipefail
P=$(cd -- "$(dirname -- "$0")" && pwd)
export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
nice -n 10 /usr/bin/python3 -I -s -B "$P/test_syncmove.py"
if command -v python3.12 >/dev/null 2>&1; then
  nice -n 10 python3.12 -I -s -B "$P/test_syncmove.py"
elif command -v python3.11 >/dev/null 2>&1; then
  nice -n 10 python3.11 -I -s -B "$P/test_syncmove.py"
else
  echo 'SECOND_INTERPRETER: python3.12 and python3.11 are unavailable on PATH'
fi
