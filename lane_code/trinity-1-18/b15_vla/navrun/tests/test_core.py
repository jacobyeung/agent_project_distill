import copy
import json
import math
import unittest
from pathlib import Path
import numpy as np
from navrun import config, lists, metrics, compare, r2rie, rows, prompts, audit
from navrun.actions import Decoder
from navrun.click import floor_plane, bearing_range, travel, controller, project, label, lead_point, ClickTranslator
from navrun.episodes import Episode, load_split, load_ie, canonical_scene
from navrun.io import digest, ordered_id_sha256, read_json, write_json
from navrun.paths import ROOT, CODEC
from navrun.vendor import nav_text as NT

class GrammarTests(unittest.TestCase):
    def test_nav_values(self):
        self.assertEqual(NT.primitives(NT.parse('forward 0.75, turn_left 30, stop','nav')),['forward']*3+['turn_left']*2+['stop'])
    def test_nav_fullmatch(self):
        for x in ['forward 1.00','forward 0.25 junk','stop, forward 0.25','turn_left 90','forward 0.25,stop','forward 0.25, stop, stop']:
            self.assertIsNone(NT.parse(x,'nav'))
    def test_nav_limit(self):
        self.assertIsNone(NT.parse(', '.join(['forward 0.25']*4),'nav'))
    def test_think_last(self):
        self.assertEqual(NT.parse('<think>x</think>bad</think> stop ','nav'),['stop'])
    def test_click_strict(self):
        for x in ['<goal frame=32 x=0.5 y=0.80>','<goal frame=32 x=1.01 y=0.80>','<goal frame=31 x=0.50 y=0.80>','<goal frame=32 x=0.50 y=0.80> hi']:
            self.assertIsNone(NT.parse(x,'click',32))
    def test_click_dynamic_frame(self):
        self.assertEqual(NT.parse('<goal frame=8 x=0.50 y=0.80>','click',8).frame,8)
    def test_big_turns(self):
        self.assertEqual(len(NT.primitives('turn_around')),12)
        self.assertEqual(NT.primitives('turn_right 90'),['turn_right']*6)
    def test_languages(self):
        self.assertEqual(len(NT.allowed_strings('nav')),910)
        self.assertEqual(len(NT.allowed_strings('click',32)),10205)
    def test_every_nav_string(self):
        self.assertTrue(all(NT.parse(x,'nav') is not None for x in NT.allowed_strings('nav')))
    def test_every_click_string(self):
        self.assertTrue(all(NT.parse(x,'click',32) is not None for x in NT.allowed_strings('click',32)))
    def test_vendor_drift(self):
        import hashlib
        local=ROOT/'navrun/vendor/nav_text.py'
        h=hashlib.sha256(local.read_bytes()).hexdigest()
        self.assertEqual(h,read_json(ROOT/'navrun/vendor/VENDOR.json')['nav_text.py']['sha256'])
        self.assertEqual(local.read_bytes(),CODEC.read_bytes())
        self.assertEqual(local.read_bytes(),(CODEC.parents[4]/'ext_where/vla_where/vendor/nav_text.py').read_bytes())
    def test_trie(self):
        t=NT.TokenTrie([[1,2],[1,3],[1]],9)
        self.assertEqual(t.allowed([]),[1]);self.assertEqual(t.allowed([1]),[2,3,9]);self.assertEqual(t.allowed([7]),[])
    def test_tokenizer_constraint(self):
        class T:
            eos_token_id=999
            def encode(self,s,add_special_tokens=False):return list(s.encode())
        t=NT.constraint(T(),'nav')
        self.assertIn(999,t.allowed(list(b'stop')))
        self.assertNotIn(999,t.allowed(list(b'sto')))

