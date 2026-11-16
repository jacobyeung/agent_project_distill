"""Synthetic known-answer and local integration tests. All outputs are PLUMBING."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
import time
import uuid
import itertools
from fractions import Fraction
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('native_vs_direct', HERE.parent / 'native_vs_direct.py')
N = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(N)
ROOT = N.ROOT
FIXTURE = ROOT / 'builds/01_c8/work/rh_full_01/runs/c80000002/native'
PILOT = N.BUILD / 'work/pilot'


def fixture_case():
    keys = ['devrows:' + x for x in ('a', 'b', 'c', 'd')]
    captures = ['d1/scene0155_00', 'd1/scene0155_01', 'd1/scene0155_02', 'd1/scene0166_00']
    rooms = ['d1/scene0155'] * 3 + ['d1/scene0166']
    task_rows, direct, arms = [], [], {a: [] for a in N.ARMS}
    for i, key in enumerate(keys):
        task_rows.append(dict(id=key.split(':')[1], native=captures[i], room=rooms[i],
            scene='scannet/' + captures[i].split('/')[1], dataset='scannet',
            question_type='object_abs_distance', stratum='primary', scorer='official_vsi_mra',
            question='How far in meters?', ground_truth='1', released_answer='1', answer='2'))
        direct.append(dict(key=key, id=task_rows[-1]['id'], question_type='object_abs_distance',
            stratum='primary', native=captures[i], room=rooms[i], budget=2048,
            score=[0, 1, .5, 1][i], hit_token_cap=False, parse_failed=False, forced_close=False, finish_reason='stop', derivation_error=False, arm='B2048', status='complete', ground_truth='1'))
        for a in N.ARMS:
            val = ([1, 0, .5, 0] if a == 'unflagged' else [.5, 1, 1, 0])[i]
            arms[a].append(dict(key=key, arm=a, question_type='object_abs_distance', stratum='primary',
                room=rooms[i], scores=dict(released_answer=val, answer=0), capped=a == 'unflagged' and i == 1,
                no_answer=i == 3, called=i != 3, call_errors=0, version_errors=0, budget_truncated_calls=0,
                question_unit=dict(unit='meters', metric=True, meter_based=True),
                geometry_refusal=dict(capture=captures[i], code=N.REFUSAL_CODE) if i == 3 else None,
                decode=dict(finish='geometry_refusal' if i == 3 else 'stop')))
    whole = dict(items=3, all_items=4, geometry_refused_items=1,
                 scores_pct=dict(unflagged=50, scripted=250/3),
                 all_item_scores_pct=dict(unflagged=37.5, scripted=62.5))
    empty = dict(items=0, all_items=0, geometry_refused_items=0,
                 scores_pct=dict(unflagged=None, scripted=None),
                 all_item_scores_pct=dict(unflagged=None, scripted=None))
    unit_scores = {}
    for typ in N.TYPES[:2]:
        unit_scores[typ] = {g: copy.deepcopy(whole if typ == N.TYPES[0] and g in ('all','metric','meter_based') else empty)
                           for g in ('all','metric','nonmetric','meter_based','other_units','unknown')}
        unit_scores[typ]['exact_units'] = {'meters':3} if typ == N.TYPES[0] else {}
        unit_scores[typ]['geometry_refused_exact_units'] = {'meters':1} if typ == N.TYPES[0] else {}
    bundle = dict(schema='legs1-r1-nomdg-v1', expected_keys=keys, arms=arms, unit_scores=unit_scores, synthetic=True)
    admission = dict(report=dict(per_type={'object_abs_distance':dict(items=4, call_rate_denominator_items=3,
        call_rate_decoded_items_pct=100, call_rate_all_items_pct=75)},
        gravity_guard_report={'dev-S1':dict(captures=captures, capture_count=4,
            reviewed_refused=[captures[-1]], reviewed_refused_count=1)},
        program_refusals=dict(total=0), unit_scores=copy.deepcopy(unit_scores)))
    return bundle, admission, direct, task_rows


class SyntheticTests(unittest.TestCase):
    def setUp(self):
        self.b, self.a, self.d, rows = fixture_case()
        self.folder = N.BUILD / 'work/test_cases' / uuid.uuid4().hex
        self.folder.mkdir(parents=True)
        self.tasks = self.folder / 'TASKS.jsonl'
        self.tasks.write_text(''.join(json.dumps(r)+'\n' for r in rows))
        self.camera = self.folder / 'CAMERA_TASKS.jsonl'
        self.camera.write_text('')
        self.frames = self.folder / 'FRAMES.json'
        N.write(self.frames, dict(captures=[dict(native=r['native'], scene=r['scene']) for r in rows]))
        self.meta, self.mapping = N.metadata(self.tasks, self.frames, self.camera, set(self.b['expected_keys']))

    def analyze(self):
        return N.analyze(self.b, self.a, self.d, self.meta, self.mapping, subset=True, draws=10000)

    def test_hand_computed_all_and_sensitivity(self):
        result = self.analyze()
        self.assertTrue(result['mode'].startswith('PLUMBING'))
        self.assertNotIn('conclusion', result)
        all_items = result['groups']['all']['all_items']
        passed = result['groups']['all']['passed_geometry']
        self.assertEqual((all_items['items'], all_items['rooms']), (4, 2))
        self.assertEqual((all_items['native_pct'],all_items['scripted_pct'],all_items['direct_pct']), (37.5,62.5,62.5))
        self.assertEqual(all_items['differences']['unflagged']['points'], -25)
        self.assertEqual(all_items['differences']['scripted']['points'], 0)
        self.assertEqual(all_items['differences']['unflagged']['paired95_rooms'], [-100,0])
        self.assertAlmostEqual(all_items['differences']['scripted']['paired95_rooms'][0],-100)
        self.assertAlmostEqual(all_items['differences']['scripted']['paired95_rooms'][1],100/3)
        self.assertEqual((passed['items'],passed['rooms']), (3,1))
        self.assertEqual(passed['native_pct'], 50)
        self.assertEqual(passed['direct_pct'], 50)
        self.assertAlmostEqual(passed['scripted_pct'], 250/3)
        self.assertEqual(passed['differences']['unflagged']['paired95_rooms'], [0,0])
        for value in passed['differences']['scripted']['paired95_rooms']:
            self.assertAlmostEqual(value, 100/3)

    def test_refused_capture_and_capped_item_retained(self):
        result = self.analyze()
        for a in N.ARMS:
            self.assertEqual(result['counts'][a]['geometry_refused_items'], 1)
            self.assertEqual(result['counts'][a]['no_answer'], 0)
            self.assertEqual(result['counts'][a]['no_answer_including_geometry'], 1)
        self.assertEqual(result['counts']['unflagged']['native_budget_fires'], 1)
        self.assertEqual(result['counts']['direct']['items'], 4)

    def test_rescans_form_one_cluster(self):
        rooms = [self.mapping['captures']['d1/scene0155_'+x]['room'] for x in ('00','01','02')]
        self.assertEqual(set(rooms), {'d1/scene0155'})
        self.assertEqual(self.mapping['summary']['d1'], dict(captures=4,rooms=2))

    def test_bootstrap_unequal_room_sizes(self):
        rows = [('a',1,1,0),('b',0,0,0),('b',0,0,0),('b',0,0,0)]
        ci = N.bootstrap(rows)
        self.assertEqual(ci['unflagged'], [0,100])
        self.assertEqual(ci['scripted'], ci['unflagged'])
        self.assertEqual(N.bootstrap(rows), ci)

    def test_minimum_draws(self):
        with self.assertRaisesRegex(N.Refusal, '10000'):
            N.bootstrap([('r',1,0,0)], 9999)

    def test_missing_keys_in_each_arm_and_direct(self):
        for which in (*N.ARMS, 'direct'):
            with self.subTest(which=which):
                saved_b, saved_d = copy.deepcopy(self.b), copy.deepcopy(self.d)
                if which == 'direct':
                    self.d = self.d[1:]
                else:
                    self.b['arms'][which] = self.b['arms'][which][1:]
                with self.assertRaises(N.Refusal): self.analyze()
                self.b, self.d = saved_b, saved_d

    def test_duplicate_keys_in_each_arm_direct_expected(self):
        for which in (*N.ARMS,'direct','expected'):
            with self.subTest(which=which):
                saved_b, saved_d = copy.deepcopy(self.b), copy.deepcopy(self.d)
                rows = self.d if which == 'direct' else self.b['expected_keys'] if which == 'expected' else self.b['arms'][which]
                rows.append(copy.deepcopy(rows[0]))
                with self.assertRaisesRegex(N.Refusal, 'Duplicate'): self.analyze()
                self.b, self.d = saved_b, saved_d

    def test_direct_room_disagreement(self):
        self.d[0]['room'] = 'd1/scene9999'
        with self.assertRaisesRegex(N.Refusal, 'room-map'): self.analyze()

    def test_native_room_disagreement(self):
        self.b['arms']['scripted'][0]['room'] = 'd1/scene9999'
        with self.assertRaisesRegex(N.Refusal, 'room-map'): self.analyze()

    def test_metadata_rescan_disagreement(self):
        rows = N.jsonl(self.tasks)
        rows[0]['room'] = 'd1/scene0155_00'
        self.tasks.write_text(''.join(json.dumps(r)+'\n' for r in rows))
        with self.assertRaisesRegex(N.Refusal, 'Rescan room'):
            N.metadata(self.tasks, self.frames, self.camera, set(self.b['expected_keys']))

    def test_venue_cluster(self):
        rows = N.jsonl(self.tasks)[:2]
        for i, row in enumerate(rows):
            row.update(native='d3/'+str(41069053+i), scene='arkitscenes/'+str(41069053+i),
                       dataset='arkitscenes', room='d3/venue381619')
        self.tasks.write_text(''.join(json.dumps(r)+'\n' for r in rows))
        N.write(self.frames,dict(captures=[dict(native=r['native'],scene=r['scene']) for r in rows]))
        _, mapping = N.metadata(self.tasks,self.frames,self.camera,set(self.b['expected_keys'][:2]))
        self.assertEqual(mapping['summary']['d3'],dict(captures=2, rooms=1))

    def test_label_pairing_disagreement(self):
        self.meta[self.b['expected_keys'][0]]['ground_truth'] = '9'
        with self.assertRaisesRegex(N.Refusal, 'Label pairing'): self.analyze()

    def test_call_rate_disagreement(self):
        self.a['report']['per_type']['object_abs_distance']['call_rate_decoded_items_pct'] = 75
        with self.assertRaisesRegex(N.Refusal, 'Admission call rate'): self.analyze()

    def test_unit_scores_disagreement(self):
        self.b['unit_scores']['object_abs_distance']['other_units']['all_items'] = 1
        with self.assertRaisesRegex(N.Refusal, 'unit_scores'): self.analyze()

    def test_unit_groups_direct_and_both_arms(self):
        result = self.analyze()
        grouped = result['unit_scores_with_direct']['object_abs_distance']
        for row in (grouped['groups']['metric'], grouped['exact_units']['meters']):
            self.assertEqual(row['all_items'],4)
            self.assertEqual(row['items'],3)
            self.assertEqual(row['all_item_scores_pct'],dict(unflagged=37.5,scripted=62.5,direct=62.5))
            self.assertEqual(row['scores_pct']['direct'],50)
            self.assertAlmostEqual(row['scores_pct']['scripted'],250/3)

    def test_unit_parser_centimeters_other_metric(self):
        unit = N.question_unit('What is the distance in centimeters?')
        self.assertEqual(unit, dict(unit='centimeters',metric=True,meter_based=False))
        self.assertEqual(N.question_unit('Area in square feet?'), dict(unit='square feet',metric=False,meter_based=False))

    def test_geometry_flag_disagreement(self):
        self.b['arms']['scripted'][-1]['geometry_refusal'] = None
        with self.assertRaisesRegex(N.Refusal, 'Geometry refusal'): self.analyze()

    def test_geometry_score_nonzero(self):
        self.b['arms']['unflagged'][-1]['scores']['released_answer'] = 1
        with self.assertRaisesRegex(N.Refusal, 'Geometry refusal'): self.analyze()

    def refresh_units(self):
        arms = {a: N.index(self.b['arms'][a], a) for a in N.ARMS}
        original, _ = N.units(self.b['expected_keys'], arms, N.index(self.d, 'direct'))
        self.b['unit_scores'] = original
        self.a['report']['unit_scores'] = copy.deepcopy(original)

    def test_positive_capped_score_retained(self):
        self.b['arms']['unflagged'][1]['scores']['released_answer'] = .6
        self.refresh_units()
        result = self.analyze()
        self.assertEqual(result['groups']['object_abs_distance']['all_items']['native_pct'], 52.5)
        self.assertEqual(result['counts']['unflagged']['budget_forced_close'], 1)
        self.assertEqual(result['groups']['object_abs_distance']['capped_zeroed']['native_pct'], 37.5)

    def test_direct_parse_failure_retained(self):
        self.d[0]['parse_failed'] = True
        self.d[0]['hit_token_cap'] = True
        result = self.analyze()
        self.assertEqual(result['counts']['direct']['direct_hit_token_cap'], 1)
        self.assertEqual(result['counts']['direct']['parse_failed'], 1)
        self.assertEqual(result['counts']['direct']['no_final_answer'], 1)

    def test_program_refusal_report_disagreement(self):
        self.a['report']['program_refusals']['total'] = 1
        with self.assertRaisesRegex(N.Refusal, 'program refusals'): self.analyze()

    def test_full_denominator_guard(self):
        with self.assertRaisesRegex(N.Refusal, 'Full cohort type'):
            N.analyze(self.b,self.a,self.d,self.meta,self.mapping)

    def test_cli_subset_end_to_end(self):
        for name, value in (('BUNDLE.json',self.b),('ADMISSION.json',self.a),('DIRECT.json',self.d),('KEYS.json',self.b['expected_keys'])):
            N.write(self.folder/name,value)
        (self.folder/'RAW.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in self.d))
        output=self.folder/'output'
        command=[sys.executable,'-I','-s','-B',str(HERE.parent/'native_vs_direct.py'),
            '--bundle',str(self.folder/'BUNDLE.json'),'--admission',str(self.folder/'ADMISSION.json'),
            '--direct',str(self.folder/'DIRECT.json'),'--direct-raw',str(self.folder/'RAW.jsonl'),'--tasks',str(self.tasks),'--frames',str(self.frames),
            '--camera-tasks',str(self.camera),'--subset',str(self.folder/'KEYS.json'),'--output',str(output)]
        completed=subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(completed.returncode,0,completed.stderr)
        result=N.read(output/'NATIVE_VS_DIRECT.json')
        self.assertEqual(result['groups']['all']['all_items']['native_pct'],37.5)
        self.assertIn(result['caveats'][0],(output/'NATIVE_VS_DIRECT.md').read_text())
        self.assertTrue(N.read(output/'ROOM_MAP.json')['mode'].startswith('PLUMBING'))

    def test_exhaustive_five_unequal_rooms_endpoints(self):
        # Every ordered room draw appears equally often. Fractions supply an
        # independent item-weighted reference, without Monte Carlo tolerances.
        sizes = (1, 2, 3, 5, 8)
        native = (Fraction(1), Fraction(0), Fraction(1, 3), Fraction(4, 5), Fraction(1, 4))
        scripted = (Fraction(0), Fraction(1, 2), Fraction(1), Fraction(1, 5), Fraction(3, 4))
        direct = (Fraction(1, 2), Fraction(1), Fraction(0), Fraction(2, 5), Fraction(1, 8))
        rows = [(str(i), float(native[i]), float(scripted[i]), float(direct[i]))
                for i, size in enumerate(sizes) for _ in range(size)]
        samples = list(itertools.product(range(5), repeat=5)) * 4
        expected = {}
        for arm, scores in zip(N.ARMS, (native, scripted)):
            values = sorted(Fraction(100) * sum(sizes[i] * (scores[i] - direct[i]) for i in sample)
                            / sum(sizes[i] for i in sample) for sample in samples)
            endpoints = []
            for probability in (Fraction(1, 40), Fraction(39, 40)):
                position = (len(values) - 1) * probability
                lo = int(position)
                endpoints.append(float(values[lo] + (values[lo+1] - values[lo]) * (position-lo)))
            expected[arm] = endpoints
        class ExhaustiveRandom:
            def __init__(self, seed): self.samples = itertools.cycle(samples)
            def choices(self, clusters, k):
                return [clusters[i] for i in next(self.samples)]
        with patch.object(N.random, 'Random', ExhaustiveRandom):
            actual = N.bootstrap(rows, draws=len(samples))
        for arm in N.ARMS:
            for got, want in zip(actual[arm], expected[arm]):
                self.assertAlmostEqual(got, want, places=10)

    def test_state_definitions(self):
        for flags in ({'no_answer': True}, {'parse_failed': True}, {'strict_no_answer': True},
                      {'decode': {'finish': 'call_limit'}}, {'decode': {'strict_no_answer': True}},
                      {'decode': {'text': 'unclosed reasoning'}}):
            with self.subTest(flags=flags):
                row = dict(capped=True, **flags)
                self.assertEqual(N.answer_states(row), dict(budget_forced_close=False, no_final_answer=True))
        self.assertEqual(N.answer_states(dict(capped=True, no_answer=False)),
                         dict(budget_forced_close=True, no_final_answer=False))
        for row in (dict(forced_close=True, parse_failed=True), dict(hit_token_cap=True),
                    dict(stopped_unclosed=True)):
            self.assertTrue(N.answer_states(row, True)['no_final_answer'])
        self.assertTrue(N.answer_states(dict(forced_close=True, raw_generation='</think>1'), True)['budget_forced_close'])

    def test_no_final_nonzero_refuses_each_arm(self):
        for arm in N.ARMS:
            with self.subTest(arm=arm):
                row = self.b['arms'][arm][0]
                row['no_answer'] = True
                with self.assertRaisesRegex(N.Refusal, 'No-final-answer'):
                    self.analyze()
                row['no_answer'] = False
        self.d[1]['parse_failed'] = True
        with self.assertRaisesRegex(N.Refusal, 'No-final-answer'):
            self.analyze()

    def test_direct_forced_close_primary_and_sensitivity(self):
        self.d[1]['forced_close'] = True
        result = self.analyze()
        c = result['counts']['direct']
        self.assertEqual((c['direct_forced_close'], c['direct_hit_token_cap'], c['budget_forced_close']), (1, 0, 1))
        self.assertEqual(result['groups']['all']['all_items']['direct_pct'], 62.5)
        self.assertEqual(result['groups']['all']['capped_zeroed']['direct_pct'], 37.5)

    def test_capped_sign_change_flagged_per_type_and_group(self):
        self.d[1]['forced_close'] = True
        self.d[3]['forced_close'] = True
        result = self.analyze()
        for group in ('object_abs_distance', 'd1/object_abs_distance'):
            self.assertEqual(result['claims'][group]['unflagged']['claim'], 'unresolved under the capped rule')
        result['sources'] = {}
        text = N.markdown(result, self.folder)
        self.assertIn('unresolved under the capped rule', '\n'.join(text.splitlines()[:12]))

    def test_producer_errors_drop_keys_from_all_arms(self):
        self.d[0].update(finish_reason='error', derivation_error=True)
        self.b['arms']['unflagged'][1]['decode']['finish'] = 'error'
        result = self.analyze()
        self.assertEqual(result['counts']['direct']['producer_errors'], 1)
        self.assertEqual(result['counts']['unflagged']['producer_errors'], 1)
        self.assertEqual(result['counts']['scripted']['producer_errors'], 0)
        self.assertEqual(result['counts_per_type']['room_size_estimation']['direct']['producer_errors'], 0)
        row = result['groups']['object_abs_distance']['no_producer_error']
        self.assertEqual(row['items'], 2)
        self.assertEqual((row['native_pct'], row['scripted_pct'], row['direct_pct']), (25, 50, 75))
        self.assertEqual(result['groups']['object_abs_distance']['all_items']['items'], 4)

    def test_producer_error_nonzero_refuses(self):
        self.d[1]['finish_reason'] = 'error'
        with self.assertRaisesRegex(N.Refusal, 'producer-error'): self.analyze()

    def test_geometry_code_refuses(self):
        self.b['arms']['unflagged'][-1]['geometry_refusal']['code'] = 'other'
        with self.assertRaisesRegex(N.Refusal, 'Geometry refusal code'): self.analyze()

    def test_raw_shared_fields_and_missing(self):
        raw = copy.deepcopy(self.d)
        merged = N.merge_direct_raw(self.d, raw, self.b['expected_keys'])
        self.assertEqual(merged, self.d)
        for field, value in (('score', .2), ('room', 'wrong'), ('finish_reason', 'error'),
                             ('native', 'd2/wrong'), ('budget', 1024), ('parse_failed', True)):
            other = copy.deepcopy(raw); other[0][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(N.Refusal, 'Raw/compact'):
                N.merge_direct_raw(self.d, other, self.b['expected_keys'])
        with self.assertRaisesRegex(N.Refusal, 'lacks expected'):
            N.merge_direct_raw(self.d, raw[1:], self.b['expected_keys'])
        with self.assertRaisesRegex(N.Refusal, 'Duplicate'):
            N.merge_direct_raw(self.d, raw + [raw[0]], self.b['expected_keys'])

    def test_export_artifact_validation(self):
        arms = {a: N.index(self.b['arms'][a], a) for a in N.ARMS}
        for rows in arms.values():
            for row in rows.values(): row['checkpoint_sha256'] = N.EXPECTED_ARTIFACT
        self.assertEqual(N.artifact_check(self.b, arms, None)['status'], 'PARTIAL')
        self.assertEqual(N.artifact_check(self.b, arms, N.EXPECTED_ARTIFACT)['status'], 'PASS')
        with self.assertRaisesRegex(N.Refusal, 'Direct export'):
            N.artifact_check(self.b, arms, 'bad')
        next(iter(arms['scripted'].values()))['checkpoint_sha256'] = 'bad'
        with self.assertRaisesRegex(N.Refusal, 'Native export'):
            N.artifact_check(self.b, arms, None)

    def test_metre_only_intervals_and_reporting(self):
        result = self.analyze()
        for group in ('object_abs_distance', 'd1/object_abs_distance'):
            self.assertEqual(result['groups'][group]['metre_only'], result['groups'][group]['all_items'])
        self.assertEqual(result['metre_only_check']['room_size_estimation'], 0)
        result['sources'] = {}
        text = N.markdown(result, self.folder)
        self.assertLess(text.index('| object_abs_distance | all_items'), text.index('## Descriptive pooled'))
        self.assertGreater(text.index('| all | all_items'), text.index('## Descriptive pooled'))
        self.assertIn('sealed guard 11 (pilot-era replay; supplied context)', text)
        self.assertIn('reviewed guard refuses 1 captures (1 items)', text)
        self.assertIn('parent direct mean: no sourced record', text)
        routed = [line for line in text.splitlines() if line.startswith('| object_abs_distance | all_items')][0]
        for caveat in result['caveats']: self.assertIn(caveat, routed)

    def test_sealed_guard_uses_admission_count(self):
        self.a['report']['gravity_guard_report']['dev-S1']['sealed_refused_count'] = 3
        self.assertIn('sealed guard 3 (recorded in IN_JOB_ADMISSION)', ' '.join(self.analyze()['caveats']))


class IntegrationTests(unittest.TestCase):
    def test_full_fixture_cli(self):
        started = time.monotonic()
        output=HERE.parent/'fixture'
        completed=subprocess.run([sys.executable,'-I','-s','-B',str(HERE.parent/'native_vs_direct.py'),
            '--bundle',str(FIXTURE/'R1.json'),'--admission',str(FIXTURE/'paired/IN_JOB_ADMISSION.json'),
            '--plumbing','--output',str(output)], capture_output=True,text=True)
        self.assertEqual(completed.returncode,0,completed.stderr)
        result=N.read(output/'NATIVE_VS_DIRECT.json')
        elapsed = time.monotonic() - started
        N.write(output/'RUNTIME.json', dict(seconds=elapsed, limit_seconds=600, report=str(output/'NATIVE_VS_DIRECT.json'), draws=result['method']['draws']))
        self.assertLess(elapsed, 600)
        self.assertEqual(result['method']['draws'],50000)
        self.assertEqual(result['metre_only_check'], dict(object_abs_distance=43, room_size_estimation=29))
        self.assertEqual(result['counts']['direct']['producer_errors'],20)
        self.assertEqual({t: result['counts_per_type'][t]['direct']['producer_errors'] for t in N.TYPES}, dict(zip(N.TYPES, (0,1,14,5,0))))
        self.assertEqual(result['raw_direct_check']['keys'],636)
        self.assertEqual(result['items'],636)
        self.assertTrue(result['mode'].startswith('PLUMBING'))
        self.assertTrue(result['unit_check']['matches_brief_full_counts'])
        self.assertEqual(result['label_pairing']['counts'],dict(answer=450,released_answer=186))
        self.assertEqual(result['counts']['unflagged']['geometry_refused_items'],2)
        self.assertEqual(result['counts']['scripted']['geometry_refused_items'],2)
        self.assertEqual(result['groups']['all']['passed_geometry']['items'],634)
        mapping=N.read(output/'ROOM_MAP.json')['captures']
        self.assertEqual(len(mapping),84)
        self.assertEqual({mapping['d1/scene0155_'+i]['room'] for i in ('00','01','02')},{'d1/scene0155'})
        self.assertEqual(mapping['d3/41069053']['room'], mapping['d3/41069054']['room'])

    def test_real_pilot_cli(self):
        self.assertTrue((PILOT/'PILOT_CHECK.json').exists(),'Verified real pilot test has not run')
        check=N.read(PILOT/'PILOT_CHECK.json')
        self.assertEqual(check['status'],'PASS')
        self.assertTrue(check['archive_sha256'].startswith('6086a12e'))
        output=HERE.parent/'pilot'
        completed=subprocess.run([sys.executable,'-I','-s','-B',str(HERE.parent/'native_vs_direct.py'),
            '--bundle',str(PILOT/'R1.json'),'--admission',str(PILOT/'IN_JOB_ADMISSION.json'),
            '--subset',str(PILOT/'KEYS.json'),'--output',str(output)],capture_output=True,text=True)
        self.assertEqual(completed.returncode,0,completed.stderr)
        result=N.read(output/'NATIVE_VS_DIRECT.json')
        self.assertEqual(result['items'],10)
        self.assertTrue(result['mode'].startswith('PLUMBING'))
        self.assertNotIn('conclusion', result)
        self.assertEqual(result['counts']['unflagged']['native_capped_recorded'],check['expected_capped'])
        self.assertEqual(result['counts']['unflagged']['no_answer'],check['expected_no_answer'])
        self.assertEqual(result['counts']['unflagged']['call_errors'],check['expected_call_errors'])
        self.assertEqual(result['counts']['unflagged']['program_refusals'],check['expected_program_refusals'])
        self.assertEqual(result['counts']['unflagged']['geometry_refused_items'],check['expected_geometry_refusals'])


if __name__=='__main__':
    unittest.main()
