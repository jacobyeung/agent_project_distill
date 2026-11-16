"""Identity refusals, exact preservation, sourced means, and a known-answer CLI toy."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('parent_adapter', HERE.parent / 'parent_adapter.py')
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)


def object_bytes(path):
    text = path.read_bytes().decode()
    return {row['key']: text[start:end].encode() for start, end, row in A.array_spans(text)}


def raw_lines(path):
    return {json.loads(line)['key']: line for line in path.read_bytes().splitlines(keepends=True) if line.strip()}


class ParentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        full = A.read(A.PATHS['bundle'])
        # Identity tests need no embedded images, token arrays or tool traces.
        cls.bundle = dict(expected_keys=full['expected_keys'], arms={})
        fields = ('key', 'question_type', 'room', 'stratum', 'perception', 'geometry_refusal', 'no_answer')
        for arm, rows in full['arms'].items():
            cls.bundle['arms'][arm] = []
            for row in rows:
                small = {k: row[k] for k in fields if k in row}
                if row.get('decode'):
                    small['decode'] = {k: row['decode'][k] for k in ('decode_budget',) if k in row['decode']}
                cls.bundle['arms'][arm].append(small)
        cls.parent, cls.kit, cls.config = (A.read(A.PATHS[k]) for k in ('parent','kit','config'))
        cls.tasks, cls.frames = A.lines(A.PATHS['tasks']), A.read(A.PATHS['frames'])
        cls.compact, cls.raw = A.read(A.PATHS['compact']), A.lines(A.PATHS['raw_main'])
        cls.strata = A.lines(A.PATHS['strata'])
        cls.identity = A.read(A.OUT / 'IDENTITY_CHECKS.json')
        cls.selected = {r['key'] for r in cls.identity['items']}
        cls.first = next(iter(sorted(cls.selected)))

    def case(self):
        return [self.bundle, self.parent, self.kit, self.tasks, self.frames,
                self.config, self.compact, self.raw, self.strata]

    def mutate(self, slot):
        args = self.case()
        args[slot] = copy.deepcopy(args[slot])
        return args

    def test_identity_all_paired_items(self):
        result = A.validate(*self.case())
        self.assertEqual(result['paired_counts'], {'object_abs_distance': 150, 'room_size_estimation': 36})
        self.assertEqual(len(result['unpaired_camera_keys']), 450)
        self.assertEqual(result['decode_checks'], {'decoded_budget_checked': 184, 'geometry_refused_without_decode': 2})

    def test_parent_means_match_kit_and_script(self):
        compact = A.read(A.OUT / 'DIRECT_PARENT_COMPACT.json')
        raw = A.lines(A.OUT / 'items_parent_main.jsonl')
        report = A.read(A.RESULT / 'NATIVE_VS_DIRECT.json')
        expected = {'object_abs_distance': 0.38866666666666666, 'room_size_estimation': 0.5555555555555556}
        for typ in A.TYPES:
            for rows in (compact, raw):
                values = [r['score'] for r in rows if r['key'] in self.selected and r['question_type'] == typ]
                mean = sum(values) / len(values)
                self.assertAlmostEqual(mean, expected[typ], places=12)
                self.assertAlmostEqual(mean, self.kit['benchmarks']['devrows']['per_type'][typ]['score'], places=12)
                for selection in ('all_items','capped_zeroed'):
                    self.assertAlmostEqual(100 * mean, report['groups'][typ][selection]['direct_pct'], places=10)

    def test_uncovered_compact_objects_byte_identical(self):
        original = object_bytes(A.PATHS['compact'])
        adapted = object_bytes(A.OUT / 'DIRECT_PARENT_COMPACT.json')
        self.assertEqual(set(original), set(adapted))
        uncovered = set(original) - self.selected
        self.assertEqual(len(uncovered), 2089)
        for key in uncovered:
            self.assertEqual(original[key], adapted[key], key)
        def masked(path):
            text = path.read_bytes().decode()
            parts, cursor = [], 0
            for start, end, row in A.array_spans(text):
                if row['key'] in self.selected:
                    parts.extend((text[cursor:start], '<paired-row>'))
                    cursor = end
            return ''.join(parts) + text[cursor:]
        self.assertEqual(masked(A.PATHS['compact']), masked(A.OUT / 'DIRECT_PARENT_COMPACT.json'))

    def test_uncovered_raw_lines_byte_identical(self):
        original, adapted = raw_lines(A.PATHS['raw_main']), raw_lines(A.OUT / 'items_parent_main.jsonl')
        self.assertEqual(set(original), set(adapted))
        for key in set(original) - self.selected:
            self.assertEqual(original[key], adapted[key], key)

    def test_camera_bytes_and_cli_path_unchanged(self):
        receipt = A.read(A.OUT / 'CLI_RECEIPT.json')
        sources = A.read(A.OUT / 'ADAPTED_INPUTS.json')
        self.assertEqual(sources['direct_raw_camera']['path'], str(A.PATHS['raw_camera']))
        self.assertEqual(sources['direct_raw_camera']['sha256'], A.sha(A.PATHS['raw_camera']))
        self.assertIn(str(A.PATHS['raw_camera']), receipt['command'])
        self.assertFalse(set(raw_lines(A.PATHS['raw_camera'])) & self.selected)

    def test_selected_raw_has_no_student_generation_and_shared_fields_match(self):
        compact = A.index(A.read(A.OUT / 'DIRECT_PARENT_COMPACT.json'))
        raw = A.index(A.lines(A.OUT / 'items_parent_main.jsonl'))
        parent = A.index(self.parent['rows'])
        for key in self.selected:
            self.assertFalse({'raw_generation','token_ids','prompt_text','extracted_answer','response_text','raw_answer','scoring_text'} & set(raw[key]))
            for field in compact[key].keys() & raw[key].keys():
                self.assertEqual(compact[key][field], raw[key][field], key + '/' + field)
            self.assertEqual(raw[key]['score'], parent[key]['scores']['released_answer'])
            self.assertEqual(raw[key]['binding'], self.parent['request_binding'])
            self.assertFalse(raw[key]['forced_close'])
            self.assertFalse(raw[key]['producer_error'])
            self.assertEqual(raw[key]['finish_reason_evidence'], 'normalized from flags; original unavailable')

    def test_refuse_key_mismatch(self):
        args = self.mutate(1)
        A.index(args[1]['rows'])[self.first]['key'] += '_wrong'
        with self.assertRaisesRegex(A.Refusal, 'key mismatch'):
            A.validate(*args)

    def test_refuse_room_mismatch(self):
        args = self.mutate(1)
        A.index(args[1]['rows'])[self.first]['room'] = 'wrong-room'
        with self.assertRaisesRegex(A.Refusal, 'room mismatch'):
            A.validate(*args)

    def test_refuse_stratum_mismatch(self):
        args = self.mutate(1)
        A.index(args[1]['rows'])[self.first]['stratum'] = 'wrong-stratum'
        with self.assertRaisesRegex(A.Refusal, 'stratum mismatch'):
            A.validate(*args)

    def test_refuse_frame_sha_mismatch(self):
        args = self.mutate(0)
        A.index(args[0]['arms']['unflagged'])[self.first]['perception']['frame_sha256'][0] = 'f' * 64
        with self.assertRaisesRegex(A.Refusal, 'frame-sha mismatch'):
            A.validate(*args)

    def test_refuse_nonzero_derivation_counts(self):
        for field in ('forced_close','stopped_unclosed','derivation_error'):
            with self.subTest(field=field):
                args = self.mutate(2)
                args[2]['derivation']['per_type'][A.TYPES[0]][field] = 1
                with self.assertRaisesRegex(A.Refusal, 'nonzero derivation count'):
                    A.validate(*args)

    def test_refuse_changed_script_sha(self):
        path = HERE / 'changed_script_fixture.py'
        path.write_bytes(A.SCRIPT.read_bytes() + b'\n# synthetic changed digest\n')
        with self.assertRaisesRegex(A.Refusal, 'script sha mismatch'):
            A.verify_script(path)
        self.assertEqual(A.verify_script(), A.SCRIPT_SHA)

    def test_refuse_question_mismatch(self):
        args = self.mutate(7)
        A.index(args[7])[self.first]['question'] = 'Different question'
        with self.assertRaisesRegex(A.Refusal, 'TASKS question mismatch'):
            A.validate(*args)

    def test_refuse_anchor_mismatch(self):
        args = self.mutate(2)
        args[2]['anchor_indices'][self.first][0] += 1
        with self.assertRaisesRegex(A.Refusal, 'anchor mismatch'):
            A.validate(*args)

    def test_refuse_decode_budget_mismatch(self):
        args = self.mutate(0)
        row = next(r for r in args[0]['arms']['unflagged'] if r['key'] in self.selected and not r.get('geometry_refusal'))
        row['decode']['decode_budget']['thinking_tokens'] += 1
        with self.assertRaisesRegex(A.Refusal, 'decode budget mismatch'):
            A.validate(*args)

    def test_refuse_native_duplicate_layout_mismatch(self):
        args = self.mutate(5)
        args[5]['full_projection']['parity']['P3']['trainer_audit']['original_timestamps_seconds'][1] = -1
        with self.assertRaisesRegex(A.Refusal, 'duplicate layout mismatch'):
            A.validate(*args)


def toy_case():
    typ = A.TYPES[0]
    tasks, frames, parent, direct = [], [], [], []
    arms = {'unflagged': [], 'scripted': []}
    values = {'unflagged': [1, .5, 0], 'scripted': [.5, .25, .75], 'direct': [0, .25, .25]}
    anchors = list(range(32))
    for i in range(3):
        room = f'd1/scene{i+1:04d}'
        capture = room + '_00'
        key = 'devrows:toy' + str(i)
        task = dict(id='toy'+str(i), question_type=typ, stratum='primary', room=room, native=capture,
                    dataset='scannet', scene='scannet/'+capture.split('/')[1], question='How far in meters?',
                    options=[], answer='2', released_answer='1', ground_truth='1', scorer='official_vsi_mra',
                    source_frame_indices=anchors, fps=30)
        tasks.append(task)
        frame = dict(native=capture, scene=task['scene'], anchor_indices=anchors, fps=30,
                     timestamps=[x/30 for x in anchors], frames=[dict(index=x, sha256=f'{i*32+x:064x}') for x in anchors])
        frames.append(frame)
        parent.append(dict(key=key, question_type=typ, stratum='primary', room=room,
                           scores=dict(answer=.9, released_answer=values['direct'][i]),
                           capped=False, unparsed=False, unanswered=False))
        dr = dict(task, key=key, family='main', score=.9, hit_token_cap=False, parse_failed=False,
                  budget=2048, finish_reason='stop', forced_close=False, derivation_error=False,
                  arm='B2048', status='complete', raw_generation='STUDENT TEXT MUST NOT SURVIVE')
        direct.append(dr)
        for arm in arms:
            arms[arm].append(dict(key=key, arm=arm, question_type=typ, stratum='primary', room=room,
                scores=dict(released_answer=values[arm][i], answer=.9), capped=arm=='unflagged' and i==0,
                no_answer=False, called=True, call_errors=0, version_errors=0, budget_truncated_calls=0,
                question_unit=dict(unit='meters', metric=True, meter_based=True),
                perception=dict(frame_indices=anchors, frame_sha256=[f['sha256'] for f in frame['frames']]),
                decode=dict(finish='stop', text='</think>\n1', decode_budget=dict(thinking_tokens=2048, answer_tokens=64,
                    fired=arm=='unflagged' and i==0))))
    whole = dict(items=3, all_items=3, geometry_refused_items=0,
                 scores_pct=dict(unflagged=50, scripted=50), all_item_scores_pct=dict(unflagged=50, scripted=50))
    empty = dict(items=0, all_items=0, geometry_refused_items=0,
                 scores_pct=dict(unflagged=None, scripted=None), all_item_scores_pct=dict(unflagged=None, scripted=None))
    units = {}
    for t in A.TYPES:
        units[t] = {g: copy.deepcopy(whole if t==typ and g in ('all','metric','meter_based') else empty)
                    for g in ('all','metric','nonmetric','meter_based','other_units','unknown')}
        units[t].update(exact_units={'meters':3} if t==typ else {}, geometry_refused_exact_units={})
    keys = [r['key'] for r in parent]
    bundle = dict(schema='legs1-r1-nomdg-v1', expected_keys=keys, arms=arms, unit_scores=units, synthetic=True)
    admission = dict(report=dict(per_type={typ:dict(items=3, call_rate_denominator_items=3,
                    call_rate_decoded_items_pct=100, call_rate_all_items_pct=100)}, unit_scores=units,
                    program_refusals=dict(total=0), gravity_guard_report={'dev-S1':dict(captures=[t['native'] for t in tasks],
                    capture_count=3, reviewed_refused=[], reviewed_refused_count=0)}))
    kit = dict(model='cp1m200', layout='duplicate', frames=32, parity_pass=True, binding='toy-kit',
               request_binding='toy-request', anchor_indices={k:anchors for k in keys},
               budget_arm=dict(arm='B2048', budget=2048, answer_cap=64, frames=32, layout='duplicate'),
               derivation=dict(total=3, per_type={typ:dict(forced_close=0, stopped_unclosed=0, derivation_error=0)}),
               benchmarks={'devrows':dict(expected=3, completed=3, errors=0, cap_hits=0, parse_failures=0, unanswered=0,
                                          per_type={typ:dict(count=3, score=1/6)})})
    config = dict(full_projection=dict(parity=dict(P3=dict(trainer_audit=dict(frame_count=64, do_sample_frames=False,
        original_frame_indices=[x for x in anchors for _ in range(2)], fps=30,
        original_timestamps_seconds=[x/30 for x in anchors for _ in range(2)],
        temporal_patch_timestamps_seconds=[x/30 for x in anchors])))))
    return bundle, admission, dict(rows=parent, model='cp1m200', arm='B2048'), kit, tasks, dict(captures=frames), config, direct


class ToyTests(unittest.TestCase):
    def test_three_room_adapter_and_script_cli_known_answer(self):
        folder = Path(tempfile.mkdtemp(prefix='three_room_', dir=HERE))
        bundle, admission, parent, kit, tasks, frames, config, direct = toy_case()
        identity = A.validate(bundle, parent, kit, tasks, frames, config, direct, direct, full=False)
        selected = {r['key'] for r in identity['items']}
        compact = [{k: r[k] for k in ('key','id','family','question_type','room','native','stratum',
                    'score','hit_token_cap','parse_failed','budget','finish_reason')} for r in direct]
        compact_bytes, raw_bytes, _ = A.substitute(json.dumps(compact),
            ''.join(json.dumps(x)+'\n' for x in direct).encode(), A.index(parent['rows']), kit,
            {'devrows:'+t['id']: t for t in tasks}, selected)
        for name, data in (('bundle.json',bundle),('admission.json',admission),('frames.json',frames),('subset.json',sorted(selected))):
            A.write(folder/name, data)
        (folder/'compact.json').write_bytes(compact_bytes)
        (folder/'raw.jsonl').write_bytes(raw_bytes)
        (folder/'tasks.jsonl').write_text(''.join(json.dumps(t)+'\n' for t in tasks))
        (folder/'camera.jsonl').write_text('')
        for name in ('BRIEF_03.md','20261116T0126Z_ORCH_RULING_forced_close_and_fixes.md',
                     'review_an/REVIEW_VERDICT_ANALYSIS.md','20261115T2358Z_ORCH_GO_full.md','REVIEW_VERDICT_C8R.md'):
            path = folder/'in'/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('Synthetic fixture source; no model evidence.\n')
        n = A.analysis_module()
        n.BUILD = folder
        argv = ['--bundle',str(folder/'bundle.json'),'--admission',str(folder/'admission.json'),
                '--direct',str(folder/'compact.json'),'--direct-raw',str(folder/'raw.jsonl'),
                '--tasks',str(folder/'tasks.jsonl'),'--frames',str(folder/'frames.json'),
                '--camera-tasks',str(folder/'camera.jsonl'),'--subset',str(folder/'subset.json'),
                '--plumbing','--draws','10000','--output',str(folder/'result')]
        log = io.StringIO()
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            status = n.main(argv)
        (folder/'cli.log').write_text(log.getvalue())
        self.assertEqual(status, 0, log.getvalue())
        result = A.read(folder/'result/NATIVE_VS_DIRECT.json')
        self.assertTrue(result['mode'].startswith('PLUMBING'))
        primary = result['groups'][A.TYPES[0]]['all_items']
        self.assertEqual((primary['items'], primary['rooms']), (3,3))
        self.assertAlmostEqual(primary['direct_pct'], 100/6)
        self.assertEqual(primary['native_pct'], 50)
        self.assertEqual(primary['scripted_pct'], 50)
        for arm, bounds in (('unflagged',[-25,100]),('scripted',[0,50])):
            self.assertAlmostEqual(primary['differences'][arm]['points'], 100/3)
            self.assertEqual(primary['differences'][arm]['paired95_rooms'], bounds)
        capped = result['groups'][A.TYPES[0]]['capped_zeroed']
        self.assertAlmostEqual(capped['differences']['unflagged']['points'], 0)
        self.assertEqual(capped['differences']['unflagged']['paired95_rooms'], [-25,25])
        A.write(HERE/'TOY_RECEIPT.json', dict(fixture_path=str(folder), result_path=str(folder/'result/NATIVE_VS_DIRECT.json'),
                expected_primary_difference_points=100/3, expected_native_interval=[-25,100],
                expected_scripted_interval=[0,50], expected_capped_native_difference=0,
                explanation='Each room has one item. Native-parent differences are 1, 1/4, -1/4; scripted-parent are 1/2, 0, 1/2. Extreme room samples each occur with probability 1/27, so percentile endpoints are the extremes.',
                script_sha_after=A.verify_script(), status='PASS', synthetic=True))


if __name__ == '__main__':
    unittest.main(verbosity=2)
