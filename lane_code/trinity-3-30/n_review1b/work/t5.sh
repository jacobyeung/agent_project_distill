T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1
wc -c $T/student_pilot/r2_scene_bindings.py $T/student_pilot/r2_contract.py $T/student_pilot/r1_rooms.py
cat $T/student_pilot/r2_scene_bindings.py
echo "=== r2_contract 55-90"; sed -n 55,90p $T/student_pilot/r2_contract.py
