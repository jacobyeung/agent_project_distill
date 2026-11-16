import hashlib
import json
from pathlib import Path
import re


SCHEMA = "evalx-orchard-native-config-v1"
ROOT = Path(__file__).resolve().parent.parent
LOGICAL_ROOT = Path("/scratch/jjyeung/orch_cd/evalx/work/milestone")
WORKER_FIELDS = {"inputs", "expected_keys", "pilot_selection", "config", "data_receipt",
                 "raw_tower", "mask_cache", "adapter_pins", "kernel_source_pins", "frames_root",
                 "geometry_captures"}


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024**2), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pin(path):
    path = Path(path)
    return dict(path=str(path), sha256=sha(path))


def checked(record, resolve=None):
    path = Path(record["path"])
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("Native input path is not canonical")
    path = path if resolve is None else Path(resolve(path))
    if (path.is_symlink()
            or not path.is_file() or sha(path) != record["sha256"]):
        raise ValueError("Native input pin differs: "+str(path))
    return path


def load(path):
    path = Path(path)
    if path.stat().st_size > 16*1024**2:
        raise ValueError("Native control metadata exceeds its limit")
    return json.loads(path.read_text())


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def plan(config):
    return canonical({key: value for key, value in config.items() if key != "plan_sha256"})


def order_line(config):
    return "LAUNCH EVALX NATIVE "+" ".join(str(config[key]) for key in
        ("mode", "step", "partition", "token"))+" "+config["family"]["sha256"]+" "+config["worker"]["artifact"]["sha256"]


def validate_order(text, config):
    if text.splitlines().count(order_line(config)) != 1:
        raise ValueError("Require exactly one ORCH launch line for this native packet")


def admit(config, family, review):
    validate_config(config, launch=False)
    if config.get("build_only") is not False:
        raise ValueError("A build-only native packet cannot run")
    if (family.get("schema") != "evalx-orchard-native-family-v1"
            or family.get("synthetic") is not False
            or family.get("modes") != ["pilot", "full"]
            or family.get("partitions") != ["general", "advanced"]
            or config["assets"] != family["assets"]
            or config["limits"] != family["limits"][config["mode"]]):
        raise ValueError("Native assets, limits or scope differ from the family seal")
    if (review.get("verdict") != "ACCEPT" or not review.get("reviewer")
            or review.get("synthetic") is not False
            or review.get("family_sha256") != config["family"]["sha256"]):
        raise ValueError("The native family lacks its scoped admission")
    authority = config.get("authorization", {})
    expected = dict(issuer="ORCH", site="orchard", mode=config["mode"], token=config["token"],
                    partition=config["partition"], step=config["step"], gpus=1,
                    artifact_sha256=config["worker"]["artifact"]["sha256"],
                    family_sha256=config["family"]["sha256"])
    if any(authority.get(key) != value for key, value in expected.items()):
        raise ValueError("The native launch order does not bind this packet and export")
    contract = family.get("worker_contract", {})
    if set(contract) != WORKER_FIELDS or any(config["worker"].get(k) != v for k, v in contract.items()):
        raise ValueError("The native worker differs from its reviewed input contract")
    if (config["logical_run"] != str(LOGICAL_ROOT/"runs"/config["token"])
            or config.get("plan_sha256") != plan(config)
            or config["transport"].get("artifact_sha256") != config["worker"]["artifact"]["sha256"]
            or config["transport"].get("step") != config["step"]):
        raise ValueError("Native run, transport or plan identity differs")
    if config["mode"] == "full":
        import native_metrics as M
        M.validate(config.get("full_projection"), config["family"]["sha256"])
        report = config["full_projection"]["report"]
        if (report["selection"] != config["worker"]["pilot_selection"]
                or any(row["native"] not in config["worker"]["geometry_captures"]
                       for row in report["geometry"])):
            raise ValueError("The passed pilot used a different sealed selection or geometry cohort")
    return config


def validate_config(config, launch=True, resolve=None):
    if (config.get("schema") != SCHEMA or config.get("synthetic") is not False
            or config.get("mode") not in ("pilot", "full")
            or config.get("partition") not in ("general", "advanced")
            or type(config.get("step")) is not int or config["step"] < 1
            or not re.fullmatch("[a-z][0-9a-f]{8,32}", config.get("token", ""))):
        raise ValueError("Native mode, partition, step or identity differs")
    if config.get("gpus") != 1 or type(config["gpus"]) is not int:
        raise ValueError("The native family requires exactly one GPU")
    if launch:
        family = load(checked(config["family"], resolve))
        review = load(checked(config["review"], resolve))
        admit(config, family, review)
        order = checked(config["authorization"]["orch_order"], resolve)
        validate_order(order.read_text(), config)
        for path, expected_sha in family["code_pins"].items():
            checked(dict(path=path, sha256=expected_sha), resolve)
        artifact = load(checked(config["worker"]["artifact"], resolve))
        if artifact.get("step") != config["step"]:
            raise ValueError("Native checkpoint step differs from its bound packet")
    return config
