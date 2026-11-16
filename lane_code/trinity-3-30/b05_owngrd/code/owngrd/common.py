"""Shared helpers: the teacher's pinned name normalization, RLE, hashing and atomic IO."""
from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
# The teacher's normalization (kit_k1a vendor_sam/vendor/phrase.py); tests check this copy against the pinned file.
PHRASE_SHA256 = 'e0f429bfb8fbd013570fea3ede806d051516ad7c6e380561f5061168b756863c'
SINGULAR = {'kitchen cabinets': 'kitchen cabinet', 'cabinets': 'cabinet', 'chairs': 'chair',
            'tables': 'table', 'doors': 'door', 'windows': 'window', 'shelves': 'shelf',
            'bookshelves': 'bookshelf', 'desks': 'desk', 'beds': 'bed', 'sofas': 'sofa',
            'couches': 'couch', 'curtains': 'curtain', 'blinds': 'window blind',
            'books': 'book', 'pillows': 'pillow', 'lamps': 'lamp', 'boxes': 'box',
            'pictures': 'picture', 'towels': 'towel', 'clothes': 'clothing',
            'clothes dryers': 'clothes dryer', 'pipes': 'pipe'}


def normalize_name(label: str) -> str:
    label = ' '.join(str(label).lower().replace('_', ' ').split())
    return SINGULAR.get(label, label)


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def sha256_json(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def atomic_write_bytes(path, data: bytes):
    path = Path(path)
    tmp = path.with_name(path.name + f'.tmp{os.getpid()}')
    with open(tmp, 'wb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def atomic_write_json(path, value, gz=False):
    data = json.dumps(value, sort_keys=True, allow_nan=False).encode()
    atomic_write_bytes(path, gzip.compress(data, 6) if gz else data)


def read_json(path):
    path = str(path)
    opener = gzip.open if path.endswith('.gz') else open
    with opener(path, 'rt') as f:
        return json.load(f)


def rle_encode(mask) -> dict:
    """Column-major uncompressed RLE, size = [h, w] (the K1 tower's format)."""
    a = np.asarray(mask, dtype=np.uint8)
    flat = a.ravel(order='F')
    counts = np.diff(np.r_[0, np.flatnonzero(np.diff(flat)) + 1, flat.size]).tolist()
    if flat.size and flat[0]:
        counts.insert(0, 0)
    return {'size': list(a.shape), 'counts': [int(c) for c in counts]}


def rle_decode(r) -> np.ndarray:
    h, w = r['size']
    counts = r['counts']
    if h <= 0 or w <= 0 or any(int(c) < 0 for c in counts) or sum(counts) != h * w:
        raise ValueError('Invalid RLE')
    return np.repeat(np.arange(len(counts)) % 2, counts).astype(bool).reshape((h, w), order='F')


def room_of(canonical: str, room: str | None = None) -> str:
    """A room is a scan name without its trailing _NN (ScanNet); other datasets carry an explicit room."""
    if room:
        return room
    ds, scene = canonical.split('/', 1)
    if ds == 'scannet' and len(scene) > 3 and scene[-3] == '_':
        return f'{ds}/{scene[:-3]}'
    return canonical
