T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1; cd $T
grep -rn "Rooms(\|rooms.admit\|\.admit(row\|room_authority\|room_report\|reserve_withheld\|634820b4\|969cdb56\|withheld" --include=*.py student_pilot launch_r1 | grep -v "/tests/" | head -40
echo ==== room_report; grep -n "def room_report" -A40 /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/kit_n_go/b/z.py | head -60
echo ==== r1_training 100-200; sed -n 95,200p student_pilot/r1_training.py
