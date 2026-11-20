"""Stage-1 selector head: scores one name's SAM 3 candidates from tower tensors and the name as written.

    logits = SelectorHead(cfg)(x [N, F_IN], name_emb [D_NAME] | None, name=str, mask_tokens=None, vit_feats=None)
    slots = head.with_null(...)   # [N + 1]: the N candidates' logits and a null logit ("no candidate is the object")

x is selector_inputs.candidate_vectors (fixed math on SAM 3 proposals and the scaled G3T geometry). The name enters
as the frozen SAM 3 text encoder's pooled embedding (name_mode 'sam3'), as a learned character-trigram hashing
embedding whose table is a parameter of this head ('trigram'), or not at all ('none'). Set context is a DeepSets
mean and max over the name's candidates. Sockets: `mask_tokens` [N, D_MASK] (SAM 3 mask tokens) and `vit_feats`
[N, D_VIT] (own-ViT features pooled in the mask) enter through zero-initialised projections, so a head trained
without them answers identically when they are zeros. No alias table: the only normalization is lowercase+strip.
"""
import hashlib, json
from pathlib import Path
import torch
from torch import nn

F_IN = 58
D_NAME = 256
D_MASK = 256
D_VIT = 1024


def name_key(name):
    return str(name).strip().lower()


def trigram_ids(name, n_hash):
    s = '#' + name_key(name) + '#'
    grams = [s[i:i + 3] for i in range(max(len(s) - 2, 1))]
    return [int.from_bytes(hashlib.md5(g.encode()).digest()[:4], 'little') % n_hash for g in grams]


class SelectorHead(nn.Module):
    def __init__(self, hidden=64, name_mode='sam3', n_hash=4096, f_in=F_IN):
        super().__init__()
        self.cfg = dict(hidden=hidden, name_mode=name_mode, n_hash=n_hash, f_in=f_in)
        self.register_buffer('feat_mean', torch.zeros(f_in, dtype=torch.float64))
        self.register_buffer('feat_std', torch.ones(f_in, dtype=torch.float64))
        self.phi = nn.Sequential(nn.Linear(f_in, hidden), nn.GELU(), nn.Linear(hidden, hidden), nn.GELU())
        if name_mode == 'sam3':
            self.name = nn.Linear(D_NAME, hidden)
        elif name_mode == 'trigram':
            self.name = nn.EmbeddingBag(n_hash, hidden, mode='mean')
        self.mask_proj = nn.Linear(D_MASK, hidden)
        self.vit_proj = nn.Linear(D_VIT, hidden)
        for m in (self.mask_proj, self.vit_proj):
            nn.init.zeros_(m.weight); nn.init.zeros_(m.bias)
        self.out = nn.Sequential(nn.Linear(4 * hidden, hidden), nn.GELU(), nn.Linear(hidden, 1))
        self.null = nn.Sequential(nn.Linear(3 * hidden, hidden), nn.GELU(), nn.Linear(hidden, 1))

    def name_vector(self, name_emb, name):
        h = self.cfg['hidden']
        if self.cfg['name_mode'] == 'sam3':
            return self.name(name_emb.float())
        if self.cfg['name_mode'] == 'trigram':
            ids = torch.tensor([trigram_ids(name, self.cfg['n_hash'])])
            return self.name(ids)[0]
        return torch.zeros(h)

    def both(self, x, name_emb=None, name=None, mask_tokens=None, vit_feats=None):
        z = ((x.double() - self.feat_mean) / self.feat_std).float()
        h = self.phi(z)
        if mask_tokens is not None:
            h = h + self.mask_proj(mask_tokens.float())
        if vit_feats is not None:
            h = h + self.vit_proj(vit_feats.float())
        n = h.shape[0]
        ctx = torch.cat([h.mean(0), h.max(0).values, self.name_vector(name_emb, name)])
        return self.out(torch.cat([h, ctx.expand(n, -1)], 1))[:, 0], self.null(ctx)

    def forward(self, x, name_emb=None, name=None, mask_tokens=None, vit_feats=None):
        return self.both(x, name_emb, name, mask_tokens, vit_feats)[0]

    def with_null(self, x, name_emb=None, name=None, mask_tokens=None, vit_feats=None):
        logits, null = self.both(x, name_emb, name, mask_tokens, vit_feats)
        return torch.cat([logits, null])


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_head(directory, expected_sha256=None):
    """Load selector_head.safetensors + selector_head.json; refuse on a sha256 mismatch."""
    from safetensors.torch import load_file
    d = Path(directory)
    meta = json.loads((d / 'selector_head.json').read_text())
    weights = d / 'selector_head.safetensors'
    expected = expected_sha256 or meta['weights_sha256']
    actual = file_sha256(weights)
    if actual != expected:
        raise ValueError(f'selector head sha256 mismatch: expected {expected}, got {actual}')
    head = SelectorHead(**{k: meta['config'][k] for k in ('hidden', 'name_mode', 'n_hash')})
    head.load_state_dict(load_file(str(weights)))
    return head.eval(), meta
