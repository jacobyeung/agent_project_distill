"""K5 local tests: scorer on synthetic records, installer, supervisor pins, and the stub dry-run properties."""
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent/'work'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


S = module('score_k5', ROOT/'score_k5.py')


def sha(a):
    a = np.ascontiguousarray(np.asarray(a))
    return dict(sha256=hashlib.sha256(a.tobytes()).hexdigest(), dtype=str(a.dtype), shape=list(a.shape))


def record(key, position, index, shift=0.0, turn=0.0, scale=2.0, seconds=1.0, rebuilt=False):
    K = np.tile(np.array([[500., 0, 320], [0, 500., 240], [0, 0, 1]]), (32, 1, 1))
    cu = np.tile(np.eye(4), (32, 1, 1))
    cu[:, 0, 3] = np.arange(32)*0.1
    cu[5, 0, 3] += shift
    a = math.radians(turn)
    cu[7, :3, :3] = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    cm = cu.copy()
    cm[:, :3, 3] *= scale
    tower = np.concatenate([cu.ravel(), [shift, turn]])
    shas = {n: sha(tower+i) for i, n in enumerate(('p9', 'd', 'dc', 'pt'))}
    shas.update(K=sha(K), cm=sha(cm), cu=sha(cu), s=sha(np.float64(scale)))
    return dict(status='ok', k=key, n=64, seconds=seconds, rebuilt=rebuilt, K=K.tolist(), cm=cm.tolist(),
                cu=cu.tolist(), s=scale, sha=shas, position=position, index=index)


KEYS = ['k0', 'k1x', 'k2x']


def reference(path):
    caps = []
    for i, (k, ds) in enumerate(zip(KEYS, ('ScanNet', 'ScanNet++', 'ARKit'))):
        caps.append(dict(k=k, dataset=ds, position=i, frames=64, dump=None))
    r = record('k0', 0, 0)
    fixed = np.asarray(r['cu'])
    fixed[:, :3, 3] *= 2.0
    caps[0]['dump'] = dict(K=r['K'], c2w_unscaled=r['cu'], c2w_metric=fixed.tolist(), scale=2.0,
                           depth_sha256='0'*64)
    Path(path).write_text(json.dumps(dict(captures=caps)))


def arm(a, reverse, edits=None, drop=None, seconds=1.0):
    order = list(range(3))
    if reverse:
        order.reverse()
    order.append(0)
    recs = []
    for pos, x in enumerate(order):
        kw = dict(seconds=seconds)
        if edits and (x, pos == 3) in edits:
            kw.update(edits[(x, pos == 3)])
        if drop == x and pos != 3:
            continue
        recs.append(record(KEYS[x], pos, x, **kw))
    return dict(arm=a, status='ok', complete=True, records=recs, wall_seconds=10.0, warn_only=False)


def results(arms):
    return [dict(group=0, arms=arms[:2]), dict(group=1, arms=arms[2:])]


