"""Bounded in-memory RGB cache after the original per-read frame verification."""
from collections import OrderedDict
import os
from threading import RLock

import numpy as np
from PIL import Image


class DecodedRGB:
    def __init__(self, capacity_bytes):
        self.capacity = capacity_bytes
        self.values = OrderedDict()
        self.bytes = self.hits = self.misses = 0
        self.lock = RLock()

    @staticmethod
    def identity(path):
        stat = path.stat()
        return (str(path), stat.st_dev, stat.st_ino, stat.st_size,
                stat.st_mtime_ns, stat.st_ctime_ns)

    def get(self, path, logical_path):
        # Callers must verify the pin on EVERY access, including hits. An eviction
        # never changes admission, row selection, augmentation or preprocessing.
        with self.lock:
            identity = self.identity(path)
            cached = self.values.get(identity)
            if cached is not None:
                self.hits += 1
                self.values.move_to_end(identity)
                return cached.copy()
            self.misses += 1
            with Image.open(path) as image:
                if image.mode != 'RGB':
                    raise ValueError(f'Source is not RGB: {logical_path}')
                value = np.asarray(image).copy()
            if self.identity(path) != identity:
                raise ValueError('Frame changed while decoding')
            if value.nbytes <= self.capacity:
                while self.bytes + value.nbytes > self.capacity and self.values:
                    _, old = self.values.popitem(last=False)
                    self.bytes -= old.nbytes
                self.values[identity] = value
                self.bytes += value.nbytes
            return value.copy()


_cache = None
_lock = RLock()


def read(path, logical_path):
    global _cache
    from .c1_switches import get
    mib = int(get('C1_DECODED_CACHE_MIB'))
    if not 1 <= mib <= 4096:
        raise ValueError('C1_DECODED_CACHE_MIB must be 0 (OFF) or 1..4096')
    with _lock:
        if _cache is None or _cache.capacity != mib * (1 << 20):
            _cache = DecodedRGB(mib * (1 << 20))
        cache = _cache
    return cache.get(path, logical_path)


def stats():
    """Cumulative counters; step differences give hits/misses during that update."""
    with _lock:
        if _cache is None:
            return dict(hits=0, misses=0, bytes=0, capacity_bytes=0)
        with _cache.lock:
            return dict(hits=_cache.hits, misses=_cache.misses, bytes=_cache.bytes,
                        capacity_bytes=_cache.capacity)
