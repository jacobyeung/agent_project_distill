export TZ=UTC
F=/project/community/jjyeung/okh7/x_69d2930d/runs/673bc60f/metrics_171377.jsonl
ls -la $F; sha256sum $F
python3 -B - $F <<'PY'
import json,sys,statistics as S
rows=[]
for line in open(sys.argv[1],'rb'):
  if line.endswith(b'\n'): rows.append(json.loads(line))
print('rows',len(rows),'last step',rows[-1]['step'])
base={}
sel=[r for r in rows if 186<=r['step']<=200]
for s in ('pose','vqa','routing','pointing'):
  v=[sum(k['stream_means'].get(s,float('nan')) for k in r['ranks'])/len(r['ranks']) for r in sel]
  m=S.median(v); d=S.median([abs(x-m) for x in v]); base[s]=(m,d)
print('BASE_186_200',json.dumps(base))
print('wall_last',[round(r['ranks'][0]['wall_seconds']) for r in rows[-3:]])
print('keys',list(rows[-1]['ranks'][0].keys())[:40])
PY
