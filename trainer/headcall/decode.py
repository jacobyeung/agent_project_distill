"""Decoding with head-call interception.

headcall_generate (HF): one prefill over the prompt (its hidden states go to the heads), then one forward per token
on the model's cache. When the model emits </tool_call>, the loop parses the call, asks the heads and feeds
<tool_response>value</tool_response> into the cache, then decoding resumes.

Inserted tokens are fed one at a time. Qwen3.5's linear-attention layers (transformers 5.3 GatedDeltaNet) reuse their
cached recurrent and convolution state only for single-token forwards; a multi-token forward on a non-empty cache
restarts those layers from a zero state, which is what generate(past_key_values=...) does to a continuation chunk.
tests/test_decode.py checks the loop's logits against one uncached forward over the whole sequence.

segment_generate (vLLM or any engine): the engine decodes until </tool_call> or EOS; the loop appends the response
and resubmits prompt + history. Engines do not expose hidden states, so the heads get their context from a separate
HF prefill (HeadContext built by the caller).

Phase 1's heads read 16 camera carriers in the prompt (camera_targets.insert_carriers): a backend with needs_carriers
gets a prompt that must hold them. A carrier-bearing prompt is prefilled by phase1.prefill: for a model with phase 1's
camera heads it is one use_cache forward with training's camera hooks, so the cache holds the learned c_first /
c_rest carrier embeddings and the heads' states come from that same forward (HeadContext.camera_states; Phase1Heads
builds its session from them, with no second forward).

Limits: max_new_tokens counts generated and inserted tokens (the evaluator's output cap), max_calls caps answered
calls (later calls get an error response), and an open call longer than max_call_tokens is closed by the loop.
"""
import time
from collections import namedtuple

from .heads import HeadContext
from .protocol import (CALL_CLOSE, CALL_OPEN, RESPONSE_CLOSE, RESPONSE_OPEN, CallError, format_error,
                       format_value, parse_call)

CallRecord = namedtuple("CallRecord", "index open_token close_token body parse response error_code head_seconds "
                                      "inserted_tokens")


class DecodeConfig(object):
    """allow_lenient: execute a call that parses only after a repair (protocol.parse_call's aliases, key fixes,
    bracket closing); False answers it with an error ('lenient'). Results always count lenient calls apart."""

    def __init__(self, eos_token_ids, max_new_tokens=16384, max_calls=80, max_call_tokens=128, do_sample=False,
                 temperature=1.0, top_p=1.0, seed=17, allow_lenient=True):
        self.eos_token_ids = tuple(eos_token_ids)
        self.max_new_tokens, self.max_calls, self.max_call_tokens = max_new_tokens, max_calls, max_call_tokens
        self.do_sample, self.temperature, self.top_p, self.seed = do_sample, temperature, top_p, seed
        self.allow_lenient = bool(allow_lenient)


class DecodeResult(object):
    def __init__(self, tokens, inserted, calls, finish_reason, timing, self_responses):
        self.tokens, self.inserted, self.calls = tokens, inserted, calls
        self.finish_reason, self.timing, self.self_responses = finish_reason, timing, self_responses

    def summary(self):
        return {"finish_reason": self.finish_reason, "tokens": len(self.tokens),
                "model_tokens": self.inserted.count(False), "inserted_tokens": self.inserted.count(True),
                "calls": len(self.calls), "valid_calls": sum(1 for c in self.calls if c.error_code is None),
                "strict_calls": sum(1 for c in self.calls if c.parse is not None and c.parse.strict),
                "lenient_calls": sum(1 for c in self.calls if c.error_code is None and c.parse is not None
                                     and not c.parse.strict),
                "lenient_refused": sum(1 for c in self.calls if c.error_code == "lenient"),
                "self_responses": self.self_responses, "timing": self.timing}


