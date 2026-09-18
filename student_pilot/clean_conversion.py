import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from . import conversion
from .clean_source import (POOL, SnapshotIncomplete, clean_path, freeze, load_snapshot, local_path, pin, read_json,
                           require, select_qids, verify_pin, write_json)
from .common import REPO, canonical_bytes, digest_json
from .detailed_audit import concise_tool_evidence, native_segments

JOB_SCHEMA = "clean-vsi590k-conversion-job-v1"
RUN_SCHEMA = "clean-vsi590k-conversion-run-v1"
REVIEW_SCHEMA = "clean-vsi590k-independent-grounded-review-v1"
MANIFEST_SCHEMA = "clean-vsi590k-accepted-detailed-targets-v1"
INDEX_SCHEMA = "clean-vsi590k-admission-index-v1"
LEASE_SCHEMA = "clean-vsi590k-api-lease-v1"
ADMISSION_CONTRACT = "individually_reviewed_rows_only_v1"
FORBIDDEN = {"label", "labels", "gold", "gold_label", "gold_labels", "ground_truth", "gt_answer", "answer_key",
             "score", "scores", "scoring", "scoring_rule", "is_correct", "correct", "correctness", "answer_correct",
             "accepted", "acceptance", "pred", "prediction", "mra", "em", "ground_truth_answer", "correct_answer",
             "answer_label", "evaluation_qid", "eval_qid", "evaluation_mapping", "benchmark_qid"}
ALIAS_PATTERN = "|".join(r"[_\-\s]+".join(re.escape(part) for part in alias.split("_"))
                         for alias in sorted(FORBIDDEN, key=len, reverse=True))
SERIALIZED_FIELD = re.compile(r"(?<!\w)(?P<alias>" + ALIAS_PATTERN + r")(?!\w)(?:\\*[\"'])?"
                              r"(?:\s*[:=|/\\>]\s*|\s+(?:is|was)\s+|\s+(?=[\"'\d]|true\b|false\b|null\b))(?=\S)", re.I)
OFFLINE_LABEL_PATH = re.compile(r"(?<!\w)(?P<alias>offline[_\-\s]+labels)[/\\]v\d+[/\\]", re.I)
PAYLOAD_KEYS = {"question", "options", "native_final_provenance", "frame_metadata", "evidence"}
EVIDENCE_KEYS = {"id", "kind", "text", "source_pointer", "text_sha256", "message_index", "tool_call_id",
                 "call_arguments_sha256", "coordinate_convention_verified", "tool_name", "argument_summary"}


def namespace(workspace, path):
    path = clean_path(workspace, path)
    parts = path.relative_to(Path(workspace)).parts
    return Path(workspace).joinpath(*parts[:parts.index(POOL) + 1])


class LabelAliasInRequest(ValueError):
    reason = "label_alias_in_request"
    offset_units = "unicode_code_points"

    def __init__(self, evidence_id, offset, field_path, alias):
        self.evidence_id, self.offset, self.field_path, self.alias = evidence_id, offset, field_path, alias
        super().__init__(f"{self.reason}: Serialized label/scoring alias; evidence_id={evidence_id} "
                         f"offset={offset} field={field_path} alias={alias}")


def check_no_selection_fields(value, evidence_id="payload", field_path="", perception_confidence=False):
    if isinstance(value, dict):
        if isinstance(value.get("id"), str) and "text" in value:
            evidence_id = value["id"]
        for key in sorted(value, key=lambda key: key != "evidence"):
            pointer = field_path + "/" + str(key).replace("~", "~0").replace("/", "~1")
            alias = re.sub(r"[_\-\s]+", "_", str(key).strip()).lower()
            if alias in FORBIDDEN:
                raise LabelAliasInRequest(evidence_id, len(str(key)) - len(str(key).lstrip()), pointer, alias)
            check_no_selection_fields(str(key), evidence_id, pointer + "/<key>")
            check_no_selection_fields(value[key], evidence_id, pointer, key == "text" and value.get("kind") == "tool_observation" and value.get("tool_name") in {"predict_2d_segmentation_masks", "predict_2d_segmentation_masks_video", "predict_2d_bounding_box"})
    elif isinstance(value, list):
        for index, item in enumerate(value):
            check_no_selection_fields(item, evidence_id, field_path + "/" + str(index))
    elif isinstance(value, str):
        if perception_confidence:
            # Mask/box scores are perception confidence; preserve text and match offsets.
            value = re.sub(r'"score"\s*:\s*(?:0(?:\.\d+)?|1(?:\.0+)?)(?![\w.])',
                           lambda match: " " * len(match.group()), value)
        matches = [pattern.search(value) for pattern in (SERIALIZED_FIELD, OFFLINE_LABEL_PATH)]
        matches = [match for match in matches if match is not None]
        if matches:
            match = min(matches, key=lambda match: match.start("alias"))
            raise LabelAliasInRequest(evidence_id, match.start("alias"), field_path, match.group("alias"))


