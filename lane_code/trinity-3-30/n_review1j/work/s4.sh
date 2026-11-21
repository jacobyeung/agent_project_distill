T=/scratch/jjyeung/orch_n30/n_review/r1j/t; C=$T/student_pilot
n=$(grep -n "^def ancestor_admits" $C/c1_pose_mix.py < /dev/null | cut -d: -f1); echo "== ancestor_admits $n"; sed -n "${n},$((n+40))p" $C/c1_pose_mix.py < /dev/null
echo "== division in c1_pose_mix"; grep -n "division" $C/c1_pose_mix.py < /dev/null | head -40
echo "== ROUTING_SCHEMA"; grep -rn "ROUTING_SCHEMA *=" $C/*.py < /dev/null
echo "== git-free: who writes vqa c1-stream-v1 with division"; grep -ln "c1-stream-v1" $C/*.py $T/launch_*/*.py < /dev/null 2>/dev/null
