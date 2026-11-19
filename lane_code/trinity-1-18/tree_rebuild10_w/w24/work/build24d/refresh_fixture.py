from pathlib import Path
import json,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24d';O=L/'work/build24/proofs/capacity'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1'),str(L/'work/build21')]
import native24 as N
import joblib as J
from student_pilot import s1_pool,r1_persisted as P
from student_pilot.p3_provenance import file_pin,load,pinned
root=D/'go';cfg=J.load(root/'input.json');old=load(pinned(cfg['s1_routing']['selection']))
aliases={p.name:str(p) for folder in ('build21','build22') for p in (L/'work'/folder/'upload/u').glob('*') if p.is_file()}
with P.scope(aliases):
 new=s1_pool.prepare(old['manifest'],root/'selection',cfg['remove_files'],old.get('tokenizer'))
cfg['s1_routing']['selection']=file_pin(root/'selection/receipt.json')
pin=J.write(root/'input2.json',cfg);request=J.load(root/'r.json');request['config']=pin;request['staged_pins']=[pin]
J.write(root/'r2.json',request)
J.write(D/'FIXTURE_SELECTION.json',dict(reason='Retained fixture receipt predates the sealed implementation',old=old['implementation'],new=new['implementation'],same_selected_rows=old['selected_rows']==new['selected_rows']))
# Inspect the production selection's producer fingerprint if its JSON is local.
real=L.parent/'ext/m400real';run=J.load(real/'r.json');runtime=J.load(real/('files'+run['config']['path']));selection=runtime['s1_routing']['selection'];p=real/('files'+selection['path'])
v=dict(pin=selection,local=p.is_file())
if p.is_file():
 actual=J.load(p);expected=s1_pool.implementation();v.update(matches=actual['implementation']==expected,differences={n:dict(p=h,n=expected.get(n)) for n,h in actual['implementation'].items() if h!=expected.get(n)})
J.write(D/'PRODUCTION_SELECTION.json',v)
