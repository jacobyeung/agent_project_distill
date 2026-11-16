"""CPU fixtures only: bind real immutable adapters, never launch an engine."""
import offline_guard
import importlib.util
import json
from pathlib import Path
import sys

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,'/scratch/jjyeung/orch_n30/evalx27/work/kit/proof')
import fakes
fakes.install()
spec=importlib.util.spec_from_file_location('candidate_worker',root/'kit/reader/worker.py')
W=importlib.util.module_from_spec(spec);spec.loader.exec_module(W)
family=sys.argv[1];out=Path(sys.argv[2]);step=int(sys.argv[3]) if len(sys.argv)>3 else 100
models=json.loads((root/'kit/launcher/MODELS.json').read_text())
models['cp1m200']=dict(models['cp1m200'],path=models['cp1m200']['path'].replace('469ddece/m544','359fcc3c/m'+str(step)))
config=dict(spec=dict(models=models,artifact=models['cp1m200'],step=step))
runtime=Path('/scratch/jjyeung/orch_n30/evalx27/work/pull/x27c/r2/sj/orch_cd')
camera=Path('/scratch/jjyeung/orch_n30/trin_read/root/sj/orch_cd/evalx/work/camera')
result=W.bind(config,family,out,reader=runtime/'legs1_reads',kit=runtime/'rv_merge_fix/work/r3/aws_vl64rt',camera=camera)
direct,origin,media,dest,cfg,tasks,captures=result
accepted=Path('/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/direct')/family
assert (dest/'PROMPT_PINS.json').read_bytes()==(accepted/'PROMPT_PINS.json').read_bytes()
value=dict(family=family,items=len(tasks),prompts_byte_equal=True,source=cfg['source_sha256'],
                     need=len({f['sha256'] for c in captures.values() for f in c['frames']}),
                     rgb_bytes=sum(c['hw'][0]*c['hw'][1]*3*len(c['frames']) for c in captures.values()),
                     real_gpu=False,step=step)
(out/'BIND_CHECK.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(value))
