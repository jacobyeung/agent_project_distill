import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from . import admission
from .common import ARTIFACTS, CONTRACT_SHA, DONOR, PILOT, REGISTRY, REGISTRY_SHA, REPO, binding, digest_json, load_json, write_once
from .split import physical_group

SPLIT_SHA = "4b1db3e9c44e9db1fedfd36645ec83b0c2fb349a43e0957078dbbfae50ff577b"
ANSWER = re.compile(r"<ANSWER>.*?</ANSWER>", re.I | re.S)
PROSE_ARGUMENTS = {"execution_summary", "plan_text", "explanation", "reasoning", "summary"}


def messages(entry):
    trace = entry.get("trace", [])
    return (trace.get("messages", []), "/trace/messages") if isinstance(trace, dict) else (trace, "/trace")


def text_metadata(text):
    return {
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
        "characters": len(text), "utf8_bytes": len(text.encode()), "whitespace_words": len(text.split()),
        "frame_reference_count": len(re.findall(r"\b(?:frame|image)s?\s*(?:id|index|#|:)?\s*\d", text, re.I)),
        "time_reference_count": len(re.findall(r"\b\d+(?:\.\d+)?\s*(?:s|sec|seconds)\b", text, re.I)),
        "numeric_literal_count": len(re.findall(r"(?<!\w)[+-]?\d+(?:\.\d+)?", text)),
        "coordinate_tuple_count": len(re.findall(r"[\[(]\s*[+-]?\d+(?:\.\d+)?\s*,\s*[+-]?\d+(?:\.\d+)?\s*,\s*[+-]?\d+(?:\.\d+)?\s*[\])]", text)),
        "tool_or_code_reference_count": len(re.findall(r"\b(?:tool|python|pointcloud|point_cloud|function|verify_plan|query|execute)[\w]*\b", text, re.I)),
        "has_relationship_marker": bool(re.search(r"\b(?:left|right|front|behind|near|far|between|closest|largest|smallest|before|after)\b", text, re.I)),
        "has_calculation_marker": bool(re.search(r"\b(?:distance|angle|norm|dot product|cross product|area|volume|subtract|sum|multiply|divide|meters|metres|cm)\b|=", text, re.I)),
        "has_uncertainty_marker": bool(re.search(r"\b(?:uncertain|ambiguous|approximately|likely|estimate|maybe|roughly)\b", text, re.I)),
        "has_correction_marker": bool(re.search(r"\b(?:correction|correcting|instead|mistake|recheck|revise|however|actually)\b", text, re.I)),
        "has_pending_action_marker": bool(re.search(r"\b(?:I (?:will|need|should)|let(?:'s| us)|need to|must (?:check|verify)|next step)\b", text, re.I)),
    }


def provider_matches(message):
    raw = message.get("raw_response")
    return (isinstance(raw, dict) and message.get("provenance") == "provider"
            and "content" in raw and raw["content"] == message.get("content")
            and raw.get("response_metadata") == message.get("response_metadata")
            and (raw.get("tool_calls") or []) == (message.get("tool_calls") or [])
            and not raw.get("invalid_tool_calls"))


def native_segments(entry):
    result = []
    trace, root = messages(entry)
    for index, message in enumerate(trace):
        if message.get("role", "").lower() not in ("ai", "aimessage"):
            continue
        matched = provider_matches(message)
        base = {"message_index": index, "message_id": message.get("id"), "raw_response_matches": matched,
                "provenance": message.get("provenance"), "has_tool_calls": bool(message.get("tool_calls"))}
        content = message.get("content", "")
        parts = [(f"{root}/{index}/content", "assistant_text", content)] if isinstance(content, str) else []
        if isinstance(content, list):
            for part_index, part in enumerate(content):
                if not isinstance(part, dict):
                    continue
                part_root = f"{root}/{index}/content/{part_index}"
                if part.get("type") == "text" and isinstance(part.get("text"), str):
                    parts.append((part_root + "/text", "assistant_text", part["text"]))
                if part.get("type") in ("thinking", "reasoning"):
                    for key in ("thinking", "reasoning", "text"):
                        if isinstance(part.get(key), str):
                            parts.append((part_root + "/" + key, "provider_thought_summary", part[key]))
        for call_index, call in enumerate(message.get("tool_calls") or []):
            for key, value in (call.get("args") or {}).items():
                if key in PROSE_ARGUMENTS and isinstance(value, str):
                    parts.append((f"{root}/{index}/tool_calls/{call_index}/args/{key}", "assistant_tool_argument", value))
        for pointer, kind, text in parts:
            if text.strip():
                result.append({**base, "pointer": pointer, "kind": kind, "text": text})
    return result


def transcript_equal(raw, clean, assistant_only=False):
    fields = ("role", "content", "provenance", "id", "tool_calls", "raw_response", "response_metadata")
    def payload(entry):
        return [{key: message.get(key) for key in fields} for message in messages(entry)[0]
                if not assistant_only or message.get("role", "").lower() in ("ai", "aimessage")]
    return payload(raw) == payload(clean)


