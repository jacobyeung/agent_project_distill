from .job_env import key as env_key
from collections import Counter, defaultdict
from pathlib import Path

from . import diagnostic_data as clean
from .pose_samples import encode_row
from .common import REPO, binding, digest_json, load_json, resolve_read
from .conversion import verify_pin
from .provisional import (load_provisional_candidates, require_mode, source_path, division_candidates, tag,
                          validate_label, validate_rgb, write_artifact)
from .division import physical_group
from .students import get_student


def runtime_bindings():
    names = ("provisional.py", "provisional_data.py", "provisional_cli.py", "provisional_eval.py", "finetune_lane.py",
             "benchmark_eval/contracts.py", "benchmark_eval/answers.py")
    from .orchard_paths import enabled
    if enabled():
        names += ("orchard_paths.py", "orchard_admission.py", "orchard_checkpoints.py")
    return clean.runtime_bindings() + [binding(REPO / "student_pilot" / name) for name in names]


def input_row(row):
    return {key: row[key] for key in ("qid", "dataset", "scene", "category", "student_input")}


def training_protocol_fields(training_config, student):
    from . import ddp_config

    raw = load_json(source_path(training_config))
    settings = ddp_config.normalize_training_config(raw, student)
    run_control = ddp_config.run_control_from_config(raw)
    return {"protocol_version": ddp_config.VERSION, "training": settings, "training_sha256": digest_json(settings),
            "run_control": run_control, "run_control_sha256": digest_json(run_control),
            **ddp_config.camera_protocol_fields(raw), "training_config_source": binding(source_path(training_config))}


def prepare_protocol(index_path, output, label, student="onethinker", heldout_fraction=0.1, scratch_root=None, training_config=None, inherit_division=None,
                     init_adapter=None, init_adapter_weights_sha256=None, init_adapter_published_sha256=None, init_adapter_run_name=None):
    validate_label(label)
    index_path = source_path(index_path).resolve()
    source = binding(index_path)
    rows = load_provisional_candidates(index_path, label)
    if source != binding(Path(index_path).resolve()):
        raise ValueError("Candidate source changed during provisional admission")
    inherited_from = binding(source_path(inherit_division)) if inherit_division is not None else None
    division = division_candidates(rows, label, heldout_fraction, inherited_from)
    protocol = tag({"schema": "provisional-student-diagnostic-protocol-v1", "student": student,
                    "candidate_source": source, **division,
                    "candidate_census": [{"qid": row["qid"], "dataset": row["dataset"], "scene": row["scene"],
                                          "category": row["category"], "row_sha256": digest_json(row),
                                          "input_sha256": digest_json(input_row(row))} for row in rows],
                    "training": clean.training_settings(student), "generation": clean.GENERATION, "rgb": clean.RGB,
                    "base": clean.checkpoint_bindings(student), "runtime": runtime_bindings(), "versions": clean.versions(),
                    "selection_frozen_before_evaluation": True}, label)
    if training_config is not None:
        from . import ddp_config
        protocol.update(**training_protocol_fields(training_config, student),
                        runtime=protocol["runtime"] + ddp_config.runtime_bindings())
    from .trace_contract import ANSWER_FORMAT_INSTRUCTION
    protocol["answer_format_instruction"] = ANSWER_FORMAT_INSTRUCTION
    protocol["prompt_sha256"] = digest_json({"answer_format_instruction": ANSWER_FORMAT_INSTRUCTION})
    protocol["base_sha256"] = digest_json(protocol["base"])
    configured = load_json(source_path(training_config)).get("init_adapter") if training_config is not None else None
    if configured is not None or any(value is not None for value in
            (init_adapter, init_adapter_weights_sha256, init_adapter_published_sha256, init_adapter_run_name)):
        from .warmstart import freeze_initialization
        freeze_initialization(protocol, output, label, scratch_root, training_config, configured, init_adapter,
                              init_adapter_weights_sha256, init_adapter_published_sha256, init_adapter_run_name)
    if training_config is not None:
        from .ddp_config import require_frozen_parent
        require_frozen_parent(protocol)
    from .orchard_paths import enabled
    if enabled():
        import os
        protocol["orchard_path_map"] = os.environ.get((env_key('STUDENT_FRAME_ROOT_MAP')))
    write_artifact(output, protocol, label, scratch_root)
    return tag({"status": "PROVISIONAL_PROTOCOL_FROZEN_NO_GPU", "protocol": binding(output),
                "PROVISIONAL_DIVISION_SHA": protocol["PROVISIONAL_DIVISION_SHA"],
                "train_rows": len(protocol["division"]["train_candidate_qids"]),
                "heldout_rows": len(protocol["division"]["heldout_qids"])}, label)


