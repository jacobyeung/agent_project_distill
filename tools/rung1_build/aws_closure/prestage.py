"""Startup pre-stage for the code-aws GPU jobs (closure file; lane startup_cpu_prestage).

A CPU job runs the pinned trainer's own startup verification of one frozen preparation and writes a ready cache of a few
packed files. Every later GPU job of that preparation attaches the cache: one background process per node extracts the
frames to node-local storage and warms the page cache with the base weights, and site_alias/prestage_hooks.py answers the
trainer's startup reads from the cache. Rows, row order, audits, staged bytes and the run's artifacts are those the
trainer's own startup would produce; any mismatch falls back to the trainer's own path.

usage (inside the image, cwd = trainer tree, PYTHONPATH = closure site_alias):
  prestage.py key FROZEN               print the cache directory of FROZEN
  prestage.py build FROZEN             CPU job: verify, pack frames, pickle the verified manifest, render the input rows
  prestage.py attach CACHE LOCAL HOT   GPU node, background: frames -> LOCAL/frames, warm weights (HOT=1: also the
                                       manifest and rendered rows, for the node that runs rank 0)
Cache directory runs/aws128p_20261025/prestage/<frozen>/<key16>/: RECEIPT.json, STAGING.json, manifest.pkl, rows.json
and frames_NN.pack (raw frame bytes in digest order; STAGING.json holds each part's [digest, size] index).
"""
import hashlib
import json
import math
import os
from pathlib import Path
import pickle
import re
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

FORMAT = "r1-prestage-v1"
LABEL = "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW"
STUDENT = bytes.fromhex(os.environ.get("R1_STUDENT_HEX") or "7177656e3335").decode()
INPUTS = ("training.json", "protocol.json", "request.json", "config.json", "training.json.source_receipt.json")
BIG = ("rows", "input_audits")  # manifest fields the lease-request identity never reads
PLACEHOLDER = "/r1_prestage_frames_root_9c2e"  # stands for the run's resolved frames directory in rows.json
MEMO_MIN_BYTES = 64 << 10  # frames are never recorded (they are verified when decoded)
PART_BYTES = 1 << 30
SAFE_PATH = re.compile(r"/[A-Za-z0-9_./-]+")


def event(phase, **values):
    print(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "prestage": phase, **values}, sort_keys=True), flush=True)


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=1) + "\n").encode()


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    value = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            value.update(block)
    return value.hexdigest()


def fingerprint(path):
    status = os.stat(path)
    return [status.st_size, status.st_mtime_ns, status.st_ctime_ns, status.st_ino]


def trainer_commit():
    return subprocess.check_output(["git", "-C", os.environ["TRAINER"], "rev-parse", "HEAD"], text=True).strip()


def cache_dir(frozen):
    """The cache is keyed by the bytes of request.json (which pins training.json and protocol.json by SHA256) and
    config.json, the trainer commit, the student and the input mappings, so a re-prepared arm gets a new cache."""
    frozen = Path(frozen).resolve()
    here = Path(__file__).resolve().parent
    material = {"format": FORMAT, "frozen": str(frozen), "request_sha256": sha_file(frozen / "request.json"),
                "config_sha256": sha_file(frozen / "config.json"), "trainer_commit": trainer_commit(),
                "student": STUDENT, "label": LABEL, "frame_root_map": os.environ.get("STUDENT_FRAME_ROOT_MAP"),
                "model_root": os.environ.get("STUDENT_MODEL_ROOT"),
                # a changed input file or changed pre-stage code gets a new cache instead of a stale one
                "input_stats": {name: fingerprint(frozen / name) for name in INPUTS},
                "code_sha256": {name: sha_file(here / name) for name in ("prestage.py", "site_alias/prestage_hooks.py")}}
    key = sha_bytes(canonical(material))
    return frozen.parent.parent / "prestage" / frozen.name / key[:16], key, material


