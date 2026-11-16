#!/usr/bin/env python3
"""Publish a smoke milestone of an HC/HX v3 run (full weights, heads and the gated G3T connector) as an
orchard-evaluator publication, for the head-call decode check.

The closure's publish_smoke_milestone.py (milestone_20, no geometry) with two changes: the milestone step is an argument,
and the milestone's geometry/ (connector manifest and weights) is published with its hashes in the training result and
the receipt, as diagnostic finalize publishes a geometry-input run. The publication is admitted at once with the eval
feature store, carriers inserted and head-call decoding (validate_adapter), so a broken publication fails here.

usage: publish_hc_v3.py RUN_OUTPUT CHECKPOINT_ROOT FROZEN PUB_DIR STEP STORE_MANIFEST STORE_SHA256
"""
import json
import os
import sys
from pathlib import Path

for candidate in (os.environ.get("TRAINER"), os.environ.get("R1_TRAINER")):
    if candidate and Path(candidate).is_dir() and candidate not in sys.path:
        sys.path.insert(0, candidate)

from student_pilot import ddp_config, full_ft, geometry_input, provisional, provisional_data, storage  # noqa: E402
from student_pilot.common import binding, canonical_bytes, digest_json, load_json, sha256  # noqa: E402
from student_pilot.orchard_eval.contracts import DEFAULT_CONFIG, MODEL_PINS, validate_adapter  # noqa: E402

LABEL = "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW"


