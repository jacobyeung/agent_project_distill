import importlib.metadata
from collections import Counter
from pathlib import Path

from .admission import DIVISION_PATH, authorities, load_scorer, resolve_answer_key, source_candidate, video_timing
from .common import ARTIFACTS, REGISTRY, REPO, binding, digest_json, load_json, write_once
from .students import get_student, training_parameters, validate_snapshot
from .storage import write_output
from .conversion import DIVISION_SHA, load_accepted, repo_output, verify_pin
from .division import physical_group

TRAINING = {"seed": 17, "epochs": 1, "optimizer": "AdamW", "learning_rate": 1e-5,
            "weight_decay": 0.0, "gradient_accumulation": 4, "microbatch_size": 1,
            "clip_norm": 1.0, "max_target_tokens_including_eos": 8192, "max_sequence_tokens": 16384,
            "trainable_parameters": 48070400, "base_restart": "original_checkpoint_only",
            "target_truncation": False, "shuffle": "python_random_seed17_once"}
GENERATION = {"seed": 17, "do_sample": False, "num_beams": 1, "num_return_sequences": 1,
              "initial_max_new_tokens": 16384, "retry_max_new_tokens": 32768,
              "use_cache": True, "retry_policy": "one_fresh_32768_attempt_only_if_recorded_16384_cap_and_not_pinned_full_credit"}
RGB = {"frame_count": 32, "do_sample_frames": False,
       "size": {"shortest_edge": 32 * 128 * 128, "longest_edge": 32 * 384 * 384},
       "timing": "original_source_indices_and_fps_native_processor", "question_options": "verbatim; null options mean no options"}
FLAGS = {"infrastructure_only": False, "detailed_distillation": True,
         "benchmark_trained_diagnostic": True, "benchmark_improvement_claim": False,
         "score_nomination_allowed": False, "future_clean_student_restarts_original_weights": True}


def runtime_bindings():
    files = ("__init__.py", "cli.py", "diagnostic.py", "diagnostic_data.py", "trace_contract.py", "conversion.py", "admission.py", "common.py", "division.py", "lease.py", "adapters.py", "batches.py", "runner.py", "students.py", "storage.py", "infrastructure_smoke.py")
    return [binding(REPO / "student_pilot" / name) for name in files] + [binding(REPO / name) for name in ("requirements.txt", "scripts/diagnostic_gpu_batch.sh")]


def versions():
    return {name: importlib.metadata.version(name) for name in ("torch", "torchvision", "transformers", "peft", "accelerate", "numpy", "Pillow", "av")}


def training_settings(student="onethinker"):
    return {**TRAINING, "trainable_parameters": training_parameters(student)}


def checkpoint_bindings(student="onethinker"):
    snapshot = validate_snapshot(student)
    index = load_json(snapshot / "model.safetensors.index.json")
    shards = sorted(set(index["weight_map"].values()))
    if not shards or any(Path(name).name != name or not name.endswith(".safetensors") for name in shards):
        raise ValueError("Unexpected original checkpoint shard closure")
    files = ["config.json", "model.safetensors.index.json", "tokenizer.json", "tokenizer_config.json"]
    files += [name for name in ("generation_config.json", "preprocessor_config.json", "video_preprocessor_config.json", "processor_config.json", "chat_template.jinja", "chat_template.json", "special_tokens_map.json", "added_tokens.json") if (snapshot / name).is_file()]
    return {"revision": snapshot.name, "files": [binding(snapshot / name) for name in files],
            "weight_shards": [binding(snapshot / name) for name in shards]}


def prepare_protocol(output, student="onethinker", scratch_root=None):
    _, _, pins, _ = authorities()
    binding(DIVISION_PATH, DIVISION_SHA)
    protocol = {"schema": "fixed-student-diagnostic-protocol-v1", **FLAGS, "student": student,
                "training": training_settings(student), "generation": GENERATION, "rgb": RGB,
                "authorities": pins, "base": checkpoint_bindings(student), "runtime": runtime_bindings(), "versions": versions()}
    protocol["base_sha256"] = digest_json(protocol["base"])
    write_output(output, protocol, scratch_root)
    return {"status": "PROTOCOL_FROZEN_NO_GPU", "protocol": binding(output), "base_sha256": protocol["base_sha256"]}


