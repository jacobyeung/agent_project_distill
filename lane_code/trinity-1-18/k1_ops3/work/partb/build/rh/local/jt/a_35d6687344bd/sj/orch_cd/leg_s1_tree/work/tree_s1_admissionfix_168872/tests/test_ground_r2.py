from pathlib import Path
import json, os, unittest, uuid
from unittest.mock import patch
import numpy as np
import ofs
from ofs.core import voxel_set
from scipy.ndimage import zoom
from student_pilot.geometry_profiles import (GeometryContract,ProfileGeometry,ContractAdapter,
    GeometryError,legacy_from_heads,scaled_from_heads)
from student_pilot.scene_state import FrameMap,SceneState
from student_pilot.ground_sources import MaskBatch,MaskProvider,OwnProposals,NativeMDG,CachedSAM3
from student_pilot.ground_v3 import GroundV3
from student_pilot.object_memory import ClipMemory
from student_pilot.ground_lifting import mask_pixels,lift_object
from student_pilot.p3_printed_calculator import PrintedPointRegistry as Reg
from student_pilot import carrier_c1_decode as D
from rk.programs import load_heads

ROOT=Path(os.environ.get('GV_FIX_ROOT',Path.cwd())).resolve()
TMP=ROOT/'work/tmp';TMP.mkdir(parents=True,exist_ok=True)
(ROOT/'out').mkdir(parents=True,exist_ok=True)

def synthetic():
    k=np.arange(32,dtype=float)
    yaw=.013*k;pitch=.004*k
    R=[]
    for y,p in zip(yaw,pitch):
        rz=np.array([[np.cos(y),-np.sin(y),0],[np.sin(y),np.cos(y),0],[0,0,1]])
        rx=np.array([[1,0,0],[0,np.cos(p),-np.sin(p)],[0,np.sin(p),np.cos(p)]])
        R.append(rz@rx@np.array([[1,0,0],[0,0,1],[0,-1,0]]))
    R=np.array(R);t=np.column_stack((k*.017,k*.023,k*.011))
    fov=np.column_stack((.72+k*.009,1.1+k*.007))
    u,v=np.meshgrid(np.linspace(0,1000,51),np.linspace(0,1000,51))
    depth=np.array([2+i*.031+u*.00021+v*.00073 for i in range(32)],dtype=np.float64)
    return dict(layout=np.array('per_frame'),gravity_source=np.array('own'),r_grav=R,t_grav=t,
        fov_hw=fov,source_hw=np.array([480,640]),depth_grid=depth,grid_uv=np.linspace(0,1000,51),
        scale=np.array(1.7),anchor_frame_indices=np.arange(32)*3+7)

def production(values=None):
    values=synthetic() if values is None else values
    path=TMP/f'heads_{uuid.uuid4().hex}.npz';np.savez(path,**values)
    return legacy_from_heads(path,FrameMap(tuple((np.arange(32)*3+7).tolist())),load_heads)

def geometry():
    z=synthetic();C=np.repeat(np.eye(4)[None],32,axis=0);C[:,:3,:3]=z['r_grav'];C[:,:3,3]=z['t_grav']
    K=np.zeros((32,3,3));K[:,0,0]=640/(2*np.tan(z['fov_hw'][:,1]/2));K[:,1,1]=480/(2*np.tan(z['fov_hw'][:,0]/2))
    K[:,0,2]=320;K[:,1,2]=240;K[:,2,2]=1
    c=GeometryContract('legacy_v3122',FrameMap(tuple(z['anchor_frame_indices'].tolist())),7,K,
        np.repeat(np.diag([.64,.48,1])[None],32,axis=0),C,1.7,'vc','metric','metric',0,1)
    return ProfileGeometry(c,z['depth_grid'])

def batch(indices,x=2):
    m=np.zeros((32,12,20),bool);m[0,2:10,x:x+6]=True;m[31,2:10,x:x+6]=True
    return MaskBatch(m,m.any(axis=(1,2)).astype(float),indices)

def backend(g=None,source=None,memory=None,video='a'*64,**kw):
    g=g or geometry();source=source or MaskProvider(lambda n:batch(g.frame_map.source_indices),'test')
    return GroundV3(SceneState(video,g.frame_map,g.identity),g,source,memory=memory,
        audit_dir=TMP/'audits',**kw)

