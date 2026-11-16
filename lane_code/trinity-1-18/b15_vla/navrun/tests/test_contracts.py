import importlib.util
import sys
import unittest
import numpy as np
from navrun.paths import ROOT, CODEC
from navrun.io import read_json
from navrun import config, metrics
from navrun.click import ClickTranslator
from navrun.model import NativePolicy, CallablePolicy
from navrun.policies import ScriptPolicy
from navrun.runner import Runner
from navrun.sim import Environment
from navrun.episodes import load_split

class ContractTests(unittest.TestCase):
    def test_external_schema10_configs(self):
        path=CODEC.parents[1]/'config.py'
        spec=importlib.util.spec_from_file_location('navrun_external_config',path)
        module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
        for arm in ('N0','N1','NU'):
            cfg,rest=module.VLAConfig.from_spec(read_json(ROOT/'configs'/f'{arm}.json'))
            self.assertEqual(cfg.action_dim,3);self.assertEqual(cfg.proprio_dim,0)
            self.assertEqual(rest['train_effective']['episodes'],1082)
            self.assertEqual(rest['eval_effective']['step_cap'],500)
            self.assertEqual(rest['control_only'],arm=='N0')
    def test_chunk_codec_source_language(self):
        from navrun.vendor import nav_text as NT
        self.assertEqual(NT.GRAMMAR,'nav_grammar_v1')
        self.assertEqual(NT.FALLBACK,('turn_left',))
    def test_click_analytic_fixture(self):
        b=ClickTranslator();p,w,i=b.decide('<goal frame=32 x=0.62 y=0.81>',{})
        self.assertAlmostEqual(i['bearing_deg'],-13.4957332808,places=7)
        self.assertAlmostEqual(i['range_m'],1.25*np.sqrt(1+.24**2)/.62)
        self.assertEqual(p,['turn_right']+['forward']*6)
    def test_unreachable_spl_is_finite(self):
        r=metrics.metrics([[0,0,0]],[[0,0,0]],[float('inf')],float('inf'),False)
        self.assertEqual(r['SPL'],0)
    def test_zero_motion_decision_cap(self):
        cfg=config.Config(output_format='waypoint',step_cap=3);env=Environment(cfg)
        try:
            r=Runner(env).episode(load_split('val_unseen')[0],ScriptPolicy([dict(heading_deg=0,distance_m=0,stop=False)]))
            self.assertEqual(r['decisions'],3);self.assertEqual(r['steps'],0);self.assertEqual(r['termination'],'decision_cap')
        finally:env.close()
    def test_callable_whitelist(self):
        calls=[]
        p=CallablePolicy(lambda x:calls.append(x) or 'stop')
        self.assertEqual(p.act([None],'go',dict(executed=[],decision_index=0,constants={})), 'stop')
        self.assertEqual(set(calls[0]),{'frames','instruction','executed','decision_index','constants'})
    def test_model_rejects_blind_frames(self):
        class Tokenizer:
            eos_token_id=999
            def encode(self,s,add_special_tokens=False):return list(s.encode())
        p=NativePolicy(None,Tokenizer())
        with self.assertRaisesRegex(ValueError,'rendered'):p.act([None]*32,'go',dict(executed=[]))
    def test_policy_server(self):
        import io,json
        from navrun.policy_server import serve
        request=dict(frames=[None],instruction='go',executed=[],decision_index=0,constants={})
        output=io.StringIO();serve(CallablePolicy(lambda x:'stop'),io.StringIO(json.dumps(request)+'\n'),output)
        self.assertEqual(json.loads(output.getvalue()),{'answer':'stop'})
        output=io.StringIO();request['sim']='forbidden'
        serve(ScriptPolicy(['stop']),io.StringIO(json.dumps(request)+'\n'),output)
        self.assertIn('error',json.loads(output.getvalue()))
