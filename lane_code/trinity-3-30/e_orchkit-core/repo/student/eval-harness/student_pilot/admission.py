import importlib.util
import math
import re
from pathlib import Path

from .common import ARTIFACTS, CONTRACT, CONTRACT_SHA, DONOR, MEMBERSHIP, MEMBERSHIP_SHA, PILOT, REGISTRY, REGISTRY_SHA, SCORER_LIB, SCORER_MAIN, binding, load_json, write_once
from .split import make_split, physical_group

ANSWER_KEY_SHA = "c23cb4d5e80517ee768829301c2fcd95b9dae43ade30249d8dbaf37de7cc8532"
SPLIT_PATH = ARTIFACTS / "data/split.json"


def authorities():
    pins = {"contract": binding(CONTRACT, CONTRACT_SHA), "canonical_membership": binding(MEMBERSHIP, MEMBERSHIP_SHA), "selected_frame_registry": binding(REGISTRY, REGISTRY_SHA)}
    contract = load_json(CONTRACT)
    subset_pin = contract["membership"]
    pins["donor_subset"] = binding(subset_pin["sealed_subset_path"], subset_pin["sealed_subset_sha256"])
    inference_pin = contract["inference_dataset"]
    pins["inference_dataset"] = binding(inference_pin["path"], inference_pin["sha256"])
    split = load_json(SPLIT_PATH)
    derived = make_split(load_json(MEMBERSHIP), load_json(subset_pin["sealed_subset_path"])["members"])
    if any(split.get(key) != value for key, value in derived.items()) or split["bindings"] != pins:
        raise ValueError("Frozen split or its source bindings changed")
    if len(split["train_candidate_qids"]) != 201 or len(split["heldout_qids"]) != 63:
        raise ValueError("Frozen training/holdout cohort sizes changed")
    pins["split"] = binding(SPLIT_PATH)
    return contract, split, pins, load_json(inference_pin["path"])


def native_final(entry):
    trace = entry.get("trace", {})
    messages = trace.get("messages", []) if isinstance(trace, dict) else trace
    finals = [(index, message) for index, message in enumerate(messages)
              if message.get("role", "").lower() in ("ai", "aimessage") and not message.get("tool_calls")]
    if not finals:
        raise ValueError("No committed native final; predictions are not an answer authority")
    index, final = finals[-1]
    metadata = final.get("response_metadata", {})
    if final.get("provenance") != "provider" or metadata.get("finish_reason") != "STOP" or metadata.get("model_name") != "gemini-3.1-pro-preview":
        raise ValueError("Final is not a complete native response from the pinned teacher")
    def text(content):
        return content if isinstance(content, str) else "\n".join(part.get("text", "") for part in content if part.get("type") == "text")
    native = text(final.get("content", ""))
    raw = final.get("raw_response", {})
    if text(raw.get("content", "")) != native or raw.get("tool_calls") or raw.get("invalid_tool_calls"):
        raise ValueError("Committed text does not match its native raw response")
    answers = list(re.finditer(r"<ANSWER>(.*?)</ANSWER>", native, flags=re.I | re.S))
    if len(answers) != 1 or not answers[0].group(1).strip():
        raise ValueError("A single complete native answer block is required")
    answer = answers[0]
    return {
        "message_index": index, "message_id": final.get("id"), "native_final": native,
        "native_answer_block": answer.group(0),
        "target": "<answer>" + answer.group(1) + "</answer>",
        "target_transform": "Copy native answer-block content verbatim; lowercase only its delimiters; omit thoughts and explanations for infrastructure smoke",
        "response_metadata": metadata,
    }


def video_timing(video_path, indices):
    import av

    with av.open(str(video_path), mode="r") as container:
        videos = list(container.streams.video)
        if len(videos) != 1:
            raise ValueError("Expected exactly one source video stream")
        stream = videos[0]
        if stream.average_rate is None or stream.frames <= 0:
            raise ValueError("Source video lacks original FPS or frame count")
        fps, count = float(stream.average_rate), stream.frames
        timestamps = sorted(float(packet.pts * packet.time_base) for packet in container.demux(stream) if packet.pts is not None)
        width, height = stream.width, stream.height
    if len(timestamps) != count or fps <= 0 or not math.isfinite(fps):
        raise ValueError("Source packet timestamps and original frame count disagree")
    if any(not math.isclose(timestamp, index / fps, rel_tol=0, abs_tol=1e-6) for index, timestamp in enumerate(timestamps)):
        raise ValueError("Source is not zero-origin constant-frame-rate video; do not invent timestamps")
    if max(indices) >= count:
        raise ValueError("Selected index exceeds original source-video frame count")
    return {
        "fps": fps, "total_num_frames": count, "timestamps": [timestamps[index] for index in indices],
        "source_width_height": [width, height], "packet_timestamps_verified": len(timestamps),
        "timestamp_source": "Original source-video presentation timestamps; all packet PTS verified against original frame indices/FPS",
    }