class _Responder(object):
    """Turns the tokens of one call into response token ids (shared by both decoders)."""

    def __init__(self, tokenizer, heads, config):
        self.tokenizer, self.heads, self.config = tokenizer, heads, config
        self.ids = {name: _single_id(tokenizer, name) for name in (CALL_OPEN, CALL_CLOSE, RESPONSE_OPEN, RESPONSE_CLOSE)}
        self.calls = []
        self.head_seconds = 0.0

    def respond(self, tokens, open_at, close_at, room):
        body = self.tokenizer.decode(tokens[open_at + 1:close_at]) if open_at is not None else None
        parsed, code, tick = None, None, time.monotonic()
        if body is None:
            code, text = "unopened", format_error("</tool_call> without <tool_call>")
        else:
            addressing = getattr(self.heads, "addressing", "frame")
            parsed = parse_call(body, addressing=addressing)
            if len([c for c in self.calls if c.error_code != "unopened"]) >= self.config.max_calls:
                code, text = "limit", format_error("call limit reached; answer without more calls")
            elif not parsed.valid:
                code, text = parsed.error.code, format_error(parsed.error)
            elif not parsed.strict and not self.config.allow_lenient:
                code, text = "lenient", format_error("the call must be strict JSON: "
                                                     '{"name": "depth", "frame": 4, "point": [x, y]}')
            else:
                try:
                    text = format_value(parsed.call.name, self.heads.answer(parsed.call))
                except CallError as error:
                    code, text = error.code, format_error(error)
        seconds = time.monotonic() - tick
        self.head_seconds += seconds
        ids = self.tokenizer.encode(RESPONSE_OPEN + text + RESPONSE_CLOSE, add_special_tokens=False)
        ids = ids[:max(0, room)]
        self.calls.append(CallRecord(len(self.calls), open_at, close_at, body, parsed, text, code, seconds, len(ids)))
        return ids


def _single_id(tokenizer, text):
    ids = tokenizer.encode(text, add_special_tokens=False)
    if len(ids) != 1:
        raise ValueError("%s is not a single token in this tokenizer" % text)
    return ids[0]


def _language_core(model):
    for name in ("model", "base_model"):
        inner = getattr(model, name, None)
        if inner is not None and hasattr(inner, "rope_deltas"):
            return inner
        if inner is not None and inner is not model:
            found = _language_core(inner)
            if found is not None:
                return found
    return model if hasattr(model, "rope_deltas") else None


