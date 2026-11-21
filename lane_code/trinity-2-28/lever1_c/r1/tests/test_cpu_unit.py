"""CPU real unit: production worker path, time guard and memory guard, in p1cpu and the pinned env.

Each scenario runs the delivered operator's cpu_unit (the Orchard CPU check's
step after rehearsal), which launches the delivered numeric entry (action 3,
g.w.run) through the operator prefix seam with tests/cpu_unit_fixture.py
doubles (tiny production-architecture carrier and G3T components; see that
file). Served PNGs come from the authenticated local a2.tar through production
stage_capture. The pinned scenarios run the pinned Orchard interpreter
(transformers 5.19.0, torch 2.13.0) inside the production-shaped bwrap
namespace of r1_fixtures_old/real_cl2opr5g. Writes out/CPU_UNIT_CHECKS.json.
"""
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tarfile
import time
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import cpu_unit as CU
FIXTURES = HERE.parent/'r1_fixtures_old'
A2 = Path('/scratch/jjyeung/orch_n30/reads228/dl/a2.tar')
PINNED = FIXTURES/'real_cl2opr5g/j'
# The production interpreter: pinned venv plus the pinned overlay (inputs['python']).
PY = '/scratch/jjyeung/b01ec87a6f29b/d/v/py'
OVERLAY = '/scratch/jjyeung/b01ec87a6f29b/d/v/site'
EVIDENCE = dict(cases=[])
# Tiny-fixture seconds for the admission arithmetic; production uses cpu_unit.ESTIMATES.
TINY = dict(first_model={'32': 10, '64': 40}, load=20, prefill=10, margin=5)


def sha(data):return hashlib.sha256(data).hexdigest()


def unwrap(value):
    return json.loads(bytes.fromhex(value['a0'])) if isinstance(value, dict) and set(value) == {'a0'} else value


def namespace(work):
    """Production namespace shape (orchard_job.namespace) over the local pinned extraction."""
    R = PINNED
    argv = ['/usr/bin/bwrap']
    for name in ('usr', 'bin', 'sbin', 'lib', 'lib64', 'etc', 'opt', 'run', 'sys'):
        path = Path('/')/name
        if path.is_symlink():argv += ['--symlink', os.readlink(path), str(path)]
        elif path.exists():argv += ['--ro-bind', str(path), str(path)]
    argv += ['--dev-bind', '/dev', '/dev', '--proc', '/proc', '--dir', '/tmp',
             '--dir', '/scratch', '--bind', str(R/'sj'), '/scratch/jjyeung',
             '--bind', str(R/'fsw'), '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung',
             '--dir', '/lustre', '--bind', str(R/'m/ap'), '/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap',
             '--ro-bind', str(R/'sj/uv-python/cpython-3.12.13-linux-x86_64-gnu'), '/home/jyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu',
             '--dir', '/home/jjyeung',
             # Test harness only: the fixture work tree, the tests and the local served-PNG archive.
             '--bind', str(work), str(work), '--ro-bind', str(HERE/'tests'), str(HERE/'tests'),
             '--ro-bind', str(A2), str(A2), '--die-with-parent', '--chdir', str(work)]
    return argv


