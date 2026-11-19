"""Third-review regressions, including the reviewer's rollback and missing-root probes."""
from support import *
import datetime
import fcntl
import importlib.util
import shutil
import tarfile

PACKAGE = Path(os.environ.get('LCS_ROUND3_PACKAGE', str(BASE)))
LABELS = ('trinity-1-18', 'trinity-3-30', 'orch_n30/tools', 'orch_n30/briefs')


def load(name):
    spec = importlib.util.spec_from_file_location(name, str(PACKAGE / (name + '.py')))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def calibration():
    from test_round2 import calibration_log
    text = calibration_log()
    # Keep this fixture independent of the prior test's optional SCAN records.
    text = '\n'.join(line for line in text.splitlines() if 'SCAN scanned=' not in line)
    return text.replace('2026-11-19T13:00:00Z STAGE-ONLY done', '\n'.join(
        '  [copy %s] SCAN scanned=%d copied=1 unchanged=0 flagged=0 list=fixture' % (label, i + 1)
        for i, label in enumerate(LABELS)) + '\n2026-11-19T13:00:00Z STAGE-ONLY done')


class RuntimeRound3Tests(DriverFixture):
    def test_other_remote_root_does_not_skip(self):
        self.env['LCS_REMOTE_NODES'] = 'trinity-1-19'
        self.env['FAKE_trinity_1_19'] = 'missing'
        result = self.run_driver()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(b'FAIL trinity-1-19 stage rc=66', result.stdout)
        self.assertNotIn(b'SKIP trinity-1-19 (no source root)', result.stdout)
        self.assertEqual(len(list((self.root / 'events').glob('*_BLOCKER_sync_failed.md'))), 1)

    def test_missing_local_roots_fail_and_emit_blocker(self):
        for label in ('trinity-3-30', 'orch_n30/tools', 'orch_n30/briefs'):
            with self.subTest(label=label):
                self.setUp()
                if label == 'orch_n30/tools':
                    # Keep executable helpers in place; inject ENOENT only at source cd.
                    path = self.b / 'tools/lane_code_stage.sh'
                    path.write_text(path.read_text().replace('source=$B/tools;', 'source=$B/tools_absent;'))
                else:
                    source = self.local if label == 'trinity-3-30' else self.b / 'briefs'
                    source.rename(source.with_name(source.name + '_moved'))
                result = self.run_driver()
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(('FAIL %s stage rc=66' % label).encode(), result.stdout)
                self.assertNotIn(('SKIP %s (no source root)' % label).encode(), result.stdout)
                self.assertEqual(len(list((self.root / 'events').glob('*_BLOCKER_sync_failed.md'))), 1)
                self.assertIn(b'committed', result.stdout)

    def test_zero_exit_without_accept_marker_fails_before_copy(self):
        # The installed old-layout scanner exits 0 without the protocol marker.
        (self.b / 'tools/lane_code_scan.py').write_bytes((INPUT / 'lane_code_scan.py').read_bytes())
        result = self.run_driver()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(b'accept protocol missing ACCEPTING', result.stdout)
        self.assertNotIn(b'ROBUST copy ', result.stdout)
        self.assertNotIn(b'STAGED ', result.stdout)
        self.assertEqual((self.repo / 'lane_code/trinity-1-18/good.py').read_text(), 'prior-good')
        self.assertEqual(len(list((self.root / 'events').glob('*_BLOCKER_sync_failed.md'))), 1)


