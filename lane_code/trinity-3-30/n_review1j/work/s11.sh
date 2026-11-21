C=/scratch/jjyeung/orch_n30/n_review/r1j/t/student_pilot
wc -l $C/s1_exclusions.py < /dev/null; sed -n 255,360p $C/s1_exclusions.py < /dev/null
echo "== run 610-630"; sed -n 610,630p $C/carrier_c1_run.py < /dev/null