def load_protocol(path, weights=False, student=None):
    protocol = load_json(path)
    declared_student = protocol.get("student", "onethinker")
    if student is not None and student != declared_student:
        raise ValueError("Requested student differs from the frozen protocol")
    settings = training_settings(declared_student)
    if protocol.get("schema") != "fixed-student-diagnostic-protocol-v1" or any(protocol.get(key) != value for key, value in (("training", settings), ("generation", GENERATION), ("rgb", RGB))):
        raise ValueError("Predeclared diagnostic settings changed")
    if protocol["base"].get("revision") != get_student(declared_student)["snapshot"].name or protocol["base_sha256"] != digest_json(protocol["base"]):
        raise ValueError("Original model snapshot identity changed")
    _, _, pins, _ = authorities()
    if pins != protocol["authorities"] or versions() != protocol["versions"]:
        raise ValueError("Diagnostic source authorities or software environment changed")
    for pin in protocol["runtime"] + protocol["base"]["files"] + (protocol["base"]["weight_shards"] if weights else []):
        verify_pin(pin)
    return protocol


def rgb_arrays(row):
    from transformers.video_utils import VideoMetadata
    from .batches import load_rgb

    inputs = row["student_input"]
    arrays, sizes = load_rgb(inputs)
    metadata = VideoMetadata(total_num_frames=inputs["total_num_frames"], fps=inputs["fps"],
                             frames_indices=list(inputs["frame_indices"]), width=sizes[0][0], height=sizes[0][1])
    return inputs, arrays, sizes, metadata


def encode_training(processor, row):
    from .batches import encode_arrays

    inputs, arrays, sizes, metadata = rgb_arrays(row)
    batch, audit = encode_arrays(processor, inputs["question"], inputs["options"] or [], arrays, metadata,
                                 row["target"], max_length=TRAINING["max_sequence_tokens"])
    return batch, {"qid": row["qid"], "original_width_height_per_frame": sizes,
                   "null_options_normalized_to_empty": inputs["options"] is None, **audit}


def encode_prompt(processor, row):
    inputs, arrays, sizes, metadata = rgb_arrays(row)
    options = inputs["options"] or []
    if not isinstance(inputs["question"], str) or not isinstance(options, list) or not all(isinstance(option, str) for option in options):
        raise ValueError("Inference requires original question/option strings")
    from .trace_contract import ANSWER_FORMAT_INSTRUCTION

    text = inputs["question"] + ("\n" + "\n".join(options) if options else "") + "\n\n" + ANSWER_FORMAT_INSTRUCTION
    messages = [{"role": "user", "content": [{"type": "video"}, {"type": "text", "text": text}]}]
    prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    batch = processor(text=[prompt], videos=[arrays], video_metadata=[metadata], do_sample_frames=False,
                      size=RGB["size"], return_tensors="pt", return_metadata=True)
    returned = batch.pop("video_metadata", None)
    if returned is not None and (list(returned[0].frames_indices) != list(metadata.frames_indices) or returned[0].fps != metadata.fps):
        raise ValueError("Inference processor changed original frame sampling or timing")
    grid = batch["video_grid_thw"]
    if grid.shape != (1, 3) or int(grid[0, 0]) * processor.video_processor.temporal_patch_size != 32:
        raise ValueError("Inference processor changed the RGB32 temporal grid")
    visual_tokens = int((batch["input_ids"] == processor.video_token_id).sum())
    if visual_tokens != int(grid.prod()) // processor.video_processor.merge_size**2:
        raise ValueError("Inference visual placeholder/grid mismatch")
    timestamps = [index / metadata.fps for index in metadata.frames_indices]
    decoded = processor.tokenizer.decode(batch["input_ids"][0], skip_special_tokens=False)
    if any(f"<{(timestamps[index] + timestamps[index + 1]) / 2:.1f} seconds>" not in decoded for index in range(0, 32, 2)):
        raise ValueError("Inference lost native temporal-patch timestamps")
    if set(batch) - {"input_ids", "attention_mask", "mm_token_type_ids", "pixel_values_videos", "video_grid_thw"}:
        raise ValueError("Answer-free inference contains an unexpected processor field")
    return dict(batch), {"qid": row["qid"], "frame_count": 32, "prompt_tokens": batch["input_ids"].shape[1],
                         "video_grid_thw": grid.tolist(), "visual_tokens": visual_tokens,
                         "processed_height_width": [int(grid[0, 1]) * 16, int(grid[0, 2]) * 16],
                         "original_frame_indices": inputs["frame_indices"], "original_timestamps_seconds": timestamps,
                         "original_width_height_per_frame": sizes, "answer_content_in_prompt": False,
                         "null_options_normalized_to_empty": inputs["options"] is None}


