export TZ=UTC; date -u +%FT%TZ
R=/tmp/a170674b01ec87a6f29b/sj/b01ec87a6f29b/r
timeout 60 srun --jobid=170674 --overlap -n1 -c1 --mem=1G --gres=gpu:1 bash -c "python3 -c '
import json
for l in open(\"$R/metadata/journals/3/0/items.jsonl\"):
    r=json.loads(l); o=r[\"output\"]; d=o[\"decode_budget\"]
    print(r[\"id\"], r[\"mode\"], o[\"finish\"], round(r[\"seconds\"]), \"calls\", len(o[\"calls\"]), \"samp\", d[\"sampled_tokens\"], \"inj\", d[\"injected_tokens\"], \"forced\", d[\"forced_eos\"], {k:round(v,1) for k,v in o[\"timings\"].items()})
    for c in o[\"calls\"]: print(\"   \", json.dumps(c)[:300])
    print(\"   TEXT:\", o[\"text\"][-700:].replace(chr(10),\" | \"))
'; tail -n 3 $R/logs/30.log | cut -c1-200" 2>&1 | head -60
