"""Publish complete checkpoints before advancing past a checkpoint boundary."""
import json
import os
import shutil
import time
from pathlib import Path
from uuid import uuid4

from .common import sha256
from .orchard_paths import PROJECT


def publish(source):
    source = Path(source)
    root = Path(os.environ['ORCHARD_CHECKPOINT_ROOT']).resolve()
    if not root.is_relative_to(PROJECT / 'runs'):
        raise ValueError('Orchard checkpoints must publish below project runs')
    root.mkdir(parents=True, exist_ok=True)
    destination = root / source.name
    manifest = json.loads((source / 'checkpoint.json').read_text())
    if destination.exists():
        if sha256(destination / 'checkpoint.json') != sha256(source / 'checkpoint.json'):
            raise ValueError('Checkpoint step already has different durable bytes')
        return destination
    temporary = root / ('.' + source.name + '.' + uuid4().hex + '.partial')
    temporary.mkdir()
    started = time.monotonic()
    for name, pin in manifest['files'].items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Invalid checkpoint file path')
        target = temporary / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / relative, target)
        if target.stat().st_size != pin['bytes'] or sha256(target) != pin['sha256']:
            raise ValueError('Durable checkpoint copy failed verification')
        with target.open('rb') as stream:
            os.fsync(stream.fileno())
    shutil.copyfile(source / 'checkpoint.json', temporary / 'checkpoint.json')
    with (temporary / 'checkpoint.json').open('rb') as stream:
        os.fsync(stream.fileno())
    temporary.rename(destination)
    fd = os.open(root, os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    with (root / 'publication_metrics.jsonl').open('a') as stream:
        stream.write(json.dumps({'step': manifest['step'], 'copy_seconds': time.monotonic() - started}) + '\n')
    return destination
