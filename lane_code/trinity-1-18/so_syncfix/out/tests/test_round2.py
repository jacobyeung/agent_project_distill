"""Second-review regressions; all fixtures and fake services stay under tmp_* roots."""
from support import *
import datetime
import importlib.util
import shutil

PACKAGE = Path(os.environ.get('LCS_ROUND2_PACKAGE', str(BASE)))
SCANFIX_SHA = 'f9460a5e3e23e5f2765e454824645d8970b333817518d626847a5e0cba46fabb'


def module(name):
    spec = importlib.util.spec_from_file_location(name, str(PACKAGE / (name + '.py')))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def calibration_log():
    lines = []
    for i, label in enumerate(('trinity-1-18', 'trinity-3-30', 'orch_n30/tools', 'orch_n30/briefs')):
        start = datetime.datetime(2026, 11, 19, 12) + datetime.timedelta(seconds=i * 1000)
        for seconds, message in ((0, 'ROBUST stage ' + label), (10, 'ROBUST accept ' + label),
                                 (110, 'STAGED ' + label + ' rc=0'), (120, 'ROBUST copy ' + label),
                                 (420, 'COPIED ' + label + ' rc=0')):
            lines.append((start + datetime.timedelta(seconds=seconds)).strftime('%Y-%m-%dT%H:%M:%SZ') + ' ' + message)
    lines.extend('  [copy %s] SCAN scanned=1 copied=1 unchanged=0 flagged=0' % label
                 for label in ('trinity-1-18', 'trinity-3-30', 'orch_n30/tools', 'orch_n30/briefs'))
    lines.append('2026-11-19T13:00:00Z STAGE-ONLY done')
    return '\n'.join(lines)


