T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1; cd $T; date -u +%TZ
grep -rn --include=*.py -l "r2_persistence" . </dev/null | head -20
grep -rn --include=*.py "r2_persistence" launch_r2 tools scripts 2>/dev/null </dev/null | grep -v "^./tests" | head -15 | cut -c1-220
grep -rn --include=*.py "'r2_identity'" launch_r1 student_pilot/r1_*.py </dev/null | head -8 | cut -c1-200
grep -n -A12 "def requested" student_pilot/stop_control.py </dev/null | cut -c1-160 | head -20
