"""Review regressions use native export, readers and decoder control flow."""
import ast,json,os,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import numpy as np
import torch
from student_pilot import carrier_c1_run as C, carrier_c1_decode as D
from student_pilot.carrier_c1_routing import OwnGeometry,RenderError
from student_pilot.p3_provenance import file_pin

class MergeReview(unittest.TestCase):
    def root(self,name):
        p=Path(os.environ['R2_PROOFS'])/'review11'/name;p.mkdir(parents=True,exist_ok=True);return p

    def test_real_9fix_export_has_bound_constants(self):
        from tests.test_carrier_c1 import fixture
        model,_,_=fixture(4)
        heads=torch.nn.Module()
        for name,child in model.auxiliary_heads.named_children():
            if name not in ('depth_readout','heading'):heads.add_module(name,child)
        model.auxiliary_heads=heads
        source=Path(__file__).resolve().parents[2]/'merge11/legacy9fix_source.py'
        nodes=[n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='export']
        space=dict(vars(C));exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),space)
        dest=self.root('legacy')/'m200'
        if not (dest/'artifact.json').exists():
            with patch.object(C.dist,'get_rank',return_value=0),patch.object(C.dist,'get_world_size',return_value=1),patch.object(C.dist,'barrier'),patch('student_pilot.fsdp_training.publication_state',return_value=model.state_dict()):
                space['export'](dest,model,model,dict(base_identity='fixture',trace_program_version='3.13'),200)
        artifact=json.loads((dest/'artifact.json').read_text())
        self.assertNotIn('readout_config',artifact)
        fresh,_,_=fixture(4)
        with self.assertRaisesRegex(ValueError,'LEGACY_READOUT_CONFIG_IDENTITY_MISMATCH'):
            C.load_artifact(fresh,file_pin(dest/'artifact.json'))
        cfg=dict(base_identity='fixture',trace_program_version='3.13')
        C.load_artifact(fresh,file_pin(dest/'artifact.json'),evaluation_config=cfg)
        bad=dict(cfg,heading_plane_min=.4)
        with self.assertRaisesRegex(ValueError,'LEGACY_READOUT_HEADING_PLANE_MIN_MISMATCH'):
            C.load_artifact(fresh,file_pin(dest/'artifact.json'),evaluation_config=bad)
        artifact['readout_config']=fresh.readout_config
        modern=self.root('legacy')/'declared.json';modern.write_text(json.dumps(artifact))
        with self.assertRaisesRegex(ValueError,'ARTIFACT_READOUT_BUFFERS_MISSING'):
            C.load_artifact(fresh,file_pin(modern))
        artifact['readout_config']={}
        modern.write_text(json.dumps(artifact))
        with self.assertRaisesRegex(ValueError,'readout configuration differs'):
            C.load_artifact(fresh,file_pin(modern))

    def test_invalid_depth_prints_identical_error(self):
        from student_pilot.fixed_readout import DepthReadout
        from trace_format.calculator import PrintedPointRegistry
        poses=np.zeros((32,9));poses[:,6]=1;poses[:,7:]=1
        module=DepthReadout()
        for values in (np.zeros(25),np.full(25,np.nan),np.ones(24),-np.ones(25)):
            old=OwnGeometry(poses,[0,-1,0],lambda *a:values)
            new=OwnGeometry(poses,[0,-1,0],lambda *a:values,
                readout=lambda frame,uv,fov:module(None,fov,uv,frame,None,sampled=values))
            call='<depth_at frame=2 pts=[[500,500]]>'
            a=D.respond(call,PrintedPointRegistry(),old)
            b=D.respond(call,PrintedPointRegistry(),new)
            self.assertEqual(a,b);self.assertEqual(a[0],'error: invalid own depth')
            self.assertEqual(D.respond('<pose frame=2>',PrintedPointRegistry(),old),D.respond('<pose frame=2>',PrintedPointRegistry(),new))

    def test_missing_depth_and_frame_map(self):
        heads=D.HeadState.__new__(D.HeadState);heads.depth_map=None
        with self.assertRaisesRegex(RenderError,'own depth head unavailable'):heads.read_depth(1,[500,500],[1,1])
        from student_pilot.ground_context import GroundContext
        context=GroundContext(None,None,None,None,'fixture',None,{}, {})
        with self.assertRaisesRegex(ValueError,'frame_slot'):context.frame(1,0,'a'*64)

    def test_private_basis_refusals(self):
        from trace_format.contracts import private_metric_basis
        def rotation(frame):
            if frame==2:raise KeyError(frame)
            if frame==3:return np.zeros(2)
            if frame==4:return np.zeros((3,3))
            return np.array([[1,0,0],[0,0,1],[0,1,0]])
        self.assertEqual(private_metric_basis(rotation,np.array([0.,1.,0.])).shape,(3,3))
        self.assertIsNone(private_metric_basis(lambda f:np.zeros((3,3)),np.array([0.,1.,0.])))

    def test_vehicle_n_row_failure_refuses(self):
        class BrokenRows:
            def count(self,stream):return 1
            def get(self,stream,index):raise ValueError('invalid fixture row')
        with self.assertRaisesRegex(ValueError,'R1 row failure'):
            C.fetch(BrokenRows(),'routing',0,NS(training_mode='final',r1_training=True),distributed=False)
