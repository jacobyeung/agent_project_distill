"""Training plumbing for head-call traces.

mask_tool_responses   no LM loss on any token from <tool_response> through </tool_response>; the loop inserts those
                      tokens at decode time, so the model never has to produce them. </tool_call> and the text after
                      </tool_response> stay supervised. Works on token ids after any trainer's own tokenization.
encode_prompt_batch   a processor batch with phase 1's 16 camera carriers inserted (camera_targets.insert_carriers),
                      then the target appended and masked: the prompt the heads were trained to read.
ScheduledSampler      before tokenization, replaces some GT responses with the heads' answers and re-renders every
                      derived value after them from the row's target_template (headcall.derive), so no GT text
                      follows a swapped response. A swap outside the tolerance gate (depth, position, heading, pitch,
                      roll, view) keeps its GT response, and a set of swaps whose derived decision misses the GT answer
                      is rejected whole.
head_query_targets    each row's queried points and frames with GT values, padded, for the heads' own losses.
"""
import hashlib
import math
import random

from . import derive as D
from .heads import HeadContext, value_of_record
from .protocol import (CALL_CLOSE, CALL_OPEN, RESPONSE_CLOSE, RESPONSE_OPEN, Call, CallError, exchanges, format_value,
                       parse_call)

IGNORE = -100
DEFAULT_MAX_DEPTH_QUERIES = 80
DEFAULT_MAX_POSE_QUERIES = 80


def tool_token_ids(tokenizer):
    ids = {}
    for text in (CALL_OPEN, CALL_CLOSE, RESPONSE_OPEN, RESPONSE_CLOSE):
        encoded = tokenizer.encode(text, add_special_tokens=False)
        if len(encoded) != 1:
            raise ValueError("%s is not a single token" % text)
        ids[text] = encoded[0]
    return ids


def mask_tool_responses(input_ids, labels, ids, allow_truncated=False):
    """Labels with IGNORE on every tool-response token; raises on a response that does not follow </tool_call>,
    a nested response, a tool token inside a response, or an unterminated response. allow_truncated=True (only for a
    sequence that right-truncation cut, see encode_example) masks a trailing open response to the end instead."""
    input_ids = [int(t) for t in input_ids]
    is_tensor = hasattr(labels, "clone")
    out = labels.clone() if is_tensor else list(labels)
    if len(out) != len(input_ids):
        raise ValueError("input_ids and labels differ in length")
    r_open, r_close = ids[RESPONSE_OPEN], ids[RESPONSE_CLOSE]
    c_open, c_close = ids[CALL_OPEN], ids[CALL_CLOSE]
    inside = False
    for i, token in enumerate(input_ids):
        if token == r_open:
            if inside:
                raise ValueError("nested <tool_response> at token %d" % i)
            if i == 0 or input_ids[i - 1] != c_close:
                raise ValueError("<tool_response> at token %d does not follow </tool_call>" % i)
            inside = True
        elif inside and token in (c_open, c_close):
            raise ValueError("tool-call token inside a response at token %d" % i)
        elif token == r_close and not inside:
            raise ValueError("</tool_response> without <tool_response> at token %d" % i)
        if inside:
            out[i] = IGNORE
            if token == r_close:
                inside = False
    if inside and not allow_truncated:
        raise ValueError("unterminated <tool_response>")
    return out


def encode_example(tokenizer, prompt_ids, target_text, ids=None, eos_text="<|im_end|>", max_seq_len=None,
                   allow_truncated=True, require_carriers=True):
    """prompt ids + target ids with labels: IGNORE on the prompt and on tool responses. With require_carriers the
    prompt must already hold phase 1's 16 camera carriers (encode_prompt_batch inserts them)."""
    ids = ids or tool_token_ids(tokenizer)
    if require_carriers:
        from .phase1 import check_carriers
        check_carriers(prompt_ids, tokenizer)
    target_ids = tokenizer.encode(target_text + eos_text, add_special_tokens=False)
    input_ids = list(prompt_ids) + target_ids
    labels = [IGNORE] * len(prompt_ids) + list(target_ids)
    truncated = max_seq_len is not None and len(input_ids) > max_seq_len
    if truncated:
        input_ids = input_ids[:max_seq_len]
        labels = labels[:max_seq_len]
    # an open response at the end is legitimate only where truncation cut the sequence; elsewhere it is bad data
    return input_ids, mask_tool_responses(input_ids, labels, ids, allow_truncated=allow_truncated and truncated)


