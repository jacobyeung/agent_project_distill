"""StubBackbone: a tiny causal transformer LM with the adapter contract (tests, toys)."""
import torch
from torch import nn
from torch.nn import functional as F

from .base import BackboneBase, inject_lora, left_pad


class _Layer(nn.Module):
    def __init__(self, d, heads):
        super().__init__()
        self.heads = heads
        self.n1, self.n2 = nn.LayerNorm(d), nn.LayerNorm(d)
        self.qkv, self.proj = nn.Linear(d, 3 * d), nn.Linear(d, d)
        self.fc1, self.fc2 = nn.Linear(d, 4 * d), nn.Linear(4 * d, d)

    def forward(self, x, allow):
        b, t, d = x.shape
        q, k, v = (y.reshape(b, t, self.heads, -1).transpose(1, 2) for y in self.qkv(self.n1(x)).chunk(3, -1))
        y = F.scaled_dot_product_attention(q, k, v, attn_mask=allow[:, None])
        x = x + self.proj(y.transpose(1, 2).reshape(b, t, d))
        return x + self.fc2(F.gelu(self.fc1(self.n2(x))))


class StubBackbone(BackboneBase):
    """batch: input_ids [B, T], attention_mask [B, T] (any contiguous padding)."""

    LORA_TARGETS = ['qkv', 'proj', 'fc1', 'fc2']

    def __init__(self, vocab=64, hidden=32, layers=2, heads=4, max_len=512, taps=(-1,), tap_norm=False):
        super().__init__()
        self.hidden_size, self.vocab_size, self.n_layers = hidden, vocab, layers
        self.taps, self.tap_norm = self.resolve_taps(taps), tap_norm
        self.embed = nn.Embedding(vocab, hidden)
        self.pos = nn.Embedding(max_len, hidden)
        self.layers = nn.ModuleList([_Layer(hidden, heads) for _ in range(layers)])
        self.norm = nn.LayerNorm(hidden)
        self.lm_head = nn.Linear(hidden, vocab, bias=False)

    @classmethod
    def for_config(cls, cfg, vocab=64, layers=2, heads=4):
        return cls(vocab=vocab, hidden=cfg.hidden_size, layers=layers, heads=heads, taps=cfg.taps, tap_norm=cfg.tap_norm)

    def input_module(self):
        return self.embed

    def output_module(self):
        return self.lm_head

    def encode(self, batch, ext=None):
        ids = batch['input_ids']
        mask = batch.get('attention_mask')
        mask = torch.ones_like(ids, dtype=torch.bool) if mask is None else mask.bool()
        mask, ids = left_pad(mask, ids)
        x = self.embed_ids(ids)
        if ext is not None:
            x = torch.cat([x, ext.to(x.dtype)], 1)
            mask = torch.cat([mask, torch.ones(ext.shape[:2], dtype=torch.bool, device=mask.device)], 1)
        s = x.shape[1]
        x = x + self.pos((mask.long().cumsum(1) - 1).clamp(min=0))
        causal = torch.ones(s, s, dtype=torch.bool, device=x.device).tril()
        allow = causal[None] & (mask[:, None, :] | torch.eye(s, dtype=torch.bool, device=x.device)[None])
        out = {}
        for i, layer in enumerate(self.layers, 1):
            x = layer(x, allow)
            if i in self.taps:
                out[i] = self.norm(x) if (i == self.n_layers or self.tap_norm) else x
        return torch.stack([out[t] for t in self.taps]), mask

    def lm_parameters(self):
        return [p for n, p in self.named_parameters() if not n.startswith('extra_')]

    def set_trainable(self, cfg):
        for p in self.lm_parameters():
            p.requires_grad_(cfg.train_mode == 'full')
        if cfg.train_mode == 'lora':
            inject_lora(self, cfg, self.LORA_TARGETS)
        self._unfreeze_extra()