def target_tokens(processor, row):
    from .batches import training_text

    inputs = row["student_input"]
    _, suffix = training_text(processor, inputs["question"], inputs["options"] or [], row["target"])
    return len(processor.tokenizer.encode(suffix, add_special_tokens=False))


def prepare_training(accepted_paths, protocol_path, output, scratch_root=None):
    from .batches import load_processor

    protocol = load_protocol(protocol_path)
    manifests = [load_accepted(path) for path in accepted_paths]
    if len(manifests) != 2 or {manifest["phase"] for manifest in manifests} != {"first3", "remaining"}:
        raise ValueError("Training requires both reviewed conversion batches, not a selected pilot subset")
    if any(manifest["audited_packets"] != manifests[0]["audited_packets"] for manifest in manifests):
        raise ValueError("Accepted conversion batches refer to different source pools")
    selected = [qid for manifest in manifests for qid in manifest["selected_qids"]]
    if Counter(selected) != Counter(manifests[0]["audited_pool_qids"]):
        raise ValueError("Both reviewed batches must cover the entire fixed 86-packet pool exactly once")
    accepted = sorted([row for manifest in manifests for row in manifest["rows"]], key=lambda row: int(row["qid"]))
    processor = load_processor(protocol.get("student", "onethinker"))
    rows, audits, drops = [], [], []
    for row in accepted:
        tokens = target_tokens(processor, row)
        drop = {"qid": row["qid"], "target_tokens_including_eos": tokens, "complete_target_sha256": digest_json(row["target"])}
        if tokens > TRAINING["max_target_tokens_including_eos"]:
            drops.append({**drop, "reason": "complete_target_exceeds_predeclared_token_limit", "limit": TRAINING["max_target_tokens_including_eos"]})
            continue
        try:
            batch, audit = encode_training(processor, row)
        except ValueError as error:
            if str(error).startswith("Complete example requires "):
                drops.append({**drop, "reason": "complete_sequence_exceeds_predeclared_token_limit", "limit": TRAINING["max_sequence_tokens"], "detail": str(error)})
                continue
            raise
        if audit["assistant_tokens_including_eos"] != tokens:
            raise ValueError("Tokenizer and complete assistant supervision disagree")
        rows.append(row)
        audits.append(audit)
        del batch
    manifest = {"schema": "fixed-diagnostic-training-manifest-v1", **FLAGS, "protocol": binding(protocol_path),
                "accepted_manifests": [binding(path) for path in accepted_paths], "audited_pool_qids": manifests[0]["audited_pool_qids"],
                "accepted_before_token_limits": len(accepted), "rejected_conversion_qids": sorted([qid for manifest in manifests for qid in manifest["rejected_qids"]], key=int),
                "pre_evaluation_drops": drops, "input_audits": audits, "rows": rows,
                "counts": {"training_rows": len(rows), "training_scenes": len({physical_group(row["dataset"], row["scene"]) for row in rows}),
                           "frames": sum(audit["frame_count"] for audit in audits),
                           "target_tokens_including_eos": sum(audit["assistant_tokens_including_eos"] for audit in audits),
                           "prompt_tokens": sum(audit["prompt_tokens"] for audit in audits)}, "training_ready": bool(rows)}
    write_output(output, manifest, scratch_root)
    return {"status": "READY" if rows else "NO_ACCEPTED_TOKEN_FITTING_TARGETS", "counts": manifest["counts"],
            "token_limit_drops": len(drops), "manifest": binding(output)}


