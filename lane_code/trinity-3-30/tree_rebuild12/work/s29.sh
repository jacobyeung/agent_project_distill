T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/work/tree_r1; cd $T
wc -l launch_r1/p_handover_receipt.py; grep -n "def \|schema\|SLURM\|hostname\|nsenter\|mode\|environ\|getpid\|job" launch_r1/p_handover_receipt.py | head -40 | cut -c1-200
grep -rn "p-handover\|handover_receipt" --include=*.py student_pilot launch_r1 | grep -v test | head -15 | cut -c1-200