def shape(value, depth=2):
    if isinstance(value, dict):
        return {key: shape(item, depth - 1) for key, item in value.items()} if depth > 0 else {"type": "dict", "keys": sorted(value)}
    if isinstance(value, list):
        result = {"type": "list", "length": len(value), "item_types": sorted({type(item).__name__ for item in value})}
        if depth > 0 and value and isinstance(value[0], dict):
            result["first_item_schema"] = shape(value[0], depth - 1)
        return result
    return type(value).__name__


def field_inventory(entry):
    trace, _ = messages(entry)
    segments = native_segments(entry)
    kinds = Counter(segment["kind"] for segment in segments)
    ai = [(i, message) for i, message in enumerate(trace) if message.get("role", "").lower() in ("ai", "aimessage")]
    metadata = [{key: value for key, value in segment.items() if key != "text"} | text_metadata(segment["text"]) for segment in segments]
    result = {
        "top_level_keys": sorted(entry), "message_count": len(trace),
        "roles": dict(Counter(message.get("role") for message in trace)),
        "assistant_messages": len(ai), "provider_thought_summary_parts": kinds["provider_thought_summary"],
        "assistant_text_parts": kinds["assistant_text"], "assistant_tool_argument_parts": kinds["assistant_tool_argument"],
        "unmatched_provider_messages": [index for index, message in ai if not provider_matches(message)],
        "content_part_types": dict(Counter(part.get("type") for _, message in ai for part in (message.get("content") if isinstance(message.get("content"), list) else []) if isinstance(part, dict))),
        "supplementary_field_schemas": {key: shape(entry.get(key)) for key in ("initial_visual_input", "discarded_message_history", "tool_vlm_responses", "consumed_asset_receipt", "attempt_receipt", "native_google_tool_responses")},
        "segments": metadata, "exhaustive_hidden_reasoning_available": False,
        "provider_calls": dict(Counter(call.get("event", "missing") for call in entry.get("native_google_provider_calls", []))),
        "provider_call_field_names": sorted({key for call in entry.get("native_google_provider_calls", []) for key in call}),
        "native_tool_response_shape": shape(entry.get("native_google_tool_responses")),
        "discarded_recovery_count": len((entry.get("discarded_message_history") or {}).get("recoveries", [])),
        "initial_rgb_frame_count": entry.get("initial_visual_input", {}).get("frame_count"),
        "initial_rgb_frame_entries": len(entry.get("initial_visual_input", {}).get("frames", [])),
        "assistant_nonanswer_text_parts": sum(part["kind"] == "assistant_text" and bool(ANSWER.sub("", part["text"]).strip()) for part in segments),
        "tool_provider_responses": [
            {"pointer": f"/native_google_tool_responses/{index}",
             **{key: response.get(key) for key in ("where", "model_role", "requested_model", "provider_served_model", "status", "finish_reason")},
             **{key: text_metadata(response[key]) for key in ("content", "thoughts") if isinstance(response.get(key), str)},
             "raw_response_schema": shape(response.get("raw_response"), 3),
             "native_candidates_schema": shape(response.get("native_candidates"), 3)}
            for index, response in enumerate(entry.get("native_google_tool_responses", []))
        ],
        "tool_calls": [], "tool_returns": [],
    }
    call_names = {}
    for index, message in enumerate(trace):
        for call in message.get("tool_calls") or []:
            call_names[call.get("id")] = call.get("name")
            result["tool_calls"].append({"message_index": index, "name": call.get("name"), "argument_schema": shape(call.get("args"))})
        if message.get("role", "").lower() in ("tool", "toolmessage"):
            content = message.get("content")
            parsed = content
            if isinstance(content, str):
                try:
                    parsed = json.loads(content)
                except (ValueError, TypeError):
                    parsed = content
            result["tool_returns"].append({"message_index": index, "name": call_names.get(message.get("tool_call_id"), message.get("name")), "schema": shape(parsed)})
    try:
        final = admission.native_final(entry)
    except (ValueError, TypeError, KeyError):
        result.update({"native_final_valid": False, "final_explanation_characters": 0})
    else:
        final_parts = [part for part in metadata if part["message_index"] == final["message_index"]]
        result.update({"native_final_valid": True, "final_message_index": final["message_index"],
                       "final_text": text_metadata(final["native_final"]), "final_parts": final_parts,
                       "final_explanation_characters": len(ANSWER.sub("", final["native_final"]).strip())})
    return result


def training_items(split, inference):
    train, heldout = set(split["train_candidate_qids"]), set(split["heldout_qids"])
    if train & heldout or len(train) != len(split["train_candidate_qids"]):
        raise ValueError("Training identity is duplicated or overlaps heldout")
    selected = [item for item in inference if str(item["id"]) in train]
    if Counter(str(item["id"]) for item in selected) != Counter({qid: 1 for qid in train}):
        raise ValueError("Training inference identity is missing or duplicated")
    for item in selected:
        group = physical_group(item["dataset"], item["scene_name"])
        if group not in split["train_group_ids"] or group in split["heldout_group_ids"]:
            raise ValueError("Training candidate is outside frozen training scenes")
    return sorted(selected, key=lambda item: str(item["id"]))


