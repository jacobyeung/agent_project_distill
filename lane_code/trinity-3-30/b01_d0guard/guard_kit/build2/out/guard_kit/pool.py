"""Exclusive, bounded result pool; no checkpoint or input data is stored here."""
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import re
import time
from guard_core import sha
POOL_LIMIT=1024**3
POOL=Path('/project/community/jjyeung/okh7/a936d80c')

@contextmanager
def lock(root):
    root=Path(root)
    if root!=POOL or root.resolve()!=root or not root.is_dir() or (root/'.lock').is_symlink():
        raise ValueError('Result pool identity differs')
    with (root/'.lock').open('a+b') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX)
        yield

def usage(root):
    total=0;count=0;pending=[Path(root)]
    while pending:
        for p in pending.pop().iterdir():
            count+=1
            if count>10000 or p.is_symlink():raise ValueError('Result pool inventory is unsafe or unbounded')
            if p.is_dir():pending.append(p)
            elif p.is_file():total+=p.stat().st_size
            else:raise ValueError('Result pool has a special member')
    return total

def reserve(root,token):
    if not re.fullmatch('[a-f0-9]{16}',token):raise ValueError('Invalid result token')
    with lock(root):
        if usage(root)+16384>POOL_LIMIT:raise ValueError('Result pool quota exceeded')
        target=Path(root)/token;target.mkdir(mode=0o700)
    return target

def publish(root,token,source):
    source=Path(source);size=source.stat().st_size
    with lock(root):
        if usage(root)+size+16384>POOL_LIMIT:raise ValueError('Result pool quota exceeded')
        dest=Path(root)/token/source.name
        started=time.monotonic();copied=0
        with source.open('rb') as inp,dest.open('xb') as out:
            for block in iter(lambda:inp.read(256*1024),b''):
                out.write(block);copied+=len(block)
                time.sleep(max(0,copied/(4*1024**2)-(time.monotonic()-started)))
            out.flush();os.fsync(out.fileno())
        if copied!=size or sha(dest)!=sha(source):raise ValueError('Result pool readback differs')
    return dict(uri=str(dest),bytes=size,sha256=sha(dest),verified=True)
