from pathlib import Path
import sys,ast,importlib.util,json,traceback
from copy import deepcopy
from contextlib import ExitStack
from unittest.mock import patch
B=Path(__file__).resolve().parent;sys.path.insert(0,str(B));import native21 as N
source=(N.T/'student_pilot/r2_openers.py').read_text()
for node in ast.parse((B/'opener_fix21.py').read_text()).body:
 if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and getattr(node.value.func,'id',None)=='edit':
  name,old,new=map(ast.literal_eval,node.value.args)
  if name=='student_pilot/r2_openers.py':source=source.replace(old,new)
target=B/'mutant/r2_openers.py';target.parent.mkdir(exist_ok=True);target.write_text(source)
spec=importlib.util.spec_from_file_location('student_pilot.preview_openers',target);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
from student_pilot import r2_openers as O
original=N.C.prepared
def prepared(cfg,*args,**kw):
 receipt,manifest=original(cfg,*args,**kw)
 if cfg.get('r1_training'):receipt={**receipt,'_r1_start_config':deepcopy(cfg)}
 return receipt,manifest
cfg=N.load(N.O/'400/q/h/config.json');root=B/'proofs/forward_preview';root.mkdir(exist_ok=True)
with ExitStack() as stack:
 if '--one-head' in sys.argv:
  from transformers import Qwen3_5ForConditionalGeneration,Qwen3_5Config
  original_load=Qwen3_5ForConditionalGeneration.from_pretrained
  def valid_constructor(root,*args,**kwargs):
   config=Qwen3_5Config.from_pretrained(root,local_files_only=True);config.vision_config.num_heads=1
   return original_load(root,*args,config=config,**kwargs)
  stack.enter_context(patch.object(Qwen3_5ForConditionalGeneration,'from_pretrained',valid_constructor))
 stack.enter_context(N.P.proof_scope())
 stack.enter_context(patch.object(N.C,'prepared',prepared))
 stack.enter_context(patch.object(O,'initialize',module.initialize))
 stack.enter_context(patch.object(N.C,'processor_for',N.processor))
 stack.enter_context(patch('student_pilot.decoupled_v_run.processor_for',N.processor))
 value=cfg['r1_training'];closure=N.P.verify(value['handover_receipt'],value['p_run'],cfg['init_artifact']['artifact'],value['persisted_files'],weights=True,proof_mode='q')
 try:
  with N.P.scope(closure['paths']):result=N.Q.forward(cfg,root,400)
  (root/'RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
 except Exception:traceback.print_exc()
