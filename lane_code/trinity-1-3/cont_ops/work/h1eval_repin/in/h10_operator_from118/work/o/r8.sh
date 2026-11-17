R=/tmp/a170706b01ec87a6f29b/sj/b01ec87a6f29b/r
timeout 60 srun --jobid=170706 --overlap -n1 -c1 --mem=1G --gres=gpu:1 bash -c "python3 -c '
import json
L=open(\"$R/metadata/journals/3/0/items.jsonl\").read().splitlines()
for l in L[-8:]:
    r=json.loads(l); o=r[\"output\"]; d=o[\"decode_budget\"]
    print(r[\"id\"], r[\"mode\"], round(r[\"seconds\"]), o[\"finish\"], json.dumps(o[\"calls\"][\"calls\"]), \"samp\", d[\"sampled_tokens\"], \"inj\", d[\"injected_tokens\"], repr(o[\"text\"][-120:]))
import collections; print(collections.Counter(json.loads(l)[\"output\"][\"finish\"] for l in L), sum(json.loads(l)[\"seconds\"] for l in L)/len(L))
'; date -u" 2>&1 | tail -12