def encode_prompt_batch(batch, tokenizer, target_text, eos_text="<|im_end|>", max_seq_len=None, allow_truncated=True):
    """A single-row processor batch (prompt only) -> the training batch: carriers inserted after each temporal
    group's video tokens (phase 1's insert_carriers, which also returns aux_camera_positions), then the target tokens
    appended with tool-response masking. Every per-token tensor of the batch is extended to the new length."""
    import torch
    from .phase1 import insert_carriers

    prompt = insert_carriers(dict(batch), tokenizer)
    prompt_ids = prompt["input_ids"][0].tolist()
    input_ids, labels = encode_example(tokenizer, prompt_ids, target_text, eos_text=eos_text, max_seq_len=max_seq_len,
                                       allow_truncated=allow_truncated)
    added = len(input_ids) - len(prompt_ids)
    out = dict(prompt)
    out["input_ids"] = torch.tensor([input_ids], dtype=prompt["input_ids"].dtype)
    out["labels"] = torch.tensor([labels], dtype=torch.long)
    if "attention_mask" in prompt:
        out["attention_mask"] = torch.cat([prompt["attention_mask"], prompt["attention_mask"].new_ones((1, added))], 1)
    if "mm_token_type_ids" in prompt:
        out["mm_token_type_ids"] = torch.cat([prompt["mm_token_type_ids"],
                                              prompt["mm_token_type_ids"].new_zeros((1, added))], 1)
    return out


class Schedule(object):
    """p(step): start_p until start_step, linear to end_p at end_step, then end_p."""

    def __init__(self, start_p=0.0, end_p=0.5, start_step=0, end_step=1000):
        self.start_p, self.end_p, self.start_step, self.end_step = start_p, end_p, start_step, end_step

    def __call__(self, step):
        if step <= self.start_step:
            return self.start_p
        if step >= self.end_step:
            return self.end_p
        fraction = (step - self.start_step) / float(self.end_step - self.start_step)
        return self.start_p + fraction * (self.end_p - self.start_p)


