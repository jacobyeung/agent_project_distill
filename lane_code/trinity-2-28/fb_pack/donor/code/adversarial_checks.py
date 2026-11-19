import copy,json,os,sys,tempfile,types
from pathlib import Path
W=Path(__file__).resolve().parents[1];T=W/'work/new';sys.path.insert(0,str(T));p=types.ModuleType('tests');p.__path__=[str(T/'tests')];sys.modules['tests']=p
import torch
torch.set_num_threads(16)
from tests.test_scale_donor import fixture,source,settings,native_export
from student_pilot import scale_donor as D,carrier_c1_run as run
from student_pilot.p3_provenance import file_pin,sha256
O=Path(tempfile.mkdtemp(prefix='adversarial_',dir=W/'work'));m,_,_=fixture();cfg=settings(m,source(m,O/'source'),'V1');D.attach(m,cfg);pin=native_export(m,O/'export')
artifact=json.loads(Path(pin['path']).read_text());original=torch.load(O/'export/heads.pt',weights_only=True)
checks=[]
for prefix in ('scale_donor.point_depth.','scale_donor.fov.','scale_donor.frame_queries','depth.model.visual.'):
 state=copy.deepcopy(original);key=next(k for k in state if k.startswith(prefix));state[key].reshape(-1)[0]+=1
 q=O/str(len(checks));q.mkdir();torch.save(state,q/'heads.pt');a=copy.deepcopy(artifact);a['heads']=file_pin(q/'heads.pt');(q/'artifact.json').write_text(json.dumps(a))
 fresh,_,_=fixture();D.attach(fresh,cfg)
 try:run.load_artifact(fresh,file_pin(q/'artifact.json'))
 except ValueError as e:
  assert 'changed since initialization' in str(e),str(e);checks.append(dict(tensor=key,refused=True,error=str(e)))
 else:raise AssertionError('Changed export tensor accepted: '+key)
# A forger changing both self-reported hashes still cannot change pinned source weights.
state=copy.deepcopy(original);key=next(k for k in state if k.startswith('scale_donor.point_depth.'));state[key].reshape(-1)[0]+=1
meta=copy.deepcopy(state['_scale_donor']);meta['tensors']=D.tensor_pins({k.removeprefix(D.PREFIX):v for k,v in state.items() if k.startswith(D.PREFIX)})
try:D.verify_export(m,state,meta)
except ValueError as e:checks.append(dict(case='forged_internal_tensor_hashes',refused=True,error=str(e)))
else:raise AssertionError('Forged internal hashes accepted')
result=dict(input_sha256={pin['path']:pin['sha256'],cfg['checkpoint']['path']:cfg['checkpoint']['sha256'],str(Path(__file__)):sha256(__file__),str(T/'student_pilot/scale_donor.py'):sha256(T/'student_pilot/scale_donor.py'),str(T/'student_pilot/carrier_c1_run.py'):sha256(T/'student_pilot/carrier_c1_run.py')},status='PASS',checks=checks,command='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/adversarial_checks.py')
(W/'out/ADVERSARIAL.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(checks),'changed export attacks refused')