def own_source(g,layout=None):
    def fetch(name,geo,O,grids):
        rows=layout(name) if layout else [(1,0,2,8,.9),(3,0,2,8,.9)]
        out=[]
        for frame,index,x0,x1,score in rows:
            m=np.zeros((12,20),bool);m[2:10,x0:x1]=True
            m=zoom(m,(80/12,112/20),order=0,prefilter=False)
            P=geo.lift(frame,mask_pixels(m))[0];center=np.median(P,axis=0)
            out.append(O.Proposal(frame,index,score,1.,m,
                P,center,.1,4.,voxel_set(P)))
        return out,[]
    return OwnProposals(fetch,g.frame_map,'own_fixture')

def svp(g=None,source=None,**kw):
    g=g or geometry()
    kw.setdefault('rule','seed_excl_fwd')
    return backend(g,source or own_source(g),mask_source='svp_own',selector=ofs,selector_identity='ofs',**kw)


class ProductionGeometry(unittest.TestCase):
    def test_independent_per_frame_heads_and_last_mask(self):
        # Analytic oracle uses scalar pinhole equations and the generated c2w;
        # it does not call rays(), _raw_depth(), or another lifting implementation.
        z=synthetic();uv=np.array([[235.,671.],[782.,193.],[540.,420.]])
        for g in (production(z),geometry()):
            for frame in (1,2,11,23,32):
                W,Pc,spread=g.lift(frame,uv,mode='center')
                i=frame-1;d=2+i*.031+uv[:,0]*.00021+uv[:,1]*.00073
                fh,fw=z['fov_hw'][i]
                expected=np.array([[(u/500-1)*np.tan(fw/2)*dep,(v/500-1)*np.tan(fh/2)*dep,dep]
                                   for (u,v),dep in zip(uv,d)])
                np.testing.assert_allclose(Pc,expected,atol=8e-7,rtol=0)
                np.testing.assert_allclose(W,expected@z['r_grav'][i].T+z['t_grav'][i],atol=8e-7,rtol=0)
                self.assertTrue(g.has(frame))
            mb=batch(g.frame_map.source_indices)
            self.assertEqual(lift_object('chair',mb.masks,mb.probabilities,g,tau=.5)['frames'],[1,32])

    def test_source_check_and_depth_required(self):
        z=synthetic();z['anchor_frame_indices']=z['anchor_frame_indices']+1
        with self.assertRaisesRegex(ValueError,'source_frame'):production(z)
        z=synthetic();z.pop('depth_grid')
        with self.assertRaisesRegex(ValueError,'depth_grid'):production(z)

    def test_gravity_sign_and_pose_adapter_check(self):
        z=synthetic();z['r_grav']=z['r_grav']@np.diag([1,-1,-1])
        with self.assertRaisesRegex(ValueError,'gravity'):production(z)
        g=geometry()
        class Wrong:
            def cam(self,k):
                r,t=g.cam(k);return r.T,-r.T@t
        with self.assertRaisesRegex(ValueError,'camera_contract'):
            ContractAdapter(Wrong(),g.contract,depth_identity='test')

    def test_scaled_loader_one_scale(self):
        g=geometry();c=g.contract
        path=TMP/f'scaled_{uuid.uuid4().hex}.npz'
        np.savez(path,profile='scaled_g3t_depth',depth_unit='unscaled',pose_unit='unscaled',
            anchor_frame_indices=c.frame_map.source_indices,reference_source_frame=7,K=c.K,
            canvas_to_source=c.canvas_to_source,camera_to_world=c.camera_to_world,scale=2.,
            depth_scale_count=0,pose_scale_count=0,depth_grid=g.depth_grid,grid_uv=g.grid_uv)
        scaled=scaled_from_heads(path,c.frame_map)
        np.testing.assert_allclose(scaled.lift(32,[[235,671]])[0],g.lift(32,[[235,671]])[0]*2)


