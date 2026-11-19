"""CPU preparation of the HC/HX v3 frozen preparations on code-aws (inside the trainer container; TRAINER = the hc-v3
tree; /opt/anyhost_jobs = the training closure 0873a4b61d97, so pre-stage cache keys match the GPU job's).

  smoke MILESTONE              frozen/SMOKE_HCV3 and SMOKE_HXV3 = SMOKE_HC's and SMOKE_HX's rows with hc_v3.pair(
                               SMOKE_PDG_S2_V3G's config, smoke sidecars, MILESTONE's pins, smoke=True)
  full SOURCE [--steps N] [--suffix S] [--hc-rows FROZEN]
                               SOURCE = PDG v3 stage-2 run name (its newest TRAINED publication with N optimizer steps,
                               default 1550) or a milestone directory (a dry run). frozen/HCV3{S}_S17 = RG2P2_X_W32_S17's
                               rows with HC_S17_INDEX's head-call and plain targets (or a copy of --hc-rows, an earlier
                               HC v3 preparation); frozen/HXV3{S}_S17 = RG2P2_X_W32_S17's rows. Config: hc_v3.pair(the
                               publication's own config.json, full sidecars, its pins).

Every preparation copies its source's division, rows and input audits (HC: X's prompts and audits, its replaced
targets re-tokenized for the target-length fields only) and rewrites only what depends on the config. Before any GPU is
held it checks: the init pins load exactly into the live module shapes (connector, heads) and the export names this
base; the head-call sidecar joins every entry to an admitted row (headcall.rows.join, as train() does at startup); every
row has a geometry store row on its processor grid; the pre-stage cache passes prestage.py check.
"""
import argparse
import copy
import hashlib
import json
import math
import os
import pickle
import sys
import time
from pathlib import Path

sys.path.insert(0, os.environ["TRAINER"])
sys.path.insert(0, "/opt/anyhost_jobs")
sys.path.insert(0, str(Path(__file__).resolve().parent))

import hc_v3  # noqa: E402
import prep_pdg_v3 as P  # noqa: E402
import prestage  # noqa: E402
from headcall import rows as headcall_rows  # noqa: E402
from student_pilot import auxiliary_losses, common, ddp_admission, geometry_input  # noqa: E402
from student_pilot.auxiliary_targets import input_identity  # noqa: E402
from student_pilot import provisional_data as data  # noqa: E402
from student_pilot.common import binding, canonical_bytes, digest_json  # noqa: E402

RUNS = P.RUNS
WORK = RUNS / "incoming_r1" / "hcv3"
P.WORK = WORK  # build_frozen keeps a copy of each config here
LABEL, STUDENT = P.LABEL, P.STUDENT
FULL_SIDECARS = {  # tools/headcall_rows.py build v3 (HEADCALL_FULLFT_BUILD.md): full HC and HX sidecars
    "HC": {"path": "/project/community/jjyeung/ap_shared/hc/542f552b3120.jsonl.gz",
           "sha256": "542f552b3120f39958f5e381c9c431d91dcf2d9039e186b8c37966d8e038395c"},
    "HX": {"path": "/project/community/jjyeung/ap_shared/hc/f42c40c9a80d.jsonl.gz",
           "sha256": "f42c40c9a80da51af02ebe4e2d8fb8c7382ad31b6103b9c7d5ae166da29c7ed1"}}
STEPS = 1550


def log(event, **fields):
    print(f"PREP_HC_V3 {event} {json.dumps(fields, sort_keys=True, default=str)}", flush=True)


