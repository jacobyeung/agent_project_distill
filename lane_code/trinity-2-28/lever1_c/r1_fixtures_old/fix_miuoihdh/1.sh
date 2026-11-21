#!/bin/bash
ulimit -S -f 512
trap 'r=$?; printf "%s %s %s\n" "$r" "$LINENO" "${SLURM_JOB_ID:-0}" >>/scratch/jjyeung/orch_n30/lever1_c/r1_fixtures_old/fix_miuoihdh/21' ERR
trap 'r=$?; trap - ERR EXIT; printf "%s %s %s\n" "$r" "$LINENO" "${SLURM_JOB_ID:-0}" >>/scratch/jjyeung/orch_n30/lever1_c/r1_fixtures_old/fix_miuoihdh/21; exit "$r"' EXIT
exec >>/scratch/jjyeung/orch_n30/lever1_c/r1_fixtures_old/fix_miuoihdh/19 2>>/scratch/jjyeung/orch_n30/lever1_c/r1_fixtures_old/fix_miuoihdh/24
set -Eeuo pipefail
false
