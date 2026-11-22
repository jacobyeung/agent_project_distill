"""STAB synthetic tests (no banked score is read). Run: python -I -B tests.py (from stab/code)."""
import math
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np

import common as C
import price as P
import tau as T


class Youden(unittest.TestCase):
    def test_separable(self):
        r = T.youden([1, 2, 3, 4, 5, 6], [0, 0, 0, 1, 1, 1])
        self.assertFalse(r['void'])
        self.assertAlmostEqual(r['tau'], math.sqrt(12))
        self.assertEqual(r['J'], 1.0)

    def test_tie_goes_to_larger_tau(self):
        # cut 3|4: TPR 1, FPR 1/4 (J .75); cut 5|6: TPR 3/4, FPR 0 (J .75) -> larger tau
        r = T.youden([1, 2, 3, 4, 5, 6, 7, 8], [0, 0, 0, 1, 0, 1, 1, 1])
        self.assertAlmostEqual(r['J'], 0.75)
        self.assertEqual(r['tied_cuts'], 2)
        self.assertAlmostEqual(r['tau'], math.sqrt(30))

    def test_flag_is_strictly_above_and_duplicates(self):
        r = T.youden([1, 1, 2, 2, 4, 4, 4], [0, 0, 0, 0, 1, 1, 1])
        self.assertEqual([c['tau'] for c in r['cuts']], [math.sqrt(2), math.sqrt(8)])
        self.assertAlmostEqual(r['tau'], math.sqrt(8))

    def test_void_fit(self):
        for g in ([0, 0, 0, 0, 1, 1], [1, 1, 1, 1, 0, 0]):
            r = T.youden([1, 2, 3, 4, 5, 6], g)
            self.assertTrue(r['void'])
            self.assertEqual(r['tau'], 3.9)
        self.assertFalse(T.youden([1, 2, 3, 4, 5, 6], [0, 0, 0, 1, 1, 1])['void'])


def synth(n=150, rooms=30, seed=1):
    rng = np.random.default_rng(seed)
    ids = ['i%03d' % k for k in range(n)]
    room = {i: 'r%02d' % (k % rooms) for k, i in enumerate(ids)}
    sc = {a: {i: float(rng.integers(0, 2)) for i in ids} for a in ('base', 'own', 'direct')}
    return ids, room, sc


class Swap(unittest.TestCase):
    def test_unflagged_unchanged(self):
        ids, room, sc = synth()
        fl = set(ids[:20])
        sw = P.swap(sc['base'], sc['own'], fl)
        self.assertTrue(all(sw[i] == sc['base'][i] for i in ids if i not in fl))
        self.assertTrue(all(sw[i] == sc['own'][i] for i in fl))
        r = P.price_type(ids, room, fl, sc, ['base'])
        for a in P.ARMS:
            self.assertEqual(r['by_baseline']['base']['arms'][a]['unflagged_changed'], 0)

    def test_no_flag_zero_difference(self):
        ids, room, sc = synth()
        r = P.price_type(ids, room, set(), sc, ['base'])
        for a in P.ARMS:
            x = r['by_baseline']['base']['arms'][a]
            self.assertEqual((x['diff'], x['ci95'], x['ci99375']), (0.0, [0.0, 0.0], [0.0, 0.0]))

    def test_oracle_is_ceiling(self):
        ids, room, sc = synth()
        r = P.price_type(ids, room, set(ids[:40]), sc, ['base'])['by_baseline']['base']
        self.assertGreaterEqual(r['oracle']['diff'], max(r['arms'][a]['diff'] for a in P.ARMS))


