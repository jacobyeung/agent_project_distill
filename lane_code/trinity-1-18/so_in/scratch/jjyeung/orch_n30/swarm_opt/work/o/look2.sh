#!/bin/bash
set +x; set -uo pipefail; export TZ=UTC
O=/project/community/jjyeung/okh7
echo "## 171377.gpu"; cat $O/x_69d2930d/o/171377.gpu
echo "## 172660.gpu"; cat $O/x_ee227714/o/172660.gpu
echo "## 171377.err"; head -c 4000 $O/x_69d2930d/o/171377.err
echo "## runtime_config A keys"; nice -n 19 python3 -B - $O/x_69d2930d/runs/673bc60f/runtime_config.json $O/x_69d2930d/runs/673bc60f/metrics_171377.jsonl <<'PY'
import json,sys,statistics as st
c=json.load(open(sys.argv[1]))
def flat(d,p=''):
  for k,v in d.items():
    if isinstance(v,dict): yield from flat(v,p+k+'.')
    else: yield p+k, v
for k,v in flat(c):
  s=json.dumps(v)
  if len(s)<160: print('CFG',k,s)
rows=[]
with open(sys.argv[2],'rb') as f:
  for line in f:
    if line.endswith(b'\n'): rows.append(json.loads(line))
for r in rows[99:102]+rows[-1:]:
  k=r['ranks'][0]
  print('STEP',r['step'],'wall',round(k['wall_seconds'],1),'data',round(k['data_seconds'],1),{x:k.get(x) for x in ('checkpoint_seconds','export_seconds','validation_seconds','export_reused')})
  print(' shapes', json.dumps([(s['stream'],s['tokens'],s.get('grid')) for s in k['shapes']])[:6000])
  print(' mem0', json.dumps(k['memory']['microbatches'][0])[:800])
  print(' memopt', json.dumps(k['memory']['after_optimizer_step'])[:400])
tok={}
for r in rows[20:]:
  for k in r['ranks']:
    for s in k['shapes']:
      tok.setdefault(s['stream'],[]).append(s['tokens'][1])
for s,v in tok.items(): print('TOK',s,len(v),'median',st.median(v),'max',max(v),'mean',round(st.mean(v)))
PY
