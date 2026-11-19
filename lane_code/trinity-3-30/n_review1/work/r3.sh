T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1; cd $T
grep -n "^def identity" -A40 student_pilot/carrier_c1_run.py | head -70
echo ===== r1_coverage; wc -l student_pilot/r1_coverage.py; sed -n 1,200p student_pilot/r1_coverage.py
echo ===== DEFERRED refs; grep -rn "DEFERRED\|deferred(" --include=*.py . | grep -v "^./tests\|/tests/" | head -60