def load_protocol(path, label, weights=False, student=None):
    protocol = require_mode(load_json(path), label)
    declared = protocol.get("student")
    if protocol.get("schema") != "provisional-student-diagnostic-protocol-v1" or student is not None and student != declared:
        raise ValueError("Expected the matching provisional student protocol")
    from .trace_contract import ANSWER_FORMAT_INSTRUCTION
    if (protocol.get("answer_format_instruction") != ANSWER_FORMAT_INSTRUCTION
            or protocol.get("prompt_sha256") != digest_json({"answer_format_instruction": ANSWER_FORMAT_INSTRUCTION})):
        raise ValueError("The frozen training prompt contract changed")
    settings = clean.training_settings(declared)
    runtime = runtime_bindings()
    if protocol.get("protocol_version") is not None or "version" in protocol.get("training", {}):
        from . import ddp_config
        settings = ddp_config.validate_training_protocol(protocol, label)
        runtime += ddp_config.runtime_bindings()
    if "init_adapter_identity" in protocol or "init_adapter_sha256" in protocol:
        from .warmstart import runtime_bindings as initialization_runtime, validate_identity
        validate_identity(protocol)
        runtime += initialization_runtime()
    for key, expected in (("training", settings), ("generation", clean.GENERATION), ("rgb", clean.RGB)):
        if protocol.get(key) != expected:
            raise ValueError(f"Provisional settings changed: {key}")
    census = protocol["candidate_census"]
    identities = [tag({key: row[key] for key in ("qid", "dataset", "scene", "category")}, label) for row in census]
    expected = division_candidates(identities, label, protocol["division"]["heldout_fraction_of_groups"],
                                protocol["division"].get("inherited_from"))
    if (protocol["division"] != expected["division"] or protocol.get("PROVISIONAL_DIVISION_SHA") != expected["PROVISIONAL_DIVISION_SHA"]
            or protocol.get("selection_frozen_before_evaluation") is not True or "DIVISION_SHA" in protocol):
        raise ValueError("Provisional scene division or digest changed")
    if protocol["base"].get("revision") != get_student(declared)["snapshot"].name or protocol["base_sha256"] != digest_json(protocol["base"]):
        raise ValueError("Original model snapshot identity changed")
    if protocol["versions"] != clean.versions() or protocol["runtime"] != runtime:
        raise ValueError("Provisional software environment or runtime closure changed")
    for pin in protocol["base"]["files"] + (protocol["base"]["weight_shards"] if weights else []):
        verify_pin(pin)
    from .orchard_paths import enabled
    if enabled():
        import os
        if protocol.get("orchard_path_map") != os.environ.get((env_key('STUDENT_FRAME_ROOT_MAP'))):
            raise ValueError("Orchard input mapping changed after preparation")
    return protocol


def load_single_training_protocol(path, label, weights=False, student=None):
    protocol = load_protocol(path, label, weights, student)
    if protocol.get("protocol_version") is not None:
        raise ValueError("Use train-ddp for a DDP protocol; single-GPU training settings remain unchanged")
    from .orchard_paths import enabled
    if enabled():
        import os
        if protocol.get("orchard_path_map") != os.environ.get((env_key('STUDENT_FRAME_ROOT_MAP'))):
            raise ValueError("Orchard input mapping changed after preparation")
    return protocol


def source_rows(protocol, label):
    source_path(protocol["candidate_source"]["path"])
    verify_pin(protocol["candidate_source"])
    rows = load_provisional_candidates(protocol["candidate_source"]["path"], label)
    census = protocol["candidate_census"]
    if ([row["qid"] for row in rows] != [item["qid"] for item in census]
            or any(digest_json(row) != item["row_sha256"] for row, item in zip(rows, census))):
        raise ValueError("Candidate rows changed after the provisional division was frozen")
    return rows


