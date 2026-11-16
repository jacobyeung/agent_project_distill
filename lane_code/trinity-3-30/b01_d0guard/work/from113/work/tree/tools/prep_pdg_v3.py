"""CPU preparation of the PDG v3 frozen preparations on code-aws (inside the trainer container; TRAINER = the gated
connector's tree, 8ba75d5 plus geometry_input's gated injection).

  init                         write the gated connector init (pdg_v3.write_init) and prove it loads as a no-op
  s1 SRC DST INIT              frozen/DST = frozen/SRC's rows with pdg_v3.stage1_config(SRC config, INIT)
  s2 S1RUN DST [--smoke] [--geometry-init G0]
                               frozen/DST = FT_A's rows (SMOKE_FT_A's with --smoke) with pdg_v3.stage2_config(PDG_S2's
                               config) pinning S1RUN's complete export (its publication, else its final checkpoint's
                               adapters.pt); --geometry-init replaces the connector by the gated init (gate fallback)

Each frozen preparation copies the row census, division, training rows and input audits of its source byte for byte
and rewrites only what depends on the config (protocol training fields, request, admission), as prep_pdg_s2.py did for
the v2 head weights. A source with a pre-stage cache is cloned by hard links and checked with prestage.py check.
"""
import argparse
import json
import math
import os
import pickle
import socket
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, os.environ["TRAINER"])
sys.path.insert(0, "/opt/anyhost_jobs")
sys.path.insert(0, str(Path(__file__).resolve().parent))

import torch  # noqa: E402

import pdg_v3  # noqa: E402
import prep_rung1  # noqa: E402
import prestage  # noqa: E402
from student_pilot import auxiliary_losses, common, ddp_admission, ddp_config, geometry_input  # noqa: E402
from student_pilot import provisional_data as data  # noqa: E402
from student_pilot.common import binding  # noqa: E402
from student_pilot.provisional import division_candidates, tag, write_artifact  # noqa: E402
from student_pilot.storage import code_provenance  # noqa: E402
from tools.fullft_arm_configs import validated  # noqa: E402

LABEL = prep_rung1.LABEL
STUDENT = prep_rung1.STUDENT
RUNS = (Path(os.environ["R1_MOUNT"]) / "runs" / "aws128p_20261025").resolve()
WORK = RUNS / "incoming_r1" / "fullft_cpd_inputs" / "pdgv3"
S1_FROZEN = {False: "PDG_S1_V3G", True: "SMOKE_PDG_S1_V3G"}  # the gated stage-1 preparations, by --smoke
PROTOCOL_CONFIG_KEYS = ("provenance", "init_adapter_identity", "init_adapter_sha256", "camera", "camera_sha256",
                        "geometry", "geometry_sha256")


def log(event, **fields):
    print(f"PREP_PDG_V3 {event} {json.dumps(fields, sort_keys=True, default=str)}", flush=True)


def model_dims():
    config = json.loads((Path(os.environ["STUDENT_MODEL_ROOT"])
                         / "models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a/config.json").read_text())
    return (int(config["text_config"]["hidden_size"]), int(config["vision_config"]["out_hidden_size"]),
            int(config["vision_config"]["hidden_size"]))


def pin(path):
    return {"path": str(ddp_admission.input_path(path)), "sha256": prestage.sha_file(path)}


def frozen_config(name):
    return json.loads((RUNS / "frozen" / name / "config.json").read_text())


def build_init():
    _, output_dim, _ = model_dims()
    settings = pdg_v3.gated_block(frozen_config("PDG_S1")["geometry"])
    WORK.mkdir(parents=True, exist_ok=True)
    part = WORK / f"g1.part.{os.environ.get('SLURM_JOB_ID', 'local')}.{os.getpid()}.safetensors"
    sha = pdg_v3.write_init(part, settings["feature_dim"], output_dim)
    final = WORK / f"g1_{sha[:12]}.safetensors"
    if final.exists():
        if prestage.sha_file(final) != sha:
            raise ValueError(f"{final} exists with other bytes")
        part.rename(WORK / f"{part.name}.duplicate")
    else:
        part.rename(final)
        os.chmod(final, 0o444)
    check = pdg_v3.check_init(final, sha, settings, output_dim, resolve=common.resolve_read)
    log("init_ready", path=str(final), **check)
    return final


def expected_steps(frozen_name):
    """Optimizer steps of a complete run of a preparation: max_steps, else one epoch of its admitted rows."""
    config = frozen_config(frozen_name)
    rows = json.loads((RUNS / "frozen" / frozen_name / "ADMISSION.json").read_text())["rows"]
    return int(config.get("max_steps") or math.ceil(rows / config["effective_batch_size"]))


