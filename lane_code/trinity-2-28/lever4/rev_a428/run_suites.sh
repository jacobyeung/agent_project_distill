#!/bin/bash
cd /scratch/jjyeung/orch_n30/lever4/rev_a428/k/r1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=
PY=/scratch/jjyeung/orch_n30/lever4/rev_a428/py/p1cpu/bin/python
for t in test_all test_fixes test_failure test_import_audit test_bootstrap test_review8 test_review9 test_review10 test_review11 test_prebulk check_imports; do
  timeout 1200 nice -n 10 $PY -I -s -B tests/$t.py > ../S_$t.log 2>&1; echo "$t rc=$? $(grep -o 'Ran [0-9]* tests\?' ../S_$t.log)" >> ../SUITES.txt
done
echo done >> ../SUITES.txt