def check_init(config, protocol_base_sha256):
    """The pins load exactly into this config's live connector and heads, and the export names this run's base."""
    from student_pilot import full_ft
    hidden, output_dim, vit_dim = P.model_dims()
    geometry = geometry_input.GeometryInput(config["geometry"], output_dim)
    heads = auxiliary_losses.AuxiliaryHeads(hidden, None, camera=config["camera"], vit_dim=vit_dim)
    receipt = full_ft.load_init_modules(config["full_ft"], geometry=geometry, heads=heads, resolve=common.resolve_read)
    init = config["full_ft"]["init"]
    manifest_path = Path(common.resolve_read(init["path"]))
    if prestage.sha_file(manifest_path) != init["sha256"]:
        raise ValueError("The full_export manifest differs from its pin")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("base", {}).get("base_sha256") != protocol_base_sha256:
        raise ValueError("The full_export init was trained from another base snapshot")
    full_ft.read_export(manifest_path.parent)  # every shard against the manifest, as load_export reads them
    gate = float(geometry.projector.gate.detach())
    log("init_verified", modules=receipt, full_export=init["sha256"], tensors=manifest.get("tensor_count"), gate=gate)
    return {"modules": receipt, "full_export": init["sha256"], "gate": gate}


def join_check(frozen, config):
    loaded, _ = data._read_manifest(ddp_admission.input_path(frozen / "training.json"))
    _, report = headcall_rows.join(loaded["rows"], config["headcall"], resolve=common.resolve_read)
    (frozen / "headcall_join_check.json").write_bytes(canonical_bytes(report))
    log("headcall_join", frozen=frozen.name, report=report)
    return report


def ensure_prestage(frozen):
    """A preparation without a cloned cache gets prestage.py build (small smokes), then check."""
    import subprocess
    cache, _, _ = prestage.cache_dir(frozen)
    if not (cache / "RECEIPT.json").is_file():
        subprocess.run([sys.executable, "-B", "/opt/anyhost_jobs/prestage.py", "build", str(frozen)], check=True)
        subprocess.run([sys.executable, "-B", "/opt/anyhost_jobs/prestage.py", "check", str(frozen)], check=True)
    log("prestage_ready", frozen=frozen.name, cache=str(cache))


