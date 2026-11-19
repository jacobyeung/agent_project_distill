from pathlib import Path
import sys,os
from contextlib import ExitStack
from unittest.mock import patch
B=Path(__file__).resolve().parent;sys.path.insert(0,str(B))
import native19 as N
with ExitStack() as stack:
    stack.enter_context(patch.object(Path,'open',N.retain_open));stack.enter_context(patch.object(Path,'mkdir',N.retain_mkdir))
    stack.enter_context(patch.object(N.C,'processor_for',N.processor))
    stack.enter_context(patch('student_pilot.decoupled_v_run.processor_for',N.processor))
    original=os.uname();host=os.uname_result((original.sysname,'fixture-host',original.release,original.version,original.machine))
    stack.enter_context(patch.object(os,'uname',return_value=host));stack.enter_context(patch.dict(os.environ,STUDENT_R2_FRAME_HOST='1'))
    summary=N.load(N.O/'RESULT.json')
    for step in (400,600):
        root=N.O/str(step);request=N.load(root/'request.json');cfg=N.load(root/'request_config.json')
        summary['twins'][str(step)]=N.twins(request,cfg,request['staged_pins'][2],root)
        print(step,summary['twins'][str(step)]['non_R1']['refusal'],flush=True)
    N.write(N.O/'RESULT.json',summary)
output=B/'proofs/native_twins';output.mkdir(parents=True,exist_ok=True);N.m.save(output)
