import hashlib,json,sys,types
from pathlib import Path
import numpy as np
import torch
W=Path(__file__).resolve().parents[1];T=W/'work'/sys.argv[1];sys.path.insert(0,str(T));p=types.ModuleType('tests');p.__path__=[str(T/'tests')];sys.modules['tests']=p
torch.set_num_threads(16)
from tests.test_carrier_c1_final import final_fixture
from tests.test_tower_read import tower_state,tower_batch
from student_pilot.carrier_c1_decode import HeadState
from student_pilot.carrier_c1 import parameter_groups
from student_pilot import carrier_c1_run as run
m,b,t=final_fixture();b.update(tower_batch());m.eval()
def h(v):
 if isinstance(v,torch.Tensor):v=v.detach().contiguous().numpy()
 return hashlib.sha256(np.asarray(v).tobytes()).hexdigest()
with torch.no_grad():
 hidden=m.hidden(b)
 own=HeadState(m,b,hidden)
 tower=HeadState(m,b,hidden,pose_source='tower',tower_state=tower_state())
 outputs={k:h(v) for k,v in dict(hidden=hidden,own_pose=own.pose9,own_depth=own.depth(1,[[200,300],[500,500]]),tower_pose=tower.pose9,tower_scale=np.float64(tower.tower_scale),tower_depth=tower.depth(1,[[200,300],[500,500]])).items()}
outputs['groups']=[dict(name=g['name'],lr=g['lr'],parameters=len(g['params'])) for g in parameter_groups(m)]
outputs['state']={k:h(v) for k,v in m.state_dict().items()}
outputs['plain_module_groups']=[dict(name=g['name'],lr=g['lr'],parameters=len(g['params'])) for g in parameter_groups(torch.nn.Linear(3,2))]
inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),*(T/'student_pilot'/n for n in ('carrier_c1.py','carrier_c1_run.py','carrier_c1_decode.py','tower_read.py','tower_scale.py','tower_scale_rule.py')),T/'tests/test_carrier_c1_final.py',T/'tests/test_tower_read.py']}
(W/'out'/('ABSENT_'+sys.argv[1].upper()+'.json')).write_text(json.dumps(dict(input_sha256=inputs,outputs=outputs,command=f'nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/absent_parity.py {sys.argv[1]}'),indent=2)+'\n')
print(sys.argv[1],len(outputs['state']),'tensor hashes')
