"""Batch token forwards while keeping tool queues and hybrid states per row.

Each live row emits one token per tick, sampled or forced. Completed rows leave
immediately, so no padding token enters a live recurrent state. Video prefills
and tool queries use the single-row path's hooks.
"""
from collections import deque
import copy

import torch
import torch.nn.functional as F

from . import carrier_c1_decode as D

_STATE_TENSORS = ('keys', 'values', 'conv_states', 'recurrent_states')


def merge_caches(caches):
    """Left-pad full-attention KV and concatenate GDN states without padding.

    Keys retain their rotary positions. New positions use the attention-mask
    count and each row's delta. Reject static, sliding and offloaded caches.
    """
    from transformers.cache_utils import DynamicCache, DynamicLayer, LinearAttentionLayer
    if not caches or any(type(c) is not DynamicCache or c.offloading for c in caches):
        raise ValueError('Batched routing requires resident native DynamicCache instances')
    width = max(c.get_seq_length() for c in caches)
    result = copy.copy(caches[0])
    result.layers = []
    if any(len(c.layers) != len(caches[0].layers) for c in caches):
        raise ValueError('Hybrid cache layer counts differ')
    for i, first in enumerate(caches[0].layers):
        if type(first) not in (DynamicLayer, LinearAttentionLayer):
            raise ValueError('Batched routing supports full-attention and linear-attention layers only')
        originals = [c.layers[i] for c in caches]
        if any(type(x) is not type(first) for x in originals):
            raise ValueError('Hybrid cache layer types differ')
        layer = copy.copy(first)
        for name in _STATE_TENSORS:
            values = [getattr(x, name, None) for x in originals]
            if all(v is None for v in values):
                continue
            if any(v is None or v.shape[0] != 1 for v in values):
                raise ValueError('Each prefill cache must contain exactly one initialized row')
            if name in ('keys', 'values'):
                if any(v.shape[-2] != c.get_seq_length() for v, c in zip(values, caches)):
                    raise ValueError('Full-attention cache length differs from its prefix')
                values = [F.pad(v, (0, 0, width - v.shape[-2], 0)) for v in values]
            setattr(layer, name, torch.cat(values, dim=0))
        if hasattr(layer, 'max_batch_size'):
            layer.max_batch_size = len(caches)
        result.layers.append(layer)
    return result


def select_cache_rows(cache, indices):
    """Compact all four state tensors; the KV-only HF helper omits GDN."""
    for layer in cache.layers:
        for name in _STATE_TENSORS:
            value = getattr(layer, name, None)
            if value is not None:
                setattr(layer, name, value.index_select(0, indices.to(value.device)))
        if hasattr(layer, 'max_batch_size'):
            layer.max_batch_size = len(indices)


def _row_values(value, count, name):
    if value is None:
        return [None] * count
    if not isinstance(value, (list, tuple)) or len(value) != count:
        raise ValueError(f'{name} must contain one value per prompt')
    return list(value)


def _tower_failure(exc, batch, mode):
    return dict(tokens=[], text='', calls=[], finish='tower_error', mode=mode, tower_error=str(exc),
                heads=dict(pose_source='tower', tower_scale=None, pose9=None, gravity=None, depth_queries=[]),
                geometry_error=str(exc), prompt_tokens=int(batch['input_ids'].shape[1]), generated_tokens=0, errors=1)


