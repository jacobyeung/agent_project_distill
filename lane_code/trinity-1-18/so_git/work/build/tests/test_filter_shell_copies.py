import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]


class ShellCopiesTests(unittest.TestCase):
    def setUp(self):
        parent = BASE / 'work' / 'filter_tests'
        parent.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix='copies_', dir=parent))
        (self.root / 'script.py').write_text('x=1\n')
        (self.root / 'tick.sh.copy').write_text('#!/bin/bash\necho tick\n')
        (self.root / 'blob.copy').write_text('not code\n')
        (self.root / 'large.sh.copy').write_bytes(b'#' * (512 * 1024 + 1))
        (self.root / 'runs').mkdir()
        (self.root / 'runs' / 'hidden.sh.copy').write_text('echo hidden\n')

    def selected(self, enabled):
        env = dict(os.environ)
        env.pop('LCS_INCLUDE_SHELL_COPIES', None)
        if enabled:
            env['LCS_INCLUDE_SHELL_COPIES'] = '1'
        result = subprocess.run([sys.executable, '-I', '-s', '-B', str(BASE / 'tools' / 'lane_code_filter.py'), 'test'],
                                cwd=self.root, env=env, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        return {x.decode() for x in result.stdout.split(b'\0') if x}, result.stderr

    def test_default_off(self):
        paths, _ = self.selected(False)
        self.assertEqual(paths, {'script.py'})

    def test_opt_in_adds_only_small_shell_copies(self):
        paths, _ = self.selected(True)
        self.assertEqual(paths, {'script.py', 'tick.sh.copy'})


if __name__ == '__main__':
    unittest.main()
