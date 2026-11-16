import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT.parent)]
import native_common as C
import native_stage as S
import native_pin_graph as G

LANE = Path("/scratch/jjyeung/orch_cd/evalx")
BASELINE = dict(
    path=str(ROOT / "submissions/e47eeb632/FAMILY.json"),
    sha256="74e351b57f4a035b6dc385c2d89861d3bd6a7d31a8a63c8eaee0f30d51c2515a")
APPROVED = dict(
    path=str(C.LOGICAL_ROOT / "native_package_s24_02/seal/FAMILY.json"),
    sha256="2d35df0042908d3e1be22b3dd17740a538d1d9bc73080e5838ae331ff3698dab")
ROLES = {"code", "metadata", "masks", "model", "geometry"}
RUNTIME_FIELDS = ("runtime", "numpy", "fla", "closure", "sitecustomize")
PACKAGING = {str(C.LOGICAL_ROOT / "orchard_native" / name)
             for name in ("native_launcher.py", "native_local_check.py", "native_pin_graph.py",
                          "native_cpu_replica.py", "native_worker.py", "native_metrics.py", "native_common.py",
                          "kernels.py", "native_job.py", "MASK_CACHE_P6_BOUND.json")} | {
             str(C.LOGICAL_ROOT / "native/out2" / name)
             for name in ("nomdg.py", "perception.py", "reader_policy.py", "geometry.py",
                          "geometry_refusals.py", "r1.py", "camera_report.py")}
SCHEMA = "evalx-native-local-input-check-v2"


class ProductionRuntimeBoundary(Exception):
    pass


def objects(assets):
    parts = assets["small_objects"]
    if len(parts) != 5 or {part["role"] for part in parts} != ROLES:
        raise ValueError("The local check requires exactly the five uploaded objects")
    if sum(part["bytes"] for part in parts) >= 1000000000:
        raise ValueError("The five-object local check exceeds its admitted byte limit")
    result = {}
    for part in parts:
        S.cloud_uri(part)
        result[part["role"]] = {key: part[key] for key in ("name", "sha256", "generation", "bytes")}
        result[part["role"]]["members_sha256"] = C.canonical(part["members"])
    return result


