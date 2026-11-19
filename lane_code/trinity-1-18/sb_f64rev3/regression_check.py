"""Run the original focused suite with retained, workspace-only test outputs."""
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT.parent / 'sb_f64'
PKG = SRC / 'pkg'
mode = sys.argv[1]
tree = PKG / 'work' / ('tree_r1' if mode == 'baseline' else 'tree_f64')
proof = ROOT / 'proofs' / mode
proof.mkdir(parents=True, exist_ok=True)
tmp = ROOT / 'tmp' / mode
tmp.mkdir(parents=True, exist_ok=True)
os.environ.update(R2_TREE=str(tree), R2_FIXTURES=str(PKG / 'fixtures'), R2_PROOFS=str(proof),
                  R2_LANE_ROOT=str(PKG), LANE_TEST_OUTPUT=str(tmp), TMPDIR=str(tmp))
sys.path[:0] = [str(tree), *[str(PKG / 'work' / p) for p in ('n1fix2', 'build18', 'build16', 'build17')]]
tempfile.tempdir = str(tmp)
class RetainedDirectory:
    def __init__(self, suffix=None, prefix=None, dir=None, **kw):
        self.name = tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=str(tmp))
    def __enter__(self): return self.name
    def __exit__(self, *args): return False
    def cleanup(self): pass
tempfile.TemporaryDirectory = RetainedDirectory
read_paths = set()
def guard(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes)):
        p = Path(os.fsdecode(args[0])).absolute()
        flags = args[2] or 0
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            if not p.is_relative_to(ROOT):
                raise RuntimeError('Review refuses write outside workspace: ' + str(p))
        elif p.is_relative_to(SRC) or p.is_relative_to(ROOT.parent / 'sb_f64fix2'):
            read_paths.add(str(p))
    if event in ('os.remove', 'os.rmdir'):
        raise RuntimeError('Review retains test outputs: ' + str(args))
sys.addaudithook(guard)
import torch
torch.set_num_threads(8)
names = ['tests.test_r1_build18', 'tests.test_r1_build17', 'tests.test_r1_export17', 'tests.test_r1_build16',
         'tests.test_r1_build15', 'tests.test_r1_build14', 'tests.test_r2_build_n1', 'tests.test_r2_n1fix',
         'tests.test_r2_n1fix3', 'tests.test_r2_build12', 'tests.test_r1_build13',
         'tests.test_r2_build3.Build3.test_opener_export_keep_and_reset',
         'export_mutation17.HashTwin.test_same_size_shard_refuses', 'tests.test_r2_build8_frames', 'tests.test_carrier_c1_cp2']
suite = unittest.defaultTestLoader.loadTestsFromNames(names)
result = unittest.TextTestRunner(verbosity=2).run(suite)
provenance = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__), ROOT/'run_cpu.sh')}
for path in sorted(read_paths):
    p = Path(path)
    if p.is_file(): provenance[path] = hashlib.sha256(p.read_bytes()).hexdigest()
value = dict(command='bash run_cpu.sh regression_check.py ' + mode, input_sha256=provenance,
             tests=result.testsRun, failures=[(str(t), msg) for t, msg in result.failures],
             errors=[(str(t), msg) for t, msg in result.errors], skipped=[(str(t), msg) for t, msg in result.skipped])
(ROOT / 'out' / (mode + '_regression.json')).write_text(json.dumps(value, indent=2) + '\n')
