"""Gated S1c and single-arm R0-dev capture runner. Imports CUDA only after authorization."""
import argparse,os,socket,time
from common import *
from gates import *
import selection

def run(a):
 if Path(a.go_file).resolve()!=W/'configs'/f'GO_{a.run_id}.json':raise PermissionError('GO must use configs/GO_<run_id>.json')
 manifest_path=W/'configs/R0DEV_ROOM_MANIFEST.json'
 visible=os.environ.get('CUDA_VISIBLE_DEVICES','')
 code=run_code_hashes();note=read(a.go_file)
 preauthorize(note,a.run_id,sha(manifest_path),digest(code),visible)
 prerequisites(a.provenance,a.reader_receipt)
 assert sha(W/'evidence/direct_m200_room134.json')==BASE
 for field,path in [('provenance_sha256',a.provenance),('reader_receipt_sha256',a.reader_receipt)]:
  if note.get(field)!=sha(path):raise PermissionError('GO mismatch '+field)
 root=W/'out/room_pricing';root.mkdir(parents=True,exist_ok=True)
 if any((root/n).exists() for n in ['ROOM_PRED.jsonl','PRICING_TABLE.json','DECISION_REGISTRATION.json']):raise RuntimeError('R0-dev look already registered or consumed')
 chosen=None
 if a.stage=='r0dev':chosen=selection.load_selection(root,code)
 inputs={**code,str(manifest_path):sha(manifest_path),a.go_file:sha(a.go_file),a.provenance:sha(a.provenance),a.reader_receipt:sha(a.reader_receipt),str(KIT/'KIT_SEAL.json'):sha(KIT/'KIT_SEAL.json'),str(KIT/'assets/da3/model.safetensors'):sha(KIT/'assets/da3/model.safetensors'),str(W/'evidence/direct_m200_room134.json'):BASE}
 budget=Budget(root/'COST.json',inputs);budget.start();state='FAILED';records=[];backend=None;card_verified=False;uuid=note['gpu_uuid']
 try:
  import torch
  torch.set_num_threads(8)
  count=torch.cuda.device_count()
  if count!=1:raise PermissionError('exactly one actual visible CUDA device required')
  props=torch.cuda.get_device_properties(0)
  uuid='GPU-'+str(props.uuid)
  authorize(note,a.run_id,sha(manifest_path),digest(code),dict(uuid=uuid,total_memory=props.total_memory),count,visible)
  card_verified=True
  import numpy as np
  import geo_bakeoff.backends as back
  from geo_bakeoff.contract import sample_grid
  def gate(device,*args):
   if device!='cuda':raise PermissionError('GPU run must use cuda')
   if torch.cuda.device_count()!=1 or os.environ.get('CUDA_VISIBLE_DEVICES','')!=uuid:raise PermissionError('device allocation changed')
  back.validate_device=gate
  def capture(arm,ident,scene,frames,anchors,paths,hashes,manifest_sha):
   nonlocal backend
   ih={str(p):sha(p) for p in paths}
   if ih!=hashes:raise ValueError('frame digest mismatch '+scene)
   slots=[frames.index(i) for i in anchors]
   binding=dict(model='da3',weights_sha256=inputs[str(KIT/'assets/da3/model.safetensors')],code_sha256=code,seal_sha256=inputs[str(KIT/'KIT_SEAL.json')],manifest_sha256=manifest_sha,frames=frames,item_slots=slots,frame_sha256=ih,settings=SETTINGS,arm=arm)
   dest=root/'pred'/arm/scene
   if resume(dest,binding,budget.previous)=='valid':records.append(read(dest/'DONE.json'));return
   if time.monotonic()-budget.start_time+120>=budget.remaining:raise TimeoutError('insufficient budget for next capture')
   dest.mkdir(parents=True,exist_ok=True)
   previous_started=read(dest/'STARTED.json') if (dest/'STARTED.json').exists() else None
   write(dest/'STARTED.json',dict(binding=binding,run_id=a.run_id,host=socket.gethostname(),card_uuid=uuid,previous_started=previous_started),{**inputs,**ih})
   start=time.monotonic()
   if backend is None:backend=back.Backend('da3','cuda',8,a.go_file)
   torch.cuda.reset_peak_memory_stats()
   try:prediction=backend.predict([str(p) for p in paths],resolution=504)
   except torch.cuda.OutOfMemoryError:
    write(root/'ARM_DROPPED.json',dict(arm=arm,reason='CUDA OOM; resolution remains 504; no alternative arm or R0-dev pricing allowed',scene=scene,run_id=a.run_id),{**inputs,**ih})
    raise
   torch.cuda.synchronize()
   with (dest/'pred.npz.part').open('wb') as partial:np.savez_compressed(partial,frame_indices=frames,item_slots=slots,depth_grid=sample_grid(prediction.depth).astype(np.float32),intrinsics=prediction.intrinsics.astype(np.float64),c2w=prediction.c2w.astype(np.float64),source_hw=prediction.source_hw)
   os.replace(dest/'pred.npz.part',dest/'pred.npz')
   rec=dict(binding=binding,pred_sha256=sha(dest/'pred.npz'),seconds=time.monotonic()-start,peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved(),run_id=a.run_id,host=socket.gethostname(),card_uuid=uuid,gt_used=False,arm=arm,id=ident)
   write(dest/'DONE.json',rec,{**inputs,**ih});records.append(rec)
  if a.stage in ('s1c','all'):
   if (root/'SELECTION.json').exists():chosen=selection.load_selection(root,code)
   else:
    rows,caps,ins=selection.register(root,code);inputs.update(ins)
    inputs[str(root/'S1C_REGISTRATION.json')]=sha(root/'S1C_REGISTRATION.json')
    for r in rows:
     c=caps[r['capture']];frames=list(c['anchor_indices']);fs={int(f['index']):f for f in c['dense_frames']};paths=[Path(fs[i]['path']) for i in frames]
     capture('k1_f32',r['row_id'],r['capture'].replace('/','__'),frames,frames,paths,{str(Path(fs[i]['path'])):fs[i]['sha256'] for i in frames},sha(K1))
    chosen=selection.select(root)
  if a.stage in ('r0dev','all'):
   chosen=selection.load_selection(root,code)
   inputs[str(root/'SELECTION.json')]=sha(root/'SELECTION.json')
   arm=chosen['arm']
   if (root/'ARM_DROPPED.json').exists():raise RuntimeError('arm was dropped; no automatic retry or fallback')
   for item in read(manifest_path)['items']:
    frames=item['frame_indices'] if arm=='da3_f32' else item['union_indices'];paths=[R0/'frames/scannetpp'/item['scene']/f'{i:06d}.png' for i in frames]
    capture(arm,item['id'],item['scene'],frames,item['frame_indices'],paths,{str(p):item['frame_sha256'][str(i)] for i,p in zip(frames,paths)},sha(manifest_path))
  state='COMPLETE'
 finally:
  budget.finish(state)
  write(root/'RUN_RECEIPT.json',dict(state=state,stage=a.stage,host=socket.gethostname(),card_uuid=uuid,card_verified=card_verified,run_id=a.run_id,gt_used=False,captures=records,guard='diagnostic only; skipped',part_b='forbidden on R0-dev'),inputs)

def main():
 p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--go-file',required=True);p.add_argument('--provenance',required=True);p.add_argument('--reader-receipt',required=True);p.add_argument('--stage',choices=['s1c','r0dev','all'],default='r0dev')
 run(p.parse_args())
if __name__=='__main__':main()
