"""CPU guard regressions; all fixture artifacts stay in kc_guard_tests."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import trace
import unittest
from unittest.mock import patch

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[3].parent / 'kc_guard_tests'
os.environ.update(CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
                  OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
sys.path.insert(0, str(WORK))
TARGETS = [WORK / n for n in ('k1_guard.py', 'gravity_guard.py', 'k1_pipeline.py', 'k1_cli.py', 'k1_report.py')]
hits = {}


def tracer(frame, event, arg):
    name = frame.f_code.co_filename
    if name in {str(p) for p in TARGETS}:
        if event == 'line':
            hits.setdefault(name, set()).add(frame.f_lineno)
        return tracer


sys.settrace(tracer)
import numpy as np
import k1_pipeline as K
K._native()
B, P = K.B, K.P
import k1_phases as F
import k1_guard as guard
from boundaries import CPU
from student_pilot import geometry_profiles as GP
from student_pilot import camera_targets

MANIFEST = '/scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json'
CANARY = ROOT / os.environ.get('K1_CANARY_ROOT', 'canary')


class GuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ROOT / os.environ.get('K1_GUARD_TEST_RUN', 'unit')
        cls.root.mkdir()
        cls.real = B.load(MANIFEST)
        cls.c = copy.deepcopy(cls.real['captures'][0])
        cls.c['rows'] = [dict(id='refused-distance', type='object_abs_distance',
                             question='Distance between chair and table?', operands=['chair', 'table'],
                             unit='m', gt_value=1., fallback=dict(visual_evidence_verified=True,
                             trace='The image shows a gap.', answer='1.00')),
                         dict(id='refused-room', type='room_size_estimation', question='Room area?',
                              operands=[], unit='m2', gt_value=10.)]
        cls.m = dict(captures=[cls.c], inventory=cls.real['inventory'])
        cls.boundary = CPU()
        cls.tower = cls.root / 'tower'
        cls.own = cls.root / 'own'
        key = B.digest(cls.c['canonical'])[:16]
        a, b = cls.tower / key, cls.own / key
        a.mkdir(parents=True); b.mkdir(parents=True)
        state = cls.boundary.tower(cls.c, [None] * len(cls.c['dense_frames']))
        np.savez(a / 'tower.npz', raw_pose=state.raw_pose9, depth_grid=state.depth_grid,
                 depth_conf_grid=state.depth_conf_grid, frame_indices=state.frame_indices,
                 anchor_slots=state.anchor_slots, grid_uv=state.grid_uv)
        B.write(a / 'candidates.json', dict(phrases=[], frames={}, fixture_only=True))
        (a / 'parity_raw.jsonl').write_text('')
        F.receipt(cls.c, cls.boundary, a, 'tower_sam',
                  ['tower.npz', 'candidates.json', 'parity_raw.jsonl'], source_hw=[80, 112])
        depth, gravity = cls.boundary.own(cls.c, [], state)
        np.savez(b / 'own.npz', depth=depth, gravity=gravity)
        F.receipt(cls.c, cls.boundary, b, 'own', ['own.npz'])
        cls.out = cls.root / 'refusal'
        # Proper rotation: reference plane=1 and margin=-1. The real reviewed
        # validator, converter, phase checks and receipt writer all execute.
        rotations = np.repeat(np.array([[1., 0., 0.], [0., 0., -1.], [0., 1., 0.]])[None], 32, axis=0)
        with patch.object(camera_targets, 'to_gravity_reference_frame',
                          return_value=(rotations, np.zeros((32, 3)), np.ones((32, 2)))):
            assert guard.run(cls.m, cls.out, cls.boundary, 'convert', 14400, cls.tower, cls.own) == 0
        cls.dest = cls.out / key

    def test_refusal_receipt_resume_and_cached(self):
        r = B.load(self.dest / 'CACHE_COMPLETE.json')
        self.assertEqual(r['gravity_guard'], guard.GG.identity())
        self.assertEqual(r['gravity_verdict'], dict(sealed_refused=True, reviewed_refused=True))
        self.assertEqual(r['geometry_refusal'], dict(code=guard.CODE, message=guard.CODE))
        self.assertIsNone(r['geometry'])
        self.assertFalse((self.dest / 'geometry.npz').exists())
        self.assertEqual(set(r['files']), {'candidates.json', 'parity_raw.jsonl', 'REFUSED_GEOMETRY.npz'})
        for name, pin in r['files'].items():
            self.assertEqual(B.checked(pin), self.dest / name)
        before = B.sha(self.dest / 'CACHE_COMPLETE.json')
        with patch.object(guard, '_convert', side_effect=AssertionError('Resume reconverted')), \
                patch.object(guard._recorder, 'records', {}):
            self.assertEqual(guard.run(self.m, self.out, self.boundary, 'convert', 14400, self.tower, self.own), 0)
            self.assertEqual(guard.verdict(self.c), r['gravity_verdict'])
        self.assertEqual(before, B.sha(self.dest / 'CACHE_COMPLETE.json'))
        self.assertIsNone(K.cached(self.c, self.dest)[1])
        self.assertEqual(B.load(self.out / 'GUARD_REPORT.json')['K1']['reviewed_refused'], [self.c['canonical']])

    def test_forged_refusals_rejected_and_resume_halts(self):
        c = self.real['captures'][1]
        key = B.digest(c['canonical'])[:16]
        source = CANARY / key
        for evidence in (True, False):
            out = self.root / ('forged_with_evidence' if evidence else 'forged_without_evidence')
            dest = out / key
            dest.mkdir(parents=True)
            names = ['candidates.json', 'parity_raw.jsonl']
            for name in names:
                shutil.copyfile(source / name, dest / name)
            if evidence:
                shutil.copyfile(source / 'geometry.npz', dest / 'REFUSED_GEOMETRY.npz')
                names.append('REFUSED_GEOMETRY.npz')
            r = B.load(source / 'CACHE_COMPLETE.json')
            r.update(geometry=None, geometry_refusal=dict(code=guard.CODE, message=guard.CODE),
                     gravity_verdict=dict(sealed_refused=False, reviewed_refused=True),
                     files={name: B.pin(dest / name) for name in names})
            B.write(dest / 'CACHE_COMPLETE.json', r)
            message = 'refusal geometry passed reviewed guard' if evidence else 'file binding differs'
            with patch.object(guard._recorder, 'records', {}):
                with self.assertRaisesRegex(ValueError, message):
                    K.cached(c, dest)
                with patch.object(guard, '_convert', side_effect=AssertionError('Resume reconverted')):
                    with self.assertRaisesRegex(ValueError, message):
                        guard.run(dict(captures=[c]), out, self.boundary, 'convert', 14400, self.tower, self.own)
                self.assertIn(message, B.load(out / 'HALTED.json')['error'])
                self.assertFalse(guard._recorder.records.get(('K1', c['canonical']), (False, False))[1])

    def test_refusal_verdict_must_match_evidence(self):
        r = B.load(self.dest / 'CACHE_COMPLETE.json')
        r['gravity_verdict']['sealed_refused'] = False
        original = B.load
        def load(path):
            return r if Path(path) == self.dest / 'CACHE_COMPLETE.json' else original(path)
        with patch.object(B, 'load', side_effect=load), patch.object(guard._recorder, 'records', {}):
            with self.assertRaisesRegex(ValueError, 'Cache gravity verdict differs'):
                K.cached(self.c, self.dest)
            self.assertEqual(guard.verdict(self.c), dict(sealed_refused=True, reviewed_refused=True))

    def test_refusal_reload_propagates_other_errors(self):
        from student_pilot import ground_profiles
        for error in (GP.GeometryError('invalid_scale'), ValueError('mutation')):
            with patch.object(ground_profiles, 'load_geometry', side_effect=error):
                with self.assertRaisesRegex(type(error), str(error)):
                    K.cached(self.c, self.dest)

    def test_tables_and_render_keep_refusals(self):
        import build_tables
        tables = self.root / 'tables'
        with patch.object(build_tables, 'build_capture', side_effect=AssertionError('Refused candidate extraction')), \
                patch.object(K, 'gt_arrays', side_effect=AssertionError('Refused GT load')):
            K.tables(self.m, self.out, tables)
        self.assertEqual((tables / 'candidates.jsonl').read_text(), '')
        self.assertEqual((tables / 'pairs.jsonl').read_text(), '')
        self.assertEqual(B.load(tables / 'TABLE_RECEIPT.json')['geometry_refused'], {self.c['canonical']: guard.CODE})
        fit = self.root / 'fit'; fit.mkdir()
        B.write(fit / 'NATIVE_POLICY.json', dict(fixture_only=True))
        B.write(fit / 'FIT_RECEIPT.json', dict(fixture_only=False,
                native_policy_sha256=B.sha(fit / 'NATIVE_POLICY.json'),
                inputs={self.m['inventory']['path']: self.m['inventory']['sha256']}, train_rooms=[], heldout_rooms=[]))
        rendered = self.root / 'render'
        with patch.object(K, 'native_backend', side_effect=AssertionError('Refused backend')), \
                patch.object(B.perception, 'execute_calls', side_effect=AssertionError('Refused calls')), \
                patch.object(K, 'gt_arrays', side_effect=AssertionError('Refused GT load')):
            K.responses(self.m, self.out, fit, rendered)
        results = B.load(rendered / self.dest.name / 'responses.json')
        for row, result in zip(self.c['rows'], results, strict=True):
            self.assertEqual(result['decision'], P.classify(row, result, {'ok': False}))
            self.assertIsNone(result['decision']['value'])
            self.assertEqual(result['mask_match'], {'ok': False})
            self.assertEqual(len(result['calls']), 1)
            self.assertTrue(P.failure(result['calls'][0]))
        rows = [json.loads(s) for s in (rendered / 'K1_ANALYSIS_INPUT.jsonl').read_text().splitlines()]
        self.assertEqual({r['id'] for r in rows}, {r['id'] for r in self.c['rows']})
        self.assertTrue(all(r['pred'] is None and r['rendered_label'] == 'excluded'
                            and not r['training_target_available'] and r['printed_cues']['status'] == 1 for r in rows))
        for out in (tables, rendered):
            self.assertEqual(B.load(out / 'GUARD_REPORT.json')['K1']['reviewed_refused'], [self.c['canonical']])

    def test_other_exceptions_halt(self):
        for name, error in [('geometry', GP.GeometryError('invalid_scale')), ('value', ValueError('mutation'))]:
            out = self.root / ('halt_' + name)
            with patch.object(B.geometry, 'convert', side_effect=error):
                with self.assertRaisesRegex(type(error), str(error)):
                    guard.run(self.m, out, self.boundary, 'convert', 14400, self.tower, self.own)
            self.assertIn(str(error), B.load(out / 'HALTED.json')['error'])
            self.assertFalse((out / self.dest.name / 'CACHE_COMPLETE.json').exists())

    def test_matching_message_without_reviewed_verdict_halts(self):
        c = self.real['captures'][1]
        out = self.root / 'unreviewed_error'
        with patch.object(guard, '_convert', side_effect=GP.GeometryError(guard.CODE)):
            with self.assertRaisesRegex(GP.GeometryError, guard.CODE):
                guard.run(dict(captures=[c]), out, self.boundary, 'convert', 14400, self.tower, self.own)
        self.assertIn(guard.CODE, B.load(out / 'HALTED.json')['error'])

    def test_passing_canary_cached(self):
        c = self.real['captures'][2]
        raw, geo, receipt = K.cached(c, CANARY / B.digest(c['canonical'])[:16])
        self.assertIsNotNone(geo)
        self.assertEqual(receipt['gravity_verdict'], dict(sealed_refused=True, reviewed_refused=False))

    def test_passing_downstream_capture_context(self):
        import build_tables
        c = self.real['captures'][2]
        m = dict(captures=[c], inventory=self.real['inventory'])
        def build(*args):
            self.assertEqual(guard.GG._capture.get(), ('K1', c['canonical']))
            return [{'fixture': 'candidate'}], [{'fixture': 'pair'}]
        out = self.root / 'passing_tables'
        with patch.object(build_tables, 'build_capture', side_effect=build), patch.object(K, 'gt_arrays', return_value={}):
            K.tables(m, CANARY, out)
        self.assertEqual(B.load(out / 'TABLE_RECEIPT.json')['geometry_refused'], {})
        self.assertEqual(len((out / 'candidates.jsonl').read_text().splitlines()), 1)
        self.assertEqual(len((out / 'pairs.jsonl').read_text().splitlines()), 1)
        fit = self.root / 'passing_fit'; fit.mkdir()
        B.write(fit / 'NATIVE_POLICY.json', dict(fixture_only=True))
        B.write(fit / 'FIT_RECEIPT.json', dict(fixture_only=False,
                native_policy_sha256=B.sha(fit / 'NATIVE_POLICY.json'),
                inputs={m['inventory']['path']: m['inventory']['sha256']}, train_rooms=[], heldout_rooms=[]))
        def execute(geo, backend, calls):
            self.assertEqual(guard.GG._capture.get(), ('K1', c['canonical']))
            geo.contract.validate()
            return dict(calls=[dict(call=calls[0], kind='error', code='fixture_backend_failure', response='unavailable')])
        with patch.object(K, 'native_backend', return_value=object()), \
                patch.object(B.perception, 'execute_calls', side_effect=execute), \
                patch.object(K, 'gt_arrays', return_value={}):
            K.responses(m, CANARY, fit, self.root / 'passing_render')
        rows = (self.root / 'passing_render/K1_ANALYSIS_INPUT.jsonl').read_text().splitlines()
        self.assertEqual(len(rows), len(c['rows']))

    def test_cli_convert_stop(self):
        import k1_cli
        out = self.root / 'cli_stop'; out.mkdir()
        (out / 'STOP').write_text('STOP\n')
        args = ['k1_pipeline.py', 'cache', '--manifest', MANIFEST, '--out', str(out),
                '--phase', 'convert', '--max-seconds', '14400',
                '--tower-cache', str(self.tower), '--own-cache', str(self.own)]
        with patch.object(sys, 'argv', args):
            self.assertEqual(k1_cli.main(), 4)
        self.assertTrue((out / 'GUARD_REPORT.json').is_file())
        self.assertFalse((out / 'HALTED.json').exists())

    def test_bad_receipt_bindings(self):
        r = B.load(self.dest / 'CACHE_COMPLETE.json')
        mutations = [dict(gravity_guard={}), dict(sources={}), dict(geometry={'fake': True}),
                     dict(gravity_verdict=dict(sealed_refused=True, reviewed_refused=False)),
                     dict(geometry_refusal=dict(code='invalid_scale', message='invalid_scale')),
                     dict(files={}), dict(phase='wrong')]
        for changed in mutations:
            with self.assertRaises(ValueError):
                guard.check_receipt(self.c, self.dest, dict(r, **changed))

    def test_install_once_and_sealed_hash_failure(self):
        current = GP.GeometryContract.validate
        guard.install(); guard.install()
        self.assertIs(GP.GeometryContract.validate, current)
        # A fresh process must reject an altered sealed method before output exists.
        code = """import sys
