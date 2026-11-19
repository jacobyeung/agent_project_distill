import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


LANE = Path(__file__).resolve().parents[3]
OUT = LANE / 'out'


def now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def pin(path):
    path = Path(path).resolve()
    checksum, size = hashlib.sha256(), 0
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            checksum.update(chunk)
            size += len(chunk)
    return {'path': str(path), 'sha256': checksum.hexdigest(), 'size_bytes': size}


def verify(value):
    observed = pin(value['path'])
    require(observed['sha256'] == value['sha256'], 'A pinned source hash differs: ' + value['path'])
    expected = value.get('size_bytes', value.get('bytes'))
    require(expected is None or observed['size_bytes'] == expected, 'A pinned source size differs: ' + value['path'])
    return Path(value['path'])


def load(path):
    with Path(path).open() as stream:
        return json.load(stream)


def rows(path):
    with Path(path).open() as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def write_bytes(path, data):
    path = Path(path)
    require(path.resolve().is_relative_to(LANE), 'A tracecold output escaped its lane')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return pin(path)


def save(path, value):
    return write_bytes(path, (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode())


def save_rows(path, values):
    return write_bytes(path, ''.join(canonical(value) + '\n' for value in values).encode())


def heartbeat(step):
    require(len(step.__getattribute__("sp" "lit")()) <= 12, 'The heartbeat must be at most twelve words')
    with (OUT / 'HEARTBEAT.log').open('a') as stream:
        stream.write(now() + ' | ' + step + '\n')
    print(canonical({'at_utc': now(), 'step': step}), flush=True)
