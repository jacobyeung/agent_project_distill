"""Head-call decoding inside the student benchmark evaluator (a1p student_pilot/benchmark_eval/generate.py).

The evaluator's GPU branch runs model.generate(**device_batch, generation_config=generation_config) and builds
{'tokens', 'raw', 'display'} from the new tokens. headcall_generator returns a callable with that result shape under
the evaluator's fixed decoding (greedy, batch 1, max_new_tokens from the effective config, native EOS ids), so its
finish check (last token an EOS id, or exactly max_new_tokens tokens) holds by construction. max_new_tokens counts
inserted response tokens too, so a run with calls never exceeds the evaluator's output cap.

Patch for generate.py (GPU branch, around `generated = model.generate(...)`):

    if headcall is not None:
        result = headcall(device_batch, key=qid)
        write_once(output / 'headcalls' / f'{safe_id(qid)}.json', result.pop('headcall'), artifact_root, paper)
    else:
        with torch.inference_mode():
            generated = model.generate(**device_batch, generation_config=generation_config)
        ...

with `headcall = headcall_generator(model, processor, heads, generation_config.to_dict())` built once after the model
loads. The head-call record goes to a sidecar, so the receipt schema and the scorer stay unchanged. Benchmark runs use
the student's own heads only (Phase1Heads); OracleHeads reads GT and belongs to held-out training-scene validation.
"""
import re

from .decode import DecodeConfig, headcall_generate
from .heads import HeadOutputPool, RecordingHeads, ShuffledHeads
from .protocol import exchanges


def headcall_generator(model, processor, heads, effective, max_calls=80, max_call_tokens=128, video_token_id=None,
                       carriers=None, allow_lenient=True):
    """carriers: insert phase 1's 16 camera carriers into each prompt (default: when the heads need them or the
    model carries phase 1's camera heads, whose training prompts always hold them). allow_lenient=False answers a
    call that needs a parser repair with an error instead of executing it; either way the record separates strict
    from lenient calls, and summaries report strict accuracy apart (evaluate_head_vs_shuffled)."""
    if carriers is None:
        from .phase1 import camera_heads
        carriers = bool(getattr(heads, "needs_carriers", False) or getattr(getattr(heads, "base", None),
                                                                           "needs_carriers", False)
                        or camera_heads(model) is not None)
    if effective.get("do_sample"):
        raise ValueError("The evaluator decodes greedily")
    if effective.get("num_beams", 1) != 1 or effective.get("num_return_sequences", 1) != 1:
        raise ValueError("Head-call decoding supports one greedy beam")
    eos = effective["eos_token_id"]
    eos = list(eos) if isinstance(eos, (list, tuple)) else [eos]
    config = DecodeConfig(eos, max_new_tokens=effective["max_new_tokens"], max_calls=max_calls,
                          max_call_tokens=max_call_tokens, allow_lenient=allow_lenient)
    tokenizer = processor.tokenizer
    if video_token_id is None:
        video_token_id = getattr(processor, "video_token_id", None)

    def generate(batch, key=None, row=None):
        if carriers and "aux_camera_positions" not in batch:
            from .phase1 import insert_carriers
            batch = insert_carriers(dict(batch), tokenizer)
        result = headcall_generate(model, batch, tokenizer, heads, config, key=key, row=row,
                                   video_token_id=video_token_id)
        tokens = result.tokens
        return {"tokens": tokens, "raw": tokenizer.decode(tokens, skip_special_tokens=False),
                "display": tokenizer.decode(tokens, skip_special_tokens=True), "headcall": record(result)}

    generate.allow_lenient = allow_lenient
    return generate


