K=/scratch/jjyeung/orch_n30/nvkey1/work
tmux ls 2>&1 | grep nvk1; cat $K/runner.log | tail -8; tail -c 800 $K/runner.stdout 2>/dev/null
/scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import json
K='/scratch/jjyeung/orch_n30/nvkey1/work'
for l in open(K+'/meter/CALLS.jsonl'):
    r=json.loads(l); print({k: r.get(k) for k in ('utc','job','id','model','status','secs','bytes','served','prompt_tokens','completion_tokens','reasoning_tokens','dollars','header_cost','finish','fault','err','fallbacks')})
import glob
for f in glob.glob(K+'/out/*.jsonl'):
    for l in open(f):
        r=json.loads(l); print('OUT', r['id'], r['model'], repr((r['text'] or '')[:160]), r['sizes'])
PY
cat $K/meter/METER.json
