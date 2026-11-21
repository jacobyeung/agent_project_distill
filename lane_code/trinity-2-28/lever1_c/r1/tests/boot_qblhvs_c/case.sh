#!/bin/bash
ulimit -S -f 512
trap 'r=$?; printf "%s %s %s\n" "$r" "$LINENO" "${SLURM_JOB_ID:-0}" >>/scratch/jjyeung/orch_n30/lever1_c/r1/tests/boot_qblhvs_c/package/a/21' ERR
trap 'r=$?; trap - ERR EXIT; printf "%s %s %s\n" "$r" "$LINENO" "${SLURM_JOB_ID:-0}" >>/scratch/jjyeung/orch_n30/lever1_c/r1/tests/boot_qblhvs_c/package/a/21; exit "$r"' EXIT
exec >>/scratch/jjyeung/orch_n30/lever1_c/r1/tests/boot_qblhvs_c/package/a/19 2>>/scratch/jjyeung/orch_n30/lever1_c/r1/tests/boot_qblhvs_c/package/a/24
set -Eeuo pipefail
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/lever1_c/r1/tests/local_bootstrap.py parent /scratch/jjyeung/orch_n30/lever1_c/r1/tests/boot_qblhvs_c/package /scratch/jjyeung/orch_n30/lever1_c/r1/tests/boot_qblhvs_c/work /scratch/jjyeung/orch_n30/lever1_c/r1/tests/boot_qblhvs_c/pool a6f198d3c7b20 sink_start
