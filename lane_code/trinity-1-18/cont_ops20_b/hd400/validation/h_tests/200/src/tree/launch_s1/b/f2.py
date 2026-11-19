"""Verify every pinned readout RGB frame before opening a model."""
import hashlib
import json
from pathlib import Path
import re
import sys


def verify(manifest, data2root, expected_sha, prefix='k3f8'):
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


if __name__ == '__main__':
    print(verify(*sys.argv[1:]))