def request_boundary(request):
    require(isinstance(request, dict) and set(request) == {"converter_version", "model", "config", "contents"} and request["converter_version"] == "v2", "Unexpected provider-request envelope")
    contents = request["contents"]
    require(isinstance(contents, list) and len(contents) == 1 and set(contents[0]) == {"role", "parts"}
            and contents[0]["role"] == "user" and len(contents[0]["parts"]) == 1
            and set(contents[0]["parts"][0]) == {"text"}, "Only the allowlisted text annotation request may cross the provider boundary")
    wire_payload = json.loads(contents[0]["parts"][0]["text"])
    from .conversion_v2 import CONTRACT, EVIDENCE_ROLES
    require(digest_json(wire_payload.get("conversion_contract")) == digest_json(CONTRACT), "Conversion contract changed")
    payload = {key: value for key, value in wire_payload.items() if key != "conversion_contract"}
    for item in payload["evidence"]:
        require(item.pop("evidence_role", None) == EVIDENCE_ROLES.get(item["kind"]), "Evidence role changed")
    check_no_selection_fields(payload)
    require(isinstance(payload, dict) and set(payload) == PAYLOAD_KEYS, "Annotation payload is not the allowlisted projection")
    require(isinstance(payload["question"], str) and isinstance(payload["options"], list)
            and all(isinstance(x, str) for x in payload["options"]), "Request question/options schema changed")
    conversion.answer_body(payload["native_final_provenance"])
    expected_metadata = {"frame_indices", "timestamps", "fps", "total_num_frames", "selected_frame_positions", "spatial_reference_policy"}
    require(set(payload["frame_metadata"]) == expected_metadata, "Unexpected frame metadata at request boundary")
    evidence = payload["evidence"]
    require(isinstance(evidence, list) and evidence and len({e["id"] for e in evidence}) == len(evidence), "Request evidence is absent or duplicated")
    for item in evidence:
        require(set(item) <= EVIDENCE_KEYS and {"id", "kind", "text", "source_pointer", "text_sha256"} <= set(item), "Unexpected evidence field")
        require(item["kind"] in {"source_question", "source_option", "provider_thought_summary", "assistant_tool_argument", "archived_tool_result", "tool_observation", "original_frame_metadata"}, "Native final cannot serve as explanatory evidence")
        require(isinstance(item["text"], str) and item["text_sha256"] == hashlib.sha256(item["text"].encode()).hexdigest(), "Evidence span hash mismatch")
    require(request == conversion.make_request(payload), "Pinned request builder, prompt, model, thinking or generation settings changed")
    return {"verified": True, "request_sha256": digest_json(request), "payload_sha256": digest_json(payload),
            "forbidden_fields": [], "selection_authority_serialized": False}


def prepare_context(workspace, source):
    require(source["native_answer_archive"] is not None and source["media"] is not None, "Source evidence or scene metadata is unavailable")
    for value in source["sources"].values():
        verify_pin(workspace, value)
    raw = read_json(workspace, source["sources"]["raw"]["path"])
    row, media = source["source_row"], source["media"]
    evidence = []

    def add(kind, text, pointer, **metadata):
        if isinstance(text, str) and text.strip():
            evidence.append({"id": f"e{len(evidence):04d}", "kind": kind, "text": text,
                             "source_pointer": pointer, "text_sha256": hashlib.sha256(text.encode()).hexdigest(), **metadata})

    add("source_question", row["question"], "/source_row/question")
    for index, option in enumerate(row["options"]):
        add("source_option", option, f"/source_row/options/{index}")
    for span in native_segments(raw):
        if span["kind"] == "provider_thought_summary" or span["pointer"].endswith("/args/execution_summary"):
            require(span["raw_response_matches"], "Explanatory span is not an exact native-provider field")
            add(span["kind"], span["text"], span["pointer"], message_index=span["message_index"])
    for item in conversion.tool_observations(raw):
        item = dict(item)
        text, pointer = item.pop("text"), item.pop("source_pointer")
        add("tool_observation", text, pointer, **item)
    frame_metadata = {key: media[key] for key in ("frame_indices", "timestamps", "fps", "total_num_frames")}
    frame_metadata.update(selected_frame_positions=list(range(1, 33)),
                          spatial_reference_policy="Use only conventions explicitly stated in cited archived evidence; never assume camera/world axes.")
    add("original_frame_metadata", canonical_bytes(frame_metadata).decode(), "/media")
    require(any(e["kind"] in ("provider_thought_summary", "assistant_tool_argument", "archived_tool_result", "tool_observation") for e in evidence), "No explanatory source evidence is available")
    payload = {"question": row["question"], "options": row["options"],
               "native_final_provenance": source["native_answer_archive"]["native_final"],
               "frame_metadata": frame_metadata, "evidence": evidence}
    request = conversion.make_request(payload)
    boundary = request_boundary(request)
    return {"schema": "clean-vsi590k-conversion-context-v1", "source_pool": POOL, "qid": source["qid"],
            "source_row_sha256": digest_json(source), "payload": payload, "request": request,
            "request_sha256": boundary["request_sha256"], "source_status": source["status"],
            "training_eligible": False, "request_boundary": boundary}


