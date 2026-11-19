T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/work/tree_r1; cd $T
sed -n '8,104p' launch_r1/p_handover_receipt.py | cut -c1-260; sed -n '45,80p' student_pilot/r1_persisted.py | cut -c1-260
