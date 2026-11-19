"""The separately delivered wrapper patch opts new reads into integrity checks."""
from pathlib import Path
import subprocess
import unittest

import ingest_read


class NewReadWrapperTests(unittest.TestCase):
    def test_wrapper_enables_checks_without_caller_flag(self):
        wrapper = Path(ingest_read.__file__).parent / 'add_read.sh'
        line = next(line for line in wrapper.read_text().splitlines()
                    if line.startswith('python3 tool/ingest_read.py ingest '))
        # Run only argument construction. Publication and source loading never run.
        script = '''python3() { printf '%s\\n' "$@"; }
tee() { cat; }
SRC='source package' RID=new_read_id M=metadata
set -- --inputs 'input package' --archive-partial
''' + line
        result = subprocess.run(['bash', '-c', script], text=True,
                                capture_output=True, check=True)
        args = result.stdout.splitlines()
        self.assertEqual(args.count('--review2-checks'), 1)
        self.assertEqual(args[args.index('--source') + 1], 'source package')
        self.assertEqual(args[args.index('--read-id') + 1], 'new_read_id')
        self.assertEqual(args[-3:], ['--inputs', 'input package', '--archive-partial'])
