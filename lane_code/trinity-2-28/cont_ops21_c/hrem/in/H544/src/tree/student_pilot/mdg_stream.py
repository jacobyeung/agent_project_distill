"""Canonical single-token native continuation shared by decode and MDG export.

Batched BF16 suffixes can change mask signs near zero. Export uses the same
cache positions, gate and per-label decoder batch as autoregressive decode.
Training keeps its gradient-carrying batched suffix implementation.
"""
from collections import deque
from contextlib import contextmanager, nullcontext

import torch

from . import mdg_features as features


class QueryStream:
    """Keep only the latest 96 token states; never replay the LM for a ground call."""
    def __init__(self, model, tokenizer):
        self.model, self.tokenizer = model, tokenizer
        if hasattr(model, 'mdg_lora_config'):
            opener = tokenizer.encode('<ground', add_special_tokens=False)
            if len(opener) != 1 or tokenizer.decode(opener, skip_special_tokens=False) != '<ground':
                raise ValueError('Streaming MDG span LoRA requires an atomic <ground opener token')
        self.tokens, self.states = deque(maxlen=96), deque(maxlen=96)
        self.current = None

    @contextmanager
    def token(self, input_ids):
        token = int(input_ids[0, -1])
        # MDG LoRA runs only on a recognized grounding-call span, including its end.
        text = self.tokenizer.decode([*self.tokens, token], skip_special_tokens=False)
        start = text.rfind('<ground')
        token_text = self.tokenizer.decode([token], skip_special_tokens=False)
        previous = text[:-len(token_text)] if token_text else text
        active = start >= 0 and (start >= len(previous) or '>' not in previous[start:])
        gate = nullcontext()
        if hasattr(self.model, 'mdg_lora_config'):
            from .mdg_lora import suffix_mask
            mask = torch.full((1, 1), active, dtype=torch.bool, device=input_ids.device)
            gate = suffix_mask(self.model, mask)
        with gate, features._SuffixCapture(self.model) as recorded:
            yield
        layer, norm = recorded.states['layer'], recorded.states['norm']
        self.tokens.append(token)
        self.states.append(torch.stack((layer[0, -1], norm[0, -1])).float().detach())

    def finish(self, name):
        ids = list(self.tokens)
        text = self.tokenizer.decode(ids, skip_special_tokens=False)
        call = f'<ground obj="{name}">'
        if not text.endswith(call):
            raise ValueError('MDG query must end at the closed ground call')
        # Recover offsets from the actual sampled IDs. Re-encoding a sliding
        # window can merge its first tokens or lose partial UTF-8 byte tokens.
        boundaries = [0]
        for i in range(1, len(ids) + 1):
            prefix = self.tokenizer.decode(ids[:i], skip_special_tokens=False)
            common = next((j for j, (a, b) in enumerate(zip(prefix, text)) if a != b),
                          min(len(prefix), len(text)))
            boundaries.append(common)
        offsets = []
        for i in range(len(ids)):
            start, end = boundaries[i:i+2]
            if end <= start:
                end = next((b for b in boundaries[i+2:] if b > start), start)
            offsets.append((start, end))
        begin = len(text) - len(call) + len('<ground obj="')
        span = [i for i, (a, b) in enumerate(offsets)
                if a < begin + len(name) and begin < b]
        if not span:
            raise ValueError('Ground name has no token states')
        states = list(self.states)
        query = states[-1][None]
        phrase = query.new_zeros((1, features.PHRASE_MAX, 2, query.shape[-1]))
        mask = torch.zeros((1, features.PHRASE_MAX), dtype=torch.bool, device=query.device)
        selected = span[:features.PHRASE_MAX]
        phrase[0, :len(selected)] = torch.stack([states[i] for i in selected])
        mask[0, :len(selected)] = True
        self.current = features.SuffixStates(query, phrase, mask)
        return self.current


@torch.no_grad()
def stream_suffix_states(model, prefix, batch, names, *, chunk=8):
    if model.training or type(chunk) is not int or chunk < 1:
        raise ValueError('Native MDG export requires eval mode and a positive chunk')
    if prefix.cache.get_seq_length() != prefix.prefix_len or batch['input_ids'].shape[1] != prefix.prefix_len:
        raise ValueError('Incomplete MDG prefix cache or token IDs')
    if prefix.rope_deltas is None:
        raise ValueError('MDG prefix lacks RoPE deltas')
    tokenizer, native, outputs = features._tokenizer(model), features._native(model), []
    previous_delta = model.model.rope_deltas
    try:
        for name in names:
            ids, _ = features.suffix_tokens(tokenizer, name)
            full = torch.cat((batch['input_ids'], batch['input_ids'].new_tensor([ids])), 1)
            attention = torch.ones_like(full)
            cache = features.expand_cache(prefix.cache, 1)
            model.model.rope_deltas = prefix.rope_deltas.clone()
            stream = QueryStream(model, tokenizer)
            for at in range(prefix.prefix_len, full.shape[1]):
                upto = at + 1
                prepared = native.prepare_inputs_for_generation(full[:, :upto], next_sequence_length=1,
                    attention_mask=attention[:, :upto],
                    position_ids=native._prepare_position_ids_for_generation(full[:, :upto],
                        {'attention_mask': attention[:, :upto], 'past_key_values': cache}),
                    past_key_values=cache, use_cache=True, is_first_iteration=False)
                with stream.token(full[:, at:upto]):
                    output = native(**prepared, return_dict=True)
                cache = output.past_key_values
                if cache.get_seq_length() != upto:
                    raise ValueError('Native MDG export did not consume exactly one token')
            outputs.append(stream.finish(name))
    finally:
        model.model.rope_deltas = previous_delta
    if not outputs:
        d = prefix.hidden.shape[-1]
        return features.SuffixStates(prefix.hidden.new_zeros((0, 2, d), dtype=torch.float32),
            prefix.hidden.new_zeros((0, features.PHRASE_MAX, 2, d), dtype=torch.float32),
            torch.zeros((0, features.PHRASE_MAX), dtype=torch.bool, device=prefix.hidden.device))
    return features.SuffixStates(*(torch.cat([getattr(out, key) for out in outputs])
                                  for key in ('query', 'phrase', 'phrase_mask')))


def decoder_outputs(head, video, states):
    """Keep per-object inference batches and all decoder layers."""
    outputs = [head(video, states.query[i:i+1], states.phrase[i:i+1], states.phrase_mask[i:i+1])
               for i in range(len(states.query))]
    if not outputs:
        raise ValueError('MDG decoder needs at least one query')
    return [{key: torch.cat([out[layer][key] for out in outputs]) for key in outputs[0][layer]}
            for layer in range(len(outputs[0]))]


def decoder_output(head, video, states):
    """Use the same final decoder layer for native export and decode."""
    return decoder_outputs(head, video, states)[-1]