def finish(frozen, config, base_sha256, init_report):
    P.store_coverage(config, frozen)
    report = join_check(frozen, config)
    P.stamp(frozen, config)
    summary = {"frozen": str(frozen), "config_sha256": prestage.sha_bytes(prestage.canonical(config)),
               "rows": json.loads((frozen / "ADMISSION.json").read_text())["rows"], "init": init_report,
               "headcall_join": report, "headcall": config["headcall"]}
    (frozen / "HCV3_PREP.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    log("ready", **summary)


def extra_paths(config):
    paths = [config["camera"]["supervision"]["path"], config["geometry"]["store"]["manifest"],
             config["full_ft"]["init"]["path"], config["full_ft"]["init_modules"]["geometry"]["path"],
             config["full_ft"]["init_modules"]["heads"]["path"], config["headcall"]["sidecar"]["path"]]
    cam_manifest = config.get("geometry", {}).get("store", {}).get("camera_manifest")
    if cam_manifest:
        paths.append(cam_manifest)
    return paths


def attach_camera_store_pin(base, init):
    if init.get("g3t_prior") is None or base.get("geometry", {}).get("store", {}).get("camera_manifest"):
        return
    store_manifest = Path(common.resolve_read(base["geometry"]["store"]["manifest"]))
    cam_manifest = store_manifest.parent / "camera_manifest.jsonl"
    if cam_manifest.is_file():
        init["camera_store"] = P.pin(cam_manifest)


# ------------------------------------------------------------------------------------------------- HC rows (full)

def target_audit(processor, row, audit):
    """X's input audit with the target-length fields of the row's new target (prompt unchanged), as
    build_hc_smoke_frozen.update_audits_for_rows computed them for the smoke."""
    from student_pilot import diagnostic_data as clean
    tokens = clean.target_tokens(processor, row)
    if tokens > clean.TRAINING["max_target_tokens_including_eos"]:
        raise ValueError(f"Row {row['qid']} exceeds max_target_tokens_including_eos: {tokens}")
    length = int(audit["prompt_tokens"]) + tokens
    padded = math.ceil(length / 8) * 8
    if padded > clean.TRAINING["max_sequence_tokens"]:
        raise ValueError(f"Row {row['qid']} exceeds max_sequence_tokens: {padded}")
    return {**audit, "assistant_tokens_including_eos": tokens, "padding_tokens": padded - length, "sequence_tokens": padded}


def hc_rows(x_name, index_name, dst):
    """HC's training rows, audits and census from RG2P2_X's and the HC index's replaced entries; writes dst's
    candidate index (replaced entries' target_path re-pointed at dst's hard-linked target shards)."""
    from student_pilot import batches
    src, idx = (RUNS / "frozen" / x_name).resolve(), (RUNS / "frozen" / index_name).resolve()
    index_manifest = json.loads((idx / "HC_INDEX.json").read_text())
    shards = {}
    for name, sha in index_manifest["target_shards"].items():
        if not (dst / name).exists():
            os.link(idx / name, dst / name)
        if prestage.sha_file(dst / name) != sha:
            raise ValueError(f"HC target shard {name} differs from HC_INDEX.json")
        shards[name] = str(ddp_admission.input_path(dst / name))
    replaced, index_lines = {}, []
    with open(idx / "candidate_index.jsonl", "rb") as stream:
        for line in stream:
            entry = json.loads(line)
            if "target" in entry and "student_input" in entry and entry.get("target_path", "").rsplit("/", 1)[-1] in shards:
                entry["target_path"] = shards[entry["target_path"].rsplit("/", 1)[-1]]
                replaced[entry["qid"]] = entry
                line = (json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
            index_lines.append(line)
    counts = index_manifest["counts"]
    if len(replaced) != counts["replaced_headcall"] + counts["replaced_plain"]:
        raise ValueError(f"{len(replaced)} replaced entries, HC_INDEX.json counts {counts}")
    # Every replaced target is the shard's bytes at its offset (the inline text, its sha256 and the shard agree).
    blobs = {name: (dst / name).read_bytes() for name in shards}
    for entry in replaced.values():
        text_bytes = entry["target"].encode("utf-8")
        blob = blobs[entry["target_path"].rsplit("/", 1)[-1]]
        if (blob[entry["target_offset"]:entry["target_offset"] + entry["target_length"]] != text_bytes
                or hashlib.sha256(text_bytes).hexdigest() != entry["sha256"]):
            raise ValueError(f"HC index entry {entry['qid']} differs from its target shard")
    del blobs
    if not (dst / "candidate_index.jsonl").exists():
        with open(dst / "candidate_index.jsonl", "xb") as out:
            out.writelines(index_lines)
    del index_lines
    source, cache = P.source_manifest(src)
    processor = batches.load_processor(STUDENT)
    rows, audits, changed = [], [], {}
    for row, audit in zip(source["rows"], source["input_audits"]):
        if row["qid"] != audit["qid"]:
            raise ValueError("Source rows and audits are out of order")
        entry = replaced.get(row["qid"])
        if entry is None:
            rows.append(row)
            audits.append(audit)
            continue
        if input_identity(row) != input_identity(entry):
            raise ValueError(f"HC index entry {row['qid']} has another input than X's row")
        new = dict(row)
        new["target"] = entry["target"]
        new["candidate_provenance"] = {"target": {"path": entry["target_path"], "sha256": entry["sha256"],
                                                  "offset": entry["target_offset"], "length": entry["target_length"]},
                                       "row": None, "generation_commit": entry["generation_commit"],
                                       "validation_commit": entry["validation_commit"]}
        rows.append(new)
        audits.append(target_audit(processor, new, audit))
        changed[row["qid"]] = new
    if len(changed) != len(replaced):
        raise ValueError(f"{len(replaced) - len(changed)} replaced entries are not admitted X rows")
    protocol = json.loads((src / "protocol.json").read_text())
    census = []
    for item in protocol["candidate_census"]:
        if item["qid"] in changed:
            item = {**item, "row_sha256": digest_json(changed[item["qid"]])}
        census.append(item)
    manifest = {"accepted_before_token_limits": source["accepted_before_token_limits"],
                "pre_evaluation_drops": source["pre_evaluation_drops"], "rows": rows, "input_audits": audits,
                "counts": data.training_counts(rows, audits)}
    log("hc_rows", rows=len(rows), replaced=len(changed), source_cache=str(cache))
    return manifest, census, cache


def build_hc_frozen(x_name, index_name, dst_name, config, extra):
    """prep_pdg_v3.build_frozen with HC's rows: protocol from X's (HC census, HC candidate index), training manifest,
    request, admission; pre-stage cache = X's frame packs (identical frames) with rows.json rendered from HC's rows."""
    from student_pilot.provisional import division_candidates, tag, write_artifact
    from student_pilot.storage import code_provenance
    import prep_rung1
    t0 = time.time()
    src, dst = (RUNS / "frozen" / x_name).resolve(), RUNS / "frozen" / dst_name
    P.validated(json.loads(json.dumps(config)))
    config_bytes = prestage.canonical(config)
    if dst.exists() and (dst / "config.json").is_file() and (dst / "config.json").read_bytes() != config_bytes:
        raise ValueError(f"{dst} exists with another config; choose a new name")
    dst.mkdir(parents=True, exist_ok=True)
    dst = dst.resolve()
    WORK.mkdir(parents=True, exist_ok=True)
    if not (dst / "inherited_division.json").exists():
        os.link(src / "inherited_division.json", dst / "inherited_division.json")
    if not (dst / "config.json").exists():
        (dst / "config.json").write_bytes(config_bytes)
        os.chmod(dst / "config.json", 0o444)
    (WORK / f"c_{prestage.sha_bytes(config_bytes)[:12]}.json").write_bytes(config_bytes)
    manifest_rows, census, x_cache = hc_rows(x_name, index_name, dst)
    if not (dst / "protocol.json").exists():
        protocol = json.loads((src / "protocol.json").read_text())
        for key in P.PROTOCOL_CONFIG_KEYS:
            protocol.pop(key, None)
        protocol["candidate_census"] = census
        protocol["candidate_source"] = binding(ddp_admission.input_path(dst / "candidate_index.jsonl"))
        identities = [tag({key: row[key] for key in ("qid", "dataset", "scene", "category")}, LABEL) for row in census]
        protocol.update(**division_candidates(identities, LABEL, protocol["division"]["heldout_fraction_of_groups"],
                                              binding(ddp_admission.input_path(dst / "inherited_division.json"))))
        protocol.update(**data.training_protocol_fields(ddp_admission.input_path(dst / "config.json"), STUDENT),
                        runtime=data.runtime_bindings() + P.ddp_config.runtime_bindings())
        write_artifact(dst / "protocol.json", protocol, LABEL)
    verified = data.load_protocol(ddp_admission.input_path(dst / "protocol.json"), LABEL, weights=True, student=STUDENT)
    protocol_binding = binding(ddp_admission.input_path(dst / "protocol.json"))
    if not (dst / "training.json").exists():
        manifest = {"schema": "provisional-diagnostic-training-manifest-v1", "protocol": protocol_binding,
                    "PROVISIONAL_DIVISION_SHA": verified["PROVISIONAL_DIVISION_SHA"],
                    "candidate_source": verified["candidate_source"], **manifest_rows, "training_ready": True}
        write_artifact(dst / "training.json", manifest, LABEL)
    del manifest_rows
    loaded, manifest_binding = data._read_manifest(ddp_admission.input_path(dst / "training.json"))
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
    log("admitted", dst=dst_name, rows=len(loaded["rows"]), protocol_sha256=checked["protocol_sha256"],
        seconds=round(time.time() - t0, 1))
    if x_cache is None:
        raise ValueError(f"{x_name} has no pre-stage cache to take the frame packs from")
    clone_rerendered(src, x_cache, dst, loaded, verified, extra)
    import subprocess
    subprocess.run([sys.executable, "-B", "/opt/anyhost_jobs/prestage.py", "check", str(dst)], check=True)
    log("prestage_checked", dst=dst_name, seconds=round(time.time() - t0, 1))
    return dst


def clone_rerendered(src, src_cache, dst, loaded, verified, extra):
    """prep_pdg_v3.clone_prestage for rows whose targets differ from the source's: the frame packs and STAGING.json are
    hard links (same frames), rows.json is rendered from these rows exactly as prestage.build renders it, and the
    verify stamp gets these rows' order and counts."""
    cache, _, _ = prestage.cache_dir(dst)
    if (cache / "RECEIPT.json").is_file():
        return cache
    placeholder_rows, references = [], 0
    for row in loaded["rows"]:
        inputs = row.get("student_input")
        if inputs is not None:
            references += len(inputs["frames"])
            inputs = {name: ([{"path": "%s/%s/%s" % (prestage.PLACEHOLDER, frame["sha256"][:2], frame["sha256"]),
                               "sha256": frame["sha256"]} for frame in value] if name == "frames" else value)
                      for name, value in inputs.items()}
            row = {name: (inputs if name == "student_input" else value) for name, value in row.items()}
        placeholder_rows.append(row)
    text = common.canonical_bytes({"rows": placeholder_rows})
    del placeholder_rows
    prefix, suffix = b'{\n  "rows": ', b"\n}\n"
    if not text.startswith(prefix) or not text.endswith(suffix):
        raise ValueError("unexpected canonical rendering of the input rows")
    rows_text = text[len(prefix):-len(suffix)]
    del text
    if rows_text.count(prestage.PLACEHOLDER.encode()) != references:
        raise ValueError("the frames-root placeholder occurs outside the frame paths")
    src_receipt = json.loads((src_cache / "RECEIPT.json").read_text())
    if src_receipt["rows_text"]["references"] != references:
        raise ValueError("HC rows reference other frames than the source cache")
    # The shared clone writes rows.json as a link; replace it with this rendering inside the part directory.
    original = P.clone_prestage.__globals__["os"].link

    def link(source, target, *args, **kwargs):
        if Path(target).name == "rows.json":
            Path(target).write_bytes(rows_text)
            return None
        return original(source, target, *args, **kwargs)
    P.os.link = link
    try:
        cache = P.clone_prestage(src, src_cache, dst, loaded, verified, extra)
    finally:
        P.os.link = original
    receipt = json.loads((cache / "RECEIPT.json").read_text())
    stamp = json.loads((cache / "VERIFY_STAMP.json").read_text())
    order = prestage.sha_bytes(b"\0".join(row["qid"].encode() for row in loaded["rows"]))
    counts = prestage.sha_bytes(prestage.canonical(loaded["counts"]))
    if (stamp["row_order_sha256"] != order or prestage.sha_file(cache / "rows.json") != prestage.sha_bytes(rows_text)):
        raise ValueError("Re-rendered pre-stage cache differs from the HC rows")
    if stamp["counts_sha256"] != counts or receipt["rows_text"]["sha256"] != prestage.sha_bytes(rows_text):
        fix_stamp(cache, counts, rows_text, references)
    log("prestage_rerendered", dst=dst.name, cache=str(cache), rows_json_sha256=prestage.sha_bytes(rows_text))
    return cache


def fix_stamp(cache, counts_sha256, rows_text, references):
    """Rewrite VERIFY_STAMP.json (this preparation's counts) and RECEIPT.json (stamp, rows.json) of a fresh clone."""
    for name in ("VERIFY_STAMP.json", "RECEIPT.json"):
        os.chmod(cache / name, 0o644)
    stamp = json.loads((cache / "VERIFY_STAMP.json").read_text())
    stamp["counts_sha256"] = counts_sha256
    stamp_bytes = prestage.canonical(stamp)
    (cache / "VERIFY_STAMP.json").write_bytes(stamp_bytes)
    receipt = json.loads((cache / "RECEIPT.json").read_text())
    receipt["verify_stamp"] = {"file": "VERIFY_STAMP.json", "sha256": prestage.sha_bytes(stamp_bytes), "bytes": len(stamp_bytes)}
    receipt["rows_text"] = {"file": "rows.json", "sha256": prestage.sha_bytes(rows_text), "bytes": len(rows_text),
                            "placeholder": prestage.PLACEHOLDER, "references": references}
    (cache / "RECEIPT.json").write_bytes(prestage.canonical(receipt))
    for name in ("VERIFY_STAMP.json", "RECEIPT.json", "rows.json"):
        os.chmod(cache / name, 0o444)


# ------------------------------------------------------------------------------------------------------------ modes

def smoke(milestone, suffix=""):
    init = hc_v3.milestone_pins(milestone)
    log("init_source", **init["source"])
    base = P.frozen_config("SMOKE_PDG_S2_V3G")
    attach_camera_store_pin(base, init)
    sidecars = {arm: P.frozen_config(f"SMOKE_{arm}")["headcall"]["sidecar"] for arm in hc_v3.ARMS}
    configs = hc_v3.pair(base, sidecars, init, smoke=True)
    protocol_base = json.loads((RUNS / "frozen" / "SMOKE_HC" / "protocol.json").read_text())["base_sha256"]
    report = check_init(configs["HC"], protocol_base)
    for arm in hc_v3.ARMS:
        frozen = P.build_frozen(f"SMOKE_{arm}", f"SMOKE_{arm}V3{suffix}", configs[arm], extra_paths(configs[arm]))
        ensure_prestage(frozen)
        finish(frozen, configs[arm], protocol_base, {**report, "source": init["source"]})


def full(source, steps, suffix, hc_from, arms, base_name=None):
    path = Path(source)
    init = (hc_v3.milestone_pins(path) if path.is_absolute() and (path / "MILESTONE.json").is_file()
            else hc_v3.run_publication(RUNS / source, steps))
    log("init_source", **init["source"])
    if init["source"]["kind"] == "publication":
        if base_name:
            raise ValueError("A final publication derives from its own config.json; --base is for dry runs")
        base = json.loads((Path(init["source"]["path"]) / "config.json").read_text())
    else:  # a dry run from a milestone stand-in: PDG v3's stage-2 config (or another frozen v3 stage-2 config)
        base = P.frozen_config(base_name or "PDG_S2_V3G")
    attach_camera_store_pin(base, init)
    configs = hc_v3.pair(base, FULL_SIDECARS, init)
    protocol_base = json.loads((RUNS / "frozen" / "RG2P2_X_W32_S17" / "protocol.json").read_text())["base_sha256"]
    report = {**check_init(configs["HC"], protocol_base), "source": init["source"]}
    names = {"HC": f"HCV3{suffix}_S17", "HX": f"HXV3{suffix}_S17"}
    if "HX" in arms:
        hx = P.build_frozen("RG2P2_X_W32_S17", names["HX"], configs["HX"], extra_paths(configs["HX"]))
        finish(hx, configs["HX"], protocol_base, report)
    if "HC" in arms:
        if hc_from:
            hc = P.build_frozen(hc_from, names["HC"], configs["HC"], extra_paths(configs["HC"]))
        else:
            hc = build_hc_frozen("RG2P2_X_W32_S17", "HC_S17_INDEX", names["HC"], configs["HC"],
                                 extra_paths(configs["HC"]))
        finish(hc, configs["HC"], protocol_base, report)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["smoke", "full"])
    parser.add_argument("source")
    parser.add_argument("--steps", type=int, default=STEPS)
    parser.add_argument("--suffix", default="")
    parser.add_argument("--hc-rows", help="an earlier HC v3 preparation whose rows to copy (fast path)")
    parser.add_argument("--arms", default="HC,HX", help="full mode: which preparations to build (HC, HX or both)")
    parser.add_argument("--base", help="full mode from a milestone (dry run): the frozen stage-2 config to derive from")
    args = parser.parse_args()
    os.chdir(os.environ["TRAINER"])
    if args.suffix and not args.suffix.isalnum():
        raise ValueError("--suffix must be alphanumeric")
    if args.mode == "smoke":
        smoke(args.source, args.suffix)
    else:
        arms = set(args.arms.split(","))
        if not arms or arms - set(hc_v3.ARMS):
            raise ValueError("--arms takes HC, HX or HC,HX")
        full(args.source, args.steps, args.suffix, args.hc_rows, arms, args.base)


if __name__ == "__main__":
    main()
