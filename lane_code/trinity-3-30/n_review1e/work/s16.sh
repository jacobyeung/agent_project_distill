T=/scratch/jjyeung/orch_n30/n_review/r1e/tcpp; cd $T
grep -n "row\|def \|item" student_pilot/r1_routing.py | head -80
echo ====; grep -n "def row\b\|def row(" -A45 student_pilot/carrier_c1_run.py | head -80
