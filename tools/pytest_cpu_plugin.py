"""Pytest plugin for hermetic CPU runs; loaded only by tools/test_cpu.sh (-p pytest_cpu_plugin).

It puts the repository root on sys.path, points the test-output variables at a fresh directory under
TMPDIR, and leaves out every path listed under ``cpu_skip`` in tools/pytest_cpu.ini, printing each one
with its reason. Plain pytest never loads this file.
"""
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_VARS = ('H5_TEST_OUTPUT', 'COMPACT_TEST_OUTPUT', 'STUDENT_DATASET_TEST_OUTPUT',
               'STUDENT_PILOT_TEST_OUTPUT')

_skips = []
_hits = {}


def pytest_addoption(parser):
    parser.addini('cpu_skip', type='linelist', default=[],
                  help='"<repo-relative path> :: <reason>" lines; tests under the path are not collected')


def _parse(lines):
    out = []
    for line in lines:
        rel, sep, reason = line.partition('::')
        rel = rel.strip().rstrip('/')
        if not sep or not rel or not reason.strip():
            raise ValueError('cpu_skip line needs "<path> :: <reason>": %r' % line)
        out.append((os.path.join(REPO, rel), rel, reason.strip()))
    return out


def pytest_configure(config):
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    root = tempfile.mkdtemp(prefix='cpu_tests_')
    for name in OUTPUT_VARS:
        path = os.path.join(root, name.lower())
        os.makedirs(path)
        os.environ[name] = path
    _skips[:] = _parse(config.getini('cpu_skip'))


def pytest_report_header(config):
    lines = ['cpu plugin: repo %s; test outputs under %s' % (REPO, os.path.dirname(os.environ[OUTPUT_VARS[0]]))]
    lines += ['cpu skip: %s (%s)' % (rel, reason) for _, rel, reason in _skips]
    return lines


def pytest_ignore_collect(collection_path, config):
    p = str(collection_path)
    for full, rel, reason in _skips:
        if p == full or p.startswith(full + os.sep):
            _hits[rel] = reason
            return True
    return None


def pytest_terminal_summary(terminalreporter):
    for rel in sorted(_hits):
        terminalreporter.write_line('SKIPPED (not collected) %s: %s' % (rel, _hits[rel]))
