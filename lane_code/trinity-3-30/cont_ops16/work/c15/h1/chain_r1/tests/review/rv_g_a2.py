import copy,json,sys
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).resolve().parents[2];root=Path('/scratch/jjyeung/orch_n30/review_h1pkt/work/h1c/rv/out/A2_alt_tree_without_4json');sys.path.insert(0,str(root/'b'))
import g
launch=json.loads((root/'k/launch.json').read_text());launch.update(status='READY',production_authorized=True)
original=g.read_pin

def evidence(r,pin):
 value=original(r,pin)
 if pin['file']=='k/archive.json':value.update(status='ARCHIVED',durable=True,location='/project/test/archive.tar')
 if pin['file']=='k/review.json':value.update(verdict='PASS',reviewer='fixture-only')
 if pin['file']=='k/staging.json':value.update(status='PASS',missing=[])
 return value
read=Path.read_text

def text(p,*a,**kw):
 if p==root/'k/launch.json':return json.dumps(launch)
 return read(p,*a,**kw)
with patch.object(Path,'read_text',text),patch.object(g,'read_pin',evidence),patch.object(g,'persistent_launch',side_effect=lambda la,*a:la):
 try:g.check(root,environment={},mode='p')
 except ValueError as e:assert 'Written slot authorization' in str(e)
 else:raise AssertionError('stale authorization accepted')
print(json.dumps(dict(status='PASS',scope='source/config/code/authorization/admission-contract bindings only; review, archive and staging approvals supplied in memory; persistent-state operation stubbed; no production authorization'))+'\n')
print('binding checks passed')

res=json.loads((H/'evidence/review/rv_mut.json').read_text())
assert not res['A2_alt_tree_without_4json']['admitted']
assert not (H/'evidence/review/out/A2_alt_tree_without_4json').exists()
print('PASS early refusal and native gate defense')