def headcall_generate(model, batch, tokenizer, heads, config, key=None, row=None, video_token_id=None,
                      on_logits=None):
    """Decode one sample (batch size 1) with head calls. `batch` holds the processor outputs for the prompt.
    on_logits(n, logits) sees the next-token logits after n generated-or-inserted tokens (tests)."""
    import torch

    responder = _Responder(tokenizer, heads, config)
    call_open, call_close = responder.ids[CALL_OPEN], responder.ids[CALL_CLOSE]
    response_open = responder.ids[RESPONSE_OPEN]
    if getattr(heads, "needs_carriers", False):
        from .phase1 import check_carriers
        if "aux_camera_positions" not in batch:
            raise ValueError("phase 1's heads read the 16 camera carriers: insert them (phase1.insert_carriers)")
        check_carriers(batch["input_ids"][0].tolist(), tokenizer)
    from .phase1 import GeometryContext, split_geometry
    model_batch, geometry_features = split_geometry(batch)
    model_batch = {k: v for k, v in model_batch.items() if not k.startswith("aux_") and k != "labels"}
    input_ids = batch["input_ids"]
    if input_ids.shape[0] != 1:
        raise ValueError("headcall_generate decodes one sample at a time")
    device = input_ids.device
    generator = torch.Generator(device="cpu").manual_seed(config.seed)
    core = _language_core(model)
    if core is not None:
        core.rope_deltas = None  # positions of the previous sample must not carry over

    def select(logits):
        if not config.do_sample:
            return int(torch.argmax(logits))
        probs = torch.softmax(logits.float() / config.temperature, dim=-1).cpu()
        if config.top_p < 1.0:
            ordered, order = torch.sort(probs, descending=True)
            keep = torch.cumsum(ordered, dim=-1) - ordered < config.top_p
            probs = torch.zeros_like(probs).scatter(0, order[keep], ordered[keep])
        return int(torch.multinomial(probs / probs.sum(), 1, generator=generator))

    timing = {"prefill_s": 0.0, "decode_s": 0.0, "head_s": 0.0, "total_s": 0.0}
    start = time.monotonic()
    with torch.inference_mode():
        camera_states = None
        if "aux_camera_positions" in batch:
            from .phase1 import prefill
            out, camera_states = prefill(model, batch, output_hidden_states=bool(heads.needs_hidden_states))
        else:
            with GeometryContext(model, geometry_features):
                out = model(**model_batch, use_cache=True, logits_to_keep=1,
                            output_hidden_states=bool(heads.needs_hidden_states))
        cache, logits = out.past_key_values, out.logits[0, -1]
        length = input_ids.shape[1]
        heads.begin(HeadContext(input_ids[0].tolist(), out.hidden_states if heads.needs_hidden_states else None,
                                video_token_id, batch.get("video_grid_thw"), key, row, batch=batch,
                                camera_states=camera_states))
        del out
        timing["prefill_s"] = time.monotonic() - start

        def step(token):
            position = torch.tensor([length + len(tokens) - 1], device=device)
            result = model(input_ids=torch.tensor([[token]], device=device), past_key_values=cache, use_cache=True,
                           cache_position=position)
            if on_logits is not None:
                on_logits(len(tokens), result.logits[0, -1])
            return result.logits[0, -1]

        tokens, inserted, open_at, self_responses, finish = [], [], None, 0, None
        if on_logits is not None:
            on_logits(0, logits)
        while finish is None:
            if len(tokens) >= config.max_new_tokens:
                finish = "max_new_tokens"
                break
            token = select(logits)
            tokens.append(token)
            inserted.append(False)
            if token in config.eos_token_ids:
                finish = "eos"
                break
            if token == call_open:
                open_at = len(tokens) - 1
            elif token == response_open:
                self_responses += 1
            logits = step(token)
            forced = (open_at is not None and token != call_close
                      and len(tokens) - 1 - open_at >= config.max_call_tokens)
            if forced and len(tokens) >= config.max_new_tokens:
                continue
            if forced:
                tokens.append(call_close)
                inserted.append(True)
                logits = step(call_close)
            if token == call_close or forced:
                room = config.max_new_tokens - len(tokens)
                for response_token in responder.respond(tokens, open_at, len(tokens) - 1, room):
                    tokens.append(response_token)
                    inserted.append(True)
                    logits = step(response_token)
                open_at = None
    timing["total_s"] = time.monotonic() - start
    timing["head_s"] = responder.head_seconds
    timing["decode_s"] = timing["total_s"] - timing["prefill_s"] - timing["head_s"]
    timing["tokens_per_s"] = len(tokens) / timing["decode_s"] if timing["decode_s"] > 0 else None
    return DecodeResult(tokens, inserted, responder.calls, finish, timing, self_responses)


