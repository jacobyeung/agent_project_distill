"""VLAPolicy: backbone adapter + cond projector + one action head, behind loss(batch) and predict(batch).

batch keys
- backbone inputs (StubBackbone: input_ids, attention_mask; StudentAdapter: the processor outputs);
- proprio [B, P] (normalised), when proprio_dim > 0;
- cond: the raw dict of `cond.py`, when cond != none;
- actions [B, K, A] (normalised) and action_mask [B, K] or [B, K, A], for loss only.

LM input layout (left-padded context, then the appended block):
    [context] [cond tokens, where tokens if cond_inject = lm] [proprio token if proprio_inject = lm] [head block]
The regression head appends nothing: its K queries are the prompt's own query tokens (schema 1 and 4,
`QUERY_TOKEN` 🔍, the last K positions holding `query_token_id`, as StarVLA's
`_gather_action_token_embeddings`). head block: tokens = the codec ids of the chunk except the last
(training); flow with lm_token_loss = the same codec ids (training only). The flow head reads only
the prefix positions, which causal attention keeps independent of the appended codec ids, so its
inputs at training and at inference agree.
"""
import torch
from torch import nn

from .cond import CondProjector, rng_neutral
from .config import VLAConfig
from .heads import TokensHead, make_head
from .interface import HeadInputs
from .layers import zero_
from .utils.proprio import ProprioEncoder

QUERY_TOKEN = '\N{LEFT-POINTING MAGNIFYING GLASS}'  # StarVLA's action-query token (schema 4)


def query_token_id(tokenizer, chunk=8):
    """The LM id of QUERY_TOKEN; `chunk` repeats must tokenize to `chunk` copies of one id."""
    ids = tokenizer.encode(QUERY_TOKEN * chunk, add_special_tokens=False)
    if len(ids) != chunk or len(set(ids)) != 1:
        raise ValueError(f'{QUERY_TOKEN * chunk!r} tokenizes to {ids}, not {chunk} copies of one id')
    return int(ids[0])


_lookup_query_id = query_token_id


def query_positions(padded_ids, token_id, k):
    """[B, T] ids (left-padded layout) -> [B, k] ascending positions of the last k `token_id`s."""
    hits = padded_ids == token_id
    counts = hits.sum(1)
    if bool((counts < k).any()):
        raise ValueError(f'Every row needs {k} query tokens (id {token_id}); found {counts.tolist()}')
    score = torch.where(hits, torch.arange(hits.shape[1], device=hits.device)[None], torch.full_like(padded_ids, -1))
    return score.topk(k, dim=1).values.flip(1)


