"""Review regressions. All large manifests are synthetic; all network/Git calls are fake."""
from support import *
import tarfile
import io


class ReviewFilterTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='review_filter_', dir=str(FIXTURES)))

    def run_filter(self, injection, limit='120'):
        source = TOOLS / 'lane_code_filter.py'
        code = ('import os, sys, gzip, time, hashlib\n' + injection + '\n'
                'sys.argv = [%r, "fixture", "meta"]\n' % str(source) +
                'exec(compile(open(sys.argv[0]).read(), sys.argv[0], "exec"))\n')
        env = dict(os.environ, LCS_ROBUST_SYNC='1', LCS_FILE_SECONDS='3')
        return subprocess.run(['timeout', '--kill-after=5', limit] + PY + ['-c', code],
                              cwd=str(self.root), env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=float(limit) + 8)

    def test_750000_duplicate_manifest_default_budgets(self):
        injection = '''
source = %r
lines = ["lane/fixture/" + hashlib.sha256(str(i).encode()).hexdigest() + "/record.json\\t"
         + "lane/kept/" + hashlib.sha256(str(i %% 1700).encode()).hexdigest() + ".json"
         for i in range(750000)]
def trace(frame, event, arg):
    if event == 'line' and frame.f_code.co_filename == source and frame.f_code.co_name == 'robust_scan':
        if frame.f_lineno == manifest_line:
            frame.f_locals['dups'].extend(lines)
            sys.settrace(None)
    return trace
manifest_line = next(i for i, line in enumerate(open(source), 1) if line == '        if mdir:\\n')
sys.settrace(trace)
''' % str(TOOLS / 'lane_code_filter.py')
        started = time.monotonic()
        result = self.run_filter(injection)
        elapsed = time.monotonic() - started
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = self.root / 'meta' / 'DEDUP_fixture.tsv.gz'
        with gzip.open(str(manifest), 'rb') as f:
            lines = 0
            raw_bytes = 0
            for line in f:
                lines += 1
                raw_bytes += len(line)
        self.assertEqual(lines, 750000)
        self.assertEqual(list((self.root / 'meta').glob('.dedup-*')), [])
        print('MEASURE large_manifest lines=%d raw_bytes=%d gzip_bytes=%d elapsed=%.3fs file_budget=3 scan_budget=120' %
              (lines, raw_bytes, manifest.stat().st_size, elapsed), flush=True)

    def test_manifest_exception_logs_every_leftover_and_preserves_final(self):
        write(self.root / 'meta' / 'DEDUP_fixture.tsv.gz', 'prior-manifest')
        result = self.run_filter('''
def broken_write(self, data):
    raise OSError('injected manifest disk failure')
gzip.GzipFile.write = broken_write
''')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.root / 'meta' / 'DEDUP_fixture.tsv.gz').read_text(), 'prior-manifest')
        leftovers = list((self.root / 'meta').glob('.dedup-*'))
        self.assertLessEqual(len(leftovers), 1)
        self.assertEqual(len(leftovers), 1)
        self.assertIn(str(leftovers[0].relative_to(self.root)).encode(), result.stderr)
        self.assertIn(b'MANIFEST_PENDING', result.stderr)

    def test_manifest_scan_timeout_logs_pending_name(self):
        result = self.run_filter('''
original_write = gzip.GzipFile.write
def slow_write(self, data):
    time.sleep(4)
    return original_write(self, data)
gzip.GzipFile.write = slow_write
''', '0.2')
        self.assertEqual(result.returncode, 124)
        leftovers = list((self.root / 'meta').glob('.dedup-*'))
        self.assertEqual(len(leftovers), 1)
        self.assertIn(str(leftovers[0].relative_to(self.root)).encode(), result.stderr)