def require_cpu():
    if (os.environ.get("CUDA_VISIBLE_DEVICES") != ""
            or os.environ.get("SLURM_GPUS_ON_NODE", "") not in ("", "0", "N/A", "(null)")):
        raise SystemExit("prestage build runs in a CPU allocation with CUDA hidden")


def inputs_unchanged(receipt, frozen):
    return all(fingerprint(frozen / name) == receipt["inputs"][name]["stat"] for name in INPUTS)


def build(frozen):
    started = time.time()
    frozen = Path(frozen).resolve()
    cache, key, material = cache_dir(frozen)
    if (cache / "RECEIPT.json").is_file():
        receipt = json.loads((cache / "RECEIPT.json").read_text())
        if receipt.get("key") != key or not inputs_unchanged(receipt, frozen):
            event("stale", cache=str(cache), note="inputs changed after the build; the GPU job stages as before")
            return
        event("present", cache=str(cache), receipt_sha256=sha_file(cache / "RECEIPT.json"))
        return
    require_cpu()
    sys.path.insert(0, os.environ["TRAINER"])
    sys.path.insert(0, str(Path(__file__).resolve().parent / "site_alias"))
    from prestage_hooks import PINNED
    tree = Path(os.environ["TRAINER"]) / "student_pilot"
    unpinned = [name for name, digests in PINNED.items()
                if sha_file(tree / (name.rpartition(".")[2] + ".py")) not in digests]
    if unpinned:  # the GPU hooks would stay inert on this trainer tree, so a cache would never be used
        event("skipped", reason="trainer modules not pinned by prestage_hooks", modules=unpinned)
        return
    from student_pilot import common, ddp_admission, provisional, provisional_data as data
    timings = {}

    def mark(name, since):
        timings[name] = round(time.time() - since, 1)
        event(name, seconds=timings[name])
        return time.time()

    # 1. The trainer's own verification, recording every large file it hashes (path as the trainer reads it, its
    # SHA256 and the stat fingerprint before and after), so a GPU job may skip re-hashing the same unchanged bytes.
    frame_root = json.loads(os.environ.get("STUDENT_FRAME_ROOT_MAP") or "{}").get("/data2")
    recorded, original_sha = {}, common.sha256

    def recording_sha(path, *, read_path=None):
        target = (read_path or common.resolve_read)(path)
        before = fingerprint(target)
        value = original_sha(path, read_path=read_path)
        after = fingerprint(target)
        if (before == after and after[0] >= MEMO_MIN_BYTES and os.path.isabs(str(target))
                and not (frame_root and str(target).startswith(frame_root.rstrip("/") + "/"))):
            recorded[str(path)] = {"target": str(target), "sha256": value, "stat": after}
        return value

    pins = {name: {"path": str(ddp_admission.input_path(frozen / name)), "stat": fingerprint(frozen / name)} for name in INPUTS}
    common.sha256 = recording_sha
    try:
        now = time.time()
        protocol = data.load_protocol(ddp_admission.input_path(frozen / "protocol.json"), LABEL, weights=True, student=STUDENT)
        now = mark("protocol_weights_verified", now)
        manifest_path = ddp_admission.input_path(frozen / "training.json")
        manifest = data.load_training(manifest_path, LABEL)
        now = mark("training_manifest_verified", now)
        request = ddp_admission.checked_request(ddp_admission.input_path(frozen / "request.json"), LABEL)
        now = mark("lease_request_verified", now)
        strict = provisional.load_json(manifest_path)  # the strict parse every lease and rank admission repeats
        if strict != manifest:
            raise SystemExit("strict and native parses of training.json differ")
        head = {name: value for name, value in strict.items() if name not in BIG}
        del strict
        now = mark("manifest_head", now)
    finally:
        common.sha256 = original_sha
    for name in INPUTS:
        pins[name]["sha256"] = sha_file(frozen / name)
        if fingerprint(frozen / name) != pins[name]["stat"]:
            raise SystemExit(f"{name} changed during verification")
    if (request["manifest"] != {"path": pins["training.json"]["path"], "sha256": pins["training.json"]["sha256"]}
            or request["protocol"] != {"path": pins["protocol.json"]["path"], "sha256": pins["protocol.json"]["sha256"]}
            or recorded.get(pins["training.json"]["path"], {}).get("sha256") != pins["training.json"]["sha256"]):
        raise SystemExit("request.json does not pin the verified training.json and protocol.json")
    if manifest["protocol"] != request["protocol"] or not manifest["training_ready"] or not manifest["rows"]:
        raise SystemExit("training.json is not a ready manifest of the frozen protocol")

    # 2. The trainer's staging plan (storage._stage_frames_parallel): sources in first-reference order, one source per
    # digest (the last path seen), files in digest order. Every source path is read and hash-checked here.
    rows = manifest["rows"]
    sources, references = {}, 0
    for row in rows:
        if row.get("student_input") is None:
            continue
        for frame in row["student_input"]["frames"]:
            if not re.fullmatch(r"[0-9a-f]{64}", frame["sha256"]):
                raise SystemExit("frame staging requires complete SHA256 digests")
            references += 1
            sources.setdefault(frame["path"], frame)

    def verify_source(frame):
        data_bytes = common.resolve_read(frame["path"]).read_bytes()
        if sha_bytes(data_bytes) != frame["sha256"]:
            raise SystemExit(f"frame source hash mismatch: {frame['path']}")
        return {**frame, "bytes": len(data_bytes)}

    with ThreadPoolExecutor(max_workers=32) as pool:
        verified = list(pool.map(verify_source, sources.values()))
    sources = {frame["path"]: frame for frame in verified}
    unique = {frame["sha256"]: frame for frame in sources.values()}
    ordered = sorted(unique.items())
    total = sum(frame["bytes"] for _, frame in ordered)
    now = mark("frame_sources_verified", now)

    part_dir = cache.with_name(cache.name + ".part.%s.%d" % (os.environ.get("SLURM_JOB_ID", "local"), os.getpid()))
    part_dir.mkdir(parents=True)
    count = max(1, min(16, math.ceil(total / PART_BYTES)))
    bounds, running, parts = [], 0, []
    for index, (digest, frame) in enumerate(ordered):
        running += frame["bytes"]
        if len(bounds) < count - 1 and running >= total * (len(bounds) + 1) / count and index + 1 < len(ordered):
            bounds.append(index + 1)
    slices = [ordered[a:b] for a, b in zip([0] + bounds, bounds + [len(ordered)])]

    def write_part(position):
        name, value, index = "frames_%02d.pack" % position, hashlib.sha256(), []
        with open(part_dir / name, "xb") as stream:
            for digest, frame in slices[position]:
                data_bytes = common.resolve_read(frame["path"]).read_bytes()
                if len(data_bytes) != frame["bytes"] or sha_bytes(data_bytes) != digest:
                    raise SystemExit(f"frame changed while packing: {frame['path']}")
                stream.write(data_bytes)
                value.update(data_bytes)
                index.append([digest, len(data_bytes)])
        return {"file": name, "sha256": value.hexdigest(), "bytes": sum(size for _, size in index), "frames": index}

    with ThreadPoolExecutor(max_workers=len(slices)) as pool:
        parts = list(pool.map(write_part, range(len(slices))))
    now = mark("frames_packed", now)

    orchard = os.environ.get("STUDENT_ORCHARD") == "1"
    staging = {"schema": "r1-prestage-staging-v1", "rows": len(rows), "frame_references": references,
               "files": [{"source": {"path": frame["path"], "sha256": frame["sha256"]}, "bytes": frame["bytes"]}
                         for _, frame in ordered],
               "source_references": list(sources.values()), "unique_frames": len(ordered), "staged_bytes": total,
               "orchard_path_map": os.environ.get("STUDENT_FRAME_ROOT_MAP") if orchard else None, "parts": parts}
    staging_bytes = canonical(staging)
    (part_dir / "STAGING.json").write_bytes(staging_bytes)

    # 3. The verified manifest for rank 0, and the trainer's own rendering of its staged input rows with a placeholder
    # for the run's frames directory (input_manifest.json is otherwise rendered by the pure-Python indenting encoder).
    manifest_bytes = pickle.dumps(manifest, protocol=5)
    if pickle.loads(manifest_bytes) != manifest:
        raise SystemExit("manifest pickle does not round-trip")
    (part_dir / "manifest.pkl").write_bytes(manifest_bytes)
    now = mark("manifest_pickled", now)
    placeholder_rows = []
    for row in rows:
        inputs = row.get("student_input")
        if inputs is not None:
            inputs = {name: ([{"path": "%s/%s/%s" % (PLACEHOLDER, frame["sha256"][:2], frame["sha256"]),
                               "sha256": frame["sha256"]} for frame in value] if name == "frames" else value)
                      for name, value in inputs.items()}
            row = {name: (inputs if name == "student_input" else value) for name, value in row.items()}
        placeholder_rows.append(row)
    text = common.canonical_bytes({"rows": placeholder_rows})
    prefix, suffix = b'{\n  "rows": ', b"\n}\n"
    if not text.startswith(prefix) or not text.endswith(suffix):
        raise SystemExit("unexpected canonical rendering of the input rows")
    rows_text = text[len(prefix):-len(suffix)]
    del text, placeholder_rows
    if rows_text.count(PLACEHOLDER.encode()) != references:
        raise SystemExit("the frames-root placeholder occurs outside the frame paths")
    (part_dir / "rows.json").write_bytes(rows_text)
    now = mark("input_rows_rendered", now)

    weights = [str(common.resolve_read(pin["path"])) for pin in protocol["base"]["weight_shards"]]
    receipt = {"schema": "r1-prestage-receipt-v1", "format": FORMAT, "key": key, "key_material": material,
               "frozen": str(frozen), "student": STUDENT, "label": LABEL, "trainer_commit": material["trainer_commit"],
               "inputs": pins, "candidate_source": {**protocol["candidate_source"],
                                                    "stat": fingerprint(common.resolve_read(protocol["candidate_source"]["path"]))},
               "verified_hashes": recorded, "manifest_head": head, "rows": len(rows), "counts": manifest["counts"],
               "manifest_pickle": {"file": "manifest.pkl", "sha256": sha_bytes(manifest_bytes), "bytes": len(manifest_bytes)},
               "rows_text": {"file": "rows.json", "sha256": sha_bytes(rows_text), "bytes": len(rows_text),
                             "placeholder": PLACEHOLDER, "references": references},
               "staging": {"file": "STAGING.json", "sha256": sha_bytes(staging_bytes), "parts": len(parts),
                           "unique_frames": len(ordered), "staged_bytes": total},
               "weights": weights, "host": socket.gethostname(), "slurm_job": os.environ.get("SLURM_JOB_ID"),
               "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "timings": timings,
               "seconds": round(time.time() - started, 1)}
    if not inputs_unchanged(receipt, frozen):
        raise SystemExit("frozen inputs changed while the cache was built")
    (part_dir / "RECEIPT.json").write_bytes(canonical(receipt))
    for path in part_dir.iterdir():
        os.chmod(path, 0o444)
    try:
        os.rename(part_dir, cache)
    except OSError:
        if not (cache / "RECEIPT.json").is_file():
            raise
        event("duplicate", kept=str(cache), unused=str(part_dir))
    event("built", cache=str(cache), receipt_sha256=sha_file(cache / "RECEIPT.json"), rows=len(rows),
          unique_frames=len(ordered), staged_bytes=total, parts=len(parts), seconds=round(time.time() - started, 1))