class Scorer(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(dir=WORK, prefix='t_'))
        self.ref = self.tmp/'ref.json'
        reference(self.ref)

    def test_equal(self):
        v = S.score(results([arm(0, 0), arm(1, 1), arm(2, 0), arm(3, 1)]), self.ref)
        self.assertEqual(v['answers']['q1_deterministic_orders_bit_equal'], 'yes')
        self.assertEqual(v['answers']['default_orders'], 'orders agree')
        self.assertEqual(v['D1_vs_D2']['summary']['all']['bit_equal'], 3)
        self.assertTrue(all(v['recompute'][n]['bit'] for n in S.ARM_NAMES))
        self.assertEqual(v['A1_vs_rank1']['summary']['all']['K_bit'], 1)
        self.assertEqual(v['A1_vs_rank1']['summary']['all']['metric_fixed_bit'], 1)
        self.assertAlmostEqual(v['answers']['q2_cost_ratio_of_means'], 1.0)

    def test_perturbed(self):
        d2 = arm(3, 1, edits={(2, False): dict(shift=0.01), (1, False): dict(turn=1.0)})
        a2 = arm(1, 1, edits={(0, True): dict(scale=2.002)})
        v = S.score(results([arm(0, 0), a2, arm(2, 0, seconds=1.2), d2]), self.ref)
        self.assertEqual(v['answers']['q1_deterministic_orders_bit_equal'], 'no')
        s = v['D1_vs_D2']['summary']
        self.assertEqual(s['all']['bit_equal'], 1)
        self.assertAlmostEqual(s['ARKit']['translation_m']['max'], 0.02, places=9)
        self.assertAlmostEqual(s['ScanNet++']['rotation_deg']['max'], 1.0, places=6)
        self.assertFalse(v['recompute']['A2']['bit'])
        self.assertAlmostEqual(v['recompute']['A2']['scale_rel'], 0.001, places=9)
        self.assertEqual(v['answers']['default_orders'], 'orders agree')
        self.assertAlmostEqual(v['answers']['q2_cost_ratio_of_means'], 1.1, places=9)

    def test_missing_capture(self):
        v = S.score(results([arm(0, 0), arm(1, 1), arm(2, 0), arm(3, 1, drop=2)]), self.ref)
        self.assertEqual(v['D1_vs_D2']['status'], 'incomplete')
        self.assertEqual(v['D1_vs_D2']['summary']['ARKit']['missing'], 1)
        self.assertEqual(v['answers']['q1_deterministic_orders_bit_equal'], 'incomplete')

    def test_missing_arm(self):
        v = S.score([dict(group=0, arms=[arm(0, 0), arm(2, 0)])], self.ref)
        self.assertEqual(v['D1_vs_D2']['status'], 'missing arm')
        self.assertEqual(v['answers']['q1_deterministic_orders_bit_equal'], 'incomplete')

    def test_rebuilt_excluded_from_cost(self):
        a1 = arm(0, 0, edits={(0, False): dict(seconds=30.0, rebuilt=True)})
        v = S.score(results([a1, arm(1, 1), arm(2, 0), arm(3, 1)]), self.ref)
        self.assertEqual(v['cost']['all']['A']['n'], 5)
        self.assertEqual(v['cost']['rebuild_seconds']['A1'], [30.0])

    def test_receipt(self):
        d = self.tmp/'r'
        d.mkdir()
        raw = json.dumps(dict(group=0, arms=[])).encode()
        (d/'50.json').write_bytes(raw)
        (d/'50.1.json').write_text(json.dumps(dict(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw), group=0, job='7')))
        (d/'120.txt').write_text('7 COMPLETED|n|00:01:00\n')
        self.assertEqual(S.authenticated(d, 0)['group'], 0)
        (d/'50.json').write_bytes(raw+b' ')
        with self.assertRaises(ValueError):
            S.authenticated(d, 0)
        (d/'50.json').write_bytes(raw)
        (d/'120.txt').write_text('8 COMPLETED|n|00:01:00\n')
        with self.assertRaises(ValueError):
            S.authenticated(d, 0)


class Installer(unittest.TestCase):
    def body(self, dest):
        script = (ROOT/'o_place.sh').read_text()
        body = script.split("<<'PY'\n", 1)[1].rsplit('\nPY', 1)[0]
        token = (ROOT/'TOKEN').read_text().strip()
        return body.replace(repr('/project/community/jjyeung/'+token), repr(str(dest)))

    def run_body(self, body):
        return subprocess.run(['/usr/bin/python3', '-I', '-s', '-B', '-'], input=body.encode(), capture_output=True)

    def test_install_and_refuse(self):
        tmp = Path(tempfile.mkdtemp(dir=WORK, prefix='inst_'))
        dest = tmp/'x'
        body = self.body(dest)
        r = self.run_body(body)
        self.assertEqual(r.returncode, 0, r.stderr)
        build = json.loads((ROOT/'BUILD.json').read_text())
        self.assertEqual(int(r.stdout), build['placed']['file_bytes'])
        for n in build['placed']['files']:
            self.assertEqual((dest/n).read_bytes(), (ROOT/n).read_bytes())
        self.assertEqual(oct(dest.stat().st_mode & 0o777), '0o700')
        r = self.run_body(body)
        self.assertEqual((r.returncode, r.stderr.strip()), (1, b'E44'))
        bad = body.replace('ASSETS=\'H4sI', 'ASSETS=\'H5sI', 1)
        r = self.run_body(bad.replace(repr(str(dest)), repr(str(tmp/'y'))))
        self.assertEqual(r.returncode, 1)
        self.assertIn(r.stderr.strip(), (b'E40', b'E49'))
        self.assertFalse((tmp/'y').exists())

    def test_pins_refuse_tamper(self):
        tmp = Path(tempfile.mkdtemp(dir=WORK, prefix='pin_'))
        token = (ROOT/'TOKEN').read_text().strip()
        p = tmp/token
        p.mkdir()
        for n in ('0.py', '1.json', '2.py', '3.json', '8.gz', '9.py'):
            shutil.copy2(ROOT/n, p/n)
        entry = module('entry_pin', p/'0.py')
        c = entry.verify(p)
        self.assertEqual(len(c['x3']), 84)
        self.assertTrue(all(t*1.5 <= 3000 for t in c['xt']))
        with (p/'2.py').open('a') as f:
            f.write('\n')
        with self.assertRaises(ValueError):
            entry.verify(p)


