"""Compile the shipped bootstrap with the actual system interpreter."""
import hashlib
import json
from pathlib import Path
import sys


def probe(root):
    if list(sys.version_info[:2]) != [3, 6]:
        raise ValueError('System interpreter is not the required version')
    files = {}
    for path in sorted((Path(root)/'b').glob('*.py')):
        raw = path.read_bytes()
        compile(raw, str(path), 'exec')
        files[path.name] = hashlib.sha256(raw).hexdigest()
    if not files:
        raise ValueError('Missing bootstrap scripts')
    return dict(stdlib_version=list(sys.version_info[:2]), files=files)


if __name__ == '__main__':
    print(json.dumps(probe(sys.argv[1]), sort_keys=True))
