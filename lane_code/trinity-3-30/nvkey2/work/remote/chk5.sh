K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1; P=/scratch/jjyeung/envs/p1cpu/bin/python
echo 8 > ctl/RATE; echo 24 > ctl/INFLIGHT; cat ctl/RATE ctl/INFLIGHT
$P -B - <<'PY'
import json
for fn in ('out/45_v6p30.jsonl',):
    for l in open(fn):
        r = json.loads(l); print(r['id'][:22], r['secs'], r['usage']['completion'], r['usage']['reasoning'], round(r['dollars'], 3), len(r['text'] or ''))
PY
tail -2 v6/chain.log; wc -l queue/46_v6v30.jsonl
