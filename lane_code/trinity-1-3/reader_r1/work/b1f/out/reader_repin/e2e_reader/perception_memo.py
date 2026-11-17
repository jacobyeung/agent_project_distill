"""Process-local perception values. No files, names, questions, or prefill tensors.

Only the frozen G3T output and SAM image pyramids enter this store. Keys bind
pinned weights, inference configuration, raw pixels, and all frame index lists.
The serial reader owns the store; forked children start with an empty store.
"""
from collections import namedtuple
import hashlib
import os
import struct
import time

import numpy as np
import torch

MODES = ('off', 'on', 'verify')
_sessions = {}
_disabled = False
_pid = os.getpid()


def settings(value, *, required=False):
    """The API defaults to off; production settings must name the switch."""
    mode = value['perception_memo'] if required else value.get('perception_memo', 'off')
    if mode not in MODES:
        raise ValueError('unknown_perception_memo')
    ids = value['perception_memo_verify_ids'] if required else value.get('perception_memo_verify_ids', ())
    if not isinstance(ids, (list, tuple)) or any(type(i) is not str for i in ids):
        raise ValueError('invalid_perception_memo_verify_ids')
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate_perception_memo_verify_ids')
    if ids and mode != 'verify':
        raise ValueError('verify_ids_require_verify_mode')
    return dict(perception_memo=mode, perception_memo_verify_ids=tuple(ids))


def _process():
    global _pid, _sessions, _disabled
    if os.getpid() != _pid:
        _pid, _sessions, _disabled = os.getpid(), {}, False


def process_memo(value):
    _process()
    config = settings(value)
    if config['perception_memo'] == 'off':
        return None
    ident = tuple(config.values())
    if ident not in _sessions:
        _sessions[ident] = Memo(**config)
    return _sessions[ident]


