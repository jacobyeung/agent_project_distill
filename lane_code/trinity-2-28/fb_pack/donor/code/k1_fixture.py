"""Two authenticated K1 captures; native tiny weights and synthetic tower depth."""
import copy,hashlib,json,os,sys,types,tempfile
from pathlib import Path
import numpy as np
from PIL import Image
import torch
W=Path(__file__).resolve().parents[1];T=W/'work/new';sys.path.insert(0,str(T))
pkg=types.ModuleType('tests');pkg.__path__=[str(T/'tests')];sys.modules['tests']=pkg
torch.set_num_threads(16)
from tests.test_scale_donor import fixture,source,settings,train_two,native_export
from tests.test_carrier_c1 import Tokenizer
from student_pilot import scale_donor as D
from student_pilot.p3_provenance import sha256
from student_pilot.carrier_c1_data import insert_frame_carriers
from student_pilot.carrier_c1_decode import HeadState
from student_pilot.tower_read import TowerState,apply_tower
from student_pilot.tower_scale import estimate_scale
from transformers.models.qwen3_vl.video_processing_qwen3_vl import Qwen3VLVideoProcessor
from transformers.video_utils import VideoMetadata
out=Path(tempfile.mkdtemp(prefix='k1_fixture_',dir=W/'work'))
selection=json.loads((W/'out/K1_SELECTION.json').read_text())
processor=Qwen3VLVideoProcessor(patch_size=2,temporal_patch_size=2,merge_size=2,size=dict(shortest_edge=16,longest_edge=16))

def batches(c):
 frames=[c['dense_frames'][i] for i in c['anchor_slots']]
 pixels=[]
 for f in frames:
  assert sha256(f['path'])==f['sha256']
  with Image.open(f['path']) as im:pixels.append(np.asarray(im.convert('RGB').resize((4,4),Image.Resampling.BICUBIC)))
 arrays=np.repeat(np.stack(pixels),2,axis=0)
 arrays=(arrays.astype(np.float32)/255.-np.asarray(processor.image_mean,dtype=np.float32))/np.asarray(processor.image_std,dtype=np.float32)
 values=processor(videos=[arrays],video_metadata=[VideoMetadata(total_num_frames=64,fps=2.,frames_indices=list(range(64)))],do_sample_frames=False,do_resize=False,do_convert_rgb=False,do_normalize=False,do_rescale=False,input_data_format='channels_last',return_tensors='pt')
 assert values['video_grid_thw'].tolist()==[[32,2,2]]
 ids=torch.tensor([[2]+[v for _ in range(32) for v in (62,61,63)]+[10,11,12,13]])
 batch=dict(input_ids=ids,attention_mask=torch.ones_like(ids),labels=torch.full_like(ids,-100),mm_token_type_ids=torch.where(ids==61,2,0),**values)
 batch['labels'][0,-2:]=ids[0,-2:]
 batch=insert_frame_carriers(batch,Tokenizer(),frame_layout='duplicate')
 raw=np.zeros((32,9));raw[:,0]=np.arange(32)*.1;raw[:,6]=1
 raw[:,7:9]=selection['fovs'][c['canonical']]['fov_hw_rad']
 # Synthetic depth/confidence isolate estimator invariance; no K1 scale accuracy claim.
 d=np.broadcast_to(np.linspace(1,2,51)[None,None,:],(32,51,51)).copy()
 conf=np.arange(d.size,dtype=float).reshape(d.shape)
 state=TowerState(raw,d,conf,np.array(c['anchor_indices']),np.arange(32))
 batch.update(tower_frame_indices=torch.tensor(state.frame_indices.copy()),tower_anchor_slots=torch.tensor(state.anchor_slots.copy()),tower_lm_frame_indices=torch.tensor(state.frame_indices.copy()))
 return batch,state

@torch.no_grad()
def observe(model,batch,state):
 model.eval()
 head=HeadState(model,batch,model.hidden(batch))
 axis=torch.linspace(0,1000,51);yy,xx=torch.meshgrid(axis,axis,indexing='ij');uv=torch.stack((xx,yy),-1).reshape(1,-1,2).expand(32,-1,-1)
 live=head.depth_head.query(head.depth_map,uv).reshape(32,51,51)
 donor=model.auxiliary_heads.scale_donor(batch,state)
 scale,selected,threshold=estimate_scale(state.depth_grid,state.depth_conf_grid,donor.double().numpy())
 apply_tower(head,state,batch,scale_donor=model.auxiliary_heads.scale_donor)
 assert head.tower_scale==scale
 np.testing.assert_array_equal(head.pose9[:,:3],state.raw_pose9[:,:3]*scale)
 np.testing.assert_array_equal(head.depth_map[:,0].numpy(),state.depth_grid*scale)
 return dict(live=live.clone(),donor=donor.clone(),scale=scale,selected=int(selected.sum()),threshold=threshold)

