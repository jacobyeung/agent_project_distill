"""Name-conditioned frame presence, instance decoding, and listwise selection."""
from dataclasses import asdict, dataclass, field
import math

import torch
from torch import nn
from torch.nn import functional as F

from .common import sha256_file, sha256_json

STEM_SHA256 = 'f37072fd47e89c5e827621c5baffa7500819f7896bbacec160b1a16c560e07ec'
STEM_PATH = '/scratch/jjyeung/orch_n30/b05_owngrd/work/from118/weights/resnet18-f37072fd.pth'


@dataclass
class Config:
    vit_dim: int = 1152
    name_dim: int = 4096
    dim: int = 640
    heads: int = 8
    blocks: int = 4
    ffn: int = 2560
    query_hidden: int = 2048
    pixel_dim: int = 128
    presence_dim: int = 256
    selector_dim: int = 384
    selector_query_dim: int = 256
    queries: int = 16
    identity_dim: int = 128
    stem_weights: str = STEM_PATH
    pretrained_stem: bool = True
    tiny_stem: bool = False
    cosine_threshold: float = .7
    score_floor: float = .2
    max_candidates: int = 5
    points: int = 12544
    oversample: float = 3.
    importance: float = .75
    identity_temperature: float = .1
    selection_smoothing: float = .1
    weights: dict = field(default_factory=lambda: dict(mask_focal=2., mask_dice=.5, match=1.,
        presence=1., clip=.5, box_l1=1., box_giou=1., identity=.5, selection=1., distill=.5, iou=.1))

    def __post_init__(self):
        for k in ('vit_dim', 'name_dim', 'dim', 'heads', 'blocks', 'ffn', 'queries', 'points',
                  'pixel_dim', 'presence_dim', 'selector_dim', 'identity_dim', 'query_hidden', 'selector_query_dim'):
            if type(getattr(self, k)) is not int or getattr(self, k) < 1:
                raise ValueError('Invalid positive integer: ' + k)
        if any(d % self.heads for d in (self.dim, self.presence_dim, self.selector_dim)):
            raise ValueError('Attention dimensions must divide into heads')
        if not 1 <= self.max_candidates <= 5 or not -1 <= self.cosine_threshold <= 1:
            raise ValueError('Invalid clustering configuration')
        if not 0 <= self.score_floor <= 1 or not 0 <= self.importance <= 1 or self.oversample < 1:
            raise ValueError('Invalid sampling configuration')
        if self.identity_temperature <= 0 or not 0 <= self.selection_smoothing < 1:
            raise ValueError('Invalid loss configuration')
        required = {'mask_focal', 'mask_dice', 'match', 'presence', 'clip', 'box_l1',
                    'box_giou', 'identity', 'selection', 'distill', 'iou'}
        if set(self.weights) != required:
            raise ValueError('Provide the complete set of eleven loss weights')
        if any(not math.isfinite(v) or v < 0 for v in self.weights.values()):
            raise ValueError('Loss weights must be finite and nonnegative')

    @classmethod
    def tiny(cls):
        return cls(vit_dim=16, name_dim=24, dim=32, heads=4, blocks=2, ffn=64,
                   query_hidden=48, pixel_dim=16, presence_dim=16, selector_dim=16,
                   selector_query_dim=16, pretrained_stem=False, tiny_stem=True, points=64)

    @property
    def sha256(self):
        return sha256_json(asdict(self))


def pooled_name(tokens, mask):
    if not mask.any(-1).all():
        raise ValueError('Every name needs at least one token')
    return (tokens * mask[..., None]).sum(1) / mask.sum(1, keepdim=True)


