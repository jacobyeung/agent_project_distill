"""Opt-in, byte-preserving admission cache. No training or authorization shortcuts.

The complete configuration (including logical paths) is deliberately in the key.
Production maps each logical run to one node-local path, so this cannot avoid a
native rebuild there. Keep the switch OFF. Never rewrite a native run seal.
"""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import sys
import time
import uuid


SCHEMA = "s1-prepared-input-cache-v1"
AS = "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung"
AL = "/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung"
X = AS + "/ap/8865619b"
ENVIRONMENT = ("S1_CPU_REHEARSAL", "SLURM_CPUS_PER_TASK", "PYTHONHASHSEED")
# tk_env overwrites R1_MOUNT, R1_STUDENT_HEX, frame mappings and CPU settings.
# Their effective values belong to the hashed wrapper implementation. Ambient
# values before tk_env must not distinguish restore from publication after it.


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def regular(path):
    path = Path(path)
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("cache path contains a symlink: " + str(path))
    value = path.stat()
    if not stat.S_ISREG(value.st_mode):
        raise ValueError("cache payload is not a regular file: " + str(path))
    return value


def signature(value):
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def sha(path):
    before = regular(path)
    result = hashlib.sha256()
    with Path(path).open("rb") as source:
        if signature(os.fstat(source.fileno())) != signature(before):
            raise ValueError("cache file changed before hashing")
        for block in iter(lambda: source.read(8 << 20), b""):
            result.update(block)
        if signature(os.fstat(source.fileno())) != signature(before):
            raise ValueError("cache file changed while hashing")
    if signature(regular(path)) != signature(before):
        raise ValueError("cache file changed after hashing")
    return result.hexdigest()


