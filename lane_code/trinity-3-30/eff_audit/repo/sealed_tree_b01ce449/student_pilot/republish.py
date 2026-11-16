"""Re-derive an existing publication with its checkpoint cadence recorded as run control.

The cadence never shapes the weights, so it leaves ``protocol["training"]`` and the
``training_sha256`` that covers it, and moves to ``protocol["run_control"]`` under its own
``run_control_sha256``. Adapter bytes are copied and re-verified, never rewritten, and the
original publication directory is read only.
"""

from datetime import datetime, timezone
from pathlib import Path

from . import storage
from .common import binding, digest_json, load_json, sha256
from .ddp_config import normalize_training_config, run_control_from_config, validate_training_result
from .storage import adapter_directory, contained, copy_new, require_mode, write_new

RULING = ("Orchestrator ruling 2026-09-20: the checkpoint cadence is run control, not a weight-shaping "
          "training setting, so it leaves protocol[\"training\"] and training_sha256 and is recorded in "
          "protocol[\"run_control\"] with its own run_control_sha256. The adapter bytes are unchanged.")
RULING_DOCUMENTS = [
    "/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_base_reeval_instructed_onethinker/out/BLOCKER_ARMC_PROTOCOL.md",
    "/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_eval_cells_f09e526/out/BLOCKER_ATTEMPT_AUTHORITY.md",
]
REWRITTEN = ("protocol.json", "training_result.json", "publication_provenance.json")
ADDED = "republication_provenance.json"


def verify_census(root, manifest, directory):
    """Re-hash every published file; the adapter is reported separately because it must never move."""
    for name, entry in sorted(manifest["files"].items()):
        path = contained(root, name)
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Publication census file is missing or symlinked: {name}")
        if sha256(path) != entry["sha256"] or path.stat().st_size != entry["bytes"]:
            subject = "Adapter bytes" if name.startswith(directory + "/") else "Published bytes"
            raise ValueError(f"{subject} differ from the original SHA256_MANIFEST.json: {name}")
    return {name: entry["sha256"] for name, entry in manifest["files"].items()}


