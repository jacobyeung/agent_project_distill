#!/usr/bin/env python
"""r1313 answer-free training runner around the native Gemini SPLIT carrier.

The runner preserves raw planner and verifier telemetry and writes the normal
prompt, dataset snapshot, trace, and result artifacts.
"""

import argparse
import native_google_telemetry as native_google
from reference_native_tool_telemetry import native_projection
from training_assets import enter_episode
import training_policy as reference_policy
import concurrent.futures
import hashlib
import importlib.util
import json
import os
import re
import socket
import sys
import threading
import time
from pathlib import Path
from nondeleting_lifecycle import retire_path
from training_publication import final_dir, publish_finalized_triple

PACKAGE_VERSION = "r1313_gemini_sanitized_historical_reference16k_v1"

_PACKAGE_DIR = Path(__file__).resolve().parent
_SCRIPT_DIR = str(_PACKAGE_DIR)
sys.path.insert(0, _SCRIPT_DIR)
from langchain_core.messages import HumanMessage, SystemMessage
from training_assets import bootstrap_runner
_LOCAL_CONTRACT, agent_mod = bootstrap_runner(_PACKAGE_DIR)
_message_to_dict = agent_mod._message_to_dict
_LOCAL_CONTRACT_PATH = Path(os.environ['R1313_CONTRACT_PATH'])
_FLOAT_RE = re.compile(r"-?\d+\.?\d*(?:[eE][+-]?\d+)?")
_SAM3_QUARANTINE = threading.Event()
_SELECTED_FRAMES_PATH = os.environ["R1313_SCENE_RECEIPT"]
def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _qid(row: dict) -> str:
    return str(row.get("id", f"{row['scene_name']}_{row['question_type']}"))


def _build_run_receipt(system_prompt, dataset_path, out_dir, category, workers, questions):
    from training_assets import episode_receipt
    return episode_receipt(system_prompt, questions, out_dir)


def _receipt_core(receipt) -> dict | None:
    """Resume identity is exact, including host and worker count."""
    if not isinstance(receipt, dict):
        return None
    return dict(receipt)


def _verifier_skip_events(trace_list):
    return [{"tool": row.get("tool"), "error_class": row.get("error_class")}
            for row in (trace_list or [])
            if isinstance(row, dict) and row.get("verifier_skipped")]


def _trace_dicts_with_provenance(all_messages, synthetic_messages):
    """Tag provider versus runner-created AI messages by object identity."""
    tagged = []
    for message in all_messages:
        row = _message_to_dict(message)
        if row.get("role") in ("ai", "assistant"):
            label = next(
                (candidate_label for candidate, candidate_label in synthetic_messages
                 if message is candidate),
                None,
            )
            row = dict(row)
            row["provenance"] = label or "provider"
        tagged.append(row)
    return tagged


def _served_models(trace_rows) -> list[str]:
    """Collect provider-reported planner response models for one episode."""
    values = set()
    for row in trace_rows:
        if not isinstance(row, dict) or row.get("provenance") != "provider":
            continue
        served = row.get("served_model")
        if not isinstance(served, dict):
            continue
        for value in served.values():
            if isinstance(value, str) and value:
                values.add(value)
    return sorted(values)


def _tool_vlm_responses(trace_list) -> list[dict]:
    """Preserve the provider-reported model for every direct tool-VLM response."""
    return [
        {
            "where": row.get("where"),
            "requested_model": row.get("model"),
            "provider_served_model": row.get("provider_served_model"),
        }
        for row in (trace_list or [])
        if isinstance(row, dict) and row.get("model_role") == "tool_vlm" and not row.get("event")
    ]