def source_paths(item, contract):
    qid, category = str(item["id"]), item["question_type"]
    if not qid.isdigit() or category not in contract["categories"]:
        raise ValueError("Unexpected finalized source identity")
    directory = DONOR / "run" / category / contract["experiment_tag"] / "finalized" / qid
    return {"raw": directory / f"trace_{qid}.json", "clean": directory / f"trace_{qid}_clean.json", "attempt": directory / f"attempt_{qid}.json"}


def inspect_training():
    contract, split, pins, inference = admission.authorities()
    binding(admission.SPLIT_PATH, SPLIT_SHA)
    counts, part_lengths, tools, schemas, final_features = Counter(), defaultdict(list), Counter(), {}, Counter()
    differences, tool_return_schemas, provider_events = Counter(), {}, Counter()
    counts["fixed_train_candidates"] = len(split["train_candidate_qids"])
    for item in training_items(split, inference):
        paths = source_paths(item, contract)
        counts["finalized_clean_files"] += paths["clean"].is_file()
        counts["finalized_raw_files"] += paths["raw"].is_file()
        if not paths["raw"].is_file():
            continue
        raw = load_json(paths["raw"])
        inventory = field_inventory(raw)
        counts["native_final_valid"] += inventory["native_final_valid"]
        counts["native_final_with_nonanswer_text"] += inventory["final_explanation_characters"] > 0
        if paths["clean"].is_file():
            clean = load_json(paths["clean"])
            counts["raw_clean_transcripts_equal"] += transcript_equal(raw, clean)
            for left, right in zip(messages(raw)[0], messages(clean)[0]):
                for key in ("role", "content", "provenance", "id", "tool_calls", "raw_response", "response_metadata"):
                    if left.get(key) != right.get(key):
                        differences[f'{left.get("role")}/{key}'] += 1
        counts["all_provider_content_matched"] += not inventory["unmatched_provider_messages"]
        provider_events.update(inventory["provider_calls"])
        for tool_return in inventory["tool_returns"]:
            tool_return_schemas.setdefault(str(tool_return["name"]), tool_return["schema"])
        for part in inventory["segments"]:
            part_lengths[part["kind"]].append(part["characters"])
        for part in inventory.get("final_parts", []):
            if part["kind"] == "provider_thought_summary":
                part_lengths["final_provider_thought_summary"].append(part["characters"])
                for key, value in part.items():
                    if key.startswith("has_") or key.endswith("_count"):
                        final_features[key] += bool(value)
        for call in inventory["tool_calls"]:
            tools[call["name"]] += 1
            schemas.setdefault(call["name"], call["argument_schema"])
    return {"counts": dict(counts), "lengths": {key: {"parts": len(values), "min_characters": min(values), "max_characters": max(values), "total_characters": sum(values)} for key, values in part_lengths.items()}, "final_summary_marker_counts_not_semantic_validation": dict(final_features), "tool_call_counts": dict(tools), "tool_argument_schemas": schemas, "raw_clean_field_differences": dict(differences), "tool_return_schemas": tool_return_schemas, "provider_events": dict(provider_events), "bindings": pins}


def native_completion(entries, item, contract):
    qid = str(item["id"])
    attempt = entries["attempt"]
    if (str(attempt.get("question_id")), attempt.get("status"), attempt.get("arm"), attempt.get("requested_model")) != (qid, "completed", contract["arm"], contract["model"]["requested_id"]):
        raise ValueError("attempt_incomplete_or_wrong_donor")
    finals = []
    for key in ("raw", "clean"):
        entry = entries[key]
        if any(entry.get(flag) for flag in ("error", "budget_terminal", "orphan_tool_drop")):
            raise ValueError("native_terminal_incomplete")
        if (str(entry.get("question_id")), entry.get("scene_name"), entry.get("question_type"), entry.get("question")) != (qid, item["scene_name"], item["question_type"], item["question"]):
            raise ValueError("native_inference_identity_mismatch")
        receipt = entry["run_receipt"]
        if receipt["effective_contract_sha256"] != CONTRACT_SHA or receipt["model"] != contract["model"]:
            raise ValueError("native_contract_mismatch")
        if entry["initial_visual_input"]["mode"] != "text_only_control" or receipt["selected_frames_sha256"] != REGISTRY_SHA:
            raise ValueError("native_input_policy_mismatch")
        finals.append(admission.native_final(entry))
    if finals[0] != finals[1] or not transcript_equal(entries["raw"], entries["clean"], assistant_only=True):
        raise ValueError("native_assistant_archive_mismatch")
    return finals[0]


def offline_grade(raw, item, label, scorer):
    if str(item["id"]) != str(label["id"]) or any(item.get(key, [] if key == "options" else None) != label.get(key, [] if key == "options" else None) for key in ("scene_name", "dataset", "question_type", "question", "options")):
        raise ValueError("canonical_label_identity_mismatch")
    final = admission.native_final(raw)
    if scorer.extract_response(raw, strict=True) != final["native_final"]:
        raise ValueError("scorer_native_response_mismatch")
    record, metrics = scorer._score_entry(raw, label, strict=True)
    score = record.get("accuracy", record.get("MRA"))
    return {"strict_native_final": True, "fully_correct": score == 1.0 and metrics["is_correct"] is True,
            "score": score, "is_correct_flag": bool(metrics["is_correct"]), "record": record}


