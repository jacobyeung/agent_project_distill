import hashlib
import json
import os
import re
from pathlib import Path

from .admission import native_final
from .common import canonical_bytes, digest_json, sha256
from .detailed_audit import messages, provider_matches, transcript_equal

POOL = "clean_vsi590k"
SNAPSHOT_SCHEMA = "clean-vsi590k-accepted-source-snapshot-v2"
ROW_FIELDS = {"dataset", "id", "option_letters", "options", "question", "question_type",
              "question_video_sha256", "scene_name", "source_question_type", "source_row_1based", "video"}
MODEL = "gemini-3.1-pro-preview"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def local_path(workspace, path):
    root = Path(os.path.abspath(workspace))
    path = Path(path)
    require(path.is_absolute() and ".." not in path.parts and path.is_relative_to(root),
            "Path is outside the explicitly admitted workspace")
    cursor = root
    require(not cursor.is_symlink(), "Workspace symlinks are not admitted")
    for part in path.relative_to(root).parts:
        cursor = cursor / part
        require(not cursor.is_symlink(), "Source/output symlinks are not admitted")
    return path


def clean_path(workspace, path):
    path = local_path(workspace, path)
    require(POOL in path.relative_to(Path(workspace)).parts, "A separate clean_vsi590k namespace is required")
    return path


def read_json(workspace, path):
    with local_path(workspace, path).open() as stream:
        return json.load(stream)


def pin(workspace, path, expected=None):
    path = local_path(workspace, path)
    result = {"path": str(path), "sha256": sha256(path), "size_bytes": path.stat().st_size}
    require(expected is None or result["sha256"] == expected, "Source-hash drift: " + str(path))
    return result


def verify_pin(workspace, value):
    actual = pin(workspace, value["path"], value["sha256"])
    require(value.get("size_bytes", actual["size_bytes"]) == actual["size_bytes"], "Source size drift")
    return actual


def verify_pins(workspace, values):
    """Rehash every binding; bound parallel reads keep large archives practical."""
    from concurrent.futures import ThreadPoolExecutor
    values = list(values)
    with ThreadPoolExecutor(max_workers=min(16, max(1, len(values)))) as pool:
        for _ in pool.map(lambda value: verify_pin(workspace, value), values):
            pass


