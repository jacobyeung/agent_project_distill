#!/bin/bash
set +x; set -uo pipefail; export TZ=UTC
O=/project/community/jjyeung/okh7; KH=$O/x_ee227714; R=$KH/runs/6ed2c7aa; P=$R/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820
python3 -B - $R/metrics_172660.jsonl $P/vqa/receipt.json <<'PY'
import json,sys
rows=[json.loads(l) for l in open(sys.argv[1],'rb') if l.endswith(b'\n')]
r=rows[-1]; k=r['ranks'][0]
def shape(x,d=0):
  if isinstance(x,dict): return {a:shape(b,d+1) for a,b in list(x.items())[:40]} if d<3 else 'dict%d'%len(x)
  if isinstance(x,list): return 'list%d'%len(x)
  return type(x).__name__
print('ROWKEYS',json.dumps(shape({a:b for a,b in r.items() if a!='ranks'})))
print('RANKKEYS',json.dumps(shape(k))[:3000])
def find(x,p=''):
  if isinstance(x,dict):
    for a,b in x.items(): find(b,p+'.'+a)
  elif isinstance(x,list):
    for i,b in enumerate(x[:3]): find(b,p+'[%d]'%i)
  elif any(s in p.lower() for s in ('count','form','draw','procedure')): print('HIT',p,str(x)[:200])
find(k)
v=json.load(open(sys.argv[2])); print('VQA database',json.dumps(v['database'])[:400]); print('VQA source',json.dumps(v.get('source'))[:300])
PY