def export_stage1(run_name, s1_frozen):
    """The stage-1 export of a complete run: its newest publication, else its final checkpoint's adapters.pt."""
    run = (RUNS / run_name).resolve()
    steps = expected_steps(s1_frozen)
    publications = sorted(run.glob("attempt-*/publication/PUBLISHED.json"), key=lambda p: p.stat().st_mtime)
    if publications:
        publication = publications[-1].parent
        result = json.loads((publication / "training_result.json").read_text())
        if result.get("status") != "TRAINED" or int(result.get("realized", {}).get("optimizer_steps", 0)) != steps:
            raise ValueError(f"Stage-1 publication {publication} is not TRAINED at {steps} steps")
        geometry, heads = publication / "geometry" / geometry_input.WEIGHTS_NAME, publication / "auxiliary_heads.pt"
        log("stage1_publication", publication=str(publication), steps=result.get("realized", {}).get("optimizer_steps"))
        return geometry, heads
    checkpoints = sorted((run / "checkpoints").glob("step_*"), key=lambda p: int(p.name.partition("_")[2]))
    if not checkpoints:
        raise ValueError(f"No stage-1 publication or checkpoint in {run}")
    checkpoint = checkpoints[-1].resolve()
    if int(checkpoint.name.partition("_")[2]) != steps:
        raise ValueError(f"Newest stage-1 checkpoint {checkpoint.name} is not the final step {steps}")
    hidden, output_dim, vit_dim = model_dims()
    config = frozen_config(s1_frozen)
    adapters = torch.load(checkpoint / "adapters.pt", map_location="cpu", weights_only=True)
    geometry_state = {k.removeprefix("geometry_input.projector."): v.detach().to("cpu", torch.float32).contiguous()
                      for k, v in adapters.items() if k.startswith("geometry_input.projector.")}
    head_state = {k.removeprefix("auxiliary_heads."): v.detach().cpu() for k, v in adapters.items()
                  if k.startswith("auxiliary_heads.")}
    module = geometry_input.GeometryInput(config["geometry"], output_dim)
    module.projector.load_state_dict(geometry_state, strict=True)
    heads = auxiliary_losses.AuxiliaryHeads(hidden, None, camera=config["camera"], vit_dim=vit_dim)
    heads.load_state_dict(head_state, strict=True)
    export = run / f"v3_export_{checkpoint.name}"
    (export / "geometry").mkdir(parents=True, exist_ok=True)
    geometry_input.save(module, export / "geometry")
    with (export / "auxiliary_heads.pt").open("wb") as handle:
        torch.save({name: value.detach().cpu() for name, value in heads.state_dict().items()}, handle)
    log("stage1_checkpoint_export", checkpoint=str(checkpoint), export=str(export))
    return export / "geometry" / geometry_input.WEIGHTS_NAME, export / "auxiliary_heads.pt"


def source_manifest(src):
    """Training rows, audits and counts of a source preparation (its pre-stage manifest when cached)."""
    receipts = sorted((RUNS / "prestage" / src.name).glob("*/RECEIPT.json"))
    if len(receipts) > 1:
        raise ValueError(f"Expected at most one pre-stage cache for {src.name}, found {receipts}")
    if receipts:
        cache = receipts[0].parent.resolve()
        return pickle.loads((cache / "manifest.pkl").read_bytes()), cache
    manifest, _ = data._read_manifest(ddp_admission.input_path(src / "training.json"))
    return manifest, None


