T=/scratch/jjyeung/orch_n30/n_review/r1j/t; C=$T/student_pilot
ls $C/r2_scene_bindings.py $T/*/r2_scene_bindings.py 2>/dev/null
F=$(ls $C/r2_scene_bindings.py $T/*/r2_scene_bindings.py 2>/dev/null | head -1); wc -l $F < /dev/null
grep -n "def \|exact_rebuilt_population\|withheld_training_rows\|rows_withheld" $F < /dev/null | head -40