class Bootstrap(unittest.TestCase):
    def test_constant(self):
        b = P.bootstrap([('r%d' % (k % 5), 2.0) for k in range(40)])
        self.assertEqual(b['value'], 2.0)
        self.assertTrue(np.allclose(b['ci95'], [2, 2]) and np.allclose(b['ci99375'], [2, 2]))

    def test_matches_project_estimator(self):
        sys.path.insert(0, str(C.NFA/'ref/payload'))
        from h1eval import statistics
        rng = np.random.default_rng(7)
        vals = [('r%d' % (k % 11), float(rng.normal())) for k in range(150)]
        mine, ref = P.bootstrap(vals), statistics.bootstrap(vals)
        self.assertEqual(mine['value'], ref['value'])
        self.assertEqual(mine['ci95'], ref['ci95'])
        self.assertLess(mine['ci99375'][0], mine['ci95'][0])
        self.assertGreater(mine['ci99375'][1], mine['ci95'][1])

    def test_known_two_rooms(self):
        # rooms A (one item, +3) and B (one item, -1): samples are 3, 1 or -1 with probs 1/4, 1/2, 1/4
        b = P.bootstrap([('A', 3.0), ('B', -1.0)])
        self.assertEqual(b['value'], 1.0)
        self.assertEqual(b['ci95'], [-1.0, 3.0])


class Refusals(unittest.TestCase):
    def _items(self):
        return {'a': dict(question_type='camera_rotation', room_key='r1', room='d1/x', native='d1/x_00', scene='scannet/x_00'),
                'b': dict(question_type='camera_rotation', room_key='r2', room='d1/y', native='d1/y_00', scene='scannet/y_00')}

    def test_missing_key(self):
        items = self._items()
        row = lambda i: dict(id=i, type='camera_rotation', room_key=items[i]['room_key'])
        with self.assertRaises(KeyError):
            C.join(items, {'base': {'camera_rotation': {'a': row('a')}}})
        with self.assertRaises(KeyError):
            C.join(items, {'base': {'camera_rotation': {'a': row('a'), 'b': row('b'), 'c': row('a')}}})
        C.join(items, {'base': {'camera_rotation': {'a': row('a'), 'b': row('b')}}})
        with self.assertRaises(KeyError):
            P.swap({'a': 1.0, 'b': 0.0}, {'a': 1.0}, {'a'})

    def test_room_mismatch(self):
        items = self._items()
        bad = {'a': dict(id='a', type='camera_rotation', room_key='r9'), 'b': dict(id='b', type='camera_rotation', room_key='r2')}
        with self.assertRaises(ValueError):
            C.join(items, {'own': {'camera_rotation': bad}})

    def test_frame_mismatch(self):
        items = self._items()
        def r(i, count=32):
            return dict(output=dict(frames=dict(layout='duplicate', count=count, matches_training=True), key='devrows:'+i))
        d = lambda i, native: dict(native=native, key='devrows:'+i)
        arms = {'base': {k: {'a': r('a'), 'b': r('b')} for k in C.TYPES}, 'side': {}, 'own': {k: {'a': r('a'), 'b': r('b')} for k in C.TYPES},
                'direct': {k: {'a': d('a', 'd1/x_00'), 'b': d('b', 'd1/y_00')} for k in C.TYPES}}
        C.frame_checks(items, arms)
        arms['own']['camera_rotation']['b'] = r('b', count=31)
        with self.assertRaises(ValueError):
            C.frame_checks(items, arms)
        arms['own']['camera_rotation']['b'] = r('b')
        arms['direct']['camera_rotation']['b'] = d('b', 'd1/z_00')
        with self.assertRaises(ValueError):
            C.frame_checks(items, arms)