def prepare_training(protocol_path, output, label, scratch_root=None):
    from .batches import load_processor

    protocol = load_protocol(protocol_path, label)
    train_ids = set(protocol["division"]["train_candidate_qids"])
    accepted = [row for row in source_rows(protocol, label) if row["qid"] in train_ids]
    processor = load_processor(protocol["student"])
    rows, audits, drops = [], [], []
    for row in accepted:
        tokens = clean.target_tokens(processor, row)
        drop = {"qid": row["qid"], "target_tokens_including_eos": tokens, "complete_target_sha256": digest_json(row["target"])}
        if tokens > clean.TRAINING["max_target_tokens_including_eos"]:
            drops.append({**drop, "reason": "complete_target_exceeds_predeclared_token_limit",
                          "limit": clean.TRAINING["max_target_tokens_including_eos"]})
            continue
        try:
            batch, audit = encode_row(processor, row, protocol["training"].get("frames"))
        except ValueError as error:
            if not str(error).startswith("Complete example requires "):
                raise
            drops.append({**drop, "reason": "complete_sequence_exceeds_predeclared_token_limit",
                          "limit": clean.TRAINING["max_sequence_tokens"], "detail": str(error)})
            continue
        if audit["assistant_tokens_including_eos"] != tokens:
            raise ValueError("Tokenizer and complete assistant supervision disagree")
        rows.append(row)
        audits.append(audit)
        del batch
    manifest = {"schema": "provisional-diagnostic-training-manifest-v1", "protocol": binding(protocol_path),
                "PROVISIONAL_DIVISION_SHA": protocol["PROVISIONAL_DIVISION_SHA"], "candidate_source": protocol["candidate_source"],
                "accepted_before_token_limits": len(accepted), "pre_evaluation_drops": drops,
                "rows": rows, "input_audits": audits, "counts": training_counts(rows, audits), "training_ready": bool(rows)}
    write_artifact(output, manifest, label, scratch_root)
    return tag({"status": "READY" if rows else "NO_TOKEN_FITTING_TARGETS", "manifest": binding(output),
                "counts": manifest["counts"], "PROVISIONAL_DIVISION_SHA": protocol["PROVISIONAL_DIVISION_SHA"],
                "token_limit_drops": len(drops)}, label)


def training_counts(rows, audits):
    return {"training_rows": len(rows), "training_scenes": len({physical_group(row["dataset"], row["scene"]) for row in rows}),
            "frames": sum(audit["frame_count"] for audit in audits),
            "target_tokens_including_eos": sum(audit["assistant_tokens_including_eos"] for audit in audits),
            "prompt_tokens": sum(audit["prompt_tokens"] for audit in audits)}


SOURCE_RECEIPT_SCHEMA = "provisional-source-validation-receipt-v1"


def source_receipt_path(manifest_path):
    """Fixed location of the source-validation receipt that belongs to one frozen training manifest."""
    path = Path(manifest_path)
    return path.with_name(path.name + ".source_receipt.json")


def _read_manifest(path):
    """Parse and hash the same bytes, so validation and any receipt describe one manifest."""
    import hashlib
    import json

    data = resolve_read(path).read_bytes()
    return json.loads(data), {"path": str(path), "sha256": hashlib.sha256(data).hexdigest()}


def _source_receipt(manifest_binding, manifest, protocol):
    return {"schema": SOURCE_RECEIPT_SCHEMA, "status": "CANDIDATE_PAYLOADS_AND_TRAINING_MANIFEST_FULLY_VALIDATED",
            "manifest": manifest_binding, "protocol": manifest["protocol"], "candidate_source": protocol["candidate_source"],
            "candidate_census_sha256": digest_json(protocol["candidate_census"]),
            "PROVISIONAL_DIVISION_SHA": protocol["PROVISIONAL_DIVISION_SHA"], "runtime_sha256": digest_json(protocol["runtime"]),
            "training_rows": len(manifest["rows"]), "pre_evaluation_drops": len(manifest["pre_evaluation_drops"])}


def seal_source(manifest_path, output, label, scratch_root=None):
    """Run the complete training-manifest admission once, with every candidate payload re-read, on exactly the bytes
    it hashes, and record a receipt bound to that manifest, its protocol (and runtime closure), candidate source and census."""
    from .storage import code_provenance

    manifest_path = Path(manifest_path)
    if Path(output).resolve() != source_receipt_path(manifest_path).resolve():
        raise ValueError("The source receipt must sit beside its manifest at the fixed receipt path")
    if source_receipt_path(manifest_path).exists():
        raise ValueError("This manifest already has a source receipt")
    manifest, manifest_binding = _read_manifest(manifest_path)
    protocol = _admit_training(manifest_path, manifest, manifest_binding, label, use_receipt=False)
    receipt = _source_receipt(manifest_binding, manifest, protocol)
    code_provenance(receipt)
    write_artifact(output, receipt, label, scratch_root)
    return tag({**receipt, "receipt": binding(output)}, label)


