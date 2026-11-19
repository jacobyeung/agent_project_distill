#!/usr/bin/env bash
set -euo pipefail
set -o noclobber
cd "$(dirname "${BASH_SOURCE[0]}")"
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
nice -n 10 tar --exclude='*.tar' --exclude='*.tar.sha256' \
  --exclude='__pycache__' --exclude='*.pyc' --exclude='.cache' --exclude='tmp' \
  --exclude='sb_mask_phrase/work/gate_tests' --exclude='sb_mask_phrase/work/launcher_tests' \
  --exclude='work/ph2rev_probes/replays' --exclude='work/ph2rev_probes/strace_fixed/cache' \
  -cf - STATUS.md verify_cpu.py verify_staged.py stage_payload.py \
  relocate_environment.py supplement_environment.py write_report.py package.sh sb_mask_phrase payload out work > out/sb_ph2fix2.tar
nice -n 10 sha256sum out/sb_ph2fix2.tar > out/sb_ph2fix2.tar.sha256