class Guard(unittest.TestCase):
    def test_refuses_without_review_go(self):
        calls = []
        orig = (C.verify, C.load_items, C.load_arm_rows)
        C.verify = C.load_items = C.load_arm_rows = lambda *a, **k: calls.append(1) or (_ for _ in ()).throw(AssertionError('read before guard'))
        try:
            with tempfile.TemporaryDirectory() as d:
                with self.assertRaises(P.Refused):
                    P.main([], stab=Path(d))
                self.assertEqual(calls, [])
                (Path(d)/'REVIEW_GO').write_text('go\n')
                (Path(d)/'code').mkdir()
                (Path(d)/'code/PRICE_STAB.json').write_text('{}')
                with self.assertRaises(P.Refused):
                    P.main([], stab=Path(d))
                self.assertEqual(calls, [])
                with self.assertRaises(SystemExit):              # F2: no --out to redirect the output
                    P.main(['--out', str(Path(d)/'elsewhere')], stab=Path(d))
                self.assertEqual(calls, [])
        finally:
            C.verify, C.load_items, C.load_arm_rows = orig

    def test_tau_sha_mismatch_refuses(self):
        # F2: a TAU.json other than the pinned one is refused before any input is read
        calls = []
        orig = (C.verify, C.load_items, C.load_arm_rows, C.TAU_JSON)
        C.verify = C.load_items = C.load_arm_rows = lambda *a, **k: calls.append(1) or (_ for _ in ()).throw(AssertionError('read'))
        try:
            with tempfile.TemporaryDirectory() as d:
                (Path(d)/'REVIEW_GO').write_text('go\n')
                (Path(d)/'TAU.json').write_text('{"tau_deg": 9.9}')
                C.TAU_JSON = Path(d)/'TAU.json'
                with self.assertRaisesRegex(P.Refused, 'TAU.json sha256'):
                    P.main([], stab=Path(d))
                self.assertEqual(calls, [])
        finally:
            C.verify, C.load_items, C.load_arm_rows, C.TAU_JSON = orig

    def test_tau_pin_is_the_reviewed_file(self):
        self.assertEqual(C.TAU_SHA256, '2d82d31fbb296d5158ca8c45d0540c8003727571581bfe32baad1eb8feacf282')
        self.assertEqual(C.sha(C.TAU_JSON), C.TAU_SHA256)

    def test_real_lane_has_no_review_go_yet(self):
        if not (C.STAB/'REVIEW_GO').exists():
            with self.assertRaises(P.Refused):
                P.guard()


