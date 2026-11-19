"""Deferred GPU backends. No import of torch or model load in CPU planning."""
from common import *
import numpy as np

def images(frames):
 from PIL import Image
 out=[]
 for f in frames:
  assert sha(f['path'])==f['sha256']
  with Image.open(local(f['path'])) as im:out.append(im.convert('RGB'))
 return out

def g3t(scene,dense=False):
 import torch
 from student_pilot.tower_read import FrozenG3TTower
 cfg=js(ROOT/'config/PATHS.json')['sam']
 for k in ('tower_weights','tower_config'):assert sha(cfg[k]['path'])==cfg[k]['sha256']
 frames=scene['frames'] if dense else [f for f in scene['frames'] if f['index'] in scene['f32']];im=images(frames);indices=[f['index'] for f in frames];slots=[indices.index(f) for f in scene['f32']]
 tower=FrozenG3TTower(dict(weights_path=cfg['tower_weights']['path'],config_path=cfg['tower_config']['path'],device='cuda:0',dense_frames=len(frames),depth_chunk_size=8,dtype='bf16'))
 start=time.monotonic();torch.cuda.reset_peak_memory_stats()
 state=tower.run(dict(tower_native_frames=im,tower_frame_indices=indices,tower_anchor_slots=slots,frame_indices=scene['f32']),all_depth=True);torch.cuda.synchronize()
 assert state.points_grid is not None,'MISSING G3T point head output required by v2'
 data=dict(points_grid=state.points_grid,raw_pose=state.raw_pose9,depth_grid=state.depth_grid,depth_conf_grid=state.depth_conf_grid,frame_indices=state.frame_indices,anchor_slots=state.anchor_slots,depth_slots=state.depth_slots,grid_uv=state.grid_uv,source_hw=np.array([im[0].height,im[0].width]))
 stats=dict(seconds=time.monotonic()-start,peak_gpu_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved());return data,stats

def sam(scene,names,dense=False,base=None):
 import torch
 from student_pilot.sam3_tower import Sam3Tower
 from student_pilot.routed_features import rle,resize
 from e2e_reader.stage1 import sam3_detect
 cfg=js(ROOT/'config/PATHS.json')['sam']
 for k in ('sam_checkpoint','sam_receipt'):assert sha(cfg[k]['path'])==cfg[k]['sha256']
 frames=scene['frames'] if dense else [f for f in scene['frames'] if f['index'] in scene['f32']]
 extra=[f for f in frames if not dense or f['index'] not in scene['f32']];im=images(extra)
 tower=Sam3Tower(dict(device='cuda:0',checkpoint_path=cfg['sam_checkpoint']['path'],receipt_path=cfg['sam_receipt']['path'],source_root=str(local(cfg['sam_source'])),precision='bf16'))
 start=time.monotonic();torch.cuda.reset_peak_memory_stats();features=tower.encode(im)
 out=dict(phrases=names,frame_indices=[f['index'] for f in frames],frames={str(i):dict(phrases={}) for i in range(len(frames))},contract=dict(raw_name=True,joint_floor=.05,cap=30,raster=[80,112],reader_raster_preserved=[480,640]))
 slots={f['index']:i for i,f in enumerate(frames)}
 if dense:
  if base is None:raise Missing('T94 requires completed f32 SAM output')
  for i,index in enumerate(scene['f32']):
   for name in names:out['frames'][str(slots[index])]['phrases'][name]=base['frames'][str(i)]['phrases'][name]
 for name in names:
  for frame,entries in zip(extra,sam3_detect(tower,features,name),strict=True):
   out['frames'][str(slots[frame['index']])]['phrases'][name]=dict(presence=entries[0]['presence'] if entries else 0.,instances=[dict(score=e['score'],mask=rle(resize(e['mask'],(80,112))),reader_mask=rle(e['mask'])) for e in entries])
 torch.cuda.synchronize();return out,dict(seconds=time.monotonic()-start,peak_gpu_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved())

def track(scene,name):
 import torch
 from student_pilot.routed_features import rle,resize
 cfg=js(ROOT/'config/PATHS.json')['sam']
 assert sha(cfg['sam_checkpoint']['path'])==cfg['sam_checkpoint']['sha256'];sys.path.insert(0,str(local(cfg['sam_source'])))
 from sam3.model_builder import build_sam3_video_predictor
 # The source accepts a frame directory. Link pinned local images in temporal order.
 folder=ROOT/'work/track_frames'/scene['scene'];folder.mkdir(parents=True,exist_ok=True)
 fs=[f for f in scene['frames'] if f['index'] in scene['f32']]
 for i,f in enumerate(fs):
  assert sha(f['path'])==f['sha256'];p=folder/f'{i:06d}.png'
  if p.exists():assert p.resolve()==local(f['path'])
  else:p.symlink_to(local(f['path']))
 predictor=build_sam3_video_predictor(checkpoint_path=cfg['sam_checkpoint']['path'],gpus_to_use=[0],strict_state_dict_loading=True,compile=False)
 start=time.monotonic();torch.cuda.reset_peak_memory_stats();session=predictor.handle_request(dict(type='start_session',resource_path=str(folder)));sid=session['session_id'];tracks={}
 try:
  predictor.handle_request(dict(type='add_prompt',session_id=sid,frame_index=0,text=name))
  for result in predictor.handle_stream_request(dict(type='propagate_in_video',session_id=sid)):
   f=int(result['frame_index'])+1;out=result['outputs']
   for iid,mask,score in zip(out['out_obj_ids'],out['out_binary_masks'],out['out_probs'],strict=True):
    t=tracks.setdefault(str(int(iid)),dict(id=str(int(iid)),frames=[]));t['frames'].append(dict(frame=f,score=float(score),mask=rle(resize(np.asarray(mask).squeeze(),(80,112)))))
 finally:predictor.handle_request(dict(type='close_session',session_id=sid))
 torch.cuda.synchronize();return list(tracks.values()),dict(seconds=time.monotonic()-start,peak_gpu_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved())