class GeometryTests(unittest.TestCase):
    def test_floor_center(self):
        self.assertAlmostEqual(floor_plane(.5,.75)[1],2.5)
    def test_undefined(self):
        self.assertIsNone(floor_plane(.2,.5)[1]);self.assertEqual(travel(None),.5)
    def test_bearing_sign(self):
        self.assertGreater(bearing_range(*floor_plane(.25,.75))[0],0)
    def test_travel_nonnegative(self):
        self.assertEqual(travel(.1),0);self.assertEqual(travel(20),2)
    def test_rounding(self):
        self.assertEqual(controller(7.5,.125),[])
        self.assertEqual(controller(22.5,.375),['turn_left']*2+['forward']*2)
    def test_project_lift_roundtrip(self):
        for heading in (0,.5,1.5,-2):
            p=np.array([1.,.1,3.]);beta=.2;r=3
            point=p+[-r*math.sin(heading+beta),0,-r*math.cos(heading+beta)]
            uv=project(point,p,heading)
            b,rr=bearing_range(*floor_plane(*uv))
            self.assertAlmostEqual(b,math.degrees(beta));self.assertAlmostEqual(rr,r)
    def test_quantized_click_roundtrip(self):
        bearings=[];ranges=[]
        for b in np.linspace(-35,35,20):
            for r in np.linspace(2,4,10):
                point=[-r*math.sin(math.radians(b)),0,-r*math.cos(math.radians(b))]
                uv=project(point,[0,0,0],0);click=NT.parse(NT.click_text(32,*uv),'click',32)
                bb,rr=bearing_range(*floor_plane(click.x,click.y))
                bearings.append(abs(bb-b));ranges.append(abs(rr-r))
        self.assertLess(np.median(bearings),1);self.assertLess(np.median(ranges),.1)
    def test_lead_interpolation(self):
        np.testing.assert_allclose(lead_point([[0,0,0],[1,0,0],[3,0,0]],2),[2,0,0])
    def test_label_stop(self):
        self.assertEqual(label([0,0,0],0,[0,0,-2],.9)[0],'stop')
    def test_label_clamp(self):
        answer,why=label([0,0,0],0,[0,0,-.5],2)
        self.assertEqual(why,'near_point_clamp');self.assertIn('y=0.99',answer)
    def test_label_behind(self):
        self.assertEqual(label([0,0,0],0,[0,0,2],2)[0],'turn_around')
    def test_occlusion(self):
        self.assertEqual(label([0,0,0],0,[0,0,-2],2,depth=lambda uv:10)[1],'out_of_view')
    def test_backend_whitelist(self):
        with self.assertRaises(ValueError):ClickTranslator().decide('stop',{'sim':None})
    def test_backend_odometry(self):
        b=ClickTranslator();b.executed_commanded(1.25);self.assertEqual(b.commanded_m,[1.25]);b.reset();self.assertEqual(b.commanded_m,[])
    def test_backend_floor(self):
        p,w,i=ClickTranslator().decide('<goal frame=32 x=0.50 y=0.75>',{'constants':{},'frames':[None]})
        self.assertEqual(p,['forward']*8);self.assertEqual(w['distance_m'],2)

