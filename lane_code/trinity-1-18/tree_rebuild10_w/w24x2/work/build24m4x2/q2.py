from pathlib import Path
import sys,os,json,hashlib,types,resource
from unittest.mock import patch
L=Path.cwd();D=L/'work/build24m4x2';label=sys.argv[1];tree=D/'base_tree' if label=='base' else L/'work/tree_r1c'
resource.setrlimit(resource.RLIMIT_AS,(14*1024**3,14*1024**3))
root=D/'q2_shared';root.mkdir();os.environ.update(TMPDIR=str(root),R2_PROOFS=str(root),R2_FIXTURES=str(D/'tmp/fixtures'))
sys.path.insert(0,str(tree));package=types.ModuleType('tests');package.__path__=[str(tree/'tests')];sys.modules['tests']=package
from tests.test_r1_build13 import PopulationTests
from tests.test_r2_data_path import fixture,manifest
from student_pilot import r1_routing,r2_intake
results={}
for mode in ('absent','empty'):
 case=PopulationTests('test_composition_replaces_base');case.setUp();case.root=case.root/mode;case.root.mkdir()
 original=r1_routing.compose
 def compose(base,sources,batches,cfg,output):
  if mode=='empty':cfg['r1_training']['extent_pool_sources']=[]
  return original(base,sources,batches,cfg,output)
 try:
  with patch.object(r1_routing,'compose',side_effect=compose):case.test_composition_replaces_base()
  payload=(case.root/'out/receipt.json').read_bytes();assert 'extent_exempted' not in json.loads(payload)
  results['compose_'+mode]=dict(bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),text=payload.decode())
 finally:case.tearDown()
 root2=root/('intake_'+mode);root2.mkdir();row=fixture(root2);pin=manifest(root2/'m',[row]);v=json.loads(pin.read_text())
 if mode=='empty':v['extent_pool_sources']=[];pin.write_text(json.dumps(v))
 accepted,report=r2_intake.intake(pin);assert len(accepted)==1 and 'extent_exempted' not in report
 payload=(json.dumps(report,sort_keys=True,indent=2)+'\n').encode();results['intake_'+mode]=dict(bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),text=payload.decode())
(D/('Q2_'+label+'.json')).write_text(json.dumps(results,indent=2)+'\n');print(label,'Q2 four outputs recorded')