def source_candidate(qid):
    contract, split, pins, inference = authorities()
    qid = str(qid)
    if qid not in split["train_candidate_qids"] or qid in split["heldout_qids"]:
        raise ValueError("Smoke source must belong to the frozen training split")
    matches = [row for row in inference if str(row["id"]) == qid]
    if len(matches) != 1:
        raise ValueError("Inference identity is missing or duplicated")
    item = matches[0]
    scene, category, dataset = item["scene_name"], item["question_type"], item["dataset"]
    if physical_group(dataset, scene) not in split["train_group_ids"]:
        raise ValueError("Question scene is outside frozen training groups")
    directory = DONOR / "run" / category / contract["experiment_tag"] / "finalized" / qid
    paths = {"clean": directory / f"trace_{qid}_clean.json", "raw": directory / f"trace_{qid}.json", "attempt": directory / f"attempt_{qid}.json"}
    sources = {key: binding(path) for key, path in paths.items()}
    entries = {key: load_json(path) for key, path in paths.items()}
    attempt = entries["attempt"]
    if str(attempt.get("question_id")) != qid or attempt.get("status") != "completed" or attempt.get("arm") != contract["arm"] or attempt.get("requested_model") != contract["model"]["requested_id"]:
        raise ValueError("Native attempt is incomplete or belongs to a different donor")
    finals = {}
    for key in ("clean", "raw"):
        entry = entries[key]
        if (str(entry.get("question_id")), entry.get("scene_name"), entry.get("question_type"), entry.get("question")) != (qid, scene, category, item["question"]):
            raise ValueError(f"Native {key} identity differs from pinned inference")
        if entry.get("error") or entry.get("budget_terminal") or entry.get("orphan_tool_drop"):
            raise ValueError("Native trace reports an incomplete or repaired terminal")
        receipt = entry["run_receipt"]
        if receipt["effective_contract_sha256"] != CONTRACT_SHA or receipt["model"] != contract["model"]:
            raise ValueError("Native trace is not bound to the pinned teacher contract")
        if entry["initial_visual_input"]["mode"] != "text_only_control" or receipt["selected_frames_sha256"] != REGISTRY_SHA:
            raise ValueError("Native teacher input policy changed")
        finals[key] = native_final(entry)
    if finals["clean"] != finals["raw"]:
        raise ValueError("Clean and raw native finals disagree")
    external = entries["raw"]["run_receipt"]["external_data"]
    external_pins = {key: binding(external[key]["path"], external[key]["sha256"]) for key in ("frames", "source_videos")}
    selection = load_json(REGISTRY)[scene]
    indices, names = selection["indices"], selection["frame_names"]
    assets = [asset for asset in load_json(external_pins["frames"]["path"])["assets"] if asset["scene"] == scene]
    assets.sort(key=lambda asset: asset["ordinal"])
    if len(indices) != 32 or [Path(asset["path"]).stem for asset in assets] != names or any(asset["source"] != "preextracted_png" for asset in assets):
        raise ValueError("RGB registry does not match the fixed original selected-frame identities")
    frames = [binding(asset["path"], asset["sha256"]) for asset in assets]
    videos = [asset for asset in load_json(external_pins["source_videos"]["path"])["assets"] if asset["scene"] == scene and asset["dataset"] == dataset]
    if len(videos) != 1:
        raise ValueError("Original source video identity is missing or duplicated")
    video = binding(videos[0]["path"], videos[0]["sha256"])
    timing = video_timing(video["path"], indices)
    student_input = {
        "question": item["question"], "options": item.get("options", []),
        "frames": frames, "frame_indices": indices,
        **{key: timing[key] for key in ("timestamps", "fps", "total_num_frames")},
    }
    row = {
        "qid": qid, "scene": scene, "dataset": dataset, "category": category,
        "student_input": student_input, "target": finals["raw"]["target"],
        "native_answer_archive": finals["raw"], "sources": sources,
        "external_registries": external_pins, "source_video": video, "video_timing": timing,
        "teacher_input": "Privileged GT perception; initial text-only control; visual tool returns may occur",
        "student_input_boundary": "Only original RGB32, original timestamps, question, and options",
    }
    return row, pins, contract, entries["raw"]


