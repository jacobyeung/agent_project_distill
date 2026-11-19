#!/bin/bash
set +x; set -uo pipefail; export TZ=UTC
O=/project/community/jjyeung/okh7
for d in $O/x_69d2930d/runs/673bc60f $O/x_69d2930d/o $O/x_ee227714/o $O/x_ee227714/runs/6ed2c7aa $O/x_ee227714/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820; do
  echo "## ls $d"; ls -la --time-style=+%FT%T $d 2>&1 | head -60
done
for f in $O/x_69d2930d/o/*.steps $O/x_69d2930d/o/*.w.steps; do [ -f "$f" ] && { echo "## $f"; head -c 12000 "$f"; }; done
echo "## metrics A"
nice -n 19 python3 -B - $O/x_69d2930d/runs/673bc60f/metrics_171377.jsonl <<'PY'
import json,sys
rows=[]
with open(sys.argv[1],'rb') as f:
  for line in f:
    if line.endswith(b'\n'): rows.append(json.loads(line))
print('rows',len(rows),'top keys',list(rows[0].keys()))
r0=rows[-1]['ranks'][0] if 'ranks' in rows[-1] else rows[-1]
def sk(x,dep=0):
  if isinstance(x,dict): return {k:sk(v,dep+1) for k,v in list(x.items())[:40]} if dep<2 else 'dict%d'%len(x)
  if isinstance(x,list): return 'list%d'%len(x)
  return x if isinstance(x,(int,float)) else str(x)[:40]
print('rank0 last', json.dumps(sk(r0))[:5000])
print('toplevel last', json.dumps({k:sk(v) for k,v in rows[-1].items() if k!='ranks'})[:3000])
for r in rows:
  ks=r.get('ranks',[r])
  print('S',r.get('step'),[round(k.get('wall_seconds',-1),1) for k in ks],[round(k.get('data_seconds',-1),1) for k in ks], {k2:r[k2] for k2 in r if 'second' in k2})
PY
