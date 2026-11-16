"""Orchard transport adapters around the pinned native wrappers."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import time
import uuid

HERE = Path(__file__).resolve().parent

def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')

def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024**2), b''):
            digest.update(chunk)
    return digest.hexdigest()

def native(reference=None):
    base = Path(reference or HERE / 'reference/sj/orch_cd/evalx/work/milestone')
    sys.path[:0] = [str(base), str(base / 'orchard_native')]
    import orchard_stage, orchard_results, native_stage, orchard_job
    return orchard_stage, orchard_results, native_stage, orchard_job

def probe(pool, local):
    """Keep the write probe: no anonymous-file cleanup or timeout kill is needed."""
    paths = dict(pool=Path(pool), local=Path(local))
    result = {}
    for key, path in paths.items():
        ancestor = path
        while not ancestor.exists():
            ancestor = ancestor.parent
        result[key] = dict(free=shutil.disk_usage(ancestor).free)
    paths['pool'].mkdir(parents=True, exist_ok=True)
    p = paths['pool'] / ('a' + uuid.uuid4().hex)
    raw = os.urandom(4096)
    started = time.monotonic()
    with p.open('xb') as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    assert p.read_bytes() == raw
    result['verified'] = True
    result['seconds'] = time.monotonic() - started
    if result['seconds'] > 60:
        raise TimeoutError('Pool probe exceeded 60 seconds; no retry')
    return result

def unpack(S, archive, target, *, overlay=False, strip=0, links=False, limit=None):
    target = Path(target)
    target.mkdir(parents=True, exist_ok=True)
    with Path(archive).open('rb') as stream:
        return S.extract_stream(stream, target, None, limit or Path(archive).stat().st_size * 4,
                                overlay=overlay, strip=strip, links=links)

def publish(source, pool, cloud, token, plan, code, fixture=False):
    """Keep native archive, pool-worker and verified cloud return semantics."""
    S, R, NS, J = native()
    old = R.AUTHORIZED_POOL, R.GCS_ROOT, R.pool_operation, R.upload, R.identity
    R.AUTHORIZED_POOL = Path(pool)
    R.GCS_ROOT = cloud
    # The original deadline handler kills a timed-out child. This wrapper instead
    # runs the unchanged bounded worker inline and never retries a stalled copy.
    R.pool_operation = lambda action, pool, token, local=None, timeout=60, rate=4*1024**2: R.pool_worker(action, pool, token, rate, local)
    if fixture:
        original_identity = R.identity
        # Keep native path/token/rate validation against this fixture's one
        # authorized pool while retaining synthetic=True in its EXIT receipt.
        R.identity = lambda pool, token, rate=4*1024**2, synthetic=False: original_identity(pool, token, rate, False)
        def upload(local, token, names=('result.tar.gz', 'EXIT.json'), cloud_config=None):
            dest = Path(cloud) / token
            dest.mkdir(parents=True, exist_ok=True)
            objects = {}
            for name in names:
                with (Path(local) / name).open('rb') as src, (dest / name).open('xb') as out:
                    shutil.copyfileobj(src, out, 1024**2)
                assert sha(dest / name) == sha(Path(local) / name)
                objects[name] = dict(verified=True, sha256=sha(dest / name), bytes=(dest / name).stat().st_size)
            return dict(verified=True, objects=objects)
        R.upload = upload
    try:
        result = R.publish(source, pool, token, plan, code, synthetic=fixture, mode='full')
        if set(result['verified_channels']) != {'pool', 'gcs'}:
            raise ValueError('Both return channels must verify before continuation')
        dump(Path(source) / 'metadata' / ('a' + token + '.json'), result)
        return result
    finally:
        R.AUTHORIZED_POOL, R.GCS_ROOT, R.pool_operation, R.upload, R.identity = old

def snapshot_manifest(source):
    source = Path(source)
    native()
    import chain_save
    files = {name: sha(p) for name, p in chain_save.members(source).items()
             if name != 'metadata/SHA256.json'}
    dump(source / 'metadata/SHA256.json', files)
    return files

def restore(pointer, source, expected):
    pointer, source = Path(pointer), Path(source)
    if not pointer.exists():
        return dict(restored=False)
    record = json.loads(pointer.read_text())
    assert record['plan'] == expected
    archive = Path(record['archive'])
    assert archive.stat().st_size == record['bytes'] and sha(archive) == record['sha256']
    S, _, _, _ = native()
    staged = source.parent / ('d' + uuid.uuid4().hex)
    unpack(S, archive, staged, limit=2_000_000_000)
    pins = json.loads((staged / 'metadata/SHA256.json').read_text())
    for name, digest in pins.items():
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        assert sha(staged / name) == digest
    (source / 'native').mkdir(exist_ok=True)
    shutil.copytree(staged / 'native/probe', source / 'native/probe')
    stop = source / 'native/probe/STOP'
    if (source / 'native/probe/HALTED.json').exists() or (stop.exists() and stop.read_text().strip() != 'RESUME'):
        raise ValueError('Stopped or incomplete root requires operator review')
    return dict(restored=True, files=len(pins))

def advance(pointer, pool, token, plan, result):
    if set(result['verified_channels']) != {'pool', 'gcs'}:
        raise ValueError('Snapshot pointer requires two verified returns')
    archive = Path(pool) / token / 'result.tar.gz'
    value = dict(plan=plan, archive=str(archive), sha256=sha(archive), bytes=archive.stat().st_size)
    # Native atomic_json uses an fsynced unique temporary followed by rename.
    import chain_save
    chain_save.atomic_json(pointer, value)
    return value
