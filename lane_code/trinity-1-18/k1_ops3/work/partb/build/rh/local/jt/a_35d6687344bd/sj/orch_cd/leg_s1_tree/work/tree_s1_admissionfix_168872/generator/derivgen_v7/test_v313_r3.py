"""Benchmark box contract: private audit replay, invariants and real fixture review."""
import copy,json,re,unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import numpy as np
from scipy.spatial.distance import cdist
from derivgen import box_v313 as B
from derivgen import ground_v312 as old
from derivgen.ground_v313 import Session
from derivgen.ground_v313_tokens import gate_positions
from test_v313 import backend,Geometry,masks,instances,tokenizer
ROOT=Path('/scratch/jjyeung/orch_cd/spec313_kp')
class Provider:
    provider_id='test_analytic_v1'
    def __call__(self,n,obj,geo,best):return B.box([0 if n=='stand' else 2,0,2],[1,1,1],np.eye(3))
def session(**kw):return Session(backend,Geometry(),masks,instances=instances,**kw)
class BoxTests(unittest.TestCase):
    def test_arithmetic_fixture(self):
        a=B.box([0,0,2],[1,1,1],np.eye(3));b=B.box([2,0,2],[1,1,1],np.eye(3))
        self.assertAlmostEqual(B.sampled_box_512(a,b),1.0209091793740521,places=14)
        self.assertEqual(B.number(B.sampled_box_512(a,b),2),'1.02')
    def test_precision_failures_and_ties(self):
        self.assertEqual(B.number(-0.00000001,2),'0.00')
        self.assertEqual(B.number(.125,2),'0.12');self.assertEqual(B.number(.375,2),'0.38')
        x=B.box([0,0,2],[1,1,1],np.eye(3));body=B.serialize('chair','B1',[1],1,x)
        self.assertEqual(B.parse(body)['label'],'B1')
        for bad in [body.replace('1.00 x','-1.00 x',1),body.replace('yaw 0','yaw 180',1),body.replace('0.00,','-0.00,',1),body.replace('frames 1','frames 2')]:
            with self.assertRaises(ValueError):B.parse(bad)
        reg=B.BoxRegistry()
        for i,n in enumerate(['chair','table','desk'],1):reg.ingest(B.serialize(n,f'B{i}',[1],1,x),x)
        got,_=reg.gap('chair',['table','desk']);self.assertIn('min "table","desk"',got)
    def test_registry_provider_failures_and_invalidation(self):
        s=session(box_provider=Provider());self.assertEqual(s.box_provider_id,'test_analytic_v1')
        s.execute('<ground obj="stand" mode="box">');s.execute('<ground obj="face" mode="box">')
        self.assertEqual(len(s.registry._points),0);self.assertEqual(len(s.box_registry.records),2)
        s.execute('<gap a="stand" b="face" rule="sampled_box_512">')
        B.replay_audit(s.events)
        self.assertTrue(all(e['audit']['box_provider']=='test_analytic_v1' for e in s.events))
        s.execute('<ground obj="stand" mode="instances">')
        self.assertEqual(s.execute('<gap a="stand" b="face" rule="sampled_box_512">'),'not seen')
        class Missing(Provider):
            def __call__(self,*args):return None
        s.box_provider=Missing();self.assertEqual(s.execute('<ground obj="face" mode="box">'),'face: box unavailable')
        self.assertEqual(len(s.box_registry.records),2)
        with self.assertRaises(ValueError):s.execute('<gap a="face" b="face" rule="sampled_box_512">')
        s.box_registry.invalidate('stand','unresolved')
        self.assertEqual(s.execute('<gap a="stand" b="face" rule="sampled_box_512">'),'unresolved')
    def test_fixed_best_does_not_reselect(self):
        s=session(box_provider=Provider())
        obj=dict(instance_id=1,visible=[1,2],areas={'1':2.,'2':1.},frames=[2],points={'2':[[1,2,3]]})
        s._instances=lambda n:[obj]
        self.assertEqual(s.execute('<ground obj="chair" mode="box">'),'chair: box unavailable')
        self.assertFalse(s.box_registry.records)
    def test_default_provider_and_legacy_rejection(self):
        self.assertEqual(session().box_provider_id,'fit_gbox_fused_full_v1')
        for call in ['<ground obj="stand" mode="box">','<gap a="stand" b="face" rule="sampled_box_512">']:
            with self.assertRaises(ValueError):session(enabled=False).execute(call)
    def test_box_call_span_includes_mode(self):
        call='<ground obj="chair" mode="box">';suffix='<think>\n'+call+'\n</think>'
        enc=tokenizer.encode(suffix,add_special_tokens=False);positions=gate_positions(tokenizer,suffix)
        self.assertTrue(positions)
        self.assertEqual(''.join(suffix[a:b] for i,(a,b) in enumerate(enc.offsets) if i in positions),call)
    def test_all_491_independent_labels_survive_audit(self):
        rows=[json.loads(s) for s in (ROOT/'out/AUDIT_REPLAY_r4.jsonl').read_text().splitlines()]
        self.assertEqual(Counter(r['pool'] for r in rows),{'training':252,'dev':239})
        for r in rows:
            values=B.replay_audit(r['events']);self.assertEqual(B.number(values[0],2),B.number(r['independent_label'],2),r['qid'])
    def test_changed_draw_order_fails_replay(self):
        rows=[json.loads(s) for s in (ROOT/'out/AUDIT_REPLAY_r4.jsonl').read_text().splitlines()]
        r=next(r for r in rows if r['reverse_changes'])
        original=B.sampled_box_512
        with patch.object(B,'sampled_box_512',lambda a,b:original(b,a)):
            with self.assertRaisesRegex(ValueError,'audit_box_replay_mismatch'):B.replay_audit(r['events'])
    def test_changed_axis_sign_fails_replay(self):
        rows=[json.loads(s) for s in (ROOT/'out/AUDIT_REPLAY_r4.jsonl').read_text().splitlines()]
        r=copy.deepcopy(next(r for r in rows if r['sign_changes']));ev=r['events'][1]
        ev['audit']['full_precision_box']['axes'][0]=[-v for v in ev['audit']['full_precision_box']['axes'][0]]
        rec=B.parse(ev['response'].split('\n',1)[1].rsplit('\n',1)[0])
        ev['response']=old.wrap(B.serialize(rec['name'],rec['label'],rec['frames'],rec['best'],ev['audit']['full_precision_box']))
        with self.assertRaisesRegex(ValueError,'audit_box_replay_mismatch'):B.replay_audit(r['events'])
    def test_audit_metadata_and_missing_audit_fail_closed(self):
        row=json.loads((ROOT/'out/AUDIT_REPLAY_r4.jsonl').read_text().splitlines()[0])
        for field,value in [('seed',1),('draw_order','b_then_a'),('samples',511)]:
            events=copy.deepcopy(row['events']);events[-1]['audit']['sampler'][field]=value
            with self.assertRaisesRegex(ValueError,'audit_sampler_mismatch'):B.replay_audit(events)
        events=copy.deepcopy(row['events']);events[-1]['audit']['ordered_box_labels'].reverse()
        with self.assertRaisesRegex(ValueError,'audit_draw_order_mismatch'):B.replay_audit(events)
        events=copy.deepcopy(row['events']);events[0].pop('audit')
        with self.assertRaises(KeyError):B.replay_audit(events)
    def test_gravity_alignment_and_public_precision(self):
        x=B.yaw_box([.1234,-.0001,2.3456],[1.1234,2.3456,3.4567],37.4)
        body=B.serialize('chair','B1',[1],1,x)
        self.assertIn('(0.12, 0.00, 2.35) m',body)
        self.assertIn('size 1.12 x 2.35 x 3.46 m',body)
        self.assertIn('yaw 37 deg',body);self.assertNotIn('axes',body)
        self.assertFalse(re.search(r'\d+\.\d{3}',body))
        x['axes']=np.array([[1,0,0],[0,np.cos(.1),np.sin(.1)],[0,-np.sin(.1),np.cos(.1)]])
        # v3.14: a tilted box prints its enclosing gravity-aligned box (test_v314.TiltedAnnotation).
        self.assertIn('size ',B.serialize('chair','B1',[1],1,x))
    def test_measurement_uses_unrounded_boxes(self):
        a=B.yaw_box([0,0,0],[1,1,1],0);b=B.yaw_box([2.0049,0,0],[1,1,1],0)
        reg=B.BoxRegistry()
        for i,(name,value) in enumerate([('chair',a),('table',b)],1):
            reg.ingest(B.serialize(name,f'B{i}',[1],1,value),value)
        body,values=reg.gap('chair',['table'])
        self.assertEqual(values[0],B.sampled_box_512(a,b))
        self.assertEqual(body,f'distance {B.number(values[0],2)} m')
        self.assertEqual(len(body.splitlines()),1)
    def test_pairwise_reference_matches_independent_nearest_neighbor(self):
        from scipy.spatial import cKDTree
        a=B.box([.3,-.1,2],[.9,1.8,.7],np.eye(3));b=B.box([3,1,2],[1,.6,2],np.eye(3))
        rng=np.random.Generator(np.random.PCG64(0));points=[]
        for x in [a,b]:points.append((rng.uniform(-1,1,(512,3))*(x['lengths']/2))@x['axes']+x['centre'])
        self.assertEqual(B.sampled_box_512(a,b),float(cKDTree(points[0]).query(points[1],workers=1)[0].min()))
class FixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows={p.stem:[json.loads(s) for s in p.read_text().splitlines()] for p in (ROOT/'out/fixtures_r4').glob('*.jsonl')}
    def test_all_families_questions_names_and_answers(self):
        self.assertEqual(len(self.rows),12)
        for family,rows in self.rows.items():
            self.assertEqual(len(rows),20,family)
            for r in rows:
                self.assertTrue(r['question']);self.assertNotIn(r['answer'],['review-only','not seen','None'])
                self.assertLessEqual(r['suffix_tokens'],5000);self.assertFalse(r['training_admitted'])
                for ev in r['events']:
                    names=re.findall(r'(?:obj|a|b)="([^"]+)"',ev['call'])
                    self.assertFalse(set(names)&{'stand','face','far','target','query'})
                old.validate_evidence(r)
    def test_every_box_fixture_audit_and_answer(self):
        for family in ['absolute_sampled_box','relative_sampled_box']:
            for r in self.rows[family]:
                values=B.replay_audit(r['events']);self.assertTrue(values)
                if family=='absolute_sampled_box':self.assertEqual(r['answer'],B.number(values[0],2))
                else:
                    names=list(old.option_map(r['options']).values());winner=names[int(np.argmin(values))]
                    self.assertEqual(r['answer'],old.letter(r['options'],winner))
                    self.assertEqual(r['option_shuffle'],'qid-sha256-v1')
                self.assertEqual(str(r['gt_answer']) if family=='relative_sampled_box' else B.number(float(r['gt_answer']),2),r['answer'])
    def test_public_precision_and_audit_separation(self):
        from decimal import Decimal
        for family in ['absolute_sampled_box','relative_sampled_box']:
            for row in self.rows[family]:
                self.assertNotIn('full_precision_box',row['suffix'])
                self.assertNotIn('ordered_box_labels',row['suffix'])
                for event in row['events']:
                    body=event['response']
                    self.assertFalse(re.search(r'\d+\.\d{3}',body))
                    if 'mode="box"' in event['call']:
                        self.assertIn('yaw ',body);self.assertNotIn('axes ',body)
                        self.assertIn('full_precision_box',event['audit'])
                    else:
                        if family=='absolute_sampled_box':
                            d=re.search(r'distance (\d+\.\d{2}) m',body)[1]
                            self.assertEqual(row['answer'],d)
                        else:
                            ds=dict(re.findall(r'^([^\n]+): (\d+\.\d{2}) m$',body,re.M))
                            minimum=min(map(Decimal,ds.values()))
                            winners=[n for n,d in ds.items() if Decimal(d)==minimum]
                            self.assertEqual(len(winners),1)
                            self.assertEqual(row['answer'],old.letter(row['options'],winners[0]))
    def test_every_surface_distance_from_printed_text(self):
        from decimal import Decimal,localcontext,ROUND_HALF_EVEN
        for family,rows in self.rows.items():
            for r in rows:
                for ev in r['events']:
                    points=re.findall(r'^P\d+: (.+?) nearest point cam\d+ \([^\n]+?\) m; f1 \(([^)]+)\) m$',ev['response'],re.M)
                    for (a,x),(b,y) in zip(points[::2],points[1::2]):
                        with localcontext() as ctx:
                            ctx.prec=80
                            d=sum((Decimal(xx)-Decimal(yy))**2 for xx,yy in zip(x.split(', '),y.split(', '))).sqrt().quantize(Decimal('.01'),rounding=ROUND_HALF_EVEN)
                        prefix=('' if len(points)==2 else re.escape(b)+': ') if ev['call'].startswith('<gap ') else 'visible pair distance '
                        match=re.search(r'^'+prefix+r'(\d+\.\d{2}) m$',ev['response'],re.M)
                        self.assertIsNotNone(match,(family,r['qid']));self.assertEqual(d,Decimal(match[1]))
    def test_every_new_distance_template_matches_benchmark_wording(self):
        for family in ['absolute_sampled_box','relative_sampled_box']:
            for r in self.rows[family]:
                roles=r['roles']
                expected=(f'Measuring from the closest point of each object, what is the distance between the {roles["a"]} and the {roles["b"]} (in meters)?' if family=='absolute_sampled_box' else
                    f'Measuring from the closest point of each object, which of these objects ({", ".join(roles["cands"])}) is the closest to the {roles["target"]}?')
                self.assertEqual(r['question'],expected)

