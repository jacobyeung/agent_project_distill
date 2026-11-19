"""CPU-only synthetic and authenticated-loader regression tests."""
import sys
sys.dont_write_bytecode = True
import ast
import copy
import contextlib
import hashlib
import io
import json
import random
import unittest
import uuid
from collections import defaultdict
from pathlib import Path
import numpy as np

ROOT = Path(__file__).absolute().parents[1]
sys.path.insert(0, str(ROOT))
from callrate import setup_scorer, paired, execute, parser, summary, main as cli_main
from populations import tag_items, inherit_tags, room_mra
from callrate import check_pair_items
from return_reader import Inputs, OUT3, OUT3S, canonical, load_read
from measurements import capped, measure, question_template, follows
from bootstrap import bootstrap
from wording import TEMPL

IO = Inputs()
SC = setup_scorer(IO, IO.root/OUT3/'A4/src')
BASE = IO.root/OUT3/'bases'


def item(kind='object_abs_distance', unit='meters'):
    return dict(id='synthetic', room_key='synthetic-room', question_type=kind,
                question='What is the distance between the chair and the table in '+unit+'?',
                ground_truth=1., answer_type='numeric', options=[])


def row(records=None, answer='1', finish='eos', text=None):
    return dict(id='synthetic', room_key='synthetic-room', type='object_abs_distance',
                output=dict(text='</think><answer>'+answer+'</answer>' if text is None else text,
                            finish=finish, calls={'records': records or []}))


def gap(value=1, **extra):
    return dict(call='<gap a="chair" b="table" rule="box_grid_5cm">', response=f'distance {value} m', **extra)


class PopulationTests(unittest.TestCase):
    def test_explicit_sets_and_tags(self):
        i = item('room_size_estimation')
        for manifest in ({'items':[i], 'sets':{'dev-S1':['synthetic']}},
                         {'items':[{**i, 'r0_split':'R0-dev'}]}):
            tagged = tag_items(manifest)
            self.assertIn(tagged['synthetic']['_population'], ('dev-S1','R0-dev'))
        self.assertNotIn('_population', i)

    def test_unknown_membership_never_uses_prefix_or_dataset(self):
        i = {**item('room_size_estimation'), 'id':'r0_fake', 'dataset':'scannetpp'}
        self.assertIsNone(tag_items({'items':[i]})['r0_fake']['_population'])

    def test_conflicts_duplicates_and_absent_members(self):
        i = {**item('room_size_estimation'), 'r0_split':'R0-dev'}
        for sets in ({'dev-S1':['synthetic']}, {'R0-dev':['synthetic','synthetic']},
                     {'dev-S1':['absent']}, {'R0-dev':['synthetic'],'dev-S1':['synthetic']}):
            with self.subTest(sets=sets), self.assertRaises(ValueError):
                tag_items({'items':[i], 'sets':sets})

    def test_catalog_join_checks_identity_and_population(self):
        items = tag_items({'items':[item('room_size_estimation')]})
        catalog = tag_items({'items':[{**item('room_size_estimation'), 'r0_split':'R0-dev'}]})
        inherit_tags(items, catalog, check_pair_items)
        self.assertEqual(items['synthetic']['_population'], 'R0-dev')
        catalog['synthetic']['_population'] = 'dev-S1'
        with self.assertRaisesRegex(ValueError, 'population differs'):
            inherit_tags(items, catalog, check_pair_items)
        catalog['synthetic']['ground_truth'] = 999
        with self.assertRaisesRegex(ValueError, 'Paired item differs'):
            inherit_tags(items, catalog, check_pair_items)

    def test_population_bootstrap_clusters_rooms_and_tracks_missing(self):
        items, a, b = {}, {}, {}
        for k, room, pop, score in [('x','room1','dev-S1',1.), ('y','room1','dev-S1',.5),
                                     ('z','room2','dev-S1',0.), ('reserve','room3','R0-dev',.8),
                                     ('unknown','room4',None,.3)]:
            i = {**item('room_size_estimation'), 'id':k, 'room_key':room, '_population':pop}
            items[k] = i
            m = measure({**row(), 'id':k}, i, SC)
            a[k] = {**m, 'score':score}
            b[k] = {**m, 'score':0.}
        result = room_mra({'a':a, 'b':b}, {'a':items,'b':items})
        expected = bootstrap([('room1',100.),('room1',50.),('room2',0.)])
        for key, value in expected.items():
            self.assertEqual(result['dev-S1']['paired'][key], value)
        self.assertEqual(result['dev-S1']['a']['mra_answer'], .5)
        self.assertEqual(result['MISSING']['a']['n'], 1)
        self.assertEqual(result['all']['a']['n'], 5)
        partial = room_mra({'a':{k:v for k,v in a.items() if k!='reserve'}, 'b':b}, {'a':items,'b':items})
        self.assertEqual(partial['R0-dev']['a']['status'], 'MISSING')
        self.assertEqual(partial['R0-dev']['a']['missing_ids'], ['reserve'])
        self.assertIsNone(partial['R0-dev']['paired']['value'])