class Case:
    def __init__(self, pinned, unit, env=None):
        self.work = FIXTURES/('u'+secrets.token_hex(6)); self.work.mkdir()
        self.pinned = pinned
        raw = (HERE/'out/delivery.tgz').read_bytes()
        with tarfile.open(HERE/'out/delivery.tgz') as t:
            outer = {m.name: t.extractfile(m).read() for m in t if m.isfile()}
        self.delivery = sha(raw)
        self.p = self.work/'p'; self.p.mkdir()
        import io
        with tarfile.open(fileobj=io.BytesIO(outer['0.tgz'])) as t:
            for m in t:
                if m.isfile():
                    dest = self.p/m.name; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(t.extractfile(m).read())
        self.operator = self.work/'7.py'; self.operator.write_bytes(outer['a/6.py'])
        self.nine = outer['a/9.py']
        python = PY if pinned else sys.executable
        self.python = python
        self.env = dict(PATH='/usr/bin:/bin', HOME=str(self.work), USER='a', CUDA_VISIBLE_DEVICES='',
                        OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', **(env or {}))
        build = [python, '-I', '-s', '-B', str(HERE/'tests/cpu_unit_fixture.py'), 'build',
                 str(self.work), str(self.p), str(A2), OVERLAY if pinned else '']
        self.run(build, 'build')
        now = time.time()
        config = dict(package=str(self.p), output=str(self.work/'r'), python=python, export=str(self.work/'d/e'),
                      binding=str(self.work/'d/binding.json'), export_pin=str(self.work/'d/6.json'),
                      settings=str(self.work/'d/settings.json'), plan_sha256='0'*64, inputs_sha256='0'*64,
                      operator_sha256=sha(outer['a/6.py']), device='cpu', measure_memory=True,
                      prefix=[python, '-I', '-s', '-B', str(HERE/'tests/cpu_unit_fixture.py')],
                      cpu_unit=dict(dict(end=now+unit.pop('stop', 900), kill_at=now+unit.pop('kill', 930), allocation_end=now+1200,
                                         threads=2, slurm_cpus='2', address_space=CU.ADDRESS_SPACE,
                                         guard_bytes=CU.GUARD_BYTES, estimates=TINY), **unit))
        (self.work/'a').mkdir()
        (self.work/'a/1.json').write_text(json.dumps(config))
        self.config = config
        started = time.monotonic()
        self.run([python, '-I', '-s', '-B', str(HERE/'tests/cpu_unit_driver.py'), str(self.p), str(self.operator),
                  str(self.work/'a/1.json'), str(self.work/'out.json')], 'driver')
        self.seconds = time.monotonic()-started
        self.result = unwrap(json.loads((self.work/'out.json').read_text()))

    def run(self, argv, name):
        if self.pinned:argv = namespace(self.work)+argv
        done = subprocess.run(argv, env=self.env, cwd=self.work, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (self.work/(name+'.log')).write_bytes(done.stdout)
        if done.returncode:raise AssertionError((name, done.stdout.decode(errors='replace')[-6000:]))

    def decoded(self, name):
        path = self.work/'r/metadata'/name
        return unwrap(json.loads(path.read_text()))


def receipt_check(case, unit):
    """The delivered a/9.py real-unit assertions on the assembled CPU.json fields."""
    text = case.nine.decode()
    start = text.index("u=c['real_unit']"); stop = text.index("print('All CPU receipt checks passed')")
    exec(compile(text[start:stop], 'a/9.py', 'exec'), dict(c=dict(real_unit=unit, real_unit_passed=unit['passed'])))


class CpuUnitTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        EVIDENCE.update(passed=bool(EVIDENCE['cases']) and all(c['passed'] for c in EVIDENCE['cases']),
                        delivery_sha256=sha((HERE/'out/delivery.tgz').read_bytes()),
                        scope=__doc__.strip().replace('\n', ' '),
                        limits=dict(address_space_bytes=CU.ADDRESS_SPACE, guard_bytes=CU.GUARD_BYTES,
                                    stop_before_end_s=CU.UNIT_STOP_S, kill_before_end_s=CU.UNIT_KILL_S),
                        estimates=CU.ESTIMATES)
        (HERE/'out/CPU_UNIT_CHECKS.json').write_text(json.dumps(EVIDENCE, indent=2, default=str)+'\n')

    def record(self, name, case, **extra):
        unit = case.result['unit'] or {}
        entry = dict(name=name, passed=False, pinned=case.pinned, work=str(case.work), seconds=case.seconds,
                     process=case.result['process'], unit={k: unit.get(k) for k in
                     ('passed', 'status', 'failure', 'error', 'admission', 'capture_index', 'stages', 'checks',
                      'environment', 'parity', 'peak_rss_bytes', 'seconds')}, **extra)
        EVIDENCE['cases'].append(entry)
        return entry, unit

    def clean(self, name, pinned, reason, dense):
        case = Case(pinned, {})
        if reason == 'time_guard':
            # Remaining time fits a 32-frame capture but not the 64-frame first capture.
            est = TINY
            first = 1.25*(est['first_model']['64']+est['load']+est['prefill'])+est['margin']
            cheap = 1.25*(est['first_model']['32']+est['load']+est['prefill'])+est['margin']
            case = Case(pinned, dict(stop=(first+cheap)/2, kill=(first+cheap)/2+30))
        entry, unit = self.record(name, case)
        self.assertTrue(unit.get('passed'), json.dumps(unit, default=str)[-4000:])
        self.assertEqual(unit['admission']['reason'], reason)
        self.assertEqual(unit['stages'][0]['dense'], dense)
        self.assertEqual([s['name'] for s in unit['stages']], ['bind', 'first_model', 'load', 'prefill', 'record'])
        self.assertEqual(unit['environment']['threads'], 2)
        self.assertEqual(unit['environment']['address_space_bytes'], CU.ADDRESS_SPACE)
        self.assertIn('torch.bfloat16', unit['stages'][2]['dtypes'])
        process = case.result['process']
        self.assertEqual((process['returncode'], process['stopped'], process['memory']['over'], process['action']), (0, None, False, 3))
        unit['process'] = process
        receipt_check(case, unit)
        # The capture record is production's: one float16 plane of 32x51x51 per capture.
        self.assertEqual(case.decoded('6.json')['completed'], 1)
        self.assertTrue((case.work/'c/0.gz').is_file())
        entry.update(passed=True, transformers=unit['environment']['transformers'], torch=unit['environment']['torch'])
        return unit

    def test_local_first_unit(self):self.clean('local_first_unit', False, 'first_unit', 64)
    def test_local_time_guard(self):self.clean('local_time_guard', False, 'time_guard', 32)

    def test_pinned_first_unit(self):
        unit = self.clean('pinned_first_unit', True, 'first_unit', 64)
        self.assertEqual((unit['environment']['transformers'], unit['environment']['torch'].split('+')[0]), ('5.19.0', '2.13.0'))

    def test_pinned_time_guard(self):self.clean('pinned_time_guard', True, 'time_guard', 32)

    def test_deadline_kill_writes_receipt(self):
        case = Case(False, dict(stop=600, kill=8), env=dict(A_UNIT_FIXTURE_SLEEP='120'))
        entry, unit = self.record('deadline_kill', case)
        process = case.result['process']
        self.assertEqual(process['stopped'], 'deadline'); self.assertNotEqual(process['returncode'], 0)
        self.assertLess(case.seconds, 60)
        self.assertFalse(unit.get('passed')); self.assertEqual(unit['stages'][0]['name'], 'bind')
        entry.update(passed=True)

    def test_memory_guard_stops_worker(self):
        case = Case(False, dict(guard_bytes=64*1024**2), env=dict(A_UNIT_FIXTURE_SLEEP='120', A_UNIT_FIXTURE_ALLOCATE=str(3*1024**3)))
        entry, unit = self.record('memory_guard', case)
        process = case.result['process']
        self.assertEqual(process['stopped'], 'memory'); self.assertTrue(process['memory']['over'])
        self.assertLess(case.seconds, 90)
        self.assertGreaterEqual(process['memory']['guarded_bytes'], 64*1024**2)
        entry.update(passed=True)

    def test_page_cache_is_not_charged(self):
        sys.path[:0] = [str(HERE/'runtime')]
        import importlib.util
        spec = importlib.util.spec_from_file_location('unit_m', HERE/'runtime/m.py')
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        stat = 'anon 100\nfile 900\nactive_file 500\ninactive_file 400\nshmem 0\n'
        self.assertEqual(m.guarded_memory({'memory.current': '1000', 'memory.stat': stat}, 7), (100, 'cgroup'))
        self.assertEqual(m.guarded_memory({}, 7), (7, 'process_tree_rss'))
        fired = []
        guard = m.Guard(0, 150, lambda: fired.append(1), sample=lambda: ({'memory.current': '1000', 'memory.stat': stat, 'memory.max': '2000'}, 7))
        self.assertEqual(guard.check(), 100); self.assertEqual(fired, [])
        guard.limit = 100; guard.check(); guard.check(); self.assertEqual(fired, [1])
        self.assertEqual(guard.receipt()['cgroup_max'], '2000')
        EVIDENCE['cases'].append(dict(name='page_cache_guard', passed=True))

    def test_admission(self):
        est = CU.ESTIMATES
        rows = [dict(mapping=dict(dense_count=n)) for n in (64, 64, 32, 64, 32)]
        text = (HERE/'runtime/w.py').read_text()
        start = text.index('UNIT_RECEIPT='); stop = text.index('def _stats(')
        scope = dict(np=__import__('numpy'))
        exec(compile(text[start:stop], 'w.py', 'exec'), scope)
        admit = scope['admit_unit']
        full = 1.25*(est['first_model']['64']+est['load']+est['prefill'])+est['margin']
        self.assertEqual(admit(rows, full+1, est)[0], 0)
        index, info = admit(rows, full-1, est)
        self.assertEqual((index, info['reason']), (2, 'time_guard'))
        index, info = admit(rows, 10, est)
        self.assertEqual((index, info['reason']), (2, 'over_budget'))
        self.assertEqual(admit([rows[0]], 10, est)[1]['reason'], 'over_budget')
        EVIDENCE['cases'].append(dict(name='admission', passed=True, first_need_s=full))


if __name__ == '__main__':unittest.main(verbosity=2)