class Row:
    def __init__(self, state, processor, model, *, mode, pose_source, max_calls, max_new_tokens, logits_processor, reference_choice=None):
        self.reference_choice=reference_choice
        self.state, self.tokenizer = state, processor.tokenizer
        self.mode, self.pose_source, self.max_calls = mode, pose_source, max_calls
        self.max_new_tokens, self.logits_processor = max_new_tokens, logits_processor
        eos = state.native.generation_config.eos_token_id if state.native.generation_config else None
        self.eos = set(eos if isinstance(eos, (list, tuple)) else [eos or self.tokenizer.eos_token_id]) | {self.tokenizer.eos_token_id}
        self.reserved = [self.tokenizer.convert_tokens_to_ids('<tool_response>'),
                         self.tokenizer.convert_tokens_to_ids('</tool_response>'), model.carrier_id]
        self.ids, self.records, self.forced = [], [], deque()
        self.active, self.ground_layout = None, False
        self.registry = D.calculator.PrintedPointRegistry()
        self.finish = 'context_exhaustion' if state.cap <= 0 else None

    def step(self, logits):
        """Emit one token; only sampled tokens can open or close a tool call."""
        if self.forced:
            token = self.forced.popleft()
            self.ids.append(token)
        else:
            logits = logits.float().clone()
            logits[:, self.reserved] = -float('inf')
            if self.logits_processor is not None:
                logits = self.logits_processor(self.ids, logits)
            token = self.reference_choice.choose(self.records,logits) if self.reference_choice is not None else int(logits.argmax(-1))
            if token in self.reserved:
                raise ValueError('Generated tokens cannot impersonate injected responses or carriers')
            self.ids.append(token)
            if token in self.eos:
                self.finish = 'eos'
                return token
            self._call(token)
        if self.finish is None and len(self.ids) >= self.state.cap:
            self.finish = 'max_new_tokens' if self.max_new_tokens else 'context_exhaustion'
        return token

    def _call(self, token):
        ids, tokenizer = self.ids, self.tokenizer
        if token in self.state.openers:
            self.active = len(ids) - 1
        tail = tokenizer.decode(ids[self.active:] if self.active is not None else ids[-24:], skip_special_tokens=False)
        call_text = None
        if self.active is not None and (tail.endswith('>') or len(ids) - self.active > D.MAX_CALL_TOKENS):
            match = D.GROUND_TAIL.search(tail) or D.GAP_TAIL.search(tail)
            call_text, self.active = match.group(0) if match else tail, None
        elif self.active is None and tail.endswith('>'):
            ground_tail = tokenizer.decode(ids[-D.MAX_CALL_TOKENS:], skip_special_tokens=False)
            match = D.GROUND_TAIL.search(ground_tail) or D.GAP_TAIL.search(ground_tail) or D.CALCULATOR_TAIL.search(ground_tail)
            call_text = match.group(0) if match else None
        if call_text is None and tail.endswith('>'):
            match = D.trace313.extra_tail(tokenizer.decode(ids[-D.MAX_CALL_TOKENS:], skip_special_tokens=False))
            call_text = match.group(0) if match else None
        if call_text is None:
            return
        if len(self.records) >= self.max_calls:
            self.finish = 'call_limit'
            return
        text, info = D.respond_state(self.state,call_text,self.registry)
        v312 = D.ground_layout_for(self.state,info)
        self.ground_layout = self.ground_layout or v312
        wrapped = '\n<tool_response>\n' + text + '\n</tool_response>' if self.ground_layout else '<tool_response>' + text + '</tool_response>'
        forced = tokenizer.encode(wrapped, add_special_tokens=False)[:max(0, self.state.cap - len(self.ids))]
        self.records.append(dict(call=call_text, response=text, at_token=len(self.ids), forced_tokens=len(forced), **info))
        self.forced.extend(forced)

    def record(self):
        heads = self.state.heads
        result = dict(tokens=self.ids, text=self.tokenizer.decode(self.ids, skip_special_tokens=False),
                    calls=self.records, finish=self.finish, mode=self.mode,
                    heads=dict(pose9=heads.pose9.tolist(),
                        gravity=None if heads.gravity is None else heads.gravity.tolist(), depth_queries=heads.queries,
                        **(dict(pose_source='tower', tower_scale=float(heads.tower_scale)) if self.pose_source == 'tower' else {}),
                        **D.ground_records(self.state)),
                    geometry_error=self.state.geometry_error, prompt_tokens=self.state.prompt_length,
                    generated_tokens=len(self.ids), errors=sum(r['kind'] == 'error' or r.get('verify_error',False) for r in self.records))
        if self.reference_choice is not None:result["scripted"]=self.reference_choice.check_complete(result)
        return result


