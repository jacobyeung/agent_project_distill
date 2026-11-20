import sys,json,math,tempfile,hashlib,importlib.util
from pathlib import Path
import numpy as np,torch
from torch import nn
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE/'stub')]
import bindings as B
from student_pilot.point_depth_head import PointDepthHead
import student_pilot.decoupled_v as DV
spec=importlib.util.spec_from_file_location('boundaries',sys.argv[1]);bd=importlib.util.module_from_spec(spec);spec.loader.exec_module(bd)
torch.manual_seed(0)
D=32
class Depth(nn.Module):
 def __init__(s):
  super().__init__();s.dim=D;s.auxiliary_heads=nn.Module();s.auxiliary_heads.camera=nn.Module()
  h=PointDepthHead(D,{'d_proj':32,'mlp_hidden':32,'num_heads':2,'context_depth':1},vit_dim=D);h.group_embed=nn.Parameter(torch.randn(32,32)*.02)
  nn.init.normal_(h.fov_film[-1].weight,std=.5);s.auxiliary_heads.camera.point_depth=h
  s.auxiliary_heads.frame_queries=nn.Parameter(torch.randn(32,D)*.1);s.fov=nn.Linear(D,2)
class Model(nn.Module):
 def __init__(s):
  super().__init__();s.auxiliary_heads=nn.Module();s.auxiliary_heads.depth=Depth()
  s.pose_fov=torch.tensor([[1.0,0.8]]*32)+torch.linspace(0,.1,32)[:,None]
 def to(s,*a,**k):return s
tmp=Path(tempfile.mkdtemp(prefix='k1fwd2t_',dir=str(HERE)))
c={'canonical':'ds/x1','anchor_indices':list(range(0,320,10)),'anchor_slots':[],'dense_frames':[],'video_sha256':'v',
   'model_row':{'student_input':{'frame_indices':list(range(0,320,10)),'video_identity':{'video_sha256':'v'},'frames':[]}}}
c2=dict(c,canonical='ds/x2')
g3={'captures':{'ds/x1':{'capture_sha256':B.digest(c),'anchor_indices':c['anchor_indices'],'fov_hw_rad':(np.full((32,2),[1.1,0.9])+np.linspace(0,.05,32)[:,None]).tolist()}}}
gp=tmp/'g.json';gp.write_text(json.dumps(g3))
art=tmp/'art.json';art.write_text('{}');cfg=tmp/'cfg.json';cfg.write_text('{}')
def run(settings,cc,model):
 g=bd.GPU.__new__(bd.GPU);g.settings=settings;g.device='cpu';g.model=model;g.processor=None;g.checkpoint=settings['artifact']
 return g.own(cc,[],__import__('types').SimpleNamespace(grid_uv=bd_grid))
from student_pilot.tower_read import GRID_UV as bd_grid
base=dict(config=dict(path=str(cfg),sha256=B.sha(cfg)),artifact=dict(path=str(art),sha256=B.sha(art)))
m=Model()
plain,grav=run(base,c,m)
root=tmp/'probe';(root/B.digest('ds/x1')[:16]).mkdir(parents=True);(root/B.digest('ds/x2')[:16]).mkdir(parents=True)
fs=dict(base,fov_variants=dict(schema='k1-fov-variants-v1',root=str(root),g3t=dict(path=str(gp),sha256=B.sha(gp))))
served,_=run(fs,c,m)
assert np.array_equal(plain,served),'served depth changed'
assert 'encode' not in m.auxiliary_heads.depth.auxiliary_heads.camera.point_depth.__dict__
d=root/B.digest('ds/x1')[:16];z=np.load(d/'fov.npz');r=json.loads((d/'FOV_RECEIPT.json').read_text())
print(sorted(z.files),r['checks'],r['missing'])
assert sorted(z.files)==['depth_V1','depth_V2','fov_B','fov_V1','fov_V2'] and r['checks']['second_pass_pose_fov_bit_identical']
h=m.auxiliary_heads.depth.auxiliary_heads.camera.point_depth;cap=DV.features(m.auxiliary_heads.depth,None)
axis=torch.as_tensor(bd_grid.copy());yy,xx=torch.meshgrid(axis,axis,indexing='ij');uv=torch.stack((xx,yy),-1).reshape(1,-1,2).expand(32,-1,-1)
with torch.no_grad():
 v1=(1e-4+(math.pi-2e-4)*m.auxiliary_heads.depth.fov(cap.states.float()).sigmoid())[0]
 e1=h.query(h.encode(cap.grids[0],cap.vits[0],v1),uv).double().numpy().reshape(32,51,51)
 v2=torch.as_tensor(np.asarray(g3['captures']['ds/x1']['fov_hw_rad']),dtype=torch.float32)
 e2=h.query(h.encode(cap.grids[0],cap.vits[0],v2),uv).double().numpy().reshape(32,51,51)
assert np.array_equal(z['depth_V1'],e1) and np.array_equal(z['depth_V2'],e2) and np.array_equal(z['fov_B'],m.pose_fov.numpy())
assert not np.array_equal(z['depth_V1'],served) and not np.array_equal(z['depth_V2'],served),'fov must matter'
# pose FoV change: served moves, V1/V2 fixed
m.pose_fov=m.pose_fov+0.2;s2,_=run(fs,c2,m);d2=root/B.digest('ds/x2')[:16];z2=np.load(d2/'fov.npz');r2=json.loads((d2/'FOV_RECEIPT.json').read_text())
assert not np.array_equal(s2,served) and np.array_equal(z2['depth_V1'],e1) and 'depth_V2' not in z2.files and 'V2' in r2['missing']
# re-run into a destination that already has fov.npz must refuse
try:run(fs,c,m);raise SystemExit('no refusal')
except ValueError as e:print('refused:',e)
# wrong g3t identity refuses
bad=dict(g3,captures={'ds/x1':dict(g3['captures']['ds/x1'],capture_sha256='0'*64)});gp2=tmp/'g2.json';gp2.write_text(json.dumps(bad))
root3=tmp/'p3';(root3/B.digest('ds/x1')[:16]).mkdir(parents=True)
try:run(dict(base,fov_variants=dict(fs['fov_variants'],root=str(root3),g3t=dict(path=str(gp2),sha256=B.sha(gp2)))),c,Model());raise SystemExit('no refusal')
except ValueError as e:print('refused:',e)
print('PASS',r['keys'],r['seconds'])
