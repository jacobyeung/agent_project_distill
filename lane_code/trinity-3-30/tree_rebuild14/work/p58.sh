T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1; R=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24f/rehearsal3
grep -rn "COMPONENT_EVIDENCE_PREPARATION_MISMATCH" $T/student_pilot $T/launch_r1 $T/launch_r2 </dev/null | cut -c1-200 | head -5
grep -B30 "COMPONENT_EVIDENCE_PREPARATION_MISMATCH" $R/train_fresh.log | grep -E "File|line" | grep -v site-packages | tail -8 | cut -c1-220
