R=/tmp/a170674b01ec87a6f29b/sj/b01ec87a6f29b/r
timeout 60 srun --jobid=170674 --overlap -n1 -c1 --mem=1G --gres=gpu:1 bash -c "python3 -c '
import json,collections
for l in open(\"$R/metadata/journals/3/0/items.jsonl\"):
    r=json.loads(l); o=r[\"output\"]; c=o[\"calls\"]
    cl=c[\"calls\"]; kinds=collections.Counter((x.get(\"kind\") if isinstance(x,dict) else str(x)[:20]) for x in cl)
    print(r[\"id\"], r[\"mode\"], round(r[\"seconds\"]), \"ncalls\", len(cl), dict(kinds), \"unserved\", c[\"unserved\"] if not isinstance(c[\"unserved\"],list) else len(c[\"unserved\"]), \"records\", len(c[\"records\"]))
    if len(cl)>3: print(\"  first\", json.dumps(cl[0])[:200]); print(\"  sample calls:\", [ (x.get(\"call\") or x.get(\"token\") or str(x))[:60] for x in cl[3:12]])
'; date -u" 2>&1 | head -30
