"""Local stub dry run of the delivered supervisor: CPU check, preflight and both GPU groups (no GPU, no Orchard)."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
WORK = Path('/scratch/jjyeung/orch_n30/lever6/k5b/work')
SRC = Path('/scratch/jjyeung/orch_n30/lever5/k5/work')   # read-only: old package code and frames
OLD0 = SRC/'old0'
FRAMES = SRC/'f'
PY = '/scratch/jjyeung/envs/p1cpu/bin/python'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def hx(v):
    return v.encode().hex()


class FakeJob:
    """Local stand-ins for the staged namespace, environment and path mapping."""
    @staticmethod
    def namespace(root):
        return []

    @staticmethod
    def environment(root):
        env = dict(PATH='/usr/bin:/bin', HOME=str(root), SLURM_JOB_ID=os.environ['SLURM_JOB_ID'],
                   PYTHONDONTWRITEBYTECODE='1')
        if os.environ.get('K5_STUB_REFUSE'):
            env['K5_STUB_REFUSE'] = os.environ['K5_STUB_REFUSE']
        return env

    @staticmethod
    def physical(root, path):
        return Path(path)


class FakeCommon:
    calls = []

    @classmethod
    def opaque(cls, argv):
        sys.path.insert(0, str(OLD0))
        from orchard_h10.common import opaque
        opaque(argv)
        cls.calls.append(list(argv))


def setup(tag, refuse=False):
    work = Path(tempfile.mkdtemp(prefix='dry_'+tag+'_', dir=WORK))
    token = (ROOT/'TOKEN').read_text().strip()
    p = work/token
    p.mkdir()
    for n in ('0.py', '1.json', '2.py', '3.json', '8.gz', '9.py'):
        shutil.copy2(ROOT/n, p/n)
    entry = module('entry_'+tag, p/'0.py')
    original = entry.verify

    def verify(path):
        c = original(path)
        c['x8'] = [hx(str(OLD0/'tree')), hx(str(OLD0/'b'))]
        c['x9'] = [[hx(str(OLD0/(bytes.fromhex(q).decode().partition('/p/')[2]))), h] for q, h in c['x9']]
        c['xj'] = PY
        c['xc'] = str(FRAMES)
        return c
    entry.verify = verify
    entry.admit = lambda c: None
    entry.stage = lambda c, root: (FakeCommon, FakeJob, [bytes.fromhex(x).decode() for x in c['xf']])
    entry.MODES = dict(g='s', c='t')
    if refuse:
        os.environ['K5_STUB_REFUSE'] = '1'
    else:
        os.environ.pop('K5_STUB_REFUSE', None)
    return work, p, entry


def call(entry, *argv):
    saved = sys.argv
    sys.argv = ['0.py']+[str(a) for a in argv]
    try:
        return entry.main()
    finally:
        sys.argv = saved


def run(tag, refuse=False):
    os.environ['SLURM_JOB_ID'] = '9990001'
    os.environ['SLURM_JOB_END_TIME'] = str(time.time()+3000)
    work, p, entry = setup(tag, refuse)
    out = dict(work=str(work), codes={})
    started = time.time()
    out['codes']['cpu'] = call(entry, 0, p)
    for g in (0, 1):
        out['codes']['pre%d' % g] = call(entry, 2, p, g)
        os.environ['SLURM_JOB_ID'] = '999001%d' % g
        out['codes']['gpu%d' % g] = call(entry, 1, p, g)
        (p/('12%d.txt' % g)).write_text('999001%d COMPLETED|local|00:00:00\n' % g)
    out['seconds'] = time.time()-started
    out['launches'] = len(FakeCommon.calls)
    FakeCommon.calls.clear()
    return out, p


def main():
    plain, p = run('plain')
    refused, q = run('refuse', refuse=True)
    summary = dict(plain=plain, refuse=refused)
    (ROOT/'DRY_K5.json').write_text(json.dumps(summary, indent=1)+'\n')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
