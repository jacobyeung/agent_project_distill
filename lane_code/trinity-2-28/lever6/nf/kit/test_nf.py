"""Synthetic tests of replay_nf.py (K5's real returns do not exist yet)."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import replay_nf as R  # noqa: E402
import synth_k5 as S  # noqa: E402

WORK = HERE.parent/'work'
WORK.mkdir(exist_ok=True)
ROUND7 = Path('/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/round7_common.py')
CAMS = S.banked_cameras()


def run(a1, a2, draws=200):
    tmp = Path(tempfile.mkdtemp(dir=WORK, prefix='t_'))
    dirs = S.make_returns(tmp/'ret', a1, a2)
    args = R.parser().parse_args(['--k5', *map(str, dirs), '--out', str(tmp/'out'), '--draws', str(draws)])
    return R.run(args, log=lambda *a: None)


class Replay(unittest.TestCase):
    def test_identity_direct(self):
        """A2 == A1 == banked: every capture direct, zero difference, zero changed values, exactly."""
        nf = run(CAMS, CAMS)
        self.assertEqual(nf['reproduction']['served_equal'], nf['reproduction']['calls'])
        self.assertEqual(nf['reproduction']['rescored_equal'], 450)
        self.assertEqual(nf['reproduction']['rederived_equal'], 450)
        self.assertEqual(nf['substitution']['direct'], 52)
        for qt in R.CAMERA:
            e = nf['types'][qt]
            self.assertEqual(e['difference_pts'], 0.0)
            self.assertEqual(e['ci95'], [0.0, 0.0])
            self.assertEqual(e['changed_items'], 0)
            self.assertEqual(e['verdict'], 'no option A needed')
        for qt in R.UNMEASURED:
            self.assertEqual(nf['types'][qt]['items_on_changed_captures'], 0)

    def test_identity_relative(self):
        """A2 == A1 in another world frame (the banked cameras differ from A1): relative path, still zero."""
        moved = {k: (K, S.world(C), s*1.01) for k, (K, C, s) in CAMS.items()}
        nf = run(moved, moved)
        self.assertEqual(nf['substitution']['relative'], 52)
        for qt in R.CAMERA:
            self.assertEqual(nf['types'][qt]['difference_pts'], 0.0)
            self.assertEqual(nf['types'][qt]['changed_items'], 0)

    def test_one_capture_perturbed(self):
        """A large A1->A2 change on one capture changes items on that capture only."""
        nf0 = run(CAMS, CAMS, draws=10)
        caps = {}
        for it in nf0['items']:
            caps.setdefault(it['capture'], []).append(it)
        target = max(caps, key=lambda c: len(caps[c]))
        ref = {c['capture']: c['k'] for c in json.loads(Path(R.DEFAULTS['k5_reference']).read_text())['captures']}
        a1 = {k: (K, S.world(C), s) for k, (K, C, s) in CAMS.items()}
        a2 = dict(a1)
        K, C, s = a1[ref[target]]
        a2[ref[target]] = (K, S.perturb(C), s*1.3)
        nf = run(a1, a2, draws=10)
        changed = {it['capture'] for it in nf['items'] if it['banked_response'] != it['swapped_response']}
        self.assertEqual(changed, {target})
        n_changed = sum(it['banked_response'] != it['swapped_response'] for it in nf['items'])
        self.assertGreater(n_changed, len(caps[target])//2)  # pairs whose rounded print survives stay equal
        for it in nf['items']:
            if it['capture'] != target:
                self.assertEqual(it['replay_score'], it['banked_score'])
                self.assertIsNone(it['new_answer'])
        self.assertTrue(any(it['new_answer'] is not None for it in nf['items'] if it['capture'] == target))
        for qt in R.UNMEASURED:
            self.assertLessEqual(nf['types'][qt]['captures_tower_changed'], 1)
        self.assertEqual(nf0['types']['object_abs_distance']['captures_tower_changed'], 0)


class Units(unittest.TestCase):
    def test_relative_math(self):
        """(ii) on banked = W A1 reproduces A2's relative poses."""
        rng = np.random.default_rng(0)

        def rigid(n):
            out = np.tile(np.eye(4), (n, 1, 1))
            for k in range(n):
                q, _ = np.linalg.qr(rng.normal(size=(3, 3)))
                out[k, :3, :3] = q*np.sign(np.linalg.det(q))
                out[k, :3, 3] = rng.normal(size=3)
            return out
        A1 = rigid(8)
        A2 = A1@rigid(8)
        B = S.world(A1, 33, (1, 2, 3))
        z = dict(camera_to_world=B, K=np.tile(np.eye(3), (8, 1, 1)), scale=2.0)
        mode, K, C, s = R.swapped_arrays(z, dict(cu=A1.tolist(), K=z['K'].tolist(), s=1.0),
                                         dict(cu=A2.tolist(), K=z['K'].tolist(), s=1.1))
        self.assertEqual(mode, 'relative')
        self.assertAlmostEqual(s, 2.2)
        for i in range(8):
            for j in range(8):
                np.testing.assert_allclose(np.linalg.inv(C[i])@C[j], np.linalg.inv(A2[i])@A2[j], atol=1e-9)

    def test_reextract(self):
        item = dict(type='camera_displacement', text='x <move from=1 to=2>\n...</think>\n\n2.11<|im_end|>', task={})
        old = 'dx = +1.94 m, dy = +0.05 m, dz = +0.82 m, distance = 2.11 m'
        new = 'dx = +1.00 m, dy = +0.05 m, dz = +0.82 m, distance = 1.29 m'
        self.assertEqual(R.reextract(item, old, new), '1.29')
        self.assertEqual(R.with_answer(item['text'], '1.29'), 'x <move from=1 to=2>\n...</think>\n\n1.29<|im_end|>')
        item = dict(type='camera_rotation', text='</think>\n\n41<|im_end|>', task={})
        self.assertEqual(R.reextract(item, 'turn = +41 deg', 'turn = -7 deg'), '-7')
        text = ('Scoring each option by the matching component: backward = -dz = 1.12 m; right = dx = 1.31 m; '
                'left = -dx = -1.31 m; forward = dz = -1.12 m.\n\nThe largest is right. That matches option B.\n</think>\n\nB<|im_end|>')
        item = dict(type='camera_movement_direction', text=text,
                    task=dict(options=['A. backward', 'B. right', 'C. left', 'D. forward']))
        self.assertEqual(R.reextract(item, '', 'dx = -1.31 m, dy = +0.00 m, dz = +0.20 m, distance = 1.33 m'), 'C')
        self.assertEqual(R.reextract(item, '', 'dx = +0.10 m, dy = +0.00 m, dz = +2.00 m, distance = 2.00 m'), 'D')

    def test_rule_edges(self):
        A, N = 'OPTION_A before the next rule read on this type', 'no option A needed'
        self.assertEqual(R.verdict(True, 0.5, 0, 150), A)
        self.assertEqual(R.verdict(True, -0.5, 0, 150), A)
        self.assertEqual(R.verdict(True, 0.4999, 0, 150), N)
        self.assertEqual(R.verdict(True, 0.0, 5, 100), N)       # exactly 5% does not trigger
        self.assertEqual(R.verdict(True, 0.0, 6, 100), A)       # above 5% triggers
        self.assertEqual(R.verdict(True, 0.0, 8, 150), A)       # 5.33%
        self.assertEqual(R.verdict(True, 0.0, 7, 150), N)       # 4.67%
        self.assertTrue(R.verdict(False, 2.0, 50, 100).startswith('no registered rule read'))

    def test_bootstrap_matches_plan_convention(self):
        """Same draws and intervals as round7_common.Bootstrap (R8's 10,000-draw room bootstrap, seed 20261120)."""
        rng = np.random.default_rng(1)
        rows = [dict(room='r%d' % (i % 7), a=float(rng.random() < .6)*100, b=float(rng.random() < .5)*100) for i in range(40)]
        mine = R.Bootstrap([r['room'] for r in rows]).contrast(rows, 'a', 'b')
        code = ('import importlib.util,json,sys;s=importlib.util.spec_from_file_location("r7",%r);m=importlib.util.module_from_spec(s);'
                's.loader.exec_module(m);rows=json.loads(sys.stdin.read());'
                'B=m.Bootstrap({i:dict(task=dict(room=r["room"])) for i,r in enumerate(rows)});'
                'A=[dict(room=r["room"],v=r["a"]) for r in rows];C=[dict(room=r["room"],v=r["b"]) for r in rows];'
                'print(json.dumps(B.contrast(A,C,"v")))') % str(ROUND7)
        theirs = json.loads(subprocess.run([sys.executable, '-I', '-B', '-c', code], input=json.dumps(rows),
                                           capture_output=True, text=True, check=True).stdout)
        self.assertAlmostEqual(mine['mean'], theirs['mean'], places=12)
        np.testing.assert_allclose(mine['ci95'], theirs['ci95'], atol=1e-12)

    def test_receipt_tamper(self):
        tmp = Path(tempfile.mkdtemp(dir=WORK, prefix='t_'))
        d = S.write_group(tmp/'g0', 0, [])
        p = d/'50.json'
        p.write_bytes(p.read_bytes().replace(b'"complete":true', b'"complete":false'))
        with self.assertRaises(ValueError):
            R.authenticated(d)


if __name__ == '__main__':
    unittest.main(verbosity=2)
