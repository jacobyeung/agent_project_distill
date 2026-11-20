T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24c/work/tree_r1; cd $T; date -u +%TZ
sed -n 380,495p student_pilot/s1_routing.py
echo "@@@"; grep -n "direct_fail\|schema_fail\|def _direct\|direct_rows\|direct_total\|def validate_direct\|direct_schema" student_pilot/s1_routing.py | head -30
