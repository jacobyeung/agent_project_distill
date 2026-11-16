"""Mapped RGB reads and a bounded, identity-invalidated process hash memo."""
from collections import OrderedDict
import hashlib
import json
import os
from pathlib import Path
from threading import RLock


class NeedsFrameHost(FileNotFoundError):
    """The manifest is usable, but this host lacks its mapped RGB bytes."""


def resolve_frame(path):
    raw = Path(path)
    if not raw.is_absolute() or '..' in raw.parts:
        raise ValueError('Frame path must be absolute without traversal')
    mapping = json.loads(os.environ.get('STUDENT_FRAME_ROOT_MAP', '{}'))
    if not isinstance(mapping, dict):
        raise ValueError('STUDENT_FRAME_ROOT_MAP must be a JSON object')
    for old in sorted(mapping, key=len, reverse=True):
        source, destination = Path(old), Path(mapping[old])
        if not source.is_absolute() or not destination.is_absolute() or '..' in destination.parts:
            raise ValueError('Invalid frame root map')
        if raw.is_relative_to(source):
            target = destination / raw.relative_to(source)
            if not target.resolve().is_relative_to(destination.resolve()):
                raise ValueError('Frame symlink escapes mapped root')
            raw = target
            break
    resolved = raw.resolve()
    if resolved.parts[1] == 'home' or resolved.parts[1].startswith('data'):
        raise NeedsFrameHost('needs the frame host: unmapped logical frame root ' + str(raw))
    if not raw.is_file():
        raise NeedsFrameHost('needs the frame host: missing mapped RGB ' + str(raw))
    return raw


class FrameMemo:
    def __init__(self, capacity=8192):
        if capacity < 1:
            raise ValueError('Frame memo capacity must be positive')
        self.capacity, self.values, self.hashes, self.requests = capacity, OrderedDict(), 0, 0
        self.lock = RLock()

    @staticmethod
    def identity(stat):
        return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns

    def verify(self, pin):
        path = resolve_frame(pin['path'])
        with self.lock:
            self.requests += 1
            with path.open('rb') as handle:
                identity = self.identity(os.fstat(handle.fileno()))
                value = self.values.get(identity)
                if value is None:
                    hasher = hashlib.sha256()
                    for block in iter(lambda: handle.read(1 << 20), b''):
                        hasher.update(block)
                    value = hasher.hexdigest()
                    self.hashes += 1
                if identity != self.identity(os.fstat(handle.fileno())) or identity != self.identity(path.stat()):
                    raise ValueError('Frame changed while hashing')
            if value != pin['sha256']:
                raise ValueError('Stale frame pin: ' + pin['path'])
            self.values[identity] = value
            self.values.move_to_end(identity)
            while len(self.values) > self.capacity:
                self.values.popitem(last=False)
            return path

    def stats(self):
        return dict(requests=self.requests, hashes=self.hashes, cached=len(self.values), capacity=self.capacity)


MEMO = FrameMemo()


def verify_frame(pin):
    return MEMO.verify(pin)
