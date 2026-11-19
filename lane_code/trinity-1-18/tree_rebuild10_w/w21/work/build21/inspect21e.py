from pathlib import Path
import json,sys,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build21';E=L.parent/'ext/m400real'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
from student_pilot.r1_handover import export_identity
from student_pilot.carrier_c1_run import identity
e=J.load(E/'e.json');r=J.load(E/'r.json');manifest=J.load(E/'MANIFEST.json')
cfgs={}
for k in ('artifact','config','binding','preparation'):
    p=E/('files'+e['pins'][k]['path']);v=J.load(p);cfgs[k]=v
    print(k,hashlib.sha256(p.read_bytes()).hexdigest())
    if k=='config':print('identities',identity(v),export_identity(v))
kit=J.load(L.parent/'inputs/p_configs/cprime_31abe087.json')
print('kit identities',identity(kit),export_identity(kit))
pkit=L.parent/'ext/pwrap/k/aacc34e6.json';v=J.load(pkit)
print('pwrap kit',J.sha(pkit),export_identity(v), 'same',v==kit)
print('runtime versus kit',json.dumps({k:dict(runtime=cfgs['config'].get(k),kit=kit.get(k)) for k in set(kit)|set(cfgs['config']) if kit.get(k)!=cfgs['config'].get(k)},indent=2)[:20000])
print('missing',json.dumps([dict(path=x['path'],bytes=x['bytes']) for x in manifest['files'] if not (E/('files'+x['path'])).is_file()],indent=2))
def pins(v,parts=()):
    if isinstance(v,dict):
        if isinstance(v.get('path'),str) and '/69d2930d/' in v['path']:print('row reference',parts,v)
        for k,x in v.items():pins(x,parts+(k,))
    elif isinstance(v,list):
        for i,x in enumerate(v):pins(x,parts+(str(i),))
for p in E.rglob('*.json'):
    try:v=J.load(p)
    except ValueError:continue
    pins(v,(str(p.relative_to(E)),))