def build_frozen(src_name, dst_name, config, extra_paths):
    t0 = time.time()
    src, dst = (RUNS / "frozen" / src_name).resolve(), RUNS / "frozen" / dst_name
    validated(json.loads(json.dumps(config)))
    config_bytes = prestage.canonical(config)
    if dst.exists() and (dst / "config.json").is_file() and (dst / "config.json").read_bytes() != config_bytes:
        raise ValueError(f"{dst} exists with another config; choose a new name")
    dst.mkdir(parents=True, exist_ok=True)
    dst = dst.resolve()
    WORK.mkdir(parents=True, exist_ok=True)
    for name in ("candidate_index.jsonl", "inherited_division.json"):
        if not (dst / name).exists():
            os.link(src / name, dst / name)
    if not (dst / "config.json").exists():
        (dst / "config.json").write_bytes(config_bytes)
        os.chmod(dst / "config.json", 0o444)
    (WORK / f"c_{prestage.sha_bytes(config_bytes)[:12]}.json").write_bytes(config_bytes)

    if not (dst / "protocol.json").exists():
        protocol = json.loads((src / "protocol.json").read_text())
        for key in PROTOCOL_CONFIG_KEYS:
            protocol.pop(key, None)
        census = list(protocol["candidate_census"])
        protocol["candidate_source"] = binding(ddp_admission.input_path(dst / "candidate_index.jsonl"))
        identities = [tag({key: row[key] for key in ("qid", "dataset", "scene", "category")}, LABEL) for row in census]
        protocol.update(**division_candidates(identities, LABEL, protocol["division"]["heldout_fraction_of_groups"],
                                              binding(ddp_admission.input_path(dst / "inherited_division.json"))))
        protocol.update(**data.training_protocol_fields(ddp_admission.input_path(dst / "config.json"), STUDENT),
                        runtime=data.runtime_bindings() + ddp_config.runtime_bindings())
        write_artifact(dst / "protocol.json", protocol, LABEL)
    verified = data.load_protocol(ddp_admission.input_path(dst / "protocol.json"), LABEL, weights=True, student=STUDENT)
    protocol_binding = binding(ddp_admission.input_path(dst / "protocol.json"))
    log("protocol_verified", dst=dst_name, seconds=round(time.time() - t0, 1))

    source, cache = source_manifest(src)
    if not (dst / "training.json").exists():
        manifest = {"schema": "provisional-diagnostic-training-manifest-v1", "protocol": protocol_binding,
                    "PROVISIONAL_DIVISION_SHA": verified["PROVISIONAL_DIVISION_SHA"],
                    "candidate_source": verified["candidate_source"],
                    "accepted_before_token_limits": source["accepted_before_token_limits"],
                    "pre_evaluation_drops": source["pre_evaluation_drops"], "rows": source["rows"],
                    "input_audits": source["input_audits"], "counts": source["counts"], "training_ready": True}
        write_artifact(dst / "training.json", manifest, LABEL)
    loaded, manifest_binding = data._read_manifest(ddp_admission.input_path(dst / "training.json"))
    if [row["qid"] for row in loaded["rows"]] != [row["qid"] for row in source["rows"]]:
        raise ValueError("Training rows differ from the source preparation")
    if not (dst / "training.json.source_receipt.json").exists():
        receipt = data._source_receipt(manifest_binding, loaded, verified)
        code_provenance(receipt)
        write_artifact(dst / "training.json.source_receipt.json", receipt, LABEL)
    data._verified_receipt(ddp_admission.input_path(dst / "training.json"), manifest_binding, loaded, verified, LABEL)
    if not (dst / "request.json").exists():
        prep_rung1.request(dst)
    checked = ddp_admission.checked_request(ddp_admission.input_path(dst / "request.json"), LABEL)
    if not (dst / "ADMISSION.json").exists():
        bindings = {"protocol": protocol_binding, "training": manifest_binding,
                    "request": binding(ddp_admission.input_path(dst / "request.json")),
                    "config": binding(ddp_admission.input_path(dst / "config.json"))}
        (dst / "ADMISSION.json").write_text(json.dumps(
            {"status": "CPU_ADMISSION_OK", "rows": len(loaded["rows"]), "counts": loaded["counts"],
             "pre_evaluation_drops": len(loaded["pre_evaluation_drops"]), "protocol_sha256": checked["protocol_sha256"],
             "bindings": bindings}, indent=1, sort_keys=True) + "\n")
    log("admitted", dst=dst_name, rows=len(loaded["rows"]), config_sha256=prestage.sha_bytes(config_bytes),
        protocol_sha256=checked["protocol_sha256"], seconds=round(time.time() - t0, 1))
    if cache is not None:
        clone_prestage(src, cache, dst, loaded, verified, extra_paths)
        subprocess.run([sys.executable, "-B", "/opt/anyhost_jobs/prestage.py", "check", str(dst)], check=True)
        log("prestage_checked", dst=dst_name, seconds=round(time.time() - t0, 1))
    return dst