class Attention(nn.Module):
    def __init__(self, dim, heads):
        super().__init__()
        self.heads = heads
        self.q, self.k, self.v, self.proj = (nn.Linear(dim, dim) for _ in range(4))

    def forward(self, query, context):
        b, n, d = query.shape
        def split(x):
            return x.reshape(b, -1, self.heads, d//self.heads).transpose(1, 2)
        out = F.scaled_dot_product_attention(split(self.q(query)), split(self.k(context)), split(self.v(context)))
        return self.proj(out.transpose(1, 2).reshape(b, n, d))


class Block(nn.Module):
    def __init__(self, dim, heads, ffn, cross=True):
        super().__init__()
        self.self_attn = Attention(dim, heads)
        self.norm1, self.norm2 = nn.LayerNorm(dim), nn.LayerNorm(dim)
        self.ff = nn.Sequential(nn.Linear(dim, ffn), nn.GELU(), nn.Linear(ffn, dim))
        self.cross = cross
        if cross:
            self.cross_attn = Attention(dim, heads)
            self.qnorm, self.mnorm = nn.LayerNorm(dim), nn.LayerNorm(dim)

    def forward(self, x, memory=None):
        norm = self.norm1(x)
        x = x + self.self_attn(norm, norm)
        if self.cross:
            x = x + self.cross_attn(self.qnorm(x), self.mnorm(memory))
        return x + self.ff(self.norm2(x))


def positions(h, w, slots, total_frames, device):
    yy, xx = torch.meshgrid(torch.linspace(-1, 1, h, device=device),
                           torch.linspace(-1, 1, w, device=device), indexing='ij')
    tt = slots.float() / max(total_frames-1, 1) * 2 - 1
    return torch.stack((xx.expand(len(slots), -1, -1), yy.expand(len(slots), -1, -1),
                        tt[:, None, None].expand(-1, h, w)), -1)


class PresenceHead(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        d = cfg.presence_dim
        self.vision_norm, self.name_norm = nn.LayerNorm(cfg.vit_dim), nn.LayerNorm(cfg.name_dim)
        self.vision, self.name = nn.Linear(cfg.vit_dim, d), nn.Linear(cfg.name_dim, d)
        self.pool_q, self.pool_k = nn.Linear(d, d), nn.Linear(d, d)
        self.position = nn.Linear(1, d)
        self.temporal = Block(d, cfg.heads, 4*d, cross=False)
        self.frame, self.clip = nn.Linear(d, 1), nn.Linear(d, 1)

    def forward(self, merged, name):
        # Name-conditioned attention pooling over each frame's merged tokens (design 1.4: the head reads the
        # tokens, so small objects are not averaged away), plus the frame mean as context.
        frames = merged.shape[0]
        v = self.vision(self.vision_norm(merged.flatten(1, 2).float()))
        q = self.name(self.name_norm(name.float()))
        att = torch.einsum('nd,tld->ntl', self.pool_q(q), self.pool_k(v)) / math.sqrt(v.shape[-1])
        pooled = torch.einsum('ntl,tld->ntd', att.softmax(-1), v)
        x = pooled + v.mean(1)[None] + q[:, None]
        t = torch.linspace(-1, 1, frames, device=x.device)[:, None]
        x = self.temporal(x + self.position(t)[None])
        return self.frame(x).squeeze(-1), self.clip(x.mean(1)).squeeze(-1)

    @staticmethod
    def shortlist(logits, k=4, separation=2, slots=None):
        if logits.ndim == 1:
            logits = logits[None]
        slots = list(range(logits.shape[1])) if slots is None else list(slots)
        result = []
        for row in logits.detach():
            kept = []
            for i in torch.argsort(row, descending=True, stable=True).tolist():
                if all(abs(slots[i]-slots[j]) >= separation for j in kept):
                    kept.append(i)
                if len(kept) == k:
                    break
            result.append(kept)
        return result


class Stem(nn.Module):
    def __init__(self, cfg, load_pretrained):
        super().__init__()
        if cfg.tiny_stem:
            self.s4 = nn.Sequential(nn.Conv2d(3, 16, 3, 2, 1), nn.GELU(), nn.Conv2d(16, 64, 3, 2, 1), nn.GELU())
            self.s8 = nn.Sequential(nn.Conv2d(64, 128, 3, 2, 1), nn.GELU())
        else:
            from torchvision.models import resnet18
            base = resnet18(weights=None)
            if cfg.pretrained_stem and load_pretrained:
                if sha256_file(cfg.stem_weights) != STEM_SHA256:
                    raise ValueError('ResNet18 checksum mismatch')
                base.load_state_dict(torch.load(cfg.stem_weights, map_location='cpu', weights_only=True), strict=True)
            self.s4 = nn.Sequential(base.conv1, base.bn1, base.relu, base.maxpool, base.layer1)
            self.s8 = base.layer2
        self.register_buffer('mean', torch.tensor([.485, .456, .406])[None, :, None, None])
        self.register_buffer('std', torch.tensor([.229, .224, .225])[None, :, None, None])

    def forward(self, pixels):
        x = self.s4((pixels-self.mean)/self.std)
        return x, self.s8(x)


def mlp(dim, out):
    return nn.Sequential(nn.Linear(dim, dim), nn.GELU(), nn.Linear(dim, out))


class Decoder(nn.Module):
    def __init__(self, cfg, load_pretrained=True):
        super().__init__()
        self.cfg = cfg
        d, p = cfg.dim, cfg.pixel_dim
        self.tap_mix = nn.Parameter(torch.zeros(4))
        self.taps = nn.ModuleList([nn.Sequential(nn.LayerNorm(cfg.vit_dim), nn.Linear(cfg.vit_dim, d)) for _ in range(4)])
        self.stem = Stem(cfg, load_pretrained)
        self.stem_memory = nn.Conv2d(128, d, 1)
        self.memory_fuse = nn.Conv2d(d, d, 3, padding=1)
        self.position = nn.Linear(3, d)
        self.pixel_tap, self.pixel_s4, self.pixel_s8 = nn.Conv2d(d, p, 1), nn.Conv2d(64, p, 1), nn.Conv2d(128, p, 1)
        self.pixel_fuse = nn.Sequential(nn.Conv2d(p, p, 3, padding=1), nn.GroupNorm(math.gcd(p, 16), p), nn.GELU())
        self.name = nn.Sequential(nn.Linear(cfg.name_dim, cfg.query_hidden), nn.GELU(), nn.Linear(cfg.query_hidden, d))
        self.query = nn.Parameter(torch.randn(cfg.queries+1, d) * .02)
        self.blocks = nn.ModuleList([Block(d, cfg.heads, cfg.ffn) for _ in range(cfg.blocks)])
        self.match, self.mask, self.box = mlp(d, 1), mlp(d, p), mlp(d, 4)
        self.iou, self.identity, self.presence = mlp(d, 1), nn.Linear(d, cfg.identity_dim), nn.Linear(d, 1)

    def forward(self, taps, pixels, name, frame_ids, total_frames):
        if len(taps) != 4 or any(t.shape != taps[0].shape for t in taps):
            raise ValueError('Four equally shaped tap maps required')
        nf, h, w, _ = taps[0].shape
        n = len(name)
        mixed = sum(weight*proj(t.float()) for weight, proj, t in zip(self.tap_mix.softmax(0), self.taps, taps))
        s4, s8 = self.stem(pixels)
        memory = mixed.permute(0, 3, 1, 2) + F.interpolate(self.stem_memory(s8), (h, w), mode='area')
        memory = self.memory_fuse(memory)
        pixel = self.pixel_fuse(self.pixel_s4(s4) + F.interpolate(self.pixel_s8(s8), s4.shape[-2:], mode='bilinear', align_corners=False)
                                + F.interpolate(self.pixel_tap(memory), s4.shape[-2:], mode='bilinear', align_corners=False))
        pos = self.position(positions(h, w, frame_ids, total_frames, memory.device))
        memory = (memory.permute(0, 2, 3, 1)+pos).reshape(nf, h*w, -1)
        x = self.name(name)[:, None, None] + self.query[None, None]
        x = x.expand(n, nf, -1, -1).reshape(n*nf, self.cfg.queries+1, -1)
        memory = memory[None].expand(n, -1, -1, -1).reshape(n*nf, h*w, -1)
        for block in self.blocks:
            x = block(x, memory)
        x = x.reshape(n, nf, self.cfg.queries+1, -1)
        query, presence = x[:, :, :-1], self.presence(x[:, :, -1]).squeeze(-1)
        match = self.match(query).squeeze(-1)
        return dict(match=match, masks=torch.einsum('nfqp,fphw->nfqhw', self.mask(query), pixel),
                    boxes=self.box(query).sigmoid(), iou=self.iou(query).squeeze(-1).sigmoid(),
                    identity=F.normalize(self.identity(query), dim=-1), decoder_presence=presence,
                    scores=presence.sigmoid()[..., None]*match.sigmoid())


def cluster_candidates(scores, identity, presence, iou, threshold=.7, floor=.2, limit=5):
    """Greedy, score-ordered clusters; each cluster contains at most one query per frame."""
    eligible = (scores.detach() >= floor).nonzero().tolist()
    eligible.sort(key=lambda fq: (-float(scores[fq[0], fq[1]].detach()), fq[0], fq[1]))
    clusters = []
    for f, q in eligible:
        best, similarity = None, threshold
        for c in clusters:
            if any(ff == f for ff, _ in c):
                continue
            centroid = F.normalize(torch.stack([identity[ff, qq].detach() for ff, qq in c]).mean(0), dim=0)
            cosine = float((centroid*identity[f, q].detach()).sum())
            if cosine >= similarity:
                best, similarity = c, cosine
        if best is None:
            clusters.append([(f, q)])
        else:
            best.append((f, q))
    clusters.sort(key=lambda c: -max(float(scores[f, q].detach()) for f, q in c))
    clusters = clusters[:limit]
    features = []
    for c in clusters:
        s = torch.stack([scores[f, q] for f, q in c])
        emb = torch.stack([identity[f, q] for f, q in c])
        centroid = F.normalize(emb.mean(0), dim=0)
        features.append(torch.stack([s.max(), s.mean(), s.new_tensor(len(c)/len(scores)),
            torch.stack([presence[f].sigmoid() for f, _ in c]).mean(),
            torch.stack([iou[f, q] for f, q in c]).mean(), (emb*centroid).sum(-1).mean()]))
    return clusters, torch.stack(features) if features else scores.new_empty((0, 6))


class Selector(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        d = cfg.selector_dim
        self.features = nn.Linear(6, d)
        self.name = nn.Sequential(nn.Linear(cfg.name_dim, cfg.selector_query_dim), nn.GELU(), nn.Linear(cfg.selector_query_dim, d))
        self.none = nn.Parameter(torch.zeros(d))
        self.listwise = Block(d, cfg.heads, 4*d, cross=False)
        self.score = nn.Linear(d, 1)

    def forward(self, features, name):
        tokens = torch.cat((self.features(features), self.none[None]), 0) + self.name(name)[None]
        return self.score(self.listwise(tokens[None])[0]).squeeze(-1)


class GroundingHead(nn.Module):
    def __init__(self, cfg=None, load_pretrained=True):
        super().__init__()
        torch.set_num_threads(min(torch.get_num_threads(), 16))
        self.cfg = cfg or Config()
        self.presence = PresenceHead(self.cfg)
        self.decoder = Decoder(self.cfg, load_pretrained)
        self.selector = Selector(self.cfg)

    def forward(self, taps, merged, pixels, name_tokens, name_mask, frame_ids=None, selection_targets=None):
        name = pooled_name(name_tokens, name_mask)
        if frame_ids is None:
            frame_ids = torch.arange(len(taps[0]), device=pixels.device)
        frame_ids = torch.as_tensor(frame_ids, device=pixels.device, dtype=torch.long)
        if len(frame_ids) != len(pixels) or (frame_ids < 0).any() or (frame_ids >= len(merged)).any():
            raise ValueError('Decoder frame ids must index all-frame merged features')
        out = self.decoder(taps, pixels, name, frame_ids, len(merged))
        out['presence'], out['clip'] = self.presence(merged, name)
        out['frame_ids'] = frame_ids
        out['candidates'], out['selection'], out['selection_candidates'] = [], [], []
        for n in range(len(name)):
            c, features = cluster_candidates(out['scores'][n], out['identity'][n], out['decoder_presence'][n],
                out['iou'][n], self.cfg.cosine_threshold, self.cfg.score_floor, self.cfg.max_candidates)
            out['candidates'].append(c)
            selection_candidates = [dict(source='decoder', members=members, weight=1., native=False) for members in c]
            if selection_targets is not None:
                from .data import teacher_candidates
                from .losses import mask_iou
                # Alternate the extra slot between sources in the training RNG stream.
                teacher_slots = min(self.cfg.max_candidates, 2 + int(torch.randint(2, ()).item()))
                tc = teacher_candidates(selection_targets[n], teacher_slots)
                teacher_features = []
                for candidate in tc:
                    best = [(f, int(mask_iou(out['masks'][n, f].detach().sigmoid(), mask.to(pixels)).argmax()))
                            for f, mask in candidate['members']]
                    estimates = torch.stack([out['iou'][n, f, q] for f, q in best])
                    embeddings = torch.stack([out['identity'][n, f, q] for f, q in best])
                    centroid = F.normalize(embeddings.mean(0), dim=0)
                    feature = torch.cat((features.new_tensor(candidate['features'][:4]),
                        estimates.mean().reshape(1), (embeddings*centroid).sum(-1).mean().reshape(1)))
                    candidate['features'] = feature
                    teacher_features.append(feature)
                dc = min(len(c), self.cfg.max_candidates-len(tc))
                selection_candidates = selection_candidates[:dc] + tc
                features = torch.cat((features[:dc], torch.stack(teacher_features) if teacher_features
                                      else features.new_empty((0, 6))), 0)
            out['selection_candidates'].append(selection_candidates)
            out['selection'].append(self.selector(features, name[n]))
        return out

    def parameter_counts(self):
        counts = {name: sum(p.numel() for p in module.parameters() if p.requires_grad)
                  for name, module in self.named_children()}
        return {**counts, 'total': sum(counts.values())}
