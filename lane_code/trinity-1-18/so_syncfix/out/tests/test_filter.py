from support import *

class FilterTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='filter_', dir=str(FIXTURES)))

    def scan(self, enabled=True, source=None, injection='', manifest=None):
        source = source or TOOLS / 'lane_code_filter.py'
        env = dict(os.environ, LCS_ROBUST_SYNC='1' if enabled else '0', LCS_FILE_SECONDS='0.05')
        argv = [str(source), 'fixture'] + ([manifest] if manifest else [])
        if injection:
            code = 'import os, sys, time, stat\n' + injection + '\n' + \
                'sys.argv = ' + repr(argv) + '\nexec(compile(open(sys.argv[0]).read(), sys.argv[0], "exec"))\n'
            command = PY + ['-c', code]
        else:
            command = PY + argv
        return subprocess.run(command, cwd=str(self.root), env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)

    def test_regular_tree_byte_identical_and_default_off(self):
        for i in range(120):
            write(self.root / ('lane%02d' % (i % 9)) / ('file%03d.py' % i), 'value = %d\n' % (i % 31))
        for name in ('space name.md', 'new\nline.txt', 'unicode_é.yaml', '-option.py'):
            write(self.root / name, name)
        write(self.root / 'runs' / 'hidden.py', 'excluded')
        write(self.root / 'large.json', 'x' * (256 * 1024 + 1))
        write(self.root / 'large.py', 'x' * (512 * 1024 + 1))
        original = self.scan(False, INPUT / 'lane_code_filter.py')
        off, on = self.scan(False), self.scan(True)
        self.assertEqual((original.returncode, off.returncode, on.returncode), (0, 0, 0))
        self.assertEqual((off.stdout, off.stderr), (original.stdout, original.stderr))
        self.assertEqual(on.stdout, original.stdout)
        print('MEASURE regular_paths_sha256=' + hashlib.sha256(on.stdout).hexdigest(), flush=True)

    def test_fifo_socket_symlinks_never_opened(self):
        write(self.root / 'good.py', 'good')
        os.mkfifo(str(self.root / 'DECISION_PART2.json'))
        # A socket inode suffices; no bind/listen or network access is required.
        os.mknod(str(self.root / 'socket.json'), stat.S_IFSOCK | 0o600)
        outside = self.root.parent / (self.root.name + '_outside')
        write(outside / 'outside.py', 'outside')
        os.symlink(str(outside / 'outside.py'), str(self.root / 'link.py'))
        os.symlink(str(outside), str(self.root / 'linked_directory'))
        injection = '''original_open = os.open
def checked_open(path, flags, *args, **kw):
    if path in ('DECISION_PART2.json', 'socket.json', 'link.py', 'linked_directory'):
        raise AssertionError('opened a nonregular fixture: ' + path)
    return original_open(path, flags, *args, **kw)
os.open = checked_open'''
        result = self.scan(injection=injection)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b'good.py\0')
        self.assertIn(b'skipped_nonregular=2', result.stderr)
        self.assertIn(b'skipped_symlink=2', result.stderr)

    def test_device_mode_is_rejected_before_open(self):
        write(self.root / 'device.json', 'simulated device')
        result = self.scan(injection='''original_lstat = os.lstat
original_open = os.open
def device_lstat(path, *args, **kw):
    result = original_lstat(path, *args, **kw)
    if path == 'device.json':
        fields = list(result); fields[0] = stat.S_IFCHR | 0o600
        return os.stat_result(fields)
    return result
def checked_open(path, *args, **kw):
    if path == 'device.json': raise AssertionError('opened device')
    return original_open(path, *args, **kw)
os.lstat = device_lstat
os.open = checked_open''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b'')
        self.assertIn(b'skipped_nonregular=1', result.stderr)

    def test_slow_read_deadline_counts_and_continues(self):
        write(self.root / 'a.py', 'slow')
        write(self.root / 'b.py', 'good')
        started = time.monotonic()
        result = self.scan(injection='''original_read = os.read
slow = [True]
def slow_read(fd, size):
    if slow[0]:
        slow[0] = False
        time.sleep(2)
    return original_read(fd, size)
os.read = slow_read''')
        elapsed = time.monotonic() - started
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b'b.py\0')
        self.assertIn(b'skipped_timeout=1', result.stderr)
        self.assertLess(elapsed, 1)
        print('MEASURE slow_file_elapsed=%.3fs deadline=0.05s' % elapsed, flush=True)

    def test_replacement_fifo_is_nonblocking_and_fstat_rejected(self):
        write(self.root / 'race.py', 'before')
        result = self.scan(injection='''original_open = os.open
def racing_open(path, flags, *args, **kw):
    if path == 'race.py':
        assert flags & os.O_NONBLOCK and flags & os.O_NOFOLLOW
        os.rename('race.py', 'saved.bin')
        os.mkfifo('race.py')
    return original_open(path, flags, *args, **kw)
os.open = racing_open''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b'')
        self.assertIn(b'skipped_nonregular=1', result.stderr)

    def test_replacement_symlink_is_not_followed(self):
        write(self.root / 'race.py', 'before')
        result = self.scan(injection='''original_open = os.open
def racing_open(path, flags, *args, **kw):
    if path == 'race.py':
        os.rename('race.py', 'saved.bin')
        os.symlink('saved.bin', 'race.py')
    return original_open(path, flags, *args, **kw)
os.open = racing_open''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b'')
        self.assertIn(b'skipped_symlink=1', result.stderr)

    def test_directory_replacement_never_follows_link_or_blocks_on_fifo(self):
        for replacement in ('symlink', 'fifo'):
            root = self.root
            self.root = root / replacement
            write(self.root / 'adir' / 'good.py', 'inside')
            outside = root / (replacement + '_outside')
            write(outside / 'outside.py', 'outside')
            injection = '''original_open = os.open
count = [0]
def racing_open(path, flags, *args, **kw):
    if path == 'adir':
        assert flags & os.O_NOFOLLOW and flags & os.O_NONBLOCK and flags & os.O_DIRECTORY
        count[0] += 1
        if count[0] == 2:
            os.rename('adir', 'saved_dir')
            REPLACEMENT
    return original_open(path, flags, *args, **kw)
os.open = racing_open'''
            action = 'os.symlink(%r, "adir")' % str(outside) if replacement == 'symlink' else 'os.mkfifo("adir")'
            result = self.scan(injection=injection.replace('REPLACEMENT', action))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, b'')
            self.root = root

    def test_manifest_content_matches_and_link_parent_refused(self):
        write(self.root / 'a.py', 'same')
        write(self.root / 'b.py', 'same')
        result = self.scan(manifest='meta')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b'a.py\0meta/DEDUP_fixture.tsv.gz\0')
        with gzip.open(str(self.root / 'meta' / 'DEDUP_fixture.tsv.gz'), 'rb') as f:
            self.assertEqual(f.read(), b'b.py\ta.py\n')
        outside = self.root.parent / (self.root.name + '_outside')
        outside.mkdir()
        os.symlink(str(outside), str(self.root / 'badmeta'))
        refused = self.scan(manifest='badmeta')
        self.assertNotEqual(refused.returncode, 0)
        self.assertEqual(list(outside.iterdir()), [])

    def test_growth_is_capped_and_io_errors_counted(self):
        write(self.root / 'a.py', 'small')
        write(self.root / 'b.py', 'unreadable')
        result = self.scan(injection='''original_read, original_open = os.read, os.open
def growing_read(fd, size):
    return b'x' * size
def bad_open(path, *args, **kw):
    if path == 'b.py': raise PermissionError('simulated denial')
    return original_open(path, *args, **kw)
os.read, os.open = growing_read, bad_open''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b'')
        self.assertIn(b'skipped_oversize=1', result.stderr)
        self.assertIn(b'skipped_io=1', result.stderr)

    def test_changed_regular_inode_is_rejected(self):
        write(self.root / 'race.py', 'before')
        result = self.scan(injection='''original_open = os.open
def racing_open(path, flags, *args, **kw):
    if path == 'race.py':
        os.rename('race.py', 'saved.bin')
        with open('race.py', 'w') as f: f.write('after')
    return original_open(path, flags, *args, **kw)
os.open = racing_open''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b'')
        self.assertIn(b'skipped_changed=1', result.stderr)

    def test_original_fifo_reproduces_and_hotfix_skips(self):
        os.mkfifo(str(self.root / 'DECISION_PART2.json'))
        started = time.monotonic()
        original = subprocess.run(['timeout', '--kill-after=0.1', '0.15'] + PY +
                                  [str(INPUT / 'lane_code_filter.py.orig'), 'original'],
                                  cwd=str(self.root), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2)
        elapsed = time.monotonic() - started
        self.assertEqual(original.returncode, 124, original.stderr)
        hotfix = self.scan(False, INPUT / 'lane_code_filter.py')
        self.assertEqual(hotfix.returncode, 0, hotfix.stderr)
        self.assertEqual(hotfix.stdout, b'')
        print('MEASURE original_fifo_timeout_rc=124 elapsed=%.3fs hotfix_rc=0' % elapsed, flush=True)