def write_bytes(workspace, path, content):
    path = clean_path(workspace, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    return pin(workspace, path)


def write_json(workspace, path, value):
    return write_bytes(workspace, path, canonical_bytes(value))


def select_qids(qids, count=None):
    require(isinstance(qids, list) and qids and all(isinstance(q, str) and re.fullmatch(r"vsi590k_\d+", q) for q in qids),
            "Only string VSI-590K question identities are admitted")
    require(len(qids) == len(set(qids)), "Duplicate accepted question identity")
    count = len(qids) if count is None else count
    require(type(count) is int and 0 < count <= len(qids), "Requested count exceeds the accepted snapshot")
    return sorted(qids)[:count]


def validate_row(row):
    require(isinstance(row, dict) and set(row) == ROW_FIELDS, "Answer-free membership fields changed")
    select_qids([row["id"]])
    for key in ("dataset", "scene_name"):
        require(isinstance(row[key], str) and all(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", part) and part not in (".", "..") for part in row[key].split("/")) and (key != "dataset" or "/" not in row[key]), "Invalid physical scene identity")
    require(isinstance(row["question"], str) and row["question"].strip(), "Empty source question")
    require(isinstance(row["options"], list) and all(isinstance(x, str) for x in row["options"]), "Invalid source options")
    require(isinstance(row["option_letters"], list) and len(row["option_letters"]) == len(row["options"]), "Option mapping mismatch")
    require(isinstance(row["question_video_sha256"], str) and re.fullmatch(r"[a-f0-9]{64}", row["question_video_sha256"]), "Missing question/video identity hash")
    video = Path(row["video"])
    require(not video.is_absolute() and ".." not in video.parts and len(video.parts) >= 2
            and video.parts[0] == row["dataset"] and str(Path(*video.parts[1:]).with_suffix("")) == row["scene_name"], "Question/video/scene identity mismatch")
    return row


class SourceStore:
    def __init__(self, workspace, run_root, original_run_root, mapping=None):
        self.workspace = str(Path(os.path.abspath(workspace)))
        self.run_root = local_path(self.workspace, run_root)
        self.original_run_root = Path(original_run_root)
        self.mapping = mapping or {}
        self.bindings = {}
        self.missing = []
        self.captures = []
        self.errors = []
        self.undiscovered = []
        self.discrepancies = []
        self.inventory_mode = False
        self.media_cache = {}
        for target in self.mapping.values():
            local_path(self.workspace, target)

    def resolve(self, source):
        source = str(source)
        if source in self.mapping:
            return local_path(self.workspace, self.mapping[source])
        path = Path(source)
        if path.is_relative_to(self.original_run_root):
            return local_path(self.workspace, self.run_root / path.relative_to(self.original_run_root))
        if path.is_absolute() and path.is_relative_to(Path(self.workspace)):
            return local_path(self.workspace, path)
        return None

    def capture(self, source, expected=None, kind="source", size=None):
        require(expected is None or isinstance(expected, str) and re.fullmatch(r"[a-f0-9]{64}", expected), "Invalid source SHA-256")
        target = self.resolve(source)
        result = {"source_path": str(source), "sha256": expected, "kind": kind,
                  "sha256_expectation": expected or "not_recorded_by_available_authority",
                  "local_path": str(target) if target is not None else None, "availability": "missing"}
        if target is None or not target.is_file():
            if expected is not None:
                for item in self.missing:
                    if item["source_path"] == result["source_path"] and item.get("sha256") is None:
                        item.update(sha256=expected, sha256_expectation=expected)
            if not any(item["source_path"] == result["source_path"] and (expected is None or item.get("sha256") == expected)
                       for item in self.missing):
                self.missing.append(result)
        else:
            try:
                key = str(target)
                if key not in self.bindings:
                    self.bindings[key] = pin(self.workspace, target, expected)
                actual = self.bindings[key]
                require(expected is None or actual["sha256"] == expected, "Source-hash drift: " + str(source))
                require(size is None or actual["size_bytes"] == size, "Source size differs from receipt: " + str(source))
                result.update(actual, availability="verified")
            except (ValueError, OSError) as error:
                if not self.inventory_mode:
                    raise
                result.update(availability="invalid", error=str(error))
                self.errors.append(result)
        self.captures.append(result)
        return result

    def reference(self, spec, kind):
        require(isinstance(spec, dict) and isinstance(spec.get("path"), str) and Path(spec["path"]).is_absolute()
                and isinstance(spec.get("sha256"), str) and re.fullmatch(r"[a-f0-9]{64}", spec["sha256"]),
                "Missing authenticated " + kind)
        return self.capture(spec["path"], spec["sha256"], kind, spec.get("size_bytes", spec.get("bytes")))

    def json(self, record):
        if record["availability"] != "verified":
            return None
        try:
            return read_json(self.workspace, record["path"])
        except (ValueError, OSError) as error:
            if not self.inventory_mode:
                raise
            self.errors.append({**record, "error": str(error), "availability": "invalid"})
            return None

    def unresolved(self, record, description):
        item = {"source_path": record["source_path"], "sha256": record.get("sha256"),
                "kind": record["kind"], "discover_after_staging": description}
        if item not in self.undiscovered:
            self.undiscovered.append(item)

    def inventory(self, attempts):
        return {"schema": "clean-vsi590k-strict-inventory-v1", "reason": "requires_source_media", "runnable": False,
                "missing": self.missing, "invalid": self.errors, "attempt_inventory": attempts,
                "frame_path_discrepancies": self.discrepancies, "undiscovered_dependencies": self.undiscovered,
                "all_reference_paths_discovered": not self.undiscovered, "provider_calls": 0}


class SnapshotIncomplete(ValueError):
    def __init__(self, inventory):
        self.inventory = inventory
        super().__init__("requires_source_media: source snapshot has missing or invalid authorities/media; "
                         f"missing={len(inventory['missing'])}, invalid={len(inventory['invalid'])}")


def census_records(summary, accepted, decisions):
    require(summary.get("schema") == "r1313-collection-census-v1", "Wrong accepted-source authority schema")
    require(isinstance(accepted, list) and isinstance(decisions, list), "Malformed census authority")
    selected = select_qids([r["id"] for r in accepted])
    decision_ids = [r["id"] for r in decisions]
    require(len(decision_ids) == len(set(decision_ids)), "Duplicate census decision")
    by_id = {row["id"]: row for row in decisions}
    require(set(selected) == {r["id"] for r in decisions if r.get("accepted") is True}, "Acceptance-authority mismatch")
    require(summary.get("distinct_accepted") == len(accepted) and summary.get("distinct_finalized") == len(decisions), "Census counts disagree with acceptance authority")
    for row in accepted:
        require(by_id.get(row["id"]) == row, "Accepted record differs from the final census decision")
        require(all(row.get(key) is True for key in ("accepted", "answer_correct", "mechanically_complete", "has_perceptual_evidence")),
                "Successful terminal is not accepted-source authority")
        require(row.get("needs_topup") is False and row.get("final_cap_failure") is False and row.get("perceptual_evidence"), "Incomplete accepted-source selection")
        require(type(row.get("chosen_budget")) is int and row["chosen_budget"] in (16384, 32768), "Unrecognized selected attempt budget")
        require(re.fullmatch(r"[a-f0-9]{64}", row.get("trace_sha256", "")), "Accepted trace lacks a source hash")
        projection = row.get("metadata_projection")
        require(projection is None or projection.get("original_trace_sha256") == row["trace_sha256"] and projection.get("raw_trace_unchanged") is True,
                "Census interpretation does not bind unchanged trace bytes")
    return {row["id"]: row for row in accepted}


def validate_triplet(entries, row, decision, identity):
    raw, clean, attempt = (entries[key] for key in ("raw", "clean", "attempt"))
    qid, budget = row["id"], decision["chosen_budget"]
    require(attempt.get("question_id") == qid and attempt.get("status") == "completed"
            and attempt.get("arm") == "teacher_training_GT" and attempt.get("requested_model") == MODEL
            and attempt.get("planner_output_budget_tokens") == budget, "Selected attempt identity or completion mismatch")
    expected_row = {**row, "source_scene_name": row["scene_name"], "scene_name": row["dataset"] + "__" + row["scene_name"]}
    finals = []
    for entry in (raw, clean):
        require((entry.get("question_id"), entry.get("scene_name"), entry.get("question_type"), entry.get("question")) ==
                (qid, expected_row["scene_name"], row["question_type"], row["question"]), "Trace qid or physical scene differs from membership")
        require(not any(entry.get(key) for key in ("error", "budget_terminal", "orphan_tool_drop")), "Incomplete or capped source trace")
        receipt = entry["run_receipt"]
        require(receipt.get("schema") == "r1313-training-episode-v1" and receipt.get("round") == 1313
                and receipt.get("fixture_only") is False, "Not a production r1313 source trace")
        require(receipt.get("input_rows") == [expected_row] and receipt.get("membership_sha256") == identity["membership_sha256"], "Membership/trace admission mismatch")
        require(receipt.get("source_contract", {}).get("sha256") == identity["source_contract_sha256"]
                and receipt.get("planner_output_budget_tokens") == budget, "Source contract or budget authority mismatch")
        require(receipt.get("selected_frames_sha256") == receipt.get("scene_receipt", {}).get("sha256"), "Scene receipt selection binding mismatch")
        require(receipt.get("student_inputs", {}).get("modality") == "question_and_RGB_only", "Student modality changed")
        for message in messages(entry)[0]:
            if message.get("role", "").lower() not in ("ai", "aimessage"):
                continue
            require(provider_matches(message), "Native-provider response mismatch")
            usage = message.get("usage_metadata")
            require(isinstance(usage, dict) and usage == message["raw_response"].get("usage_metadata")
                    and all(type(usage.get(k)) is int and usage[k] >= 0 for k in ("input_tokens", "output_tokens", "total_tokens")), "Missing native source telemetry")
            require(message.get("response_metadata", {}).get("finish_reason") == "STOP"
                    and message["response_metadata"].get("model_name") == MODEL, "Capped or unpinned native source response")
        final = native_final(entry)
        require(final["message_index"] == len(messages(entry)[0]) - 1, "Native final is not the terminal teacher message")
        finals.append(final)
    require(finals[0] == finals[1] and transcript_equal(raw, clean), "Raw/clean native-final or evidence disagreement")
    require(raw["run_receipt"] == clean["run_receipt"], "Raw/clean source receipt disagreement")
    transcript = messages(raw)[0]
    calls = {}
    for index, message in enumerate(transcript):
        for call in message.get("tool_calls") or []:
            require(isinstance(call.get("id"), str) and call["id"] not in calls, "Duplicate native tool-call identity")
            calls[call["id"]] = (index, call)
    for evidence in decision["perceptual_evidence"]:
        call_index, call = calls.get(evidence.get("tool_call_id"), (-1, {}))
        results = [index for index, message in enumerate(transcript)
                   if message.get("role", "").lower() in ("tool", "toolmessage")
                   and message.get("tool_call_id") == evidence.get("tool_call_id") and message.get("content")]
        require(call.get("name") == evidence.get("tool") and len(results) == 1 and call_index < results[0]
                and any(message.get("role", "").lower() in ("ai", "aimessage") for message in transcript[results[0] + 1:]),
                "Accepted perceptual evidence is not bound to a tool result received by the teacher")
    return finals[0]


def capture_archive(store, attempt_path, row, raw, attempt):
    root = Path(attempt_path) / "archive"
    records = {name: store.capture(root / name, kind="source_archive")
               for name in ("identity.json", "journal.jsonl", "artifact_refs.jsonl")}
    if any(value["availability"] == "missing" for value in records.values()):
        return {"records": records, "events": [], "scene": None, "complete": False}
    identity = store.json(records["identity.json"])
    require(identity.get("question_id") == row["id"] and identity.get("source_question") == row
            and identity.get("budget") == attempt["planner_output_budget_tokens"]
            and identity.get("scene_receipt_path") == raw["run_receipt"]["scene_receipt"]["path"], "Archive/source identity mismatch")
    with local_path(store.workspace, records["journal.jsonl"]["path"]).open() as stream:
        journal = [json.loads(line) for line in stream if line.strip()]
    events, event_pins = [], []
    for index, item in enumerate(journal, 1):
        require(item.get("id") == index and isinstance(item.get("kind"), str), "Archive journal sequence mismatch")
        relative = Path(item["path"])
        require(not relative.is_absolute() and ".." not in relative.parts and relative.parts[0] == "events", "Invalid source archive event path")
        event_pin = store.capture(root / relative, kind="source_archive_event")
        event_pins.append(event_pin)
        event = store.json(event_pin)
        if event is None:
            continue
        require(event.get("id") == index and event.get("kind") == item["kind"], "Source archive journal/event mismatch")
        events.append(event)
    scene_events = [e["payload"] for e in events if e["kind"] == "scene_input"]
    require(len(scene_events) <= 1, "Ambiguous archived scene receipt")
    complete = len(events) == len(journal)
    if complete:
        require(len(scene_events) == 1, "Missing archived scene input")
        requests = [e["payload"] for e in events if e["kind"] == "provider_request"]
        responses = [e["payload"] for e in events if e["kind"] in ("provider_response", "provider_chunk")]
        terminals = [e["payload"] for e in events if e["kind"] == "provider_terminal"]
        call_ids = [item.get("call_id") for item in requests]
        require(call_ids and len(set(call_ids)) == len(call_ids) and all(isinstance(x, str) and x for x in call_ids), "Missing or duplicate native provider requests")
        require(len(terminals) == len(call_ids) and {item.get("call_id") for item in terminals} == set(call_ids)
                and all(item.get("status") in ("ok", "error") for item in terminals), "Incomplete native provider terminal census")
        failed = {item["call_id"]: item for item in terminals if item["status"] == "error"}
        require(all(isinstance(item.get("type"), str) and item.get("type") and isinstance(item.get("message"), str) for item in failed.values()), "Missing archived provider error details")
        response_ids = {item.get("call_id") for item in responses}
        require(set(call_ids) - set(failed) <= response_ids <= set(call_ids), "Missing native provider response archive")
        require(all(item.get("method") in ("generate_content", "generate_content_stream") for item in requests), "Unknown archived provider method")
        primary = [item for item in requests if item["method"] == "generate_content"]
        by_call = {call_id: [item["response"] for item in responses if item["call_id"] == call_id] for call_id in call_ids}
        for request in requests:
            if request["call_id"] in failed:
                continue
            replies = by_call[request["call_id"]]
            finishes = [candidate.get("finish_reason") for reply in replies for candidate in reply.get("candidates", []) if candidate.get("finish_reason")]
            usages = [reply["usage_metadata"] for reply in replies if isinstance(reply.get("usage_metadata"), dict)]
            require(finishes and usages and all(type(usages[-1].get(key)) is int and usages[-1][key] >= 0
                    for key in ("prompt_token_count", "candidates_token_count", "total_token_count")), "Missing native SDK call telemetry")
            if request["method"] == "generate_content":
                require(len(replies) == 1 and finishes == ["STOP"] and request.get("kwargs", {}).get("model") == MODEL,
                        "Planner archive model/finish/count mismatch")
        planner = [e["payload"] for e in events if e["kind"] == "planner_attempt"]
        successful_planner = [p for p in planner if p.get("status", "ok") == "ok"]
        require(len(planner) == len(primary), "Source provider attempt journal count mismatch")
        ai = [m for m in messages(raw)[0] if m.get("role", "").lower() in ("ai", "aimessage")]
        require(len(successful_planner) == attempt.get("planner_calls") and len(primary) == attempt.get("provider_attempts"), "Source planner call-count/telemetry mismatch")
        require([p.get("raw_response") for p in successful_planner] == [m["raw_response"] for m in ai], "Native attempt archive disagrees with committed provider responses")
        require(primary[-1]["call_id"] not in failed, "Native source final provider call failed")
        last = by_call[primary[-1]["call_id"]][-1]
        candidates = last.get("candidates", [])
        require(len(candidates) == 1 and candidates[0].get("finish_reason") == "STOP", "Native source final is absent or capped")
        parts = candidates[0].get("content", {}).get("parts", [])
        native_text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        require(native_text == native_final(raw)["native_final"], "Native SDK final disagrees with committed final")
        require(isinstance(last.get("usage_metadata"), dict) and all(type(last["usage_metadata"].get(k)) is int for k in
                ("prompt_token_count", "candidates_token_count", "total_token_count")), "Missing native SDK telemetry")
    return {"records": records, "events": event_pins, "scene": scene_events[0] if scene_events else None, "complete": complete}


def inventory_reference(store, spec, kind):
    try:
        return store.reference(spec, kind)
    except (ValueError, OSError) as error:
        if not store.inventory_mode:
            raise
        spec = spec if isinstance(spec, dict) else {}
        record = {"source_path": str(spec.get("path") or "<path absent from " + kind + ">"),
                  "sha256": spec.get("sha256"), "sha256_expectation": spec.get("sha256") or "not_recorded_by_available_authority",
                  "kind": kind, "availability": "invalid", "error": str(error).replace("topup_authority", "top-up authority")}
        store.errors.append(record)
        store.captures.append(record)
        return record


def inventory_media(store, qid, scene):
    references = [("source_video", scene.get("video")), ("frame_alignment", scene.get("alignment")),
                  ("source_provenance", scene.get("source_provenance"))]
    references.extend(("source_RGB", frame) for frame in scene.get("frames", []))
    for kind, spec in references:
        record = inventory_reference(store, spec, kind)
        if kind != "source_provenance":
            continue
        provenance = store.json(record)
        if provenance is None:
            store.unresolved(record, "source-frame receipt and original camera video paths and hashes")
            continue
        inventory_reference(store, provenance.get("source_frames_receipt"), "source_frames_receipt")
        inventory_reference(store, provenance.get("raw_sources", {}).get("iphone/rgb.mkv"), "original_camera_video")
    physical = scene.get("runtime_scene_id")
    mismatches = [frame for frame in scene.get("frames", []) if physical not in Path(frame["path"]).parts]
    if mismatches:
        store.discrepancies.append({"qid": qid, "physical_scene": physical, "pixels_verified": False,
                                    "frames": [{"source_path": frame["path"], "sha256": frame["sha256"]} for frame in mismatches]})


def inventory_attempt(store, qid, budget, disposition, selected, decision=None):
    start = len(store.captures)
    directory = store.original_run_root / "attempts" / qid / f"b{budget}"
    final = directory / "finalized" / qid
    store.capture(store.original_run_root / "episode_inputs" / (qid + ".json"), kind="membership_row")
    paths = {"raw": final / f"trace_{qid}.json", "clean": final / f"trace_{qid}_clean.json", "attempt": final / "attempt.json",
             "terminal": store.original_run_root / "terminals" / f"{qid}__b{budget}.json"}
    records = {}
    for key, path in paths.items():
        target = store.resolve(path)
        if disposition != "partial" or target is not None and target.is_file():
            expected = decision.get("trace_sha256") if decision and key == "raw" else None
            records[key] = store.capture(path, expected, "preserved_" + key)
    archive = directory / "archive"
    archived = {name: store.capture(archive / name, kind="source_archive")
                for name in ("identity.json", "journal.jsonl", "artifact_refs.jsonl")}
    refs = archived["artifact_refs.jsonl"]
    if refs["availability"] == "verified":
        with local_path(store.workspace, refs["path"]).open() as stream:
            for line in stream:
                if line.strip():
                    inventory_reference(store, json.loads(line), "preserved_archive_blob")
    local = store.resolve(directory)
    if local is not None and local.is_dir():
        for path in sorted(local.rglob("*")):
            local_path(store.workspace, path)
            if path.is_file():
                store.capture(directory / path.relative_to(local), kind="preserved_attempt_file")
    scene = None
    journal = archived["journal.jsonl"]
    if journal["availability"] == "verified":
        with local_path(store.workspace, journal["path"]).open() as stream:
            for line in stream:
                if not line.strip():
                    continue
                entry = json.loads(line)
                relative = Path(entry["path"])
                require(not relative.is_absolute() and ".." not in relative.parts and relative.parts[0] == "events",
                        "Invalid source archive event path")
                event = store.json(store.capture(archive / relative, kind="source_archive_event"))
                if event is not None and entry.get("kind") == "scene_input":
                    scene = event.get("payload")
    else:
        store.unresolved(journal, "native archive event paths and archived scene receipt")
    raw = store.json(records["raw"]) if "raw" in records else None
    if raw is None and "clean" in records:
        raw = store.json(records["clean"])
    authority = {}
    if raw is not None:
        receipt = raw.get("run_receipt", {})
        for key in ("source_contract", "collection_config", "scene_receipt"):
            authority[key] = inventory_reference(store, receipt.get(key), key)
        config = store.json(authority["collection_config"])
        if config is not None:
            authority["scene_registry"] = inventory_reference(store, {"path": config.get("assets_registry"),
                                                                       "sha256": config.get("assets_registry_sha256")}, "scene_registry")
            if budget == 32768 or config.get("topups") is not None or config.get("topups_sha256") is not None:
                authority["topups"] = inventory_reference(store, {"path": config.get("topups"), "sha256": config.get("topups_sha256")},
                                                            "topup_authority")
        else:
            store.unresolved(authority["collection_config"], "scene registry and any historical 32k top-up authority paths and hashes")
        receipt_scene = store.json(authority["scene_receipt"])
        scene = receipt_scene if receipt_scene is not None else scene
    elif "raw" in records:
        store.unresolved(records["raw"], "source contract, collection config, scene receipt and top-up authority paths and hashes")
    if scene is not None:
        inventory_media(store, qid, scene)
    elif "scene_receipt" in authority:
        store.unresolved(authority["scene_receipt"], "all selected RGB, video, alignment and source-provenance paths and hashes")
    if budget == 32768 and "topups" in authority:
        topups = store.json(authority["topups"])
        initial_path = store.original_run_root / "attempts" / qid / "b16384" / "finalized" / qid / f"trace_{qid}.json"
        for record in topups if isinstance(topups, list) else []:
            if isinstance(record, dict) and record.get("row", {}).get("id") == qid and record.get("original_trace_path") == str(initial_path):
                inventory_reference(store, {"path": str(initial_path), "sha256": record.get("original_trace_sha256")}, "initial_raw")
    unique = {(record["source_path"], record["kind"], record.get("sha256")): record for record in store.captures[start:]}
    return {"qid": qid, "budget": budget, "disposition": disposition, "selected": selected,
            "census_record_sha256": digest_json(decision) if decision else None,
            "files": list(unique.values()), "authority": authority}


def collect_attempt_inventory(store, docs):
    tasks = {}
    selected = {(row["id"], row["chosen_budget"]) for row in docs.get("ACCEPTED") or []}
    for name in ("DECISIONS", "ACCEPTED", "TOPUPS", "PARTIAL_ATTEMPTS"):
        for record in docs.get(name) or []:
            qid, budget = record["id"], record.get("chosen_budget", record.get("budget", 16384))
            select_qids([qid])
            require(type(budget) is int and budget in (16384, 32768), "Unknown inventoried attempt budget")
            disposition = "partial" if name == "PARTIAL_ATTEMPTS" else "selected" if (qid, budget) in selected else "rejected"
            tasks.setdefault((qid, budget), (disposition, record))
            if budget == 32768:
                tasks.setdefault((qid, 16384), ("capped_initial", None))
    for qid in {qid for qid, _ in tasks}:
        for budget in (16384, 32768):
            directory = store.resolve(store.original_run_root / "attempts" / qid / f"b{budget}")
            if directory is not None and directory.is_dir():
                tasks.setdefault((qid, budget), ("unselected", None))
    result = []
    for (qid, budget), (disposition, decision) in sorted(tasks.items()):
        try:
            result.append(inventory_attempt(store, qid, budget, disposition, (qid, budget) in selected, decision))
        except (ValueError, OSError, KeyError, TypeError) as error:
            if not store.inventory_mode:
                raise
            failure = {"qid": qid, "budget": budget, "error": str(error), "kind": "attempt_inventory",
                       "source_path": str(store.original_run_root / "attempts" / qid / f"b{budget}"), "sha256": None,
                       "sha256_expectation": "not_recorded_by_available_authority"}
            store.errors.append(failure)
            store.unresolved(failure, "remaining references in the unreadable or malformed attempt")
    return result


def validate_collection_config(config, identity, store, budget, receipt):
    require(config.get("schema") == "r1313-collection-config-v1" and config.get("mode") == "production"
            and config.get("run_root") == str(store.original_run_root) and config.get("budget", 16384) == budget,
            "Collection config/run/budget mismatch")
    require(all(config.get(key) == identity[key] for key in ("agent_id", "work_id", "source_contract_sha256"))
            and config.get("source_contract") == receipt["source_contract"]["path"], "Collection config/identity mismatch")


def topup_selection(store, row, decision, identity, config, authority):
    qid, budget = row["id"], decision["chosen_budget"]
    selection = {"selected_attempt": f"b{budget}", "selected_trace_path": decision["trace_path"],
                 "selected_trace_sha256": decision["trace_sha256"], "census_record_sha256": digest_json(decision),
                 "reason": "accepted_initial_16k_by_final_census" if budget == 16384 else "accepted_32k_after_authorized_capped_16k",
                 "topup_authority_verified": False, "topup_required": budget == 32768}
    if config is None:
        return selection
    if budget == 16384 and config.get("topups") is None and config.get("topups_sha256") is None:
        return selection
    require(isinstance(config.get("topups"), str) and isinstance(config.get("topups_sha256"), str),
            "Missing authenticated historical top-up authority in collection config")
    authority["topups"] = store.capture(config["topups"], config["topups_sha256"], "topup_authority")
    records = store.json(authority["topups"])
    if budget == 16384 or records is None:
        return selection
    require(isinstance(records, list) and all(isinstance(record, dict) for record in records), "Malformed top-up authority")
    matches = [record for record in records if record.get("row", {}).get("id") == qid]
    require(len(matches) == 1, "Historical top-up authority must name the selected qid exactly once")
    authorization = matches[0]
    require(authorization.get("row") == row and authorization.get("output_budget_tokens") == 32768,
            "Historical top-up source row or output budget mismatch")
    directory = store.original_run_root / "attempts" / qid / "b16384"
    final = directory / "finalized" / qid
    require(authorization.get("original_trace_path") == str(final / f"trace_{qid}.json")
            and isinstance(authorization.get("original_trace_sha256"), str), "Historical top-up initial trace binding mismatch")
    initial_pins = {key: store.capture(final / name, authorization["original_trace_sha256"] if key == "raw" else None, "initial_" + key)
                    for key, name in (("raw", f"trace_{qid}.json"), ("clean", f"trace_{qid}_clean.json"), ("attempt", "attempt.json"))}
    initial = {key: store.json(value) for key, value in initial_pins.items()}
    terminal = store.json(store.capture(store.original_run_root / "terminals" / f"{qid}__b16384.json", kind="initial_terminal"))
    selection.update(authorization_record_sha256=digest_json(authorization), initial_sources=initial_pins)
    if any(value is None for value in initial.values()) or terminal is None:
        return selection
    require(terminal.get("question_id") == qid and terminal.get("episode_id") == qid + "__b16384"
            and terminal.get("budget") == 16384 and terminal.get("output") == str(directory), "top-up initial terminal binding mismatch")
    expected_row = {**row, "source_scene_name": row["scene_name"], "scene_name": row["dataset"] + "__" + row["scene_name"]}
    for entry in (initial["raw"], initial["clean"]):
        receipt = entry.get("run_receipt", {})
        require(entry.get("question_id") == qid and entry.get("scene_name") == expected_row["scene_name"]
                and entry.get("question") == row["question"] and entry.get("budget_terminal") is True
                and receipt.get("input_rows") == [expected_row] and receipt.get("membership_sha256") == identity["membership_sha256"]
                and receipt.get("planner_output_budget_tokens") == 16384 and receipt.get("experiment_dir") == str(directory)
                and receipt.get("source_contract", {}).get("sha256") == identity["source_contract_sha256"],
                "top-up initial attempt binding or recorded cap mismatch")
    require(initial["raw"]["run_receipt"] == initial["clean"]["run_receipt"], "top-up initial raw/clean receipt binding mismatch")
    attempt = initial["attempt"]
    require(attempt.get("question_id") == qid and attempt.get("planner_output_budget_tokens") == 16384
            and attempt.get("requested_model") == MODEL and attempt.get("arm") == "teacher_training_GT", "top-up initial attempt binding mismatch")
    initial_receipt = initial["raw"]["run_receipt"]
    selected_raw = store.json(store.capture(decision["trace_path"], decision["trace_sha256"], "selected_raw"))
    if selected_raw is None:
        return selection
    fixed_inputs = ("schema", "round", "fixture_only", "input_rows", "membership_sha256", "source_contract",
                    "scene_receipt", "selected_frames_sha256", "student_inputs", "prompt_sha256")
    require(all(initial_receipt.get(key) == selected_raw["run_receipt"].get(key) for key in fixed_inputs),
            "top-up initial inference input binding differs from the selected attempt")
    authority["initial_collection_config"] = store.reference(initial_receipt["collection_config"], "collection_config")
    initial_config = store.json(authority["initial_collection_config"])
    if initial_config is None:
        return selection
    validate_collection_config(initial_config, identity, store, 16384, initial_receipt)
    excluded = {"budget", "topups", "topups_sha256"}
    require({key: value for key, value in initial_config.items() if key not in excluded} ==
            {key: value for key, value in config.items() if key not in excluded}, "Historical top-up changed a nonbudget collection configuration")
    selection["topup_authority_verified"] = True
    return selection


def inspect_source(store, decision, identity, membership, attempt_inventory):
    qid, budget = decision["id"], decision["chosen_budget"]
    attempt_path = store.original_run_root / "attempts" / qid / f"b{budget}"
    final_path = attempt_path / "finalized" / qid
    require(str(final_path / f"trace_{qid}.json") == decision["trace_path"], "Census selected attempt path does not match its identity")
    start_capture = len(store.captures)
    terminal_pin = store.capture(store.original_run_root / "terminals" / f"{qid}__b{budget}.json", kind="selected_terminal")
    terminal = store.json(terminal_pin)
    require(terminal is not None and terminal.get("question_id") == qid and terminal.get("episode_id") == f"{qid}__b{budget}"
            and terminal.get("budget") == budget and terminal.get("return_code") == 0
            and terminal.get("output") == str(attempt_path), "Acceptance-authority/terminal mismatch")
    episode = store.capture(store.original_run_root / "episode_inputs" / f"{qid}.json", kind="membership_row")
    row = store.json(episode)
    require(row is not None, "Accepted identity is missing its answer-free episode input")
    validate_row(row)
    require(row["id"] == qid, "Episode qid mismatch")
    if membership is not None:
        require(qid in membership and membership[qid]["row"] == row, "Episode input is not the bound membership row")
    paths = {"raw": final_path / f"trace_{qid}.json", "clean": final_path / f"trace_{qid}_clean.json", "attempt": final_path / "attempt.json"}
    sources = {key: store.capture(path, decision["trace_sha256"] if key == "raw" else None, "selected_" + key) for key, path in paths.items()}
    preserved = [item for item in attempt_inventory if item["qid"] == qid]
    result = {"qid": qid, "source_row": row, "membership_row_sha256": digest_json(row),
              "membership_line_sha256": membership[qid]["line_sha256"] if membership is not None else None,
              "membership_verified": membership is not None, "episode_input": episode,
              "acceptance_record_sha256": digest_json(decision), "selected_budget": budget,
              "terminal": terminal_pin, "sources": sources, "preserved_attempts": preserved,
              "native_answer_archive": None, "scene": None, "media": None, "archive": None, "authority": {}}
    result["selection"] = topup_selection(store, row, decision, identity, None, result["authority"])
    entries = {key: store.json(value) for key, value in sources.items()}
    if all(value is not None for value in entries.values()):
        raw = entries["raw"]
        result["native_answer_archive"] = validate_triplet(entries, row, decision, identity)
        receipt = raw["run_receipt"]
        require(receipt.get("experiment_dir") == str(attempt_path), "Native attempt directory binding mismatch")
        for key in ("source_contract", "collection_config", "scene_receipt"):
            result["authority"][key] = store.reference(receipt[key], key)
        contract = store.json(result["authority"]["source_contract"])
        if contract is not None:
            require(contract.get("schema") == "r1313-vsi590k-gt-collector-v1" and contract.get("round") == 1313
                    and contract.get("arm") == "teacher_training_GT" and contract.get("model") == {"requested_id": MODEL}, "Wrong source contract")
            require(contract.get("membership", {}).get("sha256") == identity["membership_sha256"], "Contract membership authority mismatch")
        config = store.json(result["authority"]["collection_config"])
        if config is not None:
            validate_collection_config(config, identity, store, budget, receipt)
            result["selection"] = topup_selection(store, row, decision, identity, config, result["authority"])
            registry_pin = store.capture(config["assets_registry"], config["assets_registry_sha256"], "scene_registry")
            result["authority"]["scene_registry"] = registry_pin
            registry = store.json(registry_pin)
            if registry is not None:
                matches = [p for p in registry.get("receipts", []) if p.get("path") == receipt["scene_receipt"]["path"] and p.get("sha256") == receipt["scene_receipt"]["sha256"]]
                require(registry.get("schema") == "r1313-assets-registry-v1" and len(matches) == 1, "Scene was not admitted by the collection config")
        archive = capture_archive(store, attempt_path, row, raw, entries["attempt"])
        result["archive"] = archive
        scene = store.json(result["authority"]["scene_receipt"])
        if scene is not None and archive["scene"] is not None:
            require(scene == archive["scene"], "Archived scene differs from its hash-bound receipt")
        scene = scene if scene is not None else archive["scene"]
        result["scene"] = scene
        if scene is not None:
            from .clean_media import validate_media
            result["media"] = validate_media(store, row, receipt, scene)
    required = store.captures[start_capture:] + [value for item in preserved for value in item["files"]]
    result["missing"] = [value for value in required if value["availability"] != "verified"]
    media_ready = result["media"] is not None and result["media"]["status"] == "verified"
    selection_ready = budget == 16384 or result["selection"]["topup_authority_verified"]
    result["status"] = "ready" if (membership is not None and not result["missing"] and media_ready and selection_ready
                                   and result["archive"] and result["archive"]["complete"]) else "requires_source_media"
    return result


def freeze(workspace, run_root, census_root, output, membership_path=None, source_map=None, allow_missing=False, strict=False):
    require(not (strict and allow_missing), "--strict and --allow-missing are mutually exclusive")
    output = clean_path(workspace, output)
    require(not output.exists(), "Accepted-source snapshots are immutable; choose a new output")
    census_root = local_path(workspace, census_root)
    run_root = local_path(workspace, run_root)
    mapping, map_pin = {}, None
    if source_map is not None:
        map_pin = pin(workspace, source_map)
        mapping_doc = read_json(workspace, source_map)
        require(mapping_doc.get("schema") == "clean-vsi590k-source-map-v1" and isinstance(mapping_doc.get("files"), dict), "Invalid explicit source map")
        mapping = mapping_doc["files"]
    store = SourceStore(workspace, run_root, run_root, mapping)
    store.inventory_mode = True
    authority_paths = {"run_identity": run_root / "RUN_IDENTITY.json", **{name: census_root / (name + ".json") for name in
                       ("SUMMARY", "ACCEPTED", "DECISIONS", "TOPUPS", "PARTIAL_ATTEMPTS")}}
    authority_pins = {key: store.capture(path, kind="census_" + key) for key, path in authority_paths.items()}
    docs = {key: store.json(value) for key, value in authority_pins.items()}
    identity = docs["run_identity"] or {}
    records = docs["ACCEPTED"] or docs["DECISIONS"] or []
    original_run = Path(records[0]["trace_path"]).parents[4].parent if records else run_root
    store.original_run_root = original_run
    if membership_path is not None:
        membership_pin = store.capture(local_path(workspace, membership_path), identity.get("membership_sha256"), "membership")
    else:
        membership_pin = {"source_path": "<supply --membership>", "sha256": identity.get("membership_sha256"),
                          "sha256_expectation": identity.get("membership_sha256") or "not_recorded_by_available_authority",
                          "availability": "missing", "kind": "membership"}
        store.missing.append(membership_pin)
    inventory = collect_attempt_inventory(store, docs)
    core_missing = any(value is None for value in docs.values())
    for key, value in docs.items():
        if value is None:
            store.unresolved(authority_pins[key], "the authority's identities and referenced attempt paths and hashes")
    if strict and (store.missing or store.errors) or core_missing:
        raise SnapshotIncomplete(store.inventory(inventory))
    if store.errors:
        raise ValueError(store.errors[0]["error"])
    store.inventory_mode = False
    require(identity.get("schema") == "r1313-run-identity-v1", "Wrong collector run identity")
    accepted = census_records(docs["SUMMARY"], docs["ACCEPTED"], docs["DECISIONS"])
    qids = select_qids(list(accepted))
    membership = None
    if membership_pin["availability"] == "verified":
        membership, all_ids = {}, set()
        with local_path(workspace, membership_pin["path"]).open("rb") as stream:
            for line in stream:
                row = validate_row(json.loads(line))
                require(row["id"] not in all_ids, "Duplicate membership row")
                all_ids.add(row["id"])
                if row["id"] in accepted:
                    membership[row["id"]] = {"row": row, "line_sha256": hashlib.sha256(line).hexdigest()}
        require(set(membership) == set(accepted), "Census contains nonmember accepted identities")
        require(docs["SUMMARY"].get("candidate_questions") == len(all_ids), "Membership/census population mismatch")
    rows = []
    for qid in qids:
        try:
            rows.append(inspect_source(store, accepted[qid], identity, membership, inventory))
        except (ValueError, OSError) as error:
            if not strict:
                raise
            store.errors.append({"qid": qid, "error": str(error), "source_path": accepted[qid]["trace_path"],
                                 "sha256": accepted[qid]["trace_sha256"]})
    if store.errors or not allow_missing and (store.missing or any(row["status"] != "ready" for row in rows)):
        raise SnapshotIncomplete(store.inventory(inventory))
    verify_pins(workspace, list(authority_pins.values()) + list(store.bindings.values()))
    frozen = {}
    for key, value in authority_pins.items():
        frozen[key] = write_bytes(workspace, output / "authority" / authority_paths[key].name, local_path(workspace, value["path"]).read_bytes())
        require(frozen[key]["sha256"] == value["sha256"], "Authority changed while freezing")
    attempt_authorities = {(value["source_path"], value["kind"]): value for value in store.captures
                           if value["kind"] in ("collection_config", "topup_authority") and value["availability"] == "verified"}
    frozen_attempts = []
    for index, ((original, kind), value) in enumerate(sorted(attempt_authorities.items())):
        frozen_pin = write_bytes(workspace, output / "attempt_authority" / f"{index:04d}_{value['sha256']}.json",
                                 local_path(workspace, value["path"]).read_bytes())
        require(frozen_pin["sha256"] == value["sha256"], "Attempt authority changed while freezing")
        frozen_attempts.append({**frozen_pin, "source_path": original, "kind": kind})
    snapshot = {"schema": SNAPSHOT_SCHEMA, "source_pool": POOL, "clean_vsi590k_training": True,
                "benchmark_trained_diagnostic": False, "training_eligible": False,
                "workspace": str(Path(workspace)), "original_run_root": str(original_run), "run_root": str(run_root),
                "authority": frozen, "original_authority": authority_pins, "membership": membership_pin,
                "source_map": map_pin, "source_bindings": sorted(store.bindings.values(), key=lambda p: p["path"]),
                "accepted_qids": qids, "selection": "exact_final_census_chosen_budget; lexical_string_qids; no_regrading",
                "rows": rows, "missing": store.missing, "runnable": not store.missing and all(row["status"] == "ready" for row in rows),
                "attempt_inventory": inventory, "frozen_attempt_authority": frozen_attempts,
                "undiscovered_dependencies": store.undiscovered,
                "student_initialization": "original_weights_required_for_each_clean_student"}
    snapshot["snapshot_payload_sha256"] = digest_json(snapshot)
    return write_json(workspace, output / "snapshot.json", snapshot)


def load_snapshot(workspace, path, require_ready=True):
    clean_path(workspace, path)
    snapshot = read_json(workspace, path)
    require(snapshot.get("snapshot_payload_sha256") == digest_json({key: value for key, value in snapshot.items() if key != "snapshot_payload_sha256"}),
            "Frozen source snapshot content drift")
    require(snapshot.get("schema") == SNAPSHOT_SCHEMA and snapshot.get("source_pool") == POOL
            and snapshot.get("benchmark_trained_diagnostic") is False, "Diagnostic and clean source pools cannot be mixed")
    require(snapshot.get("workspace") == str(Path(workspace)), "Snapshot workspace binding changed")
    pins = (list(snapshot["authority"].values()) + list(snapshot["original_authority"].values())
            + snapshot["source_bindings"] + snapshot["frozen_attempt_authority"])
    if snapshot["membership"].get("availability") == "verified":
        pins.append(snapshot["membership"])
    if snapshot["source_map"] is not None:
        pins.append(snapshot["source_map"])
    verify_pins(workspace, pins)
    authority = {key: read_json(workspace, value["path"]) for key, value in snapshot["authority"].items()}
    accepted = census_records(authority["SUMMARY"], authority["ACCEPTED"], authority["DECISIONS"])
    require(snapshot["accepted_qids"] == select_qids(list(accepted)) and [r["qid"] for r in snapshot["rows"]] == snapshot["accepted_qids"], "Frozen source census identity drift")
    inventory = snapshot["attempt_inventory"]
    inventory_keys = {(item["qid"], item["budget"]) for item in inventory}
    required_attempts = {(record["id"], record.get("chosen_budget", record.get("budget", 16384)))
                         for name in ("DECISIONS", "TOPUPS", "PARTIAL_ATTEMPTS") for record in authority[name]}
    required_attempts |= {(qid, 16384) for qid, budget in required_attempts if budget == 32768}
    require(len(inventory_keys) == len(inventory) and required_attempts <= inventory_keys, "Frozen attempt inventory lost a rejected/capped/partial attempt")
    require({(item["qid"], item["budget"]) for item in inventory if item["selected"]} ==
            {(qid, record["chosen_budget"]) for qid, record in accepted.items()}, "Frozen selected attempt inventory drift")
    expected_authorities = {(value["source_path"], value["sha256"], value["kind"]) for item in inventory
                            for value in item["authority"].values() if value["availability"] == "verified"
                            and value["kind"] in ("collection_config", "topup_authority")}
    frozen_authorities = {(value["source_path"], value["sha256"], value["kind"]) for value in snapshot["frozen_attempt_authority"]}
    require(expected_authorities == frozen_authorities, "Frozen collection config/top-up authority inventory drift")
    mapping = read_json(workspace, snapshot["source_map"]["path"])["files"] if snapshot["source_map"] is not None else None
    store = SourceStore(workspace, snapshot["run_root"], snapshot["original_run_root"], mapping)
    for row in snapshot["rows"]:
        decision = accepted[row["qid"]]
        require(row["acceptance_record_sha256"] == digest_json(decision)
                and row["selected_budget"] == decision["chosen_budget"]
                and row["sources"]["raw"]["sha256"] == decision["trace_sha256"], "Frozen accepted attempt authority drift")
        require(row["membership_row_sha256"] == digest_json(row["source_row"]), "Frozen membership row drift")
        require(read_json(workspace, row["episode_input"]["path"]) == row["source_row"], "Frozen episode row differs from its bytes")
        config_pin = row["authority"].get("collection_config")
        config = store.json(config_pin) if config_pin is not None else None
        expected_selection = topup_selection(store, row["source_row"], decision, authority["run_identity"], config, dict(row["authority"]))
        require(row["selection"] == expected_selection, "Frozen selected attempt reason/top-up authority drift")
        if require_ready and row["selected_budget"] == 32768:
            require(row["selection"]["topup_authority_verified"], "Selected 32k source lacks verified top-up authority")
    if require_ready:
        require(snapshot.get("runnable") is True and not snapshot["missing"] and all(r["status"] == "ready" for r in snapshot["rows"]),
                "requires_source_media: an incomplete dry-run snapshot cannot authorize conversion")
    return snapshot
