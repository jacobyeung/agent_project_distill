import ast,sys,unittest,json
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
W=Path(__file__).resolve().parents[1];P=W/'out/src'
sys.path[:0]=[str(P/'b'),str(P/'tree'),str(P)]
import torch
from e2e_reader import stage1,real
from h1eval.perception import perception
from h1eval.h10.perception_own import LazyStageOne

def fixture_maker(*args,**kwargs):
 return lambda item:dict(text='0',finish='stop')

class Wiring(unittest.TestCase):
 def construct(self,arm,rule,mutant=False):
  made=[]
  def init(obj,detect,head,geo,rule='null_argmax'):
   obj.rule=rule;obj.head=head;obj.diagnostics={};made.append(obj)
  head=NS(with_null=lambda *a:torch.tensor([1.,2.,100.]))
  with patch.object(stage1.StageOne,'__init__',init),patch('e2e_reader.geometry.frame_count',return_value=32),patch.object(real,'TowerG3T',return_value=None),patch.object(real,'Perception',side_effect=lambda *a:NS(socket=a[3])):
   if arm=='own':
    LazyStageOne(None,NS(_h10_ground_components=(object(),head)),'cpu',{'stage1_select_rule':rule})(None,None)
   else:
    if mutant:
     source=(P/'b/e2e_reader/real.py').read_text().replace('rule=stage1_select_rule',"rule='null_argmax'")
     node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='real_perception')
     ns=dict(real.__dict__);exec(compile(ast.Module(body=[node],type_ignores=[]),'mutant','exec'),ns)
     with patch.object(real,'real_perception',ns['real_perception']):
      p=perception('tower',sam3_tower=object(),selector_head=head,stage1_select_rule=rule)
    else:p=perception('tower',sam3_tower=object(),selector_head=head,stage1_select_rule=rule)
    p.socket(None,None)
  self.assertEqual(len(made),1);self.assertEqual(made[0].rule,rule)
  self.assertEqual(made[0].select({'x':torch.zeros(2,58),'name':'x'}),-1 if rule=='null_argmax' else 1)
 def test_both_arms_reach_stageone(self):
  for arm in ('own','tower'):
   for rule in ('null_argmax','candidates_argmax'):self.construct(arm,rule)
 def test_ignored_tower_rule_mutant_fails(self):
  with self.assertRaises(AssertionError):self.construct('tower','candidates_argmax',True)
 def test_production_parity_settings_and_mutant(self):
  source=(P/'b/e2e_reader/parity.py').read_text()
  def check(source):
   call=next(n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='real_perception')
   expr=ast.Expression(next(k.value for k in call.keywords if k.arg=='stage1_select_rule'))
   for rule in ('null_argmax','candidates_argmax'):
    self.assertEqual(eval(compile(expr,'parity','eval'),{'settings':{'stage1_select_rule':rule}}),rule)
  check(source)
  with self.assertRaises(AssertionError):check(source.replace("settings.get('stage1_select_rule','null_argmax')","'null_argmax'"))
 def test_production_make_real_reaches_stageone(self):
  from e2e_reader import parity
  from types import ModuleType
  from contextlib import ExitStack
  sam_module=ModuleType('student_pilot.sam3_tower');sam_module.Sam3Tower=lambda settings:object()
  head=NS(with_null=lambda *a:torch.tensor([1.,2.,100.]))
  paths=[(W/'work/1').resolve(),(W/'work/2').resolve()]
  artifact=NS(files=lambda role:paths);artifact.verify=lambda:artifact
  proc=NS(tokenizer=None,_routing_tokens={'ids':{}})
  for rule in ('null_argmax','candidates_argmax'):
   made=[]
   def init(obj,detect,head,geo,rule='null_argmax'):
    obj.rule=rule;obj.head=head;obj.diagnostics={};made.append(obj)
   with ExitStack() as stack:
    for name,value in dict(install=lambda *a:None,Artifact=lambda *a,**k:artifact,
      load_native=lambda *a,**k:(None,proc,{'config':{},'export':{'frame_layout':'duplicate'}}),
      CallHook=lambda *a:None,install_hook=lambda *a:None,_head=lambda *a:head,
      policy=lambda:NS(),ParityGenerator=lambda *a,**k:NS(perception=a[3])).items():
     stack.enter_context(patch.object(parity,name,value))
    stack.enter_context(patch.dict(sys.modules,{'student_pilot.sam3_tower':sam_module}))
    stack.enter_context(patch.object(stage1.StageOne,'__init__',init))
    stack.enter_context(patch('e2e_reader.geometry.frame_count',return_value=32))
    stack.enter_context(patch.object(real,'TowerG3T',return_value=None))
    settings=dict(arm='own_depth',sam3=dict(checkpoint_path=str(paths[0]),receipt_path=str(paths[1])),
      selector_head='stub',frames_json={'captures':{}},dense_manifest={'captures':{}},stage1_select_rule=rule)
    g=parity.make_real(None,dict(root='stub',name='stub',sha256='stub'),[],settings=settings)
    g.generator.perception.socket(None,None)
   self.assertEqual(made[0].rule,rule)
   self.assertEqual(made[0].select(dict(x=torch.zeros(2,58),name='x')),-1 if rule=='null_argmax' else 1)
 def test_tower_reuse_across_rules_refused(self):
  from h1eval.h10.launch import tower_records
  p=W/'work/tower_reuse';p.mkdir(exist_ok=True)
  binding={k:'x' for k in ('export_sha256','item_set_sha256','items_sha256','reader_sha256','artifact_manifest_sha256')}
  (p/'environment.json').write_text(json.dumps({'binding':dict(binding,stage1_select_rule='null_argmax')}))
  with self.assertRaisesRegex(ValueError,'stage1_select_rule'):tower_records(p,dict(binding,stage1_select_rule='candidates_argmax'),[])
 def test_launcher_resume_across_rules_refused(self):
  import tempfile,io
  from h1eval.h10 import launch,parity_adapter
  from h1eval.items import load_manifest
  root=Path(tempfile.mkdtemp(prefix='binding_',dir=W/'work/tmp'));(root/'e').mkdir();(root/'e/w').write_bytes(b'fixture')
  binding=root/'b.json';binding.write_text(json.dumps(dict(root=str(root),name='fixture',sha256='a'*64)))
  settings=root/'s.json';value=dict(export_dir=str(root/'e'),artifact_manifest=str(binding),stage1_select_rule='null_argmax',perception_memo='off')
  settings.write_text(json.dumps(value));items=load_manifest(P/'items/devs1_routed.json')['items']
  args=launch.parser().parse_args(['--items',str(P/'items/devs1_routed.json'),'--export',str(root/'e'),
    '--artifact-manifest',str(binding),'--reader-root',str(P/'b'),'--out',str(root/'journal'),
    '--export-pin',str(W/'out/export_544.json'),'--settings',str(settings),'--shard','0/1000','--arms','tower','--modes','none','--device','cpu'])
  with patch.object(parity_adapter,'map_items',return_value=({r['id']:r for r in items},{'sha256':'a'*64})),patch('sys.stdout',new=io.StringIO()):
   launch.run(args,make_real=fixture_maker)
   observed=json.loads((root/'journal/environment.json').read_text())['binding']
   self.assertEqual((observed['lineage'],observed['step'],observed['stage1_select_rule'],observed['save_own_depth']),('SFT',544,'null_argmax',False))
   value['stage1_select_rule']='candidates_argmax';settings.write_text(json.dumps(value))
   with self.assertRaisesRegex(ValueError,'Resume binding differs'):launch.run(args,make_real=fixture_maker)
 def test_default_snapshot_off(self):
  source=(P/'h1eval/h10/launch.py').read_text()
  self.assertIn("get('save_own_depth', False)",source)
  self.assertIn("get('save_own_depth',False)",(P/'orchard_h10/prepare.py').read_text())

if __name__=='__main__':unittest.main(verbosity=2)
