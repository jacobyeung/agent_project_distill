TZ=UTC date +%TZ
timeout 200 srun --overlap --jobid 174134 -N1 -n1 nice -n 15 bash -c '
N=/tmp/q_22c714e1_174134; cd $N/p/q; python3 -V
python3 - <<"PY"
import json,os
c=json.load(open("c.json")); po=c["preparation_output"]; print("preparation_output",po)
loc=po.replace("/tmp/q_22c714e1/","/tmp/q_22c714e1_174134/",1) if po.startswith("/tmp/q_22c714e1/") else po
print("local",loc, os.path.isdir(loc))
if os.path.isdir(loc):
    for r,ds,fs in os.walk(loc):
        if r.count("/")-loc.count("/")>2: continue
        print(r, sorted(fs)[:12], len(fs))
for k in ("2","3"):
    d=json.load(open(f"sc/{k}/0.json")); print("sc",k,{x:(json.dumps(v)[:300]) for x,v in d.items() if x!="source_scene_exclusions"})
print("sc/0/0", {x:(json.dumps(v)[:300]) for x,v in json.load(open("sc/0/0.json")).items() if x!="source_scene_exclusions"})
PY
' < /dev/null
