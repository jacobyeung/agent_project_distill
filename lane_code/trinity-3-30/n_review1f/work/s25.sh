W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; P=$W/w24t/work/build24m4o/p_tree; ls $P | head; ls $P/student_pilot | wc -l
ls $P/student_pilot/extent_receipt.py 2>&1; grep -n -i "extent" $P/student_pilot/*.py | head -20
sed -n 1068,1085p $P/student_pilot/carrier_c1_run.py; grep -n "def row" $P/student_pilot/carrier_c1_run.py
