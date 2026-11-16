"""CPU end-to-end rehearsal with synthetic neural outputs, real geometry/selection/rendering."""
import os,sys,json,uuid
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bindings as B,pipeline as P
from boundaries import CPU
import numpy as np
from PIL import Image

def fixture(root):
 root=Path(root);root.mkdir(parents=True,exist_ok=False);frames=[]
 for i in range(64):
  p=root/f'f{i:03}.png';Image.new('RGB',(112,80),(i+30,80,100)).save(p);frames.append(dict(B.pin(p),index=i))
 slots=np.linspace(0,63,32).astype(int).tolist()
 rows=[dict(id='distance',type=P.TYPES[0],question='What is the distance between chair and table in meters?',operands=['chair','table'],unit='m',gt_value=1.,gt_instances={'chair':1,'table':2}),dict(id='failure',type=P.TYPES[0],question='What is the distance between chair and lamp in meters?',operands=['chair','lamp'],unit='m',gt_value=2.,gt_instances={'chair':1,'lamp':3},fallback=dict(trace='The objects appear separated across the room, so I estimate their gap from the image.',answer='2.00',visual_evidence_verified=True)),dict(id='room',type=P.TYPES[1],question='What is the room area in square meters?',operands=[],unit='m2',gt_value=10.)]
 # Raster targets are independent rectangles aligned with the synthetic SAM forward geometry.
 from sam3_tower import FrameDetections
 import torch,torch.nn.functional as F
 from sam_backend import make_postprocess
 from student_pilot.routed_features import resize,OUTPUT_SHAPE
 SHAPE=OUTPUT_SHAPE
 truth=np.zeros((32,*SHAPE),np.int32)
 for gid,x0,x1 in [(1,8,19),(2,29,40)]:
  m=torch.full((1,1,36,48),-12.);m[:,:,10:27,x0:x1]=12.
  mask=F.interpolate(m,(80,112),mode='bilinear',align_corners=False).sigmoid()[0,0].numpy()>.5
  truth[:,resize(mask,OUTPUT_SHAPE)]=gid
 gt=root/'gt.npz';np.savez(gt,instances=truth,frame_indices=np.array([frames[s]['index'] for s in slots]))
 c=dict(canonical='synthetic/room',room='synthetic/room',split='train',dense_source_authority='CPU synthetic dense sequence',dense_frames=frames,anchor_slots=slots,anchor_indices=[frames[s]['index'] for s in slots],video_sha256='f'*64,rows=rows,gt=B.pin(gt))
 ex=dict(complete=True,authorities=dict(benchmark='CPU fixture',dev_s1='CPU fixture'),scenes=[],rooms=[])
 return c,ex

def run(root):
 import torch
 torch.set_num_threads(1)
 root=Path(root);root.mkdir(parents=True,exist_ok=False)
 c,ex=fixture(root/'input');B.write(root/'manifest.json',dict(captures=[c],exclusions=ex,synthetic=True))
 receipt=P.run_capture(c,ex,CPU(),root/'capture')
 results=B.load(root/'capture/responses.json')
 B.write(root/'REHEARSAL.json',dict(receipt=receipt,results=[dict(id=r['id'],decision=r['decision'],calls=r['calls'],mask_match=r['mask_match']) for r in results],scope='Real dense-state conversion, SAM encode/postprocess/alias merge, frozen selector, native response dispatcher, filter and event writer; stand-ins only for tower/own-head/SAM neural outputs',gpu_parity=False))
 print(json.dumps(dict(root=str(root),labels=receipt['labels'])))
 return root
if __name__=='__main__':run(sys.argv[1])
