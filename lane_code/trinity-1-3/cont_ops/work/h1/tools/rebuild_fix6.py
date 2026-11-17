"""Rebind the packet using its retained trainer; validate on CPU before publication."""
import copy, hashlib, json, sys
from pathlib import Path
H=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(H/'tools'),str(H/'build/tree'),str(H/'build/fx/b')]
import derive_kit_h1 as dk
from student_pilot.carrier_c1_run import validate
from d import contract
w=dk.write
old=H/'evidence/fix6_before'
ids=json.loads((old/'ids.json').read_text());tok=ids['tokens']
tok.update({k:hashlib.sha256(('20261116-h1-1-'+k+'-fix6').encode()).hexdigest()[:8] for k in ('kit','root')})
over=json.loads((old/'build/over_local.json').read_text())
over.update(kit_key=tok['kit'],persistent_run_root='/project/community/jjyeung/okh7/r/'+tok['root'])
cfg=json.loads((old/'config.json').read_text())
dk.refresh_disk_plan(cfg,over)
validate(cfg)
ident=dk.identity(cfg)
# The admission contract names the unchanged logical run inputs, not the config hash.
la=json.loads((H/'build/fx/k/launch.json').read_text())
cont=dk.digest(contract(la,cfg));assert cont==ids['contract']
for name in ('4.json','review.json','staging.json'):
 v=json.loads((old/'payload'/name).read_text());v['config_sha256']=ident
 if 'admission_contract_sha256' in v:v['admission_contract_sha256']=cont
 w(H/'payload'/name,v)
 over['add_k'][name]=dict(path=str(H/'payload'/name),sha256=dk.sha(H/'payload'/name))
for name in ('over_local.json','over_seed.json'):w(H/'build'/name,over)
w(H/'build/over_fx.json',dict(over,fixture=True))
for name in ('fx','fx_seed'):
 p=H/'build'/name
 if p.exists():p.rename(H/'build'/(name+'_r5'))
 res=dk.derive('/scratch/jjyeung/orch_n30/review_h1pkt/work/d0/kitfull',p,dict(over,fixture=True))
 w(H/'evidence'/(name+'.json'),res)
 actual=json.loads((p/'k'/(res['config_key']+'.json')).read_text());validate(actual)
 assert res['config_identity']==ident
remote=json.loads((old/'payload/over.json').read_text())
remote.update(kit_key=tok['kit'],persistent_run_root=over['persistent_run_root'])
for n in ('4.json','review.json','staging.json'):remote['add_k'][n]['sha256']=over['add_k'][n]['sha256']
w(H/'payload/over.json',remote)
ids.update(identity=ident,contract=cont,config_key=res['config_key'],fixture_manifest=res['manifest_sha256'])
w(H/'ids.json',ids);w(H/'TOKENS_H1.json',tok)
print(json.dumps(ids,indent=2))
