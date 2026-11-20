R=/scratch/jjyeung/orch_n30/n_review/r1f; PY=/scratch/jjyeung/envs/p1cpu/bin/python; cd $R/tcpt || exit 1; date -u +%TZ
sed -n 100,125p student_pilot/r1_training.py; echo @@; sed -n 15,40p student_pilot/r1_launch22.py; echo @@; sed -n 70,82p student_pilot/r1_routing.py
echo "@@@ tests naming"; grep -l -E "extent_receipt|Extents|r2_intake|r1_routing" tests/*.py | head -20
