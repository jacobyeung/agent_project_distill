"""Batched mask grounding on detached language, vision and RGB features."""
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from .grounding_head import _Attention, _validate_meta as _validate_gh_meta


STEM_WEIGHTS = '/scratch/jjyeung/orch_cd/mdg_build/work/weights/resnet18-f37072fd.pth'
STEM_SHA256 = 'f37072fd47e89c5e827621c5baffa7500819f7896bbacec160b1a16c560e07ec'


@dataclass
class MDGConfig:
    vit_dim: int
    lm_dim: int = 4096
    dim: int = 512
    n_taps: int = 3
    n_vit: int = 3
    blocks: int = 4
    heads: int = 8
    mlp: int = 2048
    pixel_dim: int = 64
    phrase_max: int = 8
    max_frames: int = 32
    stem_pretrained: bool = True
    stem_weights: str = STEM_WEIGHTS
    geo_dim: int = 0
    points: int = 12544
    oversample: float = 3.0
    importance: float = .75
    w_bce: float = 2.0
    w_dice: float = .5
    w_frame: float = 1.0
    w_clip: float = .5
    w_iou: float = .1
    w_deep: float = .5
    focal_gamma: float = 2.0
    presence_prior: float = .3

    def __post_init__(self):
        for name in ('vit_dim', 'lm_dim', 'dim', 'n_taps', 'n_vit', 'blocks', 'heads',
                     'mlp', 'pixel_dim', 'phrase_max', 'max_frames', 'points'):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise ValueError('Invalid MDG configuration: ' + name)
        if self.dim % self.heads or self.dim % 4:
            raise ValueError('MDG dim must be divisible by heads and four')
        if type(self.geo_dim) is not int or self.geo_dim < 0 or type(self.stem_pretrained) is not bool:
            raise ValueError('Invalid MDG geometry or stem setting')
        if not isinstance(self.stem_weights, str) or not self.stem_weights:
            raise ValueError('MDG stem_weights must name a local file')
        for name in ('oversample', 'importance', 'w_bce', 'w_dice', 'w_frame', 'w_clip',
                     'w_iou', 'w_deep', 'focal_gamma', 'presence_prior'):
            value = getattr(self, name)
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError('Invalid MDG configuration: ' + name)
        if self.oversample < 1 or self.importance > 1 or not 0 < self.presence_prior < 1:
            raise ValueError('Invalid MDG sampling or presence prior')