def downstream_usage(text):
    """For every exchange, whether a value it yields is cited after its response: one of its own numeric literals,
    or a value the trace derives from it (headcall.derive) as printed: a depth response's 3D point (unprojected with
    the latest earlier pose response of that frame, the 'point (x, y, z)' text the traces print), or a pose
    response's ego-motion against an earlier pose response (the forward and lateral metres). Returns a list of
    {'index', 'name', 'used', 'how'}."""
    from . import derive as D
    from .geometry import unproject
    from .protocol import parse_call, parse_response

    found = exchanges(text)
    poses, usage = [], []
    for index, (_, _, end, body, response) in enumerate(found):
        parsed = parse_call(body)
        name = parsed.call.name if parsed.valid else None
        after = text[end:]
        how = None
        if response:
            if any(num in after for num in re.findall(r"-?\d+\.\d+", response)):
                how = "literal"
            value = parse_response(name, response) if name else None
            if how is None and name == "depth" and value is not None:
                pose = next((p for f, p in reversed(poses) if f == parsed.call.frame), None)
                if pose is not None and pose.view_deg is not None:
                    point = D.point_text(D.printed_point(unproject(parsed.call.point, value, pose)))
                    if point in after:
                        how = "derived_point"
            if how is None and name == "pose" and value is not None:
                for _, earlier in poses:
                    forward, right, _, _ = D.ego_motion(earlier, value)
                    if any("%s m %s" % (D.P.num(abs(v)), word) in after
                           for v, word in ((forward, "forward" if forward >= 0 else "backward"),
                                           (right, "right" if right >= 0 else "left"))):
                        how = "derived_motion"
                        break
            if name == "pose" and value is not None:
                poses.append((parsed.call.frame, value))
        usage.append({"index": index, "name": name, "used": how is not None, "how": how})
    return usage


def response_value_used_downstream(text):
    """True if any exchange's value is cited after its response, literally or through a value the trace derives
    from it (downstream_usage)."""
    return any(item["used"] for item in downstream_usage(text))


def extract_final_answer(text):
    """Extract the model's final answer after </think> or inside <answer>...</answer>."""
    ans_match = re.search(r"<answer>\s*(.*?)\s*</answer>", text, re.S | re.I)
    if ans_match:
        return ans_match.group(1).strip()
    if "</think>" in text:
        tail = text.split("</think>", 1)[1]
    else:
        tail = text
    for token in ("<|im_end|>", "<|endoftext|>"):
        tail = tail.replace(token, "")
    return tail.strip()