def read_all(path, block=64 << 20):
    with open(path, "rb") as stream:
        while stream.read(block):
            pass


def attach(cache, local, hot):
    """One per GPU node, in the background from the container's start: frames -> LOCAL/frames (renamed there only
    when every part is extracted and hash-checked), then STATE.json; base weights (and on the rank-0 node the
    manifest and rendered rows) are read once so the trainer later reads them from the page cache."""
    started = time.time()
    cache, local = Path(cache), Path(local)
    state = local / "STATE.json"
    local.mkdir(parents=True, exist_ok=True)
    (local / "PID").write_text("%d\n" % os.getpid())  # the hooks stop waiting when this process is gone
    try:
        raw = (cache / "RECEIPT.json").read_bytes()
        if sha_bytes(raw) != os.environ["R1_PRESTAGE_RECEIPT_SHA256"]:
            raise ValueError("RECEIPT.json differs from its pinned SHA256")
        receipt = json.loads(raw)
        staging_raw = (cache / receipt["staging"]["file"]).read_bytes()
        if sha_bytes(staging_raw) != receipt["staging"]["sha256"]:
            raise ValueError("STAGING.json differs from its receipt")
        staging = json.loads(staging_raw)
        warm = list(receipt["weights"])
        if hot:
            warm += [str(cache / receipt["manifest_pickle"]["file"]), str(cache / receipt["rows_text"]["file"])]
        target = local / "frames.part"
        target.mkdir()

        def extract(part):
            value, made = hashlib.sha256(), set()
            with open(cache / part["file"], "rb") as stream:
                for digest, size in part["frames"]:
                    if not re.fullmatch(r"[0-9a-f]{64}", digest):
                        raise ValueError("pack index holds a malformed digest")
                    data_bytes = stream.read(size)
                    if len(data_bytes) != size or sha_bytes(data_bytes) != digest:
                        raise ValueError(f"pack {part['file']} frame {digest} is truncated or corrupt")
                    value.update(data_bytes)
                    folder = target / digest[:2]
                    if digest[:2] not in made:
                        folder.mkdir(exist_ok=True)
                        made.add(digest[:2])
                    with open(folder / digest, "xb") as out:
                        out.write(data_bytes)
                if stream.read(1) or value.hexdigest() != part["sha256"]:
                    raise ValueError(f"pack {part['file']} differs from its receipt")
            return len(part["frames"])

        with ThreadPoolExecutor(max_workers=len(staging["parts"])) as pool:
            extracted = sum(pool.map(extract, staging["parts"]))
        if extracted != staging["unique_frames"]:
            raise ValueError("extracted frame count differs from the staging plan")
        os.rename(target, local / "frames")
        frames_seconds = round(time.time() - started, 1)
        write_state(state, {"status": "ready", "frames": extracted, "bytes": staging["staged_bytes"], "seconds": frames_seconds})
        event("frames_ready", frames=extracted, bytes=staging["staged_bytes"], seconds=frames_seconds)
        with ThreadPoolExecutor(max_workers=4) as pool:  # after the frames: they are needed first
            list(pool.map(read_all, warm))
        event("warm", files=len(warm), seconds=round(time.time() - started, 1))
    except BaseException as error:
        write_state(state, {"status": "failed", "error": f"{type(error).__name__}: {error}"})
        event("attach_failed", error=f"{type(error).__name__}: {error}")
        raise


def write_state(path, value):
    part = path.with_name(path.name + ".part")
    part.write_text(json.dumps(value) + "\n")
    os.replace(part, path)


def main(argv):
    if argv[:1] == ["key"] and len(argv) == 2:
        print(cache_dir(argv[1])[0])
    elif argv[:1] == ["build"] and len(argv) == 2:
        build(argv[1])
    elif argv[:1] == ["attach"] and len(argv) == 4:
        attach(argv[1], argv[2], argv[3] == "1")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
