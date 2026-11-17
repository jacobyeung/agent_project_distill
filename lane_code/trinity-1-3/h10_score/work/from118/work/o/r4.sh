R=/tmp/a170674b01ec87a6f29b/sj/b01ec87a6f29b/r
timeout 60 srun --jobid=170674 --overlap -n1 -c1 --mem=1G --gres=gpu:1 bash -c "python3 -c '
import json,collections
for l in open(\"$R/metadata/journals/3/0/items.jsonl\"):
    r=json.loads(l); o=r[\"output\"]; c=o[\"calls\"]; d=o[\"decode_budget\"]
    t=o[\"text\"]; a=t[t.find(\"<answer>\"):][:40]
    print(r[\"id\"], r[\"mode\"], round(r[\"seconds\"]), json.dumps(c[\"calls\"]), \"samp\", d[\"sampled_tokens\"], \"nrec\", len(c[\"records\"]), a, \"resp:\", [x.get(\"response\",\"\")[:30] for x in c[\"records\"][:6]])
'" 2>&1 | tail -8
ls /project/community/jjyeung/okh7 | tr '\n' ' ' | cut -c1-1500
