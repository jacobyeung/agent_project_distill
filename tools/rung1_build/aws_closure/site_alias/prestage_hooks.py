"""Answer the pinned trainer's GPU-job startup from a CPU-built pre-stage cache (closure file; see prestage.py).

sitecustomize.py calls patch(module) after each trainer module below executes, and only when the job exported
R1_PRESTAGE_DIR with R1_PRESTAGE_RECEIPT_SHA256 (cache hooks) or R1_PROBE_REGISTRY (memory-probe reuse). Each hook
applies only to a module whose source bytes are pinned here, and each one falls back to the trainer's own code whenever
its inputs are not exactly the cached ones. What the hooks change is where startup reads come from:

  common.sha256                 a large file the CPU job hashed with the trainer's code, whose stat fingerprint (size,
                                mtime, ctime, inode) is unchanged since, returns that recorded SHA256
  ddp_admission.request_identity  reads the recorded top-level fields of training.json (all but rows and input_audits)
                                instead of re-parsing 4 GB; every pin it compares is still hashed by binding()
  provisional_data.load_training  returns the manifest the CPU job admitted with the trainer's own load_training
  storage.stage_frames          renames the node-local frames extracted from the cache into the run's frames directory
                                and returns the staged rows and receipt the trainer's staging would build
  storage.write_new             writes input_manifest.json from the CPU job's rendering of the same rows
  ddp_training.mirror_staged_frames  the same checks, with the node's extracted frames renamed in place of the copies
  ddp_training.startup_memory_probe  reuses a measured probe of the same memory configuration
"""
import atexit
import copy
import hashlib
import json
import os
from pathlib import Path
import pickle
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from uuid import uuid4

# Source bytes of the hooked modules in trainer trees 299b0c52, 94902f07, 9596b114 and the rung-2 sharded-target tree
# 9183d0d6 (which changes only provisional.py's candidate loading, run by the CPU job's own verification).
PINNED = {
    "student_pilot.common": {"dc087343291b18607235a85d1bdcdfe2b66b1b8f02d3963bb96a5530607621d2"},
    "student_pilot.ddp_admission": {"d3036c32f1f5364304ecec4992280da06defb76b68e916fd7a049f7203ae1c50",
                                    "bcd718947c3c2623287bff32236b1ba63b2ed45a25b6bc2a323c3b0de58271d5"},
    "student_pilot.provisional_data": {"9a95bb1f3dc5f5d3a454cd2936bcaffefb48e2355be28af5552d75750bc055f7"},
    "student_pilot.storage": {"74b51ddd14a8bc8b1b2b783d3ae1b7a268a37e71f9164840aa7fdd618d5c8186"},
    "student_pilot.ddp_training": {"74f33f63db6b6cff8a66b93ffd3bdd9026a565e514ced0d5597f1d4d1c45d29c"},
}
SENTINEL = "__r1_prestage_rows_sentinel_5d0c1e__"
FRAMES_WAIT_SECONDS = 900
CACHE_LOCK = threading.Lock()  # lazy cache load
SWAP_LOCK = threading.RLock()  # provisional.load_json swap during one request_identity call
# Training settings that do not change the memory of a probe microbatch; every other setting is part of the probe key.
PROBE_FREE_SETTINGS = ("seed", "learning_rate", "epochs", "max_steps", "warmup_ratio", "weight_decay", "betas",
                       "clip_norm", "schedule", "shuffle")


def log(event, **values):
    print("AWS_PRESTAGE %s pid=%d %s" % (event, os.getpid(), json.dumps(values, sort_keys=True, default=str)),
          file=sys.stderr, flush=True)


def fingerprint(path):
    status = os.stat(path)
    return [status.st_size, status.st_mtime_ns, status.st_ctime_ns, status.st_ino]


def enabled():
    return bool(os.environ.get("R1_PRESTAGE_DIR") and os.environ.get("R1_PRESTAGE_RECEIPT_SHA256"))