def _verified_receipt(path, manifest_binding, manifest, protocol, label):
    from .storage import code_provenance

    recorded = require_mode(load_json(source_receipt_path(path)), label)
    expected = tag(_source_receipt(manifest_binding, manifest, protocol), label)
    provenance = recorded.get("provenance")
    if ({key: value for key, value in recorded.items() if key != "provenance"} != expected
            or not isinstance(provenance, dict) or provenance.get("dirty") is not False
            or provenance.get("config_sha256") != digest_json(expected)
            or provenance.get("commit") != code_provenance(expected)["commit"]):
        raise ValueError("Source receipt does not match this manifest, protocol, candidate source, census or code")
    verify_pin(protocol["candidate_source"])


def _census_rows(protocol, qids, label):
    """Validate only the named candidates, re-reading their payloads, and bind each to its frozen census digest."""
    from .provisional import _load_candidate_rows, candidate_entries

    verify_pin(protocol["candidate_source"])
    entries, source = candidate_entries(protocol["candidate_source"]["path"], label)
    wanted = [entry for entry in entries if isinstance(entry, dict) and entry.get("qid") in qids]
    rows = _load_candidate_rows(((entry, None) for entry in wanted), source, label)
    census = {item["qid"]: item["row_sha256"] for item in protocol["candidate_census"]}
    if (sorted(row["qid"] for row in rows) != sorted(qids)
            or any(digest_json(row) != census.get(row["qid"]) for row in rows)):
        raise ValueError("Candidate rows changed after the provisional division was frozen")
    return {row["qid"]: row for row in rows}


def load_training(path, label, use_receipt=True):
    """Admit a frozen training manifest. With a matching source receipt (written by seal_source after a complete
    validation of the same bytes), kept rows' candidate payloads are not re-read: every kept row must still hash to its
    frozen census digest (its frames are re-verified when staged), and every dropped row is re-read and re-checked in full."""
    manifest, manifest_binding = _read_manifest(path)
    _admit_training(path, manifest, manifest_binding, label, use_receipt)
    return manifest


def _admit_training(path, manifest, manifest_binding, label, use_receipt):
    manifest = require_mode(manifest, label)
    if manifest.get("schema") != "provisional-diagnostic-training-manifest-v1":
        raise ValueError("Only explicitly provisional training manifests may enter this mode")
    verify_pin(manifest["protocol"])
    protocol = load_protocol(manifest["protocol"]["path"], label)
    if manifest.get("PROVISIONAL_DIVISION_SHA") != protocol["PROVISIONAL_DIVISION_SHA"] or manifest.get("candidate_source") != protocol["candidate_source"]:
        raise ValueError("Training manifest changed the provisional division or source")
    training = set(protocol["division"]["train_candidate_qids"])
    rows, audits, drops = manifest["rows"], manifest["input_audits"], manifest["pre_evaluation_drops"]
    kept = [row["qid"] for row in rows]
    if use_receipt and source_receipt_path(path).exists():
        _verified_receipt(path, manifest_binding, manifest, protocol, label)
        census = {item["qid"]: item["row_sha256"] for item in protocol["candidate_census"]}
        admitted = [item["qid"] for item in protocol["candidate_census"] if item["qid"] in training]
        rows_changed = any(row["qid"] not in training or digest_json(row) != census.get(row["qid"]) for row in rows)
        dropped = {drop["qid"] for drop in drops if isinstance(drop, dict)} & set(admitted)
        accepted = {qid: None for qid in admitted}
        accepted.update(_census_rows(protocol, dropped, label) if dropped else {})
    else:
        accepted = {row["qid"]: row for row in source_rows(protocol, label) if row["qid"] in training}
        rows_changed = any(row != accepted[row["qid"]] for row in rows)
    if (Counter(kept + [drop["qid"] for drop in drops]) != Counter(accepted.keys())
            or rows_changed
            or [audit["qid"] for audit in audits] != kept
            or manifest["counts"] != training_counts(rows, audits)
            or manifest.get("accepted_before_token_limits") != len(accepted)
            or manifest.get("training_ready") is not bool(rows)):
        raise ValueError("Provisional training coverage, rows, or input audit counts changed")
    if drops:
        from .batches import load_processor
        processor = load_processor(protocol["student"])
        for drop in drops:
            row = accepted[drop["qid"]]
            tokens = clean.target_tokens(processor, row)
            if tokens != drop["target_tokens_including_eos"] or digest_json(row["target"]) != drop["complete_target_sha256"]:
                raise ValueError("Dropped complete target or token count changed")
            if drop["reason"] == "complete_target_exceeds_predeclared_token_limit":
                if drop["limit"] != clean.TRAINING["max_target_tokens_including_eos"] or tokens <= drop["limit"]:
                    raise ValueError("Dropped target fits the frozen token limit")
            elif drop["reason"] == "complete_sequence_exceeds_predeclared_token_limit":
                if drop["limit"] != clean.TRAINING["max_sequence_tokens"]:
                    raise ValueError("Sequence drop changed its frozen limit")
                try:
                    encode_row(processor, row, protocol["training"].get("frames"))
                except ValueError as error:
                    if not str(error).startswith("Complete example requires "):
                        raise
                else:
                    raise ValueError("Dropped sequence fits the frozen token limit")
            else:
                raise ValueError("Undeclared provisional training exclusion")
    return protocol


