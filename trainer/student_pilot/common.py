from .orchard_paths import resolve_read, enabled as orchard_enabled, owned as orchard_owned
import hashlib
import json
import os
from collections import deque
from concurrent.futures import Future
from pathlib import Path
from threading import Lock

REPO = Path(__file__).resolve().parents[1]
PILOT = REPO.parent
ARTIFACTS = REPO / "artifacts"
DONOR = Path("/data2/jjyeung/agent_project_data/r1298_req229_common_gt/v14/cells/gt_gt_high")
CONTRACT = DONOR / "package/contract.json"
CONTRACT_SHA = "0027aa304dd8255eb9ead6d6e7fb473fbba45fd12b667febf6a70634806972a1"
MEMBERSHIP = Path("/data2/jjyeung/agent_project_data/answerable500_membership_20260824/MEMBERSHIP_ANSWERABLE_500.json")
MEMBERSHIP_SHA = "2de71c248b9b9817d515510b48dd4d9a5a3800583f5ea64ea2be855b16220fbf"
REGISTRY = Path("/home/jjyeung/agent_project_astra_self_improve/right_now/selected_frames_full.json")
REGISTRY_SHA = "85f88a727b68b94be82e38b977415328c241fd3fe6bd3e7dd70a5ea7e386acbc"
SCORER_MAIN = Path("/home/jjyeung/agent_project/agent/agentic_information_5.0/evaluate_benchmark_v4.py")
SCORER_LIB = SCORER_MAIN.parent.parent / "evaluation/scoring.py"
MODEL = Path("/data2/jjyeung/cache/huggingface/hub/models--OneThink--OneThinker-8B/snapshots/2b7032f4179d8c032d2eac67b3692263f85be0fc")
MODEL_REVISION = MODEL.name


def startup_event(phase):
    import time
    from datetime import datetime, timezone

    print(json.dumps({"event": "startup_phase", "phase": phase,
                      "utc": datetime.now(timezone.utc).isoformat(), "monotonic_seconds": time.monotonic(),
                      "rank": os.environ.get("RANK", os.environ.get("EVAL_SHARD_INDEX")),
                      "pid": os.getpid()}, sort_keys=True), flush=True)


def kernel_cache_identity():
    import platform
    import sys
    from importlib.metadata import PackageNotFoundError, version

    packages = {}
    for name in ("torch", "triton", "tilelang", "flash-linear-attention", "fla-core", "causal-conv1d"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    return {"schema": 1, "python": sys.implementation.cache_tag, "machine": platform.machine(),
            "packages": packages, "cuda_home": os.environ.get("CUDA_HOME"),
            "cuda_version": os.environ.get("CUDA_VERSION")}


def configure_kernel_cache(runtime_root):
    import re

    value = os.environ.get("STUDENT_KERNEL_CACHE_ROOT")
    if value is None:
        return {}
    raw, runtime = Path(value), Path(runtime_root).resolve()
    root = raw.resolve()
    tag = os.environ.get("STUDENT_KERNEL_CACHE_TAG", "")
    if (not raw.is_absolute() or ".." in raw.parts
            or not (root.is_relative_to(REPO) or orchard_owned(root))
            or not (runtime.is_relative_to(REPO) or runtime.is_relative_to(Path("/scratch/jjyeung")) or orchard_owned(runtime))):
        raise ValueError("Kernel cache paths must stay in owned repository or Orchard storage")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", tag):
        raise ValueError("STUDENT_KERNEL_CACHE_TAG must identify the pinned hardware and compiler environment")
    identity = {"runtime": kernel_cache_identity(), "tag": tag}
    namespace = root / ("v1-" + hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest())
    paths = {"TRITON_CACHE_DIR": namespace / "triton", "TILELANG_CACHE_DIR": namespace / "tilelang",
             "CUDA_CACHE_PATH": namespace / "cuda", "TORCHINDUCTOR_CACHE_DIR": namespace / "torchinductor"}
    for path in (root, namespace, *paths.values()):
        if not path.resolve().is_relative_to(root):
            raise ValueError("Kernel cache symlink escapes its root")
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        metadata = path.stat()
        if metadata.st_uid != os.geteuid() or metadata.st_mode & 0o022:
            raise ValueError("Kernel caches must be owned by this user and not writable by others")
    temporary = runtime / ".tmp/tilelang"
    temporary.mkdir(parents=True, exist_ok=True)
    paths["TILELANG_TMP_DIR"] = temporary
    result = {key: str(path) for key, path in paths.items()}
    os.environ.update(result)
    return result


def configure_environment(runtime_root=None):
    root = Path(runtime_root or REPO).resolve()
    if not root.is_relative_to(REPO) and not root.is_relative_to(Path("/scratch/jjyeung")) and not orchard_owned(root):
        raise ValueError("Runtime caches must stay in the repository or node-local scratch")
    paths = {
        "TMPDIR": root / ".tmp",
        "XDG_CACHE_HOME": root / ".cache",
        "TORCH_HOME": root / ".cache/torch",
        "TRITON_CACHE_DIR": root / ".cache/triton",
        "PIP_CACHE_DIR": root / ".cache/pip",
        "CUDA_CACHE_PATH": root / ".cache/cuda",
        "TORCHINDUCTOR_CACHE_DIR": root / ".cache/torchinductor",
    }
    for key, path in paths.items():
        path.mkdir(parents=True, exist_ok=True)
        os.environ[key] = str(path)
    os.environ.setdefault("HF_HOME", "/data2/jjyeung/cache/huggingface")
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(Path(os.environ["HF_HOME"]) / "hub"))
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["WANDB_DISABLED"] = "true"
    os.environ.setdefault("OMP_NUM_THREADS", "4")
    configure_kernel_cache(root)


