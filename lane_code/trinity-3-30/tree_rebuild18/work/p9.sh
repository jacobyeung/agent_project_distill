T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24c/work/tree_r1; K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24e/out/kit_qd; date -u +%TZ
sed -n 330,380p $T/student_pilot/s1_routing.py; echo "@@@RB"; cat $K/b/rb.py | head -60; echo "@@@DT"; grep -n "def direct_transform\|DIRECT_RULE =" -A25 $T/student_pilot/s1_routing.py | head -60
