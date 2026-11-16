"""Verify the complete preparer package against its externally pinned contract."""
import hashlib
import json
import os
from pathlib import Path


def verify_package():
    root = Path(__file__).resolve().parent
    contract = root / 'PREP_CONTRACT.json'
    actual = hashlib.sha256(contract.read_bytes()).hexdigest()
    if os.environ.get('PREP_CONTRACT_SHA256') != actual:
        raise ValueError('PREP_CONTRACT_SHA256 must pin this immutable preparer contract')
    spec = json.loads(contract.read_text())
    paths = [p for p in root.rglob('*') if p.is_file()]
    if any(p.is_symlink() for p in root.rglob('*')):
        raise ValueError('preparer package must be a full regular-file copy')
    census = {str(p.relative_to(root)) for p in paths if p != contract}
    if census != set(spec['files']):
        raise ValueError('preparer package file census drift')
    for name, expected in spec['files'].items():
        path = root / name
        if path.stat().st_size != expected['size_bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != expected['sha256']:
            raise ValueError(f'preparer file drift: {name}')
    return {'path': str(contract), 'sha256': actual, 'size_bytes': contract.stat().st_size}


if __name__ == '__main__':
    print(json.dumps(verify_package(), sort_keys=True))
