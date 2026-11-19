#!/usr/bin/env bash
# After the full-capture CPU run: dry-run rerun (steps 0-3, stubs, pricing, manifest, staging, tests, collation), the
# reviewer's reproduce.sh, tests and contract audits against this kit, the preflight, and a code test of mc_summary final.
set -uo pipefail
ROOT=/scratch/jjyeung/orch_n30/sb_cafix
L="$ROOT/work/v2/logs"; mkdir -p "$L"
stamp() { echo "$(date -u +%FT%TZ) $*" >> "$L/after_cpu.log"; }
stamp start
MC_DRYRUN_FULL=0 bash "$ROOT/kit_v2/dryrun.sh"; stamp "dryrun exit $?"
cd "$ROOT/review"
bash reproduce.sh; stamp "reproduce exit $?"
bash review_run.sh p1cpu tests_run.py > logs/tests.log 2>&1; stamp "review tests exit $?"
bash review_run.sh p1cpu contract_audit.py > logs/contracts.log 2>&1; stamp "contract_audit exit $?"
bash review_run.sh p1cpu contract_audit_4col.py > logs/contracts_4col.log 2>&1; stamp "contract_audit_4col exit $?"
cd "$ROOT/kit_v2"
CUDA_VISIBLE_DEVICES='' PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD" OMP_NUM_THREADS=8 \
  nice -n 10 /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python -B mc_preflight.py > "$L/preflight.log" 2>&1; stamp "preflight exit $?"
mkdir -p "$ROOT/work/v2/final_code_test"
bash run_cpu.sh p1cpu mc_summary.py final "$ROOT/out/v2/dry/price_cpu_full" "$ROOT/work/v2/final_code_test" > "$L/final_code_test.log" 2>&1
stamp "final_code_test exit $?"
stamp done