class Cache:
    def __init__(self):
        self.dir = Path(os.environ["R1_PRESTAGE_DIR"])
        raw = (self.dir / "RECEIPT.json").read_bytes()
        if hashlib.sha256(raw).hexdigest() != os.environ["R1_PRESTAGE_RECEIPT_SHA256"]:
            raise ValueError("pre-stage RECEIPT.json differs from its pinned SHA256")
        self.receipt = json.loads(raw)
        if self.receipt.get("schema") != "r1-prestage-receipt-v1":
            raise ValueError("unknown pre-stage receipt schema")
        self.memo = self.receipt["verified_hashes"]
        self.local = Path(os.environ["R1_PRESTAGE_LOCAL"]) if os.environ.get("R1_PRESTAGE_LOCAL") else None
        self.manifest_rows = self.staged_rows = self.frames_root = self._staging = None
        self.hits = self.heads = 0
        atexit.register(self.summary)

    def summary(self):
        if self.hits or self.heads:
            log("summary", hash_memo_hits=self.hits, manifest_head_reads=self.heads)

    def unchanged(self, path, pin):
        try:
            return fingerprint(path) == pin["stat"]
        except OSError:
            return False

    def inputs_unchanged(self, resolve_read):
        """The frozen inputs and the candidate source the CPU job admitted still have their stat fingerprints."""
        candidate = self.receipt["candidate_source"]
        return (all(self.unchanged(pin["path"], pin) for pin in self.receipt["inputs"].values())
                and self.unchanged(resolve_read(candidate["path"]), candidate))

    def manifest_pin(self, path, label):
        pin = self.receipt["inputs"]["training.json"]
        if str(path) == pin["path"] and label == self.receipt["label"] and self.unchanged(pin["path"], pin):
            return pin
        return None

    def read_pinned(self, item):
        data = (self.dir / item["file"]).read_bytes()
        if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise ValueError(f"pre-stage {item['file']} differs from its receipt")
        return data

    def staging(self):
        if self._staging is None:
            item = self.receipt["staging"]
            data = (self.dir / item["file"]).read_bytes()
            if hashlib.sha256(data).hexdigest() != item["sha256"]:
                raise ValueError("pre-stage STAGING.json differs from its receipt")
            self._staging = json.loads(data)
        return self._staging

    def wait_frames(self):
        """The node-local frames the attach process extracted, or None (no attach, failure or timeout)."""
        if self.local is None:
            return None
        state, frames = self.local / "STATE.json", self.local / "frames"
        deadline = time.monotonic() + FRAMES_WAIT_SECONDS
        while time.monotonic() < deadline:
            try:
                value = json.loads(state.read_text())
            except (OSError, ValueError):
                value = None
            if value is not None:
                if value.get("status") == "ready" and frames.is_dir():
                    return frames
                log("frames_unavailable", state=value)
                return None
            if not self.attach_alive():
                log("frames_unavailable", reason="attach process ended without a state")
                return None
            time.sleep(1)
        log("frames_timeout", local=str(self.local))
        return None

    def attach_alive(self):
        try:
            os.kill(int((self.local / "PID").read_text()), 0)
            return True
        except ProcessLookupError:
            return False
        except (OSError, ValueError):
            return True  # PID not written yet, or not ours to signal: keep waiting until the deadline


_CACHE = [None, False]


def cache():
    if not enabled():
        return None
    with CACHE_LOCK:
        if not _CACHE[1]:
            _CACHE[1] = True
            try:
                _CACHE[0] = Cache()
            except Exception as error:
                log("cache_refused", error=f"{type(error).__name__}: {error}")
        return _CACHE[0]


# --- student_pilot.common -------------------------------------------------------------------------------------------
def patch_common(module):
    original = module.sha256

    def sha256(path, *, read_path=None):
        state = cache()
        entry = state.memo.get(str(path)) if state is not None else None
        if entry is not None:
            try:
                target = str((read_path or module.resolve_read)(path))
                if target == entry["target"] and fingerprint(target) == entry["stat"]:
                    state.hits += 1
                    return entry["sha256"]
            except (OSError, TypeError, ValueError):
                pass
        return original(path, read_path=read_path)

    module.sha256 = sha256