class RebaseTests(unittest.TestCase):
    def test_installed_scanfix_is_preimage_and_pattern_in_both_paths(self):
        self.assertEqual(hashlib.sha256((PACKAGE / 'inputs/lane_code_scan.py').read_bytes()).hexdigest(), SCANFIX_SHA)
        self.assertEqual((PACKAGE / 'PREIMAGE.sha256').read_text().splitlines()[3], SCANFIX_SHA + '  tools/lane_code_scan.py')
        pattern = next(line for line in (PACKAGE / 'inputs/lane_code_scan.py').read_text().splitlines() if "('url_credentials'," in line)
        self.assertIn(pattern, (TOOLS / 'lane_code_scan.py').read_text().splitlines())
        self.assertIn('{0,32}', pattern)
        self.assertNotIn('512', pattern)

    def test_installer_refuses_old_layout_even_with_matching_postimage(self):
        root = Path(tempfile.mkdtemp(prefix='tmp_install_old_', dir=str(FIXTURES)))
        package, base, state = root / 'package', root / 'base', root / 'state'
        state.mkdir()
        for name in ('tools', 'inputs'):
            shutil.copytree(str(PACKAGE / name), str(package / name))
        for name in ('PREIMAGE.sha256', 'POSTIMAGE.sha256', 'install_tools.py'):
            shutil.copyfile(str(PACKAGE / name), str(package / name))
        for line in (package / 'PREIMAGE.sha256').read_text().splitlines():
            unused, name = line.split(None, 1)
            path = base / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((package / 'inputs' / path.name).read_bytes())
        old = (package / 'inputs/lane_code_scan.py').read_bytes()
        (package / 'tools/lane_code_scan.py').write_bytes(old)
        lines = (package / 'POSTIMAGE.sha256').read_text().splitlines()
        (package / 'POSTIMAGE.sha256').write_text('\n'.join(
            hashlib.sha256(old).hexdigest() + '  tools/lane_code_scan.py' if line.endswith('tools/lane_code_scan.py') else line
            for line in lines) + '\n')
        before = {p.name: p.read_bytes() for p in (base / 'tools').iterdir()}
        write(root / 'bin/hostname', '#!/bin/bash\necho trinity-3-30\n', True)
        result = subprocess.run(PY + [str(package / 'install_tools.py'), str(package), str(base), str(state)],
                                env=dict(os.environ, PATH=str(root / 'bin') + ':/usr/bin:/bin', LCS_ROBUST_SYNC='0'),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn(b'scanner protocol', result.stderr)
        self.assertEqual({p.name: p.read_bytes() for p in (base / 'tools').iterdir()}, before)
        self.assertFalse((state / 'install-backups').exists())


class CalibrationRound2Tests(unittest.TestCase):
    def test_stage_accept_copy_measured_and_budget_at_least_double(self):
        try:
            measured, budgets = module('calibrate_budgets').derive(calibration_log())
        except ValueError as error:
            self.fail(str(error))
        self.assertEqual(measured['trinity-1-18'], {'stage': 10, 'accept': 100, 'copy': 300})
        self.assertGreaterEqual(dict(budgets)['LCS_COPY_SECONDS'], 600)
        root = Path(tempfile.mkdtemp(prefix='tmp_calibration_', dir=str(FIXTURES)))
        write(root / 'log', calibration_log())
        result = subprocess.run(PY + [str(PACKAGE / 'calibrate_budgets.py'), str(root / 'log')],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b'LCS_COPY_SECONDS=', result.stdout)
        self.assertIn(b'accept_seconds trinity-1-18=100', result.stderr)
        self.assertIn(b'copy_seconds trinity-1-18=300', result.stderr)

    def test_missing_accept_or_copy_measurement_refused(self):
        derive = module('calibrate_budgets').derive
        # A dry-only log must be refused even though every stage succeeded.
        dry = '\n'.join(line for line in calibration_log().splitlines()
                        if not any(word in line for word in ('ROBUST accept', 'ROBUST copy', 'COPIED')))
        dry = dry.replace('STAGE-ONLY done', 'DRY done')
        with self.assertRaises(ValueError):
            derive(dry)
        for omitted in ('ROBUST accept trinity-1-18', 'ROBUST copy trinity-1-18', 'COPIED trinity-1-18'):
            with self.subTest(omitted=omitted), self.assertRaises(ValueError):
                derive('\n'.join(line for line in calibration_log().splitlines() if omitted not in line))

    def test_saved_scripts_and_window_guard(self):
        for name in ('install.sh', 'calibrate.sh', 'pre_enable.sh', 'owner_checks.py'):
            self.assertTrue((PACKAGE / name).is_file(), name)
        text = (PACKAGE / 'calibrate.sh').read_text()
        self.assertIn('--stage-only', text)
        self.assertNotIn('--dry', text)
        self.assertIn('window', text)
        self.assertLess(text.index('window'), text.index('--stage-only'))
        self.assertNotIn(': > "$S/LCS_ROBUST_SYNC', text)
        checks = module('owner_checks')
        now = datetime.datetime(2026, 11, 19, 13)
        good = '2026-11-19T12:40:00Z START dry=0 queue_only=0\n2026-11-19T12:50:00Z END ok\n'
        self.assertEqual(checks.window(good, now), 600)
        for bad in (good.replace('12:50:00', '12:49:59'), good.replace('12:50:00', '13:00:01'),
                    '', '2026-11-19T12:59:00Z QUEUE-ONLY END ok\n',
                    good + '2026-11-19T12:59:00Z START dry=0 queue_only=0\n'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                checks.window(bad, now)

    def test_pre_enable_counts_failures_against_hourly_runs(self):
        self.assertTrue((PACKAGE / 'owner_checks.py').is_file())
        root = Path(tempfile.mkdtemp(prefix='tmp_pre_enable_', dir=str(FIXTURES)))
        lines = ['2026-11-19T12:00:00Z START dry=0 queue_only=0'] * 20
        lines += ['2026-11-19T12:00:00Z START dry=1 queue_only=0',
                  '2026-11-19T12:00:00Z START dry=0 queue_only=1']
        failure = '2026-11-19T12:01:00Z FAIL trinity-1-18 stage rc=4: PIPE 0 1 0'
        for count, status, message in ((1, 0, b'within threshold'), (2, 2, b'STAY LEGACY')):
            write(root / 'sync.log', '\n'.join(lines + [failure] * count))
            result = subprocess.run(PY + [str(PACKAGE / 'owner_checks.py'), 'pre-enable', str(root / 'sync.log')],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
            self.assertEqual(result.returncode, status, result.stdout + result.stderr)
            self.assertIn(('runs=20 stage_rc4_lines=%d' % count).encode(), result.stdout)
            self.assertIn(b'threshold=5.00%', result.stdout)
            self.assertIn(message, result.stdout)


class QueueRound2Tests(unittest.TestCase):
    def test_queue_scan_through_symlinked_parent_is_legacy_identical(self):
        root = Path(tempfile.mkdtemp(prefix='tmp_queue_', dir=str(FIXTURES)))
        write(root / 'real/qscan/pkg/good.py', 'clean')
        write(root / 'real/qscan/pkg/secret.txt', 'https://user:' + 'p' * 1150 + '@host')
        os.symlink(str(root / 'real'), str(root / 'link'))
        stage = root / 'link/qscan'
        flags = root / 'flags'
        outputs = []
        for source, robust in ((INPUT / 'lane_code_scan.py', '0'), (TOOLS / 'lane_code_scan.py', '1')):
            env = dict(os.environ, LCS_ROBUST_SYNC=robust)
            env.pop('LCS_COPY_TMP', None)
            result = subprocess.run(PY + [str(source), str(stage), str(stage), str(flags)], env=env,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
            self.assertEqual(result.returncode, 0, result.stderr)
            outputs.append((result.stdout, result.stderr, flags.read_bytes()))
        self.assertEqual(outputs[0], outputs[1])
        self.assertIn(b'url_credentials', outputs[1][2])


class ManifestRound2Tests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='tmp_manifest_', dir=str(FIXTURES)))
        write(self.root / 'meta/DEDUP_fixture.tsv.gz', 'prior')

    def run_filter(self, injection=''):
        source = TOOLS / 'lane_code_filter.py'
        code = 'import os,sys,gzip\n' + injection + '\nsys.argv=%r\nexec(compile(open(sys.argv[0]).read(),sys.argv[0],"exec"))' % [str(source), 'fixture', 'meta']
        return subprocess.run(PY + ['-c', code], cwd=str(self.root), env=dict(os.environ, LCS_ROBUST_SYNC='1'),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)

    def test_repeated_failed_manifest_reuses_one_name(self):
        for unused in range(3):
            result = self.run_filter("def broken(self, data): raise OSError('injected write failure')\ngzip.GzipFile.write=broken")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b'MANIFEST_PENDING', result.stderr)
        self.assertEqual([p.name for p in (self.root / 'meta').glob('.dedup-*')], ['.dedup-fixture.pending'])
        self.assertEqual((self.root / 'meta/DEDUP_fixture.tsv.gz').read_text(), 'prior')

    def test_regular_manifest_slot_is_truncated_and_replaced(self):
        slot = self.root / 'meta/.dedup-fixture.pending'
        slot.write_bytes(b'leftover' * 10000)
        result = self.run_filter()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(slot.exists())
        with gzip.open(str(self.root / 'meta/DEDUP_fixture.tsv.gz'), 'rb') as stream:
            self.assertEqual(stream.read(), b'')

    def test_fixed_manifest_slot_refuses_fifo_symlink_and_hardlink_before_truncation(self):
        for kind in ('fifo', 'symlink', 'hardlink'):
            with self.subTest(kind=kind):
                self.setUp()
                slot = self.root / 'meta/.dedup-fixture.pending'
                target = self.root / 'target.bin'
                target.write_bytes(b'unchanged target')
                if kind == 'fifo': os.mkfifo(str(slot))
                elif kind == 'symlink': os.symlink(str(target), str(slot))
                else: os.link(str(target), str(slot))
                result = self.run_filter()
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(target.read_bytes(), b'unchanged target')
                self.assertEqual((self.root / 'meta/DEDUP_fixture.tsv.gz').read_text(), 'prior')


class BudgetRound2Tests(DriverFixture):
    def test_unordered_budgets_refused_before_starting_sources(self):
        for key, value in (('LCS_SCAN_SECONDS', '0.7'), ('LCS_LEG_SECONDS', '1.0'), ('LCS_REMOTE_SECONDS', '1.3')):
            with self.subTest(key=key):
                self.setUp()
                self.env[key] = value
                result = self.run_driver(('--dry',))
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn(b'SCAN < LEG < REMOTE < NODE', result.stdout)
                self.assertFalse((self.root / 'ssh.jsonl').exists())


class FixtureRound2Tests(unittest.TestCase):
    def test_default_fixture_root_is_pruned(self):
        source = (PACKAGE / 'tests/run_tests.py').read_text()
        self.assertIn("'tmp_test-work'", source)
        self.assertNotIn("'test-work'", source)
