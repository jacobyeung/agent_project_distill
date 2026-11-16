"""Bounded unittest runner and changed-statement coverage, using only stdlib tracing."""
import ast
import difflib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

LANE = Path(__file__).resolve().parents[2]
TREE = Path(os.environ.get('BUILD1_TEST_TREE', str(LANE/'work/tree_r1')))
BASE = LANE/'work/base/tree_b01ce449'
TMP = LANE/'work/tmp'
sys.path.insert(0, str(TREE))
os.environ.update(TMPDIR=str(TMP), LANE_TEST_OUTPUT=str(TMP), HF_HUB_OFFLINE='1',
                  XDG_CACHE_HOME=str(TMP/'cache'), HF_HOME=str(TMP/'hf'), TORCH_HOME=str(TMP/'torch'),
                  GF1_BASE_TREE=str(BASE))
tempfile.tempdir = str(TMP)


def boundary(event, args):
    if event in ('socket.bind', 'socket.connect'):
        raise OSError('Build brief forbids network, including test sockets')
    if event in ('os.remove', 'os.rmdir'):
        raise PermissionError('Build brief retains all test artifacts')
    if event == 'open' and isinstance(args[0], (str, bytes)):
        path = Path(os.fsdecode(args[0]))
        if path.is_absolute() and (path.parts[1] == 'home' or path.parts[1].startswith('data')):
            raise PermissionError('Build brief forbids unnamed shared-storage reads')


sys.addaudithook(boundary)


def size(path):
    return sum(p.stat().st_size for p in path.rglob('*') if p.is_file())


def guard():
    value = size(TMP)
    if value > 200_000_000:
        raise RuntimeError('Temporary folder exceeds the 200 MB test limit')
    if size(LANE) > 2_000_000_000:
        raise RuntimeError('Lane exceeds the build storage limit')
    return value


class RetainedDirectory:
    """Keep test artifacts for review; this lane never cleans directories."""
    def __init__(self, *args, **kwargs):
        self.name = tempfile.mkdtemp(prefix=kwargs.get('prefix', 'retained_'), dir=TMP)
    def __enter__(self):
        return self.name
    def __exit__(self, *args):
        pass
    def cleanup(self):
        pass


tempfile.TemporaryDirectory = RetainedDirectory
changed = {}
for path in TREE.rglob('*.py'):
    relative = path.relative_to(TREE)
    original = BASE/relative
    source = path.read_text()
    old = original.read_text() if original.exists() else ''
    if source == old:
        continue
    lines = set()
    for tag, _, _, start, stop in difflib.SequenceMatcher(None, old.splitlines(), source.splitlines(), autojunk=False).get_opcodes():
        if tag in ('insert', 'replace'):
            lines.update(range(start+1, stop+1))
    nodes = ast.walk(ast.parse(source))
    statements = {node.lineno for node in nodes if isinstance(node, ast.stmt)
                  and not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant))
                  and lines.intersection(range(node.lineno, node.end_lineno+1))}
    changed[str(path)] = statements
hits = {path: set() for path in changed}


def trace(frame, event, arg):
    path = frame.f_code.co_filename
    if path not in hits:
        return None
    if event == 'line':
        hits[path].add(frame.f_lineno)
    return trace


class Result(unittest.TextTestResult):
    records = []
    def startTest(self, test):
        self.before = guard()
        self.started = time.monotonic()
        super().startTest(test)
    def stopTest(self, test):
        after = guard()
        self.records.append(dict(test=test.id(), tmp_before=self.before, tmp_after=after,
                                 seconds=time.monotonic()-self.started))
        super().stopTest(test)


sys.settrace(trace)
names = sys.argv[1:] or ['tests.test_r2_data_path']
suite = unittest.defaultTestLoader.loadTestsFromNames(names)
result = unittest.TextTestRunner(verbosity=2, resultclass=Result).run(suite)
sys.settrace(None)
output = LANE/'out'
prefix = os.environ.get('BUILD1_RESULT_PREFIX', '')
coverage = {str(Path(path).relative_to(TREE)): dict(changed_statements=len(lines), executed=len(lines & hits[path]),
            uncovered=sorted(lines-hits[path]), executed_lines=sorted(lines & hits[path])) for path, lines in changed.items()}
(output/(prefix+'COVERAGE.json')).write_text(json.dumps(coverage, indent=2)+'\n')
(output/(prefix+'TEST_RESULTS.json')).write_text(json.dumps(dict(tests=result.testsRun, failures=[(str(t), s) for t,s in result.failures],
    errors=[(str(t), s) for t,s in result.errors], skipped=[(str(t), s) for t,s in result.skipped],
    records=result.records, tmp_bytes=guard(), lane_bytes=size(LANE)), indent=2)+'\n')
raise SystemExit(not result.wasSuccessful())
