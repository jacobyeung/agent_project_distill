"""Serial video prefills, left-padded hybrid caches, batched greedy forwards."""
import copy
import time

# Hybrid cache layers keep their states either as one tensor per attribute
# (transformers 5.12) or as {state_idx: tensor} dicts with per-index flag dicts
# (transformers 5.19, the pinned production runtime). Both forms are handled.
_KV = ('keys', 'values')
_STATES = ('conv_states', 'recurrent_states')
_FLAGS = ('is_conv_states_initialized', 'is_recurrent_states_initialized', 'has_previous_state')


def _entries(value):
    return value if isinstance(value, dict) else {0: value}


def _rebuild(template, entries):
    return dict(entries) if isinstance(template, dict) else entries[0]


def _row_tensor(value):
    if value is None or not hasattr(value, 'shape') or value.shape[0] != 1:
        raise ValueError('Each prefill cache must contain exactly one initialized row')
    return value


def merge_caches(caches):
    """Left-pad full-attention KV and concatenate linear-attention states.

    Keys keep their rotary positions; new positions come from the attention-mask
    count plus each row's delta. Linear-attention states are concatenated without
    padding, so no padding token enters a recurrent or convolution state. Static,
    sliding, offloaded and past-recording caches are rejected.
    """
    import torch
    import torch.nn.functional as F
    from transformers.cache_utils import DynamicCache, DynamicLayer, LinearAttentionLayer
    if not caches or any(type(c) is not DynamicCache or getattr(c, 'offloading', False) for c in caches):
        raise ValueError('Batched routing requires resident native DynamicCache instances')
    if any(len(c.layers) != len(caches[0].layers) for c in caches):
        raise ValueError('Hybrid cache layer counts differ')
    lengths = [c.get_seq_length() for c in caches]
    width = max(lengths)
    result = copy.copy(caches[0])
    result.layers = []
    for i, first in enumerate(caches[0].layers):
        originals = [c.layers[i] for c in caches]
        if type(first) not in (DynamicLayer, LinearAttentionLayer) or any(type(x) is not type(first) for x in originals):
            raise ValueError('Batched routing supports matching full-attention and linear-attention layers only')
        layer = copy.copy(first)
        if type(first) is DynamicLayer:
            for name in _KV:
                values = [_row_tensor(getattr(x, name, None)) for x in originals]
                if any(v.shape[-2] != n for v, n in zip(values, lengths)):
                    raise ValueError('Full-attention cache length differs from its prefix')
                setattr(layer, name, torch.cat([F.pad(v, (0, 0, width-v.shape[-2], 0)) for v in values], dim=0))
        else:
            if any(getattr(x, 'record_past', False) for x in originals):
                raise ValueError('Batched routing refuses past-recording linear-attention layers')
            for name in _FLAGS:
                flags = [getattr(x, name, None) for x in originals]
                if any(f != flags[0] for f in flags):
                    raise ValueError('Linear-attention state flags differ between prefill caches')
                if isinstance(flags[0], dict):
                    setattr(layer, name, dict(flags[0]))
            if isinstance(getattr(first, 'conv_kernel_size', None), dict):
                layer.conv_kernel_size = dict(first.conv_kernel_size)
            for name in _STATES:
                states = [_entries(getattr(x, name, None)) for x in originals]
                if any(s.keys() != states[0].keys() for s in states):
                    raise ValueError('Linear-attention state indices differ between prefill caches')
                merged = {}
                for k in states[0]:
                    values = [s[k] for s in states]
                    if all(v is None for v in values):
                        merged[k] = None
                        continue
                    merged[k] = torch.cat([_row_tensor(v) for v in values], dim=0)
                setattr(layer, name, _rebuild(getattr(first, name, None), merged))
        if hasattr(layer, 'max_batch_size'):
            layer.max_batch_size = len(caches)
        result.layers.append(layer)
    return result


