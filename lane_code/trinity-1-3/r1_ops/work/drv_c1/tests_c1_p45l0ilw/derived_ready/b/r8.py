"""Print u when the run directory holds a parseable complete.json under a checkpoint, else t (jt8's mode chooser)."""
import argparse
import sys
import datetime
import json
import hashlib
import os
from pathlib import Path
import re
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))


def complete(path, binding):
    try:
        value = json.loads(path.read_text())
        world = binding["world_size"]
        if (value.get("schema") != "c1-checkpoint-v1" or value.get("binding") != binding
                or type(world) is not int or world < 1
                or type(value.get("step")) is not int or value["step"] < 1):
            return False
        required = {"replicated.pt"} | {f"rng{rank:03d}.pt" for rank in range(world)} | {
            f"shards/rank{rank:03d}.pt" for rank in range(world)}
        if not required <= set(value["files"]):
            return False
        for name, pin in value["files"].items():
            relative = Path(name)
            target = path.parent / relative
            if (relative.is_absolute() or ".." in relative.parts or target.is_symlink()
                    or not target.resolve().is_relative_to(path.parent.resolve())
                    or type(pin.get("bytes")) is not int or pin["bytes"] < 1
                    or not re.fullmatch("[0-9a-f]{64}", pin.get("sha256", ""))
                    or target.stat().st_size != pin["bytes"]):
                return False
            hashed = hashlib.sha256()
            with target.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024*1024), b""):
                    hashed.update(chunk)
            if hashed.hexdigest() != pin["sha256"]:
                return False
        return True
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return False


def checksum(path):
    if path.is_symlink():
        raise ValueError("Persistent evidence must not be a symlink")
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024*1024), b""):
            value.update(chunk)
    return value.hexdigest()


def recorded_checksum(path, filename):
    if path.is_symlink():
        raise ValueError("Persistent digest must not be a symlink")
    fields = path.read_text().split()
    if (len(fields) not in (1, 2) or not re.fullmatch("[0-9a-f]{64}", fields[0])
            or (len(fields) == 2 and Path(fields[1].lstrip("*")).name != filename)):
        raise ValueError("Persistent digest format differs")
    return fields[0]


def persistent_check(root, directory, job, mode, binding, step):
    persistent = Path(directory)
    job = str(job) if job is not None else ""
    if (not persistent.is_absolute() or ".." in persistent.parts or persistent.is_symlink()
            or persistent.resolve().is_relative_to(root.resolve())
            or not re.fullmatch("[1-9][0-9]*", job)):
        raise ValueError("Persistent location or Slurm job identity is invalid")
    persistent.mkdir(parents=True, exist_ok=True)
    marker = persistent / "RUN.json"
    history = [persistent / name for name in ("binding.json", "binding.json.sha256")]
    history += [persistent / f"{slot}.{suffix}" for slot in ("A", "B") for suffix in ("tar", "sha256", "json")]
    if not marker.exists():
        if any(path.exists() or path.is_symlink() for path in history) or mode != "t":
            raise ValueError("Unmarked persistent history; refusing a cold restart")
        value = dict(run=root.name, first_job=job,
                     started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        temporary = persistent / ("RUN."+uuid.uuid4().hex+".json")
        with temporary.open("x") as handle:
            json.dump(value, handle, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, marker)
        except FileExistsError:
            pass
    if marker.is_symlink():
        raise ValueError("Persistent run marker must not be a symlink")
    recorded = json.loads(marker.read_text())
    first_job = str(recorded.get("first_job", ""))
    if (recorded.get("run") != root.name or not re.fullmatch("[1-9][0-9]*", first_job)
            or not isinstance(recorded.get("started_utc"), str) or not recorded["started_utc"]):
        raise ValueError("Persistent marker identifies another run or has incomplete identity")
    previous = first_job != job
    slot_history = any(path.exists() or path.is_symlink() for path in history[2:])
    if mode == "t":
        if previous or slot_history:
            raise ValueError("An earlier run leg or state slot exists; refusing a cold restart")
        return
    steps = []
    for slot in ("A", "B"):
        index = persistent / f"{slot}.json"
        if not index.exists():
            continue
        if index.is_symlink():
            raise ValueError("Persistent slot index must not be a symlink")
        value = json.loads(index.read_text())
        if value.get("verified") is False:
            continue
        archive = persistent / f"{slot}.tar"
        if (value.get("verified") is not True or value.get("slot") != slot
                or type(value.get("step")) is not int or value["step"] < 1
                or type(value.get("bytes")) is not int or value["bytes"] < 1
                or archive.is_symlink() or archive.stat().st_size != value["bytes"]):
            raise ValueError("Persistent verified-slot attestation differs")
        recorded_checksum(persistent / f"{slot}.sha256", slot+".tar")
        steps.append(value["step"])
    mirror = persistent / "binding.json"
    if previous and (not steps or not mirror.is_file()):
        raise ValueError("A later job requires a verified slot and binding mirror")
    if mirror.exists():
        expected = recorded_checksum(persistent / "binding.json.sha256", "binding.json")
        if (checksum(mirror) != expected or checksum(root / "binding.json") != expected
                or json.loads(mirror.read_text()) != binding):
            raise ValueError("Restored checkpoint and persistent binding differ")
    if steps and step < max(steps):
        raise ValueError("Restored checkpoint is older than the newest verified slot")


def main(directory, persistent=None, job=None):
    root = Path(directory)
    if root.is_symlink():
        raise ValueError("Run directory must not be a symlink")
    checkpoints = list(root.glob("checkpoint_*"))
    binding, step, mode = None, 0, "t"
    if checkpoints:
        binding = json.loads((root / "binding.json").read_text())
        states = [path / "complete.json" for path in checkpoints
                  if path.is_dir() and not path.is_symlink() and complete(path / "complete.json", binding)]
        if not states:
            raise ValueError("No structurally complete matching checkpoint; refusing a cold restart over retained state")
        step = max(json.loads(path.read_text())["step"] for path in states)
        mode = "u"
    if not checkpoints and (root/'d/0.json').exists():
        from c0 import verify, load as c_load
        kit=Path(os.environ['TK_KIT_HOME'])
        verify(root/'d',c_load(kit/'k/a0.json'))
        if persistent is not None:persistent_check(root,persistent,job,'t',None,0)
        return 'u'
    if persistent is not None:
        persistent_check(root, persistent, job, mode, binding, step)
    return mode


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory")
    parser.add_argument("--kit")
    args = parser.parse_args()
    persistent = None
    if args.kit:
        launch = json.loads((Path(args.kit) / "k/launch.json").read_text())
        persistent = launch.get("persistent_run_root")
        if (not isinstance(persistent, str) or not persistent
                or Path(launch["run_directory"]).resolve() != Path(args.directory).resolve()):
            raise ValueError("Kit run or persistent location differs")
    print(main(args.directory, persistent, os.environ.get("SLURM_JOB_ID")))