class ReviewDriverTests(DriverFixture):
    def test_slots_reused_and_failed_attempt_never_scanned(self):
        result = self.run_driver()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        slots = self.state / 'stage-robust'
        self.assertTrue(slots.is_dir())
        accepted = slots / 'trinity-1-18' / 'accepted'
        old_hash = hashlib.sha256(accepted.read_bytes()).hexdigest()
        names = sorted(str(p.relative_to(slots)) for p in slots.rglob('*'))
        first_bytes = sum(p.stat().st_size for p in slots.rglob('*') if p.is_file())
        write(self.root / 'sources' / 'trinity-1-18' / 'failure_only.py', 'never publish this')
        self.env['FAKE_trinity_1_18'] = 'partial'
        result = self.run_driver()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(hashlib.sha256(accepted.read_bytes()).hexdigest(), old_hash)
        self.assertFalse((self.repo / 'lane_code' / 'trinity-1-18' / 'failure_only.py').exists())
        self.assertNotIn(b'[copy trinity-1-18]', result.stdout)
        # Move the source fixture aside without deleting; the next success must not leak it.
        os.rename(str(self.root / 'sources' / 'trinity-1-18' / 'failure_only.py'),
                  str(self.root / 'sources' / 'trinity-1-18' / 'failure_only.bin'))
        self.env['FAKE_trinity_1_18'] = 'success'
        for unused in range(2):
            result = self.run_driver()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.repo / 'lane_code' / 'trinity-1-18' / 'failure_only.py').exists())
        self.assertFalse((self.state / 'stage-runs').exists())
        self.assertEqual(names, sorted(str(p.relative_to(slots)) for p in slots.rglob('*')))
        total = 0
        for label in ('trinity-1-18', 'trinity-2-28', 'trinity-3-30', 'orch_n30/tools', 'orch_n30/briefs'):
            slot = slots / label
            amounts = {p.name: p.stat().st_size for p in slot.iterdir() if p.is_file()}
            total += sum(amounts.values())
            print('MEASURE slot=%s bytes=%s total=%d' % (label, json.dumps(amounts, sort_keys=True), sum(amounts.values())), flush=True)
        print('MEASURE slots_initial_bytes=%d slots_final_bytes=%d runs=4' % (first_bytes, total), flush=True)

    def test_missing_root_has_no_fail_or_blocker(self):
        self.env['FAKE_trinity_1_18'] = 'missing'
        result = self.run_driver()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(b'SKIP trinity-1-18 (no source root)', result.stdout)
        self.assertNotIn(b'FAIL', result.stdout)
        self.assertEqual(list((self.root / 'events').iterdir()), [])

    def test_optional_unreachable_node_is_skip(self):
        self.env['FAKE_trinity_2_28'] = 'unreachable'
        result = self.run_driver()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(b'SKIP trinity-2-28 (unreachable', result.stdout)
        self.assertNotIn(b'FAIL', result.stdout)
        self.assertEqual(list((self.root / 'events').iterdir()), [])

    def test_initialization_errors_all_emit_blocker(self):
        for failure in ('missing_helper', 'bad_budget', 'slot_mkdir'):
            with self.subTest(failure=failure):
                helper = self.b / 'tools' / 'lane_code_stage.sh'
                saved = helper.read_bytes()
                if failure == 'missing_helper':
                    helper.write_text('return 2\n')
                elif failure == 'bad_budget':
                    self.env['LCS_NODE_SECONDS'] = '0'
                else:
                    write(self.state / 'stage-robust', 'not a directory')
                result = self.run_driver()
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                events = list((self.root / 'events').glob('*_BLOCKER_sync_failed.md'))
                self.assertTrue(events, result.stdout + result.stderr)
                self.assertIn('code_sync run failed', events[-1].read_text())
                helper.write_bytes(saved)
                self.env['LCS_NODE_SECONDS'] = '1.3'

    def test_file_deadline_driver_and_filter_agree(self):
        self.env['LCS_FILE_SECONDS'] = '30.1'
        result = self.run_driver()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn(b'invalid LCS_FILE_SECONDS=30.1', result.stdout)
        self.assertFalse((self.root / 'ssh.jsonl').exists())

    def test_regular_flag_enables_without_environment(self):
        self.env.pop('LCS_ROBUST_SYNC')
        write(self.state / 'LCS_ROBUST_SYNC', '')
        result = self.run_driver(('--dry',))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(b'ROBUST', result.stdout)
        self.assertIn(b'STAGED trinity-2-28', result.stdout)

    def test_tar_exit_one_quarantines_node_but_publishes_other_sources(self):
        write(self.bin / 'tar', '#!/bin/bash\n/usr/bin/tar "$@"\nrc=$?\n'
              'if [[ "$PWD" == */sources/trinity-1-18 ]] && [[ " $* " == *" -cf "* ]]; then\n'
              '  echo "tar: file changed as we read it" >&2; exit 1\n'
              'fi\nexit "$rc"\n', True)
        result = self.run_driver()
        self.check_partial_success(result)
        self.assertIn(b'PIPE 0 1 0', result.stdout)
        self.assertIn(b'not published: archive may contain changed or incomplete files', result.stdout)


class ReviewCopyTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='review_copy_', dir=str(FIXTURES)))

    def test_copy_timeout_cannot_commit_a_truncated_file(self):
        stage = self.root / 'stage'
        dest = self.root / 'repo' / 'lane_code' / 'fixture'
        write(stage / 'good.py', 'complete-new-file' * 1000)
        write(dest / 'good.py', 'complete-prior-file')
        source = TOOLS / 'lane_code_scan.py'
        pending = self.root / 'repo' / '.lcs-copy.pending'
        code = '''import os, sys, shutil, time
original_replace = os.replace
def slow_copy(source, dest):
    with open(dest, 'wb') as f:
        f.write(b'truncated'); f.flush(); time.sleep(5)
def slow_replace(source, dest, *a, **kw):
    time.sleep(5)
    return original_replace(source, dest, *a, **kw)
shutil.copyfile = slow_copy
os.replace = slow_replace
sys.argv = %r
exec(compile(open(sys.argv[0]).read(), sys.argv[0], 'exec'))
''' % [str(source), str(stage), str(dest), str(self.root / 'flags' / 'flags.txt')]
        env = dict(os.environ, LCS_ROBUST_SYNC='1', LCS_COPY_TMP=str(pending))
        result = subprocess.run(['timeout', '--kill-after=0.1', '0.2'] + PY + ['-c', code], env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2)
        self.assertEqual(result.returncode, 124, result.stderr)
        self.assertEqual((dest / 'good.py').read_text(), 'complete-prior-file')
        self.assertEqual(sorted(p.name for p in dest.iterdir()), ['good.py'])
        self.assertTrue(pending.is_file())
        self.assertIn(str(pending).encode(), result.stderr)

    def test_default_off_copy_matches_input(self):
        stage = self.root / 'stage'
        write(stage / 'good.py', 'clean\n')
        write(stage / 'secret.txt', 'ghp_' + 'a' * 32)
        outputs = []
        trees = []
        for name, source in (('input', INPUT / 'lane_code_scan.py'), ('new', TOOLS / 'lane_code_scan.py')):
            dest = self.root / name
            flags = self.root / (name + '.flags')
            result = subprocess.run(PY + [str(source), str(stage), str(dest), str(flags)],
                                    env=dict(os.environ, LCS_ROBUST_SYNC='0'), stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, timeout=3)
            self.assertEqual(result.returncode, 0, result.stderr)
            outputs.append((result.stdout.replace(str(flags).encode(), b'<FLAGS>'), result.stderr, flags.read_bytes()))
            trees.append({str(p.relative_to(dest)): p.read_bytes() for p in dest.rglob('*') if p.is_file()})
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(trees[0], trees[1])