def _extract_python_stdout_fallback(messages, question: str = "") -> str | None:
    """r118: when step-cap fires and no <ANSWER> was emitted, scan
    backwards for the most recent `execute_python_code` ToolMessage and
    return the last numeric token in its stdout. Targets NA categories
    (abs_distance, counting, size, room_size) where the python print
    output IS the intended answer. Per r117 abs_distance subagent
    finding: ex_88 (0.727) had multiple cap-fire NO_ANSWERs whose
    python stdout already contained the correct distance.

    r126: unit-aware fallback for centimeter questions. r125 size
    subagent found 5/15 size NO_ANSWER cases where the agent's
    intermediate stdout printed Z-extents in METERS (e.g. 1.34 / 0.23)
    before its final `*100` cm-conversion line ran — the step cap
    truncated execution before that conversion. When the question
    text includes "centimeters" / "cm" and the scraped numeric is
    physically implausible as a centimeter answer (≤ 5.0 cm — too
    small for any common indoor object), assume it was reported in
    meters and multiply by 100. Pure post-hoc fix-up; never widens a
    number that was already in cm range.

    SALVAGE_NUMGUARD (r219): when set, this scraper is disabled entirely —
    it is the ONLY recovery path that parses an arbitrary trailing numeric
    from a tool output. Counting-collapse EA qid 96: the step cap fired
    while the last execute_python_code stdout was a 3D->pixel projection
    (`Chair B back: [363.82, 243.51]`) and this scraper committed pred=244
    (round(243.51)) as the count. Provenance-based recovery
    (_extract_tool_output_fallback: cluster counts / aggregate_aabbs_*
    extents / room area) and the salvage LLM commit are unaffected; if
    neither yields an answer, the question scores no-answer rather than a
    coordinate leak.
    """
    if os.environ.get("SALVAGE_NUMGUARD", "0") == "1":
        return None
    for m in reversed(messages):
        msg_type = getattr(m, "type", None) or m.__class__.__name__.lower()
        if msg_type not in ("tool", "toolmessage"):
            continue
        if getattr(m, "name", None) != "execute_python_code":
            continue
        content = getattr(m, "content", None)
        if isinstance(content, list):
            content = " ".join(
                c.get("text", "") if isinstance(c, dict) else str(c) for c in content
            )
        if not isinstance(content, str) or not content.strip():
            continue
        # Skip error frames — they aren't an "answer".
        low = content.lower()
        if "traceback" in low or low.startswith("error"):
            continue
        # r184: image-shape leak guard. size analysis (qid 484) found the
        # fallback grabbed an image dimension — the agent ran cv2.imread and
        # printed the shape `(640, 480, 3)`, and "480" is cm-plausible so it
        # won as the size answer over the real measured extent. Mask out any
        # numeric token that sits inside an image-shape tuple `(W, H, C)` with
        # C in 1..4, and skip stdout that is just an imread/.shape readout.
        _shape_spans = [(mm.start(), mm.end()) for mm in
                        re.finditer(r"\(\s*\d{2,4}\s*,\s*\d{2,4}\s*,\s*[1-4]\s*\)", content)]
        # r132: filter out word-internal matches (e.g. the `5` in
        # `min_xyz_p5`, the `3` in `pts3d_world`). Use finditer so we can
        # check the character immediately before each match — reject if
        # it's a letter or underscore. The original `_FLOAT_RE.findall`
        # in r118 swept these up, leading to q3548-style "fallback grabs
        # 5 from min_xyz_p5, rescales to 500 cm" garbage.
        nums = []
        for m_iter in _FLOAT_RE.finditer(content):
            i = m_iter.start()
            if i > 0 and (content[i-1].isalpha() or content[i-1] == "_"):
                continue
            if any(s <= i < e for s, e in _shape_spans):
                continue  # r184: image-shape dimension, not an answer
            nums.append(m_iter.group(0))
        if not nums:
            continue
        q_low = (question or "").lower()
        is_cm = ("centimeter" in q_low or " cm" in q_low or "(cm)" in q_low)
        # r132: for cm questions, walk backwards through stdout tokens with
        # a tiered preference: prefer the most-recent token already in the
        # cm-plausible range (5-1000); else the most-recent in the
        # meters-plausible range (0-5, rescaled below); else the last
        # token (existing fallback). r131 size subagent traced 3 q3548-
        # style failures to the fallback grabbing a frame-min Z-coord
        # (-1.55) or cluster Min-Z (-1.26) when recursion fired and the
        # agent's final `*100` print never ran. We additionally reject
        # negatives and huge values that are clearly coordinates / area
        # readings rather than length answers.
        if is_cm:
            cm_plausible = None      # 5 < v ≤ 1000 — accept as-is
            m_plausible  = None      # 0 < v ≤ 5    — rescale by 100
            for tok in reversed(nums):
                try:
                    v = float(tok)
                except (TypeError, ValueError):
                    continue
                if 5.0 < v <= 1000.0 and cm_plausible is None:
                    cm_plausible = tok
                elif 0.0 < v <= 5.0 and m_plausible is None:
                    m_plausible = tok
                if cm_plausible is not None:
                    break
            if cm_plausible is not None:
                raw = cm_plausible
            elif m_plausible is not None:
                v = float(m_plausible)
                rescaled = v * 100.0
                if rescaled == int(rescaled):
                    return f"{int(rescaled)}"
                return f"{rescaled:.4g}"
            else:
                # No plausible value anywhere in stdout — preserve original
                # behavior (last token) so we don't silently change other
                # categories' default fallback.
                raw = nums[-1]
            return raw

        # r137: Non-unit-tagged question — walk back, reject coordinate-leak
        # (|v| < 0.1, e.g. q4538 r136 pred=-0.0066 from a coordinate token
        # when the agent timed out). For "how many"/"count" questions also
        # reject negatives and force integer rounding.
        is_counting = any(k in q_low for k in ("how many", "count", "number of"))
        for tok in reversed(nums):
            try:
                v = float(tok)
            except (TypeError, ValueError):
                continue
            if abs(v) < 0.1:
                continue   # coordinate leak guard
            if is_counting:
                if v < 0:
                    continue
                rounded = int(round(v))
                if rounded < 1:
                    continue   # 0 isn't a valid count for "how many X"
                return str(rounded)
            return tok
        # All tokens rejected — preserve original behavior (avoid empty pred).
        return nums[-1]
    return None