def runtime_pins(workspace, telemetry_path):
    names = ("clean_source.py", "clean_media.py", "clean_conversion.py", "conversion.py", "conversion_v2.py", "admission.py", "detailed_audit.py", "common.py", "split.py")
    values = [pin(workspace, REPO / "student_pilot" / name) for name in names]
    if telemetry_path is not None:
        values.append(pin(workspace, telemetry_path))
    return values


def prepare(workspace, snapshot_path, output, count=None, dry_run=False, telemetry_path=None):
    snapshot = load_snapshot(workspace, snapshot_path, require_ready=not dry_run)
    output = clean_path(workspace, output)
    require(not output.exists(), "Conversion jobs are immutable; choose a new clean-pool output")
    require(namespace(workspace, output) == namespace(workspace, snapshot_path), "Clean snapshot and job need one isolated namespace")
    selected = select_qids(snapshot["accepted_qids"], count)
    by_qid = {row["qid"]: row for row in snapshot["rows"]}
    contexts, boundary_rows, unavailable = [], [], []
    for qid in selected:
        source = by_qid[qid]
        context = None
        if source["native_answer_archive"] is not None and source["media"] is not None:
            context = prepare_context(workspace, source)
        if context is None:
            require(dry_run, "Source evidence is unavailable")
            contexts.append({"qid": qid, "status": "requires_source_media", "context": None, "request_sha256": None})
            unavailable.append(qid)
            continue
        context_pin = write_json(workspace, output / "contexts" / (qid + ".json"), context)
        contexts.append({"qid": qid, "status": source["status"], "context": context_pin, "request_sha256": context["request_sha256"]})
        boundary_rows.append({"qid": qid, **context["request_boundary"], "preview_only": dry_run})
    telemetry = pin(workspace, telemetry_path) if telemetry_path is not None else None
    require(dry_run or telemetry is not None, "A hash-bound native telemetry implementation is required")
    job = {"schema": JOB_SCHEMA, "source_pool": POOL, "clean_vsi590k_training": True,
           "benchmark_trained_diagnostic": False, "snapshot": pin(workspace, snapshot_path),
           "selected_qids": selected, "contexts": contexts, "model": conversion.MODEL, "settings": conversion.SETTINGS,
           "worker_cap": 1, "paid_calls_maximum": 0 if dry_run else len(selected), "dry_run": dry_run,
           "runnable": not dry_run and snapshot["runnable"], "training_eligible": False,
           "native_telemetry": telemetry, "runtime": runtime_pins(workspace, telemetry_path),
           "admission_contract": ADMISSION_CONTRACT, "original_weights_required": True}
    job_pin = write_json(workspace, output / "job.json", job)
    check = {"schema": "clean-vsi590k-request-boundary-check-v1", "source_pool": POOL, "job": job_pin,
             "selected_count": len(selected), "serialized_request_count": len(boundary_rows), "requests": boundary_rows,
             "unmaterialized_qids": unavailable, "all_serialized_requests_checked": True,
             "all_selected_requests_materialized": not unavailable, "provider_calls": 0, "training_eligible": False}
    boundary_pin = write_json(workspace, output / "request_boundary.json", check)
    return {"job": job_pin, "request_boundary": boundary_pin, "selected": len(selected),
            "serialized_requests": len(boundary_rows), "runnable": job["runnable"], "provider_calls": 0}