def load_training(path):
    manifest = load_json(path)
    if manifest.get("schema") != "fixed-diagnostic-training-manifest-v1":
        raise ValueError("Only accepted detailed diagnostic training manifests may train; review packets and smoke cannot")
    verify_pin(manifest["protocol"])
    protocol = load_protocol(manifest["protocol"]["path"])
    accepted = {}
    selected = []
    for pin in manifest["accepted_manifests"]:
        verify_pin(pin)
        source = load_accepted(pin["path"])
        selected.extend(source["selected_qids"])
        accepted.update({row["qid"]: row for row in source["rows"]})
    if Counter(selected) != Counter(manifest["audited_pool_qids"]):
        raise ValueError("Training lost fixed conversion-pool coverage")
    kept = [row["qid"] for row in manifest["rows"]]
    dropped = [row["qid"] for row in manifest["pre_evaluation_drops"]]
    if Counter(kept + dropped) != Counter(accepted.keys()) or any(row != accepted[row["qid"]] for row in manifest["rows"]):
        raise ValueError("Training rows were filtered, duplicated, truncated, or changed outside the predeclared token policy")
    if len(manifest["input_audits"]) != len(kept) or [audit["qid"] for audit in manifest["input_audits"]] != kept:
        raise ValueError("Training input audit coverage changed")
    if dropped:
        from .batches import load_processor
        processor = load_processor(protocol.get("student", "onethinker"))
        for drop in manifest["pre_evaluation_drops"]:
            row = accepted[drop["qid"]]
            tokens = target_tokens(processor, row)
            if tokens != drop["target_tokens_including_eos"] or digest_json(row["target"]) != drop["complete_target_sha256"]:
                raise ValueError("Dropped complete target or its token count changed")
            if drop["reason"] == "complete_target_exceeds_predeclared_token_limit":
                if drop["limit"] != TRAINING["max_target_tokens_including_eos"] or tokens <= drop["limit"]:
                    raise ValueError("Target drop does not exceed the predeclared limit")
            elif drop["reason"] == "complete_sequence_exceeds_predeclared_token_limit":
                if drop["limit"] != TRAINING["max_sequence_tokens"]:
                    raise ValueError("Sequence drop changed its predeclared limit")
                try:
                    encode_training(processor, row)
                except ValueError as error:
                    if not str(error).startswith("Complete example requires "):
                        raise
                else:
                    raise ValueError("Dropped sequence actually fits the predeclared limit")
            else:
                raise ValueError("Undeclared training exclusion")
    return manifest


