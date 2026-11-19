#!/usr/bin/env bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/sb_ph2gate
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
nice -n 10 tar --exclude='*.tar' --exclude='*.tar.sha256' \
  --exclude='__pycache__' --exclude='*.pyc' --exclude='.cache' --exclude='tmp' \
  --exclude='sb_mask_phrase/work/gate_tests' \
  -cf out/sb_ph2gate.tar STATUS.md verify_cpu.py write_report.py package.sh sb_mask_phrase out
sha256sum out/sb_ph2gate.tar > out/sb_ph2gate.tar.sha256