def copy_value(value):
    if isinstance(value, np.ndarray):
        if value.dtype.hasobject:
            raise TypeError('object arrays are not perception values')
        return value.copy(order='K')
    if isinstance(value, torch.Tensor):
        return value.detach().clone(memory_format=torch.preserve_format)
    if isinstance(value, dict):
        return {k: copy_value(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return type(value)(copy_value(v) for v in value)
    if isinstance(value, np.generic):
        return value.copy()
    if value is None or isinstance(value, (str, bytes, bool, int, float)):
        return value
    raise TypeError('unsupported perception value: ' + type(value).__name__)


HostTensor = namedtuple('HostTensor', 'value device')


def store_value(value):
    """Retain tensor payload on the host and remember its exact return device."""
    if isinstance(value, torch.Tensor):
        return HostTensor(value.detach().to(device='cpu', copy=True), value.device)
    if isinstance(value, dict):
        return {k: store_value(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return type(value)(store_value(v) for v in value)
    return copy_value(value)


def restore_value(value):
    if isinstance(value, HostTensor):
        return value.value.to(device=value.device, copy=True)
    if isinstance(value, dict):
        return {k: restore_value(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return type(value)(restore_value(v) for v in value)
    return copy_value(value)


def held_bytes(value):
    if isinstance(value, np.ndarray):
        return value.nbytes
    if isinstance(value, torch.Tensor):
        return value.numel() * value.element_size()
    if isinstance(value, dict):
        return sum(held_bytes(k) + held_bytes(v) for k, v in value.items())
    if isinstance(value, (tuple, list)):
        return sum(held_bytes(v) for v in value)
    if isinstance(value, (str, bytes)):
        return len(value)
    return struct.calcsize('d')


def _tensor_bytes(value):
    # uint8 also handles bfloat16; numpy cannot represent bfloat16 directly.
    return value.detach().contiguous().reshape(-1).view(torch.uint8).cpu().numpy().tobytes()


def equal(a, b):
    """Compare dtype, shape, placement and bytes, including NaNs and signed zeros."""
    if type(a) is not type(b):
        return False
    if isinstance(a, np.ndarray):
        return a.dtype == b.dtype and a.shape == b.shape and a.tobytes() == b.tobytes()
    if isinstance(a, torch.Tensor):
        return (a.dtype == b.dtype and a.shape == b.shape and a.device == b.device
                and a.layout == b.layout and _tensor_bytes(a) == _tensor_bytes(b))
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, (tuple, list)):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    if isinstance(a, np.generic):
        return a.dtype == b.dtype and a.tobytes() == b.tobytes()
    if isinstance(a, float):
        return struct.pack('!d', a) == struct.pack('!d', b)
    return a == b


def _feed(h, value):
    """Length-delimited typed encoding; never pickle or serialize to a file."""
    def raw(data):
        h.update(str(len(data)).encode() + b':' + data)
    raw(type(value).__name__.encode())
    if isinstance(value, np.ndarray):
        _feed(h, (value.dtype.str, value.shape));raw(value.tobytes())
    elif isinstance(value, torch.Tensor):
        _feed(h, (str(value.dtype), tuple(value.shape), str(value.device)));raw(_tensor_bytes(value))
    elif isinstance(value, dict):
        _feed(h, tuple((k, value[k]) for k in sorted(value)))
    elif isinstance(value, (tuple, list)):
        raw(str(len(value)).encode())
        for v in value:
            _feed(h, v)
    elif isinstance(value, bytes):
        raw(value)
    elif isinstance(value, np.generic):
        _feed(h, (value.dtype.str, value.tobytes()))
    elif isinstance(value, float):
        raw(struct.pack('!d', value))
    elif value is None or isinstance(value, (str, int, bool)):
        raw(str(value).encode())
    else:
        raise TypeError('unsupported perception key: ' + type(value).__name__)


def frame_indices(frames):
    return {k: v for k, v in frames.items()
            if k in ('dense_indices', 'anchor_slots', 'anchor_indices')
            or 'indices' in k or 'index' in k or 'slots' in k}


def key(module, identity, images, indices):
    h = hashlib.sha256()
    _feed(h, ('perception-memo-v1', module, identity, indices, len(images)))
    for im in images:
        if getattr(im, 'fp', None) is not None:
            raise ValueError('memo_requires_decoded_memory_frames')
        _feed(h, (im.mode, im.size, im.tobytes()))
        if im.palette is not None:
            _feed(h, im.palette.tobytes())
    return h.hexdigest()


def weight_identity(artifact, component, config):
    # Artifact.verify authenticates these pins before model construction. No IO here.
    files = artifact.manifest['components'][component]['files']
    if not files or any(len(f['sha256']) != hashlib.sha256().digest_size * 2 for f in files):
        raise ValueError('missing_perception_weight_identity')
    return dict(files=tuple(sorted((f['rel'], f['sha256'], f['bytes']) for f in files)), config=config)


class Memo:
    def __init__(self, perception_memo='on', perception_memo_verify_ids=()):
        self.pid = os.getpid()
        self.requested = perception_memo
        self.mode = perception_memo
        self.verify_ids = frozenset(perception_memo_verify_ids)
        self.item_id = None
        self.entries = {}
        self.bytes = 0
        self.events = []
        self.reads = 0
        self.start = 0
        self.hits = self.misses = 0

    def _owner(self):
        _process()
        if self.pid != os.getpid():
            self.__init__(self.requested, tuple(self.verify_ids))

    def begin_read(self):
        self._owner()
        self.reads += 1
        self.start = len(self.events)
        self.mode = ('verify' if self.item_id in self.verify_ids else 'on') if self.requested == 'verify' else self.requested

    def report(self):
        return dict(requested=self.requested, effective='off' if _disabled else self.mode,
                    read=self.reads, held_bytes=self.bytes, hits=self.hits, misses=self.misses,
                    item_id=self.item_id, events=copy_value(self.events[self.start:]))

    def call(self, module, identity, images, indices, fresh):
        global _disabled
        self._owner()
        if _disabled or self.mode == 'off':
            return fresh()
        started = time.perf_counter()
        digest = key(module, identity, images, indices)
        if digest in self.entries:
            self.hits += 1
            stored, size = self.entries[digest]
            result = restore_value(stored)
            hit_s = time.perf_counter() - started
            if self.mode == 'verify':
                t = time.perf_counter()
                recomputed = fresh()
                fresh_s = time.perf_counter() - t
                same = equal(result, recomputed)
                self.events.append(dict(module=module, key_prefix=digest[:16], equal=same,
                                        fresh_seconds=fresh_s, hit_seconds=hit_s))
                if not same:
                    _disabled = True
                    # Disable every policy instance for the rest of this process.
                    for memo in _sessions.values():
                        memo.entries.clear();memo.bytes = 0
                    self.entries.clear();self.bytes = 0
                    return recomputed
            return result
        self.misses += 1
        value = fresh()
        size = held_bytes(value)
        self.entries[digest] = (store_value(value), size)
        self.bytes += size
        return copy_value(value)


def sam_encode(memo, artifact, tower, images, frames):
    from student_pilot.sam3_tower import ClipFeatures
    config = dict(device=str(tower.device), precision=tower.precision,
                  image_batch_size=tower.image_batch_size, native_image_batch=tower.native_image_batch,
                  dense_frames=len(frames['native_frames']), anchor_frames=len(images))
    identity = weight_identity(artifact, 'sam3', config)
    def fresh():
        features = tower.encode(images)
        # The ownership marker is not a model result. Reattach the current tower's
        # marker after copying the pyramids; never copy or memoize the tower itself.
        return dict(frames=features.frames, sizes=features.sizes)
    value = memo.call('sam3', identity, images, frame_indices(frames), fresh)
    return ClipFeatures(value['frames'], value['sizes'], tower._owner)
