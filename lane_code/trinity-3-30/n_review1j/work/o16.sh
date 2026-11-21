TZ=UTC date +%TZ; cat /tmp/rv1j_a.out
timeout 150 srun --overlap --jobid 174134 -N1 -n1 nice -n 15 /usr/bin/python3 -I - <<"PY" 2>&1
import json
Q="/tmp/q_22c714e1_174134/p/q"
d=json.load(open(Q+"/sc/p/p/receipt.json")); print("POOLREB",list(d))
for k,v in d.items(): print(" ",k,json.dumps(v)[:500])
d=json.load(open(Q+"/selection/pool/receipt.json")); print("SELPOOL",list(d))
for k,v in d.items(): print(" ",k,json.dumps(v)[:400])
d=json.load(open(Q+"/sc/0/0.json")); print("SC0 pop",json.dumps(d["scene_rebuild"])[:400])
PY
