W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ
ls $W/w24t/work | head -40; ls -d $W/w24*/work/p_tree* $W/work/p_tree* 2>&1 | head
P=$(ls -d $W/w24t/work/p_tree* 2>/dev/null | head -1); echo "P=$P"
[ -n "$P" ] && { ls $P | head; grep -rn -i "extent" $P/student_pilot/*.py | head -20; sed -n 325,390p $P/student_pilot/s1_routing.py; sed -n 1065,1085p $P/student_pilot/carrier_c1_run.py; ls $P/student_pilot/extent_receipt.py 2>&1; }
