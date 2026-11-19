T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/work/tree_r1; cd $T
grep -rn "routing_inputs\|NATIVE_ROUTING_REQUIRED" --include=*.py launch_r1 student_pilot | grep -v tests | head -20 | cut -c1-240
grep -rn "host_envelope\|def build_host\|envelope" --include=*.py student_pilot launch_r1 | grep -v tests | head -12 | cut -c1-200
