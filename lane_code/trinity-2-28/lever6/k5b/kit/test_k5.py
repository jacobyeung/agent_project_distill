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
import time
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parent
WORK = Path('/scratch/jjyeung/orch_n30/lever6/k5b/work')


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


FIX = Path('/scratch/jjyeung/orch_n30/lever1_c/r1_fixtures_old/real_cl2opr5g/j')
OLD0 = Path('/scratch/jjyeung/orch_n30/lever5/k5/work/old0')
# Package under test: this kit by default; K5_ENTRY=<dir> runs the same test on another kit's 0.py.
ENTRY = Path(os.environ.get('K5_ENTRY', str(ROOT)))


def package_modules():
    """The placed package's own common and namespace modules (the code 0.py's stage imports)."""
    sys.path.insert(0, str(OLD0))
    common = importlib.import_module('orchard_h10.common')
    return common, common.template()[1]


class LaunchPath(unittest.TestCase):
    """Run 0.py's real launch path: its own root, its stage hook stubbed with what staging produces
    (bwrap, sj, m/ap; no fsw), the package's real namespace argv and /usr/bin/bwrap, CPU unit."""

    def test_namespace_starts(self):
        tmp = Path(tempfile.mkdtemp(dir=WORK, prefix='ns_'))
        token = json.loads((ENTRY/'1.json').read_text())['x0']
        p = tmp/token
        p.mkdir()
        for n in ('0.py', '1.json', '2.py', '3.json', '8.gz', '9.py'):
            shutil.copy2(ENTRY/n, p/n)
        entry = module('entry_ns', p/'0.py')
        c = entry.verify(p)
        c['x3'] = []    # the fixture holds no frames
        common, job = package_modules()
        roots = []
        hx = lambda v: v.encode().hex()

        def stage(c, root):
            """What staging leaves behind: the namespace tool, sj, m/ap and the served code (no fsw)."""
            roots.append(root)
            (root/'bwrap').symlink_to('/usr/bin/bwrap')
            (root/'sj').symlink_to(FIX/'sj')
            (root/'m').mkdir()
            (root/'m/ap').symlink_to(FIX/'m/ap')
            # The fixture's code differs from the pins, so the pinned served code goes under root/p
            # (inside /tmp, which the namespace binds), as 0.py's own stage extracts it there.
            for d in ('tree', 'b'):
                shutil.copytree(OLD0/d, root/'p'/d, ignore=shutil.ignore_patterns('__pycache__'))
            site = bytes.fromhex(c['x8'][2]).decode()
            c['x8'] = [hx(str(root/'p/tree')), hx(str(root/'p/b')), hx(site)]
            c['x9'] = [[hx(str(root/'p'/bytes.fromhex(q).decode().partition('/p/')[2])), h] for q, h in c['x9']]
            return common, job, [bytes.fromhex(x).decode() for x in c['xf']]
        entry.stage = stage
        entry.MODES = dict(g='s', c='t')
        saved = {k: os.environ.get(k) for k in ('SLURM_JOB_ID', 'SLURM_JOB_END_TIME')}
        os.environ.update(SLURM_JOB_ID='9990002', SLURM_JOB_END_TIME=str(time.time()+3000))
        try:
            result = entry.execute(p, c, 0)
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        a = result['arms'][0]
        report = dict(entry=str(ENTRY/'0.py'), root=str(roots[0]), status=a['status'], exit_code=a['exit_code'],
                      wall_seconds=round(a['wall_seconds'], 3), child=a.get('child'),
                      error=a.get('error'), threads=(a.get('switches') or {}).get('threads'),
                      err_records=(p/'4.err').read_text() if (p/'4.err').exists() else '')
        print('LAUNCH', json.dumps(report), file=sys.stderr)
        # 2.py ran inside the namespace: it wrote its own record and imported the pinned runtime.
        self.assertNotEqual(a['status'], 'missing', report)
        self.assertIn('switches', a, report)
        self.assertNotEqual(a['pid'], os.getpid())
        self.assertNotIn((a.get('child') or {}).get('c'), ('B1', 'B2', 'N1', 'N2'), report)
        # The worker got past its whole set-up (runtime, pinned served code, plane) and stopped only
        # at the unit choice, because this run has no captures.
        self.assertEqual(a['switches']['threads'], len(os.sched_getaffinity(0)), report)
        self.assertEqual(a['decoded_frames'], 0, report)


