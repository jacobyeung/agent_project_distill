X=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/x24j_back/work/tree_r1; date -u +%TZ
sed -n 80,180p $X/launch_r1/production_proof.py
echo ==== entry 150-230; sed -n 150,230p $X/launch_r1/entry.py
echo ==== s1_routing 465-490; sed -n 465,490p $X/student_pilot/s1_routing.py 2>/dev/null || ls $X
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24; ls -t $W/work | head; ls $W/work/build24k 2>/dev/null | head -50 | tr '\n' ' '
tail -3 $W/work/build24f/rehearsal_run4.log
