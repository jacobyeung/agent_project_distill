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
 def test_tower_reuse_across_rules_refused(self):
  from h1eval.h10.launch import tower_records
  p=W/'work/tower_reuse';p.mkdir(exist_ok=True)
  binding={k:'x' for k in ('export_sha256','item_set_sha256','items_sha256','reader_sha256','artifact_manifest_sha256')}
  (p/'environment.json').write_text(json.dumps({'binding':dict(binding,stage1_select_rule='null_argmax')}))
  with self.assertRaisesRegex(ValueError,'stage1_select_rule'):tower_records(p,dict(binding,stage1_select_rule='candidates_argmax'),[])
 def test_default_snapshot_off(self):
  source=(P/'h1eval/h10/launch.py').read_text()
  self.assertIn("get('save_own_depth', False)",source)
  self.assertIn("get('save_own_depth',False)",(P/'orchard_h10/prepare.py').read_text())

if __name__=='__main__':unittest.main(verbosity=2)