def io_threads():
    workers = int(os.environ.get("STUDENT_IO_THREADS", "32"))
    if workers < 1:
        raise ValueError("STUDENT_IO_THREADS must be a positive integer")
    return workers


def io_result(function, *args, **kwargs):
    future = Future()
    try:
        future.set_result(function(*args, **kwargs))
    except BaseException as error:
        future.set_exception(error)
    return future


def memoize_io(function, *, uncached=None):
    cache, pending, lock = {}, {}, Lock()

    def cached(*args):
        try:
            hash(args)
        except TypeError:
            return function(*args)
        with lock:
            if args in cache:
                return cache[args]
            future = pending.get(args)
            owner = future is None
            if owner:
                pending[args] = future = Future()
        if owner:
            try:
                value = function(*args)
            except BaseException as error:
                future.set_exception(error)
            else:
                with lock:
                    cache[args] = value
                    pending.pop(args)
                future.set_result(value)
        return future.result()

    def verify(pool, limit):
        observations = {}
        with lock:
            for args, value in cache.items():
                key = tuple(str(arg) if isinstance(arg, Path) else arg for arg in args)
                observations.setdefault(key, (args, []))[1].append(value)

        def check(item):
            args, expected = item
            current = (uncached or function)(*args)
            if any(current != value for value in expected):
                raise ValueError(f"Path resolution changed during validation: {args[0]}")

        for _ in ordered_io(pool, check, observations.values(), limit):
            pass

    cached.verify = verify
    return cached


def ordered_io(pool, function, values, limit):
    pending, iterator, exhausted = deque(), iter(values), False
    try:
        while pending or not exhausted:
            while not exhausted and len(pending) < limit:
                try:
                    value = next(iterator)
                except StopIteration:
                    exhausted = True
                except BaseException as error:
                    future = Future()
                    future.set_exception(error)
                    pending.append(future)
                    exhausted = True
                else:
                    pending.append(pool.submit(function, value))
            if pending:
                yield pending.popleft().result()
    finally:
        for future in pending:
            future.cancel()


def sha256(path, *, read_path=None):
    digest = hashlib.sha256()
    with (read_path or resolve_read)(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path):
    with resolve_read(path).open() as stream:
        return json.load(stream)


def canonical_bytes(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def digest_json(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def write_once(path, value):
    path = Path(path)
    if not path.resolve().is_relative_to(Path("/data2")) and not orchard_owned(path):
        raise ValueError("Artifacts must remain under /data2")
    payload = canonical_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError(f"Refusing to change immutable artifact: {path}")
        return path
    with path.open("xb") as stream:
        stream.write(payload)
    return path


def binding(path, expected=None, *, read_path=None):
    result = {"path": str(path), "sha256": sha256(path) if read_path is None else sha256(path, read_path=read_path)}
    if expected is not None and result["sha256"] != expected:
        raise ValueError(f"Hash mismatch for {path}")
    return result