def resolve_pointer(entry, pointer):
    value = entry
    for key in pointer.split("/")[1:]:
        key = key.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def render_review(entry):
    final = admission.native_final(entry)
    parts = [part for part in native_segments(entry) if part["kind"] == "provider_thought_summary"
             or part["pointer"].endswith("/args/execution_summary")
             or (part["kind"] == "assistant_text" and part["message_index"] == final["message_index"])]
    if any(not part["raw_response_matches"] for part in parts):
        raise ValueError("Unmatched native source cannot be rendered")
    chunks, spans, offset = [], [], 0
    for part in parts:
        if chunks:
            offset += 2
        text = part["text"]
        spans.append({"pointer": part["pointer"], "kind": part["kind"], "message_index": part["message_index"],
                      "start": offset, "end": offset + len(text), "sha256": hashlib.sha256(text.encode()).hexdigest()})
        chunks.append(text)
        offset += len(text)
    rendering = "\n\n".join(chunks)
    return {"target_type": "verbatim_archived_summary_transcript_and_native_final_review_only",
            "training_eligible": False, "self_contained_verified": False,
            "contains_provider_thought_summaries": any(part["kind"] == "provider_thought_summary" for part in parts),
            "exhaustive_hidden_reasoning_available": False,
            "transform": "Copy bound source fields verbatim in transcript order; insert only two newlines between spans. Omit pre-execution plans, code, intermediate answer text, and tool results from the rendering.",
            "rendering": rendering, "length": text_metadata(rendering), "spans": spans}


def concise_tool_evidence(entry):
    trace, root = messages(entry)
    calls, excerpts = {}, []
    for index, message in enumerate(trace):
        for call in message.get("tool_calls") or []:
            calls[call.get("id")] = call
        if message.get("role", "").lower() not in ("tool", "toolmessage"):
            continue
        call = calls.get(message.get("tool_call_id"), {})
        text = message.get("content")
        if call.get("name") != "execute_python_code" or not isinstance(text, str) or len(text) > 2000 or len(text.splitlines()) > 20:
            continue
        if re.search(r"[\[\]{}]|\b(?:error|traceback|base64|mask|centroid|xyz|coordinate)\b|<ANSWER>", text, re.I) or text_metadata(text)["coordinate_tuple_count"]:
            continue
        if not re.search(r"\d", text) or not re.search(r"[A-Za-z]{3,}", text):
            continue
        excerpts.append({"pointer": f"{root}/{index}/content", "tool_call_id": message.get("tool_call_id"),
                         "tool_name": call["name"], "call_arguments_sha256": digest_json(call.get("args")),
                         "text": text, "length": text_metadata(text), "coordinate_convention_verified": False,
                         "training_eligible": False})
    return excerpts


def length_stats(values):
    return {"count": len(values), "min": min(values), "median": median(values), "max": max(values), "sum": sum(values)} if values else {"count": 0}


def runtime_bindings():
    relative = ["AGENTS.md", ".gitignore", "requirements.txt", "scripts/gpu_batch.sh",
                "artifacts/data/split.json", "artifacts/data/smoke.json", "artifacts/data/smoke.input_audit.json"]
    relative += [f"student_pilot/{name}.py" for name in ("__init__", "adapters", "admission", "batches", "checks", "cli", "common", "inspect_source", "lease", "runner", "split")]
    relative += [f"tests/test_{name}.py" for name in ("admission", "split", "training")]
    return [binding(REPO / path) for path in relative] + [binding(PILOT / f"development/{name}") for name in ("label_path.txt", "implementation_status.md")]


def count_rows(rows):
    return {
        "fixed_train_candidates": len(rows),
        "finalized_clean_files": sum("clean" in row["sources"] for row in rows),
        "finalized_raw_files": sum("raw" in row["sources"] for row in rows),
        "finalized_attempt_files": sum("attempt" in row["sources"] for row in rows),
        "finalized_complete_native": sum(row["native_complete"] for row in rows),
        "offline_fully_correct": sum(row.get("offline", {}).get("fully_correct", False) for row in rows),
        "answer_only_eligible": sum(row["answer_only_eligible"] for row in rows),
        "usable_faithful_detailed_targets": sum(row["detailed_target_eligible"] for row in rows),
    }


def registry_differences(selection, assets):
    assets = sorted(assets, key=lambda asset: asset["ordinal"])
    names = [Path(asset["path"]).stem for asset in assets]
    failed = []
    if len(selection["indices"]) != 32:
        failed.append("selected_frame_count_not_32")
    if names != selection["frame_names"]:
        failed.append("registered_frame_names_or_order_differ")
    if any(asset["source"] != "preextracted_png" for asset in assets):
        failed.append("non_preextracted_asset_source")
    return {"selected_indices_count": len(selection["indices"]), "selected_frame_names_count": len(selection["frame_names"]),
            "registered_scene_asset_count": len(assets), "registered_asset_sources": dict(Counter(asset["source"] for asset in assets)),
            "selected_frame_names_sha256": digest_json(selection["frame_names"]), "registered_frame_names_sha256": digest_json(names),
            "failed_checks": failed, "admission_relaxed": False}


