#!/usr/bin/env bash
set -euo pipefail
L=/scratch/jjyeung/orch_n30/so_modep
cd "$L"
source "$L/work/env.sh"
export MODEP_RUN_GLOO=1
export MODEP_TEST_LABEL="gloo_$(date -u +%Y%m%dT%H%M%SZ)"
exec nice -n 10 taskset -c 0-7 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$L/work/run_native_tests.py" tests.test_modep_gloo tests.test_s1_checkpoint_buffers