def prepare_heldout(protocol_path, output, scratch_root=None):
    load_protocol(protocol_path)
    _, division, pins, inference = authorities()
    binding(DIVISION_PATH, DIVISION_SHA)
    identities = {str(item["id"]): item for item in inference if str(item["id"]) in set(division["heldout_qids"])}
    if set(identities) != set(division["heldout_qids"]):
        raise ValueError("Answer-free source inference does not cover the canonical 63 heldout questions")
    training_source, _, _, _ = source_candidate("1506")
    external = training_source["external_registries"]
    for pin in external.values():
        verify_pin(pin)
    frame_assets = load_json(external["frames"]["path"])["assets"]
    videos = load_json(external["source_videos"]["path"])["assets"]
    registry = load_json(REGISTRY)
    scenes, rows = {}, []
    for qid in division["heldout_qids"]:
        item = identities[qid]
        scene, dataset = item["scene_name"], item["dataset"]
        key = (dataset, scene)
        if physical_group(dataset, scene) not in division["heldout_group_ids"]:
            raise ValueError("Heldout scene identity differs from the frozen division")
        if key not in scenes:
            try:
                selection = registry[scene]
                assets = sorted([asset for asset in frame_assets if asset["scene"] == scene], key=lambda asset: asset["ordinal"])
                if len(selection["indices"]) != 32 or [Path(asset["path"]).stem for asset in assets] != selection["frame_names"] or any(asset["source"] != "preextracted_png" for asset in assets):
                    raise ValueError("Original selected RGB32 registry mismatch")
                frames = [binding(asset["path"], asset["sha256"]) for asset in assets]
                selected_videos = [asset for asset in videos if asset["scene"] == scene and asset["dataset"] == dataset]
                if len(selected_videos) != 1:
                    raise ValueError("Original source video missing or duplicated")
                video = binding(selected_videos[0]["path"], selected_videos[0]["sha256"])
                timing = video_timing(video["path"], selection["indices"])
                scenes[key] = {"frames": frames, "frame_indices": selection["indices"], "source_video": video,
                               **{field: timing[field] for field in ("timestamps", "fps", "total_num_frames")}}
            except (ValueError, OSError, KeyError) as error:
                scenes[key] = {"media_failure": {"error_type": type(error).__name__, "reason": str(error)}}
        media = scenes[key]
        row = {"qid": qid, "scene": scene, "dataset": dataset, "category": item["question_type"],
               "question_sha256": digest_json(item["question"]), "options_sha256": digest_json(item.get("options", []))}
        if "media_failure" in media:
            row.update(student_input=None, **media)
        else:
            row.update(source_video=media["source_video"], student_input={"question": item["question"], "options": item.get("options", []),
                       **{field: media[field] for field in ("frames", "frame_indices", "timestamps", "fps", "total_num_frames")}})
        rows.append(row)
    manifest = {"schema": "fixed63-answer-free-rgb-evaluation-v1", **FLAGS, "protocol": binding(protocol_path),
                "bindings": pins, "external_registries": external, "heldout_qids": division["heldout_qids"], "rows": rows,
                "cohort_size": 63, "media_ready": sum(row["student_input"] is not None for row in rows),
                "missing_media_counts_as_failure": True, "labels_present": False, "teacher_outputs_present": False}
    write_output(output, manifest, scratch_root)
    return {"status": "FIXED63_PREPARED_NO_INFERENCE", "cohort_size": 63, "media_ready": manifest["media_ready"],
            "media_failures": 63 - manifest["media_ready"], "manifest": binding(output)}


def load_heldout(path):
    manifest = load_json(path)
    if manifest.get("schema") != "fixed63-answer-free-rgb-evaluation-v1" or manifest.get("labels_present") is not False or manifest.get("teacher_outputs_present") is not False:
        raise ValueError("Evaluation requires the answer-free fixed63 RGB manifest")
    _, division, pins, inference = authorities()
    if manifest["bindings"] != pins or manifest["heldout_qids"] != division["heldout_qids"] or [row["qid"] for row in manifest["rows"]] != division["heldout_qids"]:
        raise ValueError("Evaluation cohort or source authorities changed")
    verify_pin(manifest["protocol"])
    allowed = {"qid", "scene", "dataset", "category", "question_sha256", "options_sha256", "student_input", "source_video", "media_failure"}
    identities = {str(item["id"]): item for item in inference}
    for row in manifest["rows"]:
        item = identities[row["qid"]]
        if set(row) - allowed or (row["scene"], row["dataset"], row["category"]) != (item["scene_name"], item["dataset"], item["question_type"]):
            raise ValueError("Evaluation row identity or answer-free fields changed")
        if row["question_sha256"] != digest_json(item["question"]) or row["options_sha256"] != digest_json(item.get("options", [])):
            raise ValueError("Evaluation question/option identity changed")
        if row["student_input"] is not None:
            inputs = row["student_input"]
            if inputs["question"] != item["question"] or inputs["options"] != item.get("options", []):
                raise ValueError("Student question/options are not verbatim source inputs")
            verify_pin(row["source_video"])
            for pin in inputs["frames"]:
                verify_pin(pin)
    return manifest


def check_heldout_inputs(manifest_path, output, scratch_root=None):
    import torch
    from .batches import load_processor

    manifest = load_heldout(manifest_path)
    protocol = load_protocol(manifest["protocol"]["path"])
    processor = load_processor(protocol.get("student", "onethinker"))
    audits = []
    for row in manifest["rows"]:
        if row["student_input"] is None:
            audits.append({"qid": row["qid"], "status": "SOURCE_MEDIA_FAILURE", "failure": row["media_failure"]})
            continue
        batch, audit = encode_prompt(processor, row)
        audits.append({"status": "RGB32_PROMPT_VERIFIED", **audit})
        del batch
    if torch.cuda.is_initialized():
        raise ValueError("CPU input verification unexpectedly initialized CUDA")
    report = {"schema": "fixed63-cpu-input-check-v1", "manifest": binding(manifest_path), "cohort_size": 63,
              "counts": dict(Counter(audit["status"] for audit in audits)), "rows": audits,
              "cuda_initialized": False, "student_generation_performed": False, "offline_scoring_performed": False}
    write_output(output, report, scratch_root)
    return {key: report[key] for key in ("cohort_size", "counts", "cuda_initialized", "student_generation_performed", "offline_scoring_performed")}


