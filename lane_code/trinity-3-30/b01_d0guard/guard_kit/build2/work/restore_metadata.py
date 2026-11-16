"""Run unchanged metadata validators with a test-only path transport adapter."""
from pathlib import Path
import sys,os,json,importlib
B=Path(__file__).resolve().parents[1];W=B.parents[1]/'work';T=W/'from113/work/tree'
K=B/'out/guard_kit';C=K/'sj/orch_cd/evalx/work/milestone/native/out2'
os.environ['LEGS1_TREE']=str(T)
sys.path[:0]=[str(K),str(W/'from113/work/np226'),str(W/'from113/work/pyextra'),str(T),str(C)]
import closure
from guard_core import read,write,sha
from student_pilot import p3_provenance as P
SHARED=W/'from113/builds/01_c8/work/rehearsal_assets/d03de829ae52386f'
reads=[]
def physical(path):
 p=str(path)
 if p.startswith(str(B.parents[1])+'/'):return Path(path)
 if p==closure.ROOT+'k/t_b01ce449beffe35b.tar':return W/'from113/work/obj/t_b01ce449beffe35b.tar'
 if p.startswith(closure.ROOT):
  candidate=W/'d0closure/x'/p[len(closure.ROOT):]
  if candidate.is_file():return candidate
 for prefix,target in [('/scratch/jjyeung/',SHARED/'sj'),('/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/',SHARED/'fsw'),('/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/',SHARED/'fsw/ap')]:
  if p.startswith(prefix):return target/p[len(prefix):]
 return Path(path)
original=P.pinned
def pinned(pin):
 result=original(dict(pin,path=str(physical(pin['path']))));reads.append(dict(logical=pin['path'],physical=str(result),sha256=pin['sha256']));return result
P.pinned=pinned
# Dependencies import the adapter before the unchanged trainer is imported.
from student_pilot import carrier_c1_run as trainer
import common
common.local=lambda p:physical(p).resolve()
import read_runtime
from evalpath import runtime
files=closure.members(W/'d0closure/closure_359fcc3c.tar')
r=closure.authenticate(files,50,trainer,W/'from113/work/obj/m544_artifact.json')
art=dict(path=closure.ROOT+'runs/359fcc3c/m50/artifact.json',sha256=r['artifact_sha256'])
try:
 cfg,receipt,model=read_runtime.prepared(r['config'],art,r['data_receipt'])
 init=runtime.check_init_spec(receipt,art)
 result=dict(status='PASS',config_identity=trainer.identity(cfg),init_spec=init,model_manifest=receipt['model'],
             validator_source_sha256=sha(read_runtime.__file__),trainer_source_sha256=sha(trainer.__file__),
             path_transport_only=True,model_loaded=False,reads=reads)
except Exception as error:
 result=dict(status='FAIL',error=str(error),reads=reads);write(B/'out/RESTORATION_TEST.json',result);raise
write(B/'out/RESTORATION_TEST.json',result);print(json.dumps({k:v for k,v in result.items() if k!='reads'},indent=2))
