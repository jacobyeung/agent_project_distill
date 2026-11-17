R=/tmp/a170706b01ec87a6f29b/sj/b01ec87a6f29b/r
timeout 60 srun --jobid=170706 --overlap -n1 -c1 --mem=1G --gres=gpu:1 bash -c "python3 -c '
import json
for l in open(\"$R/metadata/journals/3/0/items.jsonl\"):
    r=json.loads(l); o=r[\"output\"]
    print(r[\"id\"], r[\"mode\"], round(r[\"seconds\"]), o[\"finish\"], [x[\"call\"][:40] for x in o[\"calls\"][\"records\"]], repr(o[\"text\"][-160:]))
'" 2>&1 | tail -40