# --- student_pilot.ddp_admission ------------------------------------------------------------------------------------
def patch_admission(module):
    original = module.request_identity
    provisional = module.provisional

    def request_identity(manifest_path, protocol_path, label, student, world_size):
        state = cache()
        try:
            target = str(module.input_path(manifest_path))
        except Exception:
            target = None
        pin = state.manifest_pin(target, label) if state is not None and target is not None else None
        if pin is None:
            return original(manifest_path, protocol_path, label, student, world_size)
        load = provisional.load_json

        def load_json(path):
            if str(path) == target and state.unchanged(target, pin):
                state.heads += 1
                return copy.deepcopy(state.receipt["manifest_head"])
            return load(path)

        with SWAP_LOCK:
            provisional.load_json = load_json
            try:
                return original(manifest_path, protocol_path, label, student, world_size)
            finally:
                provisional.load_json = load

    module.request_identity = request_identity


# --- student_pilot.provisional_data ---------------------------------------------------------------------------------
def patch_data(module):
    original = module.load_training

    def load_training(path, label, use_receipt=True):
        state = cache()
        if (state is not None and use_receipt and state.manifest_pin(str(path), label) is not None
                and state.inputs_unchanged(module.resolve_read)):
            started = time.monotonic()
            try:
                manifest = pickle.loads(state.read_pinned(state.receipt["manifest_pickle"]))
                if len(manifest["rows"]) != state.receipt["rows"] or manifest["counts"] != state.receipt["counts"]:
                    raise ValueError("pre-stage manifest differs from its receipt")
            except Exception as error:
                log("manifest_fallback", error=f"{type(error).__name__}: {error}")
                return original(path, label, use_receipt)
            state.manifest_rows = manifest["rows"]
            log("manifest_from_cache", rows=len(manifest["rows"]), seconds=round(time.monotonic() - started, 1))
            return manifest
        return original(path, label, use_receipt)

    module.load_training = load_training


# --- student_pilot.storage ------------------------------------------------------------------------------------------
def staged_copy(rows, destinations):
    """Rows equal to those storage._stage_frames_parallel returns: new row and student-input dicts whose frames are
    copies of the staged bindings. Other values are shared with the admitted rows rather than deep-copied, as the
    trainer's own prepared-startup path (startup_receipt.localize_shared) shares them; startup never mutates rows."""
    staged = []
    for row in rows:
        inputs = row.get("student_input")
        if inputs is None:
            staged.append(dict(row))
            continue
        inputs = {name: ([destinations[frame["sha256"]].copy() for frame in value] if name == "frames" else value)
                  for name, value in inputs.items()}
        staged.append({name: (inputs if name == "student_input" else value) for name, value in row.items()})
    return staged