def resolve_answer_key(path=None):
    pointer = PILOT / "development/label_path.txt"
    if path is None:
        if not pointer.is_file():
            raise ValueError(f"Canonical offline answer-key location is unresolved; supply {pointer} or --answer-key. Required SHA256: {ANSWER_KEY_SHA}")
        path = pointer.read_text().strip()
    path = Path(path)
    if not path.is_absolute():
        raise ValueError("Canonical answer-key path must be absolute")
    return binding(path, ANSWER_KEY_SHA)


def load_scorer(contract):
    spec = contract["scorer"]
    if spec["implementation_path"] != str(SCORER_LIB) or spec["evaluator_path"] != str(SCORER_MAIN):
        raise ValueError("Pinned offline scorer paths changed")
    pins = {"implementation": binding(SCORER_LIB, spec["implementation_sha256"]), "evaluator": binding(SCORER_MAIN, spec["evaluator_sha256"])}
    module_spec = importlib.util.spec_from_file_location("student_pilot_offline_scoring", SCORER_LIB)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module, pins


def build_manifest(qid, answer_key_path):
    answer_key = resolve_answer_key(answer_key_path)
    row, pins, contract, raw = source_candidate(qid)
    labels = load_json(answer_key["path"])
    if not isinstance(labels, list):
        raise ValueError("Expected canonical offline answer key to be a list")
    matches = [item for item in labels if str(item["id"]) == row["qid"]]
    if len(matches) != 1:
        raise ValueError("Canonical answer identity is missing or duplicated")
    label = matches[0]
    identity = {"scene_name": row["scene"], "dataset": row["dataset"], "question_type": row["category"], "question": row["student_input"]["question"], "options": row["student_input"]["options"]}
    if any(label.get(key, [] if key == "options" else None) != value for key, value in identity.items()):
        raise ValueError("Canonical labels and source inference identity disagree")
    scorer, scorer_pins = load_scorer(contract)
    if scorer.extract_response(raw, strict=True) != row["native_answer_archive"]["native_final"]:
        raise ValueError("Offline scorer did not select the archived native final")
    record, metrics = scorer._score_entry(raw, label, strict=True)
    score = record.get("accuracy", record.get("MRA"))
    if score != 1.0 or metrics["is_correct"] is not True:
        raise ValueError(f"Native answer for training qid {qid} is not fully correct under the pinned offline scorer")
    return {
        "schema": "source-backed-native-answer-smoke-v1",
        "infrastructure_only": True, "detailed_distillation": False,
        "benchmark_trained_diagnostic": True, "benchmark_improvement_claim": False,
        "future_clean_student_restarts_original_weights": True,
        "bindings": pins, "answer_key": answer_key, "scorer": scorer_pins,
        "offline_admission": {"qid": row["qid"], "strict_native_final": True, "fully_correct": True, "score": score, "scoring_record": record},
        "native_answer_archive_scope": "Exact local source-bound smoke subset; not answer-bank registration",
        "rows": [row],
    }


def prepare_smoke(qid, answer_key_path, output_path):
    from .batches import encode_row, load_processor

    manifest = build_manifest(qid, answer_key_path)
    _, audit = encode_row(load_processor(), manifest["rows"][0])
    write_once(output_path, manifest)
    write_once(Path(output_path).with_suffix(".input_audit.json"), audit)
    return {"status": "ADMITTED_INFRASTRUCTURE_ONLY", "qid": str(qid), "rows": 1, "offline_fully_correct": True, "frame_count": audit["frame_count"], "video_grid_thw": audit["video_grid_thw"], "manifest": binding(output_path)}


def load_admitted_manifest(path):
    manifest = load_json(path)
    if manifest.get("schema") != "source-backed-native-answer-smoke-v1" or len(manifest.get("rows", [])) != 1:
        raise ValueError("Smoke requires exactly one bounded source-backed admitted training row")
    expected = build_manifest(manifest["rows"][0]["qid"], manifest["answer_key"]["path"])
    if manifest != expected:
        raise ValueError("Smoke manifest differs from freshly verified source/admission evidence")
    return manifest


def inspect_candidate(qid, output_path):
    from .batches import encode_row, load_processor

    row, pins, _, _ = source_candidate(qid)
    _, audit = encode_row(load_processor(), row)
    report = {"status": "SOURCE_AND_RGB_VERIFIED_NOT_GRADED", "offline_correctness_verified": False, "infrastructure_only": True, "detailed_distillation": False, "row": row, "bindings": pins, "input_audit": audit}
    write_once(output_path, report)
    return {"status": report["status"], "qid": str(qid), "frame_count": audit["frame_count"], "video_grid_thw": audit["video_grid_thw"], "report": str(output_path)}