def select_cache_rows(cache, indices):
    """Keep the given rows of every KV and linear-attention state tensor."""
    for layer in cache.layers:
        for name in _KV:
            value = getattr(layer, name, None)
            if value is not None and value.numel():
                setattr(layer, name, value.index_select(0, indices.to(value.device)))
        for name in _STATES:
            value = getattr(layer, name, None)
            if value is None:
                continue
            kept = {k: v if v is None else v.index_select(0, indices.to(v.device)) for k, v in _entries(value).items()}
            setattr(layer, name, _rebuild(value, kept))
        if hasattr(layer, 'max_batch_size'):
            layer.max_batch_size = len(indices)



def selfcheck(steps=6):
    """Batched-versus-serial greedy parity on a tiny native hybrid model (CPU, seconds).

    Exercises merge_caches, select_cache_rows and the native cache continuation
    against the installed transformers before any checkpoint is loaded.
    """
    import torch
    import transformers
    from student_pilot.carrier_c1_decode import consume_cache_tokens
    begun = time.monotonic()
    text = dict(vocab_size=64, hidden_size=32, intermediate_size=64, num_hidden_layers=4,
                num_attention_heads=4, num_key_value_heads=2, head_dim=8, use_cache=True,
                layer_types=['linear_attention']*3+['full_attention'], linear_key_head_dim=4,
                linear_value_head_dim=4, linear_num_key_heads=2, linear_num_value_heads=4,
                pad_token_id=0, rope_parameters=dict(rope_type='default', rope_theta=10000.,
                                                    mrope_section=[1, 1, 2], partial_rotary_factor=1.))
    vision = dict(depth=1, hidden_size=32, intermediate_size=64, num_heads=4, out_hidden_size=32,
                  num_position_embeddings=16, patch_size=2, temporal_patch_size=2, spatial_merge_size=2)
    from transformers import Qwen3_5Config, Qwen3_5ForConditionalGeneration
    config = Qwen3_5Config(text_config=text, vision_config=vision, image_token_id=60, video_token_id=61,
                          vision_start_token_id=62, vision_end_token_id=63)
    for item in (config, config.text_config, config.vision_config):
        item._attn_implementation = 'sdpa'
    state = torch.random.get_rng_state()
    try:
        torch.manual_seed(20261121)
        model = Qwen3_5ForConditionalGeneration(config).float().eval()
        prompts = [torch.randint(2, 60, (1, n)) for n in (5, 9, 13)]
    finally:
        torch.random.set_rng_state(state)
    previous = model.model.rope_deltas
    # Distinct per-row rotary deltas, as rows from different videos have.
    shifts = torch.tensor([[-3], [0], [5]], dtype=torch.long)
    def prefill(ids):
        model.model.rope_deltas = None
        return model(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=True, return_dict=True, logits_to_keep=1)
    try:
        with torch.no_grad():
            serial = []
            for i, ids in enumerate(prompts):
                out = prefill(ids); cache = out.past_key_values; tokens = []; logits = [out.logits[:, -1].float()]
                full = ids
                for _ in range(steps):
                    tokens.append(int(logits[-1].argmax(-1)))
                    full = torch.cat((full, full.new_tensor([[tokens[-1]]])), 1)
                    model.model.rope_deltas = shifts[i:i+1]
                    out, cache = consume_cache_tokens(model, full, torch.ones_like(full), cache)
                    logits.append(out.logits[:, -1].float())
                serial.append((tokens, logits))
            outs = [prefill(ids) for ids in prompts]
            cache = merge_caches([o.past_key_values for o in outs])
            kinds = sorted({type(layer).__name__ for layer in cache.layers})
            state_form = sorted({type(getattr(layer, 'conv_states')).__name__ for layer in cache.layers if hasattr(layer, 'conv_states')})
            width = cache.get_seq_length()
            full = torch.zeros((len(prompts), width+steps), dtype=torch.long); attn = torch.zeros_like(full)
            for j, ids in enumerate(prompts):
                full[j, width-ids.shape[1]:width] = ids[0]; attn[j, width-ids.shape[1]:width] = 1
            logits = torch.cat([o.logits[:, -1].float() for o in outs], 0)
            active = list(range(len(prompts))); worst = 0.; delta = shifts
            for step in range(steps):
                for j, i in enumerate(active):
                    worst = max(worst, float((logits[j]-serial[i][1][step][0]).abs().max()))
                    if int(logits[j].argmax(-1)) != serial[i][0][step]:
                        raise AssertionError(f'batched token differs from serial: row {i} step {step}')
                emitted = [serial[i][0][step] for i in active]
                if step == 2:
                    # Remove the middle row mid-decode, as a finished row would be.
                    keep = [j for j, i in enumerate(active) if i != 1]
                    ix = torch.tensor(keep, dtype=torch.long)
                    select_cache_rows(cache, ix)
                    full, attn, delta = full[ix], attn[ix], delta[ix]
                    active = [active[j] for j in keep]; emitted = [emitted[j] for j in keep]
                full[:, width] = full.new_tensor(emitted); attn[:, width] = 1; width += 1
                model.model.rope_deltas = delta
                out, cache = consume_cache_tokens(model, full[:, :width], attn[:, :width], cache)
                logits = out.logits[:, -1].float()
            for j, i in enumerate(active):
                worst = max(worst, float((logits[j]-serial[i][1][steps][0]).abs().max()))
            if worst > 1e-3:
                raise AssertionError(f'batched logits differ from serial by {worst}')
    finally:
        model.model.rope_deltas = previous
    return dict(passed=True, transformers=transformers.__version__, rows=len(prompts), steps=steps,
                layer_types=text['layer_types'], cache_layers=kinds, linear_state_form=state_form,
                max_logit_diff=worst, seconds=time.monotonic()-begun)


