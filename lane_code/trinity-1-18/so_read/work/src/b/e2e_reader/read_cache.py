"""Bounded, generator-owned caches for immutable evaluation inputs.

No language-model state, prompt tokens, geometry, scale, or tool response is cached.
All switches default to off. An entry owns its storage; every hit returns a copy.
"""
from collections import OrderedDict
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
import hashlib
import os
import struct
import time

import numpy as np
import torch


SWITCHES = ('read_processor_cache', 'read_vision_cache', 'read_sam_cache')


def switches(settings):
    result = {k: settings.get(k, 'off') for k in SWITCHES}
    if any(v not in ('off', 'on') for v in result.values()):
        raise ValueError('read cache switches must be off or on')
    return result


def digest(value):
    h = hashlib.sha256()
    def feed(v):
        def raw(b):
            h.update(str(len(b)).encode() + b':' + b)
        raw((type(v).__module__ + '.' + type(v).__qualname__).encode())
        if isinstance(v, torch.Tensor):
            if v.layout != torch.strided:
                raise TypeError('read cache requires strided tensors')
            feed((str(v.dtype), str(v.device), tuple(v.shape), tuple(v.stride())))
            raw(v.detach().contiguous().reshape(-1).view(torch.uint8).cpu().numpy().tobytes())
        elif isinstance(v, np.ndarray):
            if v.dtype.hasobject: raise TypeError('object array in read cache key')
            feed((v.dtype.str, v.shape, v.strides));raw(v.tobytes())
        elif is_dataclass(v) and not isinstance(v, type):
            feed({f.name:getattr(v, f.name) for f in fields(v)})
        elif isinstance(v, Mapping):
            for k in sorted(v): feed(k);feed(v[k])
        elif isinstance(v, (list, tuple)):
            raw(str(len(v)).encode())
            for x in v: feed(x)
        elif isinstance(v, np.generic):
            feed((v.dtype.str, v.tobytes()))
        elif isinstance(v, bytes): raw(v)
        elif isinstance(v, float): raw(struct.pack('!d', v))
        elif v is None or type(v) in (bool, int, str): raw(str(v).encode())
        else: raise TypeError('unsupported read cache key: ' + type(v).__name__)
    feed(value)
    return h.hexdigest()


def snapshot(value):
    """Store tensors on CPU, with dtype/device and container type preserved."""
    if isinstance(value, torch.Tensor):
        return ('tensor', value.detach().to(device='cpu', copy=True), value.device)
    if isinstance(value, np.ndarray):
        if value.dtype.hasobject: raise TypeError('object array in read cache value')
        return ('array', value.copy(order='K'))
    if is_dataclass(value) and not isinstance(value, type):
        return ('dataclass', type(value), {f.name:snapshot(getattr(value,f.name)) for f in fields(value)})
    if isinstance(value, Mapping):
        return ('mapping', type(value), [(k,snapshot(v)) for k,v in value.items()])
    if isinstance(value, (list, tuple)):
        return ('sequence', type(value), [snapshot(v) for v in value])
    if value is None or isinstance(value, (str, bytes, bool, int, float, np.generic)):
        return ('scalar', value)
    raise TypeError('unsupported read cache value: ' + type(value).__name__)


def restore(value):
    kind = value[0]
    if kind == 'tensor': return value[1].to(device=value[2], copy=True)
    if kind == 'array': return value[1].copy(order='K')
    if kind == 'dataclass': return value[1](**{k:restore(v) for k,v in value[2].items()})
    if kind == 'mapping': return value[1]({k:restore(v) for k,v in value[2]})
    if kind == 'sequence': return value[1](restore(v) for v in value[2])
    return value[1]


