K=/scratch/jjyeung/orch_n30/nvkey1/work
date -u +%FT%TZ; cat $K/meter/METER.json; wc -l $K/out/3*.jsonl $K/out/41*.jsonl | head -4; tail -3 $K/runner.log
cd /scratch/jjyeung/orch_n30
ls -d tree_rebuild* tr1* 2>/dev/null | head -20
find tree_rebuild15_w24l -maxdepth 5 \( -path '*/validation' -o -path '*/__pycache__' -o -path '*/.git' \) -prune -o -type f \( -iname '*protect*' -o -iname '*exclu*' -o -iname '*withheld*' -o -iname '*bench_v2*' -o -iname '*rooms*.json*' \) -print 2>/dev/null | head -30
grep -c . $K/out/10_bake32.jsonl; head -c 600 $K/queue/10_bake32.jsonl | tr ',' '\n' | grep -E '"model"' | head; python3 -c "
import json
s=set()
for l in open('$K/queue/10_bake32.jsonl'): s.add(json.loads(l)['model'])
print(s)"