def main(argv):
    run_output, ckpt_root, frozen, pub_dir = (Path(item).resolve() for item in argv[:4])
    step, store = int(argv[4]), {"manifest": argv[5], "manifest_sha256": argv[6]}
    if len(argv) >= 9:
        store["camera_manifest"] = argv[7]
        store["camera_manifest_sha256"] = argv[8]
    milestone_dir = ckpt_root / f"milestone_{step}"
    if pub_dir.exists():
        raise SystemExit(f"{pub_dir} exists; publish into a new directory")
    full_ft.read_milestone(milestone_dir)
    pub_dir.mkdir(parents=True)

    protocol = load_json(frozen / "protocol.json")
    for key in ("provenance", "purpose", "infrastructure_only"):
        protocol.pop(key, None)
    settings = dict(protocol["training"])
    if settings.get("geometry") is None or settings.get("headcall") is None:
        raise SystemExit("publish_hc_v3 publishes head-call runs with a geometry input")
    settings["max_steps"] = None
    settings["epochs"] = 1
    protocol["training"] = settings
    protocol["training_sha256"] = digest_json(settings)
    div_sha = protocol["PROVISIONAL_DIVISION_SHA"]
    flags = {"infrastructure_only": False, "benchmark_improvement_claim": False, "score_nomination_allowed": False,
             **provisional.flags(LABEL), "PROVISIONAL_DIVISION_SHA": div_sha}
    prov = storage.code_provenance({"milestone_publish": str(pub_dir), "PROVISIONAL_DIVISION_SHA": div_sha})

    def record(value):
        return {**provisional.tag(value, LABEL), **flags, "provenance": prov}

    def write_json(rel, value):
        path = pub_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical_bytes(record(value)))
        return path

    if protocol.get("orchard_path_map"):
        os.environ["STUDENT_FRAME_ROOT_MAP"] = protocol["orchard_path_map"]
    proto_path = write_json("protocol.json", protocol)
    verified = provisional_data.load_protocol(proto_path, LABEL, student=protocol["student"])
    div_path = pub_dir / "division.json"
    div_path.write_bytes(canonical_bytes(protocol["division"]))

    # Training rows: step * effective_batch_size rows, so the publication's step count equals the milestone's.
    eff = int(settings["effective_batch_size"])
    original = load_json(frozen / "training.json")
    for key in ("provenance", "purpose", "infrastructure_only"):
        original.pop(key, None)
    rows, audits = original["rows"][:step * eff], original["input_audits"][:step * eff]
    manifest = {**original, "protocol": binding(proto_path), "accepted_before_token_limits": len(rows),
                "pre_evaluation_drops": [], "rows": rows, "input_audits": audits,
                "counts": provisional_data.training_counts(rows, audits), "training_ready": True}
    train_path = write_json("training.json", manifest)

    directory = provisional.adapter_directory(LABEL)
    weights_dir = pub_dir / directory / full_ft.EXPORT_DIRECTORY
    weights_dir.mkdir(parents=True)
    for item in sorted((milestone_dir / full_ft.EXPORT_DIRECTORY).iterdir()):
        if item.is_file():
            os.link(item, weights_dir / item.name)
    export = load_json(weights_dir / full_ft.EXPORT_MANIFEST)
    adapter = {"full_weights": binding(weights_dir / full_ft.EXPORT_MANIFEST), "full_weights_bytes": export["bytes"],
               "full_weights_tensors": export["tensor_count"]}
    write_json(f"{directory}/provenance.json", {"adapter": adapter, "protocol_version": ddp_config.VERSION})

    os.link(milestone_dir / "auxiliary_heads.pt", pub_dir / "auxiliary_heads.pt")
    heads_pin = binding(pub_dir / "auxiliary_heads.pt")
    heads_meta = load_json(milestone_dir / "auxiliary_heads.json")
    # As diagnostic finalize publishes it: the milestone's settings, camera and inference flag, plus the weights pin.
    write_json("auxiliary_heads.json", {**{k: v for k, v in heads_meta.items() if k in ("settings", "camera", "inference_required")},
                                        "weights": heads_pin})

    (pub_dir / "geometry").mkdir()
    for name in (geometry_input.MANIFEST_NAME, geometry_input.WEIGHTS_NAME):
        os.link(milestone_dir / "geometry" / name, pub_dir / "geometry" / name)
    published = load_json(pub_dir / "geometry" / geometry_input.MANIFEST_NAME)
    if geometry_input.normalize(published["settings"]) != settings["geometry"]:
        raise SystemExit("The milestone's connector settings differ from the training config")
    geometry = {"weights": binding(pub_dir / "geometry" / geometry_input.WEIGHTS_NAME),
                "manifest": binding(pub_dir / "geometry" / geometry_input.MANIFEST_NAME),
                "parameters": published["parameters"]}

    adapters = load_json(run_output / "adapters.json")
    record_ft = {key: adapters[key] for key in ("schema", "mode", "train", "learning_rates", "group_parameters",
                                                "trainable_parameters", "base_parameters", "init_modules") if key in adapters}
    result = {
        "schema": "completed-provisional-diagnostic-training-v1", "status": "TRAINED", "student": protocol["student"],
        "base": protocol["base"], "base_sha256": protocol["base_sha256"],
        "base_restart": "fresh_load_of_original_snapshot_no_smoke_adapter", "protocol": binding(proto_path),
        "training_manifest": binding(train_path), "adapter": adapter, "adapter_parameters": record_ft["trainable_parameters"],
        "protocol_version": ddp_config.VERSION, "training_sha256": verified["training_sha256"], "settings": settings,
        "run_control": verified["run_control"], "run_control_sha256": verified["run_control_sha256"],
        "dataset_counts": manifest["counts"], "frozen_base_unchanged": True, "completed_epochs": 1,
        "rank_checks": [{"rank": r, "frozen_base_unchanged": True} for r in range(settings["world_size"])],
        "realized": {"optimizer_steps": step, "training_rows": step * eff, "source_rows": step * eff,
                     "epoch_padding_rows": 0},
        "full_ft": record_ft, "auxiliary_heads": heads_pin, "camera": verified["camera"],
        "camera_sha256": verified["camera_sha256"], "geometry": geometry}
    ddp_config.validate_training_result(record(result), verified, LABEL)
    result_path = write_json("training_result.json", result)

    shards = {f"{directory}/{full_ft.EXPORT_DIRECTORY}/{export['index']['name']}":
              {"sha256": export["index"]["sha256"], "bytes": (weights_dir / export["index"]["name"]).stat().st_size}}
    for item in export["files"]:
        shards[f"{directory}/{full_ft.EXPORT_DIRECTORY}/{item['name']}"] = {"sha256": item["sha256"], "bytes": item["bytes"]}
    files = {}
    for path in sorted(pub_dir.rglob("*")):
        if path.is_file() and path.name not in ("SHA256_MANIFEST.json", "PUBLISHED.json"):
            rel = path.relative_to(pub_dir).as_posix()
            files[rel] = shards.get(rel) or {"sha256": sha256(path), "bytes": path.stat().st_size}
    census_path = pub_dir / "SHA256_MANIFEST.json"
    census_path.write_bytes(canonical_bytes({"schema": "student-publication-sha256-v1", "files": files,
                                             "excludes": ["SHA256_MANIFEST.json", "PUBLISHED.json"],
                                             "provenance": prov, **flags}))
    model_pin = MODEL_PINS[protocol["student"]]
    receipt = {
        "schema": "student-publication-v1", "local_path": str(pub_dir), "published_path": str(pub_dir),
        "evaluation_path": None, "sha256_manifest": binding(census_path), "training_result": binding(result_path),
        "local_training_result": binding(result_path), "file_count": len(files), "status": "TRAINED",
        "student": protocol["student"], "base": {k: model_pin[k] for k in ("repo_id", "revision")},
        "base_restart": "fresh_load_of_original_snapshot_no_smoke_adapter", "preprocessing": verified["rgb"],
        "trained_module_families": [g for g, on in record_ft["train"].items() if on],
        "adapter": {"full_weights_manifest_sha256": adapter["full_weights"]["sha256"],
                    "geometry_weights_sha256": geometry["weights"]["sha256"]},
        "adapter_directory": directory, "training_data_sha256": binding(train_path)["sha256"],
        "protocol": binding(proto_path), "division": binding(div_path), "protocol_version": ddp_config.VERSION}
    receipt_path = write_json("PUBLISHED.json", receipt)
    if "camera_manifest" not in store and heads_meta.get("camera", {}).get("settings", {}).get("g3t_prior"):
        cam_manifest = Path(argv[5]).resolve().parent / "camera_manifest.jsonl"
        if cam_manifest.is_file():
            store["camera_manifest"] = str(cam_manifest)
            store["camera_manifest_sha256"] = sha256(cam_manifest)
    pin = validate_adapter("distilled", protocol["student"], pub_dir / directory, receipt_path, DEFAULT_CONFIG,
                           provisional_diagnostic=LABEL, geometry_store=store, carriers="insert", headcall="decode")
    print(json.dumps({"published_path": str(pub_dir), "adapter_dir": str(pub_dir / directory),
                      "receipt_path": str(receipt_path), "step": step,
                      "full_weights_manifest_sha256": adapter["full_weights"]["sha256"],
                      "geometry_weights_sha256": geometry["weights"]["sha256"], "auxiliary_heads_sha256": heads_pin["sha256"],
                      "pins": sorted(pin)}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