def patch_storage(module):
    original_stage, original_write = module.stage_frames, module.write_new

    def stage_frames(rows, output, scratch_root):
        state = cache()
        if state is None or state.manifest_rows is None or rows is not state.manifest_rows:
            return original_stage(rows, output, scratch_root)
        started = time.monotonic()
        try:
            staging = state.staging()
        except Exception as error:
            log("stage_fallback", reason=f"{type(error).__name__}: {error}")
            return original_stage(rows, output, scratch_root)
        frames = state.wait_frames()
        if frames is None or staging["rows"] != len(rows):
            log("stage_fallback", reason="frames unavailable or row count differs")
            return original_stage(rows, output, scratch_root)
        output = module.output_path(output, module.scratch_directory(scratch_root), new=True)
        module.ensure_free_space(output)
        try:
            os.rename(frames, output)  # same filesystem by construction (both under the job's scratch root)
        except OSError as error:
            log("stage_fallback", reason=f"rename failed: {error}")
            return original_stage(rows, output, scratch_root)
        files, destinations = [], {}
        for item in staging["files"]:
            digest = item["source"]["sha256"]
            staged = {"path": str(output / digest[:2] / digest), "sha256": digest}
            destinations[digest] = staged
            files.append({"source": dict(item["source"]), "staged": staged, "bytes": item["bytes"]})
        present = {entry.name: entry.stat().st_size for folder in os.scandir(output) for entry in os.scandir(folder.path)}
        if present != {item["staged"]["sha256"]: item["bytes"] for item in files}:
            raise ValueError("extracted frames differ from the staging plan")
        staged_rows = staged_copy(rows, destinations)
        receipt = {"schema": "student-frame-staging-v1", "files": files, "source_references": staging["source_references"],
                   "unique_frames": len(files), "staged_bytes": sum(item["bytes"] for item in files),
                   "scratch_root": str(module.scratch_directory(scratch_root)), "rows": len(rows),
                   **({"orchard_path_map": os.environ.get("STUDENT_FRAME_ROOT_MAP")} if module.orchard_enabled() else {})}
        state.staged_rows, state.frames_root = staged_rows, str(output)
        log("frames_attached", frames=len(files), seconds=round(time.monotonic() - started, 1))
        return staged_rows, receipt

    def write_new(path, value, root):
        state = cache()
        if (state is None or state.staged_rows is None or not isinstance(value, dict)
                or value.get("rows") is not state.staged_rows or Path(path).name != "input_manifest.json"):
            return original_write(path, value, root)
        started = time.monotonic()
        item = state.receipt["rows_text"]
        frames_root = state.frames_root
        small = module.canonical_bytes({**value, "rows": SENTINEL})
        marker = json.dumps(SENTINEL).encode()
        if (not frames_root or json.dumps(frames_root) != '"%s"' % frames_root or small.count(marker) != 1
                or item["placeholder"] in frames_root):
            log("input_manifest_fallback", frames_root=frames_root)
            return original_write(path, value, root)
        try:
            text = state.read_pinned(item)
            if text.count(item["placeholder"].encode()) != item["references"]:
                raise ValueError("pre-stage rows.json placeholder count differs from its receipt")
        except Exception as error:
            log("input_manifest_fallback", error=f"{type(error).__name__}: {error}")
            return original_write(path, value, root)
        text = text.replace(item["placeholder"].encode(), frames_root.encode())
        path = module.contained(root, path)
        if path.exists():
            raise ValueError(f"Refusing to replace an existing artifact: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        module.directory_capacity(path.parent)
        head, _, tail = small.partition(marker)
        with path.open("xb") as stream:
            stream.write(head)
            stream.write(text)
            stream.write(tail)
        log("input_manifest_from_cache", bytes=len(head) + len(text) + len(tail),
            seconds=round(time.monotonic() - started, 1))
        return path

    module.stage_frames, module.write_new = stage_frames, write_new


# --- student_pilot.ddp_training -------------------------------------------------------------------------------------
def patch_training(module):
    original_mirror = module.mirror_staged_frames

    def mirror_staged_frames(receipt, receipt_pin, rows, output, scratch_root, node_rank, label):
        state = cache()
        if state is None or state.local is None:
            return original_mirror(receipt, receipt_pin, rows, output, scratch_root, node_rank, label)
        from student_pilot.storage import ensure_free_space, output_path, write_new
        root = output_path(output, scratch_root)
        files = receipt.get("files", [])
        # The trainer's checks, unchanged.
        if receipt.get("schema") != "student-frame-staging-v1" or module.digest_json(receipt) != receipt_pin["sha256"]:
            raise ValueError("Node-local frame staging receipt changed")
        expected = {(frame["path"], frame["sha256"]) for row in rows if row.get("student_input") is not None
                    for frame in row["student_input"]["frames"]}
        declared = {(item["staged"]["path"], item["staged"]["sha256"]) for item in files}
        if declared != expected or len(declared) != len(files) or receipt.get("unique_frames") != len(files):
            raise ValueError("Node-local mirror must cover exactly the admitted staged frames")
        for item in files:
            digest = item["staged"]["sha256"]
            destination = Path(item["staged"]["path"])
            if (len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest)
                    or item["source"]["sha256"] != digest or destination != root / "frames" / digest[:2] / digest
                    or destination.is_symlink() or destination.resolve() != destination
                    or type(item["bytes"]) is not int or item["bytes"] < 0):
                raise ValueError("Node-local frame path, size, or source identity changed")
        try:
            plan = state.staging()["files"]
        except Exception as error:
            log("mirror_fallback", reason=f"{type(error).__name__}: {error}")
            return original_mirror(receipt, receipt_pin, rows, output, scratch_root, node_rank, label)
        if ([(item["source"]["sha256"], item["bytes"]) for item in plan]
                != [(item["staged"]["sha256"], item["bytes"]) for item in files] or (root / "frames").exists()):
            log("mirror_fallback", reason="receipt differs from the cache plan or frames already present")
            return original_mirror(receipt, receipt_pin, rows, output, scratch_root, node_rank, label)
        frames = state.wait_frames()
        if frames is None:
            return original_mirror(receipt, receipt_pin, rows, output, scratch_root, node_rank, label)
        started = time.monotonic()
        root.mkdir(parents=True, exist_ok=True)
        ensure_free_space(root)
        try:
            os.rename(frames, root / "frames")
        except OSError as error:
            log("mirror_fallback", reason=f"rename failed: {error}")
            return original_mirror(receipt, receipt_pin, rows, output, scratch_root, node_rank, label)

        def verify(item):
            destination = Path(item["staged"]["path"])
            module.binding(destination, item["staged"]["sha256"])
            if destination.stat().st_size != item["bytes"]:
                raise ValueError("Node-local staged frame size changed")

        with ThreadPoolExecutor(max_workers=16) as pool:
            list(pool.map(verify, files))
        record = module.tag({"schema": "provisional-ddp-node-frame-staging-v1", "node_rank": node_rank,
                             "source_receipt": receipt_pin, "files": files,
                             "verified_at": datetime.now(timezone.utc).isoformat()}, label)
        path = write_new(f"runtime/node{node_rank}/frame_staging-{uuid4().hex}.json", record, root)
        log("mirror_attached", frames=len(files), seconds=round(time.monotonic() - started, 1))
        return module.binding(path)

    if enabled():
        module.mirror_staged_frames = mirror_staged_frames