def _extract_tool_output_fallback(messages, question: str = "", question_type: str = "") -> str | None:
    """r158: deterministic, noise-immune recovery of NA answers that were
    correctly COMPUTED into a tool output but never emitted because recursion /
    NO_ANSWER fired before the agent printed/answered. Complements
    _extract_python_stdout_fallback (which only scans execute_python_code stdout).
      - object_counting        -> last cluster_3d_points n_unique_centroids
                                  (else num_significant_clusters).
      - object_size_estimation -> last clean get_3d_points_in_mask/bbox
                                  extent_xyz_p90 (max axis; x100 if cm question).
    Only fires when the primary ANSWER and the stdout fallback both yielded
    nothing, so it cannot change a run that already produced an answer.
    """
    qt = question_type or ""
    q_low = (question or "").lower()
    is_cm = ("centimeter" in q_low or " cm" in q_low or "(cm)" in q_low)

    def _tool_msgs():
        for m in reversed(messages):
            mt = getattr(m, "type", None) or m.__class__.__name__.lower()
            if mt not in ("tool", "toolmessage"):
                continue
            name = getattr(m, "name", None)
            content = getattr(m, "content", None)
            if isinstance(content, list):
                content = " ".join(c.get("text", "") if isinstance(c, dict) else str(c) for c in content)
            if isinstance(content, str) and content.strip():
                yield name, content

    if qt == "object_counting":
        for name, content in _tool_msgs():
            if name != "cluster_3d_points":
                continue
            mm = re.search(r"['\"]n_unique_centroids['\"]\s*:\s*(\d+)", content)
            if mm:
                return str(int(mm.group(1)))
            mm = re.search(r"['\"]num_significant_clusters['\"]\s*:\s*(\d+)", content)
            if mm:
                return str(int(mm.group(1)))

    if qt == "object_size_estimation":
        # PLN-1 (r208): also parse aggregate_aabbs_robust (multi-frame robust
        # extent — the more authoritative estimate when present). Reverse walk
        # returns the most recent of either tool.
        for name, content in _tool_msgs():
            if name not in ("get_3d_points_in_mask", "get_3d_points_in_bbox",
                            "aggregate_aabbs_robust"):
                continue
            key = "extent_xyz" if name == "aggregate_aabbs_robust" else "extent_xyz_p90"
            mm = re.search(r"['\"]%s['\"]\s*:\s*\[([^\]]+)\]" % key, content)
            if not mm:
                continue
            try:
                vals = [abs(float(x)) for x in mm.group(1).split(",")]
            except (TypeError, ValueError):
                continue
            if not vals:
                continue
            v = max(vals)
            if is_cm:
                v *= 100.0
            return f"{int(round(v))}" if abs(v - round(v)) < 1e-9 else f"{v:.4g}"

    if qt == "room_size_estimation":
        # PLN-1 (r208): recover the alpha-shape floor area when the agent
        # computed it but never emitted an answer.
        for name, content in _tool_msgs():
            if name != "get_room_footprint_area":
                continue
            mm = re.search(r"['\"]area_m2['\"]\s*:\s*(-?\d+\.?\d*)", content)
            if not mm:
                continue
            try:
                v = float(mm.group(1))
            except (TypeError, ValueError):
                continue
            if v <= 0:
                continue
            return f"{int(round(v))}" if abs(v - round(v)) < 1e-9 else f"{v:.4g}"

    return None


