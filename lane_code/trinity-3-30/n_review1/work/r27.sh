ls /scratch/jjyeung/orch_n30/sb_framepool /scratch/jjyeung/orch_n30/sb_framepool/* 2>/dev/null | head -40
find /scratch/jjyeung/orch_n30/sb_framepool /scratch/jjyeung/orch_n30/sb_fprev /scratch/jjyeung/n30_mirror -maxdepth 5 \( -name '*.sqlite' -o -name '*.db' \) -size +1M -printf '%p %s\n' 2>/dev/null | head -20
T=/scratch/jjyeung/orch_n30/n_review/tree
grep -n "class PoseMix\|def row(\|'pose'\|\"pose\"" $T/student_pilot/carrier_c1_run.py | head -40
grep -rn "pose_targets\|def pose_row\|stream=='pose'\|stream == 'pose'" $T/student_pilot/*.py | head -20
