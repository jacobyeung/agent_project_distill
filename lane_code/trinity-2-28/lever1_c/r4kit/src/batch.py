"""Serial video prefills, left-padded hybrid caches, batched greedy forwards."""
import time


def generate(model, processor, batches, probe, emit, deadline=lambda: None, metrics=None):
    import torch
    from student_pilot.carrier_c1_decode import _prepare_decode, consume_cache_tokens
    from student_pilot.carrier_c1_batch_decode import merge_caches, select_cache_rows
    from student_pilot.ground_context import closed_adapters
    metrics = {} if metrics is None else metrics
    begun = time.monotonic()
    metrics.update(prefill_s=0., max_step_s=0., steps=0)
    previous = model.model.rope_deltas
    states, deltas = [], []
    try:
        for batch in batches:
            deadline()
            state = closed_adapters(_prepare_decode)(model, processor, batch, max_new_tokens=None)
            assert state.cap >= probe.CAP
            states.append(state)
            deltas.append(model.model.rope_deltas.detach().clone())
        native = states[0].native
        cache = merge_caches([s.output.past_key_values for s in states])
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
                break
            if len(keep) != len(active):
                ix = torch.tensor(keep, device=full.device, dtype=torch.long)
                select_cache_rows(cache, ix)
                full, attn, delta = full[ix], attn[ix], delta[ix]
                active = [active[j] for j in keep]
            full[:, width] = seed.new_tensor(emitted); attn[:, width] = 1; width += 1
            model.model.rope_deltas = delta
            output, cache = consume_cache_tokens(native, full[:, :width], attn[:, :width], cache)
            logits = output.logits[:, -1, :]
            if seed.is_cuda: torch.cuda.synchronize(seed.device)
            metrics['max_step_s'] = max(metrics['max_step_s'], time.monotonic()-step_start)
            metrics['steps'] += 1
    finally:
        model.model.rope_deltas = previous
