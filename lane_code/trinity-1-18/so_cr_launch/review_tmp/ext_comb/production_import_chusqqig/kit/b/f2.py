"""Verify every pinned readout RGB frame before opening a model."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys


def verify(manifest, data2root, expected_sha, prefix='k3f8'):
    if os.environ.get('TK_PARALLEL_FRAME_SHA', '0') == '1':
        return verify_parallel(manifest, data2root, expected_sha, prefix)
    raw = Path(manifest).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError('Frame manifest differs')
    frames = json.loads(raw)
    if not isinstance(frames, list) or not frames:
        raise ValueError('Empty frame manifest')
    root, seen = Path(data2root).resolve(), set()
    for frame in frames:
        digest = frame['sha256']
        if not re.fullmatch('[0-9a-f]{64}', digest):
            raise ValueError('Invalid frame digest')
        relative = prefix + '/' + digest[:2] + '/' + digest + '.png'
        if frame['path'] != '/data2/' + relative or digest in seen:
            raise ValueError('Invalid frame identity')
        seen.add(digest)
        path = root / relative
        if not path.resolve().is_relative_to(root) or path.is_symlink():
            raise ValueError('Frame leaves local store')
        h = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1 << 20), b''):
                h.update(block)
        if h.hexdigest() != digest:
            raise ValueError('Frame differs: ' + frame['path'])
    return len(seen)


def verify_parallel(manifest, data2root, expected_sha, prefix='k3f8'):
    """Bound work in flight; every frame still receives a complete SHA256 check."""
    from concurrent.futures import ThreadPoolExecutor
    workers = int(os.environ.get('TK_FRAME_SHA_WORKERS', '4'))
    if not 1 <= workers <= 8:
        raise ValueError('Frame SHA workers must be between 1 and 8')
    raw = Path(manifest).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError('Frame manifest differs')
    frames = json.loads(raw)
    if not isinstance(frames, list) or not frames:
        raise ValueError('Empty frame manifest')
    root, seen = Path(data2root).resolve(), set()

    def check(item):
        path, expected, logical = item
        h = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1 << 20), b''):
                h.update(block)
        if h.hexdigest() != expected:
            raise ValueError('Frame differs: ' + logical)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        pending = []
        for frame in frames:
            expected = frame['sha256']
            if not re.fullmatch('[0-9a-f]{64}', expected):
                raise ValueError('Invalid frame digest')
            relative = prefix + '/' + expected[:2] + '/' + expected + '.png'
            if frame['path'] != '/data2/' + relative or expected in seen:
                raise ValueError('Invalid frame identity')
            seen.add(expected)
            path = root / relative
            if not path.resolve().is_relative_to(root) or path.is_symlink():
                raise ValueError('Frame leaves local store')
            pending.append(pool.submit(check, (path, expected, frame['path'])))
            if len(pending) == 2 * workers:
                for future in pending:
                    future.result()
                pending.clear()
        for future in pending:
            future.result()
    return len(seen)


if __name__ == '__main__':
    print(verify(*sys.argv[1:]))
