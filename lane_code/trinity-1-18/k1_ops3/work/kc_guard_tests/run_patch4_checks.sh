#!/usr/bin/env bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export K1_NATIVE_KIT=/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit
T=/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests
W=$PWD/k1_build/work/kit_k1a/work
export XDG_CACHE_HOME="$T/runtime_cache" HF_HOME="$T/runtime_cache/hf" TRITON_CACHE_DIR="$T/runtime_cache/triton"
export K1_CANARY_ROOT=canary_patch2
SAM=/scratch/jjyeung/envs/sam3_scipy_ovl/bin/python
P1=/scratch/jjyeung/envs/p1cpu/bin/python
run_check() {
    local name=$1
    shift
    printf 'Starting %s\n' "$name"
    nice -n 10 "$@" > "$T/$name.log" 2>&1
    printf '%s: exit 0\n' "$name"
    tail -n 4 "$T/$name.log"
}
run_check patch4_json_bound "$P1" -I -s -B "$T/test_k1_json_bound.py"
run_check patch4_full_tables "$P1" -I -s -B "$T/run_patch4_tables.py"
run_check patch4_guard_sam3 env K1_GUARD_TEST_RUN=patch4_unit_sam3 "$SAM" -I -s -B "$W/test_k1_guard.py"
run_check patch4_guard_p1cpu env K1_GUARD_TEST_RUN=patch4_unit_p1cpu "$P1" -I -s -B "$W/test_k1_guard.py"
run_check patch4_canvas env K1_CANVAS_TEST_RUN=patch4_canvas "$P1" -I -s -B "$T/test_k1_canvas.py"
run_check patch4_identity "$SAM" -I -s -B "$T/verify_identity.py"
run_check patch4_test_kit "$SAM" -I -s -B "$T/run_existing.py" test_kit
run_check patch4_test_guards "$SAM" -I -s -B "$T/run_existing.py" test_guards
run_check patch4_verify_sources "$P1" -I -s -B "$W/verify_sources.py"
bash -n ../kc_guard_brief/convert7.guard.sh
bash -n ../kc_guard_brief/k1_downstream.guard.sh
printf 'Launcher syntax: exit 0\n'