def probe_key(protocol, rows, audits, settings, topology):
    import torch
    from student_pilot.ddp_config import allocator_settings
    names = ("sequence_tokens", "visual_tokens", "assistant_tokens_including_eos")
    stress = sorted({max(range(len(rows)), key=lambda index: audits[rows[index]["qid"]][name]) for name in names})
    device = torch.cuda.get_device_properties(0)
    material = {"schema": "r1-probe-key-v2", "student": protocol["student"], "base_sha256": protocol["base_sha256"],
                "runtime": protocol["runtime"], "versions": protocol["versions"],
                "init_adapter_sha256": protocol.get("init_adapter_sha256"), "efa": os.environ.get("R1_EFA"),
                "settings": {name: value for name, value in settings.items() if name not in PROBE_FREE_SETTINGS},
                "stress_audits": [audits[rows[index]["qid"]] for index in stress],
                "topology": {name: topology.get(name) for name in ("nnodes", "local_world_size")},
                "device": {"name": device.name, "total_memory_bytes": device.total_memory},
                "torch": torch.__version__, "allocator": allocator_settings()}
    return hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest(), material


def patch_probe(module):
    original = module.startup_memory_probe

    def startup_memory_probe(model, processor, rows, audits, settings, rank, lease_check, protocol, topology, checkpoint):
        import torch
        registry = os.environ.get("R1_PROBE_REGISTRY")
        if os.environ.get("STUDENT_MEMORY_PROBE_CACHE") is not None or not registry:
            return original(model, processor, rows, audits, settings, rank, lease_check, protocol, topology, checkpoint)
        world = settings["world_size"]
        key = material = reports = source = None
        try:
            key, material = probe_key(protocol, rows, audits, settings, topology)
            entry = Path(registry) / (key + ".json")
            if entry.is_file():
                value = json.loads(entry.read_text())
                if value.get("key") == key and len(value.get("ranks", [])) == world:
                    reports, source = value["ranks"], str(entry)
            resume = os.environ.get("RESUME_FROM")
            # A resumed multi-node run takes the exact microbatch (batch / world), so the checkpoint's own measured
            # probe only has to show that size fits; one-node runs pick by timing and measure afresh.
            if reports is None and checkpoint is not None and resume and topology.get("nnodes", 1) > 1:
                path = Path(resume) / "artifacts/memory_probe.json"
                pin = checkpoint["files"].get("artifacts/memory_probe.json")
                if pin is not None and hashlib.sha256(path.read_bytes()).hexdigest() == pin["sha256"]:
                    candidate = json.loads(path.read_text())["ranks"]
                    total = torch.cuda.get_device_properties(0).total_memory
                    if (len(candidate) == world and all(trial.get("total_memory_bytes") == total
                                                        for report in candidate for trial in report["trials"] if trial.get("fits"))):
                        reports, source = candidate, str(path)
        except Exception as error:
            log("probe_lookup_failed", error=f"{type(error).__name__}: {error}")
            reports = None
        usable = False
        try:
            if reports is not None:
                size = settings["effective_batch_size"] // world
                report = next((item for item in reports if item.get("rank") == rank), None)
                trial = next((item for item in (report or {}).get("trials", [])
                              if item.get("microbatch") == size and item.get("fits")), None)
                if trial is not None:
                    free, _ = torch.cuda.mem_get_info()
                    usable = (trial["peak_allocated_bytes"] * settings["memory_fit_safety_factor"]
                              <= free + torch.cuda.memory_reserved())
        except Exception as error:
            log("probe_check_failed", error=f"{type(error).__name__}: {error}")
            usable = False
        votes = module.gather({"key": key, "usable": usable}, world)  # every rank takes the same branch
        if key is not None and all(vote["usable"] and vote["key"] == key for vote in votes):
            module.startup_event("memory_probe_reused")
            report = next(item for item in reports if item.get("rank") == rank)
            log("probe_reused", source=source, key=key)
            return {**report, "reused_measured_probe": {"source": source, "key": key}}, None
        probe, context = original(model, processor, rows, audits, settings, rank, lease_check, protocol, topology, checkpoint)
        probes = module.gather(probe, world)
        if rank == 0 and key is not None:
            try:
                directory = Path(registry)
                directory.mkdir(parents=True, exist_ok=True)
                entry = directory / (key + ".json")
                if not entry.exists():
                    part = directory / (key + ".json.part.%d" % os.getpid())
                    part.write_text(json.dumps({"key": key, "material": material, "ranks": probes,
                                                "recorded_at": datetime.now(timezone.utc).isoformat()}, sort_keys=True) + "\n")
                    os.replace(part, entry)
                    log("probe_recorded", entry=str(entry))
            except Exception as error:
                log("probe_record_failed", error=f"{type(error).__name__}: {error}")
        return probe, context

    module.startup_memory_probe = startup_memory_probe


PATCHES = {"student_pilot.common": (patch_common,), "student_pilot.ddp_admission": (patch_admission,),
           "student_pilot.provisional_data": (patch_data,), "student_pilot.storage": (patch_storage,),
           "student_pilot.ddp_training": (patch_training, patch_probe)}


def wanted(fullname):
    if fullname not in PATCHES:
        return False
    if fullname == "student_pilot.ddp_training":
        return enabled() or bool(os.environ.get("R1_PROBE_REGISTRY"))
    return enabled()


def patch(module, source_bytes):
    if not wanted(module.__name__):
        return
    if hashlib.sha256(source_bytes).hexdigest() not in PINNED[module.__name__]:
        log("module_not_pinned", module=module.__name__)
        return
    for function in PATCHES[module.__name__]:
        if function is patch_probe and not os.environ.get("R1_PROBE_REGISTRY"):
            continue
        if function is not patch_probe and not enabled():
            continue
        function(module)