def generate(model, processor, batches, probe, emit, deadline=lambda: None, metrics=None, admit=None):
    """Greedy batched decode; the GPU read and the CPU real-batch check share this path.

    `admit(first_prefill_s, rows)` may shorten the batch to its first k rows after
    the first prefill; it also records per-prefill and per-step seconds.
    """
    import torch
    from student_pilot.carrier_c1_decode import _prepare_decode, consume_cache_tokens
    from student_pilot.ground_context import closed_adapters
    metrics = {} if metrics is None else metrics
    begun = time.monotonic()
    detail = admit is not None
    metrics.update(prefill_s=0., max_step_s=0., steps=0, selects=0, merge_s=None, rows=len(batches))
    if detail: metrics.update(prefill_each_s=[], step_s=[])
    previous = model.model.rope_deltas
    states, deltas = [], []
    sync = lambda: torch.cuda.synchronize(batches[0]['input_ids'].device) if batches[0]['input_ids'].is_cuda else None
    try:
        j = 0
        while j < len(batches):
            deadline()
            started = time.monotonic()
            state = closed_adapters(_prepare_decode)(model, processor, batches[j], max_new_tokens=None)
            assert state.cap >= probe.CAP
            states.append(state)
            deltas.append(model.model.rope_deltas.detach().clone())
            if detail:
                sync(); metrics['prefill_each_s'].append(time.monotonic()-started)
                if j == 0:
                    batches = batches[:max(1, int(admit(metrics['prefill_each_s'][0], len(batches))))]
                    metrics['rows'] = len(batches)
            j += 1
        native = states[0].native
        merging = time.monotonic()
        cache = merge_caches([s.output.past_key_values for s in states])
        metrics['merge_s'] = time.monotonic()-merging
        width = cache.get_seq_length()
        logits = torch.cat([s.output.logits[:, -1, :] for s in states], 0)
        for state in states: state.output = None
        # Only the native LM and cache are needed after prefill; no tool state is served.
        states = []
        seed = batches[0]['input_ids']
        full = seed.new_full((len(batches), width+probe.CAP), processor.tokenizer.pad_token_id or 0)
        attn = seed.new_zeros(full.shape)
        for j, batch in enumerate(batches):
            n = batch['input_ids'].shape[1]
            full[j, width-n:width] = batch['input_ids'][0]; attn[j, width-n:width] = 1
        delta = torch.cat(deltas, 0)
        active = list(range(len(batches))); ids = [[] for _ in batches]
        eos = native.generation_config.eos_token_id
        eos = set(eos if isinstance(eos, (list, tuple)) else [eos or processor.tokenizer.eos_token_id]) | {processor.tokenizer.eos_token_id}
        reserved = [processor.tokenizer.convert_tokens_to_ids(t) for t in ('<tool_response>', '</tool_response>')]
        if getattr(model, 'carrier_id', None) is not None: reserved.append(model.carrier_id)
        if seed.is_cuda: torch.cuda.synchronize(seed.device)
        metrics['prefill_s'] = time.monotonic()-begun
        while active:
            deadline()
            step_start = time.monotonic()
            logits = logits.float().clone(); logits[:, reserved] = -float('inf')
            chosen = logits.argmax(-1).tolist(); keep = []; emitted = []
            for j, i in enumerate(active):
                token = int(chosen[j]); ids[i].append(token)
                text = processor.tokenizer.decode(ids[i], skip_special_tokens=False)
                opened = probe.detect(text)
                finish = 'call' if opened else 'eos' if token in eos else 'cap' if len(ids[i]) == probe.CAP else None
                if finish:
                    emit(i, dict(text=text, tokens=ids[i], n=len(ids[i]), g=0 in opened,
                                 o=[v for v in opened if v], finish=finish))
                else: keep.append(j); emitted.append(token)
            if not keep:
                metrics['max_step_s'] = max(metrics['max_step_s'], time.monotonic()-step_start)
                metrics['steps'] += 1
                if detail: metrics['step_s'].append(time.monotonic()-step_start)
                break
            if len(keep) != len(active):
                ix = torch.tensor(keep, device=full.device, dtype=torch.long)
                select_cache_rows(cache, ix); metrics['selects'] += 1
                full, attn, delta = full[ix], attn[ix], delta[ix]
                active = [active[j] for j in keep]
            full[:, width] = seed.new_tensor(emitted); attn[:, width] = 1; width += 1
            model.model.rope_deltas = delta
            output, cache = consume_cache_tokens(native, full[:, :width], attn[:, :width], cache)
            logits = output.logits[:, -1, :]
            if seed.is_cuda: torch.cuda.synchronize(seed.device)
            metrics['max_step_s'] = max(metrics['max_step_s'], time.monotonic()-step_start)
            metrics['steps'] += 1
            if detail: metrics['step_s'].append(time.monotonic()-step_start)
    finally:
        model.model.rope_deltas = previous


