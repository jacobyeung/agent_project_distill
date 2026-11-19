R=/project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa; ls -la $R | head -30
F=$R/metrics_172660.jsonl; test -f $F && python3 -B - $F <<'P'
import json,sys,os
f=open(sys.argv[1],'rb'); sz=os.path.getsize(sys.argv[1]); f.seek(max(0,sz-1500000)); b=f.read().split(b'\n')
rows=[json.loads(x) for x in b[1:] if x.strip()]
print('size',sz,'rows_tail',len(rows),'steps',[r.get('step') for r in rows])
def sk(v,d=0,p=''):
  if isinstance(v,dict):
    for k,x in v.items():
      if d<4: 
        s=len(json.dumps(x)); print('  '*d+k, type(x).__name__, s, (json.dumps(x)[:120] if s<400 else ''))
        if s>=400: sk(x,d+1)
  elif isinstance(v,list) and v: print('  '*d+'[0] of',len(v)); sk(v[0],d+1)
sk(rows[-1])
P
