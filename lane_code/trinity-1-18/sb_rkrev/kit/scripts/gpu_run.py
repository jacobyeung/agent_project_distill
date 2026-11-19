"""S2 gated runner. Never invoke without the orchestrator's bound authorization."""
import argparse,os,socket,time
from common import *
from gates import *
p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--go-file',required=True);p.add_argument('--provenance',required=True);p.add_argument('--reader-receipt',required=True);a=p.parse_args()
prerequisites(a.provenance,a.reader_receipt)
manifest_path=W/'configs/R0DEV_ROOM_MANIFEST.json';manifest=read(manifest_path)
assert sha(W/'evidence/direct_m200_room134.json')==BASE
visible=os.environ.get('CUDA_VISIBLE_DEVICES','')
code=run_code_hashes();note=read(a.go_file)
preauthorize(note,a.run_id,sha(manifest_path),digest(code),visible)
uuid=note['gpu_uuid'];card_verified=False
for field,path in [('provenance_sha256',a.provenance),('reader_receipt_sha256',a.reader_receipt)]:
 if note.get(field)!=sha(path):raise PermissionError('GO mismatch '+field)
inputs={**code,str(manifest_path):sha(manifest_path),a.go_file:sha(a.go_file),a.provenance:sha(a.provenance),a.reader_receipt:sha(a.reader_receipt),str(KIT/'KIT_SEAL.json'):sha(KIT/'KIT_SEAL.json'),str(KIT/'assets/da3/model.safetensors'):sha(KIT/'assets/da3/model.safetensors'),str(W/'evidence/direct_m200_room134.json'):BASE}
root=W/'out/room_pricing';root.mkdir(exist_ok=True)
(root/'R0DEV_ROOM_MANIFEST.json').write_bytes(manifest_path.read_bytes())
# One cumulative ledger across run IDs, including loads and retries.
budget=Budget(root/'COST.json',inputs);budget.start();state='FAILED';records=[];backend=None
try:
 import torch
 count=torch.cuda.device_count()
 if count!=1:raise PermissionError('exactly one actual visible CUDA device required')
 props=torch.cuda.get_device_properties(0)
 authorize(note,a.run_id,sha(manifest_path),digest(code),dict(uuid=str(props.uuid),total_memory=props.total_memory),count,visible)
 card_verified=True
 import numpy as np
 import geo_bakeoff.backends as back
 from geo_bakeoff.contract import sample_grid
 def gate(device,*args):
  if device!='cuda':raise PermissionError('GPU run must use cuda')
  authorize(note,a.run_id,sha(manifest_path),digest(code),dict(uuid=uuid,total_memory=props.total_memory),torch.cuda.device_count(),os.environ.get('CUDA_VISIBLE_DEVICES',''))
 back.validate_device=gate
 for arm in ['da3_f32','da3_u94']:
  secondary_probe=False
  for item in manifest['items']:
   frames=item['frame_indices'] if arm=='da3_f32' else item['union_indices'];slots=[frames.index(i) for i in item['frame_indices']]
   paths=[R0/'frames/scannetpp'/item['scene']/f'{i:06d}.png' for i in frames]
   ih={str(p):sha(p) for p in paths}
   for i,p in zip(frames,paths):
    if ih[str(p)]!=item['frame_sha256'][str(i)]:raise ValueError('frame digest mismatch '+str(p))
   binding=dict(host=socket.gethostname(),card_uuid=uuid,run_id=a.run_id,model='da3',weights_sha256=inputs[str(KIT/'assets/da3/model.safetensors')],code_sha256=code,seal_sha256=inputs[str(KIT/'KIT_SEAL.json')],manifest_sha256=sha(manifest_path),frames=frames,item_slots=slots,frame_sha256=ih,settings=SETTINGS)
   dest=root/'pred'/arm/item['scene']
   if resume(dest,binding)=='valid':
    done=read(dest/'DONE.json');records.append(done)
    if arm=='da3_u94':secondary_probe=True
    continue
   # Reserve enough remaining time before starting a load/capture; the deadline also interrupts Python.
   if time.monotonic()-budget.start_time+120>=budget.remaining:raise TimeoutError('insufficient budget for next capture')
   dest.mkdir(parents=True,exist_ok=True);write(dest/'STARTED.json',dict(binding=binding,run_id=a.run_id),{**inputs,**ih})
   start=time.monotonic()
   if backend is None:backend=back.Backend('da3','cuda',8,a.go_file)
   torch.cuda.reset_peak_memory_stats()
   try:prediction=backend.predict([str(p) for p in paths],resolution=504)
   except torch.cuda.OutOfMemoryError:
    if arm!='da3_u94':raise
    write(root/'SECONDARY_DROPPED.json',dict(reason='CUDA OOM; resolution remains 504',scene=item['scene'],seconds=time.monotonic()-start,peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved()),{**inputs,**ih});break
   torch.cuda.synchronize()
   peak=torch.cuda.max_memory_allocated();reserved=torch.cuda.max_memory_reserved()
   if arm=='da3_u94' and not secondary_probe:
    write(root/'SECONDARY_MEMORY_PROBE.json',dict(peak_allocated_bytes=peak,peak_reserved_bytes=reserved,total_memory=props.total_memory,scene=item['scene'],passed=reserved<props.total_memory),{**inputs,**ih})
    if reserved>=props.total_memory:raise RuntimeError('secondary memory probe failed')
    secondary_probe=True
   np.savez_compressed(dest/'pred.npz',frame_indices=frames,item_slots=slots,depth_grid=sample_grid(prediction.depth).astype(np.float32),intrinsics=prediction.intrinsics.astype(np.float64),c2w=prediction.c2w.astype(np.float64),source_hw=prediction.source_hw)
   rec=dict(binding=binding,pred_sha256=sha(dest/'pred.npz'),seconds=time.monotonic()-start,peak_allocated_bytes=peak,peak_reserved_bytes=reserved,run_id=a.run_id,host=socket.gethostname(),card_uuid=uuid,gt_used=False,arm=arm,id=item['id'])
   write(dest/'DONE.json',rec,{**inputs,**ih});records.append(rec)
 state='COMPLETE'
finally:
 budget.finish(state)
 write(root/'RUN_RECEIPT.json',dict(state=state,host=socket.gethostname(),card_uuid=uuid,card_verified=card_verified,run_id=a.run_id,gt_used=False,captures=records,guard='MISSING authenticated dev-S1 reader frame receipt; skipped',part_b='exploratory; not run'),inputs)
