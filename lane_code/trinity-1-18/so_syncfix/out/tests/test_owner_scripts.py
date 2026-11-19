"""Execute the saved owner scripts against private trees and fake services."""
from support import *
import datetime
import shutil


class OwnerScriptTests(DriverFixture):
    def setUp(self):
        super(OwnerScriptTests, self).setUp()
        self.package = self.root / 'package'
        self.package.mkdir()
        for name in ('install.sh', 'pre_enable.sh', 'calibrate.sh', 'enable.sh', 'install_tools.py',
                     'owner_checks.py', 'calibrate_budgets.py'):
            shutil.copyfile(str(BASE / name), str(self.package / name))
        shutil.copytree(str(BASE / 'tools'), str(self.package / 'tools'))
        (self.package / 'PREIMAGE.sha256').write_bytes((BASE / 'PREIMAGE.sha256').read_bytes())
        self.env.update(B=str(self.b), S=str(self.state), LCS_ROBUST_SYNC='0', LCS_OWNER_PYTHON=sys.executable)
        self.image_manifest(self.b)
        self.sync_log()

    def image_manifest(self, root):
        (self.package / 'POSTIMAGE.sha256').write_text(''.join(
            hashlib.sha256((root / name).read_bytes()).hexdigest() + '  ' + name + '\n'
            for name in [line.split(None, 1)[1] for line in (BASE / 'POSTIMAGE.sha256').read_text().splitlines()]
            if (root / name).exists()))

    def sync_log(self, age=1):
        now = datetime.datetime.utcnow()
        (self.state / 'sync.log').write_text(
            (now - datetime.timedelta(seconds=1200)).strftime('%Y-%m-%dT%H:%M:%SZ') + ' START dry=0 queue_only=0\n' +
            (now - datetime.timedelta(seconds=age)).strftime('%Y-%m-%dT%H:%M:%SZ') + ' END ok\n')

    def run_script(self, name):
        result = subprocess.run(['bash', '-eu', str(self.package / name)], env=self.env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=12)
        (self.root / (name + '.stdout')).write_bytes(result.stdout)
        (self.root / (name + '.stderr')).write_bytes(result.stderr)
        return result

    def test_saved_calibration_copies_once_without_git_or_enabling(self):
        result = self.run_script('calibrate.sh')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(b'CALIBRATION WINDOW OK', result.stdout)
        self.assertIn(b'LCS_COPY_SECONDS=', result.stdout)
        log = (self.state / 'robust_calibration.log').read_text()
        self.assertEqual(log.count(' START '), 1)
        self.assertIn('STAGE-ONLY done', log)
        self.assertIn('ROBUST accept trinity-1-18', log)
        self.assertIn('COPIED trinity-1-18 rc=0', log)
        self.assertEqual((self.repo / 'lane_code/trinity-1-18/good.py').read_text(), "value = 'trinity-1-18'")
        self.assertFalse((self.root / 'git.jsonl').exists())
        self.assertFalse((self.state / 'LCS_ROBUST_SYNC').exists())
        self.assertTrue((self.state / 'LCS_ROBUST_BUDGETS').is_file())

    def test_stale_window_refuses_before_start_and_parent_shell_survives(self):
        self.sync_log(age=601)
        result = subprocess.run(['bash', '-c', 'bash -eu "$1"; rc=$?; echo "parent-alive rc=$rc"',
                                 'fixture', str(self.package / 'calibrate.sh')], env=self.env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        self.assertIn(b'parent-alive rc=2', result.stdout)
        self.assertIn(b'OWNER CHECK REFUSED', result.stderr)
        self.assertFalse((self.state / 'robust_calibration.log').exists())
        self.assertFalse((self.root / 'ssh.jsonl').exists())

    def test_failed_calibration_does_not_install_budgets_or_flag(self):
        self.env['FAKE_trinity_1_18'] = 'unreachable'
        result = self.run_script('calibrate.sh')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn(b'CALIBRATION REFUSED', result.stderr)
        self.assertFalse((self.state / 'LCS_ROBUST_BUDGETS').exists())
        self.assertFalse((self.state / 'LCS_ROBUST_SYNC').exists())
        self.assertFalse((self.root / 'git.jsonl').exists())

    def test_enable_requires_complete_calibration_and_matching_budgets(self):
        result = self.run_script('enable.sh')
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.state / 'LCS_ROBUST_SYNC').exists())
        result = self.run_script('calibrate.sh')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = self.run_script('enable.sh')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        flag = self.state / 'LCS_ROBUST_SYNC'
        self.assertTrue(flag.is_file())
        self.assertFalse(flag.is_symlink())

    def test_saved_install_keeps_robust_off(self):
        base = self.root / 'preimage'
        for line in (BASE / 'PREIMAGE.sha256').read_text().splitlines():
            unused, name = line.split(None, 1)
            target = base / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((INPUT / target.name).read_bytes())
        self.env['B'] = str(base)
        self.image_manifest(self.package)
        (self.package / 'SHA256SUMS').write_text(''.join(
            hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + str(path.relative_to(self.package)) + '\n'
            for path in sorted(self.package.rglob('*')) if path.is_file()))
        result = self.run_script('install.sh')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(b'PREFLIGHT scanner protocol: OK', result.stdout)
        self.assertFalse((self.state / 'LCS_ROBUST_SYNC').exists())
        self.assertEqual((base / 'tools/lane_code_scan.py').read_bytes(), (BASE / 'tools/lane_code_scan.py').read_bytes())