class Reading(unittest.TestCase):
    def _t(self, items, rooms, diff, lo, hi95, baselines=('base',)):
        arms = {a: dict(diff=diff, ci99375=[lo, diff+1], ci95=[lo, hi95], passes=diff >= 1 and lo > 0, closes=hi95 < 1) for a in P.ARMS}
        return dict(decidability=P.decidable(items, rooms, 150), by_baseline={b: dict(arms=arms) for b in baselines})

    def test_decidable_rule(self):
        self.assertTrue(P.decidable(10, 3, 150)['decidable'])
        self.assertFalse(P.decidable(9, 3, 150)['decidable'])
        self.assertFalse(P.decidable(10, 2, 150)['decidable'])
        self.assertFalse(P.decidable(10, 3, 1000)['decidable'])   # ceiling 1.0 < 2

    def test_verdicts(self):
        self.assertEqual(P.reading({'x': self._t(4, 3, 5, 1, 9)}, True)['verdict'], 'too few')
        self.assertEqual(P.reading({'x': self._t(12, 6, 2, 0.1, 4)}, True)['verdict'], 'worth building')
        self.assertEqual(P.reading({'x': self._t(12, 3, 0.2, -1, 0.9)}, True)['verdict'], 'closed')
        self.assertEqual(P.reading({'x': self._t(12, 3, 0.9, -1, 2)}, True)['verdict'], 'undecided')
        self.assertEqual(P.reading({'x': self._t(12, 6, 2, -0.1, 4)}, True)['verdict'], 'undecided')
        # a too-few type never decides the reading
        self.assertEqual(P.reading({'x': self._t(12, 3, 0.2, -1, 0.9), 'y': self._t(4, 3, 9, 5, 12)}, True)['verdict'], 'closed')

    def test_direct_pass_held_without_anchor_check(self):
        t = self._t(12, 6, 2, 0.1, 4)
        t['by_baseline']['base']['arms']['own'].update(passes=False, closes=False)
        r = P.reading({'x': t}, False)
        self.assertEqual(r['verdict'], 'undecided')
        self.assertEqual(len(r['passes_held_for_frames']), 1)
        self.assertEqual(P.reading({'x': t}, True)['verdict'], 'worth building')

    def test_f1_three_rooms_can_close_cannot_pass(self):
        d = P.decidable(12, 3, 150)
        self.assertEqual((d['decidable'], d['can_pass'], d['label']), (True, False, 'can close, cannot pass'))
        self.assertEqual(P.decidable(12, 5, 150)['label'], 'can close, cannot pass')
        self.assertEqual(P.decidable(12, 6, 150)['label'], 'can pass or close')
        self.assertEqual(P.decidable(4, 3, 150)['label'], 'too few to decide')
        r = P.reading({'x': self._t(12, 3, 2, 0.1, 4)}, True)          # would pass, but only 3 flagged rooms
        self.assertEqual((r['verdict'], r['passes'], r['cannot_pass_types']), ('undecided', [], ['x']))
        self.assertEqual(P.reading({'x': self._t(12, 3, 0.2, -1, 0.9)}, True)['verdict'], 'closed')   # may still close
        # a 3-room type cannot block the close of the others, nor pass while another type closes
        self.assertEqual(P.reading({'x': self._t(12, 3, 0.2, -1, 0.9), 'y': self._t(16, 8, 0.1, -1, 0.8)}, True)['verdict'], 'closed')
        self.assertEqual(P.reading({'x': self._t(12, 3, 2, 0.1, 4), 'y': self._t(16, 8, 0.1, -1, 0.8)}, True)['verdict'], 'undecided')

    def test_distance_needs_both_baselines(self):
        t = self._t(16, 8, 2, 0.1, 4, baselines=('base', 'side'))
        t['by_baseline']['side'] = dict(arms={a: dict(diff=0.5, ci99375=[-1, 2], ci95=[-1, 2], passes=False, closes=False) for a in P.ARMS})
        self.assertEqual(P.reading({'object_abs_distance': t}, True)['verdict'], 'undecided')


class ItemScore(unittest.TestCase):
    def test_rules(self):
        o = lambda fin, v: dict(output=dict(finish=fin, scores=dict(answer=v)))
        d = lambda **k: dict(dict(score=1.0, hit_token_cap=False, parse_failed=False, finish_reason='stop'), **k)
        arms = {'base': {k: {'a': o('eos', 0.7), 'b': o('max_calls', 1.0)} for k in C.TYPES}, 'side': {},
                'own': {k: {'a': o('eos', 0.2), 'b': o('eos', 1.0)} for k in C.TYPES},
                'direct': {k: {'a': d(), 'b': d(finish_reason='length', hit_token_cap=True), 'c': d(parse_failed=True),
                               'e': d(finish_reason='error')} for k in C.TYPES}}
        s = P.item_scores({}, arms)
        self.assertEqual(s['base']['camera_rotation'], {'a': 0.7, 'b': 0.0})
        self.assertEqual(s['own']['camera_rotation'], {'a': 0.2, 'b': 1.0})
        self.assertEqual(s['direct']['camera_rotation'], {'a': 1.0, 'b': 0.0, 'c': 0.0, 'e': 0.0})


