F=/project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa/metrics_172660.jsonl
wc -l $F
head -c 1500 $F | cut -c1-1500
echo; echo ---line2; sed -n 2p $F | cut -c1-1500
echo ---keys
python3 - <<'P'
import json,collections
F="/project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa/metrics_172660.jsonl"
c=collections.Counter();ex={}
with open(F) as f:
    for i,l in enumerate(f):
        try:d=json.loads(l)
        except Exception: c['bad']+=1;continue
        k=tuple(sorted(d.keys()))[:25]
        c[k]+=1; ex.setdefault(k,(i,l[:300]))
for k,v in c.most_common(8): print(v,k,ex.get(k))
P
cat /project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa/attempt_172660.json | cut -c1-1200
