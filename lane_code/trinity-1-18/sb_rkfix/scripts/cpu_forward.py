"""S1 full sealed backend forward; 64 then 32 K1 frames and one R0-rl plumbing capture."""
import argparse,os,resource,time
from common import *
p=argparse.ArgumentParser();p.add_argument('--capture',required=True);p.add_argument('--worker',type=int,required=True);a=p.parse_args()
os.environ['CUDA_VISIBLE_DEVICES']=''
cpus=sorted(os.sched_getaffinity(0));os.sched_setaffinity(0,cpus[a.worker*6:(a.worker+1)*6])
resource.setrlimit(resource.RLIMIT_AS,(39*1024**3,39*1024**3))
import numpy as np
from geo_bakeoff.backends import Backend
from geo_bakeoff.contract import sample_grid
import geo_bakeoff.backends as back
# CPU gate is explicit and never inspects a CUDA device.
def gate(device,*args):
 if device!='cpu': raise PermissionError('CPU stage only')
back.validate_device=gate
m=read(K1); c=next(c for c in m['captures'] if c['canonical']==a.capture)
assert c['k1_split']=='train'
frames=[int(f['index']) for f in c['dense_frames']];slots=[frames.index(int(i)) for i in c['anchor_indices']]
inputs={str(K1):sha(K1),str(KIT/'KIT_SEAL.json'):sha(KIT/'KIT_SEAL.json'),str(KIT/'assets/da3/model.safetensors'):sha(KIT/'assets/da3/model.safetensors'),**code_hashes()}
tasks=[]
for mode,sel in [('k1_64',list(range(64))),('k1_32',slots)]:
 tasks.append((mode,a.capture,[c['dense_frames'][i] for i in sel],list(c['anchor_indices']),dict(inputs)))
qpath=R0/'out/qsets/R0_QUESTIONS_rl_f32.jsonl'
qs=sorted([q for q in map(json.loads,qpath.read_text().splitlines()) if q['question_type']=='room_size_estimation'],key=lambda q:q['scene'])
q=qs[a.worker];mp=R0/'out/frame_manifests'/f"{q['scene']}.json";fm=read(mp)
fs=[dict(index=i,path=str(R0/'frames/scannetpp'/q['scene']/f'{i:06d}.png'),sha256=fm['frames'][str(i)]) for i in q['frame_indices']]
tasks.append(('r0_rl32',q['scene'],fs,q['frame_indices'],{**inputs,str(qpath):sha(qpath),str(mp):sha(mp)}))
backend=None
for mode,cap,fs,anchors,ins in tasks:
 dest=W/'out/s1'/mode/cap.replace('/','__')
 for f in fs:
  assert sha(f['path'])==f['sha256'],f['path']; ins[f['path']]=f['sha256']
 frames=[f['index'] for f in fs];slots=[frames.index(i) for i in anchors]
 binding=dict(input_sha256=ins,frames=frames,item_slots=slots,settings=dict(model='da3',device='cpu',threads=6,resolution=504,seed=0,reference='saddle_balanced'))
 if resume(dest,binding)=='valid': print('SKIP',mode,cap,flush=True);continue
 dest.mkdir(parents=True,exist_ok=True);write(dest/'STARTED.json',dict(binding=binding),ins)
 start=time.monotonic();print('START',mode,cap,flush=True)
 try:
  if backend is None: backend=Backend('da3','cpu',6,None)
  pred=backend.predict([f['path'] for f in fs],resolution=504)
  np.savez_compressed(dest/'pred.npz',frame_indices=frames,item_slots=slots,depth_grid=sample_grid(pred.depth).astype(np.float32),intrinsics=pred.intrinsics.astype(np.float64),c2w=pred.c2w.astype(np.float64),source_hw=np.asarray(pred.source_hw))
  write(dest/'DONE.json',dict(binding=binding,pred_sha256=sha(dest/'pred.npz'),seconds=time.monotonic()-start,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,gt_used=False,host=os.uname().nodename),ins)
  print('DONE',mode,cap,time.monotonic()-start,flush=True)
 except BaseException as e:
  write(dest/'ERROR.json',dict(error=repr(e),seconds=time.monotonic()-start),ins);raise