def default_target(source):
    return source.parent / (source.name + "_republish_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))


def republish(publication, publish_root=None, label=None, dry_run=False, output=None):
    source = Path(publication).resolve()
    receipt = require_mode(load_json(source / "PUBLISHED.json"), label)
    if (receipt.get("schema") != "student-publication-v1" or receipt.get("status") != "TRAINED"
            or Path(receipt.get("published_path", "")).resolve() != source):
        raise ValueError("Republication requires a completed publication directory and its own receipt")
    manifest_pin = receipt["sha256_manifest"]
    if Path(manifest_pin["path"]).resolve() != source / "SHA256_MANIFEST.json":
        raise ValueError("Publication manifest escapes its directory")
    binding(manifest_pin["path"], manifest_pin["sha256"])
    manifest = require_mode(load_json(source / "SHA256_MANIFEST.json"), label)
    if (manifest.get("schema") != "student-publication-sha256-v1" or manifest.get("provenance") != receipt.get("provenance")
            or receipt.get("file_count") != len(manifest["files"])):
        raise ValueError("Publication census, provenance, or file count is inconsistent")
    directory = adapter_directory(label)
    census = verify_census(source, manifest, directory)
    adapter = {kind: census[f"{directory}/adapter_{name}"] for kind, name in
               (("config_sha256", "config.json"), ("weights_sha256", "model.safetensors"))}
    if adapter != receipt["adapter"]:
        raise ValueError("Published adapter hashes disagree with the publication receipt")

    protocol = require_mode(load_json(source / "protocol.json"), label)
    result = require_mode(load_json(source / "training_result.json"), label)
    if "run_control" in protocol or "run_control" in result:
        raise ValueError("This publication already records its run control outside the training protocol")
    training = protocol.get("training")
    settings = normalize_training_config(training, protocol.get("student"))
    run_control = run_control_from_config(training)
    if {**settings, **run_control} != training or result.get("settings") != training:
        raise ValueError("Republication moves run-control keys only; this training block differs otherwise")
    if (protocol.get("training_sha256") != digest_json(training) or result.get("training_sha256") != protocol["training_sha256"]
            or receipt.get("protocol", {}).get("sha256") != result.get("protocol", {}).get("sha256")):
        raise ValueError("The original publication's training hash or protocol lineage is inconsistent")
    if digest_json(settings) == protocol["training_sha256"]:
        raise ValueError("Nothing to move: this training block carries no run-control key")

    target = Path(publish_root).resolve() if publish_root is not None else default_target(source)
    if not target.is_relative_to(storage.PUBLISH_HOME) or target == storage.PUBLISH_HOME or target == source:
        raise ValueError("Republication requires a new directory under /data3/jjyeung, alongside the original")
    if target.exists():
        raise ValueError(f"Use a new publication directory; existing publications remain immutable: {target}")

    moved = sorted(set(run_control) & set(training))
    new_protocol = {**protocol, "training": settings, "training_sha256": digest_json(settings),
                    "run_control": run_control, "run_control_sha256": digest_json(run_control)}
    new_result = {**result, "settings": settings, "training_sha256": digest_json(settings),
                  "run_control": run_control, "run_control_sha256": digest_json(run_control),
                  "protocol": {"path": str(target / "protocol.json"), "sha256": digest_json(new_protocol)}}
    validate_training_result(new_result, new_protocol, label)
    plan = {"schema": "student-republication-plan-v1", "original_publication": str(source), "publish_root": str(target),
            "ruling": RULING, "ruling_documents": RULING_DOCUMENTS, "moved_keys": moved, "run_control": run_control,
            "run_control_sha256": digest_json(run_control), "verified_files": len(census),
            "training_sha256": {"original": protocol["training_sha256"], "republished": digest_json(settings)},
            "rewritten": {"protocol.json": {"original_sha256": census["protocol.json"], "republished_sha256": digest_json(new_protocol)},
                          "training_result.json": {"original_sha256": census["training_result.json"],
                                                   "republished_sha256": digest_json(new_result)}},
            "adapter": {**adapter, "unchanged": True}}
    if dry_run:
        plan = storage.tag({**plan, "status": "REPUBLICATION_DRY_RUN", "dry_run": True}, label)
        if output is not None:
            write_new(Path(output).name, plan, Path(output).parent)
        return plan

    config = {"republished_from": str(source), "publish_root": str(target), "ruling": RULING,
              "original_training_sha256": protocol["training_sha256"], "training_sha256": digest_json(settings),
              "run_control_sha256": digest_json(run_control), **storage.provisional_flags(label)}
    provenance = storage.code_provenance(config)
    target.mkdir(parents=True, exist_ok=False)
    files = {}
    for name, entry in sorted(manifest["files"].items()):
        if name in REWRITTEN:
            continue
        copy_new(source / name, contained(target, name), entry["sha256"])
        files[name] = dict(entry)
    publication = require_mode(load_json(source / "publication_provenance.json"), label)
    new_publication = {**publication, "config": {**publication["config"], "publish_root": str(target),
                                                 "republished_from": str(source), "ruling": RULING},
                       "provenance": provenance}
    republication = storage.tag({"schema": "student-republication-v1", "original_publication": str(source),
                                 "original_published_sha256": sha256(source / "PUBLISHED.json"),
                                 "original_sha256_manifest": manifest_pin, "ruling": RULING,
                                 "ruling_documents": RULING_DOCUMENTS, "moved_keys": moved,
                                 "training_sha256": plan["training_sha256"], "run_control": run_control,
                                 "run_control_sha256": digest_json(run_control),
                                 "adapter": {**adapter, "unchanged": True}, "verified_files": len(census),
                                 "rewritten": {name: {"original_sha256": census[name]} for name in REWRITTEN},
                                 "provenance": provenance}, label)
    for name, value in (("protocol.json", new_protocol), ("training_result.json", new_result),
                        ("publication_provenance.json", new_publication), (ADDED, republication)):
        path = write_new(name, value, target)
        files[name] = {"sha256": sha256(path), "bytes": path.stat().st_size}
        republication["rewritten"].get(name, {})["republished_sha256"] = files[name]["sha256"]
    if files["protocol.json"]["sha256"] != digest_json(new_protocol) or files["training_result.json"]["sha256"] != digest_json(new_result):
        raise ValueError("Republished protocol or training result did not land as derived")
    manifest_path = write_new("SHA256_MANIFEST.json", {**manifest, "files": files, "provenance": provenance}, target)
    new_receipt = {**receipt, "published_path": str(target), "provenance": provenance, "file_count": len(files),
                   "sha256_manifest": binding(manifest_path), "protocol": binding(target / "protocol.json"),
                   "division": binding(target / "division.json"), "training_result": binding(target / "training_result.json"),
                   "republished_from": {"path": str(source), "published_sha256": republication["original_published_sha256"],
                                        "training_sha256": protocol["training_sha256"], "ruling": RULING}}
    write_new("PUBLISHED.json", storage.tag(new_receipt, label), target)
    verified = verify_census(target, load_json(manifest_path), directory)
    if {name: verified[name] for name in adapter_files(directory, verified)} != {name: census[name] for name in adapter_files(directory, census)}:
        raise ValueError("Republished adapter bytes differ from the original publication")
    return storage.tag({**plan, "status": "REPUBLISHED", "dry_run": False, "file_count": len(files),
                        "published": binding(target / "PUBLISHED.json"), "provenance": provenance}, label)


def adapter_files(directory, census):
    return sorted(name for name in census if name.startswith(directory + "/"))