def prepare_heldout(protocol_path, output, label, scratch_root=None):
    protocol = load_protocol(protocol_path, label)
    heldout = set(protocol["division"]["heldout_qids"])
    rows = [input_row(row) for row in source_rows(protocol, label) if row["qid"] in heldout]
    manifest = {"schema": "provisional-answer-free-rgb-evaluation-v1", "protocol": binding(protocol_path),
                "PROVISIONAL_DIVISION_SHA": protocol["PROVISIONAL_DIVISION_SHA"], "heldout_qids": [row["qid"] for row in rows],
                "rows": rows, "cohort_size": len(rows), "labels_present": False, "teacher_outputs_present": False}
    write_artifact(output, manifest, label, scratch_root)
    return tag({"status": "PROVISIONAL_HELDOUT_PREPARED_NO_INFERENCE", "manifest": binding(output),
                "cohort_size": len(rows), "PROVISIONAL_DIVISION_SHA": protocol["PROVISIONAL_DIVISION_SHA"]}, label)


def load_heldout(path, label):
    manifest = require_mode(load_json(path), label)
    if (manifest.get("schema") != "provisional-answer-free-rgb-evaluation-v1" or manifest.get("labels_present") is not False
            or manifest.get("teacher_outputs_present") is not False):
        raise ValueError("Provisional evaluation requires an answer-free holdout manifest")
    verify_pin(manifest["protocol"])
    protocol = load_protocol(manifest["protocol"]["path"], label)
    ids = protocol["division"]["heldout_qids"]
    if (manifest.get("PROVISIONAL_DIVISION_SHA") != protocol["PROVISIONAL_DIVISION_SHA"] or manifest["heldout_qids"] != ids
            or [row["qid"] for row in manifest["rows"]] != ids or manifest["cohort_size"] != len(ids)):
        raise ValueError("Provisional heldout membership or division digest changed")
    census = {row["qid"]: row for row in protocol["candidate_census"]}
    seen = set()
    for row in manifest["rows"]:
        if set(row) != {"qid", "dataset", "scene", "category", "student_input"} or digest_json(row) != census[row["qid"]]["input_sha256"]:
            raise ValueError("Provisional heldout input changed or contains target/answer fields")
        validate_rgb(row["student_input"])
        for pin in row["student_input"]["frames"]:
            key = (pin["path"], pin["sha256"])
            if key not in seen:
                verify_pin(pin)
                seen.add(key)
    return manifest