def _extract_answer(messages, question: str = "") -> str | None:
    """Walk messages in reverse; return the first <ANSWER>…</ANSWER> payload found.

    r106: skip system / human messages (prompts contain a literal
    `<ANSWER>...</ANSWER>` example) and reject ellipsis / whitespace-only
    payloads. The earlier extractor reverse-walked into the system prompt
    whenever the assistant's final answer message had `content=[]`,
    matched the prompt's `<ANSWER>...</ANSWER>` example literal, and
    returned `pred="..."` — a phantom prediction that scored as
    universally wrong. Found by the r104 object_rel_direction_easy
    subagent (qid 2463) and corroborated by other categories.

    r118: if no <ANSWER> is emitted (step cap fires mid-computation),
    fall back to the last execute_python_code stdout numeric.
    """
    for m in reversed(messages):
        # Only trust assistant messages — prompts contain example literals.
        msg_type = getattr(m, "type", None) or m.__class__.__name__.lower()
        if msg_type not in ("ai", "aimessage", "assistant"):
            continue
        content = getattr(m, "content", None)
        if isinstance(content, list):
            content = " ".join(
                c.get("text", "") if isinstance(c, dict) else str(c) for c in content
            )
        if not isinstance(content, str):
            continue
        match = re.search(r"<ANSWER>\s*([^<]*?)\s*</ANSWER>", content, re.IGNORECASE)
        if not match:
            continue
        payload = match.group(1).strip()
        if payload in ("", "...", ".") or payload.replace(".", "").strip() == "":
            continue
        return payload
    return _extract_python_stdout_fallback(messages, question=question)


def _final_message_drops_orphan_tool(messages) -> bool:
    """Detect r104's silent-tool-drop pathology: most-recent assistant
    message contains BOTH a `<ANSWER>` text block AND a `tool_calls`
    list. LangGraph captures the answer and the tool_call never
    executes, so the agent commits to a guess. Returns True if the
    pattern is present so the caller can flag the trace.
    """
    for m in reversed(messages):
        msg_type = getattr(m, "type", None) or m.__class__.__name__.lower()
        if msg_type not in ("ai", "aimessage", "assistant"):
            continue
        content = getattr(m, "content", None)
        text = ""
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            text = " ".join(c.get("text", "") if isinstance(c, dict) else str(c)
                            for c in content)
        has_answer = bool(re.search(r"<ANSWER>\s*[^<]+?\s*</ANSWER>",
                                    text, re.IGNORECASE))
        tool_calls = getattr(m, "tool_calls", None) or []
        return has_answer and bool(tool_calls)
    return False


