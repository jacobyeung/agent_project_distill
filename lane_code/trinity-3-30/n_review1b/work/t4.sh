W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; T=$W/w24/work/tree_r1; K=$W/w24/out/kit_n_go
echo "=== pp 64-96"; sed -n 64,96p $T/launch_r1/production_proof.py
echo "=== entry begin_host"; grep -n "def begin_host" -A22 $T/launch_r1/entry.py
echo "=== z bootstrap"; grep -n "def bootstrap" -A60 $K/b/z.py | grep -n "a.py\|/tmp/q_22c714e1\|bwrap\|Q_MODE\|'p'\|rd.py\|argv" | head -30
echo "=== j.json mode r bits"; python3 - <<'P'
import json,base64
v=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/kit_n_go/k/j.json'));d=json.loads(base64.b64decode(v['payload']))
s=json.dumps(d,indent=1).splitlines()
for i,l in enumerate(s):
  if 'q_22c714e1' in l or 'rd.py' in l or '"r"' in l: print(i,l[:220])
P