def load_job(workspace, path, require_runnable=True):
    clean_path(workspace, path)
    job = read_json(workspace, path)
    require(job.get("schema") == JOB_SCHEMA and job.get("source_pool") == POOL and job.get("benchmark_trained_diagnostic") is False,
            "Diagnostic and clean conversion jobs cannot be mixed")
    require(job.get("model") == conversion.MODEL and job.get("settings") == conversion.SETTINGS
            and job.get("worker_cap") == 1 and job.get("admission_contract") == ADMISSION_CONTRACT
            and job.get("original_weights_required") is True, "Clean conversion contract changed")
    verify_pin(workspace, job["snapshot"])
    require(namespace(workspace, job["snapshot"]["path"]) == namespace(workspace, path), "Cross-namespace source snapshot")
    snapshot = load_snapshot(workspace, job["snapshot"]["path"], require_ready=require_runnable)
    require(type(job.get("dry_run")) is bool and job.get("runnable") is (not job["dry_run"] and snapshot["runnable"])
            and job.get("training_eligible") is False and job.get("clean_vsi590k_training") is True, "Clean job readiness/scope metadata changed")
    expected = select_qids(snapshot["accepted_qids"], len(job["selected_qids"]))
    require(job["selected_qids"] == expected and [item["qid"] for item in job["contexts"]] == expected, "Clean job selection differs from its accepted authority")
    telemetry_path = job["native_telemetry"]["path"] if job["native_telemetry"] is not None else None
    require(job["runtime"] == runtime_pins(workspace, telemetry_path), "Converter/runtime hash drift")
    if job["native_telemetry"] is not None:
        verify_pin(workspace, job["native_telemetry"])
    require(job["paid_calls_maximum"] == (0 if job["dry_run"] else len(expected)), "Paid-call bound changed")
    if require_runnable:
        require(job.get("runnable") is True and job.get("dry_run") is False and telemetry_path is not None, "Dry-run or requires_source_media jobs cannot authorize provider calls")
    rows = {row["qid"]: row for row in snapshot["rows"]}
    for item in job["contexts"]:
        if item["context"] is None:
            require(job["dry_run"] and not require_runnable, "Conversion source context is missing")
            continue
        require(namespace(workspace, item["context"]["path"]) == namespace(workspace, path), "Cross-namespace context")
        verify_pin(workspace, item["context"])
        actual = read_json(workspace, item["context"]["path"])
        require(actual == prepare_context(workspace, rows[item["qid"]]) and actual["request_sha256"] == item["request_sha256"], "Context/request differs from exact native-source projection")
    return job, snapshot


def require_api_lease(workspace, path, job_path, count, fresh=True):
    require(namespace(workspace, path) == namespace(workspace, job_path), "Clean API leases must remain in the clean job namespace")
    lease = read_json(workspace, path)
    require(lease.get("schema") == LEASE_SCHEMA and lease.get("source_pool") == POOL and lease.get("job") == pin(workspace, job_path), "Clean API lease does not bind this exact clean job")
    require(all(lease.get(key) is True for key in ("coordination_lease_passed", "collector_handshake_passed", "no_other_paid_calls")), "Missing supervisor/collector admission")
    require(lease.get("annotation_workers") == 1 and lease.get("concurrency_cap") == 1 and lease.get("max_calls") == count
            and lease.get("model") == conversion.MODEL, "Exactly one bounded annotation worker is permitted")
    require(isinstance(lease.get("work_id"), str) and lease["work_id"].startswith(POOL + "__"), "Clean lease cannot share diagnostic work identity")
    for key in ("owner", "coordination_lease_evidence", "collector_handshake_evidence"):
        require(isinstance(lease.get(key), str) and lease[key].strip(), "Incomplete clean-pool lease evidence")
    require(namespace(workspace, lease["supervisor_status"]["path"]) == namespace(workspace, job_path), "Cross-pool supervisor receipt")
    verify_pin(workspace, lease["supervisor_status"])
    now = datetime.now(timezone.utc)
    admitted = datetime.fromisoformat(lease["admitted_at"].replace("Z", "+00:00"))
    expires = datetime.fromisoformat(lease["expires_at"].replace("Z", "+00:00"))
    require(admitted.tzinfo is not None and expires.tzinfo is not None and admitted <= now < expires
            and (not fresh or (now - admitted).total_seconds() <= 300), "Stale or expired clean-pool API lease")
    return {**lease, "evidence_file": pin(workspace, path)}


def validate_response(response, payload):
    require(isinstance(response.get("thoughts"), str), "Missing exposed native thoughts telemetry")
    require(response.get("model") == conversion.MODEL and response.get("output_budget_tokens") == conversion.SETTINGS["max_output_tokens"], "Provider request model/budget telemetry mismatch")
    raw = response.get("raw_response")
    require(isinstance(raw, list) and len(raw) == 1 and isinstance(raw[0], dict), "Missing native SDK response")
    native = raw[0]
    candidates = native.get("candidates", [])
    require(len(candidates) == 1 and candidates[0].get("finish_reason") == "STOP"
            and response.get("finish_reason") == "STOP" and response.get("tool_budget_terminal") is False, "Capped or incomplete native output cannot be admitted")
    parts = candidates[0].get("content", {}).get("parts", [])
    require(parts and all(isinstance(p, dict) and isinstance(p.get("text"), str) and not p.get("function_call") for p in parts), "Unexpected native annotation response parts")
    require("".join(p["text"] for p in parts if not p.get("thought")) == response.get("content")
            and "".join(p["text"] for p in parts if p.get("thought")) == response["thoughts"], "Native content/thoughts disagree with retained telemetry")
    require(native.get("usage_metadata") == response.get("usage") and native.get("model_version") == response.get("provider_served_model"), "Native usage/model telemetry mismatch")
    events = response.get("events", [])
    require(len(events) == 2 and events[0].get("event") == "native_google_call_start_v1"
            and events[1].get("event") == "native_google_call_terminal_v1"
            and events[0].get("call_id") == response.get("call_id") == events[1].get("call_id"), "Missing one-to-one native call telemetry")
    require(isinstance(response.get("call_id"), str) and response["call_id"]
            and all(events[0].get(key) == response.get(key) for key in ("where", "model", "output_budget_tokens")),
            "Native start/terminal model or budget mismatch")
    require(events[1] == {key: value for key, value in response.items() if key not in ("events", "sdk_version")}, "Native terminal telemetry changed")
    require(response.get("native_candidates") == candidates, "Native candidate archive changed")
    return conversion.validate_response(response, payload)


