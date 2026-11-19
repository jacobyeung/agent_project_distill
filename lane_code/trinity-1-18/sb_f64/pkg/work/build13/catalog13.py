"""Keep source hashes and QID membership from the authorized census slices."""
from pathlib import Path
import sys,json,tarfile,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build13';sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.p3_provenance import load,pinned,file_pin
cfg=load(B/'inputs/config.json');spec=load(pinned(cfg['r1_training']['row_sources']))
out=dict(schema='r1-source-catalog-v1',sources={})
for kind in ('recovery','absolute_distance','units'):
    pin=spec[kind]['source'];qids=[]
    with pinned(pin).open() as f:
        for line in f:qids.append(json.loads(line)['qid'])
    assert len(set(qids))==len(qids)
    out['sources'][kind]=dict(source=pin,qids=qids)
p=B/'inputs/source_membership.json';p.write_text(json.dumps(out,sort_keys=True,separators=(',',':')))
cfg['r1_training']['source_membership']=file_pin(p)
(B/'inputs/kit_config.json').write_text(json.dumps(cfg,indent=2))
seal=load(L/'out/TREE_SEAL.json')
archive=next((L/'work/build12/kits/r1/k').glob('t_*.tar'))
prior=B/'prior12';prior.mkdir(exist_ok=True)
with tarfile.open(archive) as t:
    for name,h in seal['files'].items():
        if not name.endswith('.py'):continue
        raw=t.extractfile(name).read();assert hashlib.sha256(raw).hexdigest()==h
        dest=prior/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
(B/'PRIOR12.json').write_text(json.dumps(dict(archive=file_pin(archive),seal=seal['tree_sha256'])))
print('Catalog source counts:',{k:len(v['qids']) for k,v in out['sources'].items()})