sys.path.insert(0, sys.argv[1])
import k1_pipeline as K
K._native()
import k1_guard as g
g.geometry_profiles.GeometryContract.validate = g.verdict
try:
    g.install()
except RuntimeError as error:
    assert str(error) == 'sealed_validate_mismatch', error
    print(error)
else:
    raise AssertionError('Installed over changed sealed method')
"""
        result = subprocess.run([sys.executable, '-I', '-s', '-B', '-c', code, str(WORK)],
                                capture_output=True, text=True, check=True)
        self.assertIn('sealed_validate_mismatch', result.stdout)

    def test_report_denominators(self):
        import k1_report as R
        cs = self.real['captures'][:2]
        inventory = dict(pilot=[dict(canonical=c['canonical'], split=split)
                              for c, split in zip(cs, ['train', 'heldout'])])
        rows = [dict(id=str(i), canonical=c['canonical'], type='object_abs_distance',
                     gt_value=1., pred=None, label='fallback', training_target_available=False,
                     printed_cues={'status': 1}) for i, c in enumerate(cs)]
        metric = dict(auc=.5, top1_accept_accuracy=.5)
        fit = dict(metrics=dict(accept=dict(refit=metric, current=metric)))
        report = R.report(rows, inventory, fit, ['0', '1'])
        self.assertEqual(report['heldout_items'], 1)
        self.assertEqual(report['answered_items'], 0)
        self.assertEqual(report['printed_cues']['status']['all']['n'], 1)
        self.assertTrue(report['complete_row_denominator_checked'])
        with self.assertRaisesRegex(ValueError, 'denominator'):
            R.report(rows[:1], inventory, fit, ['0', '1'])


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(GuardTests))
    sys.settrace(None)
    coverage = {}
    for path in TARGETS:
        executable = set(trace._find_executable_linenos(str(path)))
        executed = hits.get(str(path), set()) & executable
        coverage[path.name] = dict(executable=sorted(executable), hit=sorted(executed), missing=sorted(executable-executed))
    (ROOT / 'guard_coverage.json').write_text(json.dumps(coverage, indent=2) + '\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