def diagnose_rgb_registry(raw, item):
    external = raw["run_receipt"]["external_data"]["frames"]
    frames_pin = binding(external["path"], external["sha256"])
    registry_pin = binding(REGISTRY, REGISTRY_SHA)
    selection = load_json(REGISTRY)[item["scene_name"]]
    assets = [asset for asset in load_json(frames_pin["path"])["assets"] if asset["scene"] == item["scene_name"]]
    return {**registry_differences(selection, assets), "frames_registry": frames_pin, "selected_registry": registry_pin}


def audit(output):
    output = Path(output).resolve()
    if not output.is_relative_to(ARTIFACTS / "data") or output.exists():
        raise ValueError("Use a new audit directory under this repository's artifacts/data; never overwrite outputs")
    before = runtime_bindings()
    contract, split, pins, inference = admission.authorities()
    binding(admission.SPLIT_PATH, SPLIT_SHA)
    answer_key = admission.resolve_answer_key()
    scorer, scorer_pins = admission.load_scorer(contract)
    items = training_items(split, inference)
    labels = [label for label in load_json(answer_key["path"]) if str(label["id"]) in set(split["train_candidate_qids"])]
    if Counter(str(label["id"]) for label in labels) != Counter({str(item["id"]): 1 for item in items}):
        raise ValueError("Training labels are missing or duplicated")
    labels = {str(label["id"]): label for label in labels}
    rows, packets = [], []
    whole_finalized = sum(source_paths(item, contract)["clean"].is_file() for item in inference)
    for item in items:
        qid = str(item["id"])
        paths = source_paths(item, contract)
        sources = {key: binding(path) for key, path in paths.items() if path.is_file()}
        row = {"qid": qid, "scene": item["scene_name"], "dataset": item["dataset"], "category": item["question_type"],
               "sources": sources, "expected_paths": {key: str(path) for key, path in paths.items()},
               "native_complete": False, "answer_only_eligible": False, "detailed_target_eligible": False, "exclusions": []}
        rows.append(row)
        if len(sources) != 3:
            row["exclusions"].extend(f"missing_finalized_{key}" for key in paths if key not in sources)
            continue
        entries = {key: load_json(path) for key, path in paths.items()}
        raw = entries["raw"]
        row["fields"] = field_inventory(raw)
        row["raw_clean_full_transcript_equal"] = transcript_equal(raw, entries["clean"])
        row["raw_clean_assistant_transcript_equal"] = transcript_equal(raw, entries["clean"], assistant_only=True)
        row["attempt_status"] = entries["attempt"].get("status")
        row["native_terminal_flags"] = {key: bool(raw.get(key)) for key in ("error", "budget_terminal", "orphan_tool_drop")}
        try:
            native_completion(entries, item, contract)
            if row["fields"]["unmatched_provider_messages"]:
                raise ValueError("unmatched_provider_messages")
        except (ValueError, KeyError, TypeError) as error:
            row["exclusions"].append("native_completion_failed")
            row["native_completion_error"] = str(error)
            continue
        row["native_complete"] = True
        try:
            row["offline"] = offline_grade(raw, item, labels[qid], scorer)
        except (ValueError, KeyError, TypeError) as error:
            row["exclusions"].append("offline_admission_failed")
            row["offline_error_type"] = type(error).__name__
            continue
        if not row["offline"]["fully_correct"]:
            row["exclusions"].append("native_final_not_fully_correct")
            continue
        try:
            admitted, candidate_pins, _, admitted_raw = admission.source_candidate(qid)
            if candidate_pins != pins or admitted["sources"] != sources or native_segments(admitted_raw) != native_segments(raw):
                raise ValueError("source_changed_during_audit")
        except (ValueError, KeyError, TypeError, OSError, RuntimeError) as error:
            row["exclusions"].append("rgb_source_admission_failed")
            row["rgb_error_type"] = type(error).__name__
            row["rgb_error"] = str(error)
            if str(error) == "RGB registry does not match the fixed original selected-frame identities":
                row["rgb_registry_diagnostic"] = diagnose_rgb_registry(raw, item)
            continue
        row["answer_only_eligible"] = True
        row["rgb_admission"] = {"routine": "student_pilot.admission.source_candidate", "frame_count": len(admitted["student_input"]["frames"]),
                                "source_video": admitted["source_video"], "external_registries": admitted["external_registries"],
                                "frame_indices_sha256": digest_json(admitted["student_input"]["frame_indices"]),
                                "timestamps_sha256": digest_json(admitted["student_input"]["timestamps"])}
        row["exclusions"].append("self_contained_explanation_not_verified")
        if not row["fields"]["final_explanation_characters"]:
            row["exclusions"].append("ordinary_assistant_text_is_answer_only")
        packet = {"qid": qid, "sources": sources, "student_input": admitted["student_input"],
                  "source_video": admitted["source_video"], "video_timing": admitted["video_timing"],
                  **render_review(raw), "numeric_tool_evidence": concise_tool_evidence(raw)}
        packets.append(packet)
        row["review_rendering"] = {"target_type": packet["target_type"], "length": packet["length"], "spans": packet["spans"],
                                   "concise_numeric_tool_excerpts": len(packet["numeric_tool_evidence"])}
    after = runtime_bindings()
    if before != after:
        raise ValueError("Existing runtime files changed during the read-only audit")
    if "torch" in sys.modules:
        raise ValueError("The source audit must not import the model runtime")
    counts = count_rows(rows)
    field_counts, tool_counts, provider_events, lengths = Counter(), Counter(), Counter(), defaultdict(list)
    tool_provider_scopes, tool_provider_models, final_summary_markers = Counter(), Counter(), Counter()
    for row in rows:
        fields = row.get("fields", {})
        for key in ("message_count", "assistant_messages", "provider_thought_summary_parts", "assistant_text_parts", "assistant_nonanswer_text_parts", "assistant_tool_argument_parts", "discarded_recovery_count"):
            field_counts[key] += fields.get(key, 0)
        field_counts["native_valid_finals_with_explanation_text"] += fields.get("final_explanation_characters", 0) > 0
        field_counts["raw_clean_assistant_transcripts_equal"] += row.get("raw_clean_assistant_transcript_equal", False)
        field_counts["raw_clean_full_transcripts_equal"] += row.get("raw_clean_full_transcript_equal", False)
        field_counts["raw_with_all_provider_parts_matched"] += "fields" in row and not fields.get("unmatched_provider_messages")
        has_execution_summary = any(part["pointer"].endswith("/args/execution_summary") for part in fields.get("segments", []))
        has_final_summary = any(part["kind"] == "provider_thought_summary" for part in fields.get("final_parts", []))
        field_counts["questions_with_provider_summaries"] += fields.get("provider_thought_summary_parts", 0) > 0
        field_counts["questions_with_execution_summary_arguments"] += has_execution_summary
        field_counts["questions_with_final_provider_summaries"] += has_final_summary
        field_counts["eligible_with_execution_summary_arguments"] += row["answer_only_eligible"] and has_execution_summary
        field_counts["eligible_with_final_provider_summaries"] += row["answer_only_eligible"] and has_final_summary
        tool_counts.update(call["name"] for call in fields.get("tool_calls", []))
        provider_events.update(fields.get("provider_calls", {}))
        field_counts["initial_rgb_zero_frame_traces"] += fields.get("initial_rgb_frame_count") == 0 and fields.get("initial_rgb_frame_entries") == 0
        field_counts["tool_provider_responses"] += len(fields.get("tool_provider_responses", []))
        for response in fields.get("tool_provider_responses", []):
            tool_provider_scopes[str(response["where"])] += 1
            tool_provider_models[str(response["requested_model"])] += 1
            for key in ("content", "thoughts"):
                if key in response:
                    lengths["tool_provider_" + key + "_characters"].append(response[key]["characters"])
        for part in fields.get("final_parts", []):
            if part["kind"] == "provider_thought_summary":
                for key, value in part.items():
                    if key.startswith("has_") or key.endswith("_count"):
                        final_summary_markers[key] += bool(value)
        for part in fields.get("segments", []):
            lengths[part["kind"] + "_characters"].append(part["characters"])
            if row["answer_only_eligible"]:
                lengths["eligible_" + part["kind"] + "_characters"].append(part["characters"])
        if "final_text" in fields:
            lengths["native_final_characters"].append(fields["final_text"]["characters"])
    for packet in packets:
        lengths["review_rendering_characters"].append(packet["length"]["characters"])
        lengths["review_rendering_utf8_bytes"].append(packet["length"]["utf8_bytes"])
        lengths["review_rendering_whitespace_words"].append(packet["length"]["whitespace_words"])
    report = {
        "schema": "r1298-detailed-source-audit-v1", "counts": counts,
        "donor": {"questions": len(inference), "scenes": split["donor_scene_count"], "finalized_clean_file_presence_only": whole_finalized},
        "frozen_cohort": {"train_scenes": len(split["train_scenes"]), "heldout_questions": len(split["heldout_qids"]),
                          "heldout_scenes": len(split["heldout_scenes"]), "heldout_qids_sha256": digest_json(split["heldout_qids"]),
                          "heldout_archives_opened": 0, "heldout_questions_scored": 0, "selection_uses_correctness": False},
        "bindings": pins, "answer_key": answer_key, "scorer": scorer_pins,
        "field_counts_all_finalized_training": dict(field_counts), "tool_call_counts_all_finalized_training": dict(tool_counts),
        "provider_event_counts_all_finalized_training": dict(provider_events),
        "tool_provider_response_scopes": dict(tool_provider_scopes), "tool_provider_requested_models": dict(tool_provider_models),
        "final_summary_lexical_markers_not_semantic_validation": dict(final_summary_markers),
        "rgb_failure_reasons": dict(Counter(row["rgb_error"] for row in rows if "rgb_error" in row)),
        "rgb_registry_failed_checks": dict(Counter(reason for row in rows for reason in row.get("rgb_registry_diagnostic", {}).get("failed_checks", []))),
        "per_category": {category: count_rows([row for row in rows if row["category"] == category]) for category in contract["categories"]},
        "exclusion_counts": dict(Counter(reason for row in rows for reason in row["exclusions"])),
        "lengths": {key: length_stats(values) for key, values in lengths.items()},
        "review_packets": len(packets), "concise_numeric_tool_excerpts": sum(len(packet["numeric_tool_evidence"]) for packet in packets),
        "target_policy": {
            "usable_detailed_target_definition": "A source-bound, fully correct, self-contained explanation plus native answer with supported observations and explicit frame/reference conventions. Byte-faithful extraction alone does not establish this.",
            "native_archive_finding": f"The planner archive contains {field_counts['assistant_nonanswer_text_parts']} ordinary assistant text parts with non-answer prose. Provider thinking fields are archived thought summaries, not exhaustive hidden chain-of-thought. Tool arguments contain planner-authored plans and execution summaries, not an independently verified final explanation. Auxiliary tool-provider responses separately preserve content, thoughts, and native candidates; these are not planner final explanations.",
            "include_thoughts_is_not_completeness_evidence": True,
            "summary_renderings_are_review_only": True, "coordinate_triples_transformed": False,
            "tool_code_executed": False, "tool_arrays_masks_or_images_exported": False,
            "native_wire_transcript_completeness_claim": False,
            "archive_integrity_scope": "Completed attempt, contract-bound native final, clean/raw assistant transcript equality, and embedded provider payload equality. This does not certify exhaustive reasoning or equality of system/human/tool cleaning.",
            "numeric_tool_evidence_scope": "Verbatim short numeric execute_python_code returns only, separate from renderings. No new calculations, interpretation, array flattening, or coordinate conversion. Semantic support and units require review.",
            "not_proof_all_archived_summaries_are_unusable": True,
            "token_lengths_measured": False,
        },
        "blocker": "The native assistant answers have no ordinary final explanation. Archived summaries and execution arguments require source-grounded semantic review or bounded Gemini annotation before they can become self-contained detailed training targets. Do not train on the review renderings as if this check had passed.",
        "annotation_plan": {
            "api_calls_issued": 0, "initial_max_questions": 10, "selection": "At most one answer-only-eligible training qid per category; choose by sorted qid, not heldout performance.",
            "input": "Original selected RGB and original timing, question/options, immutable native transcript pointers, exact native final, and concise archived tool evidence. Never supply heldout questions or canonical labels as rewriting content.",
            "output": "One self-contained explanation and the unchanged native answer, with source JSON pointers for each claim. Preserve uncertainty and corrections. Require explicit units and frame/reference conventions; reject unsupported claims rather than fill gaps.",
            "review": "A human verifies every claim against its archived support and original frames, checks the native final remains unchanged, and checks that no tools, pointcloud access, missing frames, or hidden state are required. Re-run the pinned offline admission and student token/masking gates before promotion.",
            "expand_only_after_review": True,
        },
        "infrastructure_only_smoke_unchanged": True, "benchmark_improvement_claim": False,
        "future_clean_student_restarts_original_weights": True, "gpu_operations": 0, "torch_imported": False,
        "existing_runtime_bindings_before": before, "existing_runtime_bindings_after": after,
        "implementation": binding(Path(__file__)), "tests": binding(REPO / "tests/test_detailed_audit.py"),
    }
    output.mkdir()
    write_once(output / "per_qid.json", {"schema": "training-native-provenance-v1", "rows": rows})
    write_once(output / "review_packets.json", {"schema": "not-a-training-manifest-source-excerpts-v1", "training_eligible": False, "rows": packets})
    write_once(output / "eligible_targets.json", {"schema": "faithful-detailed-targets-v1", "rows": [], "count": 0, "reason": report["blocker"]})
    report["outputs"] = {name: binding(output / f"{name}.json") for name in ("per_qid", "review_packets", "eligible_targets")}
    write_once(output / "audit_report.json", report)
    with (output / "source_count_report.md").open("x") as stream:
        stream.write(report_markdown(report))
    return {"counts": counts, "review_packets": len(packets), "report": binding(output / "audit_report.json")}


