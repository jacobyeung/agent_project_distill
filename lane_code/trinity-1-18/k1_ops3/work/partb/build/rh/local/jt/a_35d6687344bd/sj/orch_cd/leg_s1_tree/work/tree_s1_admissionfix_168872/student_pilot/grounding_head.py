"""Dense grounding on detached, frame-aligned language and vision features."""
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F


@dataclass
class GHConfig:
    vit_dim: int
    lm_dim: int = 4096
    dim: int = 512
    n_taps: int = 3
    frames: int = 32
    blocks: int = 3
    heads: int = 8
    text_layers: int = 2
    token_update: bool = True
    point_weight: float = 0.1
    dropout: float = 0.0

    def __post_init__(self):
        for name in ('vit_dim', 'lm_dim', 'dim', 'n_taps', 'frames', 'blocks', 'heads', 'text_layers'):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise ValueError('Invalid GH configuration: ' + name)
        if self.dim % self.heads:
            raise ValueError('GH dim must be divisible by heads')
        if type(self.token_update) is not bool:
            raise ValueError('Invalid GH token_update')
        for name in ('point_weight', 'dropout'):
            value = getattr(self, name)
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError('Invalid GH configuration: ' + name)
        if self.dropout >= 1:
            raise ValueError('GH dropout must be less than one')


