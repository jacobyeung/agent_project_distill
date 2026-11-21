timeout 200 srun --overlap --jobid 174134 -N1 -n1 nice -n 15 bash -c '
python3 - <<"PY"
import json,os
d=json.load(open("/tmp/a15_dbg_174134/mixc.json"))
e=d["entry"]; print({k:(json.dumps(v)[:400]) for k,v in e.items() if k!="sources"})
for s in e["sources"]: print("SRC",{k:(json.dumps(v)[:300]) for k,v in s.items()})
def loc(p): return p.replace("/tmp/q_22c714e1/","/tmp/q_22c714e1_174134/",1)
for k,v in e.items():
    if isinstance(v,dict) and "path" in v: print(k, v["path"], os.path.exists(loc(v["path"])), os.path.exists(v["path"]))
print({k:(json.dumps(v)[:300]) for k,v in d["settings"].items()} if isinstance(d["settings"],dict) else d["settings"])
PY
' < /dev/null