def _sincos(position, dim):
    scale = 10000 ** (-torch.arange(dim // 2, device=position.device, dtype=torch.float32) * 2 / dim)
    angle = position.float()[..., None] * scale
    return torch.cat((angle.sin(), angle.cos()), -1)


def _allowed_mask(logits, size):
    q, frames = logits.shape[:2]
    allowed = F.interpolate(logits.detach().reshape(q * frames, 1, *logits.shape[-2:]),
                            size=size, mode='bilinear', align_corners=False).reshape(q, frames, -1) > 0
    return allowed | ~allowed.any(-1, keepdim=True)


class _DecoderBlock(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        attn_cfg = SimpleNamespace(dim=cfg.dim, heads=cfg.heads, dropout=0.)
        self.self_attn, self.cross_attn = _Attention(attn_cfg), _Attention(attn_cfg)
        self.self_norm, self.cross_norm = nn.LayerNorm(cfg.dim), nn.LayerNorm(cfg.dim)
        self.memory_norm, self.mlp_norm = nn.LayerNorm(cfg.dim), nn.LayerNorm(cfg.dim)
        self.mlp = nn.Sequential(nn.Linear(cfg.dim, cfg.mlp), nn.GELU(), nn.Linear(cfg.mlp, cfg.dim))

    def forward(self, tokens, memory, phrase_mask, allowed):
        labels, frames, dim = tokens.shape[0], memory.shape[0], memory.shape[-1]
        keep = torch.cat((torch.ones(labels, frames + 1, device=tokens.device, dtype=torch.bool), phrase_mask), 1)
        norm = self.self_norm(tokens)
        tokens = tokens + self.self_attn(norm, norm, keep[:, None, None, :])
        attn, heads = self.cross_attn, self.cross_attn.heads
        cells, width = memory.shape[1], dim // heads
        context = self.memory_norm(memory)
        key = attn.k(context).reshape(frames, cells, heads, width).permute(0, 2, 1, 3)
        value = attn.v(context).reshape(frames, cells, heads, width).permute(0, 2, 1, 3)
        query = attn.q(self.cross_norm(tokens[:, :frames + 1]))
        frame_query = query[:, 1:].reshape(labels, frames, heads, width).permute(1, 2, 0, 3)
        frame = F.scaled_dot_product_attention(frame_query, key, value,
                                               attn_mask=allowed.permute(1, 0, 2)[:, None])
        frame = frame.permute(2, 0, 1, 3).reshape(labels, frames, dim)
        global_query = query[:, :1].reshape(labels, heads, width).transpose(0, 1)[None]
        global_key = key.permute(1, 0, 2, 3).reshape(1, heads, frames * cells, width)
        global_value = value.permute(1, 0, 2, 3).reshape(1, heads, frames * cells, width)
        global_token = F.scaled_dot_product_attention(global_query, global_key, global_value)
        global_token = global_token[0].transpose(0, 1).reshape(labels, 1, dim)
        updated = tokens[:, :frames + 1] + attn.proj(torch.cat((global_token, frame), 1))
        tokens = torch.cat((updated, tokens[:, frames + 1:]), 1)
        return tokens + self.mlp(self.mlp_norm(tokens))


class _Stem(nn.Module):
    def __init__(self, cfg, load_pretrained):
        super().__init__()
        from torchvision.models import resnet18
        base = resnet18(weights=None)
        if cfg.stem_pretrained and load_pretrained and base.conv1.weight.device.type != 'meta':
            path = Path(cfg.stem_weights)
            with path.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            if digest != STEM_SHA256:
                raise ValueError('ResNet-18 stem weight hash mismatch')
            base.load_state_dict(torch.load(path, map_location='cpu', weights_only=True), strict=True)
        self.conv1, self.bn1, self.relu, self.maxpool = base.conv1, base.bn1, base.relu, base.maxpool
        self.layer1, self.layer2 = base.layer1, base.layer2
        self.register_buffer('mean', torch.tensor([.485, .456, .406])[None, :, None, None])
        self.register_buffer('std', torch.tensor([.229, .224, .225])[None, :, None, None])

    def forward(self, pixels):
        x = self.maxpool(self.relu(self.bn1(self.conv1((pixels - self.mean) / self.std))))
        s4 = self.layer1(x)
        return s4, self.layer2(s4)


def _conv(dim):
    return nn.Sequential(nn.Conv2d(dim, dim, 3, padding=1), nn.GroupNorm(math.gcd(32, dim), dim), nn.GELU())


def _prediction_mlp(dim, out):
    return nn.Sequential(nn.Linear(dim, dim), nn.GELU(), nn.Linear(dim, out))


class MaskGroundingHead(nn.Module):
    def __init__(self, cfg: MDGConfig, *, _load_pretrained=True):
        super().__init__()
        self.cfg = cfg
        d = cfg.dim
        self.tap_mix = nn.Parameter(torch.zeros(cfg.n_taps))
        self.video_norm, self.video_proj = nn.LayerNorm(cfg.lm_dim), nn.Linear(cfg.lm_dim, d)
        self.vit_proj = nn.ModuleList([nn.Sequential(nn.LayerNorm(cfg.vit_dim), nn.Linear(cfg.vit_dim, d))
                                       for _ in range(cfg.n_vit)])
        self.memory_fuse = nn.Conv2d(d, d, 3, padding=1)
        self.frame_embed = nn.Parameter(torch.empty(cfg.max_frames, d))
        self.global_embed = nn.Parameter(torch.empty(d))
        if cfg.geo_dim:
            self.geo_norm, self.geo_proj = nn.LayerNorm(cfg.geo_dim), nn.Linear(cfg.geo_dim, d)
            nn.init.zeros_(self.geo_proj.weight)
            nn.init.zeros_(self.geo_proj.bias)
        self.stem = _Stem(cfg, _load_pretrained)
        self.s8_proj, self.s4_proj = nn.Conv2d(128, d, 1), nn.Conv2d(64, d, 1)
        self.pixel_s8, self.pixel_s4 = _conv(d), _conv(d)
        self.pixel_proj = nn.Conv2d(d, cfg.pixel_dim, 1)
        self.query_proj = nn.Sequential(nn.Linear(2 * cfg.lm_dim, 1024), nn.GELU(), nn.Linear(1024, d))
        self.phrase_proj = nn.Linear(2 * cfg.lm_dim, d)
        self.blocks = nn.ModuleList([_DecoderBlock(cfg) for _ in range(cfg.blocks)])
        self.frame_head, self.clip_head = _prediction_mlp(d, 1), _prediction_mlp(d, 1)
        self.mask_head, self.iou_head = _prediction_mlp(d, cfg.pixel_dim), _prediction_mlp(d, 1)
        nn.init.constant_(self.clip_head[-1].bias, math.log(cfg.presence_prior / (1 - cfg.presence_prior)))
        nn.init.normal_(self.frame_embed, std=.02)
        nn.init.normal_(self.global_embed, std=.02)

    def encode_video(self, taps, vit, pixels, grid, geo=None):
        if len(grid) != 2 or any(type(x) is not int or x < 1 for x in grid):
            raise ValueError('Expected positive (gh, gw) grid')
        gh, gw = grid
        if len(taps) != self.cfg.n_taps or taps[0].ndim != 3:
            raise ValueError('Expected n_taps tensors [F, gh*gw, lm_dim]')
        frames = taps[0].shape[0]
        if not 1 <= frames <= self.cfg.max_frames:
            raise ValueError('Unsupported frame count')
        if any(t.shape != (frames, gh * gw, self.cfg.lm_dim) for t in taps):
            raise ValueError('LM features do not match grid')
        if len(vit) != self.cfg.n_vit or any(v.shape != (frames, 2 * gh, 2 * gw, self.cfg.vit_dim) for v in vit):
            raise ValueError('ViT features do not match grid')
        if pixels.shape != (frames, 3, 32 * gh, 32 * gw):
            raise ValueError('RGB pixels do not match grid')
        if geo is not None and self.cfg.geo_dim and geo.shape != (frames, 2 * gh, 2 * gw, self.cfg.geo_dim):
            raise ValueError('Geometry does not match grid')
        with torch.autocast(device_type=pixels.device.type, enabled=False):
            mixed = sum(w * t.detach().float() for w, t in zip(self.tap_mix.softmax(0), taps))
            lm = self.video_proj(self.video_norm(mixed)).transpose(1, 2).reshape(frames, self.cfg.dim, gh, gw)
            lm = F.interpolate(lm, size=(2 * gh, 2 * gw), mode='bilinear', align_corners=False)
            vision = sum(proj(v.detach().float()) for proj, v in zip(self.vit_proj, vit)).permute(0, 3, 1, 2)
            memory = self.memory_fuse(lm + vision).flatten(2).transpose(1, 2)
            y, x = torch.meshgrid(torch.arange(2 * gh, device=pixels.device) / (2 * gh),
                                  torch.arange(2 * gw, device=pixels.device) / (2 * gw), indexing='ij')
            position = torch.cat((_sincos(y * (2 * math.pi), self.cfg.dim // 2),
                                  _sincos(x * (2 * math.pi), self.cfg.dim // 2)), -1).reshape(-1, self.cfg.dim)
            frame = self.frame_embed[:frames] + _sincos(torch.arange(frames, device=pixels.device) / frames * (2 * math.pi), self.cfg.dim)
            memory = memory + position[None] + frame[:, None]
            if self.cfg.geo_dim:
                geometry = (geo.detach().float() if geo is not None else
                            memory.new_zeros(frames, 2 * gh, 2 * gw, self.cfg.geo_dim))
                stream = self.geo_proj(self.geo_norm(geometry)).reshape_as(memory)
                memory = memory + (stream if geo is not None else stream * 0.)
            s4, s8 = self.stem(pixels.detach().float())
            pixel = memory.transpose(1, 2).reshape(frames, self.cfg.dim, 2 * gh, 2 * gw)
            pixel = self.pixel_s8(F.interpolate(pixel, size=s8.shape[-2:], mode='bilinear', align_corners=False) + self.s8_proj(s8))
            pixel = self.pixel_s4(F.interpolate(pixel, size=s4.shape[-2:], mode='bilinear', align_corners=False) + self.s4_proj(s4))
            return dict(memory=memory, pixel=self.pixel_proj(pixel), frame=frame, grid=tuple(grid))

    def _predict(self, tokens, video):
        frames = video['memory'].shape[0]
        frame = tokens[:, 1:frames + 1]
        return dict(frame_logit=self.frame_head(frame).squeeze(-1),
                    clip_logit=self.clip_head(tokens[:, 0]).squeeze(-1),
                    mask_logit=torch.einsum('qfc,fchw->qfhw', self.mask_head(frame), video['pixel']),
                    iou=self.iou_head(frame).squeeze(-1).sigmoid())

    def forward(self, video, query, phrase, phrase_mask, *, train_suffix=False):
        labels, frames = query.shape[0], video['memory'].shape[0]
        if query.shape != (labels, 2, self.cfg.lm_dim) or labels < 1:
            raise ValueError('Expected query [Q, 2, lm_dim]')
        if (phrase.shape != (labels, self.cfg.phrase_max, 2, self.cfg.lm_dim)
                or phrase_mask.shape != phrase.shape[:2] or phrase_mask.dtype != torch.bool):
            raise ValueError('Expected phrase [Q, phrase_max, 2, lm_dim] and boolean mask')
        with torch.autocast(device_type=query.device.type, enabled=False):
            if not train_suffix:
                query, phrase = query.detach(), phrase.detach()
            query = self.query_proj(query.float().flatten(1))
            phrase = phrase.float().masked_fill(~phrase_mask[..., None, None], 0.)
            tokens = torch.cat(((query + self.global_embed)[:, None], query[:, None] + video['frame'][None],
                                self.phrase_proj(phrase.flatten(2))), 1)
            previous = self._predict(tokens, video)
            outs = []
            for block in self.blocks:
                allowed = _allowed_mask(previous['mask_logit'], tuple(2 * k for k in video['grid']))
                tokens = block(tokens, video['memory'], phrase_mask, allowed)
                previous = self._predict(tokens, video)
                outs.append(previous)
            return outs

    def loss(self, outs, targets):
        if len(outs) != self.cfg.blocks:
            raise ValueError('Expected one prediction per decoder block')
        with torch.autocast(device_type=outs[-1]['mask_logit'].device.type, enabled=False):
            return self._loss(outs, targets)

    def _loss(self, outs, targets):
        device = outs[-1]['mask_logit'].device
        presence = targets['frame_presence'].to(device=device, dtype=torch.float32)
        clip_target = targets['clip_present'].to(device=device, dtype=torch.float32)
        frame_valid = (targets['frame_valid'].to(device=device, dtype=torch.bool)
                       & torch.isfinite(presence) & (clip_target[:, None] == 1))
        mask_valid = targets['mask_valid'].to(device=device, dtype=torch.bool)
        masks = targets['masks'].to(device=device)[mask_valid].float()[:, None]
        parts = {}
        for index, out in enumerate(outs):
            logits, heat = out['frame_logit'].float(), out['mask_logit'].float()
            zero = sum(v.flatten()[:0].sum() for v in out.values())
            bce = dice = iou = zero
            if mask_valid.any():
                selected = heat[mask_valid][:, None]
                points = _sample_points(selected, self.cfg.points, self.cfg.oversample, self.cfg.importance)
                pred = _at_points(selected, points)
                truth = _at_points(masks, points, mode='nearest')
                bce = F.binary_cross_entropy_with_logits(pred, truth)
                probability = pred.sigmoid()
                dice = (1 - (2 * (probability * truth).sum(-1) + 1) /
                        (probability.sum(-1) + truth.sum(-1) + 1)).mean()
                with torch.no_grad():
                    target_mask = F.interpolate(masks, size=heat.shape[-2:], mode='nearest')[:, 0] > .5
                    prediction = selected[:, 0] > 0
                    union = (prediction | target_mask).sum((-1, -2))
                    true_iou = (prediction & target_mask).sum((-1, -2)) / union.clamp_min(1)
                iou = F.mse_loss(out['iou'][mask_valid].float(), true_iou)
            safe_presence = presence.nan_to_num()
            focal = F.binary_cross_entropy_with_logits(logits, safe_presence, reduction='none')
            pt = torch.where(safe_presence == 1, logits.sigmoid(), (-logits).sigmoid())
            focal = focal * (1 - pt).pow(self.cfg.focal_gamma)
            pos, neg = frame_valid & (presence == 1), frame_valid & (presence == 0)
            frame = .5 * ((focal[pos].mean() if pos.any() else zero) + (focal[neg].mean() if neg.any() else zero))
            clip = F.binary_cross_entropy_with_logits(out['clip_logit'].float(), clip_target)
            weight = 1 if index == len(outs) - 1 else self.cfg.w_deep
            for name, value in dict(bce=bce, dice=dice, frame=frame, clip=clip, iou=iou).items():
                parts[name] = parts.get(name, zero) + weight * value
        parts['total'] = sum(getattr(self.cfg, 'w_' + name) * value for name, value in parts.items())
        return parts

    @staticmethod
    @torch.no_grad()
    def decode(out, tau=None):
        heat = out['mask_logit'].detach().float()
        mask = heat > 0
        prob = out['clip_logit'].float().sigmoid()[:, None] * out['frame_logit'].float().sigmoid()
        uv = _decode_points(heat.cpu().numpy())
        decoded = dict(prob=prob, mask=mask, uv=torch.as_tensor(uv, device=heat.device),
                       iou=out['iou'], area=mask.sum((-1, -2)))
        if tau is not None:
            if not math.isfinite(tau) or not 0 <= tau <= 1:
                raise ValueError('Invalid MDG tau')
            decoded['present'] = prob >= tau
        return decoded


def _at_points(masks, points, mode='bilinear'):
    return F.grid_sample(masks, points[:, :, None] * 2 - 1, mode=mode,
                         align_corners=False)[:, 0, :, 0]


@torch.no_grad()
def _sample_points(logits, points, oversample, importance):
    batch = logits.shape[0]
    count, selected = int(points * oversample), int(points * importance)
    candidates = torch.rand(batch, count, 2, device=logits.device)
    uncertainty = -_at_points(logits, candidates).abs()
    indices = uncertainty.topk(selected, dim=1).indices
    important = candidates.gather(1, indices[..., None].expand(-1, -1, 2))
    return torch.cat((important, torch.rand(batch, points - selected, 2, device=logits.device)), 1)


def _numpy_component(mask):
    height, width = mask.shape
    seen, best = np.zeros_like(mask), []
    for row, col in np.argwhere(mask):
        if seen[row, col]:
            continue
        pending, component = [(int(row), int(col))], []
        seen[row, col] = True
        while pending:
            y, x = pending.pop()
            component.append((y, x))
            for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= yy < height and 0 <= xx < width and mask[yy, xx] and not seen[yy, xx]:
                    seen[yy, xx] = True
                    pending.append((yy, xx))
        if len(component) > len(best):
            best = component
    result = np.zeros_like(mask)
    if best:
        rows, cols = np.asarray(best).T
        result[rows, cols] = True
    return result


def _decode_points(heat, *, scipy=True):
    ndimage = None
    if scipy:
        try:
            from scipy import ndimage
        except ImportError:
            pass
    height, width = heat.shape[-2:]
    points = []
    for logits in heat.reshape(-1, height, width):
        mask = logits > 0
        if ndimage is not None:
            components, count = ndimage.label(mask)
            sizes = np.bincount(components.ravel(), minlength=count + 1)
            sizes[0] = 0
            component = components == sizes.argmax() if count else np.zeros_like(mask)
        else:
            component = _numpy_component(mask)
        if component.sum() < 4:
            index = logits.argmax()
        else:
            padded = np.pad(component, 1)
            if ndimage is not None:
                distance = ndimage.distance_transform_edt(padded)[1:-1, 1:-1]
            else:
                cost = np.where(padded, np.inf, 0.)
                y, x = np.arange(height + 2), np.arange(width + 2)
                cost = (cost[:, None, :] + (y[:, None, None] - y[None, :, None]) ** 2).min(0)
                distance = (cost[:, :, None] + (x[None, :, None] - x[None, None, :]) ** 2).min(1)[1:-1, 1:-1]
            index = distance.argmax()
        row, col = divmod(int(index), width)
        points.append((round((col + .5) / width * 1000), round((row + .5) / height * 1000)))
    return np.clip(np.asarray(points, dtype=np.int64).reshape(*heat.shape[:-2], 2), 0, 1000)


def _validate_meta(meta):
    if not isinstance(meta, dict) or meta.get('schema') != 'mdg-head-v1':
        raise ValueError('Expected mdg-head-v1 artifact schema')
    try:
        cfg = MDGConfig(**meta['config'])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError('Invalid MDG artifact config') from exc
    gh_meta = dict(meta, schema='grounding-head-v1', config=dict(vit_dim=cfg.vit_dim))
    _validate_gh_meta(gh_meta)
    return cfg


def save_artifact(directory, head, meta):
    meta = dict(meta)
    if 'schema' in meta and meta['schema'] != 'mdg-head-v1':
        raise ValueError('Expected mdg-head-v1 artifact schema')
    if 'config' in meta and meta['config'] != asdict(head.cfg):
        raise ValueError('MDG artifact config differs from head')
    meta.update(schema='mdg-head-v1', config=asdict(head.cfg))
    _validate_meta(meta)
    payload = json.dumps(meta, indent=2, sort_keys=True, allow_nan=False) + '\n'
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if (directory / 'mdg.pt').exists() or (directory / 'mdg.json').exists():
        raise FileExistsError('MDG artifact already exists')
    with (directory / 'mdg.pt').open('xb') as stream:
        torch.save({name: value.detach().cpu() for name, value in head.state_dict().items()}, stream)
    with (directory / 'mdg.json').open('x') as stream:
        stream.write(payload)


def load_artifact(directory):
    directory = Path(directory)
    meta = json.loads((directory / 'mdg.json').read_text())
    cfg = _validate_meta(meta)
    from .mdg_lora import artifact_weights
    artifact_weights(directory, meta)
    head = MaskGroundingHead(cfg, _load_pretrained=False)
    head.load_state_dict(torch.load(directory / 'mdg.pt', map_location='cpu', weights_only=True), strict=True)
    return head.eval(), meta
