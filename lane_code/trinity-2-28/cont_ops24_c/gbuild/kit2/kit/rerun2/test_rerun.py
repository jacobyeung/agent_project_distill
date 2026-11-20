import ast
import copy
import gzip
import json
from pathlib import Path
import tempfile
from contextlib import contextmanager

@contextmanager
def retained_temp():
    yield tempfile.mkdtemp(prefix="grd_funnel2_test_")
from types import SimpleNamespace as NS
import unittest
import numpy as np
from capture import Capture,Writer,rle,unrle,validate
from dry import fixture
from join import join
from parity import check
from run import load_items,policy_gate,arguments

class RerunTests(unittest.TestCase):
    def setUp(self):
        self.ref=load_items(544)[0];self.row,self.gt=fixture(self.ref)
    def test_rle(self):
        for m in [np.zeros((3,4),bool),np.ones((3,4),bool),np.eye(4,dtype=bool),np.indices((11,9)).sum(0)%2]:
            np.testing.assert_array_equal(m,unrle(rle(m)))
        with self.assertRaises(ValueError):unrle(dict(size=[1,1],counts=[2],order='F'))
    def test_parity_all_items_and_mismatch(self):
        for step in (544,400):
            for ref in load_items(step):self.assertTrue(check(ref['calls'],ref['calls'],0))
        x=copy.deepcopy(self.ref['calls']);x[0]['response']=x[0]['response'].replace('frames 7,','frames 6,')
        with self.assertRaises(ValueError):check(self.ref['calls'],x,1)
        x=copy.deepcopy(self.ref['calls']);x[-1]['response']='distance 4.96 m'
        self.assertTrue(check(self.ref['calls'],x,.01))
        with self.assertRaises(ValueError):check(self.ref['calls'],x,.009)
        with self.assertRaises(ValueError):check(self.ref['calls'],x[:-1],1)
        with self.assertRaises(ValueError):check([],[],float('nan'))
    def test_join_stages(self):
        self.assertEqual(join(self.row,self.gt)[0]['stage'],'S5')
        gt=copy.deepcopy(self.gt)
        target=next(iter(gt['targets'].values()))
        for f in target['masks'].values():
            for k,v in f.items():f[k]=rle(np.zeros(v['size'],bool))
        self.assertEqual(join(self.row,gt)[0]['stage'],'S0')
        row=copy.deepcopy(self.row);row['objects'][0]['proposals']=[]
        self.assertEqual(join(row,self.gt)[0]['stage'],'S1')
        row=copy.deepcopy(self.row);row['objects'][0]['selected_masks']={}
        self.assertEqual(join(row,self.gt)[0]['stage'],'S2')
        row=copy.deepcopy(self.row);row['objects'][0]['selected_masks'].pop('3')
        self.assertEqual(join(row,self.gt)[0]['stage'],'S3')
        row=copy.deepcopy(self.row);row['objects'][0]['fitted_box']['world']['centroid']=[1.,0,0]
        self.assertEqual(join(row,self.gt)[0]['stage'],'S4')
    def test_unknown_and_transform(self):
        target=next(iter(self.gt['targets'].values()));target['annotation_complete']=False
        self.assertEqual(join(self.row,self.gt)[0]['stage'],'U')
        target['annotation_complete']=True;target['world_alignment_reviewed']=False
        self.assertEqual(join(self.row,self.gt)[0]['stage'],'U')
        target['world_alignment_reviewed']=True;target['reader_world_to_gt_world'][0][0]=2
        with self.assertRaises(ValueError):join(self.row,self.gt)
    def test_wrong_source_frame(self):
        self.gt['source_indices']=list(reversed(self.gt['source_indices']))
        with self.assertRaises(ValueError):join(self.row,self.gt)
    def test_output_cap_and_schema(self):
        with retained_temp() as d:
            w=Writer(Path(d)/'x.gz');w.append(self.row);w.close()
            with gzip.open(Path(d)/'x.gz','rt') as f:validate(json.load(f))
            w=Writer(Path(d)/'y.gz',cap=2)
            with self.assertRaises(RuntimeError):w.append(self.row)
            w.stream.close()
        row=copy.deepcopy(self.row);row['objects'][0]['selector']['slots']=[1.]
        with self.assertRaises(ValueError):validate(row)
    def test_policy_refuses_before_weights(self):
        with self.assertRaisesRegex(ValueError,'BLOCKED'):
            policy_gate(Path(__file__).parent/'policy.json',Path('/nonexistent'))
        self.assertEqual(arguments(['--frames','96','--out','x']).frames,96)
    def test_profile_real_features_and_select_cpu_doubles(self):
        # Execute exact production methods with CPU doubles for weights/producers.
        # The code fixture is byte-pinned in SOURCE_PINS.json; decorators alone are removed.
        source=Path(__file__).parent/'fixtures/stage1.py.txt'
        tree=ast.parse(source.read_text()); cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='StageOne')
        methods=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in ('features','select')]
        for n in methods:n.decorator_list=[]
        cls.body=methods
        ns=dict(torch=NS(argmax=lambda a:np.argmax(a)),np=np,proposal_diagnostics=lambda *a:{'candidates':[]})
        exec(compile(ast.fix_missing_locations(ast.Module([cls],type_ignores=[])),str(source),'exec'),ns)
        C=ns['StageOne'];s=C();m=np.ones((2,2),bool)
        raw=[[dict(mask=m,score=.9,presence=.8)] for _ in range(32)]
        proposal=NS(frame=1,index=0,points=np.array([[0,0,1],[1,1,2.]]))
        tracks=[NS(id='x:0',proposals=[proposal],features={})]
        accepted=[dict(candidate_id='x:0',features={},masks={1:m})]
        F=NS(cache_for=lambda *a:None,candidates=NS(lift=lambda *a,**k:([proposal],[]),link=lambda *a:tracks,
             scene_candidates=lambda *a:None),accept_features=lambda *a:accepted)
        s.F=F;s.SI=NS(candidate_vectors=lambda *a:[[.5]*58]);s.detect=lambda name:raw
        s.exact=None;s.grids=None;s.raw={};s.rule='candidates_argmax';s.diagnostics={}
        g=NS(K=np.tile(np.eye(3),(32,1,1)),A=np.tile(np.eye(3),(32,1,1)),C=np.tile(np.eye(4),(32,1,1)),
             contract=NS(camera_to_world=np.tile(np.eye(4),(32,1,1)),scale=1.,reference_source_frame=0,
                         camera_axes='x_right_y_down_z_forward',world_axes='x_right_y_heading_z_up',depth_kind='optical_axis',
                         pixel_centres='edge_origin_half',gravity_up=np.array([0,0,1])),
             frame_map=NS(source_indices=self.ref['source_indices']),depth_scale_count=1,pose_scale_count=1,
             depth_grid=np.zeros((32,2,2)),identity='fixture')
        s.geometry=g;s.head=NS(with_null=lambda *a:np.array([1.,2.]))
        def fake_lift(*a):return None
        class Box:
            def __call__(self,*a):return None
        grounding=NS(lift_bestspread=fake_lift,MinAreaBoxProvider=Box)
        with Capture(C,grounding) as cap:
            before=s.features('x');choice=s.select(dict(x=np.array([[.5]*58]),name='x'))
        self.assertEqual(choice,0);self.assertEqual(cap.objects[0]['selector']['slots'],[1.,2.])
        self.assertEqual(len(cap.objects[0]['proposals']),32)
        self.assertEqual(cap.objects[0]['linked_tracks'][0]['members'],['1:0'])
        self.assertEqual(before,s.features('x'))
        self.assertEqual(cap.objects[0]['selected_masks'],{'1':rle(m)})

if __name__=='__main__':unittest.main()
