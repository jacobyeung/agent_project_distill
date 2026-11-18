"""Execute the patched select method with a stub tensor API; real Torch replay remains separate."""
import ast,json,unittest
from pathlib import Path
from types import SimpleNamespace as NS
W=Path(__file__).resolve().parents[1]
class Tensor(list):
 def __getitem__(self,k):
  v=super().__getitem__(k);return Tensor(v) if isinstance(k,slice) else v
class Torch:
 @staticmethod
 def no_grad():return lambda f:f
 @staticmethod
 def argmax(x):return max(range(len(x)),key=lambda i:x[i])

def method(source):
 tree=ast.parse(source);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='StageOne')
 fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='select')
 module=ast.Module(body=[fn],type_ignores=[]);ns={'torch':Torch};exec(compile(module,'patched-select','exec'),ns);return ns['select']
SOURCE=(W/'out/src/b/e2e_reader/stage1.py').read_text()
SELECT=method(SOURCE)
def call(fn,rule,slots):
 obj=NS(rule=rule,head=NS(with_null=lambda *args:Tensor(slots)),diagnostics={})
 return fn(obj,{'name':'x','x':Tensor([None]*(len(slots)-1))})

def check(fn):
 for slots in ([1,2,99],[2,2,99],[-4,-2,99],[0,99],[99]):
  n=len(slots)-1;want=Torch.argmax(slots[:-1]) if n else -1
  assert call(fn,'candidates_argmax',slots)==want
 for slots in ([1,2,99],[2,2,1],[-4,-2,-3],[0,99]):
  k=Torch.argmax(slots)
  assert call(fn,'null_argmax',slots)==(-1 if k==len(slots)-1 else k)

class StubTests(unittest.TestCase):
 def test_real_method_stub_head(self):check(SELECT)
 def test_off_by_one_mutant_fails(self):
  mutant=SOURCE.replace("slots[:len(inputs['x'])]","slots[:len(inputs['x'])+1]")
  with self.assertRaises(AssertionError):check(method(mutant))
 def test_ignored_rule_mutant_fails(self):
  mutant=SOURCE.replace("if rule == 'candidates_argmax':","if False:")
  with self.assertRaises(AssertionError):check(method(mutant))
 def test_null_matches_original(self):
  old=method((W/'out/baseline/b/e2e_reader/stage1.py').read_text())
  import random
  rng=random.Random(17)
  for n in range(1,70):
   slots=[rng.randrange(-3,4) for _ in range(n+1)]
   self.assertEqual(call(SELECT,'null_argmax',slots),call(old,'null_argmax',slots))
 def test_printed_format_and_mutant(self):
  from collections import Counter
  source=(W/'out/src/b/e2e_reader/callhook.py').read_text()
  def responder(s):
   tree=ast.parse(s);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='CallHook')
   fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='respond')
   ns=dict(call_family=lambda call:'ground',Unserved=type('Unserved',(Exception,),{}),OPEN='<tool_response>',CLOSE='</tool_response>')
   exec(compile(ast.Module(body=[fn],type_ignores=[]),'respond','exec'),ns);return ns['respond']
  def check_format(fn):
   cases=['chair: not seen','chair: frames 1 (best 1)\nB1: f1 centre (1.00, 2.00, 3.00) m','error: invalid_name']
   for text in cases:
    obj=NS(counts=Counter(),unserved=Counter(),servers={'ground':lambda c:(text,{'stage1':{}})},
           error_suffix=False,ground_layout=True,tokenizer=NS(encode=lambda s,**kw:list(s.encode())),records=[],ids=[])
    result=fn(obj,'<ground obj="chair" mode="box">')
    assert bytes(result)==('\n<tool_response>\n'+text+'\n</tool_response>').encode()
  check_format(responder(source))
  mutant=source.replace("wrapped = ('\\n' + OPEN", "wrapped = (' ' + OPEN")
  assert mutant!=source
  with self.assertRaises(AssertionError):check_format(responder(mutant))
 def test_settings_mutant_fails_wiring_assertion(self):
  source=(W/'out/src/h1eval/h10/perception_own.py').read_text()
  def wiring(s):
   tree=ast.parse(s)
   assignments=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='stage1_factory']
   assert len(assignments)==1
   value=next(k.value for k in assignments[0].keywords if k.arg=='rule')
   expression=ast.Expression(value)
   for rule in ('null_argmax','candidates_argmax'):
    assert eval(compile(expression,'factory rule','eval'),{},dict(self=NS(settings={'stage1_select_rule':rule})))==rule
  wiring(source)
  with self.assertRaises(AssertionError):wiring(source.replace("self.settings.get('stage1_select_rule', 'null_argmax')","'null_argmax'"))

if __name__=='__main__':unittest.main(verbosity=2)
