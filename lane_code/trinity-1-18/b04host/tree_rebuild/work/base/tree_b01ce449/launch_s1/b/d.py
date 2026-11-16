import copy
import hashlib
import json
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def config_identity(cfg):
    from i import identity
    return identity(cfg)


def contract(launch, cfg):
    value = launch.get("in_job_admission")
    coverage = cfg.get("scene_coverage", {})
    reference = coverage.get("reference", {})
    if (not isinstance(value, dict) or value.get("schema") != "s1-in-job-admission-v1"
            or cfg.get("first_step_admission") != "all_rank_native_v1"
            or cfg.get("s1_routing", {}).get("schema") != "s1-routing-inputs-v1"
            or coverage.get("schema") != "s1-scene-coverage-v1" or not coverage.get("source_map")
            or not isinstance(reference.get("sha256"), str) or len(reference["sha256"]) != 64
            or set(reference["sha256"])-set("0123456789abcdef") or reference["sha256"] == "0"*64
            or not isinstance(reference.get("path"), str) or not Path(reference["path"]).is_absolute()
            or value.get("directory") != str(Path(cfg["output"]) / "inputs")
            or value.get("parent_grounding_required") is not True
            or value.get("gpu_first_step_required") is not True
            or not isinstance(value.get("frame_roots"), list) or not value["frame_roots"]
            or any(not Path(root).is_absolute() or ".." in Path(root).parts for root in value["frame_roots"])):
        raise ValueError("In-job admission needs its exact directory, frame roots and first-step contract")
    return value


def effective(root, cfg, launch=None):
    root = Path(root)
    launch = launch or json.loads((root / "k/launch.json").read_text())
    value = contract(launch, cfg)
    has_mdg = "mdg" in cfg["streams"]
    if has_mdg != ("mdg" in cfg):
        raise ValueError("MDG stream and configuration presence differ")
    logical = Path(value["directory"])
    namespace = root == Path(cfg["output"]).parent.parent
    physical = logical if namespace else Path(launch["run_directory"]) / "inputs"

    def local(path):
        path = Path(path)
        if not path.is_absolute() or ".." in path.parts or not path.is_relative_to(logical):
            raise ValueError("Derived admission file is outside this run")
        target = physical / path.relative_to(logical)
        if target.is_symlink() or not target.resolve().is_relative_to(physical.resolve()):
            raise ValueError("Derived admission file escaped its run")
        return target

    def read(pin):
        if not isinstance(pin, dict) or set(pin) != {"path", "sha256"}:
            raise ValueError("Derived admission pin is incomplete")
        path = local(pin["path"])
        if hashlib.sha256(path.read_bytes()).hexdigest() != pin["sha256"]:
            raise ValueError("Derived admission bytes changed")
        return json.loads(path.read_text())

    data = json.loads((physical / "data_receipt.json").read_text())
    if (data.get("schema") != "s1-in-job-data-v1" or data.get("status") != "PREPARED"
            or data.get("production_authorized") is not False or data.get("rehearsal") is not False
            or data.get("real_frames_verified") is not True or data.get("gpu_first_step_pending") is not True
            or data.get("source_revision") != launch["source_revision"]
            or data.get("input_config", {}).get("sha256") != launch["config"]["sha256"]
            or data.get("world_size") != cfg["world_size"] or data.get("input_streams") != cfg["streams"]):
        raise ValueError("In-job data receipt is incomplete, foreign or a rehearsal")
    derived = read(data["config"])
    expected = copy.deepcopy(cfg)
    expected["streams"]["pointing"] = derived["streams"]["pointing"]
    expected["streams"]["routing"] = derived["streams"]["routing"]
    expected["streams"]["vqa"] = derived["streams"]["vqa"]
    if has_mdg:
        expected["mdg"]["confusers"] = derived["mdg"]["confusers"]
    expected["preparation"] = data["preparation"]
    expected["preparation_output"] = str(Path(data["preparation"]["path"]).parent)
    expected.pop("admission", None)
    if derived != expected:
        raise ValueError("In-job admission changed an unreviewed training setting")
    local_streams = [derived["streams"]["pointing"]]
    if derived["streams"]["vqa"] != cfg["streams"]["vqa"]:
        vqa = read(derived["streams"]["vqa"])
        if (vqa.get("schema") != "c1-stream-v1" or vqa.get("stream") != "vqa"
                or vqa.get("source") != cfg["streams"]["vqa"]
                or vqa.get("source_receipt") != cfg["streams"]["vqa"]):
            raise ValueError("Rebuilt VQA is not bound to the reviewed source receipt")
    if has_mdg:
        local_streams.append(derived["mdg"]["confusers"])
    for pin in local_streams:
        read(pin)
    routed = read(derived["streams"]["routing"])
    materialized = read(data["routing_materialization"])
    if (routed.get("materialization") != data["routing_materialization"]
            or materialized.get("schema") != "s1-routing-materialization-v1"
            or materialized.get("status") != "PASS" or materialized.get("inputs") != cfg["s1_routing"]
            or materialized.get("legacy") != cfg["streams"]["routing"]):
        raise ValueError("Routing materialization is not bound to the reviewed sources")
    preparation = read(data["preparation"])
    scenes = preparation.get("scene_filter_report", {})
    coverage = scenes.get("coverage", {})
    if (data.get("scene_exclusions") != scenes or coverage.get("schema") != "s1-scene-coverage-result-v1"
            or coverage.get("status") != "PASS" or coverage.get("policy") != cfg["scene_coverage"]
            or not coverage.get("sources")):
        raise ValueError("In-job scene exclusion coverage is missing or unbound")
    seal = data["source_seal"]
    sealed = dict(schema="s1-run-seal-v1", tree_sha256=launch["source_seal"]["tree_sha256"],
                  config_sha256=config_identity(derived), archive=launch["source_seal"]["archive"])
    if (seal != {**sealed, "sha256": digest(sealed)} or preparation.get("source_seal") != seal
            or preparation.get("config_sha256") != config_identity(derived)
            or data["source_counts"] != {key: stream["count"] for key, stream in preparation["streams"].items()}
            or any(type(count) is not int or count < 1 for count in data["source_counts"].values())):
        raise ValueError("Derived configuration, preparation or source counts differ")
    frames = read(data["frames"])
    if frames.get("all_retained_frames_exist") is not True or not frames.get("sources"):
        raise ValueError("In-job frame admission is incomplete")
    parent = read(data["parent_grounding"])
    parent_scoped = (
        parent.get("confusers") == derived["mdg"]["confusers"]
        and parent.get("exact_key_shape_coverage") is True
        and parent.get("method") == "rebuild-from-parent-input-embedding-rows"
    ) if has_mdg else (
        data.get("mdg") == "absent" and preparation.get("stream_status", {}).get("mdg") == "absent"
        and parent.get("mdg") == "absent" and parent.get("method") == "verify-parent-metadata-without-mdg"
        and parent.get("parent_base_identity") == cfg["base_identity"]
        and parent.get("parent_weight_payloads_verified") is False
        and parent.get("full_parent_model_loaded") is False)
    if (parent.get("schema") != "s1-parent-grounding-v1" or parent.get("status") != "PASS"
            or parent.get("parent_artifact") != cfg["init_artifact"]["artifact"]
            or not parent_scoped):
        raise ValueError("MDG init and confusers are not bound to this parent" if has_mdg
                         else "No-MDG parent metadata proof is not explicitly scoped to this parent")
    return derived
