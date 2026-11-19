"""Sequential eight-core S1c fallback. No CUDA, held-out capture or R0-dev read."""
import os,resource,time
from common import *
from gates import run_code_hashes,SETTINGS
import selection

def main():
 os.environ['CUDA_VISIBLE_DEVICES']=''
 os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:8])
 resource.setrlimit(resource.RLIMIT_AS,(39*1024**3,39*1024**3))
 import torch
 torch.set_num_threads(8)
 import numpy as np
 import geo_bakeoff.backends as back
 from geo_bakeoff.contract import sample_grid
 def gate(device,*args):
  if device!='cpu':raise PermissionError('S1c CPU only')
 back.validate_device=gate
 root=W/'out/room_pricing';code=run_code_hashes()
 if any((root/n).exists() for n in ['SELECTION.json','DECISION_REGISTRATION.json','ROOM_PRED.jsonl','PRICING_TABLE.json']):raise RuntimeError('selection or R0-dev look already frozen')
 rows,caps,ins=selection.register(root,code)
 ins.update(code);ins[str(root/'S1C_REGISTRATION.json')]=sha(root/'S1C_REGISTRATION.json')
 for p in [KIT/'KIT_SEAL.json',KIT/'assets/da3/model.safetensors']:ins[str(p)]=sha(p)
 backend=None
 for r in rows:
  c=caps[r['capture']];frames=list(c['anchor_indices']);by={int(f['index']):f for f in c['dense_frames']};fs=[by[i] for i in frames]
  hashes={f['path']:sha(f['path']) for f in fs}
  if hashes!={f['path']:f['sha256'] for f in fs}:raise ValueError('frame digest mismatch')
  binding=dict(model='da3',weights_sha256=ins[str(KIT/'assets/da3/model.safetensors')],code_sha256=code,seal_sha256=ins[str(KIT/'KIT_SEAL.json')],manifest_sha256=sha(K1),frames=frames,item_slots=list(range(32)),frame_sha256=hashes,settings=dict(SETTINGS,autocast='float32'),arm='k1_f32',device='cpu',threads=8)
  dest=root/'pred/k1_f32'/r['capture'].replace('/','__')
  if resume(dest,binding)=='valid':continue
  write(dest/'STARTED.json',dict(binding=binding,run_id='s1c-cpu'),{**ins,**hashes})
  start=time.monotonic()
  if backend is None:backend=back.Backend('da3','cpu',8,None)
  pred=backend.predict([f['path'] for f in fs],resolution=504)
  np.savez_compressed(dest/'pred.npz',frame_indices=frames,item_slots=list(range(32)),depth_grid=sample_grid(pred.depth).astype(np.float32),intrinsics=pred.intrinsics.astype(np.float64),c2w=pred.c2w.astype(np.float64),source_hw=pred.source_hw)
  write(dest/'DONE.json',dict(binding=binding,pred_sha256=sha(dest/'pred.npz'),seconds=time.monotonic()-start,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,gt_used=False,host=os.uname().nodename,run_id='s1c-cpu',card_uuid=None),{**ins,**hashes})
 selection.select(root)
if __name__=='__main__':main()