def report_markdown(report):
    lines = ["# Detailed-target source audit", "", "The audit admits no self-contained detailed target. It preserves source-faithful review material without inventing explanatory prose.", "", "| Training admission stage | Questions |", "|---|---:|"]
    lines += [f"| {key.replace('_', ' ')} | {value} |" for key, value in report["counts"].items()]
    donor, cohort = report["donor"], report["frozen_cohort"]
    lines += ["", f"The whole donor contains {donor['questions']} questions in {donor['scenes']} scenes. Exactly {donor['finalized_clean_file_presence_only']} finalized clean files exist; that is a presence count, not a usability count.",
              f"The frozen training cohort contains {cohort['train_scenes']} scenes. All {cohort['heldout_questions']} heldout questions in {cohort['heldout_scenes']} scenes remain fixed. The audit opens no heldout archive and scores no heldout question.",
              f"RGB source admission excludes {sum(report['rgb_failure_reasons'].values())} fully correct native finals. Its recorded reasons are {json.dumps(report['rgb_failure_reasons'], sort_keys=True)}. The exact registry predicates are {json.dumps(report['rgb_registry_failed_checks'], sort_keys=True)}. The audit does not relax these checks or alter the selected frames.",
              "", "## Native fields and target type", "", report["target_policy"]["native_archive_finding"],
              "The embedded raw responses preserve provider content; the provider-call ledger records call-start metadata, not an exhaustive wire transcript. Cleaned system and tool content need not equal the raw archive. The raw archive remains the source for excerpts.",
              f"The export contains {report['review_packets']} review-only renderings and {report['concise_numeric_tool_excerpts']} separate short numeric tool excerpts. The renderer copies archived summaries, execution-summary arguments, and the final assistant text verbatim. It adds only blank-line separators, omits code and tool calls, and makes no new measurements or coordinate conversions. These renderings are not admitted training targets.",
              "", "## Lengths", "", "Lengths count Unicode characters, UTF-8 bytes, or whitespace-delimited words as named. They are not student-token counts.", "", "| Field | Count | Minimum | Median | Maximum |", "|---|---:|---:|---:|---:|"]
    for key, stats in report["lengths"].items():
        lines.append(f"| {key} | {stats['count']} | {stats.get('min', '')} | {stats.get('median', '')} | {stats.get('max', '')} |")
    lines += ["", "## Blocker and bounded next step", "", report["blocker"],
              "A proposed annotation pilot covers at most ten training questions, at most one per category. Gemini may rewrite only archived supported material and must attach source pointers to each claim; a human must verify it before promotion. This audit issues no API calls. A human may also approve a genuinely self-contained native excerpt without rewriting; zero admitted targets does not prove every archived summary is unsalvageable.",
              "", "## Evidence and boundaries", "", "The JSON report pins the donor contract, canonical membership, selected-frame registry, frozen split, answer key, scorer, implementation, and output files. The per-question file records all exclusions and field metadata. Review packets retain exact source pointers and source-span hashes. No benchmark text or answers are printed to stdout.",
              "The audit uses the existing native-final, authority, offline-scorer, and RGB/frame admission routines. Fully correct requires the pinned accuracy or MRA to equal 1.0 as well as its correctness flag; numeric admission does not mean exact numeric equality. RGB eligibility does not establish token fit, training success, or benchmark improvement.",
              "The audit changes no existing runtime file, acquires no GPU, trains nothing, and evaluates no heldout student. The answer-only smoke remains infrastructure-only. The future clean VSI590K student must restart the original weights.", ""]
    return "\n".join(lines)


