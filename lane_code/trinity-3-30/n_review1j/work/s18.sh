F=/scratch/jjyeung/orch_n30/n_review/r1j/t/student_pilot/r2_scene_bindings.py; sed -n 198,227p $F < /dev/null
T=/scratch/jjyeung/orch_n30/n_review/r1j/t; grep -rn "r2_scene_rebuild" $T/student_pilot/*.py $T/launch_r1/*.py < /dev/null | cut -c1-200 | head -20