def scope(family):
    baseline = C.load(C.checked(G.P5_FAMILY))
    approved = C.load(C.checked(APPROVED))
    for key in RUNTIME_FIELDS:
        if family["assets"][key] != baseline["assets"][key]:
            raise ValueError("The admitted runtime-import input changed: " + key)
    if family["bootstrap_pins"]["native_bootstrap.py"] != baseline["bootstrap_pins"]["native_bootstrap.py"]:
        raise ValueError("The runtime-import bootstrap changed from pilot 169589")
    contract = family["worker_contract"]
    if (set(contract) != set(approved["worker_contract"]) or any(
            contract[key] != value for key, value in approved["worker_contract"].items()
            if key not in ("mask_cache", "adapter_pins", "kernel_source_pins", "pilot_selection"))):
        raise ValueError("The reader order cannot change the remaining worker contract")
    old_adapters = approved["worker_contract"]["adapter_pins"]
    new_adapter = str(C.LOGICAL_ROOT / "native/out2/geometry_refusals.py")
    if set(contract["adapter_pins"]) != set(old_adapters) | {new_adapter}:
        raise ValueError("The reader adapter dependency set differs")
    for name, digest in old_adapters.items():
        if name not in PACKAGING and contract["adapter_pins"].get(name) != digest:
            raise ValueError("A sealed reader dependency changed: " + name)
    if any(digest != family["code_pins"].get(name) for name,digest in contract["adapter_pins"].items()):
        raise ValueError("A reader adapter differs from its shipped code pin")
    if (set(contract["kernel_source_pins"]) != {"nomdg", "geometry"} or any(
            digest != family["code_pins"].get(str(C.LOGICAL_ROOT / "native/out2" / (name+".py")))
            for name,digest in contract["kernel_source_pins"].items())):
        raise ValueError("A reader kernel differs from its shipped code pin")
    if (contract["pilot_selection"].get("families") != G.K.PILOT_COUNTS or
            contract["pilot_selection"].get("distance_datasets") != G.K.DISTANCE_DATASETS or
            len(contract["pilot_selection"].get("item_keys", [])) != 10):
        raise ValueError("The ordered pilot coverage differs")
    expected = set(approved["code_pins"]) | PACKAGING
    if set(family["code_pins"]) != expected:
        raise ValueError("The packaging code-pin set differs")
    for name, digest in family["code_pins"].items():
        if name not in PACKAGING and digest != approved["code_pins"][name]:
            raise ValueError("A reviewed non-packaging source changed: " + name)
    entrypoint = family["assets"]["worker_entrypoint"]
    worker_path = str(C.LOGICAL_ROOT / "orchard_native/native_worker.py")
    if entrypoint != dict(path=worker_path, sha256=family["code_pins"][worker_path]):
        raise ValueError("The runtime entrypoint must equal the current code pin")
    if (contract["mask_cache"].get("path") != G.MASK_PATH or
            contract["mask_cache"].get("sha256") != family["code_pins"].get(G.MASK_PATH)):
        raise ValueError("The worker contract must bind its shipped mask receipt")
    for key in baseline["assets"]:
        if key not in ("small_objects", "worker_entrypoint") and family["assets"][key] != baseline["assets"][key]:
            raise ValueError("A non-code native asset changed: " + key)
    old_parts = {part["role"]: part for part in baseline["assets"]["small_objects"]}
    for part in family["assets"]["small_objects"]:
        if part["role"] != "code" and part != old_parts[part["role"]]:
            raise ValueError("A non-code uploaded object changed")
    return dict(
        baseline=G.P5_FAMILY, approved_code_family=APPROVED,
        runtime_assets_equal={key: True for key in RUNTIME_FIELDS},
        native_bootstrap_equal=True,
        runtime_bootstrap_sha256=family["bootstrap_pins"]["native_bootstrap.py"],
        reviewed_code_checked_against_current_family=True,
        derived_worker_entrypoint=entrypoint, derived_mask_receipt=contract["mask_cache"])


def check_pins(root, family, artifact):
    resolve = lambda path: S.physical(root, path)
    for path, digest in family["code_pins"].items():
        C.checked(dict(path=path, sha256=digest), resolve)
    for name, digest in family["bootstrap_pins"].items():
        S.S.relative(name)
        logical = str(C.LOGICAL_ROOT / name)
        if family["code_pins"].get(logical) != digest:
            raise ValueError("Bootstrap and code pins disagree: " + name)
        C.checked(dict(path=logical, sha256=digest), resolve)
    value = C.load(C.checked(artifact, resolve))
    if type(value.get("step")) is not int:
        raise ValueError("The staged checkpoint metadata has no step")
    for name in ("worker_entrypoint", "sitecustomize"):
        record = family["assets"][name]
        S.B.checked(dict(path=str(resolve(record["path"])), sha256=record["sha256"]))
    return dict(code_pins=len(family["code_pins"]), bootstrap_pins=len(family["bootstrap_pins"]),
                artifact=artifact, step=value["step"], bootstrap_runtime_pins=2)


def metadata_source(artifact, source):
    source = Path(source)
    if (not source.is_absolute() or source.is_symlink() or not source.is_file()
            or not source.resolve().is_relative_to(LANE) or source.stat().st_size >= 1024**2):
        raise ValueError("The published artifact metadata exceeds its local scope")
    return C.checked(dict(path=str(source), sha256=artifact["sha256"]))