class FinalFixtureTests(unittest.TestCase):
    def test_letter_balance_and_exact_count_size_templates(self):
        root=ROOT/'out/fixtures_r4'
        for family,n in [('relative_sampled_box',2),('relative_gap_witness',2),('appearance_order',4)]:
            rows=[json.loads(s) for s in (root/(family+'.jsonl')).read_text().splitlines()]
            self.assertEqual(Counter(r['answer'] for r in rows),{chr(65+i):20//n for i in range(n)})
        for family in ['counting','instances','unresolved','extent_ends']:
            rows=[json.loads(s) for s in (root/(family+'.jsonl')).read_text().splitlines()]
            for r in rows:
                name=r['roles']['obj']
                expected=(f'What is the length of the longest dimension (length, width, or height) of the {name}, measured in centimeters?' if family=='extent_ends' else f'How many {name}(s) are in this room?')
                self.assertEqual(r['question'],expected)
    def test_extent_distance_from_printed_points(self):
        from decimal import Decimal,ROUND_HALF_EVEN
        rows=[json.loads(s) for s in (ROOT/'out/fixtures_r4/extent_ends.jsonl').read_text().splitlines()]
        for r in rows:
            body=r['events'][-1]['response']
            points=re.findall(r' extent (?:start|end) cam\d+ .*?; f1 \(([^)]+)\) m',body)
            self.assertEqual(len(points),2)
            d=sum((Decimal(a)-Decimal(b))**2 for a,b in zip(points[0].split(', '),points[1].split(', '))).sqrt().quantize(Decimal('.01'),rounding=ROUND_HALF_EVEN)
            self.assertIn(f'observed endpoint distance {d:.2f} m',body)
            self.assertEqual(Decimal(r['answer']),d*100)
    def test_all_responses_pin_provider_and_diagnostic_exclusion(self):
        for p in (ROOT/'out/fixtures_r4').glob('*.jsonl'):
            for line in p.read_text().splitlines():
                r=json.loads(line)
                for e in r['events']:self.assertTrue(e.get('audit',{}).get('box_provider'),(p.name,r['qid']))
                if r['review_scope']!='benchmark':self.assertTrue(r['excluded_from_benchmark_scoring'])

class BenchmarkSourceTests(unittest.TestCase):
    def test_templates_from_pinned_benchmark_extractor(self):
        import ast
        from collections import defaultdict
        path=Path('/scratch/jjyeung/orch_cd/ground_rows/work/apply_v4_derivgen/test_v312_benchmark.py')
        tree=ast.parse(path.read_text())
        nodes=[n for n in tree.body if
               (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('SLOTS','PATTERNS') for t in n.targets))
               or isinstance(n,ast.For)
               or (isinstance(n,ast.FunctionDef) and n.name in ('benchmark_templates','matches_template'))]
        namespace=dict(json=json,re=re,Counter=Counter,defaultdict=defaultdict,
            BENCHMARK=Path('/scratch/jjyeung/orch_cd/aws_32/a_build/eval/orchard_bin/cp4tk_eval/official/meta_5130.jsonl'))
        exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),namespace)
        templates=namespace['benchmark_templates']()
        for family in ['absolute_sampled_box','relative_sampled_box']:
            for line in (ROOT/'out/fixtures_r4'/(family+'.jsonl')).read_text().splitlines():
                row=json.loads(line);self.assertTrue(namespace['matches_template'](row,templates),row['question'])

if __name__=='__main__':unittest.main()