class MetricTests(unittest.TestCase):
    def test_no_call(self):
        m = measure(row(), item(), SC)
        self.assertEqual(m['call'], 0)
        self.assertIsNone(m['usage'])

    def test_unserved_call_counts(self):
        m = measure(row([dict(call='<ground obj="chair" mode="box">', served=False)]), item(), SC)
        self.assertEqual(m['call'], 1)
        self.assertIsNone(m['usage'])

    def test_wrong_type_call_does_not_count(self):
        m = measure(row([dict(call='<turn from=1 to=2>', response='turn = 1 deg')]), item(), SC)
        self.assertEqual(m['call'], 0)
        self.assertIsNone(m['usage'])

    def test_hook_records(self):
        r = row([gap()]); r['output']['hook'] = r['output'].pop('calls')
        self.assertEqual(measure(r,item(),SC)['call'],1)

    def test_text_mention_is_not_a_recorded_call(self):
        self.assertEqual(measure(row(text='<gap a="chair" b="table"> </think>1'), item(), SC)['call'], 0)

    def test_caps_match_existing_definition(self):
        for finish in ('max_calls', 'max_new_tokens', 'length'):
            with self.subTest(finish=finish):
                self.assertTrue(capped({'finish':finish}))
        for finish in ('eos', 'stop', 'context_exhaustion', None):
            self.assertFalse(capped({'finish':finish}))

    def test_capped_without_call(self):
        m = measure(row(finish='length',text='still thinking 42'), item(), SC)
        self.assertEqual((m['capped'],m['call'],m['answer']),(1,0,0))

    def test_follow_and_dont_follow(self):
        self.assertEqual(measure(row([gap()],answer='1'),item(),SC)['usage'],1)
        self.assertEqual(measure(row([gap()],answer='2'),item(),SC)['usage'],0)

    def test_missing_response(self):
        self.assertIsNone(measure(row([dict(call='<gap a="chair" b="table">')]), item(),SC)['usage'])

    def test_error_and_unserved_responses(self):
        for g in (dict(call='<gap a="chair" b="table">',response='error: no geometry'),gap(served=False)):
            self.assertIsNone(measure(row([g]),item(),SC)['usage'])

    def test_all_length_units(self):
        for unit,factor in [('meters',1),('cm',100),('mm',1000),('feet',1/.3048),('inches',1/.0254)]:
            with self.subTest(unit=unit):
                self.assertEqual(measure(row([gap(2)],answer=str(2*factor)),item(unit=unit),SC)['usage'],1)
                self.assertEqual(measure(row([gap(2)],answer='2 m'),item(unit=unit),SC)['usage'],1)

    def test_tolerance_and_zero(self):
        for value,answer,want in [(100,'104.9',1),(100,'105.1',0),(0,'0',1),(0,'0.000000001',0)]:
            self.assertEqual(measure(row([gap(value)],answer=answer),item(),SC)['usage'],want)

    def test_nonfinite_response_is_ineligible(self):
        m=measure(row([gap('1e309')]),item(),SC)
        self.assertIsNone(m['usage'])
        self.assertEqual(m['usage_reason'],'nonfinite_response')

    def test_last_parsed_response(self):
        self.assertEqual(measure(row([gap(1),gap(2)],answer='2'),item(),SC)['usage'],1)

    def test_called_parsed_without_answer_is_eligible_failure(self):
        m=measure(row([gap()],text='reasoning 1'),item(),SC)
        self.assertEqual((m['usage'],m['answer']),(0,0))

    def test_max_calls_suppresses_answer(self):
        m=measure(row([gap()],finish='max_calls'),item(),SC)
        self.assertEqual((m['usage'],m['answer']),(0,0))

    def test_rotation(self):
        i=item('camera_rotation');i['question']='Signed turn in degrees?'
        self.assertEqual(measure(row([dict(call='<turn from=1 to=2>',response='turn = -90 deg')],answer='-90 degrees'),i,SC)['usage'],1)

    def test_direction_fixed_math(self):
        i=item('camera_movement_direction');i.update(question='Direction?',ground_truth='A',answer_type='multiple_choice',options=['A. left','B. right','C. forward','D. backward'])
        r=dict(call='<move from=1 to=2>',response='dx = -3 m, dy = 0 m, dz = 1 m, distance = 3.16 m')
        self.assertEqual(measure(row([r],answer='A'),i,SC)['usage'],1)
        self.assertEqual(measure(row([r],answer='B'),i,SC)['usage'],0)

    def test_room_response(self):
        i=item('room_size_estimation');i['question']='Area in square meters?'
        r=dict(call='<ground mode="room">',response='room: frames 1,2\nfloor height 0.00 m\nfloor cells 400; supported cells 400; cell size 0.05 m; min frames 2\narea 1.00 m^2')
        self.assertEqual(measure(row([r],answer='10000 cm^2'),i,SC)['usage'],1)
        self.assertEqual(measure(row([r],answer='2'),i,SC)['usage'],0)

    def test_unknown_type_is_reported_not_invented(self):
        m=measure(row(),item('unregistered_synthetic_type'),SC)
        self.assertIsNone(m['call'])
        self.assertIn('MISSING',m['call_status'])

    def test_additional_type_with_explicit_routing(self):
        i=item('synthetic_routed');i['routing']={'events':[{'kind':'tool_call','token':'<new_head x=1>'}]}
        m=measure(row([{'call':'<new_head x=1>'}]),i,SC)
        self.assertEqual(m['call'],1)

    def test_mask_question(self):
        s=question_template(item(),SC)
        self.assertNotIn('chair',s);self.assertNotIn('table',s);self.assertEqual(s.count('<object>'),2)

    def test_wording_matches_source(self):
        source=(IO.root/'dist_diag/work/q1/classify.py').read_text()
        node=next(n for n in ast.parse(source).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='TEMPL' for t in n.targets))
        self.assertEqual({k:v.pattern for k,v in TEMPL.items()},ast.literal_eval(node.value))

    def test_bootstrap_exact_reference(self):
        source=(IO.root/OUT3S/'score_r5.py').read_text()
        node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='bootstrap')
        scope=dict(np=np,random=random,defaultdict=defaultdict)
        exec(compile(ast.Module(body=[node],type_ignores=[]),'score_r5.py','exec'),scope)
        pairs=[('room1',2),('room1',8),('room2',-4),('room3',1)]
        self.assertEqual(bootstrap(pairs),scope['bootstrap'](pairs))
        self.assertEqual(bootstrap([]),scope['bootstrap']([]))

    def test_paired_usage_intersection(self):
        a=measure(row([gap()]),item(),SC); b=measure(row(),item(),SC)
        self.assertEqual(paired({'synthetic':a},{'synthetic':b})['usage']['n'],0)