class EndToEnd(unittest.TestCase):
    """price.main on fully synthetic inputs (temp files with their own sha256), REVIEW_GO in a temp lane."""
    def test_synthetic_run(self):
        import hashlib
        import json
        rng = np.random.default_rng(3)
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            items, base, side, own, direct = [], {k: [] for k in C.TYPES}, [], [], []
            for kind in C.TYPES:
                for k in range(30):
                    s = k % 6
                    i = '%s-%02d' % (kind[:8], k)
                    items.append(dict(id=i, question_type=kind, room_key='r%d' % (s % 4), room='d1/s%d' % s, native='d1/s%d_00' % s,
                                      scene='scannet/s%d_00' % s, source_frame_indices=list(range(32))))
                    def row(arm, cap=False):
                        return dict(id=i, type=kind, room_key='r%d' % (s % 4), arm=arm, mode='none',
                                    output=dict(frames=dict(layout='duplicate', count=32, matches_training=True), key='devrows:'+i,
                                                finish='max_calls' if cap else 'eos', scores=dict(answer=float(rng.integers(0, 2)))))
                    base[kind].append(row('tower'))
                    own.append(row('own', cap=(k == 0)))
                    if kind == 'object_abs_distance':
                        side.append(row('tower'))
                    direct.append(dict(id=i, key='devrows:'+i, question_type=kind, room='d1/s%d' % s, native='d1/s%d_00' % s,
                                       score=float(rng.integers(0, 2)), finish_reason='length' if k == 1 else 'stop',
                                       hit_token_cap=k == 1, parse_failed=False))
            files = {}
            def put(name, text):
                p = d/name
                p.write_text(text)
                files[name] = (p, hashlib.sha256(text.encode()).hexdigest())
            jl = lambda rows: ''.join(json.dumps(r)+'\n' for r in rows)
            for name in C.REG:
                put(name, '{}')
            put('items', json.dumps(dict(items=items)))
            for kind, name in C.BASE_FILE.items():
                put(name, jl(base[kind]))
            put('base_dist_r0_null', jl(side))
            put('own_cam_170631', jl([r for r in own if r['type'] != 'object_abs_distance']))
            put('own_dist_170706', jl([r for r in own if r['type'] == 'object_abs_distance']))
            put('direct_169526', json.dumps(direct))
            reg = {k: files[k] for k in C.REG}
            tau = dict(tau_deg=1.0, void_fit=False, flags=dict(list=['scannet/s0_00', 'scannet/s1_00', 'scannet/s2_00']),
                       fragile=dict(list=['scannet/s2_00', 'scannet/s3_00']))
            (d/'TAU.json').write_text(json.dumps(tau))
            orig = (C.TAU_JSON, C.DIRECT_FRAMES, C.TAU_SHA256)
            C.TAU_JSON, C.DIRECT_FRAMES = d/'TAU.json', d/'none.json'
            C.TAU_SHA256 = C.sha(d/'TAU.json')
            try:
                (d/'REVIEW_GO').write_text('synthetic\n')
                res = P.main([], stab=d, reg=reg)
                with self.assertRaisesRegex(P.Refused, 'runs once'):     # F2: second run refused
                    P.main([], stab=d, reg=reg)
            finally:
                C.TAU_JSON, C.DIRECT_FRAMES, C.TAU_SHA256 = orig
            md = (d/'code/PRICE_STAB.md').read_text()
            self.assertIn('job 170631', md)                                 # F3 caveat
            self.assertIn('(i) decline the call', md)
            self.assertNotIn("'direct'", md)
            self.assertNotIn('registered baseline', md)
            self.assertIn('171253 read 1 (pinned candidates_argmax)', md)
            self.assertIn('can close, cannot pass', md)                    # F1 label (3 flagged rooms)
            for kind in C.TYPES:
                t = res['primary']['types'][kind]
                self.assertEqual(t['flagged'], 15)                      # scenes 0, 1, 2 of 6
                self.assertEqual(t['decidability']['rooms'], 3)
                self.assertEqual(t['decidability']['label'], 'can close, cannot pass')
                self.assertEqual(set(t['by_baseline']), {'base', 'side'} if kind == 'object_abs_distance' else {'base'})
                ft = res['fragile_flipped']['types'][kind]
                self.assertEqual(ft['flagged'], 15)                     # s2 off, s3 on
            # own capped row scores 0; direct forced close scores 0
            self.assertIn(res['primary']['reading']['verdict'], ('worth building', 'closed', 'undecided', 'too few'))
            self.assertEqual(res['frames']['direct_anchor_level'][:9], 'unchecked')


if __name__ == '__main__':
    unittest.main(verbosity=2)
