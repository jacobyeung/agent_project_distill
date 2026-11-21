python3 -I - <<'PY'
import json,os,sys,io,tarfile
U='/project/community/jjyeung/okh7/x_22c714e1/u/'
E=sys.stderr
want={'depth_init': 'fd60ac2f525727836258ae7ea0705ff3a49163ae74320f7bf8a17b66cd69f0c7', 'stream.pointing': '93b21a3aeeda01efab90d9f818eff78a6ca182c18c964534279008e4af91733a', 'stream.pose': '8957d119bfa6776efe776816675da6d0f610a6e8c336acd66c297f29cf4e7e0f', 'stream.routing': 'ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984', 'stream.vqa': 'e3ee51daa46af30fa8e84a05c12448d7fc3dc9cade05284707f9df322bbe44d0'}
got={}
def summ(d):
    out={}
    for k,v in d.items():
        if isinstance(v,dict) and set(v)>={'path','sha256'}: out[k]=dict(sha=v['sha256'][:12],path=v['path'][-70:])
    return out
for label,h in want.items():
    p=U+h
    if not os.path.isfile(p): print(label,'absent',file=E); continue
    n=os.path.getsize(p)
    if n>3_000_000: print(label,'big',n,file=E); continue
    raw=open(p,'rb').read(); got[h]=raw
    try:d=json.loads(raw)
    except Exception as e: print(label,'not json',file=E); continue
    print(label,h[:12],'schema',d.get('schema'),'pins',summ(d),file=E)
    for k in ('saved','weights','encoder','init','artifact'):
        if isinstance(d.get(k),dict): print('   ',k,summ(d[k]) or {kk:str(vv)[:90] for kk,vv in list(d[k].items())[:6]},file=E)
    for s in d.get('sources',[]):
        if isinstance(s,dict): print('    source',s.get('kind'),summ(s),file=E)
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w:gz') as t:
    for h,raw in sorted(got.items()):
        ti=tarfile.TarInfo(h); ti.size=len(raw); t.addfile(ti,io.BytesIO(raw))
sys.stdout.buffer.write(buf.getvalue())
PY