def native_transport(request, telemetry):
    from google import genai
    from google.genai import types

    require(bool(os.environ.get("GOOGLE_API_KEY")), "The operator must supply the authorized provider credential")
    spec = importlib.util.spec_from_file_location("clean_vsi590k_native_telemetry", telemetry["path"])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    config = types.GenerateContentConfig(**request["config"])
    sink = []
    call = module._Call(sink, "student_grounded_conversion", "annotation", request["model"], config)
    with genai.Client(api_key=os.environ["GOOGLE_API_KEY"], http_options=types.HttpOptions(timeout=1800000, retry_options=types.HttpRetryOptions(attempts=1))) as client:
        response = client.models.generate_content(model=request["model"], contents=request["contents"], config=config)
    call.observe(response)
    call.finish()
    return {**call.row, "events": sink, "sdk_version": genai.__version__}


def run(workspace, job_path, lease_path, output):
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == "", "Clean conversion is CPU/API-only")
    expected_count = len(read_json(workspace, job_path)["selected_qids"])
    lease = require_api_lease(workspace, lease_path, job_path, expected_count)
    job, snapshot = load_job(workspace, job_path)
    require_api_lease(workspace, lease_path, job_path, len(job["selected_qids"]), fresh=False)
    output = clean_path(workspace, output)
    root = namespace(workspace, job_path)
    require(namespace(workspace, output) == root and not output.exists(), "Use a fresh run inside the clean job namespace")
    rows = {row["qid"]: row for row in snapshot["rows"]}
    with (root / "annotation.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        write_json(workspace, output / "run.json", {"schema": RUN_SCHEMA, "source_pool": POOL,
                   "job": pin(workspace, job_path), "lease": lease, "runtime": job["runtime"],
                   "converter_identity": lease["owner"], "training_eligible": False})
        for item in job["contexts"]:
            require_api_lease(workspace, lease_path, job_path, len(job["selected_qids"]), fresh=False)
            verify_pin(workspace, item["context"])
            context = read_json(workspace, item["context"]["path"])
            require(context == prepare_context(workspace, rows[item["qid"]]), "Source changed before provider call")
            request_boundary(context["request"])
            directory = output / item["qid"]
            request_pin = write_json(workspace, directory / "request.json", context["request"])
            started = write_json(workspace, Path(job_path).parent / "consumed" / (item["qid"] + ".json"),
                                 {"qid": item["qid"], "job": pin(workspace, job_path), "request": request_pin,
                                  "started_at": datetime.now(timezone.utc).isoformat()})
            try:
                response = native_transport(context["request"], job["native_telemetry"])
            except Exception as error:
                response = {"status": "error", "error_type": type(error).__name__, "raw_response": [], "finish_reason": None, "usage": None}
            provider_pin = write_json(workspace, directory / "provider.json", response)
            record = {"source_pool": POOL, "max_output_tokens": context["request"]["config"]["max_output_tokens"], "qid": item["qid"], "request": request_pin, "started": started,
                      "provider": provider_pin, "context": item["context"], "source_row_sha256": context["source_row_sha256"],
                      "training_eligible": False}
            try:
                candidate = validate_response(response, context["payload"])
            except (ValueError, KeyError, TypeError, OverflowError) as error:
                record.update(status="REJECTED", reason=str(error) if type(error) is ValueError else type(error).__name__)
            else:
                record.update(status="AWAITING_INDEPENDENT_GROUNDED_REVIEW",
                              candidate=write_json(workspace, directory / "candidate.json", candidate))
            write_json(workspace, directory / "decision.json", record)
        write_json(workspace, output / "summary.json", {"source_pool": POOL, "scheduled": len(job["contexts"]), "provider_calls": len(job["contexts"]), "accepted_targets": 0})
    return review_bundle(workspace, output, output / "review_bundle.json")


