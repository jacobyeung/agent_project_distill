import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(os.environ.get("GEO_BAKEOFF_ROOT", Path(__file__).resolve().parents[3])).resolve()
ASSETS = Path(os.environ.get("GEO_BAKEOFF_ASSETS", ROOT / "assets")).resolve()
OUTPUT_ROOT = Path(os.environ.get("GEO_BAKEOFF_OUTPUT_ROOT", ROOT / "out")).resolve()
FREE_FLOOR = 100 * 1024 ** 3
LANE_LIMIT = 5_000_000_000
ASSET_LIMIT = 40_000_000_000


def utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def json_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def local_output(path, roots=None):
    roots = (ROOT, OUTPUT_ROOT) if roots is None else roots
    path = Path(path)
    resolved = path.resolve()
    if not any(resolved.is_relative_to(p.resolve()) for p in roots):
        raise ValueError(f"Output is outside the permitted roots: {path}")
    return path


def check_space(required=0):
    result = subprocess.run(["df", "-B1", "--output=avail", "/scratch"], check=True, capture_output=True, text=True)
    free = int(result.stdout.splitlines()[-1].strip())
    if free - required < FREE_FLOOR:
        raise RuntimeError(f"Disk floor: {free} bytes free, {required} requested, {FREE_FLOOR} reserved")
    return free


def footprint(path, exclude=()):
    excluded = {Path(p).resolve() for p in exclude}
    total, seen = 0, set()
    for root, dirs, files in os.walk(path, followlinks=False):
        dirs[:] = [d for d in dirs if not Path(root, d).is_symlink() and Path(root, d).resolve() not in excluded]
        for filename in files:
            item = Path(root, filename)
            if item.is_symlink():
                continue
            stat = item.stat()
            identity = (stat.st_dev, stat.st_ino)
            if identity not in seen:
                seen.add(identity)
                total += stat.st_size
    return total


def lane_footprint():
    data = Path(os.environ.get("GEO_BAKEOFF_DATA_ROOT", ROOT / "data"))
    return footprint(ROOT, exclude=(ASSETS, ROOT / "runtime", data))


def check_lane_budget(path, required=0):
    increment = required if Path(path).resolve().is_relative_to(ROOT) else 0
    if lane_footprint() + increment > LANE_LIMIT:
        raise RuntimeError("The kit/lane's 5 GB budget would be exceeded")


def dump_json(path, value, replace=False):
    path = local_output(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if replace:
        temp = path.with_name(path.name + f".{os.getpid()}.tmp")
        with temp.open("x") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    else:
        with path.open("x") as f:
            f.write(text)


def progress(path, **state):
    dump_json(path, {"updated_at": utc(), **state}, replace=True)