class ScheduledSampler(object):
    """Replaces GT responses in a row's target with the heads' answers when within tolerance of GT, and re-renders
    the derived text after them.

    The choice of calls is a pure function of (seed, qid, step), so replays and resumed runs see the same targets.
    A call the heads cannot answer, or whose answer misses the tolerance gate, keeps its GT response. The target is
    then rendered from target_template with the mixed responses (headcall.derive): every derived point, movement
    and angle follows the responses actually shown. When the re-derived decision misses the GT answer, every swap of
    that row is rejected (the row keeps its GT target). A row without target_template is never swapped."""

    def __init__(self, schedule, heads, seed=17, depth_rel_tol=0.10, depth_abs_tol_m=0.20, pose_pos_tol_m=0.25,
                 pose_heading_tol_deg=10.0, pose_pitch_tol_deg=10.0, pose_roll_tol_deg=10.0, pose_view_tol_deg=10.0,
                 tolerance_gate=True):
        self.schedule, self.heads, self.seed = schedule, heads, seed
        self.depth_rel_tol, self.depth_abs_tol_m = float(depth_rel_tol), float(depth_abs_tol_m)
        self.pose_pos_tol_m, self.pose_heading_tol_deg = float(pose_pos_tol_m), float(pose_heading_tol_deg)
        self.pose_pitch_tol_deg, self.pose_roll_tol_deg = float(pose_pitch_tol_deg), float(pose_roll_tol_deg)
        self.pose_view_tol_deg = float(pose_view_tol_deg)
        self.tolerance_gate = bool(tolerance_gate)
        self.attempted_swaps = self.accepted_swaps = self.rejected_swaps = 0
        self.rejected_rows = self.untemplated_rows = 0

    def acceptance_rate(self):
        if self.attempted_swaps <= 0:
            return 1.0
        return self.accepted_swaps / float(self.attempted_swaps)

    def within_tolerance(self, record, value):
        if not self.tolerance_gate:
            return True
        gt = value_of_record(record)
        if record["name"] == "depth":
            err = abs(float(value) - gt)
            return err / max(gt, 1e-6) <= self.depth_rel_tol or err <= self.depth_abs_tol_m
        pos_err = math.sqrt(sum((float(a) - float(b)) ** 2 for a, b in zip(value.position, gt.position)))

        def angle(a, b):
            return abs(((float(a) - float(b) + 180.0) % 360.0) - 180.0)
        if (pos_err > self.pose_pos_tol_m or angle(value.heading_deg, gt.heading_deg) > self.pose_heading_tol_deg
                or abs(value.pitch_deg - gt.pitch_deg) > self.pose_pitch_tol_deg
                or angle(value.roll_deg, gt.roll_deg) > self.pose_roll_tol_deg):
            return False
        if (gt.view_deg is None) != (value.view_deg is None):
            return False
        return gt.view_deg is None or all(abs(a - b) <= self.pose_view_tol_deg for a, b in zip(value.view_deg, gt.view_deg))

    def chosen(self, row, step):
        """The call indices this (row, step) would swap: a pure function of (seed, qid, step)."""
        records = row.get("head_calls") or []
        p = self.schedule(step)
        if not records or p <= 0:
            return []
        text = "%s|%s|%s" % (self.seed, row.get("qid"), step)
        rng = random.Random(int(hashlib.sha256(text.encode()).hexdigest()[:16], 16))
        return [i for i in range(len(records)) if rng.random() < p]

    def __call__(self, row, step, context=None):
        records = row.get("head_calls") or []
        p = self.schedule(step)
        if not records or p <= 0:
            return row, []
        template, derived = row.get("target_template"), row.get("head_derived")
        if template is None or derived is None:
            self.untemplated_rows += 1
            return row, []
        found = exchanges(row["target"])
        if len(found) != len(records):
            raise ValueError("target exchanges differ from head_calls for %s" % row.get("qid"))
        chosen = self.chosen(row, step)
        if not chosen:
            return row, []
        self.heads.begin(context or HeadContext([], key=row.get("qid"), row=row))
        responses = [r["response"] for r in records]
        replaced = []
        addressing = getattr(self.heads, "addressing", "frame")
        for i in chosen:
            self.attempted_swaps += 1
            parsed = parse_call(found[i][3], addressing=addressing)
            try:
                value = self.heads.answer(parsed.call)
            except CallError:
                self.rejected_swaps += 1
                continue
            if not self.within_tolerance(records[i], value):
                self.rejected_swaps += 1
                continue
            responses[i] = format_value(parsed.call.name, value)
            replaced.append(i)
        if replaced:
            try:
                texts, results = D.evaluate(derived, D.values_of([r["name"] for r in records], responses))
                supported = D.answer_supported(row, derived, results)
            except ValueError:
                supported = False
            if not supported:
                self.rejected_rows += 1
                self.rejected_swaps += len(replaced)
                return dict(row, head_calls_replaced=[], head_calls_attempted=chosen,
                            head_calls_acceptance_rate=0.0), []
            self.accepted_swaps += len(replaced)
            target = D.render(template, responses, texts)
        else:
            target = row["target"]
        new = dict(row)
        new["target"] = target
        new["head_calls_replaced"] = replaced
        new["head_calls_attempted"] = chosen
        new["head_calls_acceptance_rate"] = len(replaced) / float(len(chosen))
        return new, replaced


def prompt_head_context(model, prompt_batch, key=None, row=None, video_token_id=None):
    """HeadContext from a no-grad prefill over the prompt only (scheduled sampling with trained heads)."""
    import torch

    with torch.no_grad():
        out = model(**prompt_batch, use_cache=False, output_hidden_states=True)
    return HeadContext(prompt_batch["input_ids"][0].tolist(), out.hidden_states, video_token_id,
                       prompt_batch.get("video_grid_thw"), key, row)


