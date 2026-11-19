"""Frozen reader towers; imports and forward passes are deferred until explicit GPU launch."""
import numpy as np
from common import *

def g3t(c,n,all_depth=False):
 import torch
 from PIL import Image
 from student_pilot.tower_read import FrozenG3TTower
 m=manifest();settings=m['gpu'];frames=c['dense_frames'] if n==64 else [c['dense_frames'][i] for i in c['anchor_slots']]
 for key in ('tower_weights','tower_config'):
  pin=settings[key];assert sha(pin['path'])==pin['sha256']
 images=[]
 for f in frames:
  assert sha(f['path'])==f['sha256']
  with Image.open(local(f['path'])) as im:images.append(im.convert('RGB'))
 indices=[f['index'] for f in frames];anchors=c['anchor_slots'] if n==64 else list(range(32))
 tower=FrozenG3TTower(dict(weights_path=settings['tower_weights']['path'],config_path=settings['tower_config']['path'],device='cuda:0',dense_frames=n,depth_chunk_size=8,dtype='bf16'))
 torch.cuda.reset_peak_memory_stats();t=time.monotonic()
 state=tower.run(dict(tower_native_frames=images,tower_frame_indices=indices,tower_anchor_slots=anchors,frame_indices=c['anchor_indices']),all_depth=all_depth)
 torch.cuda.synchronize()
 arrays=dict(raw_pose=state.raw_pose9,depth_grid=state.depth_grid,depth_conf_grid=state.depth_conf_grid,frame_indices=state.frame_indices,anchor_slots=state.anchor_slots,depth_slots=state.depth_slots,grid_uv=state.grid_uv,source_hw=np.array([images[0].height,images[0].width]))
 if state.points_grid is not None:arrays['points_grid']=state.points_grid
 stats=dict(seconds=time.monotonic()-t,peak_gpu_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved())
 if stats['peak_gpu_bytes']>40_000_000_000:raise MemoryError('G3T peak exceeds 40 GB')
 del tower,state;torch.cuda.empty_cache()
 return arrays,stats

def sam_nonanchors(c,validate_anchors=False):
 import torch
 from PIL import Image
 from student_pilot.sam3_tower import Sam3Tower
 from student_pilot.routed_features import rle
 from e2e_reader.stage1 import sam3_detect
 m=manifest()['gpu']
 for key in ('sam_checkpoint','sam_receipt'):assert sha(m[key]['path'])==m[key]['sha256']
 source=local(m['sam_source']);names=sorted({name.strip().lower() for row in c['rows'] for name in row.get('operands',[])})
 anchors=set(c['anchor_slots']);slots=[i for i in range(64) if i not in anchors]+(list(c['anchor_slots']) if validate_anchors else []);images=[]
 for slot in slots:
  f=c['dense_frames'][slot];assert sha(f['path'])==f['sha256']
  with Image.open(local(f['path'])) as im:images.append(im.convert('RGB'))
 tower=Sam3Tower(dict(device='cuda:0',checkpoint_path=m['sam_checkpoint']['path'],receipt_path=m['sam_receipt']['path'],source_root=str(source),precision='bf16'))
 t=time.monotonic();torch.cuda.reset_peak_memory_stats();features=tower.encode(images)
 out=dict(phrases=names,frame_indices=[x['index'] for x in c['dense_frames']],frames={},contract=dict(joint_floor=.05,cap=30,resolution=1008,dtype='bf16',prompts='raw_name'))
 old=read_json(capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'candidates.json')
 for i,slot in enumerate(c['anchor_slots']):out['frames'][str(slot)]=old['frames'][str(i)]
 anchor_checks=[]
 for name in names:
  for slot,entries in zip(slots,sam3_detect(tower,features,name),strict=True):
   if slot in anchors:
    from replay import cached_detections
    expected=cached_detections(old,name,32)[c['anchor_slots'].index(slot)]
    anchor_checks.append(dict(name=name,dense_slot=slot,expected=len(expected),got=len(entries),equal=len(expected)==len(entries) and all(np.array_equal(a['mask'],b['mask']) and abs(a['score']-b['score'])<=1e-5 and abs(a['presence']-b['presence'])<=1e-5 for a,b in zip(expected,entries))))
    continue
   rec=out['frames'].setdefault(str(slot),dict(phrases={}))
   rec['phrases'][name]=dict(presence=entries[0]['presence'] if entries else 0.,instances=[dict(score=e['score'],mask=rle(e['mask'])) for e in entries])
 out['anchor_proposal_check']=dict(status='PASS' if anchor_checks and all(x['equal'] for x in anchor_checks) else 'FAIL' if anchor_checks else 'NOT_REQUESTED',checks=anchor_checks)
 torch.cuda.synchronize();stats=dict(seconds=time.monotonic()-t,peak_gpu_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved())
 if stats['peak_gpu_bytes']>40_000_000_000:raise MemoryError('SAM3 peak exceeds 40 GB')
 del features,tower;torch.cuda.empty_cache();return out,stats

def da3(c,go_file):
 import torch
 sys.path.insert(0,str(ROOT/'code/vendor'))
 from geo_bakeoff.backends import Backend
 paths=[]
 for f in c['dense_frames']:
  assert sha(f['path'])==f['sha256'];paths.append(str(local(f['path'])))
 backend=Backend('da3',device='cuda',threads=8,go_file=go_file)
 t=time.monotonic();torch.cuda.reset_peak_memory_stats();p=backend.predict(paths)
 torch.cuda.synchronize()
 if torch.cuda.max_memory_allocated()>40_000_000_000:raise MemoryError('DA3 peak exceeds 40 GB')
 return dict(depth=p.depth,intrinsics=p.intrinsics,c2w=p.c2w,source_hw=np.asarray(p.source_hw)),dict(seconds=time.monotonic()-t,peak_gpu_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved())
