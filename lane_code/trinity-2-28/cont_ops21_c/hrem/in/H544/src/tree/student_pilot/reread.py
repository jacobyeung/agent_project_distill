"""Frozen, clip-scoped native ViT reads; no language-model forward or new weights."""
from collections import OrderedDict
from contextlib import ExitStack, nullcontext
from dataclasses import dataclass
import hashlib
from numbers import Integral

import numpy as np
from PIL import Image
import torch

from .point_depth_head import vit_grids_by_row


TAP_LAYERS = (9, 17, 25, 27)


def rgb_array(frame):
    value = np.asarray(frame)
    if value.dtype != np.uint8 or value.ndim != 3 or value.shape[2] != 3:
        raise ValueError('Frames must be native uint8 RGB HWC arrays or RGB PIL images')
    return np.array(value, copy=True, order='C')


def rgb_hash(frame):
    return hashlib.sha256(memoryview(np.ascontiguousarray(frame))).hexdigest()


def _sha(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def _ids(values):
    result = tuple(values)
    if not result or any(isinstance(v, bool) or not isinstance(v, Integral) or v < 1 for v in result):
        raise ValueError('Frame slots must be nonempty positive one-based integers')
    return tuple(map(int, result))


@dataclass(frozen=True)
class Config:
    """Opt-in row configuration. Frame identity comes from the decoder's batch."""
    frames: dict
    frame_indices: tuple
    clip_key: str
    size_hw: tuple = (768, 1024)
    preload_ids: tuple = ()
    layers: tuple = TAP_LAYERS
    chunk_size: int = 1
    max_cache_bytes: int = 256 * 1024 * 1024
    tower: str = 'own'
    sdpa_backend: str = 'auto'

    def validate(self, model, batch):
        if not _sha(self.clip_key) or batch.get('video_sha256') != self.clip_key:
            raise ValueError('Re-read clip key must match the batch video_sha256')
        if tuple(batch.get('frame_indices', ())) != tuple(self.frame_indices):
            raise ValueError('Re-read source indices differ from the displayed frames')
        if getattr(model, 'frame_layout', 'duplicate') != 'duplicate':
            raise ValueError('RGB re-reads require duplicate temporal frames; paired/spread need a pair adapter')
        hashes = batch.get('frame_rgb_sha256')
        if not isinstance(hashes, (list, tuple)) or len(hashes) != len(self.frame_indices):
            raise ValueError('Batch must supply one RGB SHA-256 per displayed frame')
        _ids(self.frames)
        for slot, frame in self.frames.items():
            if slot > len(hashes) or rgb_hash(rgb_array(frame)) != hashes[slot - 1]:
                raise ValueError('Re-read RGB differs from the authoritative displayed frame')
        if self.preload_ids and any(i not in self.frames for i in _ids(self.preload_ids)):
            raise ValueError('Preload slot is absent from frames')

    def bind(self, model, processor, batch):
        self.validate(model, batch)
        reader = ReRead(model, layers=self.layers, chunk_size=self.chunk_size,
                        max_cache_bytes=self.max_cache_bytes, tower=self.tower,
                        sdpa_backend=self.sdpa_backend)
        reader.bind_clip(self.clip_key, self.frames, processor=processor,
                         frame_indices=self.frame_indices, prefill_batch=batch)
        reader._size(self.size_hw)
        if self.preload_ids:
            reader.features(self.preload_ids, self.size_hw)
        return reader


class ReRead:
    """A plain Python object sharing the selected ViT. Use serially in eval mode.

    features returns {one_based_block: Tensor[F, H/patch, W/patch, C]} in
    caller frame order. bind_clip snapshots RGB and optional native prefill packs.
    Calling it again clears all cached tensors, even for the same clip key.
    """

    def __init__(self, model, *, layers=TAP_LAYERS, chunk_size=1,
                 max_cache_bytes=256 * 1024 * 1024, tower='own', sdpa_backend='auto'):
        if tower not in ('own', 'vc'):
            raise ValueError('tower must be own or vc')
        self.model = model
        self.visual = (model.model.visual if tower == 'own'
                       else model.auxiliary_heads.depth.model.visual)
        self.tower = tower
        self.layers = _ids(layers)
        if len(set(self.layers)) != len(self.layers) or max(self.layers) > len(self.visual.blocks):
            raise ValueError('Requested ViT blocks must be distinct and exist')
        if type(chunk_size) is not int or chunk_size < 1 or type(max_cache_bytes) is not int or max_cache_bytes < 0:
            raise ValueError('Invalid chunk size or cache byte budget')
        if sdpa_backend not in ('auto', 'math', 'flash', 'efficient', 'cudnn'):
            raise ValueError('Unknown SDPA backend')
        self.chunk_size, self.max_cache_bytes = chunk_size, max_cache_bytes
        self.sdpa_backend = sdpa_backend
        self.cache = OrderedDict()
        self.cache_bytes = 0
        self.clip_key = None
        self.forward_calls = self.frames_encoded = self.cache_hits = 0
        self._busy = False

    def _signature(self):
        # Detect parameter replacement, normal in-place updates, device/dtype and attention changes.
        return (self.visual.config._attn_implementation,
                tuple((id(p), p.data_ptr(), p._version, p.device, p.dtype)
                      for p in self.visual.parameters()))

    def bind_clip(self, clip_key, frames, *, processor=None, frame_indices=None, prefill_batch=None):
        if not _sha(clip_key):
            raise ValueError('clip_key must be a SHA-256')
        slots = _ids(frames)
        if frame_indices is not None and max(slots) > len(frame_indices):
            raise ValueError('Frame slot exceeds the source-index map')
        self.frames = {i: rgb_array(frames[i]) for i in slots}
        self.frame_hashes = {i: rgb_hash(v) for i, v in self.frames.items()}
        self.frame_indices = tuple(frame_indices) if frame_indices is not None else None
        self.processor = getattr(processor, 'image_processor', processor)
        self.prefill = None
        if prefill_batch is not None:
            grid = prefill_batch['video_grid_thw']
            if tuple(grid.shape) != (1, 3):
                raise ValueError('Re-read expects one video per row')
            t, h, w = map(int, grid[0])
            pixels = prefill_batch['pixel_values_videos']
            if max(slots) > t or pixels.ndim != 2 or pixels.shape[0] != t * h * w:
                raise ValueError('Prefill packed tokens disagree with frame slots')
            self.prefill = (h, w, {i: pixels[(i-1)*h*w:i*h*w].detach().clone() for i in slots})
        self.clip_key = clip_key
        self.clear_cache()
        self._bound_signature = self._signature()
        return self

    def clear_cache(self):
        self.cache.clear()
        self.cache_bytes = 0

    def _size(self, size_hw):
        if len(size_hw) != 2 or any(type(v) is not int or v <= 0 for v in size_hw):
            raise ValueError('size_hw must be positive (height, width) integers')
        factor = self.visual.config.patch_size * self.visual.config.spatial_merge_size
        if any(v % factor for v in size_hw):
            raise ValueError('Height and width must be divisible by patch_size * spatial_merge_size')
        return tuple(size_hw)

    def _prepare(self, ids, size):
        patch = self.visual.config.patch_size
        h, w = (s // patch for s in size)
        if self.prefill is not None and self.prefill[:2] == (h, w):
            pixels = torch.cat([self.prefill[2][i] for i in ids])
            grid = torch.tensor([[1, h, w]] * len(ids))
        else:
            if self.processor is None:
                raise ValueError('RGB resizing requires the checkpoint image processor')
            images = [Image.fromarray(self.frames[i]).resize((size[1], size[0]),
                      resample=Image.Resampling.BICUBIC) for i in ids]
            packed = self.processor(images=images, do_resize=False, return_tensors='pt')
            pixels, grid = packed['pixel_values'], packed['image_grid_thw']
            if grid.tolist() != [[1, h, w]] * len(ids):
                raise ValueError('Processor changed the requested grid; check patch/merge/temporal settings')
        param = next(self.visual.parameters())
        dtype = torch.bfloat16 if self.tower == 'vc' else param.dtype
        return pixels.to(device=param.device, dtype=dtype), grid.to(param.device)

    def _attention(self):
        if self.sdpa_backend == 'auto':
            return nullcontext()
        if self.visual.config._attn_implementation != 'sdpa':
            raise ValueError('A forced SDPA backend requires vision _attn_implementation=sdpa')
        from torch.nn.attention import SDPBackend, sdpa_kernel
        modes = dict(math=SDPBackend.MATH, flash=SDPBackend.FLASH_ATTENTION,
                     efficient=SDPBackend.EFFICIENT_ATTENTION, cudnn=SDPBackend.CUDNN_ATTENTION)
        return sdpa_kernel(modes[self.sdpa_backend])

    def _run(self, ids, size):
        pixels, grid = self._prepare(ids, size)
        captured = {}
        with ExitStack() as stack:
            for layer in self.layers:
                def hook(module, args, out, layer=layer):
                    value = out[0] if isinstance(out, tuple) else out
                    captured[layer] = value.detach().clone()
                handle = self.visual.blocks[layer - 1].register_forward_hook(hook)
                stack.callback(handle.remove)
            stack.enter_context(self._attention())
            if self.tower == 'vc':
                # Match decoupled_vc.capture_features without mutating fp32 masters.
                from torch.func import functional_call
                parameters = {n: p.to(torch.bfloat16) for n, p in self.visual.named_parameters()}
                functional_call(self.visual, parameters, (pixels,), {'grid_thw': grid})
            else:
                self.visual(pixels, grid_thw=grid)
        if set(captured) != set(self.layers):
            raise RuntimeError('Incomplete ViT tap capture')
        self.forward_calls += 1
        self.frames_encoded += len(ids)
        merge = self.visual.config.spatial_merge_size
        return {k: torch.cat(vit_grids_by_row(v, grid, merge), dim=0) for k, v in captured.items()}

    @torch.no_grad()
    def features(self, frame_ids, size_hw):
        if self.clip_key is None:
            raise ValueError('Bind a clip before reading features')
        if self.model.training or any(m.training for m in self.visual.modules()):
            raise ValueError('Re-read requires eval mode; it never changes training flags')
        if self._busy:
            raise RuntimeError('ReRead supports serial calls only')
        ids, size = _ids(frame_ids), self._size(size_hw)
        if any(i not in self.frames for i in ids):
            raise ValueError('Requested frame is not bound to this clip')
        if self._bound_signature != self._signature():
            self.clear_cache()
            raise RuntimeError('ViT weights/device/dtype/attention changed; bind the clip again')
        result, missing = {}, []
        for i in dict.fromkeys(ids):
            key = (i, size)
            if key in self.cache:
                self.cache_hits += 1
                self.cache.move_to_end(key)
                result[i] = self.cache[key]
            else:
                missing.append(i)
        self._busy = True
        try:
            for start in range(0, len(missing), self.chunk_size):
                chunk = missing[start:start + self.chunk_size]
                taps = self._run(chunk, size)
                for n, i in enumerate(chunk):
                    values = {k: v[n].clone() for k, v in taps.items()}
                    result[i] = values
                    cost = sum(v.numel() * v.element_size() for v in values.values())
                    if cost <= self.max_cache_bytes:
                        while self.cache and self.cache_bytes + cost > self.max_cache_bytes:
                            _, old = self.cache.popitem(last=False)
                            self.cache_bytes -= sum(v.numel() * v.element_size() for v in old.values())
                        self.cache[(i, size)] = values
                        self.cache_bytes += cost
        except BaseException:
            self.clear_cache()
            raise
        finally:
            self._busy = False
        # Stacking protects cached storage from downstream in-place operations.
        return {k: torch.stack([result[i][k] for i in ids]) for k in self.layers}


def validate_batch(model, batch, mode):
    config = batch.get('own_vit_reread')
    if config is not None:
        if not isinstance(config, Config) or mode != 'own':
            raise ValueError('Own ViT re-read requires Config and own mode')
        config.validate(model, batch)


def bind_heads(model, processor, batch, heads):
    config = batch.get('own_vit_reread')
    if config is not None:
        heads.own_rereader = config.bind(model, processor, batch)
