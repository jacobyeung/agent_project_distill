"""Sandboxed unittest runner: python runtests.py TREE LABEL OUT.json TMP (discover | module ...)

Denies reads of /home and /data*, subprocesses, sockets and writes outside TMP;
deletions become logged no-ops. Records every test and subtest outcome.
"""
import json
import os
import re
import shutil
import sys
import time
import traceback
import unittest
from pathlib import Path

TREE = Path(sys.argv[1]).resolve()
LABEL, OUT, TMP = sys.argv[2], Path(sys.argv[3]).resolve(), Path(sys.argv[4]).resolve()
TARGETS = sys.argv[5:]
TMP.mkdir(parents=True, exist_ok=False)
(TMP/'home').mkdir()
(TMP/'proofs').mkdir()
if os.environ.get('RUNTESTS_OUTPUT_VARS') == '1':
    for var in ('LANE_TEST_OUTPUT', 'STUDENT_PILOT_TEST_OUTPUT', 'B9_TEST_OUTPUT', 'B2_TEST_OUTPUT'):
        (TMP/var.lower()).mkdir()
        os.environ[var] = str(TMP/var.lower())
WRITABLE = (str(TMP)+'/',) + ((str(TREE/'artifacts')+'/', str(TREE/'artifacts')) if os.environ.get('RUNTESTS_OUTPUT_VARS') == '1' else ())
os.environ.update(TMPDIR=str(TMP), HOME=str(TMP/'home'), XDG_CACHE_HOME=str(TMP/'cache'), R2_PROOFS=str(TMP/'proofs'),
                  HF_HOME=str(TMP/'hf'), TRITON_CACHE_DIR=str(TMP/'triton'), MPLCONFIGDIR=str(TMP/'mpl'))
os.chdir(TREE)
sys.path.insert(0, str(TREE))
DENIED, DELETED = [], []
NFS = re.compile(r'^/(home|data\d*)(/|$)')


def norm(s):
    return str(s).replace(str(TREE), '<TREE>').replace(str(TMP), '<TMP>')


SANDBOX = [True]


def hook(event, args):
    if not SANDBOX[0]:
        return
    if event == 'open':
        path = args[0]
        if isinstance(path, int):
            return
        p = os.path.abspath(os.fsdecode(path))
        mode = str(args[1] or '')
        flags = args[2] if len(args) > 2 and isinstance(args[2], int) else 0
        if NFS.match(p):
            DENIED.append(('read', norm(p)))
            raise PermissionError('sandbox: NFS path denied: '+p)
        writing = any(c in mode for c in 'wax+') or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT)
        if writing and not (p.startswith(WRITABLE) or p == '/dev/null'):
            DENIED.append(('write', norm(p)))
            raise PermissionError('sandbox: write outside TMP denied: '+p)
    elif event in ('os.listdir', 'os.scandir'):
        p = args[0]
        if isinstance(p, (str, bytes, os.PathLike)) and NFS.match(os.path.abspath(os.fsdecode(p))):
            DENIED.append(('list', norm(os.fsdecode(p))))
            raise PermissionError('sandbox: NFS listing denied')
    elif event in ('subprocess.Popen', 'os.system', 'os.exec', 'os.posix_spawn', 'os.spawn', 'os.fork', 'pty.spawn'):
        DENIED.append(('process', event))
        raise PermissionError('sandbox: process launch denied: '+event)
    elif event in ('socket.connect', 'socket.bind', 'socket.getaddrinfo'):
        DENIED.append(('socket', event))
        raise PermissionError('sandbox: network denied')
    elif event in ('os.mkdir', 'os.rename', 'os.symlink', 'os.link', 'os.chmod'):
        p = args[0]
        if isinstance(p, (str, bytes, os.PathLike)):
            p = os.path.abspath(os.fsdecode(p))
            if not (p.startswith(WRITABLE) or p in WRITABLE):
                DENIED.append((event, norm(p)))
                raise PermissionError('sandbox: '+event+' outside TMP denied: '+p)


def nodelete(name):
    def f(path, *a, **k):
        DELETED.append((name, norm(os.fsdecode(path) if isinstance(path, (str, bytes, os.PathLike)) else path)))
    return f


os.remove = nodelete('os.remove')
os.unlink = nodelete('os.unlink')
os.rmdir = nodelete('os.rmdir')
shutil.rmtree = nodelete('shutil.rmtree')
sys.addaudithook(hook)


def short(err):
    if err is None:
        return None
    etype, value, _ = err
    text = norm(''.join(traceback.format_exception_only(etype, value)).strip().splitlines()[-1])
    return re.sub(r'0x[0-9a-f]+', '0x', re.sub(r'<TMP>/[^\s\'"]*', '<TMP>/...', text))[:400]


class Result(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.rows = {}

    def put(self, test, status, err=None):
        key = test.id()
        self.rows.setdefault(key, []).append([status, short(err)])

    def addSuccess(self, test): self.put(test, 'pass')
    def addFailure(self, test, err): self.put(test, 'fail', err)
    def addError(self, test, err): self.put(test, 'error', err)
    def addSkip(self, test, reason): self.rows.setdefault(test.id(), []).append(['skip', norm(reason)[:200]])
    def addExpectedFailure(self, test, err): self.put(test, 'xfail', err)
    def addUnexpectedSuccess(self, test): self.put(test, 'xpass')

    def addSubTest(self, test, subtest, err):
        key = subtest.id()
        if err is None:
            self.rows.setdefault(key, []).append(['pass', None])
        else:
            status = 'fail' if issubclass(err[0], test.failureException) else 'error'
            self.rows.setdefault(key, []).append([status, short(err)])


loader = unittest.TestLoader()
result = Result()
if TARGETS == ['discover']:
    TARGETS = ['tests.'+p.stem for p in sorted((TREE/'tests').glob('test*.py'))]
if True:
    suite = unittest.TestSuite()
    for t in TARGETS:
        try:
            suite.addTest(loader.loadTestsFromName(t))
        except Exception:  # noqa: BLE001
            result.rows.setdefault('loader:'+t, []).append(['error', short(sys.exc_info())])
start = time.time()
suite.run(result)
statuses = [s for v in result.rows.values() for s, _ in v]
counts = dict(tests=result.testsRun, rows=len(result.rows), **{s: statuses.count(s) for s in sorted(set(statuses))})
SANDBOX[0] = False
OUT.write_text(json.dumps(dict(tree=str(TREE), label=LABEL, targets=TARGETS, counts=counts, seconds=round(time.time()-start, 1),
                               denied=DENIED, deleted=DELETED, rows=result.rows), indent=0, sort_keys=True)+'\n')
print(LABEL, json.dumps(counts), 'denied', len(DENIED), 'deleted', len(DELETED))
