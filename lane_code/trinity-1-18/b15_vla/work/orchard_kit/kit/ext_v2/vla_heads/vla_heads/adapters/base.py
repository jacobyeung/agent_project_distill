"""The backbone contract both adapters implement.

- `encode(batch, ext=None) -> (taps [n, B, S, D], mask [B, S])`: the configured taps over the
  left-padded context followed by `ext [B, E, D]` (appended embeddings; S = T + E). The adapter
  left-pads every row, so the appended block occupies the same last E columns of every row and
  follows each row's last real token directly. Taps follow schema 2: i in 1..L-1 reads decoder
  layer i's output before the final norm (transformers' `hidden_states[i]`), -1 the final layer
  after the final norm; 0 and L raise. `tap_norm` also applies the final norm to taps below L.
- `padded_ids(batch) -> [B, T]`: input ids in that left-padded layout (-1 at padding), so callers
  locate in-prompt tokens (the regression head's query tokens) in the tap states.
- `embed_ids(ids [B, L]) -> [B, L, D]`: input embeddings, including appended codec rows.
- `reserve_tokens(n, source) -> TokenBinding`: LM ids for n codec symbols. source 'append' adds n
  new embedding and output rows after the configured vocabulary (owned by the adapter, always
  trainable); a path loads a reserved-id JSON (`codecs.reserved`); a list uses those ids.
- `decoder(batch, ext)`: the stateful callable of interface.HeadInputs.
- `set_trainable(cfg)`: train_mode full | lora | frozen and train_vision.
"""
import torch
from torch import nn
from torch.nn import functional as F

from ..codecs.reserved import load_ids


def left_pad(mask, *tensors):
    """Move each row's valid (contiguous) tokens to the right end. mask [B, T] -> rolled copies."""
    mask = mask.bool()
    lengths = mask.sum(1)
    first = mask.float().argmax(1)
    t = mask.shape[1]
    shift = (t - lengths - first) % t
    idx = (torch.arange(t, device=mask.device)[None] - shift[:, None]) % t
    rolled = [mask.gather(1, idx)] + [x.gather(1, idx) for x in tensors]
    if not torch.equal(rolled[0], torch.arange(t, device=mask.device)[None] >= (t - lengths)[:, None]):
        raise ValueError('Each row must hold one contiguous run of valid tokens')
    return rolled


class TokenBinding:
    """Codec symbol s -> LM id ids[s], with the logits the tokens head needs."""

    def __init__(self, backbone, ids):
        self._bb = [backbone]  # a list keeps the backbone out of any state_dict
        self.ids = torch.as_tensor(ids, dtype=torch.long)

    def full_logits(self, states):
        return self._bb[0].full_logits(states)

    def row_logits(self, states, ids):
        return self._bb[0].row_logits(states, ids)


class BackboneBase(nn.Module):
    hidden_size = None
    vocab_size = None
    n_layers = None
    n_extra = 0

    def resolve_taps(self, taps):
        """Schema 2: l in 1..L-1 is decoder layer l's output (before the final norm); -1 is the final
        layer after the final norm. 0 and L raise. Returns layer numbers, -1 resolved to L."""
        if any(not (int(t) == -1 or 1 <= int(t) < self.n_layers) for t in taps):
            raise ValueError(f'taps must lie in [1, {self.n_layers - 1}] or be -1 (0 and {self.n_layers} are invalid), got {taps}')
        return [self.n_layers if int(t) == -1 else int(t) for t in taps]

    def padded_ids(self, batch):
        """input_ids [B, T] in the left-padded layout encode() runs (pad positions keep their ids)."""
        ids = batch['input_ids']
        mask = batch.get('attention_mask')
        mask = torch.ones_like(ids, dtype=torch.bool) if mask is None else mask.bool()
        mask, ids = left_pad(mask, ids)
        return torch.where(mask, ids, torch.full_like(ids, -1))

    # codec rows ---------------------------------------------------------------------------------
    def reserve_tokens(self, n, source='append', sha256=''):
        if isinstance(source, (list, tuple)):
            ids = list(source)
        elif source == 'append':
            if self.n_extra:
                raise ValueError('Codec rows are already appended')
            self._append_rows(n)
            ids = list(range(self.vocab_size, self.vocab_size + n))
        else:
            ids = load_ids(source, n, sha256)
        if len(ids) != n or max(ids) >= self.vocab_size + self.n_extra:
            raise ValueError('Reserved ids do not fit the vocabulary')
        return TokenBinding(self, ids)

    def _append_rows(self, n):
        emb, out = self.input_module().weight, self.output_module().weight
        self.n_extra = n
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(0)
            self.extra_embed = nn.Embedding(n, self.hidden_size)
            self.extra_out = nn.Linear(self.hidden_size, n, bias=False)
            with torch.no_grad():
                for table, ref in ((self.extra_embed.weight, emb), (self.extra_out.weight, out)):
                    ref = ref.detach().float()
                    table.copy_(ref.mean(0) + torch.randn(table.shape) * 0.1 * ref.std(0))
        self.extra_embed.to(emb.device, emb.dtype)
        self.extra_out.to(out.device, out.dtype)

    def embed_ids(self, ids):
        base = self.input_module()(ids.clamp(max=self.vocab_size - 1))
        if self.n_extra:
            extra = ids >= self.vocab_size
            rows = self.extra_embed((ids - self.vocab_size).clamp(0, self.n_extra - 1)).to(base.dtype)
            base = torch.where(extra[..., None], rows, base)
        return base

    def full_logits(self, states):
        head = self.output_module()
        logits = head(states.to(head.weight.dtype))
        if self.n_extra:
            logits = torch.cat([logits, self.extra_out(states.to(self.extra_out.weight.dtype)).to(logits.dtype)], -1)
        return logits

    def row_logits(self, states, ids):
        head = self.output_module()
        ids = ids.to(head.weight.device)
        w = head.weight[ids.clamp(max=self.vocab_size - 1)]
        if self.n_extra:
            extra = self.extra_out.weight[(ids - self.vocab_size).clamp(0, self.n_extra - 1)].to(w.dtype)
            w = torch.where((ids >= self.vocab_size)[:, None], extra, w)
        b = getattr(head, 'bias', None)
        if b is not None:
            b = torch.where(ids >= self.vocab_size, torch.zeros_like(b[:1]), b[ids.clamp(max=self.vocab_size - 1)])
        return F.linear(states.to(w.dtype), w, b)

    def _unfreeze_extra(self):
        if self.n_extra:
            self.extra_embed.requires_grad_(True)
            self.extra_out.requires_grad_(True)

    # decoding -----------------------------------------------------------------------------------
    def decoder(self, batch, ext, use_cache=False):
        """Generic decoder without a cache: re-encodes the prefix plus the tokens chosen so far."""
        tokens = []

        def step(ids):
            if ids is not None:
                tokens.append(ids)
            full = ext
            if tokens:
                emb = self.embed_ids(torch.stack(tokens, 1))
                full = emb if ext is None else torch.cat([ext, emb.to(ext.dtype)], 1)
            taps, _ = self.encode(batch, full)
            return taps[-1][:, -1]
        return step


def inject_lora(module, cfg, targets):
    from peft import LoraConfig, inject_adapter_in_model
    config = LoraConfig(r=cfg.lora_rank, lora_alpha=cfg.lora_alpha, lora_dropout=cfg.lora_dropout,
                        target_modules=targets)
    inject_adapter_in_model(config, module)
    for name, p in module.named_parameters():
        if 'lora_' in name:
            p.requires_grad_(True)
