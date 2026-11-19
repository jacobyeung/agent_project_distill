from pathlib import Path
import json, sys
L=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(L/'work/build24'))
import joblib as J
if '--request' in sys.argv:
    v=J.load(L/'work/build24d/go/r2.json')
    print({k:x for k,x in v.items() if k!='_paths'})
    v=J.load(L/'work/build24f/rehearsal/prepared.json')
    print('prep keys',list(v))
    v=J.load(L/'work/build24/proofs/capacity/final/400/export/artifact.json')
    print('artifact keys',list(v));print('full weights',v.get('full_weights'))
    sys.exit()
for name in ('k/n.json','k/p.json','k/r.json'):
    v=J.load(L/'out/kit_n_go'/name)
    print(name, {k:x for k,x in v.items() if any(s in k for s in ('model','base','manifest','listing','receipt'))})
R=L/'work/build24f/rehearsal'
v=J.load(R/'v.json')
print('fixture relevant', {k:v[k] for k in ('model','preparation','init_artifact') if k in v})
p=Path(v['preparation']['path'].replace('/tmp/q_22c714e1',str(R)))
prep=J.load(p)
print('prep model',prep.get('model'))
manifest=J.load(prep['model']['path'])
print('fixture manifest',manifest)
ext=L.parent/'ext/m400real'
receipt=J.load(ext/'e.json')
print('production receipt pins',receipt.get('pins'))
pp=receipt['pins']['preparation']
ppath=ext/'files'/pp['path'].lstrip('/')
assert J.sha(ppath)==pp['sha256']
pp=J.load(ppath)
print('production prep model',pp['model'])
mpath=ext/'files'/pp['model']['path'].lstrip('/')
print('production model path exists',mpath,mpath.exists())
if mpath.exists():
    assert J.sha(mpath)==pp['model']['sha256']
    print('production model manifest',J.load(mpath))
for p in (ext/'m').glob('*'):
    if p.stat().st_size<20000:
        try:
            v=J.load(p)
            if isinstance(v,dict) and ('text_config' in v or 'model_type' in v):print('metadata',p,v)
        except ValueError:pass