def verify_outputs(output):
    output = Path(output)
    report = load_json(output / "audit_report.json")
    for pin in list(report["outputs"].values()) + [report["implementation"], report["tests"], report["answer_key"]] + list(report["bindings"].values()) + list(report["scorer"].values()):
        binding(pin["path"], pin["sha256"])
    _, split, pins, _ = admission.authorities()
    if pins != report["bindings"] or binding(admission.SPLIT_PATH)["sha256"] != SPLIT_SHA:
        raise ValueError("Frozen authority changed")
    rows = load_json(report["outputs"]["per_qid"]["path"])["rows"]
    packets = load_json(report["outputs"]["review_packets"]["path"])["rows"]
    targets = load_json(report["outputs"]["eligible_targets"]["path"])
    if count_rows(rows) != report["counts"] or targets["rows"] or targets["count"] != 0:
        raise ValueError("Audit counts or target eligibility changed")
    if Counter(row["qid"] for row in rows) != Counter(split["train_candidate_qids"]) or {row["qid"] for row in rows} & set(split["heldout_qids"]):
        raise ValueError("Training-only audit boundary failed")
    expected = {row["qid"] for row in rows if row["answer_only_eligible"]}
    if Counter(packet["qid"] for packet in packets) != Counter({qid: 1 for qid in expected}):
        raise ValueError("Review packet identities changed")
    for row in rows:
        for pin in row["sources"].values():
            binding(pin["path"], pin["sha256"])
    span_count = 0
    for packet in packets:
        raw = load_json(packet["sources"]["raw"]["path"])
        rendering = render_review(raw)
        if any(packet[key] != value for key, value in rendering.items()) or packet["numeric_tool_evidence"] != concise_tool_evidence(raw):
            raise ValueError("Export differs from verbatim native source")
        for span in packet["spans"]:
            if packet["rendering"][span["start"]:span["end"]] != resolve_pointer(raw, span["pointer"]):
                raise ValueError("Exported span differs from source field")
            span_count += 1
    return {"status": "VERIFIED_SOURCE_SPANS_AND_COUNTS", "counts": report["counts"], "review_packets": len(packets), "verified_spans": span_count,
            "split_sha256": SPLIT_SHA, "report": binding(output / "audit_report.json")}


def main():
    parser = argparse.ArgumentParser()
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--inspect", action="store_true")
    actions.add_argument("--output", type=Path)
    actions.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        parser.error('Run this CPU-only source audit with CUDA_VISIBLE_DEVICES=""')
    if args.inspect:
        inventory = inspect_training()
        result = {key: inventory[key] for key in ("counts", "lengths", "final_summary_marker_counts_not_semantic_validation", "raw_clean_field_differences", "provider_events", "tool_call_counts")}
    else:
        result = verify_outputs(args.verify) if args.verify else audit(args.output)
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