def stage_artifact_metadata(root, artifact, source):
    source = metadata_source(artifact, source)
    target = S.physical(root, artifact["path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        with target.open("xb") as stream:
            stream.write(source.read_bytes())
    C.checked(dict(path=str(target), sha256=artifact["sha256"]))
    return dict(source=C.pin(source), staged=C.pin(target))


def prove(family_path, local_objects, root, artifact, output, artifact_source, packet, upload, pool):
    family_path, root, output = map(Path, (family_path, root, output))
    family = C.load(family_path)
    equality = scope(family)
    identities = objects(family["assets"])
    metadata_source(artifact, artifact_source)
    if set(local_objects) != ROLES:
        raise ValueError("Local object paths do not cover the five sealed roles")
    paths = {name: Path(path) for name, path in local_objects.items()}
    for name, path in paths.items():
        if (not path.is_absolute() or path.is_symlink() or not path.is_file()
                or not path.resolve().is_relative_to(LANE)
                or path.stat().st_size != identities[name]["bytes"]):
            raise ValueError("A local uploaded-object copy differs: " + name)
    if (root.exists() or root.is_symlink() or not root.parent.is_dir()
            or not root.resolve().is_relative_to(LANE) or output.exists()):
        raise ValueError("The local check needs fresh lane-local destinations")
    required = sum(part["bytes"] + part["expanded_bytes"] for part in family["assets"]["small_objects"])
    if shutil.disk_usage(root.parent).free - required < 200 * 1024**3:
        raise ValueError("Local staging would leave less than 200 GiB free")
    root.mkdir(mode=0o700)
    cloud, copied = S.cloud, S.copied

    def local_stream(part, staged_root, assets):
        if part not in family["assets"]["small_objects"] or assets != family["assets"]:
            raise ValueError("The real stager requested an unsealed local object")
        return paths[part["role"]].open("rb")

    def boundary(item, destination):
        if item != family["assets"]["runtime"]:
            raise ValueError("The real stager reached an unexpected external input")
        raise ProductionRuntimeBoundary()

    S.cloud, S.copied = local_stream, boundary
    reached = False
    try:
        S.stage(root, dict(assets=family["assets"]))
    except ProductionRuntimeBoundary:
        reached = True
    finally:
        S.cloud, S.copied = cloud, copied
    staged = C.load(root / "STAGING.json")
    if not reached or set(staged) != {"small_" + name for name in ROLES}:
        raise ValueError("The real five-object staging path did not reach its runtime boundary")
    artifact_metadata = stage_artifact_metadata(root, artifact, artifact_source)
    checks = check_pins(root, family, artifact)
    for name, digest in family["bootstrap_pins"].items():
        source = S.physical(root, str(C.LOGICAL_ROOT / name))
        target = root / "bootstrap" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(source.read_bytes())
        C.checked(dict(path=str(target), sha256=digest))
    graph_path = output.with_name("COMPARISONS_" + output.name)
    graph = G.prove(root, family_path, packet, C.pin(upload), C.pin(pool), graph_path)
    if not graph["inputs_passed"]:
        raise ValueError("The complete comparison graph has an unevaluated or failing input row")
    value = dict(
        schema=SCHEMA, passed=True, synthetic=False, checked_utc=datetime.now(timezone.utc).isoformat(),
        family=C.pin(family_path), helper=C.pin(__file__), staged_root=str(root),
        objects=identities, staged_receipts=C.pin(root / "STAGING.json"),
        staged_archives={name: dict(path=str(root / "archives" / (name + ".tar")),
                                   sha256=part["sha256"])
                         for name, part in identities.items()},
        input_pin_checks=checks, artifact_metadata=artifact_metadata, runtime_equality=equality,
        staging_function="native_stage.stage", pin_function="native_common.checked",
        boundary="Before the unchanged production runtime copy and interpreter",
        production_interpreter_executed=False, gpu_worker_executed=False, network_calls=0,
        comparison_graph=C.pin(graph_path), comparison_helper=C.pin(G.__file__),
        comparison_rows=len(graph["rows"]), pending_real_control_rows=graph["pending_real_control_rows"],
        launch_controls_checked=False,
        full_validate_config_required_after_real_controls=True)
    C.dump(output, value)
    return value


def admit(destination, config, family, files):
    import native_job as J

    destination = Path(destination)
    record_pin = C.load(destination / "LOCAL_INPUT_CHECK.pin.json")
    record = C.load(C.checked(record_pin))
    if (record.get("schema") != SCHEMA or record.get("passed") is not True
            or record.get("synthetic") is not False
            or record.get("family", {}).get("sha256") != config["family"]["sha256"]
            or record.get("helper", {}).get("sha256") != C.sha(__file__)
            or record.get("objects") != objects(family["assets"])
            or record.get("production_interpreter_executed") is not False
            or record.get("gpu_worker_executed") is not False
            or record.get("network_calls") != 0):
        raise ValueError("The native packet lacks its exact-object local input check")
    if record.get("runtime_equality") != scope(family):
        raise ValueError("The runtime equality proof differs")
    graph = G.validate(C.load(C.checked(record["comparison_graph"])), allow_pending=True)
    C.checked(graph["source_manifest"])
    if (record.get("comparison_helper", {}).get("sha256") != C.sha(G.__file__) or
            graph["family"]["sha256"] != config["family"]["sha256"] or graph["inputs_passed"] is not True):
        raise ValueError("The complete comparison graph names different inputs")
    root = Path(record["staged_root"])
    if root.is_symlink() or not root.is_dir() or not root.resolve().is_relative_to(LANE):
        raise ValueError("The checked staged tree is unavailable")
    metadata = record.get("artifact_metadata", {})
    artifact = config["worker"]["artifact"]
    if (metadata.get("source", {}).get("sha256") != artifact["sha256"]
            or metadata.get("staged") != dict(path=str(S.physical(root, artifact["path"])),
                                             sha256=artifact["sha256"])):
        raise ValueError("The published artifact metadata binding differs")
    C.checked(metadata["staged"])
    C.checked(record["staged_receipts"])
    for name in ROLES:
        archive = record["staged_archives"][name]
        if (Path(archive["path"]) != root / "archives" / (name + ".tar")
                or archive["sha256"] != record["objects"][name]["sha256"]):
            raise ValueError("The staged archive binding differs")
        C.checked(archive)
    checks = check_pins(root, family, config["worker"]["artifact"])
    if checks != record["input_pin_checks"] or checks["step"] != config["step"]:
        raise ValueError("The staged checkpoint or pin checks differ")
    for name, data in files.items():
        S.S.relative(name)
        target = root / name
        if target.exists():
            if target.read_bytes() != data:
                raise ValueError("The staged bootstrap bytes differ: " + name)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(data)
    J.early_admission(root, config)
    controls = [config["family"], config["review"], config["authorization"]["orch_order"]]
    present = [S.physical(root, item["path"]).exists() for item in controls]
    if any(present) and not all(present):
        raise ValueError("The staged real controls are incomplete")
    if not any(present):
        J.controls(root, config)
    C.validate_config(config, resolve=lambda path: S.physical(root, path))
    graph_path = destination / "PRE_SUBMIT_PIN_GRAPH.json"
    actual_graph = G.prove(root, destination / "FAMILY.json", destination,
                           graph["upload"], graph["pool_snapshot"], graph_path)
    G.validate(actual_graph)
    result = dict(schema="evalx-native-pre-submit-input-check-v1", passed=True,
                  plan_sha256=config["plan_sha256"], family_sha256=config["family"]["sha256"],
                  local_check=record_pin, helper=C.pin(__file__),
                  real_early_admission_passed=True, real_validate_config_passed=True,
                  comparison_graph=C.pin(graph_path), comparison_rows=len(G.ROWS),
                  no_queue_or_submission_calls=True)
    target = destination / "PRE_SUBMIT_INPUT_CHECK.json"
    if target.exists():
        if C.load(target) != result:
            raise ValueError("A prior pre-submit check names different inputs")
    else:
        C.dump(target, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("family", "objects", "root", "artifact", "artifact-pin", "output",
                 "packet", "upload", "pool"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    result = prove(args.family, C.load(args.objects), args.root, C.load(args.artifact_pin),
                   args.output, args.artifact, args.packet, args.upload, args.pool)
    print("local_input_check=PASS")
    print("objects=" + str(len(result["objects"])))
    print("code_pins=" + str(result["input_pin_checks"]["code_pins"]))