class _Attention(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.heads, self.dropout = cfg.heads, cfg.dropout
        self.q, self.k, self.v, self.proj = (nn.Linear(cfg.dim, cfg.dim) for _ in range(4))

    def forward(self, query, context, mask=None):
        batch, length, dim = query.shape
        def split(value):
            return value.reshape(batch, -1, self.heads, dim // self.heads).transpose(1, 2)
        value = F.scaled_dot_product_attention(split(self.q(query)), split(self.k(context)),
                                              split(self.v(context)), attn_mask=mask,
                                              dropout_p=self.dropout if self.training else 0.)
        return self.proj(value.transpose(1, 2).reshape(batch, length, dim))


def _mlp(dim):
    return nn.Sequential(nn.Linear(dim, 4 * dim), nn.GELU(), nn.Linear(4 * dim, dim))


class _TextBlock(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.norm1, self.norm2 = nn.LayerNorm(cfg.dim), nn.LayerNorm(cfg.dim)
        self.attn, self.mlp = _Attention(cfg), _mlp(cfg.dim)

    def forward(self, tokens, mask):
        normalized = self.norm1(tokens)
        tokens = tokens + self.attn(normalized, normalized, mask)
        return tokens + self.mlp(self.norm2(tokens))


class _TwoWayBlock(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.self_attn, self.cross_attn = _Attention(cfg), _Attention(cfg)
        self.self_norm, self.cross_norm = nn.LayerNorm(cfg.dim), nn.LayerNorm(cfg.dim)
        self.token_norm, self.mlp_norm = nn.LayerNorm(cfg.dim), nn.LayerNorm(cfg.dim)
        self.mlp = _mlp(cfg.dim)
        self.token_update = cfg.token_update
        if self.token_update:
            self.reverse_attn = _Attention(cfg)
            self.reverse_query_norm, self.reverse_token_norm = nn.LayerNorm(cfg.dim), nn.LayerNorm(cfg.dim)

    def forward(self, query, tokens):
        labels, frames, dim = query.shape
        normalized = self.self_norm(query)
        query = query + self.self_attn(normalized, normalized)
        flat = self.cross_norm(query).reshape(labels * frames, 1, dim)
        query = query + self.cross_attn(flat, self.token_norm(tokens)).reshape(labels, frames, dim)
        query = query + self.mlp(self.mlp_norm(query))
        if self.token_update:
            flat = self.reverse_query_norm(query).reshape(labels * frames, 1, dim)
            tokens = tokens + self.reverse_attn(self.reverse_token_norm(tokens), flat)
        return query, tokens


def _local_point(heat):
    """Use soft weights in the clipped 3x3 window selected by a detached argmax."""
    height, width = heat.shape[-2:]
    flat = heat.float().flatten(-2)
    peak = flat.detach().argmax(-1)
    offsets = torch.arange(-1, 2, device=heat.device)
    dy, dx = torch.meshgrid(offsets, offsets, indexing='ij')
    rows = peak[..., None] // width + dy.flatten()
    cols = peak[..., None] % width + dx.flatten()
    valid = (rows >= 0) & (rows < height) & (cols >= 0) & (cols < width)
    indices = rows.clamp(0, height - 1) * width + cols.clamp(0, width - 1)
    weights = flat.gather(-1, indices).masked_fill(~valid, -torch.inf).softmax(-1)
    x = (weights * (cols.float() + .5)).sum(-1) / width * 1000
    y = (weights * (rows.float() + .5)).sum(-1) / height * 1000
    return torch.stack((x, y), dim=-1)


class GroundingHead(nn.Module):
    def __init__(self, cfg: GHConfig):
        super().__init__()
        self.cfg = cfg
        d = cfg.dim
        self.tap_mix = nn.Parameter(torch.zeros(cfg.n_taps))
        self.video_norm, self.video_proj = nn.LayerNorm(cfg.lm_dim), nn.Linear(cfg.lm_dim, d)
        self.frame_embed = nn.Parameter(torch.empty(cfg.frames, d))
        self.text_proj = nn.Linear(cfg.lm_dim, d)
        self.pres_token = nn.Parameter(torch.empty(1, 1, d))
        self.text_blocks = nn.ModuleList([_TextBlock(cfg) for _ in range(cfg.text_layers)])
        self.text_norm = nn.LayerNorm(d)
        self.blocks = nn.ModuleList([_TwoWayBlock(cfg) for _ in range(cfg.blocks)])
        self.presence = nn.Sequential(nn.Linear(d, d), nn.GELU(), nn.Linear(d, 1))
        self.token_heat_query, self.patch_heat_query = nn.Linear(d, d), nn.Linear(d, d)
        self.vit_proj = nn.Linear(cfg.vit_dim, d)
        self.upsampler = nn.Sequential(nn.Conv2d(d, d, 3, padding=1), nn.GELU(),
                                       nn.Conv2d(d, d, 3, padding=1))
        nn.init.normal_(self.frame_embed, std=.02)
        nn.init.normal_(self.pres_token, std=.02)

    def encode_video(self, taps, vit, grid):
        if len(grid) != 2 or any(type(k) is not int or k < 1 for k in grid):
            raise ValueError('Expected a positive (gh, gw) grid')
        gh, gw = grid
        if len(taps) != self.cfg.n_taps or taps[0].ndim != 3:
            raise ValueError('Expected n_taps tensors [F, N, lm_dim]')
        frames = taps[0].shape[0]
        if not 1 <= frames <= self.cfg.frames:
            raise ValueError('Unsupported frame count')
        if any(t.shape != (frames, gh * gw, self.cfg.lm_dim) for t in taps):
            raise ValueError('Taps do not match the merged grid or lm_dim')
        if vit.shape != (frames, 2 * gh, 2 * gw, self.cfg.vit_dim):
            raise ValueError('ViT features do not match the patch grid or vit_dim')
        with torch.autocast(device_type=vit.device.type, enabled=False):
            mixed = sum(w * t.detach().float() for w, t in zip(self.tap_mix.softmax(0), taps))
            tokens = self.video_proj(self.video_norm(mixed)) + self.frame_embed[:frames, None]
            return dict(tokens=tokens, vit=self.vit_proj(vit.detach().float()), grid=(gh, gw))

    def encode_query(self, phrase_embeds, phrase_mask):
        if (phrase_embeds.ndim != 3 or phrase_embeds.shape[-1] != self.cfg.lm_dim
                or phrase_mask.shape != phrase_embeds.shape[:2] or phrase_mask.dtype != torch.bool
                or phrase_embeds.shape[0] < 1):
            raise ValueError('Expected phrase embeddings [Q, T, lm_dim] and boolean mask [Q, T]')
        with torch.autocast(device_type=phrase_embeds.device.type, enabled=False):
            embeds = phrase_embeds.detach().float().masked_fill(~phrase_mask[..., None], 0.)
            tokens = torch.cat((self.pres_token.expand(embeds.shape[0], -1, -1), self.text_proj(embeds)), dim=1)
            mask = torch.cat((torch.ones_like(phrase_mask[:, :1]), phrase_mask), dim=1)
            if phrase_mask.shape[1] == 0:
                mask = torch.ones((embeds.shape[0], 1), device=embeds.device, dtype=torch.bool)
            for block in self.text_blocks:
                tokens = block(tokens, mask[:, None, None, :])
            return self.text_norm(tokens[:, 0])

    def forward(self, memory, query):
        gh, gw = memory['grid']
        frames, cells, dim = memory['tokens'].shape
        if query.ndim != 2 or query.shape[-1] != self.cfg.dim or query.shape[0] < 1:
            raise ValueError('Expected query [Q, dim]')
        labels = query.shape[0]
        with torch.autocast(device_type=query.device.type, enabled=False):
            query = query.float()[:, None] + self.frame_embed[None, :frames]
            tokens = memory['tokens'].float()[None].expand(labels, -1, -1, -1).reshape(labels * frames, cells, dim)
            for block in self.blocks:
                query, tokens = block(query, tokens)
            coarse = (self.token_heat_query(query).reshape(labels * frames, 1, dim) * tokens).sum(-1) / math.sqrt(dim)
            feature = tokens.transpose(1, 2).reshape(labels * frames, dim, gh, gw)
            feature = F.interpolate(feature, scale_factor=2, mode='bilinear', align_corners=False)
            fine = memory['vit'].float().permute(0, 3, 1, 2)[None].expand(labels, -1, -1, -1, -1)
            feature = self.upsampler(feature + fine.reshape(labels * frames, dim, 2 * gh, 2 * gw))
            heat = (self.patch_heat_query(query).reshape(labels * frames, dim, 1, 1) * feature).sum(1) / math.sqrt(dim)
            # Preserve the token-grid readout as a residual in the refined patch logits.
            heat = heat + F.interpolate(coarse.reshape(labels * frames, 1, gh, gw), scale_factor=2,
                                        mode='bilinear', align_corners=False)[:, 0]
            return dict(presence=self.presence(query).squeeze(-1), heat=heat.reshape(labels, frames, 2 * gh, 2 * gw))

    def loss(self, out, targets):
        with torch.autocast(device_type=out['heat'].device.type, enabled=False):
            logits, heat = out['presence'].float(), out['heat'].float()
            presence, mass, point = (targets[k].to(device=heat.device, dtype=torch.float32)
                                     for k in ('presence', 'mass', 'point'))
            valid = targets['presence_valid'].to(device=heat.device, dtype=torch.bool) & torch.isfinite(presence)
            positive, negative = valid & (presence == 1), valid & (presence == 0)
            zero = logits.flatten()[:0].sum() + heat.flatten()[:0].sum()
            pos_loss = F.softplus(-logits[positive]).mean() if positive.any() else zero
            neg_loss = F.softplus(logits[negative]).mean() if negative.any() else zero
            presence_loss = .5 * (pos_loss + neg_loss)
            heat_valid = positive & torch.isfinite(mass).all((-1, -2)) & (mass >= 0).all((-1, -2)) & (mass.sum((-1, -2)) > 0)
            heat_loss = -(mass[heat_valid].flatten(1) * heat[heat_valid].flatten(1).log_softmax(-1)).sum(-1).mean() if heat_valid.any() else zero
            point_valid = (positive & targets['point_valid'].to(device=heat.device, dtype=torch.bool)
                           & torch.isfinite(point).all(-1))
            point_loss = F.l1_loss(_local_point(heat[point_valid]) / 1000, point[point_valid] / 1000) if point_valid.any() else zero
            return dict(total=presence_loss + heat_loss + self.cfg.point_weight * point_loss,
                        presence=presence_loss, heat=heat_loss, point=point_loss)

    @staticmethod
    def decode(out):
        return dict(prob=out['presence'].float().sigmoid(), uv=_local_point(out['heat']).round().clamp(0, 1000).long())


def _validate_meta(meta):
    if not isinstance(meta, dict) or meta.get('schema') != 'grounding-head-v1':
        raise ValueError('Expected grounding-head-v1 artifact schema')
    try:
        cfg = GHConfig(**meta['config'])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError('Invalid grounding artifact config') from exc
    tau = meta.get('tau')
    if type(tau) not in (int, float) or not math.isfinite(tau) or not 0 <= tau <= 1:
        raise ValueError('Invalid grounding artifact tau')
    pin = meta.get('base_artifact')
    if (not isinstance(pin, dict) or not isinstance(pin.get('path'), str) or not pin['path']
            or not isinstance(pin.get('sha256'), str) or len(pin['sha256']) != 64
            or any(c not in '0123456789abcdef' for c in pin['sha256'])):
        raise ValueError('Invalid grounding base_artifact pin')
    if not isinstance(meta.get('trainer_commit'), str) or not meta['trainer_commit']:
        raise ValueError('Missing grounding trainer_commit')
    if type(meta.get('step')) is not int or meta['step'] < 0 or not isinstance(meta.get('metrics'), dict):
        raise ValueError('Invalid grounding step or metrics')
    return cfg


def save_artifact(directory, head, meta):
    meta = dict(meta)
    if 'schema' in meta and meta['schema'] != 'grounding-head-v1':
        raise ValueError('Expected grounding-head-v1 artifact schema')
    if 'config' in meta and meta['config'] != asdict(head.cfg):
        raise ValueError('Grounding artifact config differs from head')
    meta.update(schema='grounding-head-v1', config=asdict(head.cfg))
    _validate_meta(meta)
    payload = json.dumps(meta, indent=2, sort_keys=True, allow_nan=False) + '\n'
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if (directory / 'gh.pt').exists() or (directory / 'gh.json').exists():
        raise FileExistsError('Grounding artifact already exists')
    with (directory / 'gh.pt').open('xb') as stream:
        torch.save({name: value.detach().cpu() for name, value in head.state_dict().items()}, stream)
    with (directory / 'gh.json').open('x') as stream:
        stream.write(payload)


def load_artifact(directory):
    directory = Path(directory)
    meta = json.loads((directory / 'gh.json').read_text())
    cfg = _validate_meta(meta)
    head = GroundingHead(cfg)
    head.load_state_dict(torch.load(directory / 'gh.pt', map_location='cpu', weights_only=True), strict=True)
    return head.eval(), meta
