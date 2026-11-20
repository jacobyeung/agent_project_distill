K=/scratch/jjyeung/orch_n30/nvkey1/work
echo "trinity egress $(curl -s -m 15 https://checkip.amazonaws.com)"
tmux ls 2>&1 | grep nvk1; tail -5 $K/runner.log; tail -c 600 $K/runner.stdout 2>/dev/null
/scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import json, collections
K='/scratch/jjyeung/orch_n30/nvkey1/work'
c=collections.Counter(); tok=collections.defaultdict(lambda: [0,0,0,0.0,0.0,0])
for l in open(K+'/meter/CALLS.jsonl'):
    r=json.loads(l)
    if r['job']!='10_bake32': continue
    c[(r['model'].split('/')[-1], r['status'], bool(r.get('fault')))]+=1
    if r['status']==200:
        t=tok[r['model'].split('/')[-1]]; t[0]+=r.get('prompt_tokens',0); t[1]+=r.get('completion_tokens',0); t[2]+=r.get('reasoning_tokens',0); t[3]+=r.get('dollars') or 0; t[4]+=float(r.get('header_cost') or 0); t[5]+=1; 
for k,v in sorted(c.items()): print('CALLS', k, v)
for k,t in tok.items(): print('TOK', k, 'n', t[5], 'in', t[0]//max(1,t[5]), 'out', t[1]//max(1,t[5]), 'reason', t[2]//max(1,t[5]), 'list$', round(t[3],3), 'hdr$', round(t[4],3))
for l in open(K+'/meter/CALLS.jsonl'):
    r=json.loads(l)
    if r['job']=='10_bake32' and r['status']!=200: print('ERR', r['model'], r['status'], (r.get('err') or '')[:200])
import os
if os.path.exists(K+'/out/10_bake32.jsonl'):
    for l in open(K+'/out/10_bake32.jsonl'):
        r=json.loads(l); print('OUT', r['id'], r['finish'], r['secs'], len(r['text'] or ''), repr((r['text'] or '')[:100]))
PY
cat $K/meter/METER.json
