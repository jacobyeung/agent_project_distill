"""Frozen local Qwen3.5 vision taps and hash-pinned name embedding rows."""
from dataclasses import dataclass
import hashlib
from pathlib import Path

import numpy as np
from PIL import Image
import torch
from torch.nn import functional as F

from .common import normalize_name, read_json, sha256_file, sha256_json

TAP_LAYERS = (9, 17, 25, 27)
WORK = Path('/scratch/jjyeung/orch_n30/b05_owngrd/work')
DEFAULT_WEIGHTS = WORK / 'm544sub/sub/subset.safetensors'
DEFAULT_BUNDLE = WORK / 'from118/t0bundle/base'


def tensor_digest(state):
    h = hashlib.sha256()
    for key, value in sorted(state.items()):
        h.update(key.encode())
        h.update(str(tuple(value.shape)).encode())
        h.update(str(value.dtype).encode())
        h.update(value.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes())
    return h.hexdigest()


def rgb_tensor(frames, size_hw):
    h, w = size_hw
    return torch.from_numpy(np.stack([np.asarray(im.convert('RGB').resize(
        (w, h), Image.Resampling.BICUBIC), dtype=np.float32) / 255 for im in frames])).permute(0, 3, 1, 2)


def frame_size(frame, size_hw=(480, 640)):
    """Interpret size_hw as landscape; preserve a portrait frame's orientation."""
    h, w = sorted(size_hw)
    return (w, h) if frame.height > frame.width else (h, w)