class MemoryAndSources(unittest.TestCase):
    def test_claims_per_question_candidates_before_exclusivity(self):
        b=svp();b.ground('seat',Reg());self.assertEqual(b.ground('chair',Reg()),'chair: not seen')
        b.begin_question();self.assertIn('frames',b.ground('chair',Reg()))
        b.begin_question();self.assertIn('frames',b.ground('seat',Reg()))
        entry=b.memory.get('chair',b.config_hash,scene=b.scene)
        self.assertIsInstance(entry,dict);self.assertTrue(entry['candidates'])

    def test_interleaved_clips_and_separate_questions(self):
        m=ClipMemory();a=svp(memory=m);b=svp(memory=m,video='b'*64)
        first=a.ground('chair',Reg());self.assertIn('frames',b.ground('table',Reg()))
        self.assertEqual(a.ground('seat',Reg()),'seat: not seen')
        self.assertEqual(a.ground('CHAIR',Reg()).replace('CHAIR','chair'),first)
        a.begin_question();self.assertEqual(a.ground('chair',Reg()),first)
        self.assertGreater(m.hits,0)
        c=svp(memory=m);self.assertIn('frames',c.ground('seat',Reg()))

    def test_disconnected_mdg_and_same_object_sam_pieces(self):
        g=geometry()
        def masks(name):
            mb=batch(g.frame_map.source_indices);mb.masks[0,2:10,11:17]=True;return mb
        b=backend(g,MaskProvider(masks,'split'),mask_source='mdg')
        self.assertIn('frames',b.ground('table',Reg()))
        pieces=lambda n:[(1,0,2,7,.9),(1,1,9,14,.9),(3,0,2,14,.9)]
        b=svp(g,own_source(g,pieces))
        self.assertIn('frames',b.ground('table',Reg()))
        duplicate=lambda n:[(1,0,2,8,.9),(1,1,2,8,.9),(3,0,2,8,.9)]
        with self.assertRaisesRegex(ValueError,'ambiguity_margin_removed'):
            svp(g,own_source(g,duplicate),ambiguity_margin=.05)

    def test_unknown_names_queried(self):
        g=geometry();src=own_source(g);src.names=('chair',)
        self.assertIn('frames',svp(g,src).ground('red mug',Reg()))
        from types import SimpleNamespace as NS
        calls=[]
        native=NS(query=lambda n,**kw:calls.append((n,kw)) or 'states',head=None,prefix=None,memory=None,tau=.5)
        src=NativeMDG(g.frame_map,'test');src.bind_native_backend(native)
        mb=batch(g.frame_map.source_indices)
        with patch('student_pilot.mdg_decode.predict',return_value=(dict(mask=mb.masks[None],prob=mb.probabilities[None]),None)):
            src.masks_for('red mug')
        self.assertEqual(calls,[('red mug',dict(allow_unknown=True))])

    def test_bad_name_and_transient_not_cached(self):
        g=geometry();calls=[]
        def flaky(n):
            calls.append(n)
            if len(calls)==1:raise ValueError('transient')
            return batch(g.frame_map.source_indices)
        b=backend(g,MaskProvider(flaky,'flaky'));r=Reg()
        text,info=D.respond('<ground obj=" ">',r,None,lambda n:b.ground(n,r))
        self.assertEqual((text,info['kind']),('error: bad_object','error'))
        self.assertEqual(b.ground('chair',Reg()),'chair: not seen')
        b.begin_question();self.assertIn('frames',b.ground('chair',Reg()));self.assertEqual(len(calls),2)

    def test_threshold_boundary(self):
        class Verify:
            identity='half'
            def __call__(self,n,cs):return {c.id:.5 for c in cs}
        self.assertIn('frames',svp(verify=Verify()).ground('chair',Reg()))

    def test_full_cache_still_queries_new_name(self):
        b=backend(memory=ClipMemory(max_slots=1))
        self.assertIn('frames',b.ground('chair',Reg()))
        b.begin_question()
        self.assertIn('frames',b.ground('red mug',Reg()))

    def test_unknown_query_does_not_change_fixed_competitor_features(self):
        g=geometry();source=own_source(g);source.names=('chair',)
        a=svp(g,source,rule='fused',weights={'exclusivity_margin':1.})
        a.ground('red mug',Reg());a.begin_question();a.ground('chair',Reg())
        b=svp(g,source,rule='fused',weights={'exclusivity_margin':1.});b.ground('chair',Reg())
        ea=a.memory.get('chair',a.config_hash,scene=a.scene)
        eb=b.memory.get('chair',b.config_hash,scene=b.scene)
        self.assertEqual([c.features for c in ea['candidates']],[c.features for c in eb['candidates']])

    def test_manifest_read_independently(self):
        from types import SimpleNamespace
        g=geometry();path=TMP/f'manifest_{uuid.uuid4().hex}.json'
        path.write_text(json.dumps(dict(frame_indices=list(range(32)))))
        reader=SimpleNamespace(load_cache=lambda *a:{},cache_path=lambda *a:path)
        with self.assertRaisesRegex(ValueError,'source_frame'):
            CachedSAM3(None,'scene',g.frame_map,reader,path)

    def test_replay_relifts_masks(self):
        from student_pilot.ground_replay import ReplayBackend
        b=backend();text=b.ground('chair',Reg());q=b.queries[-1]
        q['result']['camera']=[999,999,999]
        self.assertEqual(ReplayBackend({'chair':q},None,Reg()).ground('chair'),text)
        q['mask_bits']=[0]*len(q['mask_bits'])
        self.assertEqual(ReplayBackend({'chair':q},None,Reg()).ground('chair'),'chair: not seen')


if __name__=='__main__':unittest.main(verbosity=2)
