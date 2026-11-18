"""Compare D0 bind prompt bytes with retained real m200 returns, without model or frame IO."""
import offline_guard
import importlib.util
import json
from pathlib import Path
import sys
import uuid
ROOT=Path(__file__).resolve().parents[1]
step=int(sys.argv[1]);family=sys.argv[2]
spec=importlib.util.spec_from_file_location('outer_worker',ROOT/'kit/reader/worker.py')
W=importlib.util.module_from_spec(spec);spec.loader.exec_module(W)
models=json.loads((ROOT/'kit/launcher/MODELS.json').read_text())
models['cp1m200']=dict(kind='c1_export',path='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/359fcc3c/m'+str(step)+'/artifact.json',sha256='a'*64)
cfg=dict(spec=dict(models=models,artifact=models['cp1m200'],step=step))
out=ROOT/'evidence'/('bind_'+str(step)+'_'+family+'_'+uuid.uuid4().hex)
result=W.bind(cfg,family,out,reader=ROOT/'readk/kit/reader',kit=ROOT/'readk/evidence/test_fix2_bind_main1000/a0/kit')
_,_,_,dest,bound,tasks,_=result
accepted=ROOT/'readk/kit/build/a4cadd8934b/fetched/x'/family/'a0/PROMPT_PINS.json'
assert (dest/'PROMPT_PINS.json').read_bytes()==accepted.read_bytes()
value=dict(step=step,family=family,items=len(tasks),prompts_byte_equal=True,source_sha256=bound['source_sha256'],output=str(out))
(out/'BIND_CHECK.json').write_text(json.dumps(value)+'\n')
print(json.dumps(value))