class DisableRound3Tests(DriverFixture):
    def setUp(self):
        super(DisableRound3Tests, self).setUp()
        self.backup = self.state / 'install-backups/fixture'
        self.backup.mkdir(parents=True)
        with tarfile.open(str(self.backup / 'preimage.tar'), 'w') as archive:
            for line in (BASE / 'PREIMAGE.sha256').read_text().splitlines():
                unused, name = line.split(None, 1)
                archive.add(str(INPUT / Path(name).name), arcname=name, recursive=False)
        (self.backup / 'PREIMAGE.sha256').write_bytes((BASE / 'PREIMAGE.sha256').read_bytes())

    def script(self, name):
        self.assertTrue((PACKAGE / name).is_file(), 'missing saved ' + name)
        return subprocess.run(['bash', '-eu', str(PACKAGE / name), str(self.backup)],
                              env=dict(self.env, B=str(self.b), S=str(self.state),
                                       LCS_ROBUST_SYNC='0', LCS_OWNER_PYTHON=sys.executable),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)

    def test_disable_prevents_stale_legacy_republication(self):
        clone = self.repo / 'lane_code/trinity-1-18/good.py'
        write(self.state / 'stage/trinity-1-18/good.py', 'stale-v1 (legacy stage before robust)')
        write(self.state / 'LCS_ROBUST_SYNC', '')
        result = self.run_driver()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(clone.read_text(), "value = 'trinity-1-18'")
        source = self.root / 'sources/trinity-1-18'
        (source / 'good.py').rename(source / 'good.bin')
        self.env['LCS_ROBUST_SYNC'] = '0'
        if (PACKAGE / 'disable.sh').is_file():
            result = self.script('disable.sh')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            # Reproduce the reviewed flag-only disable, without deleting anything.
            (self.state / 'LCS_ROBUST_SYNC').rename(self.state / 'LCS_ROBUST_SYNC.off-probe')
        result = self.run_driver()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        print('MEASURE rollback_probe legacy_rc=%d clone=%r' % (result.returncode, clone.read_text()), flush=True)
        self.assertEqual(clone.read_text(), "value = 'trinity-1-18'")
        retired = list(self.state.glob('stage.pre-robust-*'))
        self.assertEqual(len(retired), 1)
        self.assertEqual((retired[0] / 'trinity-1-18/good.py').read_text(), 'stale-v1 (legacy stage before robust)')
        self.assertFalse((self.state / 'stage/trinity-1-18/good.py').exists())

    def test_disable_holds_sync_lock_and_prints_exact_rollback(self):
        write(self.state / 'LCS_ROBUST_SYNC', 'flag')
        with open(str(self.state / '.sync.lock'), 'w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self.script('disable.sh')
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertTrue((self.state / 'LCS_ROBUST_SYNC').exists())
        self.assertTrue((self.state / 'stage').exists())
        result = self.script('disable.sh')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(str(PACKAGE / 'rollback.sh').encode(), result.stdout)
        self.assertIn(str(self.backup).encode(), result.stdout)
        self.assertFalse((self.state / 'stage').exists())
        self.assertFalse((self.state / 'LCS_ROBUST_SYNC').exists())

    def test_rollback_restores_exact_preimage_under_lock(self):
        write(self.state / 'LCS_ROBUST_SYNC', '')
        with open(str(self.state / '.sync.lock'), 'w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self.script('rollback.sh')
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        result = self.script('rollback.sh')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for line in (self.backup / 'PREIMAGE.sha256').read_text().splitlines():
            digest, name = line.split(None, 1)
            self.assertEqual(hashlib.sha256((self.b / name).read_bytes()).hexdigest(), digest)
        self.assertFalse((self.state / 'stage').exists())
        self.assertFalse((self.state / 'LCS_ROBUST_SYNC').exists())
        self.assertTrue((self.b / 'tools/lane_code_stage.sh').exists())
        self.assertIn(b'ROLLBACK OK', result.stdout)


class CalibrationRound3Tests(unittest.TestCase):
    def test_prints_calibrated_margins(self):
        root = Path(tempfile.mkdtemp(prefix='tmp_margins_', dir=str(FIXTURES)))
        write(root / 'log', calibration())
        result = subprocess.run(PY + [str(PACKAGE / 'calibrate_budgets.py'), str(root / 'log')],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(b'LEG-SCAN>=125s REMOTE-LEG>=30s NODE-REMOTE>=125s KILL=5s tssh_pre_sleep<=35s', result.stderr)

    def test_missing_or_zero_scan_counts_refused_per_required_label(self):
        derive = load('calibrate_budgets').derive
        for i, label in enumerate(LABELS):
            for replacement in ('', '  [copy %s] SCAN scanned=0 copied=0' % label):
                with self.subTest(label=label, replacement=replacement):
                    text = '\n'.join(replacement if '[copy %s]' % label in line else line
                                     for line in calibration().splitlines())
                    with self.assertRaisesRegex(ValueError, 'SCAN'):
                        derive(text)

    def test_prints_counts_beside_last_legacy_stats_and_margins(self):
        root = Path(tempfile.mkdtemp(prefix='tmp_counts_', dir=str(FIXTURES)))
        write(root / 'calibration.log', calibration())
        write(root / 'sync.log', '\n'.join(
            ['2026-11-19T10:00:00Z START dry=0 queue_only=0'] +
            ['STATS %s files=99 bytes=999 old' % label for label in LABELS] +
            ['2026-11-19T11:00:00Z START dry=0 queue_only=0'] +
            ['  [%s] STATS %s files=%d bytes=10 latest' % (label, label, i + 2)
             for i, label in enumerate(LABELS)] +
            ['2026-11-19T12:00:00Z START dry=0 queue_only=0',
             '2026-11-19T12:00:00Z ROBUST slots=fixture',
             'STATS trinity-1-18 files=500 robust-must-not-replace-legacy']))
        result = subprocess.run(PY + [str(PACKAGE / 'calibrate_budgets.py'), str(root / 'calibration.log'),
                                     str(root / 'sync.log')], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for i, label in enumerate(LABELS):
            expected = 'COUNTS %s scanned=%d legacy=STATS %s files=%d bytes=10 latest' % (label, i + 1, label, i + 2)
            self.assertIn(expected.encode(), result.stderr)
        self.assertIn(b'LEG-SCAN>=125s REMOTE-LEG>=30s NODE-REMOTE>=125s KILL=5s tssh_pre_sleep<=35s', result.stderr)
        self.assertNotIn(b'robust-must-not-replace-legacy', result.stderr)

    def test_pre_enable_counts_every_node_and_local_failures(self):
        root = Path(tempfile.mkdtemp(prefix='tmp_pre_nodes_', dir=str(FIXTURES)))
        for line, label in [('FAIL trinity-2-28 stage rc=4: PIPE 0 1 0', 'trinity-2-28'),
                            ('FAIL trinity-3-30 stage rc=4: PIPE 0 1 0', 'trinity-3-30'),
                            ('FAIL trinity-3-30 local stage', 'trinity-3-30')]:
            with self.subTest(line=line):
                write(root / 'log', '\n'.join(['2026-11-19T12:00:00Z START dry=0 queue_only=0'] * 20 +
                                              ['2026-11-19T12:01:00Z ' + line] * 2))
                result = subprocess.run(PY + [str(PACKAGE / 'owner_checks.py'), 'pre-enable', str(root / 'log')],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn(('NODE %s failures=2 rate=10.00%%' % label).encode(), result.stdout)
                self.assertIn(b'STAY LEGACY', result.stdout)


class CalibrationExitRound3Tests(DriverFixture):
    def test_nonzero_sync_prints_terminal_failure_with_log_path(self):
        package = self.root / 'package'
        package.mkdir()
        for name in ('calibrate.sh', 'owner_checks.py', 'calibrate_budgets.py'):
            shutil.copyfile(str(PACKAGE / name), str(package / name))
        # A malformed saved budget makes the real sync's robust early exit nonzero.
        write(self.state / 'LCS_ROBUST_BUDGETS', 'INVALID=1\n')
        write(package / 'POSTIMAGE.sha256', hashlib.sha256((self.b / 'tools/lane_code_sync.sh').read_bytes()).hexdigest() +
              '  tools/lane_code_sync.sh\n')
        now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        write(self.state / 'sync.log', now + ' START dry=0 queue_only=0\n' + now + ' END ok\n')
        result = subprocess.run(['bash', '-eu', str(package / 'calibrate.sh')],
                                env=dict(self.env, B=str(self.b), S=str(self.state), LCS_ROBUST_SYNC='0',
                                         LCS_OWNER_PYTHON=sys.executable),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn(('CALIBRATION FAILED rc=2; see %s/robust_calibration.log' % self.state).encode(), result.stderr)
        self.assertFalse((self.state / 'LCS_ROBUST_BUDGETS.next').exists())
        self.assertFalse((self.state / 'LCS_ROBUST_SYNC').exists())
