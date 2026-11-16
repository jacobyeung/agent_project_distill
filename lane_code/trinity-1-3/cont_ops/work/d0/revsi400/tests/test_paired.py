import offline_guard
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import paired as P


def fixture(value=1):
    tasks=[]
    for i,typ in enumerate(t for ts in P.O.GROUPS.values() for t in ts):
        question='x and facing the x' if 'forward' in typ else 'x facing in the opposite direction of x'
        tasks.append(dict(id=i,example_id=str(i),dataset='fixture',scene_name=str(i%3),question_type=typ,
                          question=question,ground_truth='A'))
    rows=[dict(t,**{k:'fixed' for k in P.META},prompt_tokens=7,media=dict(pixel_sha256='x',frame_receipt={'path':'a'}),status='complete',score=value) for t in tasks]
    return tasks,{arm:copy.deepcopy(rows) for arm in P.ARMS}


def directory():
    p=P.ROOT/'evidence'/('pair_'+uuid.uuid4().hex);p.mkdir();return p


class PairedTests(unittest.TestCase):
    def test_known_difference_all_outputs_and_determinism(self):
        t,a=fixture();_,b=fixture(0)
        r=P.compare(t,a,b,repetitions=10000,partial=True)
        self.assertEqual(r,P.compare(t,a,b,repetitions=10000,partial=True))
        self.assertIsNone(r['decision'])
        for arm,v in r['arms'].items():
            self.assertEqual(v['current']['five_category_mean']['score'],1)
            self.assertEqual(set(v['facing']),{'forward_easy','forward_hard','backward_easy','backward_hard'})
            for x in [*v['paired']['comparisons'].values(),*v['subtypes'].values()]:
                self.assertEqual(x['delta'],1);self.assertEqual(x['percentile_95'],[1,1])
        identity=P.compare(t,a,a,repetitions=20,partial=True)
        self.assertEqual(identity['arms']['B2048']['paired']['comparisons']['five_category_mean']['percentile_95'],[0,0])

    def test_reference_completeness(self):
        rows,_=P.load_packet(P.ROOT/'evidence/reference544',544)
        tasks=P.O.read_rows(P.ROOT/'kit/cohort/c5.jsonl')
        P.validate(tasks,rows,rows)
        self.assertTrue(all(len(v)==679 and all(r['status']=='complete' for r in v) for v in rows.values()))

    def test_cluster_weights_and_zero_denominators(self):
        import numpy as np
        t,a=fixture();_,b=fixture(0)
        for rows in a.values():
            for r in rows:r['score']=int(r['scene_name']=='0')
        r=P.compare(t,a,b,repetitions=100,partial=True)
        for typ,x in r['arms']['B2048']['subtypes'].items():
            self.assertLess(x['valid_replicates'],100)
        self.assertEqual(P.interval(np.array([np.nan])),dict(percentile_95=None,valid_replicates=0))
        # The equal category/subtype mean is not the item-weighted mean.
        expected=sum(sum(next(r['score'] for r in a['B2048'] if r['question_type']==k) for k in ks)/len(ks) for ks in P.O.GROUPS.values())/5
        self.assertAlmostEqual(r['arms']['B2048']['current']['five_category_mean']['score'],expected)

    def test_errors_and_derivation_errors_score_zero(self):
        t,a=fixture();_,b=fixture(0)
        for arm in a:
            a[arm][0].update(status='error',error='synthetic',score=None)
            a[arm][1]['derivation_error']=True
        r=P.compare(t,a,b,repetitions=10,partial=True)
        self.assertEqual(r['arms']['B2048']['subtypes'][t[0]['question_type']]['delta'],0)
        self.assertEqual(r['arms']['B2048']['subtypes'][t[1]['question_type']]['delta'],0)

    def test_every_metadata_field_on_either_input(self):
        t,a=fixture()
        for side in (0,1):
            for arm in P.ARMS:
                for field in [*t[0],*P.META,'media','prompt_tokens']:
                    if field=='prompt_tokens' and arm!='ON16k':continue
                    for missing in (True,False):
                        pair=[copy.deepcopy(a),copy.deepcopy(a)]
                        if missing:pair[side][arm][0].pop(field,None)
                        else:pair[side][arm][0][field]='changed'
                        with self.subTest(side=side,arm=arm,field=field,missing=missing):
                            with self.assertRaises(ValueError):P.validate(t,*pair,partial=True)

    def test_membership_id_types_status_scores_and_schema(self):
        t,a=fixture()
        mutations=[lambda p:p.pop('B4096'),lambda p:p.update(extra=[]),
            lambda p:p['B2048'].pop(),lambda p:p['ON16k'].append(p['ON16k'][0]),
            lambda p:p['B2048'][0].update(id=100,example_id='100'),
            lambda p:p['B2048'].__setitem__(0,None),
            lambda p:p['ON16k'][0].update(status='pending')]
        mutations += [lambda p,v=v:p['B2048'][0].update(score=v) for v in (True,None,float('nan'),float('inf'),-1,2,'1')]
        for mutate in mutations:
            b=copy.deepcopy(a);mutate(b)
            with self.assertRaises(ValueError):P.validate(t,a,b,partial=True)
        with self.assertRaises(ValueError):P.validate(t,a,a)
        t[0]['question_type']='foreign'
        with self.assertRaises(ValueError):P.validate(t,a,a,partial=True)

    def test_invalid_bootstrap_and_scorer_pin(self):
        t,a=fixture()
        for reps,seed in [(0,544),(1.5,544),(5,'x')]:
            with self.assertRaises(ValueError):P.compare(t,a,a,repetitions=reps,seed=seed,partial=True)
        with patch.object(P,'SCORER_SHA','0'*64):
            with self.assertRaises(ValueError):P.compare(t,a,a,repetitions=1,partial=True)

    def test_packet_validation_and_cli(self):
        root=directory();(root/'a0/results/0').mkdir(parents=True)
        marker=dict(mode='production',synthetic=False,generation_synthetic=False,items=679)
        artifact=dict(kind='c1_export',path='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/359fcc3c/m400/artifact.json',sha256='a'*64)
        request=dict(mode='production',models=dict(cp1m200=artifact),reader=dict(step=400,export_verification=dict(status='VERIFIED',step=400,artifact={k:artifact[k] for k in ('path','sha256')})))
        def write():
            for name,value in [('COMPLETE.json',marker),('SPEC.json',dict(step=400,artifact=artifact)),('a0/request.json',request)]:
                (root/name).write_text(json.dumps(value))
            for name in P.ARMS.values():(root/'a0/results/0'/name).write_text('')
        write();P.load_packet(root,400)
        for key,bad in [('mode','proof'),('synthetic',True),('generation_synthetic',True),('items',678)]:
            good=marker[key];marker[key]=bad;write()
            with self.assertRaises(ValueError):P.load_packet(root,400)
            marker[key]=good
        write()
        with self.assertRaises(ValueError):P.load_packet(root,544)
        request['reader']['step']=200;write()
        with self.assertRaises(ValueError):P.load_packet(root,400)
        request['reader']['step']=400;request['mode']='proof';write()
        with self.assertRaises(ValueError):P.load_packet(root,400)
        request['mode']='production';write();(root/'FAILED.json').write_text('{}')
        with self.assertRaises(ValueError):P.load_packet(root,400)
        with patch.object(P,'packet_comparison',return_value={'decision':None}) as compare:
            P.main(['--current',str(root),'--output',str(root/'result.json')]);compare.assert_called_once()
            self.assertEqual(json.loads((root/'result.json').read_text()),{'decision':None})

    def test_packet_protocol_and_provenance(self):
        for step in (True,544,'400'):
            with self.assertRaises(ValueError):P.packet_comparison('a','b',step)
        t,a=fixture();cfg=dict(cells=[],gpus=1,max_tokens=16384,temperature=0,thinking=True,max_model_len=49152,max_seqs=32,inflight=16,smoke_items=0,engine_version='0.32.0',mode='production',models=dict(base={}),datasets=[dict(rows=dict(path='fixture',sha256='a'*64))])
        for field in P.PROTOCOL:
            other=copy.deepcopy(cfg);other[field]='bad'
            with patch.object(P,'load_packet',side_effect=[(a,cfg),(a,other)]):
                with self.assertRaises(ValueError):P.packet_comparison('a','b',400)
        bad=dict(cfg,max_seqs=128)
        with patch.object(P,'load_packet',return_value=(a,bad)):
            with self.assertRaises(ValueError):P.packet_comparison('a','b',400)
        with patch.object(P,'load_packet',return_value=(a,cfg)),patch.object(P,'compare',return_value={}),patch.object(P.O,'read_rows',return_value=t):
            r=P.packet_comparison(P.ROOT/'evidence/reference544',P.ROOT/'evidence/reference544',400)
            self.assertEqual(r['current_step'],400);self.assertEqual(set(r['inputs']['current']),set(P.ARMS))

    def test_text_diagnostic_refuses_unknown_wording(self):
        t,a=fixture()
        for task in t:
            if 'direction' in task['question_type']:task['question']='unrecognized'
        for rows in a.values():
            for row,task in zip(rows,t):row['question']=task['question']
        with self.assertRaises(ValueError):P.compare(t,a,a,repetitions=1,partial=True)

    def test_checkpoint_and_export_verification_refusals(self):
        ref=P.ROOT/'evidence/reference544'
        original=json.loads((ref/'SPEC.json').read_text())
        request=json.loads((ref/'a0/request.json').read_text())
        original_read=Path.read_text
        cases=[]
        for field,value in [('kind','snapshot'),('path','/wrong'),('sha256',None),('sha256','x'),('sha256','0'*64),('sha256','a'*64)]:
            spec=copy.deepcopy(original);spec['artifact'][field]=value;cases.append((spec,request))
        wrong=copy.deepcopy(request);wrong['models']['cp1m200']['path']='/wrong';cases.append((original,wrong))
        for field,value in [('status','HEADER_ONLY_NOT_VERIFIED'),('step',400),('artifact',{})]:
            wrong=copy.deepcopy(request);wrong['reader']['export_verification'][field]=value;cases.append((original,wrong))
        for spec,req in cases:
            def read(path,*args,**kwargs):
                if path==ref/'SPEC.json':return json.dumps(spec)
                if path==ref/'a0/request.json':return json.dumps(req)
                return original_read(path,*args,**kwargs)
            with patch.object(Path,'read_text',read):
                with self.assertRaises(ValueError):P.load_packet(ref,544)
        a,rows=fixture()
        cfg=dict(cells=[],gpus=1,max_tokens=16384,temperature=0,thinking=True,max_model_len=49152,max_seqs=32,inflight=16,smoke_items=0,engine_version='0.32.0',mode='production',models=dict(base={}),datasets=[])
        for field,value in [('models',dict(base={'different':1})),('datasets',[{}])]:
            wrong=dict(cfg,**{field:value})
            with patch.object(P,'load_packet',side_effect=[(rows,cfg),(rows,wrong)]):
                with self.assertRaises(ValueError):P.packet_comparison('a','b',400)


    def test_media_dict_mismatch_and_script_help(self):
        t,a=fixture();b=copy.deepcopy(a);b['B2048'][0]['media']['pixel_sha256']='other'
        with self.assertRaisesRegex(ValueError,'Media metadata'):P.validate(t,a,b,partial=True)
        import runpy
        with patch.object(sys,'argv',['paired.py','--help']):
            with self.assertRaises(SystemExit) as e:runpy.run_path(str(P.ROOT/'paired.py'),run_name='__main__')
        self.assertEqual(e.exception.code,0)
