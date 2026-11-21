export TZ=UTC; date -u +%TZ
timeout 60 srun --overlap --jobid 174134 -N1 -n1 bash -c 'cd /tmp/a15_dbg_174134; python3 -I -B -c "
import json, collections
for line in open(\"n2/evb.jsonl\"):
    r=json.loads(line)
    if r[\"kind\"]==\"INFO\" and \"forward\" in r: print(\"FORWARD\", json.dumps(r[\"forward\"]))
d=json.load(open(\"n2/p/q/f.json\")); r=d[\"records\"]
print(\"records\",len(r),dict(collections.Counter(x[\"stream\"] for x in r)),\"finite\",all(x[\"finite\"] for x in r))
print(\"per rank\",dict(collections.Counter(x[\"rank\"] for x in r)))
print(\"seconds sum\",round(sum(x.get(\"seconds\",0) for x in r),1),\"max forward_peak_gib\",max(x.get(\"forward_peak_gib\",0) for x in r),\"max tokens\",max(x.get(\"tokens\",0) for x in r),\"over_10k\",sum(1 for x in r if x.get(\"over_10k_tokens\")),\"substituted\",sum(1 for x in r if x.get(\"substituted_from\") is not None))
res=json.load(open(\"n2/p/q/RESULTb.json\")); print(\"RESULT keys\",sorted(res)); print(\"status\",res[\"status\"],\"failed\",res.get(\"failed\"),\"steps\",res[\"steps\"]); print(\"host_receipt\",res.get(\"host_receipt\")); print(\"handover\",json.dumps(res.get(\"handover\"))[:600])
h=json.load(open(\"n2/p/q/hostb.json\")); print(\"host status\",h[\"status\"],\"assertions\",h[\"assertions\"],\"audit complete\",h[\"loader_audit\"].get(\"complete\"))
a=h[\"loader_audit\"]; print(\"audit draws\",a.get(\"draws\"),\"largest_repeat\",a.get(\"largest_repeat\"),\"eligible\",str(a.get(\"eligible\"))[:300])
"; echo "== c4b log non-EV tail"; grep -v "^EV" log/c4b.log | tail -4 | cut -c1-300; echo "== postc"; cat log/postc.log; tail -n 3 log/rv2.log | cut -c1-200; ls live2 | tr "\n" " "; echo; nvidia-smi --query-gpu=index,memory.used --format=csv,noheader | tr "\n" ";"; echo; ls -la n2/p/q/p/frames_4608*/r | tail -2 | cut -c1-100'
squeue -j 174134 -h -o "%i %T %M %N"
