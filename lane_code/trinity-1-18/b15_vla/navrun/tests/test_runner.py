import dataclasses
import json
import unittest
from pathlib import Path
from navrun.config import Config
from navrun.episodes import load_split
from navrun.paths import ROOT
from navrun.sim import Environment
from navrun.runner import Runner
from navrun.policies import ScriptPolicy, RandomPolicy, ForwardPolicy, InstructionPolicy, OraclePolicy
from navrun.click import ClickTranslator
from navrun.io import write_json

STATS=dict(action_probabilities=[.03,.6,.185,.185],median_forward_steps=24,median_turn_run=2)

class RunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.episodes=load_split('val_unseen')[:20]
        cls.directory=ROOT/'out/tests/runner';cls.directory.mkdir(parents=True,exist_ok=True)
        cls.counter=0
    def setUp(self):
        self.env=Environment(Config(output_format='text',step_cap=100))
    def tearDown(self):self.env.close()
    def run_policy(self,policy,cfg=None,ep=None,backend=None):
        cfg=cfg or self.env.config
        return Runner(self.env,cfg,backend).episode(ep or self.episodes[0],policy)
    def test_blind_sim(self):
        self.assertIsNone(self.env.reset(self.episodes[0]));self.assertIsNone(self.env.simulator)
    def test_forward_geometry(self):
        import numpy as np
        self.env.reset(self.episodes[0]);p=self.env.position
        self.env.step('forward');self.assertLessEqual(np.linalg.norm(self.env.position-p),.251)
    def test_left_geometry(self):
        import math
        self.env.reset(self.episodes[0]);h=self.env.heading;self.env.step('turn_left')
        diff=(self.env.heading-h+math.pi)%(2*math.pi)-math.pi
        self.assertAlmostEqual(diff,math.radians(15),places=6)
    def test_oracle(self):
        r=self.run_policy(OraclePolicy(self.env));self.assertEqual(r['SR'],1);self.assertGreater(r['SPL'],.95)
    def test_step_cap(self):
        r=self.run_policy(ScriptPolicy(['forward']))
        self.assertEqual(r['steps'],100);self.assertEqual(r['termination'],'step_cap');self.assertEqual(r['SR'],0)
    def test_parse_retry(self):
        r=self.run_policy(ScriptPolicy(['garbage','stop']))
        self.assertEqual(r['actions'],['stop']);self.assertEqual(len(r['parse_events']),1)
    def test_parse_fallback(self):
        r=self.run_policy(ScriptPolicy(['bad','bad','stop']))
        self.assertEqual(r['actions'],['turn_left','stop']);self.assertTrue(r['parse_events'][1]['fallback'])
    def test_stop_file(self):
        p=self.directory/'STOP';p.write_text('stop')
        self.assertIsNone(Runner(self.env).episode(self.episodes[0],ScriptPolicy(['stop']),stop_file=p))
    def test_determinism(self):
        p=RandomPolicy(STATS)
        a=self.run_policy(p);b=self.run_policy(p)
        for k in ('actions','SR','SPL','NE','nDTW'):self.assertEqual(a[k],b[k])
    def test_policy_whitelist(self):
        class P(ScriptPolicy):
            def act(inner,frames,instruction,state):
                self.assertEqual(set(state),{'executed','decision_index','constants'})
                self.assertEqual(frames,[None]*32)
                return 'stop'
        self.run_policy(P(['stop']))
    def test_click_whitelist_commanded(self):
        class Spy(ClickTranslator):
            def decide(inner,text,obs):
                self.assertEqual(set(obs),{'frames','instruction','executed','decision_index','constants'})
                return super().decide(text,obs)
        b=Spy();cfg=Config(output_format='click',step_cap=100)
        r=self.run_policy(ScriptPolicy(['<goal frame=32 x=0.50 y=0.75>','stop']),cfg,backend=b)
        self.assertEqual(b.commanded_m,[2.,0.]);self.assertEqual(r['actions'],['forward']*8+['stop'])
    def test_all_formats(self):
        for fmt,answers in [('text',['A','D']),('nav',['forward 0.25, stop']),
                            ('waypoint',[{'heading_deg':0,'distance_m':.25,'stop':False},{'heading_deg':0,'distance_m':0,'stop':True}]),
                            ('click',['<goal frame=32 x=0.50 y=0.99>','stop']),('chunk',[[[.25,0,0],[0,0,1]]])]:
            r=self.run_policy(ScriptPolicy(answers),Config(output_format=fmt,step_cap=100))
            self.assertEqual(r['termination'],'stop');self.assertEqual(r['parse_events'],[])
    def test_resume(self):
        path=self.directory/'resume.jsonl'
        # Unique suffix permits repeated tests without deleting prior artifacts.
        while path.exists():path=path.with_name(path.stem+'_next.jsonl')
        runner=Runner(self.env);policy=RandomPolicy(STATS)
        a=runner.evaluate(self.episodes[:3],policy,path,limit=1);self.assertEqual(len(a),1)
        b=runner.evaluate(self.episodes[:3],policy,path);self.assertEqual(len(b),3)
        c=[runner.episode(e,policy) for e in self.episodes[:3]]
        self.assertEqual([r['actions'] for r in b],[r['actions'] for r in c])
    def test_resume_changed_config(self):
        path=self.directory/'changed.jsonl'
        while path.exists():path=path.with_name(path.stem+'_next.jsonl')
        Runner(self.env).evaluate(self.episodes[:1],RandomPolicy(STATS),path)
        with self.assertRaises(ValueError):Runner(self.env,Config(step_cap=99)).evaluate(self.episodes[:1],RandomPolicy(STATS),path)
    def test_truncated_journal(self):
        path=self.directory/'truncated.jsonl'
        while path.exists():path=path.with_name(path.stem+'_next.jsonl')
        runner=Runner(self.env);policy=RandomPolicy(STATS)
        runner.evaluate(self.episodes[:2],policy,path,limit=1)
        with path.open('a') as f:f.write('{"kind":')
        r=runner.evaluate(self.episodes[:2],policy,path)
        self.assertEqual(len(r),2)
    def test_baseline_smoke_20(self):
        for cls in (RandomPolicy,ForwardPolicy,InstructionPolicy):
            policy=cls(STATS)
            for e in self.episodes:
                result=self.run_policy(policy,ep=e)
                self.assertLessEqual(result['steps'],100);self.assertGreaterEqual(result['SPL'],0)
    def test_resume_changed_policy(self):
        path=self.directory/'policy_changed.jsonl'
        while path.exists():path=path.with_name(path.stem+'_next.jsonl')
        runner=Runner(self.env)
        runner.evaluate(self.episodes[:1],ScriptPolicy(['stop']),path)
        with self.assertRaises(ValueError):runner.evaluate(self.episodes[:1],ScriptPolicy(['forward','stop']),path)
    def test_resume_changed_reference(self):
        path=self.directory/'reference_changed.jsonl'
        while path.exists():path=path.with_name(path.stem+'_next.jsonl')
        runner=Runner(self.env);eps=self.episodes[:1]
        runner.evaluate(eps,ScriptPolicy(['stop']),path)
        with self.assertRaises(ValueError):runner.evaluate(eps,ScriptPolicy(['stop']),path,{eps[0].episode_id:[[0,0,0]]})
    def test_resume_mid_episode_stop(self):
        path=self.directory/'mid_episode.jsonl'
        while path.exists():path=path.with_name(path.stem+'_next.jsonl')
        flag=path.with_suffix('.stop')
        class MidStop(ScriptPolicy):
            interrupt=True
            def resume_identity(inner):return dict(test='mid_episode',answers=inner.answers)
            def act(inner,frames,instruction,state):
                if inner.interrupt and state['decision_index']==1:flag.write_text('stop')
                return super().act(frames,instruction,state)
        policy=MidStop(['forward','stop']);runner=Runner(self.env);eps=self.episodes[:1]
        self.assertEqual(runner.evaluate(eps,policy,path,stop_file=flag),[])
        policy.interrupt=False
        resumed=runner.evaluate(eps,policy,path,stop_file=None)
        self.assertEqual(resumed[0]['actions'],['forward','stop'])
