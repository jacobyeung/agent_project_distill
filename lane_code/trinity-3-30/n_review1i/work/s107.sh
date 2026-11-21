T=/scratch/jjyeung/orch_n30/n_review/r1f/tcpx
date -u +%TZ
sed -n 125,150p $T/student_pilot/s1_admission.py < /dev/null
echo "== production_proof 60-120"; sed -n 60,119p $T/launch_r1/production_proof.py < /dev/null
grep -n "RLIMIT\|setrlimit" $T/launch_r1/*.py $T/student_pilot/carrier_c1_run.py $T/student_pilot/s1_admission.py < /dev/null | head