def nbytes(value):
    if isinstance(value, torch.Tensor): return value.numel()*value.element_size()
    if isinstance(value, np.ndarray): return value.nbytes
    if is_dataclass(value) and not isinstance(value, type):
        return sum(nbytes(getattr(value, f.name)) for f in fields(value))
    if isinstance(value, Mapping): return sum(nbytes(k)+nbytes(v) for k,v in value.items())
    if isinstance(value, (tuple, list)): return sum(map(nbytes,value))
    if isinstance(value, (str, bytes)): return len(value)
    return 64


class ReadCache:
    def __init__(self, max_bytes):
        if type(max_bytes) is not int or not 0 < max_bytes <= 16*1024**3:
            raise ValueError('read_cache_bytes must be an integer in (0,16 GiB]')
        self.max_bytes = max_bytes
        self.entries = OrderedDict()
        self.held_bytes = 0
        self.pid = os.getpid()
        self.stats = {}

    def call(self, namespace, key, fresh):
        if self.pid != os.getpid():
            self.__init__(self.max_bytes)
        info = self.stats.setdefault(namespace, dict(hits=0, misses=0, evictions=0,
                                                     oversized=0, fresh_s=0., hit_s=0.))
        start = time.perf_counter()
        k = (namespace, key)
        if k in self.entries:
            info['hits'] += 1
            value, size = self.entries.pop(k);self.entries[k] = (value,size)
            out = restore(value)
            info['hit_s'] += time.perf_counter()-start
            return out
        info['misses'] += 1
        value = fresh()
        info['fresh_s'] += time.perf_counter()-start
        if nbytes(value) > self.max_bytes:
            info['oversized'] += 1
            return value
        saved = snapshot(value);size = nbytes(saved)
        if size > self.max_bytes:
            info['oversized'] += 1
            return value
        while self.entries and self.held_bytes+size > self.max_bytes:
            _, (_, old_size) = self.entries.popitem(last=False)
            self.held_bytes -= old_size;info['evictions'] += 1
        self.entries[k] = (saved, size);self.held_bytes += size
        return value


class VideoProcessorCache:
    """Forward all attributes; memoize only the processor's video call."""
    def __init__(self, target, cache):
        self.target, self.cache = target, cache

    def __getattr__(self, name):
        return getattr(self.target, name)

    def __call__(self, *args, **kwargs):
        config = self.target.to_dict()
        key = digest((config, args, kwargs))
        return self.cache.call('processor', key, lambda:self.target(*args, **kwargs))


def install_vision_cache(model, cache):
    """Cache only the frozen visual module, retaining every language forward."""
    visual = model.model.visual
    if getattr(visual, '_read_cache_installed', False):
        raise ValueError('vision cache already installed')
    if visual.__class__.__name__ != 'Qwen3_5VisionModel':
        raise ValueError('vision cache requires the audited Qwen3_5VisionModel')
    original = visual.forward
    def forward(*args, **kwargs):
        if torch.is_grad_enabled() or any(m.training for m in visual.modules()):
            raise ValueError('vision cache requires no-grad evaluation')
        # Child hooks can inject geometry or collect intermediate states. They must run.
        from torch.nn.modules import module as module_runtime
        children = tuple(visual.modules())[1:]
        if (any(m._forward_hooks or m._forward_pre_hooks for m in children)
                or module_runtime._global_forward_hooks or module_runtime._global_forward_pre_hooks):
            info = cache.stats.setdefault('vision_bypass', {'calls':0})
            info['calls'] += 1
            return original(*args, **kwargs)
        # Cache lifetime is one immutable model. Versions invalidate normal in-place updates.
        versions = tuple((n, t._version, str(t.dtype), str(t.device))
                         for n,t in (*visual.named_parameters(), *visual.named_buffers()))
        key = digest((visual.config.to_dict(), versions, args, kwargs,
                      torch.is_autocast_enabled('cuda'), str(torch.get_autocast_dtype('cuda')),
                      torch.is_autocast_enabled('cpu'), str(torch.get_autocast_dtype('cpu'))))
        return cache.call('vision', key, lambda:original(*args, **kwargs))
    visual.forward = forward
    visual._read_cache_installed = True
