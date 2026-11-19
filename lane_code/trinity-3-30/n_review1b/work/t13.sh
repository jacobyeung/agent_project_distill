T=/scratch/jjyeung/orch_n30/n_review/r1b/t3/work/tree_r1
sed -n 328,362p $T/student_pilot/r1_handover.py
echo "### pinned"; grep -n "^def pinned" -A14 $T/student_pilot/p3_provenance.py