def clone_prestage(src, src_cache, dst, loaded, verified, extra_paths):
    """prep_pdg_s2.py's fast clone: hard-link the source cache's frame packs and rows, write this preparation's
    manifest, verify stamp and receipt."""
    t0 = time.time()
    cache, key, material = prestage.cache_dir(dst)
    if (cache / "RECEIPT.json").is_file():
        return cache
    src_receipt = json.loads((src_cache / "RECEIPT.json").read_text())
    src_stamp = json.loads((src_cache / "VERIFY_STAMP.json").read_text())
    cache.parent.mkdir(parents=True, exist_ok=True)
    part = cache.with_name(f"{cache.name}.part.{os.environ.get('SLURM_JOB_ID', 'local')}.{os.getpid()}")
    part.mkdir(parents=True, exist_ok=True)
    for index in range(int(src_receipt["staging"]["parts"])):
        os.link(src_cache / f"frames_{index:02d}.pack", part / f"frames_{index:02d}.pack")
    for name in ("STAGING.json", "rows.json"):
        os.link(src_cache / name, part / name)
    manifest_bytes = pickle.dumps(loaded, protocol=5)
    (part / "manifest.pkl").write_bytes(manifest_bytes)
    src_prefix = str(ddp_admission.input_path(src)).rstrip("/") + "/"
    recorded = {k: v for k, v in src_receipt["verified_hashes"].items()
                if not k.startswith(src_prefix) and not str(v.get("target", "")).startswith(str(src) + "/")}
    pins = {name: {"path": str(ddp_admission.input_path(dst / name)), "stat": prestage.fingerprint(dst / name),
                   "sha256": prestage.sha_file(dst / name)} for name in prestage.INPUTS}
    for name in ("candidate_index.jsonl", "inherited_division.json", "protocol.json", "training.json"):
        path = ddp_admission.input_path(dst / name)
        target = common.resolve_read(path)
        stat = prestage.fingerprint(target)
        if stat[0] >= prestage.MEMO_MIN_BYTES:
            recorded[str(path)] = {"target": str(target), "stat": stat,
                                   "sha256": pins[name]["sha256"] if name in pins else prestage.sha_file(target)}
    for extra in extra_paths:
        target = common.resolve_read(extra)
        if Path(target).is_file():
            stat = prestage.fingerprint(target)
            if stat[0] >= prestage.MEMO_MIN_BYTES:
                recorded[str(extra)] = {"target": str(target), "sha256": prestage.sha_file(target), "stat": stat}
    rebound = pdg_v3.rebind_trainer_entries(recorded, os.environ["TRAINER"], prestage.sha_file, prestage.fingerprint)
    if rebound:
        log("prestage_trainer_entries_rebound", trainer=os.environ["TRAINER"], files=rebound)
    shards = sorted(({"path": e["target"], "sha256": e["sha256"], "bytes": e["stat"][0], "mtime_ns": e["stat"][1]}
                     for e in recorded.values()), key=lambda item: item["path"])
    stamp = {"schema": "r1-prestage-verify-v1",
             "manifest": {"path": pins["training.json"]["path"], "sha256": pins["training.json"]["sha256"],
                          "bytes": pins["training.json"]["stat"][0], "mtime_ns": pins["training.json"]["stat"][1]},
             "shards": shards, "rows": len(loaded["rows"]), "row_order_sha256": src_stamp["row_order_sha256"],
             "counts_sha256": src_stamp["counts_sha256"]}
    stamp_bytes = prestage.canonical(stamp)
    (part / "VERIFY_STAMP.json").write_bytes(stamp_bytes)
    head = {name: value for name, value in loaded.items() if name not in prestage.BIG}
    receipt = {"schema": "r1-prestage-receipt-v1", "format": prestage.FORMAT, "key": key, "key_material": material,
               "frozen": str(dst), "student": STUDENT, "label": LABEL, "trainer_commit": material["trainer_commit"],
               "inputs": pins,
               "candidate_source": {**verified["candidate_source"],
                                    "stat": prestage.fingerprint(common.resolve_read(verified["candidate_source"]["path"]))},
               "verified_hashes": recorded, "manifest_head": head, "rows": len(loaded["rows"]), "counts": loaded["counts"],
               "verify_stamp": {"file": "VERIFY_STAMP.json", "sha256": prestage.sha_bytes(stamp_bytes), "bytes": len(stamp_bytes)},
               "manifest_pickle": {"file": "manifest.pkl", "sha256": prestage.sha_bytes(manifest_bytes),
                                   "bytes": len(manifest_bytes)},
               "rows_text": src_receipt["rows_text"], "staging": src_receipt["staging"], "weights": src_receipt["weights"],
               "host": socket.gethostname(), "slurm_job": os.environ.get("SLURM_JOB_ID"),
               "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "timings": {"fast_clone": round(time.time() - t0, 1)},
               "seconds": round(time.time() - t0, 1)}
    (part / "RECEIPT.json").write_bytes(prestage.canonical(receipt))
    for name in ("manifest.pkl", "VERIFY_STAMP.json", "RECEIPT.json"):
        os.chmod(part / name, 0o444)
    os.rename(part, cache)
    log("prestage_cloned", dst=dst.name, cache=str(cache), seconds=round(time.time() - t0, 1))
    return cache


