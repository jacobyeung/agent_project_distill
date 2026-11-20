"""CPU producer checks against the actual sealed reader, without weights."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'work/payload/b'),str(ROOT/'work/payload/tree'),
              str(ROOT/'work/payload/b/heads/selector/sl118')]
from gpkg.dense_runtime import d
from e2e_reader import geometry as G,grounding,stage1,real,generate
from student_pilot import routed_candidates as C,routed_features as F,geometry_profiles as GP
from student_pilot import tower_read as TR
import selector_inputs as SI


def geometry(n):
    K=np.tile([[500.,0,500.],[0,500.,500.],[0,0,1.]],(n,1,1))
    poses=np.tile(np.eye(4),(n,1,1));poses[:,0,3]=np.arange(n)*.001
    poses[:,:3,:3]=[[1,0,0],[0,0,1],[0,-1,0]]
    axis=np.linspace(0,1000,51);y,x=np.indices((51,51))
    depth=np.tile(2+x*.002+y*.001,(n,1,1))
    return G.from_arrays(K=K,canvas_to_source=np.tile(np.eye(3),(n,1,1)),camera_to_world=poses,
                         scale=1.2,depth_grid=depth,grid_uv=axis,anchor_frame_indices=list(range(n)))


def raw(n):
    mask=np.zeros(F.SHAPE,bool);mask[180:220,280:320]=True
    return [[dict(mask=mask.copy(),score=.9,presence=.95)] for _ in range(n)]


def pipeline(n):
    geo=geometry(n);frames=raw(n)
    class Head:
        def with_null(self,x,*args):return torch.tensor([1.]*len(x)+[-1.],dtype=torch.float64)
    socket=stage1.StageOne(lambda name:frames,Head(),geo,rule='candidates_argmax')
    accepted,vectors=socket.features('lamp')
    candidates,inputs=socket.propose('lamp');choice=socket.select(inputs)
    masks=grounding.StageOneSocket(socket.propose,socket.select,(240,320),n)('lamp')[0]['masks']
    lift=grounding.lift_bestspread('lamp',masks,geo)
    session=grounding.ground_session(geo,grounding.StageOneSocket(socket.propose,socket.select,(240,320),n))
    from e2e_reader.servers import ReadServers
    servers=ReadServers(geo if n==32 else geometry(32),session)
    responses=[servers.mapping()['ground']('<ground obj="'+name+'" mode="box">')[0] for name in ('lamp','table')]
    responses.append(servers.mapping()['gap']('<gap a="lamp" b="table" rule="box_grid_5cm">')[0])
    from gpkg.runtime.c import plain
    values=dict(geometry={k:hashlib.sha256(getattr(geo,k).tobytes()).hexdigest() for k in ('K','A','C','depth_grid')},
                identity=geo.identity,vectors=plain(vectors),accepted=plain(accepted),choice=choice,
                masks_sha256=hashlib.sha256(masks.tobytes()).hexdigest(),lift=lift,responses=responses)
    return geo,frames,socket,values,session


class Producers(unittest.TestCase):
    def test_production32_bytes_and_every64_producer(self):
        geo,raw32,socket,expected,_=pipeline(32)
        sealed=hashlib.sha256(__import__('inspect').getsource(GP.GeometryContract.validate).encode()).hexdigest()
        with d.installed(ROOT/'work/payload'):
            _,_,_,actual,_=pipeline(32)
            self.assertEqual(json.dumps(actual,sort_keys=True),json.dumps(expected,sort_keys=True))
            geo,frames,socket,actual,session=pipeline(64)
            self.assertEqual(list(socket.grids),list(range(1,65)))
            self.assertEqual(socket.exact.frames,tuple(range(1,65)))
            self.assertTrue(all(geo.has(i) for i in range(33,65)));self.assertFalse(geo.has(65))
            for i in range(33,65):self.assertEqual(socket.exact.depth(i).shape,(240,320))
            proposals,rejected=C.lift(F.cache_for('lamp',frames),'lamp',geo,floor=.3,phrase='lamp')
            self.assertEqual({p.frame for p in proposals},set(range(1,65)));self.assertFalse(rejected)
            tracks=C.link(proposals,'lamp');C.scene_candidates({'lamp':tracks},geo)
            self.assertEqual(tracks[0].features['visibility_frames'],list(range(1,65)))
            self.assertEqual(actual['lift']['frames'],list(range(1,65)))
            self.assertEqual(set(actual['accepted'][0]['masks']),set(map(str,range(1,65))))
            for name in ('name_frames_frac','member_frames_frac','frame_span_frac'):
                self.assertEqual(actual['vectors'][0][SI.FIELDS.index(name)],1.)
            self.assertEqual(hashlib.sha256(__import__('inspect').getsource(GP.GeometryContract.validate).encode()).hexdigest(),sealed)
            text=actual['responses'][0]
            self.assertIn(',63,64 (best ',text)
            self.assertTrue(text.startswith('lamp: frames 1,2,'),text)
            self.assertIn('distance',actual['responses'][2])
            # Dense observations are the same PIL objects, in native order.
            images=list(range(64));f=dict(native_frames=images,anchor_slots=list(range(0,64,2)))
            self.assertEqual(real.anchor_frames(f),images)
        self.assertFalse(geo.has(64))  # Restored production class rejects >32.

    def test_geometry_guards_and_anchor_deltas(self):
        with d.installed(ROOT/'work/payload'):
            from student_pilot.scene_state import FrameMap
            with self.assertRaises(ValueError):FrameMap(tuple([1]*64))
            with self.assertRaises(ValueError):FrameMap(tuple(range(48)))
            geo=geometry(64)
            bad=copy.copy(geo.contract);object.__setattr__(bad,'scale',-1)
            with self.assertRaises(ValueError):bad.validate()
            bad=copy.copy(geo.contract);K=np.array(bad.K);K[63,0,0]=-1;object.__setattr__(bad,'K',K)
            with self.assertRaises(ValueError):bad.validate()
            with self.assertRaises(ValueError):GP.ProfileGeometry(geo.contract,np.ones((32,51,51)))
            pose=np.zeros((64,9));pose[:,6]=1.;pose[:,7:]=1.;pose[:,0]=np.arange(64)*.01
            full=np.tile(np.linspace(1,2,51)[None,None,:],(64,51,1));slots=np.arange(0,64,2)
            tower=dict(raw_pose9=pose,anchor_slots=slots,frame_indices=np.arange(64),depth_grid=full[slots],
                       dense_depth_grid=full,grid_uv=np.linspace(0,1000,51),source_hw=(480,640))
            geo=d.dense_geometry(tower,[0,-1,0],1.25)
            self.assertTrue(geo.anchor_geometry_unchanged,geo.anchor_geometry_deltas)
            self.assertTrue(all(v['max_abs']==0 for v in geo.anchor_geometry_deltas.values()))
            self.assertEqual(len(geo.answer_geometry.C),32)
            scale_shapes=[]
            def scale(value):scale_shapes.append(value['depth_grid'].shape);return torch.tensor(0.)
            perception=generate.Perception(lambda frames:tower,lambda state:[0,-1,0],scale)
            servers,built=perception.lazy(dict(native_frames=[None]*64),None,{})
            # A pose call builds all services without needing a detector.
            with patch('e2e_reader.servers.ReadServers.head',return_value='pose'):
                self.assertEqual(servers['pose']('synthetic'),'pose')
            self.assertEqual(scale_shapes,[(32,51,51)])
            self.assertEqual(len(built['servers'].geometry.C),32)

    def test_sam_encode_and_text_detection_all64(self):
        import contextlib
        import types
        from PIL import Image
        from student_pilot.sam3_tower import Sam3Tower
        encodes=[];detects=[]
        def set_image(image):
            encodes.append(image)
            tensor=torch.full((1,1,2,2),float(len(encodes)))
            return dict(backbone_out=dict(backbone_fpn=[tensor],vision_pos_enc=[tensor]))
        def grounding_forward(**kw):
            detects.append(float(kw['backbone_out']['backbone_fpn'][0][0,0,0,0]))
            return dict(pred_logits=torch.tensor([[3.]]),presence_logit_dec=torch.tensor([3.]),pred_masks=torch.ones(1,1,2,2))
        model=types.SimpleNamespace(backbone=types.SimpleNamespace(forward_text=lambda *a,**kw:{}),
                                   forward_grounding=grounding_forward,_get_dummy_prompt=lambda:object())
        tower=Sam3Tower.__new__(Sam3Tower);tower.device=torch.device('cpu');tower.image_batch_size=1
        tower.native_image_batch=False;tower._owner=object();tower._load=lambda:None
        tower._autocast=contextlib.nullcontext;tower._backend=types.SimpleNamespace(set_image=set_image,model=model,find_stage=None)
        features=tower.encode([Image.new('RGB',(2,2)) for _ in range(64)])
        frames=stage1.sam3_detect(tower,features,'lamp')
        self.assertEqual(len(encodes),64);self.assertEqual(detects,list(range(1,65)))
        self.assertEqual(len(frames),64);self.assertTrue(all(len(f)==1 for f in frames[32:]))

    def test_same_aggregator_extra_head_batches_preserve_anchors(self):
        """Execute the full unchanged/extended run with deterministic tensor heads."""
        import types
        from PIL import Image
        from student_pilot import c1r_ref,_tower_native
        calls=[];aggregations=[]
        class Head:
            def __init__(self,channels):self.channels=channels
            def __call__(self,small,images,**kw):
                slots=small[23][0,:,0,0].to(torch.int).tolist();calls.append((self.channels,slots))
                value=torch.tensor(slots,dtype=torch.float32).reshape(1,-1,1,1,1).expand(1,-1,2,2,self.channels)+1
                return value,torch.ones(1,len(slots),2,2)
        class Model:
            point_head=Head(3);depth_head=Head(1);aggregator=object()
            def to(self,*a):return self
            def eval(self):return self
            def requires_grad_(self,*a):return self
            local_camera_head=staticmethod(lambda x:[torch.zeros(1,64,6)])
            global_camera_head=staticmethod(lambda x:[torch.zeros(1,64,5)])
        def selected(agg,images):
            aggregations.append(images.shape[1]);blocks=[None]*24
            blocks[23]=torch.arange(64.).reshape(1,64,1,1);return blocks,5
        def convert(*args):
            pose=np.zeros((64,9));pose[:,6]=1;pose[:,7:]=1
            return dict(raw_pose=pose,world_to_frame0=np.eye(4))
        def sample(value,*args):
            return value[:,0:1,0:1].expand(-1,51,51,-1)
        loader=types.ModuleType('vggt.utils.load_fn')
        loader.load_and_preprocess_images_square=lambda *a:(torch.zeros(1,3,2,2),torch.tensor([[0.,0.,1024.,1024.]]))
        batch=dict(tower_native_frames=[Image.new('RGB',(2,2))]*64,tower_frame_indices=list(range(64)),
                   tower_anchor_slots=list(range(0,64,2)),frame_indices=list(range(0,64,2)))
        tower=TR.FrozenG3TTower(dict(device='cpu',dense_frames=64),module=Model())
        with patch.object(c1r_ref,'source_import'),patch.object(_tower_native,'selected_layers',selected),\
             patch.object(_tower_native,'native_sample',sample),patch.object(TR,'g3t_to_c1_pose9',convert),\
             patch.dict(sys.modules,{'vggt.utils.load_fn':loader}):
            base=tower.run(batch);baseline_calls=list(calls);calls.clear()
            with d.installed(ROOT/'work/payload'):full=tower.run(batch)
        self.assertEqual(aggregations,[64,64]);self.assertEqual(calls[:8],baseline_calls)
        self.assertEqual(len(calls),16)
        for name in ('raw_pose9','depth_grid','depth_conf_grid','points_grid'):
            self.assertEqual(getattr(base,name).tobytes(),getattr(full,name).tobytes())
        self.assertEqual(full.dense_depth_grid[:,0,0].tolist(),list(range(1,65)))
        self.assertEqual(full.dense_points_grid[:,0,0,0].tolist(),list(range(1,65)))


if __name__=='__main__':unittest.main(verbosity=2)
