#!/bin/bash
ulimit -S -f 512
trap 'r=$?; printf "%s %s %s\n" "$r" "$LINENO" "${SLURM_JOB_ID:-0}" >>/scratch/jjyeung/orch_n30/lever1_c/r1/tests/fix_fdhmbnj7/21' ERR
trap 'r=$?; trap - ERR EXIT; printf "%s %s %s\n" "$r" "$LINENO" "${SLURM_JOB_ID:-0}" >>/scratch/jjyeung/orch_n30/lever1_c/r1/tests/fix_fdhmbnj7/21; exit "$r"' EXIT
exec >>/scratch/jjyeung/orch_n30/lever1_c/r1/tests/fix_fdhmbnj7/19 2>>/scratch/jjyeung/orch_n30/lever1_c/r1/tests/fix_fdhmbnj7/24
set -Eeuo pipefail
false
