#!/bin/bash
# sb_f64fix3 checks after the kit tests, one at a time; each log goes to out/fix3/<name>.log.
set -u
W=/scratch/jjyeung/orch_n30/sb_f64fix3
O="$W/out/fix3"
cd "$W"
step() { local name=$1; shift; "$@" > "$O/$name.log" 2>&1; echo "$name exit=$?" | tee -a "$O/checks.log"; }
step old_token_audit bash work/scripts/run_fix.sh -m unittest -v work/oldaudit_check/kit/tests/test_pilot_gate.py
step pilot_gate_matrix bash work/review3/run_cpu.sh pilot_gate_matrix.py
step builder_matrix bash work/review3/run_cpu.sh builder_matrix.py
step mutation_check bash work/review3/run_cpu.sh mutation_check.py
step kit_check bash work/review3/run_cpu.sh kit_check.py
step regress_baseline env F64_OUT="$O" bash work/regress/run_regress.sh regression_check.py baseline
step regress_patched env F64_OUT="$O" bash work/regress/run_regress.sh regression_check.py patched
