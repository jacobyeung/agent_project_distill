"""Verify immutable inputs and retained completion records."""
import hashlib
import json
import os
import re
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    path = Path(path)
    raw = (json.dumps(value, indent=1, sort_keys=True) + '\n').encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError('Existing output differs: ' + str(path))
        return
    with path.open('xb') as stream:
        stream.write(raw)


def pin(path):
    return {'path': str(path), 'sha256': sha(path)}


def checked(value):
    if not isinstance(value, dict) or set(value) != {'path', 'sha256'}:
        raise ValueError('Missing binding')
    if not Path(value['path']).is_absolute() or not re.fullmatch('[0-9a-f]{64}', value['sha256'] or ''):
        raise ValueError('Invalid binding')
    if sha(value['path']) != value['sha256']:
        raise ValueError('Binding differs: ' + value['path'])
    return Path(value['path'])


def tree(record_pin, directory, expected):
    record = json.loads(checked(record_pin).read_bytes())
    if not re.fullmatch('(?:[0-9a-f]{40}|sha256:[0-9a-f]{64})', expected or ''):
        raise ValueError('Revision is not sealed')
    if record.get('schema') != 'rung1-neutral-runtime-v1':
        raise ValueError('Runtime schema differs')
    spec = record['trees']['trainer']
    if spec['commit'] != expected:
        raise ValueError('Revision differs')
    root = Path(directory)
    files = {}
    for base, dirs, names in os.walk(root):
        dirs.sort()
        if any((Path(base) / name).is_symlink() for name in dirs + names):
            raise ValueError('Source links are not admitted')
        for name in names:
            path = Path(base) / name
            files[str(path.relative_to(root))] = sha(path)
    if files != spec['files'] or spec['file_count'] != len(files):
        raise ValueError('Source differs from sealed tree')
    if expected.startswith('sha256:') and hashlib.sha256(
            json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest() != expected[7:]:
        raise ValueError('Source tree digest differs')
    return record


def completed(marker, inputs):
    marker = Path(marker)
    if not marker.exists():
        return False
    saved = json.loads(marker.read_bytes())
    if saved['inputs'] != inputs:
        raise ValueError('Completion belongs to different inputs')
    for value in saved['outputs']:
        checked(value)
    return True


def finish(marker, inputs, outputs):
    write(marker, {'inputs': inputs, 'outputs': [pin(p) for p in outputs]})


def student_name():
    from student_pilot import students
    if hasattr(students, 'runtime_student'):
        return students.runtime_student()
    names = [name for name, spec in students.STUDENTS.items()
             if spec['snapshot'].name == 'c202236235762e1c871ad0ccb60c8ee5ba337b9a']
    if len(names) != 1:
        raise ValueError('Registered runtime identity is ambiguous')
    return names[0]
