"""Slot validation, activation, and budget-file integration tests."""
from support import *
import io
import tarfile


class SlotDriverTests(DriverFixture):
    def test_environment_alone_enables(self):
        self.assertFalse((self.state / 'LCS_ROBUST_SYNC').exists())
        result = self.run_driver(('--dry',))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(b'ROBUST slots=', result.stdout)
        self.assertIn(b'STAGED trinity-2-28 rc=0', result.stdout)

    def test_flag_wins_over_environment_zero(self):
        self.env['LCS_ROBUST_SYNC'] = '0'
        write(self.state / 'LCS_ROBUST_SYNC', '')
        result = self.run_driver(('--dry',))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(b'ROBUST slots=', result.stdout)

    def test_absent_directory_fifo_and_symlink_flags_stay_off(self):
        self.env.pop('LCS_ROBUST_SYNC')
        for kind in ('absent', 'directory', 'fifo', 'symlink'):
            with self.subTest(kind=kind):
                if kind != 'absent':
                    flag = self.state / 'LCS_ROBUST_SYNC'
                    if kind == 'directory': flag.mkdir()
                    elif kind == 'fifo': os.mkfifo(str(flag))
                    else:
                        write(self.state / 'target', '')
                        os.symlink(str(self.state / 'target'), str(flag))
                result = self.run_driver(('--dry',))
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertNotIn(b'ROBUST', result.stdout)
                if kind != 'absent':
                    os.rename(str(flag), str(self.state / ('disabled-' + kind)))

    def test_budget_file_and_environment_precedence(self):
        self.env.pop('LCS_SCAN_SECONDS')
        write(self.state / 'LCS_ROBUST_BUDGETS', 'LCS_SCAN_SECONDS=0.6\nLCS_FILE_SECONDS=30\n')
        result = self.run_driver(('--dry',))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(b'scan_seconds=0.6', result.stdout)
        self.assertIn(b'file_seconds=0.1', result.stdout)
        self.env.pop('LCS_FILE_SECONDS')
        result = self.run_driver(('--dry',))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(b'file_seconds=30', result.stdout)

    def test_budget_file_is_not_shell_code(self):
        write(self.state / 'LCS_ROBUST_BUDGETS', 'LCS_SCAN_SECONDS=$(touch %s)\n' % (self.root / 'executed'))
        result = self.run_driver()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertFalse((self.root / 'executed').exists())
        self.assertTrue(list((self.root / 'events').glob('*_BLOCKER_sync_failed.md')))

    def test_old_receiver_lock_refuses_new_writer(self):
        slot = self.state / 'stage-robust' / 'trinity-1-18'
        write(slot / 'incoming', 'previous incomplete transfer')
        import fcntl
        with open(str(slot / 'incoming.lock'), 'w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self.run_driver()
        self.check_partial_success(result)
        self.assertEqual((slot / 'incoming').read_text(), 'previous incomplete transfer')
        self.assertFalse((slot / 'accepted').exists())

    def test_large_log_is_capped_and_reused(self):
        write(self.bin / 'tar', '#!/bin/bash\n'
              'if [[ "$PWD" == */sources/trinity-1-18 ]] && [[ " $* " == *" -cf "* ]]; then\n'
              '  head -c 90000 /dev/zero | tr "\\0" x >&2\n'
              'fi\nexec /usr/bin/tar "$@"\n', True)
        result = self.run_driver()
        self.check_partial_success(result)
        log = self.state / 'stage-robust' / 'trinity-1-18' / 'run.log'
        self.assertLessEqual(log.stat().st_size, 65536)
        write(self.bin / 'tar', '#!/bin/bash\nexec /usr/bin/tar "$@"\n', True)
        result = self.run_driver()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertLess(log.stat().st_size, 4096)


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='tmp_archive_', dir=str(FIXTURES)))

    def accept(self, incoming, accepted):
        return subprocess.run(PY + [str(TOOLS / 'lane_code_scan.py'), '--accept-archive', str(incoming), str(accepted)],
                              env=dict(os.environ, LCS_ROBUST_SYNC='1', LCS_COPY_TMP=str(self.root / '.copy.pending')),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)

    def test_special_entries_and_truncated_archives_preserve_accepted(self):
        for kind in ('fifo', 'symlink', 'hardlink', 'character', 'parent', 'absolute', 'truncated'):
            with self.subTest(kind=kind):
                incoming = self.root / ('incoming-' + kind)
                accepted = self.root / ('accepted-' + kind)
                accepted.write_bytes(b'prior accepted archive')
                with tarfile.open(str(incoming), 'w') as archive:
                    regular = tarfile.TarInfo('first.py'); regular.size = 4
                    archive.addfile(regular, io.BytesIO(b'good'))
                    member = tarfile.TarInfo('special.py')
                    if kind == 'fifo': member.type = tarfile.FIFOTYPE
                    elif kind == 'symlink': member.type = tarfile.SYMTYPE; member.linkname = '/outside'
                    elif kind == 'hardlink': member.type = tarfile.LNKTYPE; member.linkname = 'first.py'
                    elif kind == 'character': member.type = tarfile.CHRTYPE
                    elif kind == 'parent': member.name = '../outside.py'
                    elif kind == 'absolute': member.name = '/outside.py'
                    else: member.size = 10000
                    archive.addfile(member, io.BytesIO(b'x' * member.size))
                if kind == 'truncated':
                    content = incoming.read_bytes()
                    incoming.write_bytes(content[:1800])
                result = self.accept(incoming, accepted)
                self.assertNotEqual(result.returncode, 0, result.stderr)
                self.assertEqual(accepted.read_bytes(), b'prior accepted archive')
                self.assertTrue(incoming.is_file())

    def test_archive_copy_matches_directory_copy_bytes_and_flags(self):
        source = self.root / 'source'
        write(source / 'space name.md', 'one')
        write(source / 'new\nline.py', 'two')
        write(source / 'nonutf_\udcff.py', 'three')
        write(source / 'secret.txt', 'ghp_' + 'x' * 32)
        incoming = self.root / 'incoming'
        with tarfile.open(str(incoming), 'w') as archive:
            for path in sorted(source.iterdir()):
                archive.add(str(path), arcname=path.name, recursive=False)
        accepted = self.root / 'accepted'
        result = self.accept(incoming, accepted)
        self.assertEqual(result.returncode, 0, result.stderr)
        trees, flags = [], []
        for name, stage, enabled in (('directory', source, '0'), ('archive', accepted, '1')):
            dest = self.root / name
            flag = self.root / (name + '.flags')
            result = subprocess.run(PY + [str(TOOLS / 'lane_code_scan.py'), str(stage), str(dest), str(flag)],
                                    env=dict(os.environ, LCS_ROBUST_SYNC=enabled, LCS_COPY_TMP=str(self.root / '.copy.pending')),
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
            self.assertEqual(result.returncode, 0, result.stderr)
            trees.append({str(p.relative_to(dest)): p.read_bytes() for p in dest.rglob('*') if p.is_file()})
            flags.append(flag.read_bytes())
        self.assertEqual(trees[0], trees[1])
        self.assertEqual(flags[0], flags[1])


class CopyModeTests(unittest.TestCase):
    def test_atomic_copy_preserves_existing_mode_and_respects_umask(self):
        root = Path(tempfile.mkdtemp(prefix='tmp_copy_mode_', dir=str(FIXTURES)))
        stage, dest = root / 'stage', root / 'dest'
        write(stage / 'existing.sh', 'new executable content')
        write(stage / 'new.py', 'new content')
        write(dest / 'existing.sh', 'old', True)
        source = TOOLS / 'lane_code_scan.py'
        code = 'import os,sys; os.umask(0o027); sys.argv=%r; exec(compile(open(sys.argv[0]).read(),sys.argv[0],"exec"))' % [str(source),str(stage),str(dest),str(root / 'flags.txt')]
        result = subprocess.run(PY + ['-c', code], env=dict(os.environ,LCS_ROBUST_SYNC='1', LCS_COPY_TMP=str(root / '.copy.pending')),
                                stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=3)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(stat.S_IMODE((dest / 'existing.sh').stat().st_mode),0o755)
        self.assertEqual(stat.S_IMODE((dest / 'new.py').stat().st_mode),0o640)