def _attempt_ledger_start(output: Path, qid: str, budget: int) -> tuple[Path, dict]:
    ledger = output / ".attempt_ledger" / qid
    ledger.mkdir(parents=True, exist_ok=True)
    prior = sorted(ledger.glob("attempt*.json"))
    receipt = {
        "schema": "req73-question-attempt-v4", "status": "started",
        "attempt_index": len(prior) + 1, "arm": _LOCAL_CONTRACT["arm"],
        "requested_model": _LOCAL_CONTRACT["model"]["requested_id"],
        "question_id": qid, "planner_output_budget_tokens": budget,
        "started_unix": time.time(),
    }
    path = ledger / f"attempt{receipt['attempt_index']:02d}.json"
    with path.open("x") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    return path, receipt


def _attempt_ledger_finish(path, receipt):
    target = path.with_name(path.stem + '_finished.json')
    with target.open('x') as handle:
        json.dump(receipt,handle,indent=2,sort_keys=True)
        handle.write('\n'); handle.flush(); os.fsync(handle.fileno())


def _build_initial_user_message(item: dict, selected_frames_sha256: str):
    user_prompt = f"Scene ID: {item['scene_name']}\nQuestion: {item['question']}\n"
    if item.get("options") and "Options:" not in item["question"]:
        user_prompt += "Options:\n" + "\n".join(item["options"]) + "\n"
        user_prompt += "Answer with the option's letter from the given choices directly."
    manifest = {
        "mode": "text_only_control", "frame_count": 0,
        "selected_frames_sha256": selected_frames_sha256, "frames": [],
    }
    return HumanMessage(content=user_prompt), manifest


