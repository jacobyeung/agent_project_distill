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
    "$@" > "$T/$name.log" 2>&1
    printf '%s: exit 0\n' "$name"
    tail -n 4 "$T/$name.log"
}
run_check patch2_guard_sam3 env K1_GUARD_TEST_RUN=patch2_unit_sam3 "$SAM" -I -s -B "$W/test_k1_guard.py"
cp "$T/guard_coverage.json" "$T/guard_coverage_patch2_sam3.json"
run_check patch2_guard_p1cpu env K1_GUARD_TEST_RUN=patch2_unit_p1cpu "$P1" -I -s -B "$W/test_k1_guard.py"
cp "$T/guard_coverage.json" "$T/guard_coverage_patch2_p1cpu.json"
run_check patch2_forge "$P1" -I -s -B "$T/rev_forge.py"
run_check patch2_identity "$SAM" -I -s -B "$T/verify_identity.py"
run_check patch2_test_kit "$SAM" -I -s -B "$T/run_existing.py" test_kit
run_check patch2_test_guards "$SAM" -I -s -B "$T/run_existing.py" test_guards
run_check patch2_verify_sources "$SAM" -I -s -B "$W/verify_sources.py"
run_check patch2_verify_sources_p1cpu "$P1" -I -s -B "$W/verify_sources.py"
bash -n ../kc_guard_brief/convert7.guard.sh
bash -n ../kc_guard_brief/k1_downstream.guard.sh
printf 'Launcher syntax: exit 0\n'
