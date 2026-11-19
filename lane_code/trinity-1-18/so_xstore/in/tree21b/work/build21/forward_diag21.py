from pathlib import Path
import sys,traceback,json,os
B=Path(__file__).resolve().parent;sys.path.insert(0,str(B))
import native21 as N
from unittest.mock import patch
from contextlib import ExitStack
root=N.O/'400/q';cfg=N.load(root/'h/config.json')
with ExitStack() as stack:
 stack.enter_context(N.P.proof_scope())
 stack.enter_context(patch.object(Path,'open',N.retain_open))
 stack.enter_context(patch.object(N.C,'processor_for',N.processor))
 stack.enter_context(patch('student_pilot.decoupled_v_run.processor_for',N.processor))
 value=cfg['r1_training']
 closure=N.P.verify(value['handover_receipt'],value['p_run'],cfg['init_artifact']['artifact'],value['persisted_files'],weights=True,proof_mode='q')
 try:
  with N.P.scope(closure['paths']):result=N.Q.forward(cfg,root,400)
  print(json.dumps(result))
 except Exception:traceback.print_exc()
