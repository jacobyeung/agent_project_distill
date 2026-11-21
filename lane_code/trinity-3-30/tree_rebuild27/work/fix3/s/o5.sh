python3 -I - <<'PY'
import json,os,sys,io,tarfile,hashlib
U='/project/community/jjyeung/okh7/x_22c714e1/u/'
E=sys.stderr
want=['8957d119bfa6776efe776816675da6d0f610a6e8c336acd66c297f29cf4e7e0f'];got={}
while want:
    h=want.pop()
    p=U+h
    if h in got or not os.path.isfile(p): print('absent',h[:12],file=E); continue
    if os.path.getsize(p)>3_000_000: print('big',h[:12],os.path.getsize(p),file=E); continue
    raw=open(p,'rb').read(); got[h]=raw
    try:d=json.loads(raw)
    except Exception: continue
    if isinstance(d,dict):
        print(h[:12],'schema',d.get('schema'),'keys',sorted(d)[:25],'model',d.get('model'),file=E)
        for s in d.get('sources',[]):
            if isinstance(s,dict):
                print('   source',s.get('kind'),{k:(v.get('sha256','')[:12] if isinstance(v,dict) else v) for k,v in s.items() if k in ('receipt','model','database','count')},file=E)
                if isinstance(s.get('receipt'),dict): want.append(s['receipt']['sha256'])
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w:gz') as t:
    for h,raw in sorted(got.items()):
        ti=tarfile.TarInfo(h); ti.size=len(raw); t.addfile(ti,io.BytesIO(raw))
sys.stdout.buffer.write(buf.getvalue())
PY