def zero_record(qid, category):
    metric = "accuracy" if "direction" in category or category in ("object_rel_distance", "route_planning", "obj_appearance_order") else "MRA"
    return {"id": qid, "type": category, "is_correct": False, metric: 0.0}


def retry_eligible(finish_reason, generated_tokens, budget, fully_correct):
    return not fully_correct and finish_reason == "MAX_TOKENS" and generated_tokens == budget == 16384


def load_evaluation_run(path):
    path = Path(path).resolve()
    header = load_json(path / "run.json")
    if header.get("schema") != "fixed63-student-generation-run-v1" or header.get("variant") not in ("original", "adapter"):
        raise ValueError("Expected an original or adapter diagnostic generation run")
    verify_pin(header["protocol"])
    verify_pin(header["evaluation_manifest"])
    manifest = load_heldout(header["evaluation_manifest"]["path"])
    protocol = load_protocol(header["protocol"]["path"])
    if manifest["protocol"] != header["protocol"] or header["generation"] != GENERATION or header["base_sha256"] != protocol["base_sha256"]:
        raise ValueError("Inference settings, input cohort, or model changed")
    return header, manifest


def checked_trace(path, qid, header):
    path = Path(path)
    if not path.is_file():
        return None
    trace = load_json(path)
    if trace.get("qid") != qid or trace.get("variant") != header["variant"] or trace.get("run_sha256") != digest_json(header) or trace.get("budget") != header["output_budget"]:
        raise ValueError("Generation trace identity/configuration changed")
    if trace.get("status") == "ok":
        generation = trace["generation"]
        tokens = generation["generated_token_ids"]
        eos = generation["eos_token_ids"]
        if generation["generated_tokens"] != len(tokens) or not tokens or len(tokens) > header["output_budget"]:
            raise ValueError("Generation token-count evidence is inconsistent")
        if generation["finish_reason"] == "MAX_TOKENS" and (len(tokens) != header["output_budget"] or tokens[-1] in eos):
            raise ValueError("Recorded output exhaustion lacks exact token/EOS evidence")
        if generation["finish_reason"] == "STOP" and tokens[-1] not in eos:
            raise ValueError("Recorded completion lacks native EOS evidence")
        if bool(trace["budget_terminal"]) != (generation["finish_reason"] == "MAX_TOKENS"):
            raise ValueError("Generation cap flag disagrees with its token evidence")
    elif trace.get("status") != "error":
        raise ValueError("Unknown inference trace terminal status")
    return trace


def score_trace(trace, label, scorer):
    if trace is None or trace.get("status") != "ok":
        return zero_record(str(label["id"]), label["question_type"]), False
    record, metrics = scorer._score_entry(trace, label, strict=True)
    full_credit = record.get("accuracy", record.get("MRA")) == 1.0 and metrics["is_correct"] is True
    return record, full_credit


