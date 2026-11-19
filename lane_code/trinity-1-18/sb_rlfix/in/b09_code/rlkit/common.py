"""Hashing, canonical JSON, atomic file writes and derived seeds."""
import hashlib
import json
import os
import tempfile
from pathlib import Path


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_obj(obj):
    return sha256_bytes(canonical(obj).encode())


def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(chunk)
            if not b:
                return h.hexdigest()
            h.update(b)


def atomic_write_bytes(path, data):
    """Write a temp file, fsync, rename: readers see the old file or the whole new one.

    An interrupted write leaves a `.*.part` file; every reader and resume ignore it.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.' + path.name + '.', suffix='.part', dir=path.parent)
    with os.fdopen(fd, 'wb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    dfd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


def atomic_write_json(path, obj):
    atomic_write_bytes(path, (json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=False) + '\n').encode())


def derive_seed(run_seed, prompt_id, draw):
    """Seed of one draw: a function of the run seed, the prompt id and the draw index only.

    Resume, sharding and worker count cannot change a draw's random stream.
    """
    digest = hashlib.sha256(f'rlkit-seed-v1|{int(run_seed)}|{prompt_id}|{int(draw)}'.encode()).digest()
    return int.from_bytes(digest[:8], 'big') & ((1 << 63) - 1)


def read_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl_atomic(path, rows):
    atomic_write_bytes(path, ''.join(canonical(r) + '\n' for r in rows).encode())
