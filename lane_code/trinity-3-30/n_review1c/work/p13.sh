W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w24e/out/kit_n_go; T=$W/w24c/work/tree_r1
cd /tmp; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import json,base64,hashlib;v=json.load(open('$K/k/j.json'));b=base64.b64decode(v['payload']);print('J sha',hashlib.sha256(b).hexdigest(),v.get('sha256'));L=b.decode().splitlines();print(len(L))
for i in range(390,min(len(L),445)): print(i+1, L[i][:220])
"
echo "@@@ a.py"; cat -n $K/b/a.py | cut -c1-220
echo "@@@ pp"; sed -n '80,200p' $T/launch_r1/production_proof.py | cat -n | sed 's/^ *\([0-9]*\)/\1+79/' | cut -c1-200
echo "@@@ launch22 users"; grep -n "r1_launch22\|validate_removals" $T/launch_r1/*.py $T/student_pilot/s1_admission.py $T/student_pilot/carrier_c1_run.py $K/b/*.py 2>/dev/null | head -20
echo "@@@ sc/cs/i/px callers"; grep -n -E "\b(sc|cs|i|px|rv)\b(\.py|\.| import)" $K/b/a.py $K/b/pl.py $K/b/x.py $K/b/z.py 2>/dev/null | head -30