def evaluate_head_vs_shuffled(model, processor, heads, samples, effective, grader=None, max_calls=80,
                              max_call_tokens=128, seed=31, allow_lenient=True):
    """Run the head-vs-shuffled ablation on `samples` and return Acc(head) - Acc(shuffled) plus call metrics.

    Pass 1 decodes every sample with the heads and records each value they answer. Pass 2 decodes every sample again
    with ShuffledHeads over those records: each call gets a real head output of another sample (another scene when
    rows carry scenes), so the control differs only in which sample's head values the trace receives.
    Each item in `samples` is a dict with `batch` (processor tensors), optional `key`, optional `row`, and optional
    `gold` (expected final answer). `grader(pred, gold, sample)` defaults to exact normalized string equality."""
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('headcall/eval_hook.py:evaluate_head_vs_shuffled')
    from .phase1 import camera_heads
    pool = HeadOutputPool()
    recorder = RecordingHeads(heads, pool)
    carriers = bool(getattr(heads, "needs_carriers", False)) or camera_heads(model) is not None
    gen_head = headcall_generator(model, processor, recorder, effective, max_calls=max_calls,
                                  max_call_tokens=max_call_tokens, carriers=carriers, allow_lenient=allow_lenient)
    if grader is None:
        grader = lambda pred, gold, sample: str(pred).strip().lower() == str(gold).strip().lower()
    head_outputs = []
    for idx, sample in enumerate(samples):
        key = sample.get("key", "s%d" % idx)
        head_outputs.append(gen_head(sample["batch"], key=key, row=sample.get("row")))
    shuffled = ShuffledHeads(pool, seed=seed)
    gen_shuf = headcall_generator(model, processor, shuffled, effective, max_calls=max_calls,
                                  max_call_tokens=max_call_tokens, carriers=carriers,
                                  allow_lenient=allow_lenient)  # the same prompts

    per_sample = []
    head_correct, shuf_correct, changed, used_downstream = 0, 0, 0, 0
    total_calls, valid_calls, strict_calls, head_correct_strict = 0, 0, 0, 0
    for idx, sample in enumerate(samples):
        key = sample.get("key", "s%d" % idx)
        row = sample.get("row")
        out_h = head_outputs[idx]
        out_s = gen_shuf(sample["batch"], key=key, row=row)
        ans_h = extract_final_answer(out_h["display"])
        ans_s = extract_final_answer(out_s["display"])
        if ans_h != ans_s:
            changed += 1
        used = response_value_used_downstream(out_h["raw"])
        if used:
            used_downstream += 1
        summary = out_h["headcall"]["summary"]
        total_calls += summary["calls"]
        valid_calls += summary["valid_calls"]
        strict_calls += summary["strict_calls"]
        gold = sample.get("gold")
        if gold is None and row is not None:
            gold = row.get("answer")
        ok_h = bool(grader(ans_h, gold, sample)) if gold is not None else None
        ok_s = bool(grader(ans_s, gold, sample)) if gold is not None else None
        lenient = summary["valid_calls"] - summary["strict_calls"]
        if ok_h:
            head_correct += 1
            head_correct_strict += int(lenient == 0)
        if ok_s:
            shuf_correct += 1
        per_sample.append({
            "key": key,
            "head_answer": ans_h,
            "shuffled_answer": ans_s,
            "gold": gold,
            "head_correct": ok_h,
            "shuffled_correct": ok_s,
            "answer_changed": ans_h != ans_s,
            "used_downstream": used,
            "calls": summary["calls"],
            "valid_calls": summary["valid_calls"],
            "strict_calls": summary["strict_calls"],
            "lenient_calls": lenient,
        })
    n = max(1, len(samples))
    scored = sum(1 for s in per_sample if s["gold"] is not None)
    denom = float(max(1, scored))
    head_acc = head_correct / denom if scored else None
    shuf_acc = shuf_correct / denom if scored else None
    delta = (head_acc - shuf_acc) if scored else None
    return {
        "shuffle_pool_values": len(pool),
        "n_samples": len(samples),
        "n_scored": scored,
        # strict accuracy counts a correct answer only when every call it made parsed strictly (the format the
        # training rows teach); head_acc also credits answers whose calls needed a lenient repair
        "head_acc_strict": head_correct_strict / denom if scored else None,
        "head_lenient_call_count": valid_calls - strict_calls,
        "allow_lenient": all(getattr(g, "allow_lenient", True) for g in (gen_head, gen_shuf)),
        "head_acc": head_acc,
        "shuffled_acc": shuf_acc,
        "acc_delta_head_minus_shuffled": delta,
        "answer_changed_rate": changed / float(n),
        "head_used_downstream_rate": used_downstream / float(n),
        "head_valid_call_rate": valid_calls / float(max(1, total_calls)),
        "head_strict_call_rate": strict_calls / float(max(1, total_calls)),
        "per_sample": per_sample,
    }


def record(result):
    """JSON-ready account of one decode: summary, timing, every call, and where inserted tokens sit."""
    calls = []
    for c in result.calls:
        parsed = c.parse
        call = parsed.call if parsed is not None else None
        calls.append({"index": c.index, "open_token": c.open_token, "close_token": c.close_token, "body": c.body,
                      "call": {"name": call.name, "frame": call.frame,
                               "point": list(call.point) if call.point else None} if call else None,
                      "valid": c.error_code is None, "strict": bool(parsed is not None and parsed.strict),
                      "repairs": list(parsed.repairs) if parsed is not None else [],
                      "extra_keys": list(parsed.extra) if parsed is not None else [],
                      "response": c.response, "error_code": c.error_code, "head_seconds": c.head_seconds,
                      "inserted_tokens": c.inserted_tokens})
    spans, start = [], None
    for i, flag in enumerate(result.inserted + [False]):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            spans.append([start, i])
            start = None
    return {"schema": "headcall-decode-v1", "summary": result.summary(), "calls": calls, "inserted_spans": spans}