@torch.no_grad()
def generate_batch(model, processor, batches, *, max_new_tokens=None, mode='own', donor_batch=None,
                   max_calls=200, logits_processor=None, pose_source='own', tower_state=None,mask_source=None,ground_backend=None,reread=None,verify=None,reference_trace=None):
    """Return ordered single-row records while batching all live token forwards."""
    n = len(batches)
    from .scripted_calls import ReferenceChoice
    references=_row_values(reference_trace,n,'reference_trace')
    choices=[ReferenceChoice(ref,processor.tokenizer) if ref is not None else None for ref in references]
    donors = _row_values(donor_batch, n, 'donor_batch')
    towers = _row_values(tower_state, n, 'tower_state')
    backends = _row_values(ground_backend,n,'ground_backend')
    rereads = _row_values(reread,n,'reread')
    verifies = _row_values(verify,n,'verify')
    sources = [mask_source]*n if isinstance(mask_source,str) or mask_source is None else _row_values(mask_source,n,'mask_source')
    if len({id(b) for b in backends if b is not None}) != sum(b is not None for b in backends):
        raise ValueError('each_row_requires_its_own_ground_backend')
    processors = _row_values(logits_processor, n, 'logits_processor')
    if mode not in D.MODES or (mode == 'shuffle') != (donor_batch is not None):
        raise ValueError('Shuffle mode needs a donor batch; own mode refuses one')
    if pose_source == 'own' and tower_state is not None:
        raise ValueError('own pose_source refuses tower_state')
    if model.training:
        raise ValueError('Routed decoding requires eval mode')
    for batch in batches:
        if batch['input_ids'].ndim != 2 or batch['input_ids'].shape[0] != 1:
            raise ValueError('Batched routed decode expects a sequence of single-row prompt batches')
        if batch['attention_mask'].shape != batch['input_ids'].shape or not bool(batch['attention_mask'].all()):
            raise ValueError('Supply unpadded single-row prompts; the decoder pads cached KV internally')
    results, rows, positions, deltas = [None] * n, [], [], []
    previous_delta = model.model.rope_deltas
    try:
        for i, batch in enumerate(batches):
            try:
                with D.trace313.row(i):
                    state = D._prepare_decode(model, processor, batch, max_new_tokens=max_new_tokens, mode=mode,
                                              donor_batch=donors[i], pose_source=pose_source, tower_state=towers[i],
                                              mask_source=sources[i],ground_backend=backends[i],reread=rereads[i],verify=verifies[i])
            except D.TowerError as exc:
                if pose_source != 'tower':
                    raise
                results[i] = _tower_failure(exc, batch, mode)
                continue
            row = Row(state, processor, model, mode=mode, pose_source=pose_source, max_calls=max_calls,
                      max_new_tokens=max_new_tokens, logits_processor=processors[i],reference_choice=choices[i])
            if row.finish is not None:
                results[i] = row.record()
                continue
            rows.append(row)
            positions.append(i)
            deltas.append(model.model.rope_deltas.detach().clone())
        if not rows:
            return results
        native = rows[0].state.native
        cache = merge_caches([r.state.output.past_key_values for r in rows])
        width = cache.get_seq_length()
        logits = torch.cat([r.state.output.logits[:, -1, :] for r in rows], 0)
        for row in rows:
            row.state.output = None
        template = batches[positions[0]]['input_ids']
        pad = getattr(processor.tokenizer, 'pad_token_id', None)
        full = template.new_full((len(rows), width + max(r.state.cap for r in rows)), pad if pad is not None else 0)
        mask = batches[positions[0]]['attention_mask'].new_zeros(full.shape)
        for j, i in enumerate(positions):
            length = batches[i]['input_ids'].shape[1]
            full[j, width-length:width] = batches[i]['input_ids'][0]
            mask[j, width-length:width] = 1
        delta = torch.cat(deltas, dim=0)
        while rows:
            model.model.rope_deltas = delta
            keep, emitted = [], []
            for j, (row, i) in enumerate(zip(rows, positions)):
                try:
                    with D.trace313.row(i):
                        token = row.step(logits[j:j+1])
                except D.TowerError as exc:
                    if pose_source != 'tower':
                        raise
                    results[i] = _tower_failure(exc, batches[i], mode)
                    continue
                if row.finish is not None:
                    results[i] = row.record()
                else:
                    keep.append(j)
                    emitted.append(token)
            if not keep:
                break
            if len(keep) != len(rows):
                indices = torch.tensor(keep, device=full.device, dtype=torch.long)
                select_cache_rows(cache, indices)
                full, mask, delta = full[indices], mask[indices], delta[indices]
                rows, positions = [rows[j] for j in keep], [positions[j] for j in keep]
            full[:, width] = template.new_tensor(emitted)
            mask[:, width] = 1
            width += 1
            model.model.rope_deltas = delta
            output, cache = D.consume_cache_tokens(native, full[:, :width], mask[:, :width], cache)
            logits = output.logits[:, -1, :]
        return results
    finally:
        model.model.rope_deltas = previous_delta