def verified_run(workspace, directory):
    directory = clean_path(workspace, directory)
    header = read_json(workspace, directory / "run.json")
    require(header.get("schema") == RUN_SCHEMA and header.get("source_pool") == POOL, "Not a clean-pool conversion run")
    verify_pin(workspace, header["job"])
    require(namespace(workspace, header["job"]["path"]) == namespace(workspace, directory), "Cross-namespace run/job")
    job, snapshot = load_job(workspace, header["job"]["path"])
    require(header.get("runtime") == job["runtime"], "Run/runtime source binding mismatch")
    lease = header["lease"]
    require(namespace(workspace, lease["evidence_file"]["path"]) == namespace(workspace, directory), "Cross-pool run lease")
    verify_pin(workspace, lease["evidence_file"])
    require(read_json(workspace, lease["evidence_file"]["path"]) == {key: value for key, value in lease.items() if key != "evidence_file"}
            and lease.get("schema") == LEASE_SCHEMA and lease.get("source_pool") == POOL
            and lease.get("job") == header["job"] and header.get("converter_identity") == lease.get("owner"), "Run/API-lease source binding mismatch")
    records, call_ids = [], set()
    for item in job["contexts"]:
        record = read_json(workspace, directory / item["qid"] / "decision.json")
        context = read_json(workspace, item["context"]["path"])
        require(record.get("source_pool") == POOL and record.get("qid") == item["qid"] and record.get("context") == item["context"]
                and record.get("source_row_sha256") == context["source_row_sha256"], "Conversion decision lost source provenance")
        for key in ("request", "provider", "started"):
            expected_path = (Path(header["job"]["path"]).parent / "consumed" / (item["qid"] + ".json") if key == "started"
                             else directory / item["qid"] / (key + ".json"))
            require(Path(record[key]["path"]) == expected_path, "Cross-namespace or cross-question conversion receipt")
            verify_pin(workspace, record[key])
        started = read_json(workspace, record["started"]["path"])
        require(started.get("qid") == item["qid"] and started.get("job") == header["job"] and started.get("request") == record["request"], "Provider-boundary consumption receipt mismatch")
        require(read_json(workspace, record["request"]["path"]) == context["request"], "Retained request differs from the bound projection")
        response = read_json(workspace, record["provider"]["path"])
        if response.get("status") == "ok":
            call_id = response.get("call_id")
            require(isinstance(call_id, str) and call_id and call_id not in call_ids, "Duplicate or missing native annotation call identity")
            call_ids.add(call_id)
        if "candidate" in record:
            require(Path(record["candidate"]["path"]) == directory / item["qid"] / "candidate.json", "Cross-pool or cross-question candidate")
            verify_pin(workspace, record["candidate"])
            require(record["status"] == "AWAITING_INDEPENDENT_GROUNDED_REVIEW" and
                    read_json(workspace, record["candidate"]["path"]) == validate_response(response, context["payload"]), "Candidate differs from native provider output")
        else:
            require(record.get("status") == "REJECTED", "Unvalidated conversion cannot be admitted")
        records.append((item, context, record, pin(workspace, directory / item["qid"] / "decision.json")))
    return header, job, snapshot, records


def review_bundle(workspace, run_directory, output):
    header, job, _, records = verified_run(workspace, run_directory)
    template = {"schema": REVIEW_SCHEMA, "source_pool": POOL, "admission_contract": ADMISSION_CONTRACT,
                "reviewer": "", "independent_of_converter": False, "review_method": "agent_exact_evidence_review",
                "run": pin(workspace, Path(run_directory) / "run.json"), "decisions": []}
    for item, _, record, decision_pin in records:
        candidate = read_json(workspace, record["candidate"]["path"]) if "candidate" in record else {"claims": []}
        template["decisions"].append({"qid": item["qid"], "decision": decision_pin, "verdict": "reject",
                                      "claim_verdicts": [{"id": c["id"], "supported": False} for c in candidate["claims"]],
                                      "checks": {key: False for key in conversion.REVIEW_CHECKS}})
    return write_json(workspace, output, {"schema": "clean-vsi590k-grounded-review-bundle-v1", "source_pool": POOL,
                      "review_template": template, "contexts": [item["context"] for item in job["contexts"]],
                      "snapshot": job["snapshot"], "instruction": "Review every claim of every admitted example against exact source evidence. Unreviewed examples remain unaccepted. Native finals are provenance only. Never infer support from a sample."})


