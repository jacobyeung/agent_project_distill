import ast
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace as NS
W=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(W/'out/src/b'),str(W/'out/src/tree'),str(W/'out/src')]
import numpy as np
import torch
from e2e_reader.stage1 import StageOne, stage1_factory, proposal_diagnostics
from e2e_reader.grounding import StageOneSocket, ground_session
from e2e_reader.servers import ReadServers
from e2e_reader.callhook import CallHook

class Head:
    def __init__(self,slots):self.slots=torch.tensor(slots,dtype=torch.float32)
    def with_null(self,*args):return self.slots

def select(rule,slots):
    obj=StageOne.__new__(StageOne);obj.head=Head(slots);obj.rule=rule;obj.diagnostics={}
    x=torch.zeros((len(slots)-1,58),dtype=torch.float64)
    return obj.select(dict(x=x,name='object'))

class Rules(unittest.TestCase):
    def test_candidates_and_ties(self):
        for slots in ([1,2,100],[2,2,100],[-3,-4,100],[1,-10],[100]):
            n=len(slots)-1
            want=max(range(n),key=lambda i:slots[i]) if n else -1
            self.assertEqual(select('candidates_argmax',slots),want)
    def test_null_exact(self):
        rng=np.random.default_rng(0)
        for n in range(1,50):
            for _ in range(5):
                slots=rng.normal(size=n+1).astype(np.float32)
                k=int(np.argmax(slots));self.assertEqual(select('null_argmax',slots),-1 if k==n else k)
        self.assertEqual(select('null_argmax',[1,1,1]),0)
    def test_settings_reach_factory(self):
        from h1eval.h10.perception_own import LazyStageOne
        from unittest.mock import patch
        model=NS(_h10_ground_components=('sam','head'))
        for rule in ('null_argmax','candidates_argmax'):
            with patch('e2e_reader.stage1.stage1_factory',return_value=lambda f,g:rule) as factory:
                value=LazyStageOne(None,model,'cpu',{'stage1_select_rule':rule,'perception_memo_modules':['g3t']})('frames','geo')
                self.assertEqual(value,rule);self.assertEqual(factory.call_args.kwargs['rule'],rule)
    def test_empty_socket_skips_head(self):
        sock=StageOneSocket(lambda n:([],None),lambda x:self.fail('empty selection'),(4,4),32)
        self.assertEqual(sock('x'),[])
    def test_diagnostics_bounded_and_report(self):
        raw=[[dict(score=.8,presence=.9)] for _ in range(32)]
        accepted=[dict(candidate_id=str(i),masks={j:None for j in range(1,33)},features={'peak':.8}) for i in range(45)]
        d=proposal_diagnostics('null_argmax',' X ',raw,[None]*20,[{'reason':'invalid_pose'},{'reason':'no_eligible_pixels'}],accepted,[[float(np.float32(1/3))]*58]*45)
        self.assertEqual(d['name_key'],'x');self.assertEqual(d['lift_entering'],22)
        self.assertEqual(len(d['candidates']),30);self.assertEqual(len(d['sam3']['kept_per_frame']),32)
        self.assertLess(len(json.dumps(d,allow_nan=False).encode()),64*1024)
        tok=NS(convert_tokens_to_ids=lambda t:0,encode=lambda s,**kw:list(s.encode()))
        hook=CallHook(tok,[]);hook.begin({'ground':lambda c:('x: not seen',{'audit':{},'stage1':d})})
        hook.respond('<ground obj="x" mode="box">')
        self.assertEqual(hook.report()['records'][0]['stage1'],d)
        self.assertNotIn('audit',hook.report()['records'][0])
    def test_default_decision_ast_unchanged(self):
        old=ast.parse((W.parent/'b1g/out/src/b/e2e_reader/grounding.py').read_text())
        new=ast.parse((W/'out/src/b/e2e_reader/grounding.py').read_text())
        for name in ('lift_plain','lift_bestspread','min_area_box','ground_session'):
            a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name==name)
            b=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name==name)
            self.assertEqual(ast.dump(a),ast.dump(b))
        for p in ('tree/trace_format/box_v313.py','tree/trace_format/ground_v313.py','tree/student_pilot/routed_candidates.py','tree/student_pilot/routed_features.py','b/e2e_reader/callhook.py'):
            self.assertEqual((W.parent/'b1g/out/src'/p).read_bytes(),(W/'out/src'/p).read_bytes())
    def test_snapshot(self):
        from h1eval.perception import Heads,own_profile
        from h1eval.h10.depth_snapshot import save
        pose=np.tile([0.,0.,0.,0.,0.,0.,1.,1.,1.],(32,1))
        heads=Heads(pose,np.array([0.,-1.,0.]),lambda k,uv:np.ones(len(uv))*k,'fixture')
        frames={'source_hw':(480,640)}
        geometry=own_profile(heads,frames)
        state=dict(heads=heads,geometry=geometry,frames=frames)
        dest=W/'work/snapshot_test';dest.mkdir(exist_ok=True)
        result=save(dest,'fixture','none',state)
        import hashlib
        path=dest/result['path'];self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),result['sha256'])
        with np.load(path) as z:
            self.assertEqual(z['depth_grid'].dtype,np.float16);self.assertEqual(z['depth_grid'].shape,(32,51,51))
            np.testing.assert_array_equal(z['pose9'],pose)
        self.assertLess(path.stat().st_size,200000)
    def test_resume_identity(self):
        from orchard_h10.runner import run
        from orchard_h10.common import write
        out=W/'work/resume_test';out.mkdir(exist_ok=True)
        identity=dict(plan='same',inputs=None,cards=1,order=list(__import__('orchard_h10.common',fromlist=['ORDER']).ORDER),
                      types=['object_abs_distance'],arms=['own'],stage1_select_rule='null_argmax',modes=['none'])
        write(out/'metadata/IDENTITY.json',identity)
        cfg=dict(perception_memo_modules=['g3t'],output=str(out),types=identity['types'],plan_sha256='same',stage1_select_rule='candidates_argmax',modes=['none'])
        with self.assertRaisesRegex(ValueError,'Resume requires'):
            run(cfg,['0'],0,launcher=lambda *a,**kw:self.fail('launch must not occur'))

if __name__=='__main__':unittest.main(verbosity=2)
