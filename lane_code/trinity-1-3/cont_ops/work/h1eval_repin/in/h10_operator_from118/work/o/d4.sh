export TZ=UTC; date -u +%FT%TZ
R=/tmp/a170674b01ec87a6f29b/sj/b01ec87a6f29b/r
timeout 60 srun --jobid=170674 --overlap -n1 -c1 --mem=1G --gres=gpu:1 bash -c "python3 -c '
import json
for l in open(\"$R/metadata/journals/3/0/items.jsonl\"):
    o=json.loads(l)[\"output\"]
    print(o[\"decode_budget\"], o[\"timings\"], o[\"finish\"], o[\"prompt_tokens\"] if not isinstance(o[\"prompt_tokens\"],list) else len(o[\"prompt_tokens\"]), len(o[\"calls\"]))
'; wc -l $R/metadata/journals/3/0/items.jsonl; tail -c 300 $R/logs/30.log" 2>&1 | head -20
