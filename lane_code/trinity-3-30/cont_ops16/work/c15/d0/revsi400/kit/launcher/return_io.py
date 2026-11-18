"""Bounded pool operations; the .wtest evidence is retained."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

POOL_LIMIT = 100_000_000
RESERVE = 100_000


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()


def usage(pool):
    total = 0
    for p in pool.rglob('*'):
        if p.is_symlink(): raise ValueError('Symlink in return pool')
        if p.is_file(): total += p.stat().st_size
    return total


def operate(action, pool, token, local=None):
    pool = Path(pool)
    if not pool.is_absolute() or pool.is_symlink(): raise ValueError('Invalid pool')
    pool.mkdir(parents=True, exist_ok=True)
    with os.fdopen(os.open(pool/'POOL.lock', os.O_RDWR | os.O_CREAT, 0o600), 'rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        dest = pool/token
        if action == 'test':
            if usage(pool) + 4*1024**2 + RESERVE >= POOL_LIMIT: raise ValueError('Pool exceeds 100 MB')
            dest.mkdir(mode=0o700)
            data = os.urandom(4*1024**2)
            test = dest/'.wtest'
            started = time.monotonic()
            with test.open('xb') as f:
                if f.write(data) != len(data): raise OSError('Short write test')
                f.flush(); os.fsync(f.fileno())
            digest = sha(test)
            if digest != hashlib.sha256(data).hexdigest(): raise ValueError('Write test SHA256 differs')
            # Retain the bounded write-test evidence.
            return dict(bytes=len(data), sha256=digest, seconds=time.monotonic()-started)
        if not dest.is_dir() or dest.is_symlink(): raise ValueError('Missing tested pool token')
        local = Path(local)
        names = ['result.tar.gz', 'EXIT.json', 'JOB.log'] if action == 'publish' else (['TRACE.json.gz','TRACE.pin.json'] if action=='trace' else ['RETURN_RECEIPT.json','JOB.log'])
        incoming = sum((local/n).stat().st_size for n in names)
        if action=='trace' and usage(dest)+incoming+RESERVE>=20_000_000:raise ValueError('Proof return exceeds 20 MB')
        if usage(pool) + incoming + RESERVE >= POOL_LIMIT: raise ValueError('Pool exceeds 100 MB')
        for name in names:
            src = local/name; partial = dest/(name+'.partial')
            with src.open('rb') as inp, partial.open('xb') as out:
                shutil.copyfileobj(inp, out, 256*1024); out.flush(); os.fsync(out.fileno())
            if sha(partial) != sha(src): raise ValueError('Pool copy SHA256 differs')
            os.replace(partial, dest/name)
        return dict(verified=True, files={n:dict(bytes=(dest/n).stat().st_size,sha256=sha(dest/n)) for n in names})


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['test','publish','receipt','trace'])
    p.add_argument('pool');p.add_argument('token');p.add_argument('--local');a=p.parse_args()
    print(json.dumps(operate(a.action,a.pool,a.token,a.local),sort_keys=True))
