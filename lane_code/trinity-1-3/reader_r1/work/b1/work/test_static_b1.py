"""Standard-library checks; these do not stand in for the Torch replay gate."""
import ast,hashlib,json,sys,unittest
from pathlib import Path
W=Path(__file__).resolve().parents[1];P=W/'work/p'
sys.path.insert(0,str(P))
from orchard_h10.common import write,ORDER
from orchard_h10.runner import run

class Static(unittest.TestCase):
 def test_default_paths(self):
  a=ast.parse((W/'in/pkg/p/b/e2e_reader/grounding.py').read_text());b=ast.parse((P/'b/e2e_reader/grounding.py').read_text())
  for name in ('lift_plain','lift_bestspread','min_area_box','ground_session'):
   get=lambda tree:next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
   self.assertEqual(ast.dump(get(a)),ast.dump(get(b)))
  get=lambda tree:next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='StageOneSocket')
  fn=lambda c:next(n for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='__call__')
  self.assertEqual(ast.dump(fn(get(a))),ast.dump(fn(get(b))))
  for name in ('tree/trace_format/box_v313.py','tree/trace_format/ground_v313.py','tree/student_pilot/routed_candidates.py','tree/student_pilot/routed_features.py','b/e2e_reader/callhook.py'):
   self.assertEqual((W/'in/pkg/p'/name).read_bytes(),(P/name).read_bytes())
 def test_identity(self):
  out=W/'work/static_resume';out.mkdir(exist_ok=True)
  write(out/'metadata/IDENTITY.json',dict(plan='same',inputs=None,cards=1,order=list(ORDER),types=['object_abs_distance'],arms=['own'],stage1_select_rule='null_argmax',modes=['none']))
  cfg=dict(output=str(out),types=['object_abs_distance'],plan_sha256='same',stage1_select_rule='candidates_argmax',modes=['none'])
  with self.assertRaisesRegex(ValueError,'Resume requires'):
   run(cfg,['0'],0,launcher=lambda *a,**kw:self.fail('must refuse before launch'))
 def test_rule_literals(self):
  s=ast.parse((P/'b/e2e_reader/stage1.py').read_text());cls=next(x for x in s.body if isinstance(x,ast.ClassDef) and x.name=='StageOne')
  f=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='select')
  numbers=[x.value for x in ast.walk(f) if isinstance(x,ast.Constant) and type(x.value) in (float,int)]
  self.assertTrue(set(numbers)<={0,1},numbers)
  self.assertFalse(any(isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='open' for x in ast.walk(f)))
 def test_parse_changed(self):
  for p in P.rglob('*.py'):
   old=W/'in/pkg/p'/p.relative_to(P)
   if not old.exists() or old.read_bytes()!=p.read_bytes():ast.parse(p.read_text())

if __name__=='__main__':unittest.main(verbosity=2)
