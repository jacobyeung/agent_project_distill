C=/scratch/jjyeung/orch_n30/n_review/r1j/t/student_pilot
grep -n "def settings" -A14 $C/ground_target_filter.py < /dev/null | head -30
grep -n "def __init__" -A10 $C/ground_target_filter.py < /dev/null | head -14