class ActionTests(unittest.TestCase):
    def test_text_options(self):
        d=Decoder(config.Config(output_format='text'))
        self.assertEqual(d.decode('A',{})[0],['forward']);self.assertIsNone(d.decode('A because',{})[0])
    def test_waypoint(self):
        d=Decoder(config.Config(output_format='waypoint'))
        self.assertEqual(d.decode(dict(heading_deg=-30,distance_m=.5,stop=False),{})[0],['turn_right']*2+['forward']*2)
    def test_waypoint_invalid(self):
        d=Decoder(config.Config(output_format='waypoint'))
        self.assertIsNone(d.decode(dict(heading_deg=0,distance_m=-1,stop=False),{})[0])
        self.assertIsNone(d.decode(dict(heading_deg=0,distance_m=1,stop='false'),{})[0])
    def test_chunk_residual(self):
        d=Decoder(config.Config(output_format='chunk'))
        a=[]
        for _ in range(10):a+=d.decode([[.1,3,0]],{})[0]
        self.assertEqual(a.count('forward'),4);self.assertEqual(a.count('turn_left'),2)
    def test_chunk_normalised(self):
        d=Decoder(config.Config(output_format='chunk',chunk_normalised=True))
        self.assertEqual(d.decode([[1,0,-1]],{})[0],['forward']*3)
    def test_chunk_stop(self):
        d=Decoder(config.Config(output_format='chunk'))
        self.assertEqual(d.decode([[0,0,1],[.25,0,0]],{})[0],['stop'])
    def test_chunk_invalid(self):
        d=Decoder(config.Config(output_format='chunk'))
        for x in ([[1,2]],[[float('nan'),0,0]],[],[[-1,0,0]]):self.assertIsNone(d.decode(x,{})[0])
    def test_chunk_transaction(self):
        d=Decoder(config.Config(output_format='chunk'))
        d.decode([[.1,0,0]],{});d.decode([[.1,0,0],[0,0,2]],{})
        self.assertAlmostEqual(d.forward_residual,.1)
    def test_config_defaults(self):
        c=config.Config();self.assertEqual((c.step_cap,c.success_radius,c.agent_height,c.agent_radius),(500,3,1.5,.1))
    def test_configs(self):
        for name,fmt in [('N1','nav'),('NU','click')]:
            data,c=config.load_arm(ROOT/'configs'/f'{name}.json');self.assertEqual(c.output_format,fmt)
            self.assertEqual(data['vla']['nav']['train']['episodes'],1082)
    def test_control_gate(self):
        with self.assertRaises(PermissionError):config.load_arm(ROOT/'configs/N0.json')
        self.assertEqual(config.load_arm(ROOT/'configs/N0.json',True)[1].output_format,'nav')
    def test_history(self):
        self.assertEqual(prompts.history_indices(50),[i*50//31 for i in range(32)])
        self.assertEqual(prompts.history_indices(5,1),[5]);self.assertEqual(prompts.history_indices(0),[0]*32)
    def test_prompt_frame(self):
        self.assertIn('frame=8',prompts.prompt('go',output_format='click',history_frames=8))
    def test_prompt_parity(self):
        ep=Episode('1','2','x.glb',[0,0,0],[0,0,0,1],[], 'go',[])
        r=rows.row(ep,'nav',1,'stop',[1,0],'supplied')
        self.assertEqual(r['prompt'],prompts.messages('go',['forward'],'nav')[0]['content'])

class MetricTests(unittest.TestCase):
    def test_dtw_identity(self):
        path=[[0,0,0],[1,0,0],[2,0,0]];self.assertEqual(metrics.fast_dtw(path,path),0)
    def test_dtw_short(self):
        rng=np.random.RandomState(0)
        for n in range(1,5):
            for m in range(1,5):
                a,b=rng.randn(n,3),rng.randn(m,3)
                self.assertAlmostEqual(metrics.fast_dtw(a,b),metrics.exact_dtw(a,b))
    def test_dtw_euclidean(self):
        self.assertEqual(metrics.exact_dtw([[0,0,0]],[[3,4,0]]),5)
    def test_dtw_empty(self):
        self.assertEqual(metrics.fast_dtw([],[]),0);self.assertTrue(math.isinf(metrics.fast_dtw([],[[0,0,0]])))
    def test_success_requires_stop(self):
        p=[[0,0,0],[1,0,0]];r=metrics.metrics(p,p,[2,1],2,False)
        self.assertEqual(r['SR'],0);self.assertEqual(r['OSR'],1)
    def test_success_strict_radius(self):
        r=metrics.metrics([[0,0,0]],[[0,0,0]],[3],3,True);self.assertEqual(r['SR'],0)
    def test_spl(self):
        p=[[0,0,0],[2,0,0],[0,0,0]];r=metrics.metrics(p,p,[2,1,2],2,True)
        self.assertEqual(r['TL'],4);self.assertEqual(r['SPL'],.5);self.assertEqual(r['SDTW'],1)
    def test_dedup(self):
        self.assertEqual(len(metrics.deduplicate_path([[0,0,0]]*3+[[1,0,0]])),2)
    def test_unreachable(self):
        r=metrics.metrics([[0,0,0]],[[0,0,0]],[math.inf],math.inf,False)
        self.assertIsNone(r['NE']);self.assertEqual(r['SR'],0)

class ComparisonTests(unittest.TestCase):
    def test_gain(self):self.assertEqual(compare.paired([1]*30,[0]*30,resamples=100)['outcome'],'GAIN')
    def test_harm(self):self.assertEqual(compare.paired([0]*30,[1]*30,resamples=100)['outcome'],'HARM')
    def test_equivalent(self):self.assertEqual(compare.paired([1]*30,[1]*30,resamples=100)['outcome'],'EQUIVALENT')
    def test_inconclusive(self):self.assertEqual(compare.outcome([-.1,.1],[-.05,.05]),'INCONCLUSIVE')
    def test_holm(self):np.testing.assert_allclose(compare.holm([.01,.04,.03]),[.03,.06,.06])
    def test_family_gate(self):
        r=dict(ci95=[.01,.1],ci90=[.02,.09],mcnemar_p=.2)
        self.assertEqual(compare.family([r])[0]['outcome'],'INCONCLUSIVE')
    def test_paired_ids(self):
        with self.assertRaises(ValueError):compare.compare_records([dict(episode_id='1')],[dict(episode_id='2')])
    def test_stratified_determinism(self):
        a=compare.paired([1,0,1],[0,1,1],['x','x','y'],resamples=100)
        self.assertEqual(a,compare.paired([1,0,1],[0,1,1],['x','x','y'],resamples=100))
    def test_auc(self):self.assertEqual(r2rie.detection_auc([0,1],[.1,.8]),1)
    def test_auc_ties(self):self.assertEqual(r2rie.detection_auc([0,1],[.5,.5]),.5)
    def test_atd(self):
        r=r2rie.detection_atd([3,3,3],[5,None,1],[10,10,10])
        self.assertEqual(r['ATD'],4.5);self.assertEqual(r['early_alarms'],1);self.assertEqual(r['censored_misses'],1)

class DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.train=load_split('train');cls.val=load_split('val_unseen');cls.test=load_split('test')
    def test_loader_counts(self):self.assertEqual((len(self.train),len(self.val)),(10819,1839))
    def test_scene_audit(self):
        a=audit.split_audit(self.train,self.val,self.test)
        self.assertEqual(a['scene_counts']['train'],61);self.assertEqual(a['scene_counts']['val_unseen'],11)
    def test_overlap_rejected(self):
        with self.assertRaises(ValueError):audit.split_audit(self.train,self.train,self.test)
    def test_canonical_scene(self):self.assertEqual(canonical_scene('mp3d/AbCd/AbCd.glb'),'abcd')
    def test_unknown_provenance(self):
        self.assertEqual(audit.audit_manifests(self.val,{})['models']['student']['status'],'provenance unknown')
    def test_manifest_exclusion(self):
        p=ROOT/'out/tests/manifest.json';write_json(p,{'scenes':[self.val[0].scene.upper()]})
        a=audit.audit_manifests(self.val,{'student':str(p)})
        self.assertIn(self.val[0].scene.lower(),a['excluded_scenes'])
        self.assertNotIn(self.val[0].episode_id,a['retained_ids'])
    def test_largest_remainder(self):self.assertEqual(lists.quotas({'a':7,'b':3},3),{'a':2,'b':1})
    def test_balanced(self):
        sample=lists.balanced(self.val,600);self.assertEqual(len(sample),600);self.assertEqual(len({e.scene for e in sample}),11)
        self.assertEqual([e.episode_id for e in sample],[e.episode_id for e in lists.balanced(self.val,600)])
    def test_prefix_balance(self):
        from collections import Counter
        sample=lists.balanced(self.val,600);full=Counter(e.scene for e in sample);prefix=Counter(e.scene for e in sample[:200])
        self.assertTrue(all(abs(prefix[s]-full[s]/3)<=1 for s in full))
    def test_nested_subsets(self):
        a,b=lists.subsets(self.train)
        self.assertEqual((len(a),len(b)),(108,1082));self.assertTrue({e.episode_id for e in a}<={e.episode_id for e in b})
        self.assertEqual((len({e.scene for e in a}),len({e.scene for e in b})),(61,61))
    def test_order_hash(self):self.assertNotEqual(ordered_id_sha256(['1','2']),ordered_id_sha256(['2','1']))
    def test_list_verification(self):
        m=lists.manifest('test',self.val[:10]);self.assertEqual(lists.verify_manifest(m,self.val),self.val[:10])
        m['records'][0]['trajectory_id']='wrong'
        with self.assertRaises(ValueError):lists.verify_manifest(m,self.val)
    def test_rand100_blocked(self):
        with self.assertRaisesRegex(FileNotFoundError,'BLOCKED_IDS_MISSING'):lists.load_rand100(None,self.val)
    def test_ie_pairs(self):
        eps,gt,pairs=load_ie();self.assertEqual((len(eps),len(pairs)),(3218,1609))
        self.assertEqual(len(lists.select_pairs(pairs)),300)
    def test_nav_replay(self):
        rng=np.random.RandomState(4)
        for n in (1,20,100,500):
            actions=rng.randint(1,4,n).tolist()+[0]
            result=[NT.primitives(NT.parse(a,'nav')) for _,a,_ in rows.encode_nav(actions)]
            self.assertEqual([PRIMITIVE for chunk in result for PRIMITIVE in chunk],[('stop','forward','turn_left','turn_right')[a] for a in actions])
    def test_waypoint_replay(self):
        actions=[2]*3+[1]*11+[3]*2+[1]*2+[0]
        replay=[]
        for t,w,n in rows.waypoint_decisions(actions):replay+=['stop'] if w['stop'] else controller(w['heading_deg'],w['distance_m'])
        self.assertEqual(replay,[('stop','forward','turn_left','turn_right')[a] for a in actions])