def accepted_manifest(workspace, run_directory, review_path):
    header, job, snapshot, records = verified_run(workspace, run_directory)
    require(namespace(workspace, review_path) == namespace(workspace, run_directory), "Clean reviews cannot share diagnostic receipt paths")
    review = read_json(workspace, review_path)
    require(review.get("schema") == REVIEW_SCHEMA and review.get("source_pool") == POOL
            and review.get("admission_contract") == ADMISSION_CONTRACT, "Wrong clean-pool review/admission contract")
    require(review.get("independent_of_converter") is True and review.get("review_method") == "agent_exact_evidence_review"
            and isinstance(review.get("reviewer"), str) and review["reviewer"].strip()
            and review["reviewer"] != header["converter_identity"], "Independent claim-by-claim review is required")
    require(review.get("run") == pin(workspace, Path(run_directory) / "run.json"), "Review does not bind this exact clean run")
    decisions = review.get("decisions", [])
    counts = Counter(d.get("qid") for d in decisions)
    require(all(value == 1 for value in counts.values()) and set(counts) <= set(job["selected_qids"]), "Duplicate or foreign reviewed qid")
    reviewed = {decision["qid"]: decision for decision in decisions}
    sources = {row["qid"]: row for row in snapshot["rows"]}
    rows, rejected, unreviewed = [], [], []
    for item, context, record, decision_pin in records:
        qid = item["qid"]
        if qid not in reviewed:
            unreviewed.append(qid)
            continue
        verdict = reviewed[qid]
        require(verdict.get("decision") == decision_pin and verdict.get("verdict") in ("accept", "reject"), "Independent decision is not bound to this exact example")
        if verdict["verdict"] == "reject":
            rejected.append(qid)
            continue
        require("candidate" in record and all(verdict.get("checks", {}).get(key) is True for key in conversion.REVIEW_CHECKS), "Unsupported, capped or incomplete conversion cannot be admitted")
        candidate = read_json(workspace, record["candidate"]["path"])
        claims = verdict.get("claim_verdicts", [])
        require(Counter(v.get("id") for v in claims) == Counter(c["id"] for c in candidate["claims"])
                and all(v.get("supported") is True for v in claims), "Every claim needs an independent supported verdict")
        source = sources[qid]
        require(source["status"] == "ready" and source["media"]["pixels_verified"] is True, "Only authenticated original RGB may enter clean training")
        media, original = source["media"], source["source_row"]
        student_input = {"question": original["question"], "options": original["options"],
                         "frames": [{key: value[key] for key in ("path", "sha256", "size_bytes")} for value in media["bindings"]["frames"]],
                         **{key: media[key] for key in ("frame_indices", "timestamps", "fps", "total_num_frames")}}
        rows.append({"qid": qid, "source_pool": POOL, "dataset": original["dataset"], "scene": media["physical_scene"],
                     "category": original["question_type"], "student_input": student_input, "target": candidate["target"],
                     "source_snapshot": job["snapshot"], "source_row_sha256": context["source_row_sha256"],
                     "conversion": {"decision": decision_pin, "candidate": record["candidate"], "request": record["request"],
                                    "provider": record["provider"], "review": pin(workspace, review_path), "semantic_grounding_verified": True}})
    return {"schema": MANIFEST_SCHEMA, "source_pool": POOL, "clean_vsi590k_training": True,
            "benchmark_trained_diagnostic": False, "benchmark_improvement_claim": False, "detailed_distillation": True,
            "original_weights_required": True, "students": ["OneThinker-8B", "Qwen3.5-9B"],
            "admission_contract": ADMISSION_CONTRACT, "snapshot": job["snapshot"], "job": header["job"],
            "run": pin(workspace, Path(run_directory) / "run.json"), "review": pin(workspace, review_path),
            "selected_qids": job["selected_qids"], "accepted_count": len(rows), "rows": rows,
            "rejected_qids": rejected, "unreviewed_qids": unreviewed}


def admit(workspace, run_directory, review_path, output):
    output = clean_path(workspace, output)
    require(namespace(workspace, output) == namespace(workspace, run_directory) and not output.exists(), "Use a new clean admission namespace")
    manifest = accepted_manifest(workspace, run_directory, review_path)
    manifest_pin = write_json(workspace, output / "manifest.json", manifest)
    receipt = write_json(workspace, output / "review_receipt.json", {"schema": "clean-vsi590k-review-receipt-v1", "source_pool": POOL,
                         "admission_contract": ADMISSION_CONTRACT, "review": manifest["review"], "run": manifest["run"],
                         "accepted_qids": [r["qid"] for r in manifest["rows"]], "unreviewed_qids": manifest["unreviewed_qids"]})
    return write_json(workspace, output / "index.json", {"schema": INDEX_SCHEMA, "source_pool": POOL,
                      "manifest": manifest_pin, "review_receipt": receipt, "snapshot": manifest["snapshot"],
                      "accepted_qids": [r["qid"] for r in manifest["rows"]], "original_weights_required": True})


