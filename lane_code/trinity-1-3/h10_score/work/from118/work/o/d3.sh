export TZ=UTC; date -u +%FT%TZ
R=/tmp/a170674b01ec87a6f29b/sj/b01ec87a6f29b/r
timeout 60 srun --jobid=170674 --overlap -n1 -c1 --mem=1G --gres=gpu:1 bash -c "nproc; cat /sys/fs/cgroup/cpu.max 2>/dev/null; python3 -c '
import json
for l in open(\"$R/metadata/journals/3/0/items.jsonl\"):
    r=json.loads(l); o=r[\"output\"]
    print(r[\"id\"], len(o.get(\"tokens\",[])), {k:(v if not isinstance(v,(list,dict)) else type(v).__name__+str(len(v))) for k,v in r.items() if k!=\"output\"})
    print(sorted(o.keys()))
'; tail -c 600 $R/logs/30.log; date -u" 2>&1 | head -40
