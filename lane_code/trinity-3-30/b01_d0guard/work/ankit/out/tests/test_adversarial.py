"""Reviewer's adversarial cases (review_an). Known answers computed by hand."""
import copy, importlib.util, json, sys, unittest, uuid
from pathlib import Path
AN = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('tnd', AN/'out/tests/test_native_vs_direct.py')
TM = importlib.util.module_from_spec(spec); spec.loader.exec_module(TM)
N = TM.N
RESULTS = {}

class Adv(unittest.TestCase):
    def setUp(self):
        self.b, self.a, self.d, self.rows = TM.fixture_case()
        self.reload()
    def reload(self):
        f = N.BUILD/'work/test_cases'/uuid.uuid4().hex; f.mkdir(parents=True)
        (f/'TASKS.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in self.rows))
        (f/'CAM.jsonl').write_text('')
        N.write(f/'FRAMES.json', dict(captures=list({r['native']: dict(native=r['native'], scene=r['scene']) for r in self.rows}.values())))
        self.meta, self.mapping = N.metadata(f/'TASKS.jsonl', f/'FRAMES.json', f/'CAM.jsonl', set(self.b['expected_keys']))
    def run_(self, subset=True):
        return N.analyze(self.b, self.a, self.d, self.meta, self.mapping, subset=subset, draws=10000)
    def note(self, name, v): RESULTS[name] = v

    def refresh_units(self):
        original, _ = N.units(self.b['expected_keys'], {a: N.index(self.b['arms'][a], a) for a in N.ARMS}, N.index(self.d, 'direct'))
        self.b['unit_scores'] = original
        self.a['report']['unit_scores'] = copy.deepcopy(original)

    def test_01_capped_native_parsed_answer(self):
        self.b['arms']['unflagged'][1]['scores']['released_answer'] = .6
        self.refresh_units()
        r = self.run_()
        self.assertEqual(r['groups']['all']['all_items']['native_pct'], 52.5)
        self.assertEqual(r['counts']['unflagged']['budget_forced_close'], 1)
        self.note('capped_parsed', 'PASS: parsed forced close keeps its recorded score')
    def test_02_dup_key_in_arm_full_file_but_outside_subset(self):
        extra = copy.deepcopy(self.b['arms']['unflagged'][0]); extra['key'] = 'devrows:zzz'
        self.b['arms']['unflagged'] += [extra, copy.deepcopy(extra)]
        try: self.run_(subset=True); self.note('dup_outside_subset', 'ACCEPTED (subset filters before dup check)')
        except N.Refusal as e: self.note('dup_outside_subset', 'REFUSED %s' % e)
    def test_03_one_arm_only_item(self):
        extra = copy.deepcopy(self.b['arms']['unflagged'][0]); extra['key'] = 'devrows:zzz'
        self.b['arms']['unflagged'].append(extra)
        with self.assertRaises(N.Refusal): self.run_(subset=False)
        self.note('one_arm_only_full', 'REFUSED (correct)')
    def test_04_all_equal_zero_width(self):
        for a in N.ARMS:
            for r in self.b['arms'][a]:
                r['geometry_refusal'] = None; r['no_answer'] = False; r['capped'] = False; r['called'] = True
                r['scores']['released_answer'] = 1
        for r in self.d: r['score'] = 1
        self.a['report']['gravity_guard_report']['dev-S1'].update(reviewed_refused=[], reviewed_refused_count=0)
        self.a['report']['per_type']['object_abs_distance'].update(call_rate_denominator_items=4, call_rate_decoded_items_pct=100, call_rate_all_items_pct=100)
        full = dict(items=4, all_items=4, geometry_refused_items=0, scores_pct=dict(unflagged=100, scripted=100), all_item_scores_pct=dict(unflagged=100, scripted=100))
        for g in ('all','metric','meter_based'): self.b['unit_scores']['object_abs_distance'][g] = copy.deepcopy(full)
        self.b['unit_scores']['object_abs_distance']['exact_units'] = {'meters': 4}
        self.b['unit_scores']['object_abs_distance']['geometry_refused_exact_units'] = {}
        self.a['report']['unit_scores'] = copy.deepcopy(self.b['unit_scores'])
        r = self.run_()['groups']['all']['all_items']['differences']['unflagged']
        self.assertEqual(r['points'], 0); self.assertEqual(r['paired95_rooms'], [0, 0])
        self.note('zero_width', 'OK %s' % r)
    def test_05_room_with_one_item(self):
        r = self.run_()['groups']['all']['all_items']; self.note('one_item_room', 'rooms=%d ok' % r['rooms'])
    def test_06_type_with_no_decoded_item(self):
        # every item of the type geometry-refused: call rate denominator 0.
        cap = self.rows[0]['native']
        for i, row in enumerate(self.rows): row['native'] = 'd1/scene0166_00'; row['room'] = 'd1/scene0166'; row['scene'] = 'scannet/scene0166_00'
        for a in N.ARMS:
            for r in self.b['arms'][a]:
                r.update(room='d1/scene0166', geometry_refusal=dict(capture='d1/scene0166_00', code=N.REFUSAL_CODE), no_answer=True, called=False, capped=False)
                r['scores']['released_answer'] = 0
        for r in self.d: r.update(native='d1/scene0166_00', room='d1/scene0166')
        g = self.a['report']['gravity_guard_report']['dev-S1']; g.update(captures=['d1/scene0166_00'], capture_count=1)
        self.a['report']['per_type']['object_abs_distance'].update(call_rate_denominator_items=0, call_rate_decoded_items_pct=None, call_rate_all_items_pct=0)
        e = dict(items=0, all_items=4, geometry_refused_items=4, scores_pct=dict(unflagged=None, scripted=None), all_item_scores_pct=dict(unflagged=0, scripted=0))
        for k in ('all','metric','meter_based'): self.b['unit_scores']['object_abs_distance'][k] = copy.deepcopy(e)
        self.b['unit_scores']['object_abs_distance']['exact_units'] = {}
        self.b['unit_scores']['object_abs_distance']['geometry_refused_exact_units'] = {'meters': 4}
        self.a['report']['unit_scores'] = copy.deepcopy(self.b['unit_scores'])
        self.reload()
        try:
            r = self.run_(); p = r['groups']['object_abs_distance']['passed_geometry']
            self.note('no_decoded_type', 'ACCEPTED all-items native=%s direct=%s; passed=%s' % (r['groups']['object_abs_distance']['all_items']['native_pct'], r['groups']['object_abs_distance']['all_items']['direct_pct'], p['items']))
        except N.Refusal as e: self.note('no_decoded_type', 'REFUSED %s' % e)
    def test_07_two_refused_captures_caveat(self):
        for a in N.ARMS:
            r = self.b['arms'][a][2]; r.update(geometry_refusal=dict(capture='d1/scene0155_02', code=N.REFUSAL_CODE), no_answer=True, called=False, capped=False); r['scores']['released_answer'] = 0
        g = self.a['report']['gravity_guard_report']['dev-S1']; g.update(reviewed_refused=['d1/scene0155_02','d1/scene0166_00'], reviewed_refused_count=2)
        self.a['report']['per_type']['object_abs_distance'].update(call_rate_denominator_items=2, call_rate_decoded_items_pct=100, call_rate_all_items_pct=50)
        self.refresh_units()
        r = self.run_()
        self.assertEqual(r['counts']['unflagged']['geometry_refused_captures'], 2)
        self.assertIn('reviewed guard refuses 2 captures (2 items)', ' '.join(r['caveats']))
        self.note('caveat_computed', 'PASS: caveat agrees with refusal census')
    def test_08_direct_producer_error(self):
        self.d[1].update(score=0.0, finish_reason='error', parse_failed=True)
        r = self.run_()
        self.assertEqual(r['counts_per_type']['object_abs_distance']['direct']['producer_errors'], 1)
        self.assertEqual(r['groups']['object_abs_distance']['no_producer_error']['items'], 3)
        self.assertEqual(r['groups']['object_abs_distance']['all_items']['items'], 4)
        self.note('direct_producer_error', 'PASS: counted and paired sensitivity excludes key')
    def test_09_conclusion_pools_types(self):
        r = self.run_()
        self.assertNotIn('conclusion', r)
        self.assertNotIn('all', r['claims'])
        self.note('conclusion_scope', 'PASS: claims are per type and type by group')
    def test_10_refusal_code_not_checked(self):
        for arm in N.ARMS:
            self.b['arms'][arm][3]['geometry_refusal']['code'] = 'some_other_error'
        with self.assertRaisesRegex(N.Refusal, 'Geometry refusal code'): self.run_()
        self.note('refusal_code', 'PASS: unexpected refusal code rejected')
    def test_11_direct_dup_outside_cohort_full(self):
        d = copy.deepcopy(self.d[0]); self.d += [d]
        try: self.run_(subset=False); self.note('direct_dup_full', 'ACCEPTED')
        except N.Refusal as e: self.note('direct_dup_full', 'REFUSED %s' % str(e)[:80])
    def test_12_missing_key_metadata(self):
        self.rows = self.rows[:3]
        try: self.reload(); self.note('missing_meta', 'ACCEPTED')
        except N.Refusal as e: self.note('missing_meta', 'REFUSED %s' % e)

if __name__ == '__main__':
    res = unittest.TextTestRunner(verbosity=1).run(unittest.TestLoader().loadTestsFromTestCase(Adv))
    for k in sorted(RESULTS): print(k, '::', RESULTS[k])
    json.dump(RESULTS, open(AN/'out/tests/ADVERSARIAL_RESULTS.json', 'w'), indent=1)
