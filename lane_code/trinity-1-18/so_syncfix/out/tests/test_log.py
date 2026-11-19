from support import *


class BoundedLogTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='tmp_log_', dir=str(FIXTURES)))
        self.log = self.root / 'run.log'

    def run_log(self, code, append='0'):
        return subprocess.run(PY + [str(TOOLS / 'lane_code_log.py'), str(self.log), '-', append] +
                              PY + ['-c', code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)

    def test_regular_fd_stays_capped_while_other_files_can_grow(self):
        payload = self.root / 'payload'
        code = '''import os, stat
assert stat.S_ISREG(os.fstat(1).st_mode)
with open(%r, 'wb') as f: f.write(b'z' * 200000)
try:
    for i in range(100): os.write(1, b'x' * 4096)
except OSError:
    pass
assert os.fstat(1).st_size == 65536
''' % str(payload)
        result = self.run_log(code)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.log.stat().st_size, 65536)
        self.assertEqual(payload.stat().st_size, 200000)

    def test_append_and_reuse_are_bounded(self):
        self.assertEqual(self.run_log('print("first")').returncode, 0)
        self.assertEqual(self.run_log('print("second")', '1').returncode, 0)
        self.assertEqual(self.log.read_bytes(), b'first\nsecond\n')
        self.assertEqual(self.run_log('print("replacement")').returncode, 0)
        self.assertEqual(self.log.read_bytes(), b'replacement\n')

    def test_late_detached_writer_cannot_mutate_saved_log(self):
        pid = self.root / 'holder.pid'
        child = "import os,time;os.setsid();open(%r,'w').write(str(os.getpid()));time.sleep(0.5);os.write(1,b'late');time.sleep(1)" % str(pid)
        code = 'import subprocess,sys; subprocess.Popen([sys.executable,"-I","-s","-B","-c",%r]); print("done")' % child
        started = time.monotonic()
        result = self.run_log(code)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLess(time.monotonic() - started, 0.5)
        self.assertEqual(self.log.read_bytes(), b'done\n')
        time.sleep(0.6)
        self.assertEqual(self.log.read_bytes(), b'done\n')
        os.kill(int(pid.read_text()), 0)
