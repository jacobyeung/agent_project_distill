"""Run the unchanged filter with stdout redirected to /dev/null; meter selected paths."""
import collections
import json
import os
from pathlib import Path
import runpy
import stat
import sys

script, label, destination = sys.argv[1:4]
counts = collections.defaultdict(lambda: [0, 0])
errors = []
original = sys.stdout

class Meter:
    def __init__(self):
        self.buffer = self
        self.pending = b''

    def write(self, data):
        written = original.buffer.write(data)
        self.pending += data
        while b'\0' in self.pending:
            raw, self.pending = self.pending.split(b'\0', 1)
            path = os.fsdecode(raw)
            lane = path.split('/')[0] if '/' in path else '(root files)'
            counts[lane][0] += 1
            try:
                info = os.stat(path, follow_symlinks=False)
                if not stat.S_ISREG(info.st_mode):
                    raise ValueError('selected file is no longer regular')
                counts[lane][1] += info.st_size
            except (OSError, ValueError) as error:
                errors.append([path, str(error)])
        return written

    def flush(self):
        original.flush()

meter = Meter()
sys.stdout = meter
sys.argv = [script, label]
try:
    runpy.run_path(script, run_name='__main__')
finally:
    sys.stdout = original
    result = dict(lanes=sorted(([k] + v for k, v in counts.items()), key=lambda r: (-r[2], r[0])),
                  files=sum(v[0] for v in counts.values()), bytes=sum(v[1] for v in counts.values()),
                  errors=errors, pending_bytes=len(meter.pending))
    Path(destination).write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
