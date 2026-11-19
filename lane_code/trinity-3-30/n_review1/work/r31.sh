T=/scratch/jjyeung/orch_n30/n_review/tree
grep -rn "regenerated_sha256\|routing_selection" --include=*.py $T/student_pilot $T/launch_r1 | grep -v /tests/ | head -30
ls /scratch/jjyeung/orch_n30/tree_rebuild10_w/work/x24j_back 2>&1 | head