def segment_generate(engine_generate, prompt_ids, tokenizer, heads, config, context):
    """Decode with an engine that stops on token ids: engine_generate(ids, max_tokens, stop_token_ids) -> new ids.

    The engine must return its stop token as the last id when it stops on one (vllm_engine below ensures this).
    Stops on <tool_call> too, so an open call gets at most max_call_tokens tokens, as in headcall_generate."""
    responder = _Responder(tokenizer, heads, config)
    call_open, call_close = responder.ids[CALL_OPEN], responder.ids[CALL_CLOSE]
    heads.begin(context)
    tokens, inserted, finish, start, engine_seconds = [], [], None, time.monotonic(), 0.0
    stops = [call_open, call_close] + list(config.eos_token_ids)
    open_at = None

    def answer():
        response = responder.respond(tokens, open_at, len(tokens) - 1, config.max_new_tokens - len(tokens))
        tokens.extend(response)
        inserted.extend([True] * len(response))

    while finish is None:
        room = config.max_new_tokens - len(tokens)
        if room <= 0:
            finish = "max_new_tokens"
            break
        budget = room if open_at is None else min(room, config.max_call_tokens - (len(tokens) - 1 - open_at))
        tick = time.monotonic()
        new = list(engine_generate(list(prompt_ids) + tokens, budget, stops))[:budget]
        engine_seconds += time.monotonic() - tick
        tokens.extend(new)
        inserted.extend([False] * len(new))
        last = new[-1] if new else None
        if last is None:
            finish = "engine_stop"
        elif last in config.eos_token_ids:
            finish = "eos"
        elif last == call_open:
            open_at = len(tokens) - 1
        elif last == call_close:
            answer()
            open_at = None
        elif open_at is not None and len(tokens) - 1 - open_at >= config.max_call_tokens:
            if len(tokens) >= config.max_new_tokens:
                finish = "max_new_tokens"
                break
            tokens.append(call_close)
            inserted.append(True)
            answer()
            open_at = None
        elif len(tokens) >= config.max_new_tokens:
            finish = "max_new_tokens"
        else:
            finish = "engine_stop"
    total = time.monotonic() - start
    timing = {"prefill_s": None, "decode_s": engine_seconds, "head_s": responder.head_seconds, "total_s": total,
              "tokens_per_s": len(tokens) / engine_seconds if engine_seconds > 0 else None}
    self_responses = sum(1 for t, i in zip(tokens, inserted) if not i and t == responder.ids[RESPONSE_OPEN])
    return DecodeResult(tokens, inserted, responder.calls, finish, timing, self_responses)


def hf_engine(model, batch):
    """engine_generate over HF generate that re-prefills prompt + history for every segment (slow, simple, and
    free of cache continuation; the reference that headcall_generate is checked against)."""
    import torch
    from .phase1 import GeometryContext, split_geometry

    batch, geometry_features = split_geometry(batch)
    prompt_length = batch["input_ids"].shape[1]

    def generate(ids, max_tokens, stop_token_ids):
        feed = {k: v for k, v in batch.items() if k not in ("input_ids", "attention_mask", "mm_token_type_ids", "labels")
            and not k.startswith("aux_")}
        feed["input_ids"] = torch.tensor([ids], dtype=batch["input_ids"].dtype, device=batch["input_ids"].device)
        feed["attention_mask"] = torch.ones_like(feed["input_ids"])
        if "mm_token_type_ids" in batch:
            mm = batch["mm_token_type_ids"]
            feed["mm_token_type_ids"] = torch.cat([mm, mm.new_zeros((1, len(ids) - prompt_length))], dim=1)
        core = _language_core(model)
        if core is not None:
            core.rope_deltas = None
        with torch.inference_mode(), GeometryContext(model, geometry_features):  # one prefill vision forward
            out = model.generate(**feed, do_sample=False, max_new_tokens=max_tokens, eos_token_id=list(stop_token_ids),
                                 pad_token_id=stop_token_ids[-1], temperature=None, top_p=None, top_k=None)
        return out[0, len(ids):].tolist()

    return generate


def vllm_engine(llm, multi_modal_data=None, temperature=0.0, seed=17):
    """engine_generate over a vllm.LLM (prefix caching recommended; untested here: vLLM is not installed on CPU)."""
    from vllm import SamplingParams

    def generate(ids, max_tokens, stop_token_ids):
        prompt = {"prompt_token_ids": ids}
        if multi_modal_data is not None:
            prompt["multi_modal_data"] = multi_modal_data
        params = SamplingParams(max_tokens=max_tokens, temperature=temperature, seed=seed,
                                stop_token_ids=stop_token_ids, skip_special_tokens=False)
        output = llm.generate([prompt], params, use_tqdm=False)[0].outputs[0]
        new = list(output.token_ids)
        if output.finish_reason == "stop" and output.stop_reason in stop_token_ids and (
                not new or new[-1] != output.stop_reason):
            new.append(output.stop_reason)
        return new

    return generate
