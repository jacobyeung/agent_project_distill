"""Scorer and binding tests on synthetic cameras built from the real GT anchors."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


S = module('score_k4', ROOT/'score_k4.py')
W = module('worker_k4t', ROOT/'2.py')
REF = json.loads((ROOT/'REFERENCE_K4.json').read_text())
CFG = json.loads((ROOT/'1.json').read_text())
LABELS = S.LABELS


def rz(deg):
    t = np.radians(deg)
    return np.array([[np.cos(t), -np.sin(t), 0], [np.sin(t), np.cos(t), 0], [0, 0, 1.]])


def cams(ref, plan, theta):
    """Second-half anchors turn by theta about the world z axis: rr = theta*sqrt(256/496), max error = theta."""
    gt = np.asarray(ref['gt'], float)
    anchor = gt.copy()
    anchor[16:, :3, :3] = rz(theta) @ anchor[16:, :3, :3]
    full = np.tile(np.eye(4), (len(plan['ids']), 1, 1))
    slots = plan['slots']
    for k in range(len(plan['ids'])):
        nearest = max(i for i, s in enumerate(slots) if s <= k)
        full[k] = anchor[nearest]
    return full.tolist()


def ret(thetas, stub=False):
    """thetas: {capture key: {label: degrees}} with default 2 deg for references and 90 for failing."""
    rows = []
    for ref in REF['captures']:
        arms = []
        for a, label in enumerate(LABELS):
            plan = ref['arms'][a]
            theta = thetas.get(ref['key'], {}).get(label, 90.0 if ref['group'] == 'failing' else 2.0)
            if theta is None:
                arms.append(dict(status='budget'))
                continue
            plan = copy.deepcopy(plan)
            arms.append(dict(status='ok', ids=plan['ids'], sha256=plan['sha256'], slots=plan['slots'],
                             raw_sha256=list(plan['raw_sha256']), raw_matches=[True]*len(plan['ids']),
                             raw_match_count=len(plan['ids']), decode_versions=dict(cv2='4.10.0', PIL='12.2.0', numpy='1.26.4'),
                             scale=ref['scale'], gravity=ref['gravity'], c2w=cams(ref, plan, theta), seconds=1.0))
        rows.append(dict(key=ref['key'], arms=arms))
    total = sum(len(a.get('raw_sha256', [])) for r in rows for a in r['arms'])
    return dict(schema=3, token=REF['token'], stub=stub, mode='stub' if stub else 'gpu', complete=True, rows=rows,
                raw_match_count=total, raw_frame_count=total)


FAIL = [r['key'] for r in REF['captures'] if r['group'] == 'failing']
REFS = [r['key'] for r in REF['captures'] if r['group'] == 'reference']
K = 256**.5/496**.5


class Scorer(unittest.TestCase):
    def test_repaired_confirm(self):
        t = {k: dict(A=90, A2=90.5, **{"A'": 91.0}, Bm=30, Cm=20) for k in FAIL}
        out = S.score(ret(t), REF)
        self.assertEqual(out['verdict'], 'confirm')
        self.assertEqual(len(out['decision']['repaired_any']), 5)
        row = next(r for r in out['rows'] if r['key'] == FAIL[0])
        self.assertAlmostEqual(row['floor_deg'], K*1.0, places=3)
        self.assertEqual(row['arms']['A']['similarity']['classification'], 'gross')
        self.assertEqual(row['arms']['Bm']['similarity']['classification'], 'moderate')

    def test_floor_blocks_repair_refute(self):
        t = {k: dict(A=90, A2=90, **{"A'": 150.0}, Bm=50, Cm=50) for k in FAIL}
        out = S.score(ret(t), REF)
        row = next(r for r in out['rows'] if r['key'] == FAIL[0])
        self.assertGreater(row['floor_deg'], (90-50)*K)
        self.assertEqual(out['decision']['repaired']['Bm'], [])
        self.assertEqual(out['verdict'], 'refute')

    def test_leaving_gross_needed(self):
        t = {k: dict(A=90, A2=90, **{"A'": 90.0}, Bm=70, Cm=65) for k in FAIL}
        out = S.score(ret(t), REF)
        self.assertEqual(out['decision']['repaired_any'], [])
        self.assertEqual(out['verdict'], 'refute')

    def test_two_repaired_inconclusive(self):
        t = {k: dict(Bm=20, Cm=20) for k in FAIL[:2]}
        out = S.score(ret(t), REF)
        self.assertEqual(out['verdict'], 'inconclusive')

    def test_union_over_arms_confirms(self):
        t = {FAIL[0]: dict(Bm=20), FAIL[1]: dict(Bm=20), FAIL[2]: dict(Cm=20)}
        out = S.score(ret(t), REF)
        self.assertEqual(out['decision']['repaired_any'], sorted(out['decision']['repaired_any']))
        self.assertEqual(len(out['decision']['repaired_any']), 3)
        self.assertEqual(out['verdict'], 'confirm')

    def test_one_per_arm_refutes(self):
        t = {FAIL[0]: dict(Bm=20), FAIL[1]: dict(Cm=20)}
        self.assertEqual(S.score(ret(t), REF)['verdict'], 'refute')

    def test_reference_rise_beyond_floor_blocks_confirm(self):
        t = {k: dict(Bm=20, Cm=20) for k in FAIL}
        # Floor 0 (A=A2=A'=2); rise = K*(theta-2) > 2 deg needs theta > 2+2/K.
        t[REFS[0]] = dict(Cm=2+2/K+1)
        out = S.score(ret(t), REF)
        self.assertEqual(out['decision']['reference_violations'], [[REF['captures'][5]['capture'], 'Cm']])
        self.assertEqual(out['verdict'], 'inconclusive')

    def test_reference_rise_within_floor_allowed(self):
        t = {k: dict(Bm=20, Cm=20) for k in FAIL}
        t[REFS[0]] = {"A'": 6.0, 'Cm': 2+2/K+1}
        out = S.score(ret(t), REF)
        self.assertEqual(out['decision']['reference_violations'], [])
        self.assertEqual(out['verdict'], 'confirm')

    def test_incomplete_when_any_arm_missing(self):
        t = {k: dict(Bm=20, Cm=20) for k in FAIL}
        t[REFS[4]] = {"C'": None}
        out = S.score(ret(t), REF)
        self.assertEqual(out['verdict'], 'incomplete')
        self.assertEqual(out['continuity']['verdict'], 'incomplete')

    def test_stub_is_synthetic(self):
        self.assertEqual(S.score(ret({}, stub=True), REF)['verdict'], 'synthetic')

    def test_continuity_uses_aprime(self):
        t = {k: {"A'": 90.0, "B'": 20, "C'": 20} for k in FAIL}
        out = S.score(ret(t), REF)
        self.assertEqual(out['continuity']['verdict'], 'confirm')
        self.assertEqual(out['verdict'], 'refute')

    def test_controls_reported(self):
        out = S.score(ret({}), REF)
        row = out['rows'][0]
        for k in ('A_vs_T1', 'A_vs_A2', "A_vs_A'", "A'_vs_T1"):
            self.assertIn(k, row['compare'])
        self.assertAlmostEqual(row['compare']['A_vs_A2']['center_rms_m'], 0.0)
        self.assertAlmostEqual(row['arms']['Cm']['similarity']['scale_relative_to_A'], 1.0)
        md = S.render(out)
        self.assertIn('Coverage verdict', md)

    def test_prior_continuity(self):
        prior = dict(rows=[])
        for ref in REF['captures']:
            arms = []
            for a in (2, 3):
                plan = ref['arms'][a]
                arms.append(dict(status='ok', ids=plan['ids'], slots=plan['slots'], c2w=cams(ref, plan, 1.0)))
            prior['rows'].append(dict(key=ref['key'], arms=arms))
        out = S.score(ret({}), REF, prior)
        self.assertIn("A'_vs_prior", out['rows'][0]['compare'])

    def test_forgeries_rejected(self):
        def mutate(fn):
            d = ret({})
            fn(d['rows'][0]['arms'][5])
            return d
        bad = [lambda a: a['ids'].reverse(), lambda a: a['raw_matches'].__setitem__(0, False),
               lambda a: a.__setitem__('raw_match_count', 1), lambda a: a['raw_sha256'].__setitem__(0, 'bad'),
               lambda a: a.__setitem__('scale', 1.0), lambda a: a.__setitem__('decode_versions', dict(cv2=''))]
        for fn in bad:
            with self.assertRaises(ValueError):
                S.score(mutate(fn), REF)
        d = ret({})
        d['raw_frame_count'] -= 1
        with self.assertRaises(ValueError):
            S.score(d, REF)

    def test_cpu_summary(self):
        ref = REF['captures'][0]
        plan = ref['arms'][0]
        data = dict(mode='cpu', complete=True, rows=[dict(key=ref['key'], arms=[dict(status='ok', ids=plan['ids'],
                    c2w=cams(ref, plan, 0.0), seconds=1.0, inference_seconds=0.5, rss_kib=1)]+[dict(status='budget')]*6)],
                    decoded=[dict(key=r['key'], arms=[dict(frames=len(p['ids']), raw_sha256=p['raw_sha256'], raw_match_count=len(p['ids']),
                    decode_versions=dict(cv2='a', PIL='b', numpy='c')) for p in r['arms']]) for r in REF['captures']])
        out = S.cpu_summary(data, REF)
        self.assertEqual(out['decoded_frames'], 4100)
        self.assertTrue(out['finite'])
        data['decoded'][3]['arms'][4]['raw_match_count'] -= 1
        with self.assertRaises(ValueError):
            S.cpu_summary(data, REF)


class Binding(unittest.TestCase):
    def test_plan(self):
        self.assertEqual(len(W.tasks(CFG)), 70)
        self.assertEqual(CFG['xr'], [0, 1, 2, 5, 6, 3, 4])
        self.assertLessEqual(W.forecast(CFG), CFG['xv'][1])
        for row in CFG['x3']:
            for a in range(7):
                ids, _, _ = W.binding(row, a)
                self.assertEqual(len(ids), W.SPEC[a][0])
            self.assertEqual(sum(row['x4'][5]['x5']), 31)
            self.assertEqual(sum(row['x4'][6]['x5']), 62)
            self.assertEqual(row['x4'][6]['x0'], row['x4'][4]['x0'])

    def test_rejections(self):
        cases = [(1, lambda a: a['x6'].__setitem__(0, 'f'*64), 'E19'),
                 (5, lambda a: a['x5'].__setitem__(0, True), 'E19'),
                 (6, lambda a: a['x1'].__setitem__(0, 'f'*64), 'E19'),
                 (3, lambda a: a['x0'].__setitem__(1, a['x0'][1]+1), 'E03'),
                 (4, lambda a: a['x5'].__setitem__(0, False), 'E19'),
                 (2, lambda a: a['x1'].__setitem__(3, '../x'), 'E19')]
        for arm, fn, code in cases:
            row = copy.deepcopy(CFG['x3'][0])
            fn(row['x4'][arm])
            with self.assertRaises(ValueError) as e:
                W.binding(row, arm)
            self.assertEqual(e.exception.args[0], code)


if __name__ == '__main__':
    unittest.main(verbosity=2)