class VLAPolicy(nn.Module):
    def __init__(self, cfg, backbone, codec=None, tokenizer=None, query_token_id=None):
        super().__init__()
        cfg = cfg if isinstance(cfg, VLAConfig) else VLAConfig.from_dict(cfg)
        if cfg.hidden_size != backbone.hidden_size:
            raise ValueError(f'cfg.hidden_size={cfg.hidden_size} but the backbone has {backbone.hidden_size}')
        if cfg.lm_layers != backbone.n_layers:
            raise ValueError(f'cfg.lm_layers={cfg.lm_layers} but the backbone has {backbone.n_layers} layers')
        if cfg.head == 'regression' and query_token_id is None:
            if tokenizer is None:
                raise ValueError('The regression head reads in-prompt query tokens: pass query_token_id or tokenizer')
            query_token_id = _lookup_query_id(tokenizer, cfg.chunk)
        self.query_token_id = query_token_id
        if (backbone.resolve_taps(cfg.taps), cfg.tap_norm) != (backbone.taps, backbone.tap_norm):
            raise ValueError('Build the backbone with the config taps (Adapter.for_config(..., cfg))')
        self.cfg = cfg
        self.backbone = backbone
        self.head = make_head(cfg, codec=codec, tokenizer=tokenizer) if cfg.head == 'tokens' else make_head(cfg)
        self.cond = CondProjector(cfg)
        with rng_neutral():
            lm = cfg.cond_inject == 'lm'
            self.cond_to_lm = (zero_(nn.Linear(cfg.cond_dim, cfg.hidden_size))
                               if lm and cfg.cond in ('g3t_tokens', 'both') else None)
            self.where_to_lm = (zero_(nn.Linear(cfg.where_features, cfg.hidden_size))
                                if lm and cfg.where_vector and cfg.cond in ('spatial_readouts', 'both') else None)
            self.proprio_to_lm = (ProprioEncoder(cfg.proprio_dim, cfg.hidden_size)
                                  if cfg.proprio_dim and cfg.proprio_inject == 'lm' else None)
            # The flow head's LM token loss (knowledge insulation) has its own tokens head.
            self.aux_tokens = (TokensHead(cfg, codec=codec, tokenizer=tokenizer)
                               if cfg.head == 'flow' and cfg.lm_token_loss != 'none' else None)
        if self.token_head is not None:
            self.token_head.bind(self._binding(self.token_head, tokenizer))
        backbone.set_trainable(cfg)

    @property
    def token_head(self):
        """The head whose codec the LM writes: the tokens head itself, or the flow arm's aux head."""
        return self.head if self.cfg.head == 'tokens' else self.aux_tokens

    def _binding(self, head, tokenizer):
        n = head.n_symbols
        if head.codec.name == 'digits':
            eos = getattr(tokenizer, 'eos_token_id', None)
            if eos is None:
                raise ValueError('The digits codec needs a tokenizer with eos_token_id (its end symbol)')
            return self.backbone.reserve_tokens(n, list(head.codec.allowed) + [eos])
        return self.backbone.reserve_tokens(n, self.cfg.tok_ids, self.cfg.tok_ids_sha256)

    # -------------------------------------------------------------------------------------------
    def _dtype(self):
        return self.backbone.input_module().weight.dtype

    def prefix(self, batch):
        """(prefix ext [B, E, D] or None, cond dict, proprio)."""
        cond = self.cond(batch.get('cond'), training=self.training)
        proprio = batch.get('proprio') if self.cfg.proprio_dim else None
        if self.cfg.proprio_dim and proprio is None:
            raise ValueError(f'proprio_dim={self.cfg.proprio_dim} needs batch["proprio"]')
        parts = []
        if self.cond_to_lm is not None:
            # Masked tokens enter the LM as zeros (the LM cannot mask single appended positions).
            parts.append(self.cond_to_lm(cond['tokens']) * cond['mask'][..., None])
        if self.where_to_lm is not None:
            parts.append(self.where_to_lm(cond['where'].to(self.where_to_lm.weight.dtype)) * cond['where_mask'][..., None])
        if self.proprio_to_lm is not None:
            parts.append(self.proprio_to_lm(proprio))
        ext = torch.cat([p.to(self._dtype()) for p in parts], 1) if parts else None
        return ext, cond, proprio

    def inputs(self, batch, actions=None, action_mask=None):
        """Run the backbone -> (HeadInputs for the head, token-loss inputs or None)."""
        ext, cond, proprio = self.prefix(batch)
        ids = batch['input_ids']
        b = ids.shape[0]
        e = 0 if ext is None else ext.shape[1]
        block, targets = None, None
        if self.token_head is not None and actions is not None:
            targets = self.token_head.targets(actions, action_mask)
            tok = self.token_head.token_ids(targets[0])[:, :-1]
            block = self.backbone.embed_ids(tok) if tok.shape[1] else None
        full = ext if block is None else (block if ext is None else torch.cat([ext, block.to(ext.dtype)], 1))
        taps, mask = self.backbone.encode(batch, full)
        p = taps.shape[2] - (0 if full is None else full.shape[1]) + e  # end of the prefix
        head_cond = self.cfg.cond_inject == 'head'
        inputs = HeadInputs(lm_states=taps[-1][:, :p], lm_mask=mask[:, :p],
                            tap_states=taps[:, :, :p] if taps.shape[0] > 1 else None,
                            cond_tokens=cond['tokens'] if head_cond else None,
                            cond_mask=cond['mask'] if head_cond else None,
                            where=cond['where'] if head_cond else None,
                            where_mask=cond['where_mask'] if head_cond else None,
                            proprio=proprio if self.cfg.proprio_inject == 'head' else None)
        token_inputs = None
        if self.cfg.head == 'regression':
            pos = query_positions(self.backbone.padded_ids(batch), self.query_token_id, self.cfg.chunk)
            inputs.query_states = taps[-1].gather(1, pos.to(taps.device)[..., None].expand(-1, -1, taps.shape[-1]))
        elif targets is not None:
            query = taps[-1][:, p - 1:p - 1 + targets[0].shape[1]]
            if self.cfg.head == 'tokens':
                inputs.query_states = query
            else:
                token_inputs = HeadInputs(lm_states=inputs.lm_states, lm_mask=inputs.lm_mask, query_states=query)
        return inputs, (token_inputs, targets)

    def loss(self, batch):
        actions, mask = batch['actions'], batch.get('action_mask')
        inputs, (token_inputs, targets) = self.inputs(batch, actions, mask)
        if self.cfg.head == 'tokens':
            return self.head.loss(inputs, actions, mask, targets=targets)
        out = self.head.loss(inputs, actions, mask)
        if token_inputs is not None:
            tok = self.token_head.loss(token_inputs, actions, mask, targets=targets)
            out = {'loss': out['loss'] + self.cfg.lm_token_weight * tok['loss'],
                   'parts': {**out['parts'], **{'tok_' + k: v for k, v in tok['parts'].items()}}}
        return out

    @torch.no_grad()
    def predict(self, batch, **kw):
        if self.cfg.head == 'tokens':
            # The LM states live inside the decoder; lm_states only carries batch size, dtype and device.
            ext = self.prefix(batch)[0]
            ids = batch['input_ids']
            dummy = torch.zeros(ids.shape[0], 1, self.cfg.hidden_size, dtype=self._dtype(), device=ids.device)
            return self.head.predict(HeadInputs(lm_states=dummy, lm_mask=torch.ones(dummy.shape[:2], device=ids.device),
                                                decoder=self.backbone.decoder(batch, ext, **kw)))
        return self.head.predict(self.inputs(batch)[0], **kw)

    # -------------------------------------------------------------------------------------------
    def module_groups(self):
        """{group: [parameters]}: vision, lm, codec_rows (appended LM rows), head, cond, lm_inject.
        Use them for separate learning rates (design: lm 2.5e-5, head 2.5e-4) and per-module logs."""
        groups = {k: [] for k in ('vision', 'lm', 'codec_rows', 'head', 'cond', 'lm_inject')}
        for name, p in self.named_parameters():
            if name.startswith('backbone.'):
                key = 'codec_rows' if '.extra_' in name or name.startswith('backbone.extra_') else (
                    'vision' if '.visual.' in name else 'lm')
            elif name.startswith(('head.', 'aux_tokens.')):
                key = 'head'
            elif name.startswith('cond.'):
                key = 'cond'
            else:
                key = 'lm_inject'
            groups[key].append(p)
        return groups

    def gate_norms(self):
        """Norms of the zero-initialised cond / proprio maps (design 5.6 asks the trainer to log them)."""
        out = {}
        for name, mod in self.named_modules():
            if name.endswith(('head.proprio', 'head.where', 'cond_attn.out', 'cond_to_lm', 'where_to_lm', 'cam.1')):
                w = getattr(mod, 'weight', None)
                if w is not None:
                    out[name] = float(w.detach().float().norm())
        for name, p in self.named_parameters():
            if name.endswith('cond_gate'):
                out[name] = float(p.detach().float().abs().max())
        return out
