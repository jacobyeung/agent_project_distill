"""Exercise the unmodified native sampler with N's actual bound inputs."""
import sys,json,hashlib
from pathlib import Path
T=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1')
sys.path.insert(0,str(T))
from student_pilot.p3_provenance import load,pinned
from student_pilot.r1_mix import plans
W=Path(__file__).resolve().parent
cfgpath=T.parent.parent/'out/N_LAUNCH_CONFIG.json'; cfg=load(cfgpath)
inputs=[]
for path in [cfgpath,Path(__file__),T/'student_pilot/r1_mix.py',T/'student_pilot/r1_population.py',T/'student_pilot/r1_loader.py',T/'student_pilot/r1_training.py']+[Path(pinned(pin)) for pin in cfg['r2_sampling'].values() if isinstance(pin,dict)]:
 inputs.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
try:
 # Validation rejects the incomplete population before reading stream counts.
 next(plans(cfg['r2_sampling'],{},1000))
 result={'status':'UNEXPECTED_SUCCESS'}
except ValueError as e:
 result={'status':'MISSING','native_error':str(e),'before_draws':'MISSING','after_draws':'MISSING','reason':'No complete prepared population is supplied; validation fails before stream counts are consumed.'}
for module in list(sys.modules.values()):
 path=getattr(module,'__file__',None)
 if path and str(path).startswith(str(T)) and Path(path).is_file() and not any(i['path']==str(path) for i in inputs):
  inputs.append(dict(path=str(path),sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest()))
result['inputs']=inputs
result['supported_per_row_delta']=False
result['code_lines']={
 'ceiling':'r1_mix.py:27 min(n, 4*counts[k]); r1_loader.py:92-93 checks per-qid repeats > 4',
 'unique_population':'r1_mix.py:76-79 rejects duplicate offsets; 83-84 requires full index coverage',
 'uniform_selection':'r1_mix.py:81-82 seeded shuffle; 96 cycles through each cell uniformly',
 'population_builder':'r1_population.py:120-130 assigns each native offset to exactly its family cell',
}
(W/'out/LOADER_BOUNDARY.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