def run_one(item, system_prompt, out_dir, recursion_limit=200, run_receipt=None):
    if _SAM3_QUARANTINE.is_set():
        raise RuntimeError("SAM3 daemon fleet is quarantined; episode admission refused")
    q_id = str(item.get("id", f"{item['scene_name']}_{item['question_type']}"))
    enter_episode(q_id)
    output = Path(out_dir).resolve(strict=True)
    live_file  = os.path.join(out_dir, f"trace_{q_id}_live.jsonl")
    if final_dir(output, q_id).exists():
        raise RuntimeError(f"r1313 finalized qid already exists: {q_id}")
    ledger_path, attempt_receipt = _attempt_ledger_start(
        output, q_id, agent_mod.PLANNER_MAX_OUTPUT_TOKENS)

    agent_mod.begin_r740_consumption_episode(q_id, out_dir)
    if os.path.exists(live_file):
        retire_path(live_file)

    user_message, visual_manifest = _build_initial_user_message(
        item, run_receipt["selected_frames_sha256"])
    initial_messages = [SystemMessage(content=system_prompt), user_message]
    all_messages = list(initial_messages)
    synthetic_messages = []
    from trace_archive import JournalList
    from training_assets import current_archive, tool_callbacks
    archive = current_archive()
    archive.event('initial_messages', [_message_to_dict(m) for m in initial_messages])
    trace_list = JournalList(archive, 'tool_telemetry')
    planner_attempts = JournalList(archive, 'planner_attempt')
    from provider_history import (new_discarded_history, capture_discarded_messages, clear_ordinary_history)
    discarded_message_history = new_discarded_history()

    app = agent_mod.get_agent_app()
    t0 = time.time()
    started_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0))
    error = None
    try:
        max_stream_attempts = max(1, int(os.environ.get("NV_RETRY_ATTEMPTS", "3")))
        for attempt in range(max_stream_attempts):
            retry_stream = False
            try:
                stream_iter = app.stream(
                    {"messages": initial_messages},
                    config={"callbacks": tool_callbacks(archive), "configurable": {
                                "trace_list": trace_list,
                                "llm_usage_list": trace_list,
                                "req73_planner_attempts": planner_attempts,
                            },
                            "recursion_limit": recursion_limit},
                )
            except Exception as e:
                if (agent_mod._is_transient_api_error(e)
                        and not agent_mod._is_rate_limit_429(e)
                        and attempt + 1 < max_stream_attempts):
                    error = None
                    capture_discarded_messages(
                        discarded_message_history, all_messages, synthetic_messages, planner_attempts,
                        recovery_ordinal=attempt + 1, reset_site='stream_creation',
                        serialize_segment=_trace_dicts_with_provenance)
                    all_messages = list(initial_messages)
                    clear_ordinary_history(trace_list)
                    synthetic_messages.clear()
                    if os.path.exists(live_file):
                        retire_path(live_file)
                    time.sleep(agent_mod._transient_api_backoff_seconds(e, attempt))
                    continue
                raise
            while True:
                try:
                    event = next(stream_iter)
                except StopIteration:
                    break
                except Exception as e:
                    if (agent_mod._is_transient_api_error(e)
                            and not agent_mod._is_rate_limit_429(e)
                            and attempt + 1 < max_stream_attempts):
                        error = None
                        capture_discarded_messages(
                            discarded_message_history, all_messages, synthetic_messages, planner_attempts,
                            recovery_ordinal=attempt + 1, reset_site='stream_iteration',
                            serialize_segment=_trace_dicts_with_provenance)
                        all_messages = list(initial_messages)
                        clear_ordinary_history(trace_list)
                        synthetic_messages.clear()
                        if os.path.exists(live_file):
                            retire_path(live_file)
                        time.sleep(agent_mod._transient_api_backoff_seconds(e, attempt))
                        retry_stream = True
                        break
                    if agent_mod._is_rate_limit_429(e):
                        raise
                    import traceback as _tb
                    error = f"stream error: {e}\n{_tb.format_exc()[:2000]}"
                    break
                node = list(event.keys())[0]
                payload = event[node]
                messages = payload.get('messages', []) if isinstance(payload, dict) else []
                archive.event('graph_step', {'node': node, 'messages': [_message_to_dict(m) for m in messages],
                    'state': {k:v for k,v in payload.items() if k != 'messages'} if isinstance(payload,dict) else payload})
                if isinstance(payload, dict) and "messages" in payload:
                    all_messages.extend(payload["messages"])
            if retry_stream:
                continue
            break
    except Exception as e:
        if agent_mod._is_rate_limit_429(e):
            raise
        import traceback as _tb
        error = f"outer error: {e}\n{_tb.format_exc()[:2000]}"

    # Distinguish primary (<ANSWER> tag) from r118 fallback so we can
    # measure how often the cap-fire fallback rescues an NA answer.
    terminal_cap = reference_policy.budget_terminal(planner_attempts)
    pred_primary = None
    for _m in reversed(all_messages[-1:] if terminal_cap else all_messages):
        _t = getattr(_m, "type", None) or _m.__class__.__name__.lower()
        if _t not in ("ai", "aimessage", "assistant"):
            continue
        _c = getattr(_m, "content", None)
        if isinstance(_c, list):
            _c = " ".join(c.get("text", "") if isinstance(c, dict) else str(c) for c in _c)
        if not isinstance(_c, str):
            continue
        _match = re.search(r"<ANSWER>\s*([^<]*?)\s*</ANSWER>", _c, re.IGNORECASE)
        if _match and _match.group(1).strip() not in ("", "...", "."):
            pred_primary = _match.group(1).strip()
            break
    # r119: fallback only fires for NA categories. Multiple-choice
    # categories expect a letter (A-D); the fallback returns the last
    # numeric token in execute_python_code stdout, which is meaningless
    # for MCA. r118 trace 5123 (route_planning) returned "0.54052734"
    # for a letter question — pure misfire. Restrict to NA only.
    _MCA_QTYPES = {
        "object_rel_direction_easy", "object_rel_direction_medium",
        "object_rel_direction_hard", "object_rel_distance",
        "route_planning", "obj_appearance_order",
        # VSTIBench MC types (re-applied per VSTIBENCH_RESULT.md mandatory wiring #1;
        # without these the 7 MC types fall through to the numeric salvage fallback at
        # the `not in _MCA_QTYPES` gate below — wrong for letter answers. Matches
        # run_experiment_r307.py:460-469. rv2 omitted them; rv3 fixes it.)
        "camera_movement_direction", "camera_obj_rel_dist_v1",
        "camera_obj_rel_dist_v2", "camera_obj_rel_dist_v3",
        "obj_obj_relative_pos_lr", "obj_obj_relative_pos_nf",
        "obj_obj_relative_pos_ud",
    }
    pred = None
    pred_source = "none"
    if pred_primary is not None:
        pred = pred_primary
        pred_source = "answer_tag"
    else:
        # PLN-2 (r208): the graph died without emitting <ANSWER> (recursion /
        # step-cap / stream error). ONE out-of-graph salvage commit over the
        # accumulated evidence, tool_choice='none' (NF-3). Fires for MCA too —
        # this replaces the old hard pred=None MCA default (8/500 guaranteed
        # losses in r206).
        if not terminal_cap and len(all_messages) > 2 and os.environ.get("DISABLE_SALVAGE", "0") != "1":
            try:
                salvage_prompt = HumanMessage(content=(
                    "[SYSTEM NOTIFICATION]: The session was interrupted before "
                    "you emitted an answer. Based ONLY on the evidence already "
                    "gathered above, commit to your best answer NOW. Emit ONLY "
                    "<ANSWER>...</ANSWER> — one option letter for multiple "
                    "choice, or one numeric value (no units, no prose) for "
                    "numeric questions."))
                _resp = agent_mod.salvage_commit(
                    list(all_messages) + [salvage_prompt], planner_attempts)
                all_messages.extend([salvage_prompt, _resp])
                terminal_cap = reference_policy.budget_terminal(planner_attempts)
                _c = getattr(_resp, "content", None)
                if isinstance(_c, list):
                    _c = " ".join(c.get("text", "") if isinstance(c, dict) else str(c) for c in _c)
                if isinstance(_c, str):
                    _m = re.search(r"<ANSWER>\s*([^<]*?)\s*</ANSWER>", _c, re.IGNORECASE)
                    if _m and _m.group(1).strip() not in ("", "...", "."):
                        pred = _m.group(1).strip()
                        pred_source = "salvage_commit"
            except Exception as _se:
                if error is None:
                    error = f"salvage error: {_se}"
        if not terminal_cap and pred is None and item.get("question_type") not in _MCA_QTYPES:
            # PLN-1 (r208): structured tool-output recovery FIRST — the stdout
            # regex almost never returns None, so it shadowed the structured
            # path (22/500 garbage scrapes in r206 while correct extents sat
            # in tool responses).
            pred = _extract_tool_output_fallback(all_messages,
                                                 question=item.get("question", ""),
                                                 question_type=item.get("question_type", ""))
            if pred is not None:
                pred_source = "tool_output_fallback"
            else:
                pred = _extract_python_stdout_fallback(all_messages, question=item.get("question", ""))
                if pred is not None:
                    pred_source = "python_stdout_fallback"
    if pred is not None and pred_source not in ("answer_tag", "salvage_commit"):
        # NF-1 (r208): evaluate_benchmark_v4 reads the last tool-call-free AI
        # message of the trace and never entry['pred'] — write the recovered
        # answer back as a synthetic final AI message so recovery actually
        # scores (r206: size 186/2379 recovered correctly, both scored null).
        from langchain_core.messages import AIMessage as _AIMsg
        recovery_message = _AIMsg(content=f"<ANSWER>{pred}</ANSWER>")
        all_messages.append(recovery_message)
        synthetic_messages.append((recovery_message, "runner_synthetic_recovery"))
    orphan_tool_drop = _final_message_drops_orphan_tool(all_messages)
    trace_rows = _trace_dicts_with_provenance(all_messages, synthetic_messages)
    planner_served_models = _served_models(trace_rows)
    tool_vlm_responses = _tool_vlm_responses(trace_list)
    all_served_models = sorted(
        set(planner_served_models)
        | {
            row["provider_served_model"]
            for row in tool_vlm_responses
            if isinstance(row.get("provider_served_model"), str)
        }
    )
    try:
        consumed_asset_receipt = agent_mod.finish_r740_consumption_episode()
    except Exception as consumption_exc:
        if error is None:
            error = (
                "episode-fatal external-asset receipt failure: "
                f"{type(consumption_exc).__name__}: {consumption_exc}"
            )
        consumed_asset_receipt = {
            "schema": agent_mod._R740_CONSUMPTION_SCHEMA,
            "question_id": q_id,
            "event_count": 0,
            "events": [],
            "consumed_assets": [],
            "fatal_count": 1,
            "event_sidecar": None,
            "receipt_error": f"{type(consumption_exc).__name__}: {consumption_exc}",
        }
    call_indices = sorted({int(row["call_index"]) for row in planner_attempts})
    successful_calls = [row for row in planner_attempts if row.get("status") == "ok"]
    planner_usage = {
        "calls": len(call_indices), "provider_attempts": len(planner_attempts),
        "calls_detail": planner_attempts,
        "input_tokens": sum(row["usage"]["input_tokens"] for row in successful_calls),
        "output_tokens": sum(row["usage"]["output_tokens"] for row in successful_calls),
        "total_tokens": sum(row["usage"]["total_tokens"] for row in successful_calls),
    }
    attempt_receipt.update({
        "status": "completed", "finished_unix": time.time(),
        "planner_calls": planner_usage["calls"],
        "provider_attempts": planner_usage["provider_attempts"],
    })
    record = {
        "question_id":   q_id,
        "scene_name":    item["scene_name"],
        "question_type": item["question_type"],
        "question":      item["question"],
        "initial_visual_input": visual_manifest,
        "pred":          pred,
        "budget_terminal": terminal_cap,
        "pred_source":   pred_source,
        "orphan_tool_drop": orphan_tool_drop,
        "elapsed_sec":   round(time.time() - t0, 1),
        "started_utc":   started_utc,
        "finished_utc":  time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "run_receipt":   run_receipt,
        "error":         error,
        "trace":         trace_rows,
        "discarded_message_history": discarded_message_history,
        "planner_served_models": planner_served_models,
        "tool_vlm_responses": tool_vlm_responses,
        "served_models": all_served_models,
        "sam3_quarantined": _SAM3_QUARANTINE.is_set(),
        "tool_telemetry": trace_list,
        "native_google_provider_calls": native_google.census(trace_list),
        "native_google_tool_responses": native_projection(trace_list),
        "consumed_asset_receipt": consumed_asset_receipt,
        "attempt_receipt": attempt_receipt,
        "llm_usage": {"planner": planner_usage},
    }
    record["verifier_skipped_events"] = _verifier_skip_events(trace_list)
    record["verifier_skipped_count"] = len(record["verifier_skipped_events"])
    published = publish_finalized_triple(output, q_id, record, attempt_receipt)
    _attempt_ledger_finish(ledger_path, attempt_receipt)
    print(f"[finalized] {q_id} -> {published}", flush=True)
    return record


def main():
    from training_assets import runner_main
    return runner_main(run_one, _PACKAGE_DIR)

if __name__ == '__main__':
    raise SystemExit(main())