def serial(model, processor, batch, probe, deadline=lambda: None):
    """One-row serial greedy decode with the same stops, EOS set and reserved tokens."""
    import torch
    from student_pilot.carrier_c1_decode import _prepare_decode, consume_cache_tokens
    from student_pilot.ground_context import closed_adapters
    previous = model.model.rope_deltas
    try:
        state = closed_adapters(_prepare_decode)(model, processor, batch, max_new_tokens=None)
        native = state.native; cache = [state.output.past_key_values]; delta = model.model.rope_deltas.detach().clone()
        eos = native.generation_config.eos_token_id
        eos = set(eos if isinstance(eos, (list, tuple)) else [eos or processor.tokenizer.eos_token_id]) | {processor.tokenizer.eos_token_id}
        reserved = [processor.tokenizer.convert_tokens_to_ids(t) for t in ('<tool_response>', '</tool_response>')]
        if getattr(model, 'carrier_id', None) is not None: reserved.append(model.carrier_id)
        def choose(output):
            logits = output.logits[:, -1, :].float().clone(); logits[:, reserved] = -float('inf')
            return int(logits.argmax(-1))
        def advance(ids):
            full = torch.cat((batch['input_ids'], batch['input_ids'].new_tensor([ids])), 1)
            attn = torch.cat((batch['attention_mask'], batch['attention_mask'].new_ones((1, len(ids)))), 1)
            model.model.rope_deltas = delta
            output, cache[0] = consume_cache_tokens(native, full, attn, cache[0])
            return output
        return probe.decode(state.output, choose, advance, processor.tokenizer, eos, deadline)
    finally:
        model.model.rope_deltas = previous