def score_run(original_run, output, retry_run=None):
    original_run = Path(original_run).resolve()
    header, manifest = load_evaluation_run(original_run)
    if header["output_budget"] != 16384 or header["attempt_qids"] != manifest["heldout_qids"]:
        raise ValueError("Initial inference must attempt the full fixed63 cohort at 16384 tokens")
    contract, _, _, inference = authorities()
    scorer, scorer_pins = load_scorer(contract)
    answer_key = resolve_answer_key()
    labels = [label for label in load_json(answer_key["path"]) if str(label["id"]) in set(manifest["heldout_qids"])]
    if Counter(str(label["id"]) for label in labels) != Counter(manifest["heldout_qids"]):
        raise ValueError("Canonical offline labels do not cover exactly the fixed heldout cohort")
    labels = {str(label["id"]): label for label in labels}
    inference = {str(item["id"]): item for item in inference}
    for qid, label in labels.items():
        if any(label.get(key, [] if key == "options" else None) != inference[qid].get(key, [] if key == "options" else None) for key in ("dataset", "scene_name", "question_type", "question", "options")):
            raise ValueError("Offline labels differ from the source input identity")
    initial, originals, eligible = {}, {}, []
    for row in manifest["rows"]:
        qid = row["qid"]
        path = original_run / "traces" / f"{qid}.json"
        trace = checked_trace(path, qid, header)
        originals[qid] = trace
        record, correct = score_trace(trace, labels[qid], scorer)
        initial[qid] = record
        if trace and trace.get("status") == "ok":
            info = trace["generation"]
            if retry_eligible(info["finish_reason"], info["generated_tokens"], trace["budget"], correct):
                eligible.append({"qid": qid, "original_trace": binding(path)})
    retry_header = None
    if retry_run is not None:
        retry_run = Path(retry_run).resolve()
        retry_header, _ = load_evaluation_run(retry_run)
        if retry_header["output_budget"] != 32768 or any(retry_header[key] != header[key] for key in ("variant", "protocol", "evaluation_manifest", "base_sha256", "adapter")):
            raise ValueError("Rerun model, prompt cohort, or generation settings differ from its initial run")
        if retry_header["attempt_qids"] != [item["qid"] for item in eligible] or retry_header["original_run"] != binding(original_run / "run.json"):
            raise ValueError("Rerun membership differs from the offline recorded-cap/wrong-answer policy")
    final, receipts = [], []
    eligible_ids = {item["qid"] for item in eligible}
    for row in manifest["rows"]:
        qid = row["qid"]
        needs_retry = qid in eligible_ids
        selected = originals[qid]
        chosen_path = original_run / "traces" / f"{qid}.json"
        if needs_retry:
            chosen_path = retry_run / "traces" / f"{qid}.json" if retry_run else None
            selected = checked_trace(chosen_path, qid, retry_header) if chosen_path else None
        record, correct = score_trace(selected, labels[qid], scorer)
        final.append(record)
        receipts.append({"qid": qid, "retry_eligible": needs_retry, "selected_budget": 32768 if needs_retry else 16384,
                         "initial_trace": binding(original_run / "traces" / f"{qid}.json") if originals[qid] is not None else None,
                         "selected_trace": binding(chosen_path) if chosen_path and selected is not None else None,
                         "missing_or_failed": selected is None or selected.get("status") != "ok", "fully_correct": correct})
    output = repo_output(output, new=True)
    output.mkdir(parents=True)
    retry_plan = {"schema": "answer-free-recorded-cap-retry-plan-v1", "original_run": binding(original_run / "run.json"),
                  "protocol": header["protocol"], "evaluation_manifest": header["evaluation_manifest"],
                  "variant": header["variant"], "adapter": header["adapter"], "output_budget": 32768,
                  "entries": eligible, "selection_rule": GENERATION["retry_policy"], "labels_present": False,
                  "scorer": scorer_pins}
    write_once(output / "retry_plan.json", retry_plan)
    complete = (original_run / "completion.json").is_file() and (not eligible or (retry_run is not None and (retry_run / "completion.json").is_file()))
    report = {"schema": "fixed63-offline-diagnostic-score-v1", **FLAGS,
              "status": "COMPLETE_ATTEMPTS" if complete else "INCOMPLETE_ATTEMPTS_COUNTED_AS_FAILURES",
              "variant": header["variant"], "original_run": binding(original_run / "run.json"),
              "retry_run": binding(retry_run / "run.json") if retry_run else None,
              "evaluation_manifest": header["evaluation_manifest"], "protocol": header["protocol"],
              "answer_key": answer_key, "scorer": scorer_pins, "cohort_size": 63,
              "retry_eligible_count": len(eligible), "missing_or_failed": sum(row["missing_or_failed"] for row in receipts),
              "initial_records": list(initial.values()), "records": final, "question_receipts": receipts,
              "initial_pinned_summary": dict(scorer.aggregate_records(initial.values())), "pinned_summary": dict(scorer.aggregate_records(final)),
              "mean_final_answer_credit": sum(record.get("accuracy", record.get("MRA", 0.0)) for record in final) / 63,
              "full_credit_questions": sum(row["fully_correct"] for row in receipts)}
    write_once(output / "score.json", report)
    return {"status": report["status"], "cohort_size": 63, "retry_eligible_count": len(eligible),
            "missing_or_failed": report["missing_or_failed"], "score_report": binding(output / "score.json"),
            "retry_plan": binding(output / "retry_plan.json")}


