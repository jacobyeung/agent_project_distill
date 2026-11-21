W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; T=/scratch/jjyeung/orch_n30/n_review/r1f/tcpx
date -u +%TZ
cat $W/work/d173881/173881/routing_types.json < /dev/null; echo
n=$(grep -n 'def check_plan_rows' $T/student_pilot/carrier_c1_run.py < /dev/null | cut -d: -f1); echo "check_plan_rows at $n"; sed -n "${n},$((n+110))p" $T/student_pilot/carrier_c1_run.py < /dev/null | cut -c1-260
ls $W/w24z14/out < /dev/null 2>&1 | head; ls $W/w24z15/out < /dev/null 2>&1 | head