def array_hash(x):return hashlib.sha256(x.detach().contiguous().numpy().tobytes()).hexdigest()
reports=[];inputs={str(W/'out/K1_SELECTION.json'):sha256(W/'out/K1_SELECTION.json'),**selection['input_sha256']}
for variant in ('V1','V2'):
 model,_,targets=fixture(); model.frame_layout='duplicate';model.auxiliary_heads.depth.config.p3['frame_layout']='duplicate'
 # Match the launch depth weight while retaining native tiny-model architecture.
 model.recipe=copy.deepcopy(model.recipe);model.recipe['weights']['depth']=.25
 root=out/variant;root.mkdir(exist_ok=True)
 pin=source(model,root/'source');cfg=settings(model,pin,variant);donor=D.attach(model,cfg)
 tensors0=D.tensor_pins(donor.state_dict());visual0=D.visual_identity(donor.visual)
 live0=D.tensor_pins(model.auxiliary_heads.depth.auxiliary_heads.camera.point_depth.state_dict())
 pairs=[batches(c) for c in selection['captures']]
 before=[observe(model,*x) for x in pairs]
 optimizer,steps=train_two(model,pairs[0][0],targets)
 after=[observe(model,*x) for x in pairs]
 tensors1=D.tensor_pins(donor.state_dict());live1=D.tensor_pins(model.auxiliary_heads.depth.auxiliary_heads.camera.point_depth.state_dict())
 assert tensors0==tensors1 and visual0==D.visual_identity(donor.visual)
 changed=[n for n in live0 if live0[n]!=live1[n]];assert changed
 captures=[]
 for c,a,b in zip(selection['captures'],before,after):
  assert torch.equal(a['donor'],b['donor']) and a['scale']==b['scale'] and not torch.equal(a['live'],b['live'])
  captures.append(dict(canonical=c['canonical'],donor_grid_before_sha256=array_hash(a['donor']),donor_grid_after_sha256=array_hash(b['donor']),live_grid_before_sha256=array_hash(a['live']),live_grid_after_sha256=array_hash(b['live']),scale_before=a['scale'],scale_after=b['scale'],scale_float64_before_sha256=hashlib.sha256(np.float64(a['scale']).tobytes()).hexdigest(),scale_float64_after_sha256=hashlib.sha256(np.float64(b['scale']).tobytes()).hexdigest(),selected_points=a['selected'],grid_shape=list(a['donor'].shape)))
 epin=native_export(model,root/'export')
 inputs[pin['path']]=pin['sha256']; inputs[str(root/'source/heads.pt')]=sha256(root/'source/heads.pt')
 reports.append(dict(variant=variant,settings=cfg,steps=len(steps),optimizer_groups=[dict(name=g['name'],initial_lr=g['initial_lr'],parameters=len(g['params'])) for g in optimizer.param_groups],donor_tensors_before=tensors0,donor_tensors_after=tensors1,shared_visual_sha256=visual0,live_head_tensors=len(live0),live_head_tensors_changed=changed,captures=captures,export=epin))
for p in [Path(__file__),T/'tests/test_scale_donor.py',T/'tests/test_carrier_c1_final.py',T/'tests/test_carrier_c1.py',*(T/'student_pilot'/n for n in ('scale_donor.py','carrier_c1.py','carrier_c1_run.py','carrier_c1_decode.py','tower_read.py','tower_scale.py','tower_scale_rule.py',*D.FEATURE_FILES))]:inputs[str(p)]=sha256(p)
result=dict(input_sha256=inputs,status='PASS',weights='native tiny fixture; real step400/544 heads MISSING',RGB='authenticated K1 train; 4x4 bicubic fixture resize; native Qwen patch packing/normalization; duplicate temporal layout',tower='synthetic depth/confidence/translation; frozen real V2 FoV from G3T_FOV.json',variants=reports,command='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/k1_fixture.py')
(W/'out/K1_INVARIANCE.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS two K1 captures, both variants, two native optimizer steps per variant')