class DryRun(unittest.TestCase):
    """Properties of the delivered supervisor and worker, read from the stub dry run."""
    @classmethod
    def setUpClass(cls):
        cls.dry = json.loads((ROOT/'DRY_K5.json').read_text())
        cls.cfg = json.loads((ROOT/'1.json').read_text())

    def group(self, run, g):
        token = (ROOT/'TOKEN').read_text().strip()
        p = Path(self.dry[run]['work'])/token
        return p, S.authenticated(p, g)

    def test_codes(self):
        for run in ('plain', 'refuse'):
            self.assertEqual(self.dry[run]['codes'], dict(cpu=0, pre0=0, gpu0=0, pre1=0, gpu1=0), run)

    def test_cpu_unit(self):
        p, _ = self.group('plain', 0)
        cpu = json.loads((p/'4.1.json').read_text())
        a = cpu['arms'][0]
        total = sum(r['n'] for r in self.cfg['x3'])
        self.assertEqual((a['decoded_frames'], cpu['frames_verified']), (total, total))
        self.assertEqual(a['order'], [0])
        self.assertTrue(json.loads((p/'4.json').read_text())['passed'])

    def test_order_recompute_fresh(self):
        n = len(self.cfg['x3'])
        pids = set()
        for g in (0, 1):
            _, r = self.group('plain', g)
            self.assertTrue(r['complete'])
            self.assertEqual([a['arm'] for a in r['arms']], self.cfg['xq'][g])
            for a in r['arms']:
                reverse = self.cfg['xr'][a['arm']][0]
                want = (list(reversed(range(n))) if reverse else list(range(n)))+[0]
                self.assertEqual(a['order'], want)
                self.assertEqual([x['index'] for x in a['records']], want)
                self.assertEqual(a['records'][-1]['sha'], next(x for x in a['records'] if x['index'] == 0)['sha'])
                pids.add(a['pid'])
        self.assertEqual(len(pids), 4)

    def test_switches(self):
        for g in (0, 1):
            _, r = self.group('plain', g)
            for a in r['arms']:
                sw = a['switches']
                self.assertFalse(sw['cuda_initialized_at_set'])
                self.assertFalse(sw['after']['cuda_initialized'])
                if a['det']:
                    self.assertTrue(sw['after']['cudnn_deterministic'] and sw['after']['algorithms'])
                    self.assertFalse(sw['after']['cudnn_auto'])
                    self.assertEqual(sw['after']['env_CUBLAS_WORKSPACE_CONFIG'], ':4096:8')
                    self.assertEqual(sw['after']['matmul_tf32'], sw['before']['matmul_tf32'])
                    self.assertFalse(a['warn_only'])
                else:
                    self.assertFalse(sw['after']['algorithms'])
                    self.assertIsNone(sw['after']['env_CUBLAS_WORKSPACE_CONFIG'])
                    self.assertEqual(sw['set'], [])

    def test_refusal_relaunch(self):
        for g in (0, 1):
            _, r = self.group('refuse', g)
            self.assertTrue(r['complete'])
            d = next(a for a in r['arms'] if a['det'])
            self.assertTrue(d['warn_only'])
            self.assertEqual(d['strict_attempt']['exit_code'], 3)
            self.assertEqual([bytes.fromhex(o).decode() for o in d['strict_attempt']['ops']], ['index_add_cuda_'])
            self.assertEqual([bytes.fromhex(o).decode() for o in d['warned_ops']], ['index_add_cuda_'])
            a = next(a for a in r['arms'] if not a['det'])
            self.assertNotIn('strict_attempt', a)

    def test_scores_and_size(self):
        results = [self.group('plain', g)[1] for g in (0, 1)]
        v = S.score(results, ROOT/'REFERENCE_K5.json')
        self.assertEqual(v['answers']['q1_deterministic_orders_bit_equal'], 'yes')
        self.assertEqual(v['A1_vs_rank1']['summary']['all']['compared'], 60)
        for g in (0, 1):
            p, _ = self.group('plain', g)
            self.assertLess((p/('5%d.json' % g)).stat().st_size, 6_000_000)


if __name__ == '__main__':
    unittest.main(verbosity=2)
