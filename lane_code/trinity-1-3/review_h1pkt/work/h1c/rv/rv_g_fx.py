import copy,json,sys
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).resolve().parents[1];root=H/'build/fx';sys.path.insert(0,str(root/'b'))
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
 g.check(root,environment={},mode='p')
print(json.dumps(dict(status='PASS',scope='source/config/code/authorization/admission-contract bindings only; review, archive and staging approvals supplied in memory; persistent-state operation stubbed; no production authorization'))+'\n')
print('binding checks passed')
