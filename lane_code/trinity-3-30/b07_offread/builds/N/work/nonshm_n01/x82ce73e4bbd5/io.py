"""Bounded writes, canonical identities, safe archives, and append-only journals."""
import hashlib
import io
import json
from pathlib import Path
import tarfile
from .paths import ROOT

def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()

def owned(path):
    p = Path(path).resolve()
    if not (p.is_relative_to(ROOT) or p.is_relative_to(Path('/dev/shm/b07_n6'))):
        raise ValueError('write outside build N')
    return p

def dump(path, value):
    p = owned(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')

def load(path):
    return json.loads(Path(path).read_text())

def journal(path, row):
    p = owned(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('a') as f:
        f.write(json.dumps(row, sort_keys=True, allow_nan=False) + '\n')
        f.flush()

def rows(path):
    with Path(path).open() as f:
        return [json.loads(s) for s in f if s.strip()]

def extract(source, destination, max_bytes=90_000_000):
    destination = owned(destination)
    with tarfile.open(source) as archive:
        members = archive.getmembers()
        names = [m.name for m in members]
        if len(set(names)) != len(names):
            raise ValueError('duplicate archive path')
        for m in members:
            p = Path(m.name)
            if p.is_absolute() or '..' in p.parts or not m.isfile():
                raise ValueError('unsafe archive member; links are forbidden')
        if sum(m.size for m in members) > max_bytes:
            raise ValueError('return exceeds byte budget')
        for m in members:
            p = owned(destination / m.name)
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open('xb') as f:
                f.write(archive.extractfile(m).read())

def tar_bytes(files):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w') as archive:
        for name, data in sorted(files.items()):
            if Path(name).is_absolute() or '..' in Path(name).parts:
                raise ValueError('unsafe packet path')
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o600
            info.mtime = 0
            archive.addfile(info, io.BytesIO(data))
    return buf.getvalue()
