"""Run the existing offline suites with every fixture confined to evidence/test_*.

The original reference source and pins stay intact. Path construction redirects
only fixture names, generated test reports and preparation ledgers. An audit hook
rejects all other writes, deletions, process launches and network operations.
"""
import argparse
import os
from pathlib import Path
import runpy
import sys
import unittest
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('suite', choices=('candidate', 'ported', 'reference', 'refute', 'runtime', 'targeted', 'pins'))
args = parser.parse_args()
work = ROOT/'evidence'/('test_fix3_'+args.suite+'_'+uuid.uuid4().hex)
work.mkdir()
print('Fixture root:', work, flush=True)
original_join = Path.__truediv__
evidence_roots = (ROOT/'evidence', ROOT/'readk/evidence')
ledger_roots = (ROOT, ROOT/'readk')
report_paths = {ROOT/'evidence'/name for name in ('D0_SELF_PAIR.json', 'RUNTIME_FIXTURE.json')}
original_open = Path.open

def joined(path, child):
    value = original_join(path, child)
    if value.parent in evidence_roots and value.name.startswith(('test_', 'chain_', 'fix1_', 'fix1c_', 'runtime_')):
        return original_join(work, value.name)
    if path in ledger_roots and str(child) == 'LEDGER.jsonl':
        return work/('reference_LEDGER.jsonl' if path.name == 'readk' else 'LEDGER.jsonl')
    return value


def opened(path, mode='r', *args, **kwargs):
    if path in report_paths and any(flag in mode for flag in 'wax+'):
        path = work/path.name
    return original_open(path, mode, *args, **kwargs)


def audit(event, values):
    if event in {'os.remove', 'os.rmdir'}:
        raise RuntimeError('Offline fixture guard: '+event)
    paths = []
    if event == 'open' and not isinstance(values[0], int):
        flags = values[2]
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            paths = values[:1]
    elif event in ('os.mkdir', 'os.chmod'):
        paths = values[:1]
    elif event in ('os.rename', 'os.link', 'os.symlink'):
        paths = values[:2]
    for value in paths:
        path = Path(value).absolute()
        if not path.is_relative_to(work) or not path.resolve().is_relative_to(work):
            raise RuntimeError('Write outside fixture root: '+str(path))

sys.addaudithook(audit)
reference = args.suite == 'reference'
test_root = ROOT/'readk' if reference else ROOT
os.chdir(test_root)
sys.path[:0] = [str(test_root/'tests'), str(test_root)]
import offline_guard
with patch.object(Path, '__truediv__', joined), patch.object(Path, 'open', opened):
    if args.suite == 'runtime':
        runpy.run_path(str(ROOT/'tests/runtime_fixture.py'), run_name='__main__')
    else:
        loader = unittest.defaultTestLoader
        if args.suite in ('candidate', 'reference', 'refute'):
            suite = loader.discover(str(test_root/'tests'), pattern='test_refute.py' if args.suite == 'refute' else 'test_*.py')
        else:
            names = {'ported': ['test_kit', 'test_chain', 'test_verdict'],
                     'targeted': ['test_fix3'], 'pins': ['test_kit.KitTests.test_final_pins_match']}[args.suite]
            suite = loader.loadTestsFromNames(names)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        sys.exit(not result.wasSuccessful())