def pack_qwen(rgb, patch=16, temporal=2, merge=2):
    n, c, h, w = rgb.shape
    if h % (patch * merge) or w % (patch * merge):
        raise ValueError('Qwen dimensions must be divisible by patch * merge')
    x = rgb[:, None].expand(n, temporal, c, h, w)
    x = x.reshape(n, temporal, c, h//patch//merge, merge, patch, w//patch//merge, merge, patch)
    packed = x.permute(0, 3, 6, 4, 7, 2, 1, 5, 8).reshape(n*h//patch*w//patch, -1)
    # Independent still images, each duplicated across its temporal patch.
    return packed, torch.tensor([[1, h//patch, w//patch]] * n, dtype=torch.long)


def unpack_qwen(tokens, grid, merge=2):
    grids = grid.cpu().tolist()
    if not grids or any(g != grids[0] or g[0] != 1 for g in grids):
        raise ValueError('Expected equally sized independent frames')
    _, h, w = grids[0]
    n = len(grids)
    return tokens.reshape(n, h//merge, w//merge, merge, merge, -1).permute(
        0, 1, 3, 2, 4, 5).reshape(n, h, w, -1)


@dataclass
class NameQuery:
    tokens: torch.Tensor
    mask: torch.Tensor
    token_ids: list
    rows_sha256: str
    tokenizer_sha256: str

    def __iter__(self):
        yield self.tokens
        yield self.mask


class FrozenViT:
    def __init__(self, weights=DEFAULT_WEIGHTS, bundle=DEFAULT_BUNDLE, device='cpu', verify_file=True):
        from safetensors import safe_open
        from transformers import AutoTokenizer
        from transformers.models.qwen3_5.configuration_qwen3_5 import Qwen3_5VisionConfig
        from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5VisionModel
        torch.set_num_threads(min(torch.get_num_threads(), 16))
        self.weights, self.bundle = Path(weights), Path(bundle)
        self.device = torch.device(device)
        self.file_sha256 = None
        if verify_file:
            pins = (self.weights.parent / 'SHA256SUMS').read_text().splitlines()
            expected = next((line.split()[0] for line in pins
                             if line.split()[-1].lstrip('*').split('/')[-1] == self.weights.name), None)
            if expected is None or sha256_file(self.weights) != expected:
                raise ValueError('Subset checksum mismatch or missing SHA256SUMS entry')
            self.file_sha256 = expected
        cfg = Qwen3_5VisionConfig(**read_json(self.bundle / 'config.json')['vision_config'])
        cfg._attn_implementation = 'sdpa'
        with torch.device('meta'):
            model = Qwen3_5VisionModel(cfg)
        with safe_open(str(self.weights), framework='pt', device='cpu') as f:
            state = {k.removeprefix('model.visual.'): f.get_tensor(k)
                     for k in f.keys() if k.startswith('model.visual.')}
        self.source_state_sha256 = tensor_digest(state)
        model.load_state_dict(state, strict=True, assign=True)
        rotary = model.rotary_pos_emb
        model.rotary_pos_emb = type(rotary)(dim=cfg.hidden_size//cfg.num_heads//2,
                                           theta=getattr(rotary, 'theta', 10000.))
        self.model = model.float().to(self.device).eval().requires_grad_(False)
        if any(b.is_meta for b in model.buffers()):
            raise ValueError('Unmaterialized vision buffer')
        self.state_sha256 = tensor_digest(self.model.state_dict())
        self.sha256 = sha256_json(dict(state=self.state_sha256, config=sha256_file(self.bundle/'config.json'),
                                      taps=TAP_LAYERS, merge='final-tap-2x2-mean', preprocess='rgb-bicubic-.5-.5'))
        self.tokenizer = AutoTokenizer.from_pretrained(str(self.bundle), local_files_only=True)
        self.tokenizer_sha256 = sha256_json({p.name: sha256_file(p) for p in sorted(self.bundle.glob('*'))
                                           if p.is_file() and ('token' in p.name or p.name in ('vocab.json', 'merges.txt'))})
        self.rows = {}

    @torch.no_grad()
    def taps(self, frames, size_hw=None):
        if not frames:
            raise ValueError('Empty frame batch')
        size = tuple(size_hw) if size_hw is not None else frame_size(frames[0])
        if size_hw is None and any(frame_size(im) != size for im in frames):
            raise ValueError('Batch frames by orientation or pass an explicit size')
        cfg = self.model.config
        x, grid = pack_qwen((rgb_tensor(frames, size)-.5)/.5, cfg.patch_size,
                            cfg.temporal_patch_size, cfg.spatial_merge_size)
        captured, handles = {}, []
        for layer in TAP_LAYERS:
            def hook(module, args, value, layer=layer):
                captured[layer] = value[0] if isinstance(value, tuple) else value
            handles.append(self.model.blocks[layer-1].register_forward_hook(hook))
        try:
            self.model.eval()(x.to(self.device), grid_thw=grid.to(self.device))
        finally:
            for handle in handles:
                handle.remove()
        maps = [unpack_qwen(captured[k], grid, cfg.spatial_merge_size).detach() for k in TAP_LAYERS]
        merged = F.avg_pool2d(maps[-1].permute(0, 3, 1, 2), 2, 2).permute(0, 2, 3, 1).contiguous()
        return maps, merged

    def name_query(self, names):
        from safetensors import safe_open
        normalized = [normalize_name(n) for n in names]
        if not normalized or any(not n for n in normalized):
            raise ValueError('Names must be nonempty')
        ids = [self.tokenizer.encode(n, add_special_tokens=False) for n in normalized]
        if any(not seq for seq in ids):
            raise ValueError('Name has no tokens')
        unique = sorted({i for seq in ids for i in seq})
        with safe_open(str(self.weights), framework='pt', device='cpu') as f:
            rows = f.get_slice('model.language_model.embed_tokens.weight')
            if rows.get_shape() != [248320, 4096]:
                raise ValueError('Unexpected embedding shape')
            for i in unique:
                if i not in self.rows:
                    self.rows[i] = rows[i:i+1].clone()[0]
        digest = tensor_digest({str(i): self.rows[i] for i in unique})
        tokens = torch.zeros(len(ids), max(map(len, ids)), 4096)
        mask = torch.zeros(tokens.shape[:2], dtype=torch.bool)
        for j, seq in enumerate(ids):
            tokens[j, :len(seq)] = torch.stack([self.rows[i].float() for i in seq])
            mask[j, :len(seq)] = True
        return NameQuery(tokens.to(self.device), mask.to(self.device), ids, digest, self.tokenizer_sha256)
