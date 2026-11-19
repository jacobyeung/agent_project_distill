from support import *
import fcntl
import tarfile


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='tmp_install_', dir=str(FIXTURES)))
        self.base = self.root / 'base'
        self.state = self.root / 'state'
        self.state.mkdir()
        self.bin = self.root / 'bin'
        write(self.bin / 'hostname', '#!/bin/bash\necho trinity-3-30\n', True)
        self.env = dict(os.environ, PATH=str(self.bin) + ':/usr/bin:/bin', LCS_ROBUST_SYNC='0')
        source = Path(os.environ.get('LCS_INSTALLED_INPUT', str(INPUT)))
        for line in (BASE / 'PREIMAGE.sha256').read_text().splitlines():
            unused, name = line.split(None, 1)
            path = self.base / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((source / Path(name).name).read_bytes())

    def run_install(self):
        return subprocess.run(PY + [str(BASE / 'install_tools.py'), str(BASE), str(self.base), str(self.state)],
                              env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)

    def test_install_preimages_backups_atomic_replacements_and_postimages(self):
        before = {p.name: p.read_bytes() for p in (self.base / 'tools').iterdir()}
        result = self.run_install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for line in (BASE / 'POSTIMAGE.sha256').read_text().splitlines():
            digest, name = line.split(None, 1)
            self.assertEqual(hashlib.sha256((self.base / name).read_bytes()).hexdigest(), digest)
        archives = list((self.state / 'install-backups').glob('*/preimage.tar'))
        self.assertEqual(len(archives), 1)
        with tarfile.open(str(archives[0])) as archive:
            self.assertEqual({Path(m.name).name: archive.extractfile(m).read() for m in archive}, before)
        self.assertFalse(list((self.base / 'tools').glob('.*.lcs-*')))
        self.assertFalse((self.state / 'LCS_ROBUST_SYNC').exists())
        self.assertIn(b'robust mode remains OFF', result.stdout)

    def test_busy_lock_defers_without_writes(self):
        with open(str(self.state / '.sync.lock'), 'w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self.run_install()
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertFalse((self.state / 'install-backups').exists())

    def test_mismatched_preimage_stops_before_backup_or_install(self):
        write(self.base / 'tools' / 'lane_code_scan.py', 'unexpected edit')
        result = self.run_install()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn(b'mismatch', result.stderr)
        self.assertFalse((self.state / 'install-backups').exists())
        self.assertFalse((self.base / 'tools' / 'lane_code_stage.sh').exists())


class CalibrationTests(unittest.TestCase):
    def test_derives_budgets_and_refuses_failure_or_incomplete_log(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('calibrate', str(BASE / 'calibrate_budgets.py'))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        lines = []
        for label in ('trinity-1-18', 'trinity-3-30', 'orch_n30/tools', 'orch_n30/briefs'):
            lines += ['2026-11-19T12:00:00Z ROBUST stage ' + label,
                      '2026-11-19T12:02:00Z ROBUST accept ' + label,
                      '2026-11-19T12:02:10Z STAGED ' + label + ' rc=0',
                      '2026-11-19T12:02:11Z ROBUST copy ' + label,
                      '2026-11-19T12:05:11Z COPIED ' + label + ' rc=0']
        lines += ['2026-11-19T12:05:12Z STAGE-ONLY done']
        text = '\n'.join(lines)
        measured, budgets = module.derive(text)
        self.assertTrue(all(value == {'stage': 120, 'accept': 10, 'copy': 180} for value in measured.values()))
        self.assertEqual(dict(budgets), dict(LCS_FILE_SECONDS=3, LCS_SCAN_SECONDS=270, LCS_COPY_SECONDS=390,
                                          LCS_LEG_SECONDS=395, LCS_REMOTE_SECONDS=425, LCS_NODE_SECONDS=550,
                                          LCS_KILL_SECONDS=5))
        for bad in (text + '\n2026-11-19T12:02:02Z FAIL source', '\n'.join(lines[:-1])):
            with self.assertRaises(ValueError): module.derive(bad)
