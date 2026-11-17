R=/tmp/a170674b01ec87a6f29b/sj/b01ec87a6f29b/r
timeout 60 srun --jobid=170674 --overlap -n1 -c1 --mem=1G --gres=gpu:1 bash -c "python3 -c '
import json,collections
for l in open(\"$R/metadata/journals/3/0/items.jsonl\"):
    r=json.loads(l); o=r[\"output\"]; c=o[\"calls\"]
    print(r[\"id\"], json.dumps(c[\"calls\"])[:200], json.dumps(c[\"unserved\"])[:100])
    rec=c[\"records\"]; print(\"  rec0\", json.dumps(rec[0])[:250])
    if len(rec)>3:
        cnt=collections.Counter(json.dumps(x.get(\"call\",x))[:70] for x in rec); print(\"  top\", cnt.most_common(6))
'; date -u" 2>&1 | head -30