class Diagnostics(unittest.TestCase):
    def setUp(self):
        self.d = module('diag', ROOT/'9.py')

    def test_classes(self):
        c = self.d.classify
        self.assertEqual(c(b"bwrap: Can't find source path /tmp/a1/fsw: No such file or directory", b'', 1), 'B1')
        self.assertEqual(c(b'bwrap: execvp /x/py: No such file or directory', b'', 1), 'N1')
        self.assertEqual(c(b'/x/py: line 2: /y/python: No such file or directory', b'', 127), 'N1')
        self.assertEqual(c(b'Traceback (most recent call last):\n  File "x"', b'FileNotFoundError: No such file or directory', 1), 'P1')
        self.assertEqual(c(b'bwrap: Creating new namespace failed', b'', 1), 'B2')
        self.assertEqual(c(b'', b'', 1), 'Z0')
        self.assertEqual(c(b'', b'', -9), 'S1')
        self.assertEqual(c(b'E99\n', b'E99\n', 1), 'W1')
        self.assertEqual(c(b'odd', b'odd', 1), 'X0')

    def test_capture_keeps_class_only(self):
        proc = self.d.capture(['/usr/bin/bwrap', '--bind', '/nonexistent_k5', '/x', '/bin/true'], keep=4096)
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(proc.kept['c'], 'B1')
        self.assertEqual(set(proc.kept), {'c', 'b'})

    def test_no_record_gets_code(self):
        """An arm that exits nonzero without an error record leaves an E94 record with class, exit and time."""
        tmp = Path(tempfile.mkdtemp(dir=WORK, prefix='e94_'))
        (tmp/'p').mkdir()
        root = tmp/'r'
        root.mkdir()
        for n in ('0.py', '9.py'):
            shutil.copy2(ROOT/n, tmp/'p'/n)
        entry = module('entry_e94', tmp/'p'/'0.py')

        class J:
            @staticmethod
            def namespace(root):
                return ['/usr/bin/bwrap', '--bind', str(root/'fsw_absent'), '/x', '--']

        class C:
            @staticmethod
            def opaque(values):
                pass
        v = entry.launch(dict(xj='/bin/true'), root, C, J, [None]*6+['', 'namespace', 'opaque'], 2, 't', 1,
                         dict(PATH='/usr/bin:/bin'), time.time()+600, tmp/'p', 0)
        self.assertEqual(v['status'], 'missing')
        self.assertEqual(v['child']['c'], 'B1')
        rec = json.loads((tmp/'p'/'4.err').read_text())
        self.assertEqual((rec['code'], rec['c'], rec['status']), ('E94', 'B1', v['exit_code']))
        self.assertLess(rec['s'], 60)

    def test_cards_parse(self):
        entry = module('entry_cards', ROOT/'0.py')
        one = entry.parse_cards('0, GPU-1a2b3c4d-0000-1111-2222-333344445555, 00000000:1B:00.0\n', '0')
        self.assertEqual((one['uuid'], one['bus']), ('GPU-1a2b3c4d-0000-1111-2222-333344445555', '00000000:1B:00.0'))
        two = entry.parse_cards('0, GPU-aa, 00000000:1B:00.0\n3, GPU-bb, 00000000:9C:00.0\n', '3')
        self.assertEqual(two['uuid'], 'GPU-bb')
        self.assertIsNone(entry.parse_cards('', '0')['uuid'])


class SlurmScripts(unittest.TestCase):
    """Fetch scripts tolerate a purged job id; o_sub1.sh pins only to a COMPLETED job 0."""

    def run_head(self, name, stop, queue, state):
        tmp = Path(tempfile.mkdtemp(dir=WORK, prefix='sl_'))
        b = tmp/'bin'
        b.mkdir()
        q = ('echo "slurm_load_jobs error: Invalid job id specified" >&2; exit 1' if queue is None
             else 'echo %s' % queue if queue else 'exit 0')
        (b/'squeue').write_text('#!/bin/bash\n'+q+'\n')
        (b/'sacct').write_text('#!/bin/bash\necho "%s"\n' % state)
        for f in ('squeue', 'sacct'):
            (b/f).chmod(0o755)
        for n in ('6.txt', '70.txt') + (() if name == 'o_sub1.sh' else ('71.txt',)):
            (tmp/n).write_text('174236\n')
        lines = (ROOT/name).read_text().split('\n')
        cut = next(i for i, l in enumerate(lines) if l.startswith(stop))
        text = '\n'.join(l if not l.startswith('P=') else 'P='+str(tmp) for l in lines[:cut+1])+'\necho REACHED\n'
        r = subprocess.run(['bash', '-c', text], capture_output=True, text=True,
                           env=dict(PATH=str(b)+':/usr/bin:/bin'))
        return r.returncode, r.stdout.strip(), r.stderr.strip()

    def test_fetch_purged(self):
        for name in ('o_cfetch.sh', 'o_fetch0.sh', 'o_fetch1.sh'):
            self.assertEqual(self.run_head(name, 'case', None, 'FAILED|n1|00:03:56')[:2], (0, 'REACHED'), name)
            self.assertEqual(self.run_head(name, 'case', '', 'COMPLETED|n1|00:30:00')[:2], (0, 'REACHED'), name)
            self.assertNotEqual(self.run_head(name, 'case', '174236', 'RUNNING|n1|00:01:00')[0], 0, name)
            self.assertNotEqual(self.run_head(name, 'case', None, 'RUNNING|n1|00:01:00')[0], 0, name)

    def test_sub1_requires_completed(self):
        code, out, _ = self.run_head('o_sub1.sh', '[[ "$node"', None, 'COMPLETED|orchard-community-2')
        self.assertEqual((code, out), (0, 'REACHED'))
        for state in ('FAILED|orchard-community-2', 'NODE_FAIL|orchard-community-2', 'TIMEOUT|n1'):
            code, out, err = self.run_head('o_sub1.sh', '[[ "$node"', None, state)
            self.assertEqual((code, out, err), (1, '', 'E51'), state)
        self.assertNotEqual(self.run_head('o_sub1.sh', '[[ "$node"', '174236', 'COMPLETED|n1')[0], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
