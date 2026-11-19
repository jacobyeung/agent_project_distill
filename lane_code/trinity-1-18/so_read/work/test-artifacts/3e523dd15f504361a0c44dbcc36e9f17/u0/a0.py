"""Bounded, generator-owned caches for immutable evaluation inputs.

No language-model state, prompt tokens, geometry, scale, or tool response is cached.
All switches default to off. An entry owns its storage; every hit returns a copy.
"""
from collections import OrderedDict
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
import os
import struct
import sys
import time
import threading

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
            h.update(str(len(b)).encode() + b':'); h.update(b)
        raw((type(v).__module__ + '.' + type(v).__qualname__).encode())
        if isinstance(v, Enum):
            feed(v.value)
        elif isinstance(v, torch.Tensor):
            if type(v) not in (torch.Tensor,torch.nn.Parameter):raise TypeError('tensor subclass in cache key')
            if v.layout != torch.strided:
                raise TypeError('read cache requires strided tensors')
            feed((str(v.dtype), str(v.device), tuple(v.shape), tuple(v.stride())))
            h.update(str(v.numel()*v.element_size()).encode()+b':')
            def chunks(t):
                if t.is_contiguous():
                    flat=t.detach().reshape(-1).view(torch.uint8)
                    for offset in range(0,flat.numel(),65536):
                        part=flat[offset:offset+65536].cpu().numpy()
                        h.update(memoryview(part))
                else:
                    for row in t:chunks(row)
            chunks(v)
        elif isinstance(v, np.ndarray):
            if type(v) is not np.ndarray:raise TypeError('array subclass in cache key')
            if v.dtype.hasobject: raise TypeError('object array in read cache key')
            feed((v.dtype.str, v.shape, v.strides))
            h.update(str(v.nbytes).encode()+b':')
            for part in np.nditer(v,flags=['external_loop','buffered','zerosize_ok'],
                                  order='C',buffersize=max(1,65536//max(1,v.itemsize))):
                h.update(part.tobytes())
        elif is_dataclass(v) and not isinstance(v, type):
            raw(str(len(fields(v))).encode())
            for field in fields(v):feed(field.name);feed(getattr(v,field.name))
        elif isinstance(v, Mapping):
            raw(str(len(v)).encode())
            for k,item in v.items():feed(k);feed(item)
        elif isinstance(v, (list, tuple)):
            raw(str(len(v)).encode())
            for x in v: feed(x)
        elif isinstance(v, np.generic):
            if v.dtype.hasobject:raise TypeError('object scalar in cache key')
            feed((v.dtype.str, v.tobytes()))
        elif isinstance(v, bytes): raw(v)
        elif isinstance(v, float): raw(struct.pack('!d', v))
        elif type(v) is str:
            length=sum(len(v[i:i+1024].encode()) for i in range(0,len(v),1024))
            h.update(str(length).encode()+b':')
            for i in range(0,len(v),1024):h.update(v[i:i+1024].encode())
        elif v is None or type(v) in (bool, int): raw(str(v).encode())
        else: raise TypeError('unsupported read cache key: ' + type(v).__name__)
    feed(value)
    return h.hexdigest()


def snapshot(value):
    """Store tensors on CPU, with dtype/device and container type preserved."""
    if isinstance(value, torch.Tensor):
        return ('tensor', value.detach().to(device='cpu', copy=True), value.device)
    if isinstance(value, np.generic):return ('numpy_scalar',value.copy())
    if isinstance(value, np.ndarray):
        if value.dtype.hasobject: raise TypeError('object array in read cache value')
        return ('array', value.copy(order='K'))
    if is_dataclass(value) and not isinstance(value, type):
        return ('dataclass', type(value), {f.name:snapshot(getattr(value,f.name)) for f in fields(value)})
    if isinstance(value, Mapping):
        return ('mapping', type(value), [(k,snapshot(v)) for k,v in value.items()])
    if isinstance(value, (list, tuple)):
        return ('sequence', type(value), [snapshot(v) for v in value])
    if value is None or isinstance(value, (str, bytes, bool, int, float, np.generic, Enum)):
        return ('scalar', value)
    raise TypeError('unsupported read cache value: ' + type(value).__name__)


def restore(value):
    kind = value[0]
    if kind == 'tensor': return value[1].to(device=value[2], copy=True)
    if kind == 'array': return value[1].copy(order='K')
    if kind == 'numpy_scalar': return value[1].copy()
    if kind == 'dataclass': return value[1](**{k:restore(v) for k,v in value[2].items()})
    if kind == 'mapping': return value[1]({k:restore(v) for k,v in value[2]})
    if kind == 'sequence': return value[1](restore(v) for v in value[2])
    return value[1]


def image_identity(images, indices, identity):
    """Hash decoded RGB pixels without materializing a clip/frame byte string."""
    h=hashlib.sha256()
    h.update(digest((identity,indices,len(images))).encode())
    for image in images:
        if image.mode!='RGB' or getattr(image,'fp',None) is not None:
            raise ValueError('SAM cache requires decoded RGB memory images')
        h.update(digest((image.mode,image.size)).encode())
        for y in range(image.height):
            for x in range(0,image.width,512):
                h.update(image.crop((x,y,min(x+512,image.width),y+1)).tobytes())
    return h.hexdigest()


def immutable_key(value):
    if type(value) in (str,bytes,int,float,bool,type(None)):return True
    return type(value) is tuple and all(immutable_key(v) for v in value)


def payload_bytes(value):
    if isinstance(value,torch.Tensor):return value.numel()*value.element_size()
    if isinstance(value,np.ndarray):return value.nbytes
    if is_dataclass(value) and not isinstance(value,type):return sum(payload_bytes(getattr(value,f.name)) for f in fields(value))
    if isinstance(value,Mapping):return sum(payload_bytes(v) for v in value.values())
    if isinstance(value,(tuple,list)):return sum(map(payload_bytes,value))
    return 0


def nbytes(value):
    """Conservative owned-storage charge, including every container and key.

    Count aliases twice. The extra per-node allowance covers snapshot tags,
    restored container slots, tensor/storage wrappers and allocator alignment.
    The admission walk never copies a payload.
    """
    def visit(v, depth):
        if depth > 64:
            raise TypeError('read cache value nesting exceeds 64')
        size = sys.getsizeof(v) + 512
        if isinstance(v, torch.Tensor):
            if type(v) not in (torch.Tensor,torch.nn.Parameter):raise TypeError('tensor subclass in cache value')
            if not v.is_contiguous():raise TypeError('noncontiguous cache value')
            return size + v.numel()*v.element_size() + 512
        if isinstance(v, np.ndarray):
            if type(v) is not np.ndarray:raise TypeError('array subclass in cache value')
            if v.dtype.hasobject: raise TypeError('object array in read cache value')
            if not (v.flags.c_contiguous or v.flags.f_contiguous):raise TypeError('noncontiguous cache array')
            return size + (0 if v.flags.owndata else v.nbytes) + 512
        if is_dataclass(v) and not isinstance(v, type):
            cls=type(v)
            generated=(getattr(getattr(cls.__init__,'__code__',None),'co_filename',None)=='<string>'
                       and not hasattr(cls,'__post_init__')
                       and cls.__setattr__ is object.__setattr__
                       and cls.__new__ is object.__new__
                       and cls.__getattribute__ is object.__getattribute__
                       and not any(hasattr(cls.__dict__.get(f.name),'__set__') for f in fields(v)))
            audited=cls.__module__.startswith('transformers.')
            if not (generated or audited):raise TypeError('unaudited dataclass constructor')
            return size + sum(visit(getattr(v, f.name), depth+1)+512 for f in fields(v))
        if isinstance(v, Mapping):
            if type(v) not in (dict,OrderedDict) and not (type(v).__module__.startswith('transformers.') and type(v).__name__=='BatchFeature'):
                raise TypeError('unaudited mapping constructor')
            if any(not immutable_key(k) for k in v):raise TypeError('mutable mapping key')
            return size + sum(visit(k,depth+1)+visit(x,depth+1)+512 for k,x in v.items())
        if isinstance(v, (tuple,list)):
            if type(v) not in (tuple,list):raise TypeError('unaudited sequence constructor')
            return size + sum(visit(x,depth+1)+512 for x in v)
        if isinstance(v,np.generic) and v.dtype.hasobject:raise TypeError('object scalar in cache value')
        if v is None or type(v) in (str,bytes,bool,int,float) or isinstance(v,(np.generic,Enum,torch.device,type)):
            return size
        raise TypeError('unsupported read cache value: '+type(v).__name__)
    return visit(value,0)


class ReadCache:
    # Reserve room for the cache object, OrderedDict nodes, counters, and call
    # bookkeeping. Cache-owned storage is bounded; model/processor working
    # memory and values that the caller continues to own are outside this cap.
    BOOKKEEPING = 262144
    def __init__(self, max_bytes):
        if type(max_bytes) is not int or not self.BOOKKEEPING <= max_bytes <= 16*1024**3:
            raise ValueError('read_cache_bytes must be an integer in [256 KiB,16 GiB]')
        self.max_bytes = max_bytes
        self.entries = OrderedDict()
        self.held_bytes = 0
        self.peak_bytes = min(max_bytes,self.BOOKKEEPING)
        self.pid = os.getpid()
        self.thread = threading.get_ident()
        self.stats = {}

    def _room(self, reserve, info, keep=None):
        while self.entries and self.BOOKKEEPING+self.held_bytes+reserve > self.max_bytes:
            victim = next((k for k in self.entries if k != keep),None)
            if victim is None: break
            _, size, _ = self.entries.pop(victim)
            self.held_bytes -= size; info['evictions'] += 1
        total = self.BOOKKEEPING+self.held_bytes+reserve
        if total > self.max_bytes:return False
        self.peak_bytes = max(self.peak_bytes,total)
        return True

    def call(self, namespace, key, fresh):
        if self.pid != os.getpid():
            self.__init__(self.max_bytes)
        if self.thread != threading.get_ident():
            raise ValueError('ReadCache requires its owning serial thread')
        # Production namespaces are fixed. Bound diagnostic growth as well.
        if type(namespace) is not str or len(namespace)>64:return fresh()
        if namespace not in self.stats and len(self.stats) >= 16:
            return fresh()
        info = self.stats.setdefault(namespace, dict(hits=0, misses=0, evictions=0,
                                                     oversized=0, fresh_s=0., hit_s=0.))
        start = time.perf_counter()
        k = (namespace, key)
        if k in self.entries:
            saved, size, reserve = self.entries[k]
            if self._room(reserve,info,keep=k):
                info['hits'] += 1
                self.entries.move_to_end(k)
                out = restore(saved)
                info['hit_s'] += time.perf_counter()-start
                return out
        info['misses'] += 1
        value = fresh()
        info['fresh_s'] += time.perf_counter()-start
        try:
            # A snapshot has tag containers in addition to the original value.
            # Payload storage is charged once; the per-node allowance covers
            # snapshot tags, container slots and key/entry overhead. Reserve
            # a second complete copy before snapshots and hit restores.
            size=nbytes(value);payload=payload_bytes(value)
            reserve=payload+8*(size-payload)+nbytes(k)+8192+1024
        except TypeError:
            info['oversized'] += 1
            return value
        # Evict BEFORE allocating any snapshot. An oversized entry never copies.
        if not self._room(2*reserve,info):
            info['oversized'] += 1
            return value
        saved = snapshot(value)
        size = nbytes(saved)+nbytes(k)+1024
        if size > reserve:
            raise RuntimeError('Snapshot exceeded its preflight reservation')
        self.entries[k] = (saved, reserve, reserve)
        self.held_bytes += reserve
        return value


class VideoProcessorCache:
    """Forward all attributes; memoize only the processor's video call."""
    def __init__(self, target, cache):
        self.target, self.cache = target, cache

    def __getattr__(self, name):
        return getattr(self.target, name)

    def __call__(self, *args, **kwargs):
        config = self.target.to_dict()
        methods=hashlib.sha256()
        for cls in type(self.target).__mro__:
            for name,value in cls.__dict__.items():
                if callable(value):methods.update(digest((cls.__module__,cls.__qualname__,name,id(value))).encode())
        try:key = digest((id(self.target),methods.hexdigest(),config,args,kwargs,execution_state(),str(torch.get_default_dtype())))
        except (TypeError,RecursionError):
            info=self.cache.stats.setdefault('processor',dict(hits=0,misses=0,evictions=0,
                                                oversized=0,fresh_s=0.,hit_s=0.))
            info['bypasses']=info.get('bypasses',0)+1
            return self.target(*args,**kwargs)
        return self.cache.call('processor', key, lambda:self.target(*args, **kwargs))


def tensor_version(tensor):
    try:return tensor._version
    except RuntimeError:return None  # inference tensors still bind content below


def execution_state():
    return (torch.is_autocast_enabled('cuda'),str(torch.get_autocast_dtype('cuda')),
            torch.is_autocast_enabled('cpu'),str(torch.get_autocast_dtype('cpu')),
            torch.is_inference_mode_enabled(),torch.are_deterministic_algorithms_enabled(),
            str(torch.get_default_dtype()),torch.get_num_threads(),
            torch.get_float32_matmul_precision(),torch.backends.cudnn.deterministic,
            torch.backends.cudnn.benchmark,torch.backends.cudnn.allow_tf32,
            torch.backends.cuda.matmul.allow_tf32,
            torch.backends.cuda.matmul.allow_fp16_reduced_precision_reduction,
            torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction,
            torch.backends.cuda.matmul.allow_fp16_accumulation,torch.backends.cuda.flash_sdp_enabled(),
            torch.backends.cuda.mem_efficient_sdp_enabled(),torch.backends.cuda.math_sdp_enabled())


def module_identity(model):
    """Stream live model identity/content; never assemble a model-sized key."""
    h=hashlib.sha256()
    h.update(digest((id(model),execution_state())).encode())
    for name,module in model.named_modules():
        h.update(digest((name,id(module),type(module).__module__,type(module).__qualname__,
                         id(getattr(module.forward,'__func__',module.forward)),module.training)).encode())
        configuration=getattr(module,'config',None)
        h.update(digest((getattr(configuration,'_attn_implementation',None),
                         getattr(configuration,'_attn_implementation_internal',None))).encode())
        for key,value in vars(module).items():
            if key.startswith('_') or key in ('training','calls'):continue
            if hasattr(value,'to_dict'):value=value.to_dict()
            elif callable(value):value=('callable',id(value))
            try:stamp=digest(value)
            except TypeError:stamp=digest((type(value).__module__,type(value).__qualname__,id(value)))
            h.update(digest((key,stamp)).encode())
    for iterator in (model.named_parameters(),model.named_buffers()):
        for name,tensor in iterator:
            h.update(digest((name,id(tensor),tensor.data_ptr(),tensor_version(tensor),digest(tensor))).encode())
    return h.hexdigest()


def has_hooks(model, *, children_only=False):
    from torch.nn.modules import module as runtime
    for index,module in enumerate(model.modules()):
        if (getattr(module,'_compiled_call_impl',None) is not None or getattr(module,'_hf_hook',None) is not None):
            return True
        if index==0 and children_only:continue
        if module._forward_hooks or module._forward_pre_hooks:return True
    return bool(runtime._global_forward_hooks or runtime._global_forward_pre_hooks)


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
        # Outer hooks still run in Module.__call__; child/global hooks and
        # compiled/accelerated dispatch must execute the original forward.
        if has_hooks(visual,children_only=True):
            info = cache.stats.setdefault('vision_bypass', {'calls':0})
            info['calls'] += 1
            return original(*args, **kwargs)
        # Bind identity and content: replacements and raw-storage writes must miss.
        try:key = digest((visual.config.to_dict(),module_identity(visual),args,kwargs))
        except (TypeError,RecursionError):
            info=cache.stats.setdefault('vision_bypass',{'calls':0});info['calls']+=1
            return original(*args,**kwargs)
        return cache.call('vision', key, lambda:original(*args, **kwargs))
    visual.forward = forward
    visual._read_cache_installed = True