class LoaderTests(unittest.TestCase):
    def setUp(self):
        self.work=ROOT/'tests/artifacts'/uuid.uuid4().hex
        self.package=self.work/'package'
        self.ret=self.work/'ret'
        self.journal=self.ret/'metadata/reads/0/metadata/journals/0/0'
        self.journal.mkdir(parents=True)
        (self.package/'src/items').mkdir(parents=True)
        (self.package/'package').mkdir()
        ref=next((BASE/'b1/work/ret/metadata/reads/0/metadata/journals').glob('*/*/environment.json'))
        binding=json.loads(ref.read_text())['binding']
        self.expected=dict(arm='tower',expected=1,modes=['none'],perception_memo='on',perception_memo_modules=['g3t'],perception_memo_verify_ids=[],save_own_depth=False,stage1_select_rule='candidates_argmax',types=[0])
        self.pin=dict(run='synthetic',step=400,member_directory='m400',lineage='SFT',object='synthetic400',config_sha256='synthetic-config',preparation_sha256={})
        self.plan={'read_settings':[self.expected],'export_binding':self.pin}
        self.write(self.package/'READ_PLAN.json',self.plan)
        self.write(self.package/'package/0.json',{'plan_sha256':'synthetic-plan'})
        (self.package/'tower_sequence.py').write_text('# Synthetic test operator\n')
        operator=hashlib.sha256((self.package/'tower_sequence.py').read_bytes()).hexdigest()
        self.identity={'plan':'synthetic-plan','operator_sha256':operator,'reads':[self.expected]}
        self.write(self.ret/'metadata/IDENTITY.json',self.identity)
        self.write(self.ret/'metadata/EXPORT_PIN.json',{**self.pin,'preparation':{}})
        self.manifest={'items':[item()],'item_set_sha256':'synthetic-set'}
        self.write(self.package/'src/items/devs1_routed.json',self.manifest)
        self.write(self.package/'src/9.json',{'order':['object_abs_distance']})
        settings={k:self.expected[k] for k in ('stage1_select_rule','perception_memo','perception_memo_modules','perception_memo_verify_ids','save_own_depth')}
        binding.update(step=400,stage1_select_rule='candidates_argmax',perception_memo='on',perception_memo_verify_ids=[],items_sha256=hashlib.sha256((self.package/'src/items/devs1_routed.json').read_bytes()).hexdigest(),item_set_sha256='synthetic-set',settings_sha256=canonical(settings))
        self.env={'binding':binding,'settings':settings}
        self.write(self.journal/'environment.json',self.env)
        self.record={**row([gap()]),'complete':True,'arm':'tower','mode':'none'}
        self.journal_text=json.dumps(self.record)+'\n'
        (self.journal/'items.jsonl').write_text(self.journal_text)

    def write(self,p,value):
        p.write_text(json.dumps(value)+'\n')

    def load(self,step=400):
        return load_read(Inputs(),self.ret,self.package,0,step,BASE)

    def test_new_step_400_and_600(self):
        self.assertEqual(len(self.load()[0]),1)
        self.pin.update(step=600,member_directory='m600',object='synthetic600')
        self.write(self.package/'READ_PLAN.json',self.plan)
        self.write(self.ret/'metadata/EXPORT_PIN.json',{**self.pin,'preparation':{}})
        self.env['binding']['step']=600
        self.write(self.journal/'environment.json',self.env)
        self.assertEqual(len(self.load(600)[0]),1)

    def test_identity_mismatch(self):
        self.identity['plan']='wrong';self.write(self.ret/'metadata/IDENTITY.json',self.identity)
        with self.assertRaisesRegex(ValueError,'plan/operator'):self.load()

    def test_export_mismatch(self):
        self.write(self.ret/'metadata/EXPORT_PIN.json',{**self.pin,'step':600,'preparation':{}})
        with self.assertRaisesRegex(ValueError,'Export binding'):self.load()

    def test_settings_tamper(self):
        self.env['settings']['perception_memo']='off';self.write(self.journal/'environment.json',self.env)
        with self.assertRaisesRegex(ValueError,'Settings hash'):self.load()

    def test_evaluator_binding_tamper(self):
        self.env['binding']['evaluator_code_sha256']='wrong';self.write(self.journal/'environment.json',self.env)
        with self.assertRaisesRegex(ValueError,'Journal binding differs'):self.load()

    def test_duplicate_row(self):
        (self.journal/'items.jsonl').write_text(self.journal_text*2)
        with self.assertRaisesRegex(ValueError,'Duplicate'):self.load()

    def test_partial_journal_tail(self):
        (self.journal/'items.jsonl').write_text(self.journal_text.rstrip())
        with self.assertRaisesRegex(ValueError,'Uncommitted tail'):self.load()

    def test_started_without_items(self):
        p=self.journal.parent/'1';p.mkdir();self.write(p/'STARTED.json',{})
        with self.assertRaisesRegex(ValueError,'Started segment'):self.load()

    def test_incomplete_row(self):
        self.record['complete']=False
        (self.journal/'items.jsonl').write_text(json.dumps(self.record)+'\n')
        with self.assertRaisesRegex(ValueError,'Uncommitted'):self.load()

    def test_missing_manifest(self):
        self.env['binding']['items_sha256']='absent-sha256';self.write(self.journal/'environment.json',self.env)
        with self.assertRaisesRegex(FileNotFoundError,'MISSING: unique manifest'):self.load()

    def test_cli_step400_vs600_and_read_only(self):
        a_ret,a_package=self.ret,self.package
        self.setUp()
        self.pin.update(step=600,member_directory='m600',object='synthetic600')
        self.write(self.package/'READ_PLAN.json',self.plan)
        self.write(self.ret/'metadata/EXPORT_PIN.json',{**self.pin,'preparation':{}})
        self.env['binding']['step']=600
        self.write(self.journal/'environment.json',self.env)
        paths=list(a_ret.rglob('*'))+list(self.ret.rglob('*'))
        before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}
        target=self.work/'comparison'
        args=['--a',str(a_ret),'--a-step','400','--a-package',str(a_package),
              '--b',str(self.ret),'--b-step','600','--b-package',str(self.package),
              '--scorer-src',str(IO.root/OUT3/'A4/src'),'--baseline-root',str(BASE),'--out',str(target)]
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cli_main(args),0)
        result=json.loads((target/'callrate.json').read_text())
        self.assertEqual((result['a_step'],result['b_step']),(400,600))
        self.assertEqual(result['types']['object_abs_distance']['paired']['usage']['value'],0.)
        for source in result['sources']:
            self.assertEqual(hashlib.sha256(Path(source['path']).read_bytes()).hexdigest(),source['sha256'])
        self.assertEqual(before,{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()})

    def test_cli_missing_input_is_explicit(self):
        target=self.work/'missing-output'
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            code=cli_main(['--a',str(self.work/'absent-return'),'--a-step','400','--out',str(target)])
        self.assertEqual(code,2)
        result=json.loads((target/'callrate.json').read_text())
        self.assertEqual(result['status'],'MISSING')
        self.assertIn('absent-return/metadata/IDENTITY.json',result['error'])
        self.assertTrue(result['sources'])

    def test_summary_400_600_with_room_populations(self):
        def configure(step):
            self.pin.update(step=step,member_directory='m'+str(step),object='synthetic'+str(step))
            self.write(self.package/'READ_PLAN.json', self.plan)
            self.write(self.ret/'metadata/EXPORT_PIN.json', {**self.pin,'preparation':{}})
            entries = [{**item('room_size_estimation'), 'id':key, 'r0_split':pop}
                       for key,pop in [('s1','dev-S1'),('reserve','R0-dev')]]
            self.manifest = {'items':entries,'item_set_sha256':'synthetic-set'}
            path = self.package/'src/items/devs1_routed.json'
            self.write(path,self.manifest)
            self.write(self.package/'src/9.json',{'order':['room_size_estimation']})
            self.env['binding'].update(step=step,items_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            self.write(self.journal/'environment.json',self.env)
            records = [{**self.record,'id':i['id'],'type':'room_size_estimation'} for i in entries]
            (self.journal/'items.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
        configure(400)
        a_ret,a_package = self.ret,self.package
        self.setUp()
        configure(600)
        target = self.work/'summary-output'
        args = ['--a',str(a_ret),'--a-step','400','--a-package',str(a_package),
                '--b',str(self.ret),'--b-step','600','--b-package',str(self.package),
                '--scorer-src',str(IO.root/OUT3/'A4/src'),'--baseline-root',str(BASE),
                '--out',str(target),'--summary']
        stdout,stderr = io.StringIO(),io.StringIO()
        with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
            self.assertEqual(cli_main(args),0)
        result = json.loads((target/'callrate.json').read_text())
        self.assertEqual(stdout.getvalue(),summary(result))
        self.assertEqual(stdout.getvalue(),(target/'callrate.summary.txt').read_text())
        self.assertEqual(stderr.getvalue(),'')
        self.assertEqual(len(stdout.getvalue().splitlines()),7)
        self.assertIn('dev-S1 | 1/1 | 100.00/100.00 | 0.00 [0.00, 0.00]',stdout.getvalue())
        self.assertIn('R0-dev | 1/1 | 100.00/100.00',stdout.getvalue())
        self.assertNotIn('wording=',stdout.getvalue())
        self.assertIn('wording=',(target/'callrate.txt').read_text())
        for source in result['sources']:
            self.assertEqual(hashlib.sha256(Path(source['path']).read_bytes()).hexdigest(),source['sha256'])

    def test_summary_distance_units(self):
        target = self.work/'distance-summary'
        args = ['--a',str(self.ret),'--a-step','400','--a-package',str(self.package),
                '--b',str(self.ret),'--b-step','400','--b-package',str(self.package),
                '--scorer-src',str(IO.root/OUT3/'A4/src'),'--baseline-root',str(BASE),
                '--out',str(target),'--summary']
        stdout,stderr = io.StringIO(),io.StringIO()
        with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
            self.assertEqual(cli_main(args),0)
        self.assertEqual(stdout.getvalue(),
            'A=400 B=400; rates/scores in %, delta A-B in pp\n'
            'type | call A/B | capped A/B | usage A/B | answer A/B | score A/B | delta score [95% CI]\n'
            'object_abs_distance | 100.00/100.00 | 0.00/0.00 | 100.00/100.00 | 100.00/100.00 | 100.00/100.00 | 0.00 [0.00, 0.00]\n'
            'distance unit | call % A/B\nm | 100.00/100.00\n')
        self.assertEqual(stderr.getvalue(),'')

    def test_cli_unknown_population_retains_metrics_and_reports_missing(self):
        self.manifest['items'] = [item('room_size_estimation')]
        path = self.package/'src/items/devs1_routed.json'
        self.write(path,self.manifest)
        self.write(self.package/'src/9.json',{'order':['room_size_estimation']})
        self.env['binding']['items_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.write(self.journal/'environment.json',self.env)
        self.record['type'] = 'room_size_estimation'
        (self.journal/'items.jsonl').write_text(json.dumps(self.record)+'\n')
        target = self.work/'unknown-population'
        args = ['--a',str(self.ret),'--a-step','400','--a-package',str(self.package),
                '--b',str(self.ret),'--b-step','400','--b-package',str(self.package),
                '--scorer-src',str(IO.root/OUT3/'A4/src'),'--baseline-root',str(BASE),
                '--out',str(target),'--summary']
        stdout,stderr = io.StringIO(),io.StringIO()
        with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
            self.assertEqual(cli_main(args),2)
        result = json.loads((target/'callrate.json').read_text())
        self.assertEqual(result['missing_population_ids'],['synthetic'])
        self.assertEqual(result['room_mra']['MISSING']['a']['n'],1)
        self.assertEqual(result['room_mra']['dev-S1']['a']['n'],0)
        self.assertIsNone(result['room_mra']['dev-S1']['a']['mra_answer'])
        self.assertIn(str(BASE/'b2/src/items/room134.json'),stderr.getvalue())
        self.assertIn('MISSING | 1/1',stdout.getvalue())


if __name__=='__main__':
    unittest.main(verbosity=2)
