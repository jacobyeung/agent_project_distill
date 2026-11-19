"""Assertion regressions adapted from work/tmp_review/review_tests.py."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

PACKAGE = Path(__file__).resolve().parents[1]
TARGET = Path(os.environ.get('ROUND1_TARGET', str(PACKAGE)))
FILTER = TARGET / 'tools/lane_code_filter.py'
WORK = PACKAGE.parent / 'work'


def put(root, rel):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(rel.encode())


def run(root, robust, label):
    result = subprocess.run([sys.executable, '-I', '-s', '-B', '-', label],
                            input=FILTER.read_bytes(), cwd=str(root),
                            env=dict(os.environ, LCS_ROBUST_SYNC=str(robust)),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    assert result.returncode == 0, result.stderr
    return set(os.fsdecode(p) for p in result.stdout.split(b'\0') if p)


class ReviewRegressions(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='tmp_round1_', dir=str(WORK)))

    def check(self, keep, drop, label='trinity-2-28'):
        for path in keep + drop:
            put(self.root, path)
        for robust in (0, 1):
            with self.subTest(robust=robust):
                self.assertEqual(run(self.root, robust, label), set(keep))

    def test_finding1_word_number(self):
        self.check(['lane/out/kit_parity50/run.py', 'lane/validation/h_shell400/BUILD.json',
                    'lane/work/res/so_reads228/REPORT.md'],
                   ['lane/work/driver_abcde123/run.py', 'lane/work/random_a2sjw8b2/run.py'])

    def test_finding1_run_records(self):
        records = ['20261119T152211Z_so_reads228', '20261119T134431Z_sb_ph2gate3',
                   'driver_a2sjw8b2', 'results', 'ab' * 16]
        self.check(['lane/agent/scratch/codex_runs/' + n + '/meta.json' for n in records] +
                   ['lane/agent/scratch/codex_runs/20261119T152211Z_so_reads228/prompt.md'],
                   ['lane/agent/scratch/codex_runs/20261119T134431Z_sb_ph2gate3/test_runs/a.py'])

    def test_findings2_3_context(self):
        keep = ['keep.py', 'work/keep2.py']
        drop = ['test_runs/a.py', 'sandbox/b.py', 'results/c.py', 'attic/e.py',
                'work/build1/work/f.py', 'ab' * 16 + '/g.py', 'crowded/h.py']
        for path in keep + drop:
            put(self.root, 'lane/' + path)
        for i in range(2001):
            put(self.root, 'lane/crowded/n%04d.bin' % i)
        for robust in (0, 1):
            hourly = run(self.root, robust, 'trinity-2-28')
            dry = run(self.root / 'lane', robust, 'lane')
            self.assertEqual(dry, set(keep))
            self.assertEqual(hourly, set('lane/' + p for p in dry))
        kit = self.root / 'kit_fixture'
        for p in ['README.md', 'results/r.json', 'runs/run.sh', 'evidence/e.md',
                  'artifacts/a.json', 'tmp_helpers/h.py', 'env/a.py', 'numpy/a.py']:
            put(kit, p)
        for label in ('kit', 'orch_n30/tools', 'orch_n30/briefs', 'trinity-2-28x'):
            for robust in (0, 1):
                self.assertEqual(run(kit, robust, label), {'README.md'})

    def test_finding4_directory_python(self):
        self.check(['lane/src/lib/python_compat.py', 'lane/src/lib/python3_compat.py',
                    'lane/lib/python_helpers/run.py'],
                   ['lane/lib/python3.12/run.py', 'lane/lib/python2.7/run.py'])

    def test_finding5_proven_outputs(self):
        self.check(['lane/work/base/run.py', 'lane/work/replay/run.py',
                    'lane/work/replay_delivery/run.py', 'lane/src/pytest_kit/plugin.py',
                    'lane/work/pytest_helpers/plugin.py', 'lane/src/fcopy/run.py'],
                   ['lane/work/' + n + '/sb_mask_phrase/run.py' for n in ('fcopy', 'scopy', 'lcopy', 'pcopy')] +
                   ['lane/work/ownarm/out/fix400/' + n + '/test_one0/run.py'
                    for n in ('pytest_kit', 'pytest_dry', 'pytest_dry_verified', 'pytest_patched')])

    def test_finding6_default_documented(self):
        for name in ('REPORT.md', 'GIT_OWNER.md'):
            self.assertIn('Ancestor gates apply even when `LCS_REVIEW2_FIXES` is unset',
                          (TARGET / name).read_text())

    def test_finding6_default_ancestor_gate(self):
        spec = importlib.util.spec_from_file_location('dry_round1', str(TARGET / 'tools/dry_count.py'))
        dry = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dry)
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(dry.os, 'listdir', return_value=[]):
            self.assertTrue(dry.root_gate(FILTER, Path('/scratch/jjyeung/orch_n30/lane/test_runs/kit')))
            self.assertIsNone(dry.root_gate(FILTER, Path('/scratch/jjyeung/orch_n30/lane/agent/codex_runs/20261119T134431Z_sb_ph2gate3')))

    def test_finding7_old_anchor(self):
        self.check(['lane/test_runs\n/source.py'],
                   ['lane/results\n/source.py', 'lane/tmp_x\n/source.py'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