def head_query_targets(row, max_depth=DEFAULT_MAX_DEPTH_QUERIES, max_pose=DEFAULT_MAX_POSE_QUERIES):
    """The row's queried depth points and pose frames with GT values, deduplicated and padded (torch tensors).
    pose columns: x, y, z (m), heading, pitch, roll (deg), view horizontal, view vertical (deg; pose_view_mask)."""
    import torch

    depth, pose, seen = [], [], set()
    for record in row.get("head_calls") or []:
        point = tuple(record["point"]) if record.get("point") is not None else None
        key = (record["name"], record["frame"], point)
        if key in seen:
            continue
        seen.add(key)
        value = value_of_record(record)
        if record["name"] == "depth":
            depth.append((record["frame"], point, value))
        else:
            view = list(value.view_deg) if value.view_deg else [0.0, 0.0]
            pose.append((record["frame"], list(value.position) + [value.heading_deg, value.pitch_deg, value.roll_deg]
                         + view, value.view_deg is not None))
    if len(depth) > max_depth or len(pose) > max_pose:
        raise ValueError("row %s has more head queries than the caps (%d depth, %d pose)"
                         % (row.get("qid"), len(depth), len(pose)))
    out = {"depth_frame": torch.ones(max_depth, dtype=torch.long),
           "depth_point": torch.zeros(max_depth, 2, dtype=torch.long),
           "depth_m": torch.ones(max_depth), "depth_mask": torch.zeros(max_depth, dtype=torch.bool),
           "pose_frame": torch.ones(max_pose, dtype=torch.long), "pose": torch.zeros(max_pose, 8),
           "pose_mask": torch.zeros(max_pose, dtype=torch.bool), "pose_view_mask": torch.zeros(max_pose, dtype=torch.bool)}
    for i, (frame, point, value) in enumerate(depth):
        out["depth_frame"][i], out["depth_point"][i], out["depth_m"][i], out["depth_mask"][i] = frame, \
            torch.tensor(point), value, True
    for i, (frame, value, has_view) in enumerate(pose):
        out["pose_frame"][i], out["pose"][i], out["pose_mask"][i] = frame, torch.tensor(value), True
        out["pose_view_mask"][i] = has_view
    return out


def phase1_point_depth_targets(row, points_per_frame=64):
    """The row's depth queries in phase 1's label layout (point_depth uv [16, K, 2], depth [16, K], mask [16, K]),
    so phase 1's own point-depth loss can supervise the points the trace queries. Same first-hit GT as the bank."""
    import numpy as np

    uv = np.zeros((16, points_per_frame, 2), dtype=np.float32)
    gt = np.zeros((16, points_per_frame), dtype=np.float32)
    mask = np.zeros((16, points_per_frame), dtype=bool)
    used = [0] * 16
    for record in row.get("head_calls") or []:
        if record["name"] != "depth":
            continue
        group = record["frame"] // 2 - 1
        if used[group] >= points_per_frame:
            raise ValueError("more depth queries in frame %d than points_per_frame" % record["frame"])
        k = used[group]
        uv[group, k], gt[group, k], mask[group, k] = record["point"], record["gt"]["depth_m"], True
        used[group] += 1
    return {"uv": uv.tolist(), "depth": gt.tolist(), "mask": mask.tolist()}


def collate_head_queries(items):
    import torch

    return {key: torch.stack([item[key] for item in items]) for key in items[0]}


def strip_calls_target(target):
    """The no-call ablation of a converted target: every call and response removed (line text kept)."""
    from .protocol import strip_exchanges
    return strip_exchanges(target)


def call_of(record):
    return Call(record["name"], record["frame"], tuple(record["point"]) if record.get("point") else None)


def swap_targets(row, responses):
    """The row's target with these response texts (one per call) and every derived value re-rendered."""
    texts, _ = D.evaluate(row["head_derived"], D.values_of([r["name"] for r in row["head_calls"]], responses))
    return D.render(row["target_template"], responses, texts)