def score_run(run, output, label, scratch_root=None):
    from .benchmark_eval.answers import parse_answer

    run = Path(run).resolve()
    header = require_mode(load_json(run / "run.json"), label)
    if (header.get("schema") != "provisional-student-generation-run-v1" or header.get("variant") not in ("original", "adapter")
            or header.get("retry_plan") is not None):
        raise ValueError("Expected one provisional heldout generation pass")
    verify_pin(header["evaluation_manifest"])
    verify_pin(header["protocol"])
    manifest = load_heldout(header["evaluation_manifest"]["path"], label)
    protocol = load_protocol(header["protocol"]["path"], label)
    ids = manifest["heldout_qids"]
    if (header["attempt_qids"] != ids or header["cohort_size"] != len(ids)
            or manifest["protocol"] != header["protocol"] or header["PROVISIONAL_DIVISION_SHA"] != protocol["PROVISIONAL_DIVISION_SHA"]
            or header["base_sha256"] != protocol["base_sha256"] or header["generation"] != clean.GENERATION
            or header["output_budget"] != clean.GENERATION["initial_max_new_tokens"]):
        raise ValueError("Provisional generation does not match the frozen heldout protocol")
    labels = {row["qid"]: row for row in source_rows(protocol, label) if row["qid"] in set(ids)}
    records, credits, pins = [], defaultdict(list), []
    for row in manifest["rows"]:
        qid = row["qid"]
        path = run / "traces" / f"{qid}.json"
        trace = clean.checked_trace(path, qid, header)
        parsed, expected = None, str(labels[qid]["answer"])
        if trace is not None:
            require_mode(trace, label)
            if trace.get("input_sha256") != digest_json(row["student_input"]):
                raise ValueError("Provisional trace input identity changed")
            pins.append(binding(path))
        options = row["student_input"]["options"] or []
        if options:
            options = [f"{chr(65 + i)}. {text}" for i, text in enumerate(options)]
        if trace is not None and trace["status"] == "ok":
            parsed = parse_answer(trace["generation"]["raw_decoded_text"], options)["answer"]
        expected = parse_answer(expected, options)["answer"]
        if expected is None:
            raise ValueError("Candidate answer cannot be parsed for heldout exact-match scoring")
        credit = int(parsed is not None and parsed == expected)
        records.append(tag({"qid": qid, "category": row["category"], "parsed_answer": parsed,
                            "expected_answer": expected, "exact_match": credit,
                            "status": trace["status"] if trace else "missing"}, label))
        credits[row["category"]].append(credit)
    report = {"schema": "provisional-heldout-exact-match-v1", "run": binding(run / "run.json"), "variant": header["variant"],
              "student": protocol["student"], "protocol": header["protocol"], "PROVISIONAL_DIVISION_SHA": protocol["PROVISIONAL_DIVISION_SHA"],
              "cohort_size": len(ids), "denominator_includes_failures": True, "trace_bindings": pins, "rows": records,
              "exact_match": sum(row["exact_match"] for row in records) / len(ids),
              "per_question_type": {name: {"count": len(values), "exact_match": sum(values) / len(values)} for name, values in sorted(credits.items())}}
    write_artifact(output, report, label, scratch_root)
    return tag(report, label)


def compare_scores(original_path, adapter_path, output, label, scratch_root=None):
    original, adapter = [require_mode(load_json(path), label) for path in (original_path, adapter_path)]
    if (original.get("schema") != "provisional-heldout-exact-match-v1" or adapter.get("schema") != original["schema"]
            or original["variant"] != "original" or adapter["variant"] != "adapter"
            or any(original[key] != adapter[key] for key in ("student", "protocol", "PROVISIONAL_DIVISION_SHA", "cohort_size"))
            or [(row["qid"], row["category"]) for row in original["rows"]] != [(row["qid"], row["category"]) for row in adapter["rows"]]):
        raise ValueError("Heldout comparison requires paired provisional base/adapter cohorts")
    for score in (original, adapter):
        for pin in [score["run"], score["protocol"]] + score["trace_bindings"]:
            verify_pin(pin)
    report = {"schema": "provisional-heldout-comparison-v1", "base": binding(original_path), "adapter": binding(adapter_path),
              "PROVISIONAL_DIVISION_SHA": original["PROVISIONAL_DIVISION_SHA"], "cohort_size": original["cohort_size"],
              "base_exact_match": original["exact_match"], "adapter_exact_match": adapter["exact_match"],
              "per_question_type": {name: {"count": values["count"], "base_exact_match": values["exact_match"],
                                           "adapter_exact_match": adapter["per_question_type"][name]["exact_match"]}
                                    for name, values in original["per_question_type"].items()}}
    write_artifact(output, report, label, scratch_root)
    return tag(report, label)