def load_retry_plan(path, manifest_path, protocol_path, variant, adapter):
    plan = load_json(path)
    if plan.get("schema") != "answer-free-recorded-cap-retry-plan-v1" or plan.get("labels_present") is not False or plan.get("output_budget") != 32768 or plan.get("selection_rule") != GENERATION["retry_policy"]:
        raise ValueError("Rerun requires the offline answer-free recorded-cap plan")
    if plan["protocol"] != binding(protocol_path) or plan["evaluation_manifest"] != binding(manifest_path) or plan["variant"] != variant or plan["adapter"] != adapter:
        raise ValueError("Rerun plan differs from the bound model and input configuration")
    verify_pin(plan["original_run"])
    header, manifest = load_evaluation_run(Path(plan["original_run"]["path"]).parent)
    qids = [item["qid"] for item in plan["entries"]]
    if len(set(qids)) != len(qids) or not set(qids) <= set(manifest["heldout_qids"]):
        raise ValueError("Rerun identities are duplicated or outside the fixed heldout cohort")
    for item in plan["entries"]:
        verify_pin(item["original_trace"])
        trace = checked_trace(item["original_trace"]["path"], item["qid"], header)
        info = trace["generation"]
        if not retry_eligible(info["finish_reason"], info["generated_tokens"], trace["budget"], False):
            raise ValueError("Rerun lacks archived initial cap evidence")
    return plan


def compare_scores(original_path, adapter_path, output):
    scores = [load_json(path) for path in (original_path, adapter_path)]
    if [score.get("variant") for score in scores] != ["original", "adapter"] or any(score.get("schema") != "fixed63-offline-diagnostic-score-v1" or score.get("cohort_size") != 63 for score in scores):
        raise ValueError("Comparison requires original and adapter fixed63 score receipts")
    for key in ("evaluation_manifest", "protocol", "answer_key", "scorer"):
        if scores[0][key] != scores[1][key]:
            raise ValueError("Original/adapter comparison changed its input, protocol, or scorer")
    cohort = load_heldout(scores[0]["evaluation_manifest"]["path"])["heldout_qids"]
    for score in scores:
        if Counter(row["id"] for row in score["records"]) != Counter(cohort):
            raise ValueError("Comparison silently changed the heldout denominator")
        for pin in [score["original_run"], score["evaluation_manifest"], score["protocol"], score["answer_key"]] + list(score["scorer"].values()):
            verify_pin(pin)
        if score["retry_run"]:
            verify_pin(score["retry_run"])
        for row in score["question_receipts"]:
            for key in ("initial_trace", "selected_trace"):
                if row[key]:
                    verify_pin(row[key])
    result = {"schema": "benchmark-trained-fixed63-diagnostic-comparison-v1", **FLAGS,
              "cohort_size": 63, "scores": {"original": binding(original_path), "adapter": binding(adapter_path)},
              "primary_measure": "final-answer credit on every frozen heldout question; missing/failed outputs receive zero",
              "original_mean_final_answer_credit": scores[0]["mean_final_answer_credit"],
              "adapter_mean_final_answer_credit": scores[1]["mean_final_answer_credit"],
              "final_answer_credit_delta": scores[1]["mean_final_answer_credit"] - scores[0]["mean_final_answer_credit"],
              "original_pinned_summary": scores[0]["pinned_summary"], "adapter_pinned_summary": scores[1]["pinned_summary"],
              "full_credit_question_delta": scores[1]["full_credit_questions"] - scores[0]["full_credit_questions"],
              "missing_or_failed": {score["variant"]: score["missing_or_failed"] for score in scores},
              "attempts_complete": all(score["status"] == "COMPLETE_ATTEMPTS" for score in scores)}
    write_once(repo_output(output, new=True), result)
    return result
