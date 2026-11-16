"""Per-clip cache for frozen-tower outputs.

Frozen towers (SAM 3 candidates, G3T lifting, a TowerState) give the same output for the
same clip and export, so a clip pays for them once across its K draws and across every
prompt on the same clip. Two layers:
  * memory: an LRU of live objects (a GroundV3 backend keeps its own per-name candidate
    cache, so reusing the backend object across draws is the cache);
  * disk (optional): picklable values such as a TowerState, keyed by sha256 of the key.
Keys must name everything the value depends on (video sha256, frame indices, export
identity, tower identity); `key_of` builds them.
"""
import pickle
from collections import OrderedDict
from pathlib import Path

from .common import atomic_write_bytes, sha256_obj


def key_of(**parts):
    return sha256_obj(parts)


class ClipCache:
    def __init__(self, max_items=8, disk_dir=None):
        self.max_items = int(max_items)
        self.items = OrderedDict()
        self.disk = Path(disk_dir) if disk_dir else None
        self.hits = self.misses = self.disk_hits = 0

    def get(self, key, build, *, persist=False):
        if key in self.items:
            self.items.move_to_end(key)
            self.hits += 1
            return self.items[key]
        value = None
        path = self.disk / key[:2] / (key + '.pkl') if (self.disk and persist) else None
        if path is not None and path.exists():
            value = pickle.loads(path.read_bytes())
            self.disk_hits += 1
        if value is None:
            self.misses += 1
            value = build()
            if path is not None:
                atomic_write_bytes(path, pickle.dumps(value, protocol=4))
        self.items[key] = value
        while len(self.items) > self.max_items:
            self.items.popitem(last=False)  # drop from memory only
        return value

    def stats(self):
        return dict(hits=self.hits, misses=self.misses, disk_hits=self.disk_hits, live=len(self.items))
