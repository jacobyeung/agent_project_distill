"""(c) Action tokens written by the LM (design record 1.5).

A codec (`codecs/`) turns the normalised chunk into symbols; `bind(binding)` maps symbol s to LM id
`binding.ids[s]` (variable-length codecs get one more id, the end symbol). Training is teacher
forced: the policy appends the ids after the prefix and `query_states[:, j]` is the LM state that
predicts symbol j; cross-entropy runs over the full vocabulary (`tok_ce=full`) or the codec ids only
(`restricted`). Inference decodes greedily through `inputs.decoder`, constrained to the codec ids,
until the end symbol (or the fixed length, or `tok_max_tokens`). A sequence that does not parse
decodes to zeros with `last_ok` False for that row; the caller re-queries once, then logs a no-op.

The same class provides the flow head's LM token loss (`lm_token_loss`, knowledge insulation).
"""
import torch
from torch.nn import functional as F

from ..codecs import make_codec
from ..interface import ActionHead


class TokensHead(ActionHead):
    kind = 'tokens'

    def __init__(self, cfg, codec=None, tokenizer=None):
        super().__init__(cfg)
        self.codec = codec or make_codec(cfg, tokenizer=tokenizer)
        self.variable = self.codec.fixed_length is None
        self.n_symbols = self.codec.vocab + (1 if self.variable else 0)
        self.end = self.codec.vocab if self.variable else None
        self._binding = None
        self.last_ok = None

    def check(self, inputs, actions=None):
        """The LM reads cond and proprio (as the flow arm's auxiliary, it reads only the prefix)."""
        if actions is not None and tuple(actions.shape[1:]) != (self.cfg.chunk, self.cfg.action_dim):
            raise ValueError(f'actions must be [B, {self.cfg.chunk}, {self.cfg.action_dim}], got {tuple(actions.shape)}')

    def bind(self, binding):
        """binding: ids [n_symbols] LongTensor, full_logits(states), row_logits(states, ids)."""
        if len(binding.ids) != self.n_symbols:
            raise ValueError(f'binding holds {len(binding.ids)} ids, the codec needs {self.n_symbols}')
        self._binding = [binding]

    @property
    def binding(self):
        if self._binding is None:
            raise RuntimeError('TokensHead.bind(binding) was not called')
        return self._binding[0]

    @property
    def max_len(self):
        return self.codec.fixed_length or self.cfg.tok_max_tokens

    def targets(self, actions, action_mask=None):
        """-> (symbols [B, L] long, mask [B, L] bool). Variable codecs end each row with the end
        symbol and pad with it (padding masked)."""
        seqs = self.codec.encode(actions)
        if self.variable:
            seqs = [s + [self.end] for s in seqs]
            if max(map(len, seqs)) > self.max_len:
                raise ValueError(f'A chunk needs {max(map(len, seqs))} tokens > tok_max_tokens={self.max_len}')
        length = max(map(len, seqs))
        sym = torch.full((len(seqs), length), self.end if self.variable else 0, dtype=torch.long)
        mask = torch.zeros(len(seqs), length, dtype=torch.bool)
        for i, s in enumerate(seqs):
            sym[i, :len(s)] = torch.tensor(s)
            mask[i, :len(s)] = True
        if action_mask is not None and hasattr(self.codec, 'step_of_token'):
            am = action_mask.bool().cpu()
            am = am if am.ndim == 2 else am.all(-1)
            mask &= am[:, self.codec.step_of_token()]
        device = actions.device
        return sym.to(device), mask.to(device)

    def token_ids(self, symbols):
        return self.binding.ids.to(symbols.device)[symbols]

    def loss(self, inputs, actions, action_mask=None, targets=None):
        self.check(inputs, actions)
        sym, mask = self.targets(actions, action_mask) if targets is None else targets
        q = inputs.query_states
        if q is None or q.shape[1] != sym.shape[1]:
            raise ValueError(f'The tokens head needs query_states [B, {sym.shape[1]}, D] (teacher forced)')
        if self.cfg.tok_ce == 'full':
            logits = self.binding.full_logits(q).float()
            target = self.token_ids(sym)
        else:
            logits = self.binding.row_logits(q, self.binding.ids).float()
            target = sym
        ce = F.cross_entropy(logits.reshape(-1, logits.shape[-1]), target.reshape(-1), reduction='none')
        m = mask.reshape(-1).float()
        loss = (ce * m).sum() / m.sum().clamp(min=1.0)
        with torch.no_grad():
            pred = self.binding.row_logits(q, self.binding.ids).argmax(-1)
            acc = ((pred == sym).float().reshape(-1) * m).sum() / m.sum().clamp(min=1.0)
        return {'loss': loss, 'parts': {'ce': loss.detach(), 'token_acc': acc}}

    @torch.no_grad()
    def predict(self, inputs):
        if inputs.decoder is None:
            raise ValueError('The tokens head predicts through the LM: pass inputs.decoder')
        ids = self.binding.ids.to(inputs.lm_states.device)
        state = inputs.decoder(None)
        b = state.shape[0]
        done = torch.zeros(b, dtype=torch.bool, device=state.device)
        seqs = [[] for _ in range(b)]
        for j in range(self.max_len):
            sym = self.binding.row_logits(state, ids).argmax(-1)
            for i in range(b):
                if not done[i] and not (self.variable and sym[i] == self.end):
                    seqs[i].append(int(sym[i]))
            if self.variable:
                done |= sym == self.end
            if bool(done.all()) or j + 1 == self.max_len:
                break
            state = inputs.decoder(ids[sym])
        actions, ok = self.codec.decode(seqs)
        if self.variable:
            ok &= done.cpu()
        self.last_ok = ok
        actions = torch.where(ok[:, None, None], actions, torch.zeros_like(actions))
        return actions.clamp(-1, 1).to(device=inputs.lm_states.device, dtype=inputs.lm_states.dtype)