def inside(root, relative):
    root, relative = Path(root), Path(relative)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ValueError("unsafe cache relative path")
    target = root / relative
    if any(p.is_symlink() for p in (target, *target.parents)):
        raise ValueError("cache path contains a symlink")
    return target


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex)
    with temporary.open("xb") as stream:
        stream.write(encoded(value) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


@contextmanager
def locked(root, key):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    lock = inside(root, key + ".lock")
    with lock.open("a+b") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def key_components(cfg, current, contract, implementation, environment, input_config=None):
    frames = {k: v for k, v in current.items() if re.fullmatch(r"f[0-9]+_manifest", k)}
    if not frames or not cfg.get("streams"):
        raise ValueError("cache requires store receipts and frame manifests")
    if any(not isinstance(pin, dict) or not isinstance(pin.get("path"), str)
           or not re.fullmatch("[0-9a-f]{64}", pin.get("sha256", ""))
           for pin in cfg.get("remove_files", [])):
        raise ValueError("cache requires content-pinned REMOVE lists")
    # Native MDG also accepts path-only inputs and computes fresh pins while
    # preparing. Those variants cannot safely reuse a key formed from config.
    # Decline caching and let the unchanged native path compute their contents.
    def content_pin(value):
        return (isinstance(value, dict) and set(value) == {"path", "sha256"}
                and isinstance(value.get("path"), str) and Path(value["path"]).is_absolute()
                and ".." not in Path(value["path"]).parts
                and isinstance(value.get("sha256"), str)
                and re.fullmatch("[0-9a-f]{64}", value["sha256"]) is not None)
    if "mdg" in cfg:
        mdg = cfg["mdg"]
        if not isinstance(mdg, dict):
            raise ValueError("cache requires content-pinned MDG inputs")
        for name in ("clips_jsonl", "confusers", "vocab", "stem_weights"):
            if not content_pin(mdg.get(name)):
                raise ValueError("cache requires content-pinned MDG " + name)
        for name in ("frame_root", "rasters"):
            value = mdg.get(name)
            if (not isinstance(value, dict) or set(value) != {"root", "manifest"}
                    or not isinstance(value["root"], str) or not Path(value["root"]).is_absolute()
                    or ".." in Path(value["root"]).parts or not content_pin(value["manifest"])):
                raise ValueError("cache requires content-pinned MDG " + name)
        excluded = mdg.get("exclude_scenes")
        if not (isinstance(excluded, list) and all(isinstance(name, str) for name in excluded)
                or content_pin(excluded)):
            raise ValueError("cache requires content-pinned MDG exclude_scenes")
        if "init_artifact" in mdg:
            value = mdg["init_artifact"]
            if (not isinstance(value, dict) or not {"mdg.json", "mdg.pt"} <= set(value)
                    or set(value) - {"mdg.json", "mdg.pt", "lora.pt"}
                    or not all(content_pin(pin) for pin in value.values())):
                raise ValueError("cache requires content-pinned MDG init_artifact")
    components = dict(schema=SCHEMA, input_config=input_config,
                store_receipts=cfg["streams"], preparation_config=cfg,
                frame_manifests=frames, preparation_code_identity=dict(
                    commit=current["commit"], trainer=current["trainer"], code=cfg["code"],
                    wrapper=implementation), staging=current, admission_contract=contract,
                environment={name: environment.get(name) for name in ENVIRONMENT})
    # Keep the components independent, including when callers mutate one in a test.
    return json.loads(encoded(components))


class Context:
    def __init__(self, kit, node, cache, job):
        self.kit, self.node, self.cache = map(lambda p: Path(p).absolute(), (kit, node, cache))
        if any(p.is_symlink() for root in (self.kit, self.node, self.cache) for p in (root, *root.parents)):
            raise ValueError("cache roots must not contain symlinks")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", str(job)):
            raise ValueError("invalid cache job identity")
        self.job = str(job)
        self.current, self.launch = read(self.kit / "k/0.json"), read(self.kit / "k/launch.json")
        pin = self.launch["config"]
        config = inside(self.kit, pin["file"])
        if sha(config) != pin["sha256"]:
            raise ValueError("cache configuration pin differs")
        self.cfg = read(config)
        self.contract = self.launch["in_job_admission"]
        self.logical = Path(self.contract["directory"])
        if (self.contract.get("schema") != "s1-in-job-admission-v1"
                or self.logical != Path(self.cfg["output"]) / "inputs"
                or not self.logical.is_absolute() or ".." in self.logical.parts):
            raise ValueError("cache admission directory differs")
        self.destination = Path(self.launch["run_directory"]).absolute() / "inputs"
        if any(p.is_symlink() for p in self.destination.parents):
            raise ValueError("cache destination contains a symlink")
        if self.cache == self.destination or self.cache.is_relative_to(self.destination):
            raise ValueError("cache index must be outside the admission directory")
        self.frame_root = self.node / "c7d31ddd/data2root"
        implementation = {str(p.relative_to(self.kit / "b")): sha(p)
                          for p in sorted((self.kit / "b").rglob("*")) if p.is_file()}
        self.components = key_components(self.cfg, self.current, self.contract, implementation, os.environ,
                                         input_config=self.launch["config"])
        self.key = digest(self.components)
        self.report = self.kit / "o" / (self.job + ".prepared-cache.json")

    def host(self, path):
        # Small frame manifests are already staged when c.sh calls restore/seal.
        for prefix, root in ((X + "/", self.node.parent / ("x_" + self.job)), (AS + "/", self.node / "aws/u"),
                             (AL + "/", self.node / "aws/u")):
            if path.startswith(prefix):
                return inside(root, path[len(prefix):])
        return Path(path)

    def result(self, status, **fields):
        value = dict(schema=SCHEMA, job=self.job, status=status, key=self.key,
                     key_components=self.components, target_inputs=str(self.destination),
                     target_frames=str(self.frame_root), recorded_unix=time.time(),
                     production_authorized=False, gpu_first_step_pending=True, **fields)
        atomic(self.report, value)
        return value


def local_name(logical, path):
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("invalid admission pin path")
    return str(path.relative_to(logical))


def pins(value):
    if isinstance(value, dict):
        if "path" in value and "sha256" in value:
            yield value
        for part in value.values():
            yield from pins(part)
    elif isinstance(value, list):
        for part in value:
            yield from pins(part)


def admission_files(ctx, root):
    """Require both complete phases and every local reference, not just surviving files."""
    names = {"request.json", "data_receipt.json"}
    request, data = read(inside(root, "request.json")), read(inside(root, "data_receipt.json"))
    if (data.get("schema") != "s1-in-job-data-v1" or data.get("status") != "PREPARED"
            or data.get("real_frames_verified") is not True or data.get("rehearsal") is not False
            or data.get("gpu_first_step_pending") is not True
            or data.get("input_config", {}).get("sha256") != ctx.launch["config"]["sha256"]
            or data.get("input_streams") != ctx.cfg["streams"]
            or data.get("source_revision") != ctx.current["commit"]
            or request.get("config") != data.get("input_config")
            or request.get("frame_roots") != ctx.contract["frame_roots"]):
        raise ValueError("incomplete or foreign admission data")
    for phase in ("prepare", "frames"):
        name = "phase_" + phase + ".complete.json"
        marker = read(inside(root, name))
        if marker.get("schema") != "s1-admission-phase-v1" or marker.get("binding") != request:
            raise ValueError("incomplete or foreign admission phase")
        payload = marker["payload"]
        relative = local_name(ctx.logical, payload["path"])
        directory = Path(relative).parent
        if len(directory.parts) != 1 or not re.fullmatch(phase + r"_[0-9a-f]{32}", directory.name):
            raise ValueError("admission phase directory differs")
        source = inside(root, relative)
        if sha(source) != payload["sha256"] or not read(source).get("outputs"):
            raise ValueError("admission phase payload differs")
        names.add(name)
        for path in inside(root, str(directory)).rglob("*"):
            if path.is_symlink():
                raise ValueError("admission payload contains a symlink")
            if path.is_file():
                names.add(str(path.relative_to(root)))
    files = {name: dict(sha256=sha(inside(root, name)), bytes=regular(inside(root, name)).st_size)
             for name in sorted(names)}
    for name in names:
        if Path(name).suffix != ".json":
            continue
        for pin in pins(read(inside(root, name))):
            path = Path(pin["path"])
            if path.is_relative_to(ctx.logical):
                relative = local_name(ctx.logical, str(path))
                if relative not in files or files[relative]["sha256"] != pin["sha256"]:
                    raise ValueError("admission closure is partial or corrupt: " + relative)
    return files


def frame_files(ctx):
    files = {}
    for key, pin in sorted(ctx.components["frame_manifests"].items()):
        path = ctx.host(pin["file"])
        if sha(path) != pin["sha256"]:
            raise ValueError("frame manifest differs")
        frames = read(path)
        if not isinstance(frames, list) or not frames:
            raise ValueError("empty frame manifest")
        store = ctx.current.get("stores", {}).get(key[:-9], "k3f8") or "k3f8"
        for frame in frames:
            expected = frame["sha256"]
            if not re.fullmatch("[0-9a-f]{64}", expected):
                raise ValueError("invalid frame hash")
            name = store + "/" + expected[:2] + "/" + expected + ".png"
            if frame["path"] != "/data2/" + name:
                raise ValueError("frame manifest path differs")
            target = inside(ctx.frame_root, name)
            if name not in files:
                if sha(target) != expected:
                    raise ValueError("staged frame differs: " + name)
                files[name] = dict(sha256=expected, bytes=regular(target).st_size)
    return files


def covered_frames(ctx, files):
    data = read(ctx.destination / "data_receipt.json")
    report = read(inside(ctx.destination, local_name(ctx.logical, data["frames"]["path"])))
    inventory = inside(ctx.destination, local_name(ctx.logical, report["inventory"]["path"]))
    with sqlite3.connect(inventory.as_uri() + "?mode=ro", uri=True) as connection:
        count = 0
        for logical, expected in connection.execute("SELECT logical,sha256 FROM frames"):
            relative = str(Path(logical).relative_to("/data2"))
            if files.get(relative, {}).get("sha256") != expected:
                raise ValueError("a retained frame is outside the cached manifests")
            count += 1
        if not count:
            raise ValueError("empty retained frame inventory")


def verify_files(root, files):
    if not files:
        raise ValueError("empty cache inventory")
    for name, pin in files.items():
        path = inside(root, name)
        if (not re.fullmatch("[0-9a-f]{64}", pin["sha256"])
                or regular(path).st_size != pin["bytes"] or sha(path) != pin["sha256"]):
            raise ValueError("cache payload differs: " + str(path))


def quarantine(path):
    path = Path(path)
    if path.exists() or path.is_symlink():
        # Preserve failures for inspection; cache cleanup belongs to the operator.
        destination = path.with_name(path.name + ".cache-refused." + uuid.uuid4().hex)
        path.rename(destination)
        return str(destination)
    return None


def copy_verified(source, destination, files):
    destination.mkdir(parents=True)
    for name, pin in files.items():
        origin, target = inside(source, name), inside(destination, name)
        before = regular(origin)
        target.parent.mkdir(parents=True, exist_ok=True)
        value = hashlib.sha256()
        with origin.open("rb") as inp, target.open("xb") as out:
            for block in iter(lambda: inp.read(8 << 20), b""):
                value.update(block)
                out.write(block)
            out.flush()
            os.fsync(out.fileno())
        if (signature(regular(origin)) != signature(before) or value.hexdigest() != pin["sha256"]
                or regular(target).st_size != pin["bytes"] or sha(target) != pin["sha256"]):
            raise ValueError("cache copy did not verify")


def check_frames(ctx, files):
    """Repair refused members through the ordinary archive stage, never trust stamps."""
    if not files:
        raise ValueError("empty cached frame inventory")
    bad = []
    for name, pin in files.items():
        path = inside(ctx.frame_root, name)
        try:
            verify_files(ctx.frame_root, {name: pin})
        except (OSError, ValueError):
            bad.append(path)
    if not bad:
        return
    for path in bad:
        quarantine(path)
    for key in ctx.components["frame_manifests"]:
        bundle = key[:-9]
        pin = ctx.current[bundle]
        quarantine(inside(ctx.node / ".stamp", bundle + "." + pin["sha256"] + "." + ctx.current[key]["sha256"]))
    code = sha(ctx.kit / "b/s.py")
    for entry in ctx.current.get("staged_inputs", {}).get("archives", []):
        identity = digest(dict(entry=entry, implementation=code))
        quarantine(inside(ctx.node / ".imports", identity + ".json"))
    raise ValueError("cached frames absent or corrupt; ordinary archive staging required")


def restore(ctx):
    started = time.monotonic()
    try:
        with locked(ctx.cache, ctx.key):
            index = read(inside(ctx.cache, ctx.key + ".json"))
            receipt_path = inside(ctx.cache, index["receipt"])
            if sha(receipt_path) != index["sha256"]:
                raise ValueError("cache receipt hash differs")
            receipt = read(receipt_path)
            if (receipt.get("schema") != SCHEMA or receipt.get("key") != ctx.key
                    or receipt.get("key_components") != ctx.components):
                raise ValueError("cache key or preparation code identity differs")
            source = Path(receipt["source_inputs"])
            verify_files(source, receipt["files"])
            # Reuse only frames available on this node. A cold node takes ordinary staging.
            check_frames(ctx, receipt["frames"])
            target_verified = source == ctx.destination
            if not target_verified and ctx.destination.is_dir():
                try:
                    verify_files(ctx.destination, receipt["files"])
                    target_verified = True
                except (OSError, ValueError):
                    # Equal inputs can produce different UUID paths. Never replace a
                    # complete native journal: retained checkpoints pin those paths.
                    try:
                        admission_files(ctx, ctx.destination)
                    except (OSError, ValueError, KeyError, TypeError, AttributeError):
                        pass
                    else:
                        raise ValueError("complete native journal has another preparation generation")
            if not target_verified:
                temporary = ctx.destination.with_name("inputs.cache-copy." + uuid.uuid4().hex)
                copy_verified(source, temporary, receipt["files"])
                # Only a fully verified HIT may replace a destination. A failed
                # install must restore the native journal before reporting MISS.
                previous = quarantine(ctx.destination)
                try:
                    temporary.rename(ctx.destination)
                except OSError:
                    if previous is not None:
                        try:
                            Path(previous).rename(ctx.destination)
                        except OSError as error:
                            raise RuntimeError("cache install rollback failed; native journal retained at " + previous) from error
                    raise
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        try:
            admission_files(ctx, ctx.destination)
            native = True
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            native = False
        # Native admission owns partial and foreign-config journals as well as
        # complete ones. A MISS must leave that decision, and the bytes, intact.
        ctx.result("NATIVE_JOURNAL" if native else "MISS", reason=type(error).__name__ + ": " + str(error),
                   seconds=time.monotonic() - started)
        return False
    # A report write error after installation is fatal, not a cache MISS.
    ctx.result("HIT", source_job=receipt["source_job"], source_inputs=str(source),
               source_frames=receipt["source_frames"], receipt=dict(path=str(receipt_path), sha256=index["sha256"]),
               verified_files=len(receipt["files"]), verified_frames=len(receipt["frames"]),
               seconds=time.monotonic() - started)
    return True


def seal(ctx):
    if ctx.report.is_file() and read(ctx.report).get("status") == "NATIVE_JOURNAL":
        # Its producer job is unknown to this cache; keep the native provenance intact.
        return False
    started = time.monotonic()
    files = admission_files(ctx, ctx.destination)
    frames = frame_files(ctx)
    covered_frames(ctx, frames)
    receipt = dict(schema=SCHEMA, key=ctx.key, key_components=ctx.components,
                   source_job=ctx.job, source_inputs=str(ctx.destination), source_frames=str(ctx.frame_root),
                   files=files, frames=frames)
    with locked(ctx.cache, ctx.key):
        name = ctx.key + "." + uuid.uuid4().hex + ".receipt.json"
        path = inside(ctx.cache, name)
        atomic(path, receipt)
        pin = dict(receipt=name, sha256=sha(path))
        atomic(inside(ctx.cache, ctx.key + ".json"), pin)
    ctx.result("BUILT", source_job=ctx.job, source_inputs=str(ctx.destination),
               receipt=dict(path=str(path), sha256=pin["sha256"]),
               files=len(files), frames=len(frames), seconds=time.monotonic() - started)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("restore", "seal"))
    parser.add_argument("kit")
    parser.add_argument("node")
    parser.add_argument("cache")
    parser.add_argument("job")
    args = parser.parse_args()
    if os.environ.get("TK_PREPARED_INPUT_CACHE", "0") != "1":
        return 1
    ctx = Context(args.kit, args.node, args.cache, args.job)
    if args.operation == "restore":
        try:
            return 0 if restore(ctx) else 1
        except (OSError, ValueError, KeyError, TypeError, AttributeError, RuntimeError) as error:
            # The wrapper reserves exit 1 for a safe MISS. Do not run native
            # preparation after a failed HIT report or an uncertain install.
            print("prepared input cache restore error: " + str(error), file=sys.stderr)
            return 2
    return 0 if seal(ctx) else 1


if __name__ == "__main__":
    raise SystemExit(main())
