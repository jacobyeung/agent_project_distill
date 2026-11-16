import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from i import identity
from v import sha


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def read_pin(root, pin):
    if not isinstance(pin, dict) or set(pin) != {"file", "sha256"}:
        raise ValueError("Missing local launch evidence pin")
    relative = Path(pin["file"])
    path = root / relative
    if (relative.is_absolute() or ".." in relative.parts or path.is_symlink()
            or not path.resolve().is_relative_to(root.resolve())
            or not re.fullmatch("[0-9a-f]{64}", pin["sha256"])
            or sha(path) != pin["sha256"]):
        raise ValueError("Launch evidence differs")
    return json.loads(path.read_text())


def persistent_launch(launch, cfg, environment, mode):
    persistent = launch.get("persistent_run_root")
    if cfg["world_size"] == 4 or persistent is not None:
        if not isinstance(persistent, str) or not persistent:
            raise ValueError("Persistent run location is missing")
        from r8 import main as choose
        selected = choose(launch["run_directory"], persistent, environment.get("SLURM_JOB_ID"))
        if (mode in ("t", "u", "x") and selected != ("u" if mode == "x" else mode)):
            raise ValueError("Requested entry differs from the verified persistent resume mode")
    return launch


def check(root, environment=None, mode="t"):
    root = Path(root)
    environment = os.environ if environment is None else environment
    launch = json.loads((root / "k/launch.json").read_text())
    if launch.get("schema") != "s1-orchard-launch-v1":
        raise ValueError("Launch contract differs")
    switch = launch.get("rehearsal_environment")
    if not isinstance(switch, str) or not switch or environment.get(switch, "0") != "0":
        raise ValueError("Production entry refuses CPU rehearsal mode")
    preparation_only = mode == "p" and launch.get("status") == "PREPARATION_ONLY"
    if not preparation_only and (launch.get("status") != "READY" or launch.get("production_authorized") is not True):
        raise ValueError("Launch is blocked pending staged inputs, first batch, independent review and authorization")
    cfg = read_pin(root, launch["config"])
    cur = json.loads((root / "k/0.json").read_text())
    commit = cur["commit"]
    if (not isinstance(commit, str) or not re.fullmatch("(?:[0-9a-f]{40}|sha256:[0-9a-f]{64})", commit)
            or launch["source_revision"] != commit
            or cfg.get("world_size") not in (4, 8) or cfg["recipe"].get("world_size") != cfg["world_size"]
            or cfg["recipe"].get("wall_seconds") != 86400
            or cfg["recipe"].get("stop_before_seconds") != (3600 if cfg["world_size"] == 4 else 900)
            or cfg.get("trace_program_version") != "3.14" or cfg.get("tool_mode_flag") is not None):
        raise ValueError("Launch source, slot resources or unflagged version contract differs")
    run = Path(launch["run_directory"])
    if not run.is_absolute() or ".." in run.parts or not run.is_relative_to("/tmp/jjyeung"):
        raise ValueError("Run output must remain in node-local temporary storage")
    code = json.loads((root / "k/7.json").read_text())
    sealed = code.get("schema") == "c1-sealed-source-v1"
    if ((not sealed and code.get("clean") is not True) or code.get("commit") != commit
            or cfg.get("code", {}).get("sha256") != sha(root / "k/7.json")):
        raise ValueError("Source seal differs")
    if sealed:
        value = dict(schema="s1-run-seal-v1", tree_sha256=code["tree_sha256"],
                     config_sha256=identity(cfg), archive=code["archive"])
        record = json.loads((root / "k" / Path(cur["record"]["file"]).name).read_text())
        if (commit != "sha256:"+digest(code["files"]) or code["tree_sha256"] != commit[7:]
                or record["trees"]["trainer"]["files"] != code["files"]
                or code["archive"]["sha256"] != cur["trainer"]["sha256"]
                or launch.get("source_seal") != {**value, "sha256": digest(value)}):
            raise ValueError("Tree/configuration/archive binding differs")
    auth = json.loads((root / "k/4.json").read_text())
    expiry = datetime.datetime.fromisoformat(auth["allow_until_utc"].replace("Z", "+00:00"))
    if (expiry.tzinfo is None or expiry < datetime.datetime(2026, 11, 22, tzinfo=datetime.timezone.utc)
            or expiry <= datetime.datetime.now(datetime.timezone.utc) or auth.get("source_revision") != commit
            or mode not in auth.get("modes", [])):
        raise ValueError("Written slot authorization is absent or expires too early")
    if preparation_only:
        return persistent_launch(launch, cfg, environment, mode)
    if sealed:
        archived = read_pin(root, launch["archive"])
        if (archived.get("status") != "ARCHIVED" or archived.get("durable") is not True
                or archived.get("sha256") != code["archive"]["sha256"]
                or archived.get("tree_sha256") != code["tree_sha256"]
                or not isinstance(archived.get("location"), str) or not archived["location"]
                or archived["location"].startswith(("/scratch/", "/tmp/"))):
            raise ValueError("Off-scratch source archive is not attested")
    review = read_pin(root, launch["review"])
    config_sha = identity(cfg)
    if (review.get("verdict") != "PASS" or not review.get("reviewer")
            or review.get("config_sha256") != config_sha
            or cfg.get("admission", {}).get("sha256") != launch["review"]["sha256"]):
        raise ValueError("Independent admission is not bound to the launch configuration")
    if launch.get("in_job_admission"):
        from d import contract, effective
        admission = contract(launch, cfg)
        if (review.get("admission_contract_sha256") != digest(admission)
                or review.get("admission_scope") != "pinned-template-and-native-data-derivation"):
            raise ValueError("Independent review does not cover the in-job derivation")
        staged = read_pin(root, launch["staging"])
        if (staged.get("status") != "PASS" or staged.get("source_revision") != commit
                or staged.get("config_sha256") != config_sha or staged.get("missing") != []
                or staged.get("project_community_write_bytes") != 0):
            raise ValueError("Read-only cache staging is not verified")
        if mode != "p":
            effective(root, cfg, launch)
        return persistent_launch(launch, cfg, environment, mode)
    if review.get("preparation") != cfg.get("preparation"):
        raise ValueError("Independent admission is not bound to the preparation")
    batch = read_pin(root, launch["first_batch"])
    if (batch.get("schema") != "s1-first-batch-binding-v1" or batch.get("config_sha256") != config_sha
            or batch.get("source_revision") != commit
            or batch.get("preparation") != cfg.get("preparation") or batch.get("streams") != cfg.get("streams")
            or batch.get("real_rgb_verified") is not True or batch.get("native_full_forward") is not True):
        raise ValueError("First-batch input binding differs or uses fixture RGB")
    report = read_pin(root, batch["report"])
    world = cfg["world_size"]
    expected = {(rank, stream) for rank in range(world) for stream in set(cfg["recipe"]["mix"])}
    actual = {(record.get("rank"), record.get("stream")) for record in report.get("records", [])}
    if (report.get("schema") != "c1-first-batch-check-v1" or report.get("ranks") != list(range(world))
            or report.get("device") != "cpu" or not expected <= actual
            or any(record.get("finite") is not True for record in report.get("records", []))):
        raise ValueError("Every rank and stream needs a finite native CPU first batch")
    staged = read_pin(root, launch["staging"])
    if (staged.get("status") != "PASS" or staged.get("source_revision") != commit
            or staged.get("config_sha256") != config_sha or staged.get("missing") != []
            or staged.get("project_community_write_bytes") != 0):
        raise ValueError("Read-only cache staging is not verified")
    return persistent_launch(launch, cfg, environment, mode)


if __name__ == "__main__":
    check(sys.argv[1], mode=sys.argv[2] if len(sys.argv) > 2 else "t")