def store_coverage(config, frozen):
    """Every training row's 32-frame selection has a row in the config's geometry store (no silent zero features)."""
    from student_pilot import camera_config
    store = geometry_input.FeatureStore(config["geometry"], resolve=common.resolve_read)
    need_cam = camera_config.g3t_prior_enabled(config.get("camera"))
    if need_cam and not store.has_camera_sidecar:
        raise ValueError("camera.g3t_prior is enabled, but geometry store has no camera_manifest.jsonl")
    loaded, _ = data._read_manifest(ddp_admission.input_path(frozen / "training.json"))
    audits = {audit["qid"]: audit for audit in loaded["input_audits"]}
    missing = mismatched = missing_cam = 0
    for row in loaded["rows"]:  # ddp_training.open_geometry_store's check, before any GPU is held
        key = geometry_input.frame_key([frame["sha256"] for frame in row["student_input"]["frames"]])
        if key not in store.rows:
            missing += 1
            continue
        if store.rows[key]["shape"][1:3] != list(geometry_input.store_grid(store.settings,
                                                                             audits[row["qid"]]["video_grid_thw"][0])):
            mismatched += 1
        if need_cam and key not in store.camera_rows:
            missing_cam += 1
    log("store_coverage", frozen=frozen.name, rows=len(loaded["rows"]), missing=missing, grid_mismatch=mismatched,
        missing_camera=missing_cam, has_camera_sidecar=store.has_camera_sidecar)
    if missing or mismatched or missing_cam:
        raise ValueError(f"{missing} training rows have no geometry store row, {mismatched} differ in grid, "
                         f"{missing_cam} lack camera sidecar rows")


def stamp(frozen, config):
    """prep_pdg_s2.py's completion marker, written after admission, pre-stage check and store coverage pass."""
    (RUNS / "incoming_r1" / f"S_{frozen.name}.stamp").write_text(json.dumps(
        {"arm": frozen.name, "frozen": str(frozen), "config_sha256": prestage.sha_bytes(prestage.canonical(config))},
        indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["init", "s1", "s2"])
    parser.add_argument("names", nargs="*")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--geometry-init", help="s2 gate-failure fallback: start the connector from this gated "
                                                "init instead of the stage-1 export (heads still come from stage 1)")
    args = parser.parse_args()
    os.chdir(os.environ["TRAINER"])
    if args.mode == "init":
        build_init()
    elif args.mode == "s1":
        src, dst, init = args.names
        init_path = Path(init)
        config = pdg_v3.stage1_config(frozen_config(src), pin(init_path))
        frozen = build_frozen(src, dst, config, [config["camera"]["supervision"]["path"],
                                                 config["geometry"]["store"]["manifest"], pin(init_path)["path"]])
        store_coverage(config, frozen)
        stamp(frozen, config)
    else:
        s1_run, dst = args.names
        s1_frozen = S1_FROZEN[args.smoke]
        geometry, heads = export_stage1(s1_run, s1_frozen)
        if args.geometry_init:
            geometry = Path(args.geometry_init)
            pdg_v3.check_init(geometry, prestage.sha_file(geometry), frozen_config(s1_frozen)["geometry"], model_dims()[1],
                              resolve=common.resolve_read)
            log("stage2_fallback_geometry_init", geometry=str(geometry))
        hidden, output_dim, vit_dim = model_dims()
        config = pdg_v3.stage2_config(frozen_config("PDG_S2"), pin(geometry), pin(heads))
        if args.smoke:
            config = pdg_v3.smoke_config(config)
        check = geometry_input.GeometryInput(config["geometry"], output_dim)
        head_check = auxiliary_losses.AuxiliaryHeads(hidden, None, camera=config["camera"], vit_dim=vit_dim)
        from student_pilot import full_ft
        receipt = full_ft.load_init_modules(config["full_ft"], geometry=check, heads=head_check, resolve=common.resolve_read)
        log("stage2_init_verified", receipt=receipt)
        frozen = build_frozen("SMOKE_FT_A" if args.smoke else "FT_A", dst, config,
                              [config["camera"]["supervision"]["path"], config["geometry"]["store"]["manifest"],
                               pin(geometry)["path"], pin(heads)["path"]])
        store_coverage(config, frozen)
        stamp(frozen, config)


if __name__ == "__main__":
    main()