def load_admitted(workspace, path):
    clean_path(workspace, path)
    index = read_json(workspace, path)
    require(index.get("schema") == INDEX_SCHEMA and index.get("source_pool") == POOL
            and index.get("original_weights_required") is True, "Only clean-pool admission indexes may select clean training targets")
    for key in ("manifest", "review_receipt", "snapshot"):
        require(namespace(workspace, index[key]["path"]) == namespace(workspace, path), "Cross-pool admission binding")
        verify_pin(workspace, index[key])
    manifest = read_json(workspace, index["manifest"]["path"])
    require(manifest.get("schema") == MANIFEST_SCHEMA and manifest.get("source_pool") == POOL, "Diagnostic manifest cannot enter clean training")
    for key in ("run", "review"):
        verify_pin(workspace, manifest[key])
    expected = accepted_manifest(workspace, Path(manifest["run"]["path"]).parent, manifest["review"]["path"])
    require(manifest == expected and index["accepted_qids"] == [r["qid"] for r in manifest["rows"]]
            and index["snapshot"] == manifest["snapshot"], "Admission index differs from exact reviewed examples")
    receipt = read_json(workspace, index["review_receipt"]["path"])
    require(receipt == {"schema": "clean-vsi590k-review-receipt-v1", "source_pool": POOL,
                       "admission_contract": ADMISSION_CONTRACT, "review": manifest["review"], "run": manifest["run"],
                       "accepted_qids": index["accepted_qids"], "unreviewed_qids": manifest["unreviewed_qids"]},
            "Independent review receipt mismatch")
    return manifest


def student_rows(workspace, index_path, student, initialization):
    require(student in ("OneThinker-8B", "Qwen3.5-9B") and initialization == "original_weights", "Every clean student must start from its original weights, not a diagnostic adapter")
    manifest = load_admitted(workspace, index_path)
    return [{"qid": row["qid"], "student_input": row["student_input"], "target": row["target"]} for row in manifest["rows"]]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Separate VSI-590K source admission and grounded conversion; dry-run never contacts a provider")
    sub = parser.add_subparsers(dest="command", required=True)
    snapshot = sub.add_parser("snapshot")
    dry = sub.add_parser("dry-run")
    for command in (snapshot, dry):
        command.add_argument("--workspace", required=True)
        command.add_argument("--run-root", required=True)
        command.add_argument("--census-root", required=True)
        command.add_argument("--membership")
        command.add_argument("--source-map")
        command.add_argument("--output", required=True)
    snapshot_mode = snapshot.add_mutually_exclusive_group()
    snapshot_mode.add_argument("--allow-missing", action="store_true")
    snapshot_mode.add_argument("--strict", action="store_true", help="Refuse incomplete sources and print every discoverable missing path and SHA expectation")
    dry.add_argument("--count", type=int, required=True)
    dry.add_argument("--telemetry")
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--workspace", required=True)
    prepare_parser.add_argument("--snapshot", required=True)
    prepare_parser.add_argument("--output", required=True)
    prepare_parser.add_argument("--count", type=int, required=True)
    prepare_parser.add_argument("--telemetry", required=True)
    run_parser = sub.add_parser("run")
    for key in ("workspace", "job", "lease", "output"):
        run_parser.add_argument("--" + key, required=True)
    accept = sub.add_parser("accept")
    for key in ("workspace", "run", "review", "output"):
        accept.add_argument("--" + key, required=True)
    check = sub.add_parser("check")
    check.add_argument("--workspace", required=True)
    check.add_argument("--job", required=True)
    args = parser.parse_args(argv)
    if args.command == "dry-run":
        root = local_path(args.workspace, Path(args.output)) / POOL
        source = freeze(args.workspace, args.run_root, args.census_root, root / "snapshots/r1313",
                        args.membership, args.source_map, allow_missing=True)
        result = prepare(args.workspace, source["path"], root / "jobs/r1313", args.count, dry_run=True, telemetry_path=args.telemetry)
    elif args.command == "snapshot":
        try:
            result = freeze(args.workspace, args.run_root, args.census_root, args.output, args.membership, args.source_map,
                            args.allow_missing, strict=args.strict)
        except SnapshotIncomplete as error:
            print(json.dumps(error.inventory, indent=2))
            return 2
    elif args.command == "prepare":
        result = prepare(args.workspace, args.snapshot, args.output, args.count, telemetry_path=args.telemetry)
    elif args.command == "run":
        result = run(args.workspace, args.job, args.lease, args.output)
    elif args.command == "accept":
        result = admit(args.workspace, args.run, args.review, args.output)
    else:
        job, _ = load_job(args.workspace, args.job, require_runnable=False)
        result = {"verified": True, "source_pool": POOL, "selected": len(job["selected_qids"]), "runnable": job["runnable"]}
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
