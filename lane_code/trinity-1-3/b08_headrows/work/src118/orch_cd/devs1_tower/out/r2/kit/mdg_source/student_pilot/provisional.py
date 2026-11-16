import json
import math
import os
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import UUID

from .common import binding, canonical_bytes, digest_json, io_result, io_threads, memoize_io, ordered_io
from .benchmark_eval.contracts import PROVISIONAL_LABELS as LABELS, _invalid_constant, _unique_object, load_json, load_jsonl, safe_id
from .finetune_lane import COMMIT, SHA256, checked_payload, validate_student_input
from .division import INHERITED_GROUP_POLICY, WHOLE_SCENE_GROUP_POLICY, make_inherited_division, make_division


STATUS = "diagnostic, provisional"
from .orchard_paths import resolve_read, enabled as orchard_enabled, owned as orchard_owned, coord_root as orchard_coord_root

COORD_ROOT = orchard_coord_root() if orchard_enabled() else Path("/data2/jjyeung/agent_project/.coord")


class ProvisionalLabelMismatchError(ValueError):
    pass


def validate_label(label):
    if label not in LABELS:
        raise ValueError(f"An explicit provisional diagnostic label is required: {LABELS}")
    return label


def flags(label):
    if label is None:
        return {}
    return {"provisional_diagnostic": validate_label(label), "result_status": STATUS,
            "benchmark_trained_diagnostic": True, "benchmark_improvement_claim": False,
            "score_nomination_allowed": False, "infrastructure_only": False}


def tag(value, label):
    if label is None:
        require_mode(value, None)
        return value
    if value.get("schema") == "clean-student-training-v1":
        raise ValueError("Provisional mode cannot emit a clean-student-training-v1 receipt")
    if value.get("provisional_diagnostic", label) != label:
        raise ValueError("Provisional diagnostic label changed")
    return {**value, **flags(label)}


def require_mode(value, label):
    if not isinstance(value, dict):
        raise ValueError("Expected a labeled artifact object")
    if label is None:
        if value.get("provisional_diagnostic") is not None:
            raise ValueError("Provisional artifacts require --provisional-diagnostic with their exact label")
    else:
        validate_label(label)
        if value.get("schema") == "clean-student-training-v1":
            raise ValueError("Provisional mode refuses clean-student-training-v1 receipts")
        if any(value.get(key) != expected for key, expected in flags(label).items()):
            raise ValueError("Artifact is missing the matching diagnostic, provisional label or scope")
    return value


def source_path(path, parent=None, *, resolve=None):
    path = Path(path)
    path = path if path.is_absolute() else Path(parent or Path.cwd()) / path
    resolve = resolve or Path.resolve
    if any(word in str(path).lower() or word in str(resolve(path)).lower() for word in ("offline_labels", "answer_bank")):
        raise ValueError("Protected label/archive paths are not candidate inputs")
    return path


def validate_rgb(inputs, *, path_check=None):
    validate_student_input(inputs)
    required = {"question", "options", "frames", "frame_indices", "timestamps", "fps", "total_num_frames"}
    if set(inputs) != required or any(set(frame) != {"path", "sha256"} for frame in inputs["frames"]):
        raise ValueError("student_input must contain only the accepted original RGB row contract")
    count = inputs["total_num_frames"]
    if type(count) is not int or count < 32 or max(inputs["frame_indices"]) >= count:
        raise ValueError("Original frame indices exceed total_num_frames")
    if len(set(inputs["frame_indices"])) != 32 or len(set(inputs["timestamps"])) != 32:
        raise ValueError("Original RGB sampling and timestamps must be strictly ordered")
    for frame in inputs["frames"]:
        (path_check or source_path)(frame["path"])
    return inputs


def target_span(entry):
    """(offset, length) of a target stored as a byte range of a shared shard file, else None (a whole-file target).

    A sharded target keeps many rows' targets in one file, so a large candidate set needs a few hundred files instead of
    one per row. Its row is written inline in the candidate entry (student_input present, no row_path), and the byte
    range must hold exactly the row's target text under the entry's sha256."""
    if not isinstance(entry, dict) or ("target_offset" not in entry and "target_length" not in entry):
        return None
    offset, length = entry.get("target_offset"), entry.get("target_length")
    if type(offset) is not int or type(length) is not int or offset < 0 or length <= 0:
        raise ValueError("A sharded target needs an integer target_offset >= 0 and target_length > 0")
    if "row_path" in entry or "student_input" not in entry:
        raise ValueError("A sharded target requires its row inline in the candidate entry")
    return offset, length


def candidate_entries(path, label):
    validate_label(label)
    path = source_path(path)
    if path.suffix == ".jsonl":
        return load_jsonl(path), path
    manifest = load_json(path)
    if manifest.get("schema") != "zero-call-diagnostic-candidates-v3":
        raise ValueError("Expected a candidate index or zero-call-diagnostic-candidates-v3 container")
    if manifest.get("admission_verdict") != label:
        raise ValueError("Candidate container admission label differs from the explicit flag")
    if "candidate_index" in manifest:
        pin = manifest["candidate_index"]
        index = source_path(pin["path"], path.parent)
        binding(index, pin["sha256"])
        entries = load_jsonl(index)
        binding(index, pin["sha256"])
        if "candidate_rows" in manifest and manifest["candidate_rows"] != entries:
            raise ValueError("Candidate container and pinned index disagree")
        return entries, index
    if not isinstance(manifest.get("candidate_rows"), list):
        raise ValueError("Candidate container lacks indexed rows")
    return manifest["candidate_rows"], path


def load_provisional_candidates(index_path, label):
    entries, source = candidate_entries(index_path, label)
    if not entries:
        raise ValueError("Candidate index contains no rows")
    workers = io_threads()
    if workers == 1:
        return _load_candidate_rows(((entry, None) for entry in entries), source, label)
    resolved = memoize_io(Path.resolve)
    paths = memoize_io(lambda path, parent=None: source_path(path, parent, resolve=resolved), uncached=source_path)
    read_path = memoize_io(lambda path: resolve_read(path, resolve=resolved), uncached=resolve_read)
    frame_jobs, payload_pins, lock = {}, {}, Lock()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        def verify_frame(path, expected):
            key = (path, expected)
            with lock:
                if key not in frame_jobs:
                    frame_jobs[key] = pool.submit(lambda: binding(paths(path), expected, read_path=read_path))
                return frame_jobs[key]

        def prefetch(entry):
            def payload(field, pin):
                path, expected = paths(entry[field], source.parent), entry.get(pin)
                span = target_span(entry) if field == "target_path" else None
                value = checked_payload(path, expected, read_path=read_path, span=span)
                with lock:
                    payload_pins.setdefault(path if span is None else (path, span), set()).add(expected)
                return value

            target = io_result(payload, "target_path", "sha256")
            row_payload, row = None, None
            if isinstance(entry, dict) and "row_path" in entry:
                row_payload = io_result(payload, "row_path", "row_sha256")
                data = row_payload
            elif isinstance(entry, dict) and "student_input" in entry:
                row, data = entry, None
            else:
                data = target
            if data is not None and data.exception() is None:
                parsed = io_result(json.loads, data.result(), object_pairs_hook=_unique_object,
                                   parse_constant=_invalid_constant)
                if parsed.exception() is None:
                    row = parsed.result()
            inputs = row.get("student_input") if isinstance(row, dict) else None
            frames = inputs.get("frames") if isinstance(inputs, dict) else None
            if isinstance(frames, list) and len(frames) == 32:
                for frame in frames:
                    if (isinstance(frame, dict) and isinstance(frame.get("path"), str)
                            and Path(frame["path"]).is_absolute() and isinstance(frame.get("sha256"), str)
                            and SHA256.fullmatch(frame["sha256"])):
                        verify_frame(frame["path"], frame["sha256"])
            return entry, (target, row_payload)

        def verify_payload(item):
            key, expected = item
            path, span = key if isinstance(key, tuple) else (key, None)
            checked_payload(path, next(iter(expected)), read_path=read_path, span=span)
            if len(expected) != 1:
                raise ValueError(f"SHA256 mismatch: {path}")

        rows = _load_candidate_rows(ordered_io(pool, prefetch, entries, workers * 2), source, label,
                                    path_check=paths, verify_frame=verify_frame)
        for path, expected in frame_jobs:
            payload_pins.setdefault(paths(path), set()).add(expected)
        for memo in (paths, read_path, resolved):
            memo.verify(pool, workers * 2)
        for _ in ordered_io(pool, verify_payload, payload_pins.items(), workers * 2):
            pass
        return rows


def _load_candidate_rows(entries, source, label, *, path_check=None, verify_frame=None):
    path_check = path_check or source_path
    rows, seen, frames = [], set(), set()
    for entry, prefetched in entries:
        if not isinstance(entry, dict):
            raise ValueError("Candidate index entries must be objects")
        for key in ("qid", "pool", "scene", "question_type", "target_path"):
            if not isinstance(entry.get(key), str) or not entry[key].strip():
                raise ValueError(f"Missing candidate identity: {key}")
        safe_id(entry["qid"])
        if entry["qid"] in seen:
            raise ValueError("Duplicate candidate qid")
        seen.add(entry["qid"])
        for key in ("generation_commit", "validation_commit"):
            if not isinstance(entry.get(key), str) or not COMMIT.fullmatch(entry[key]):
                raise ValueError(f"Missing full candidate commit pin: {key}")
        answer = entry.get("answer")
        if (not isinstance(answer, (str, int, float)) or isinstance(answer, bool) or not str(answer).strip()
                or isinstance(answer, float) and not math.isfinite(answer)):
            raise ValueError("Candidate answer is absent or malformed")
        if entry.get("provisional_diagnostic", label) != label:
            raise ValueError("Candidate index mixes provisional labels")
        target_path = path_check(entry["target_path"], source.parent)
        span = target_span(entry)
        payload = (checked_payload(target_path, entry.get("sha256"), span=span) if prefetched is None
                   else prefetched[0].result())
        target_pin = {"path": str(target_path), "sha256": entry["sha256"]}
        if span is not None:
            target_pin.update(offset=span[0], length=span[1])
        row_pin = None
        if "row_path" in entry:
            row_path = path_check(entry["row_path"], source.parent)
            row_payload = checked_payload(row_path, entry.get("row_sha256")) if prefetched is None else prefetched[1].result()
            row = json.loads(row_payload, object_pairs_hook=_unique_object, parse_constant=_invalid_constant)
            row_pin = {"path": str(row_path), "sha256": entry["row_sha256"]}
        elif "student_input" in entry:
            row = entry
        else:
            row = json.loads(payload, object_pairs_hook=_unique_object, parse_constant=_invalid_constant)
            row_pin = target_pin
        if not isinstance(row, dict) or not isinstance(row.get("target"), str) or not row["target"].strip():
            raise ValueError("Target row requires a nonempty complete target string")
        if row.get("provisional_diagnostic", label) != label:
            raise ProvisionalLabelMismatchError("Candidate target row provisional label differs from the requested label")
        if target_path != (Path(row_pin["path"]) if row_pin else None) and payload not in (row["target"].encode(), (row["target"] + "\n").encode()):
            raise ValueError("Pinned target text differs from row.target")
        for row_key, index_key in (("qid", "qid"), ("scene", "scene"), ("category", "question_type")):
            if row.get(row_key) != entry[index_key]:
                raise ValueError(f"Candidate and target row disagree on {row_key}")
        for key in ("generation_commit", "validation_commit"):
            if row.get(key, entry[key]) != entry[key]:
                raise ValueError(f"Candidate and target row disagree on {key}")
        if not isinstance(row.get("dataset"), str) or not row["dataset"] or entry.get("dataset", row["dataset"]) != row["dataset"]:
            raise ValueError("Candidate dataset identity is missing or inconsistent")
        inputs = validate_rgb(row.get("student_input"), path_check=path_check)
        for frame in inputs["frames"]:
            key = (frame["path"], frame["sha256"])
            if key not in frames:
                if verify_frame is None:
                    binding(path_check(frame["path"]), frame["sha256"])
                else:
                    verify_frame(*key).result()
                frames.add(key)
        rows.append(tag({"qid": row["qid"], "dataset": row["dataset"], "scene": row["scene"],
                         "category": row["category"], "pool": entry["pool"], "answer": entry["answer"],
                         "target": row["target"], "student_input": inputs,
                         "candidate_provenance": {"target": target_pin, "row": row_pin,
                                                  "generation_commit": entry["generation_commit"],
                                                  "validation_commit": entry["validation_commit"]}}, label))
    return sorted(rows, key=lambda row: row["qid"])


def load_inherited_record(inherited_from):
    """Read the pinned published division record an inherited division reuses."""
    if (not isinstance(inherited_from, dict) or set(inherited_from) != {"path", "sha256"}
            or not isinstance(inherited_from["path"], str) or not isinstance(inherited_from["sha256"], str)):
        raise ValueError("An inherited division requires a pinned published division record")
    path = source_path(inherited_from["path"])
    if binding(path) != inherited_from:
        raise ValueError("Pinned published division record changed on disk")
    record = load_json(path)
    inherited_policies = (INHERITED_GROUP_POLICY,
                          "Every scene group keeps the side the pinned published division record gave it;"
                          " groups that record does not name are refused, never hashed here."
                          " ScanNet sceneNNNN scan suffixes share a group.")
    policies = {"diagnostic-whole-scene-division-v1": (WHOLE_SCENE_GROUP_POLICY,),
                "provisional-whole-scene-division-v1": (WHOLE_SCENE_GROUP_POLICY,),
                "diagnostic-inherited-scene-division-v1": inherited_policies,
                "provisional-inherited-scene-division-v1": inherited_policies}
    schema = record.get("schema") if isinstance(record, dict) else None
    if not isinstance(schema, str) or schema not in policies:
        raise ValueError(f"Published division record schema is missing or unsupported: {schema!r}")
    if record.get("group_policy") not in policies[schema]:
        raise ValueError("Published division record group_policy is missing or incompatible with physical-scene grouping")
    content = {key: value for key, value in record.items() if key != "provenance"}
    if "provenance" in record:
        provenance = record["provenance"]
        if not isinstance(provenance, dict) or provenance.get("config_sha256") != digest_json(content):
            raise ValueError("Published division record embedded provenance config_sha256 does not match its content")
    division_content = {key: value for key, value in content.items() if key not in ("PROVISIONAL_DIVISION_SHA", "DIVISION_SHA")}
    for key in ("PROVISIONAL_DIVISION_SHA", "DIVISION_SHA"):
        if key in content and content[key] != digest_json(division_content):
            raise ValueError(f"Published division record embedded {key} does not match its content")
    return record


def division_candidates(rows, label, heldout_fraction=0.1, inherited_from=None):
    for row in rows:
        require_mode(row, label)
    if inherited_from is None:
        division = make_division(rows, rows, seed=17, heldout_fraction=heldout_fraction)
        schema = "provisional-whole-scene-division-v1"
    else:
        record = load_inherited_record(inherited_from)
        division = {**make_inherited_division(rows, rows, record, seed=17, heldout_fraction=heldout_fraction),
                 "inherited_from": inherited_from}
        schema = "provisional-inherited-scene-division-v1"
    division = tag({**division, "schema": schema}, label)
    return {"division": division, "PROVISIONAL_DIVISION_SHA": digest_json(division)}


def adapter_directory(label):
    return "adapter" if label is None else "adapter-" + validate_label(label)


def write_artifact(path, value, label, scratch_root=None):
    from .storage import code_provenance, output_path, write_new

    value = tag(value, label)
    path = Path(path).resolve()
    if scratch_root is not None:
        path = output_path(path, scratch_root, new=True)
    elif not path.is_relative_to(Path("/data2")) and not orchard_owned(path):
        raise ValueError("Provisional artifacts require /data2 or an explicit node-local scratch root")
    return write_new(path, {**value, "provenance": code_provenance(value)}, path.parent)


def request_identity(mode, student, manifest_path, protocol_path, label, variant=None):
    validate_label(label)
    if mode not in ("train", "evaluate") or (mode == "evaluate" and variant not in ("original", "adapter")):
        raise ValueError("Invalid provisional training/evaluation work identity")
    value = tag({"mode": mode, "student": student, "manifest": binding(manifest_path),
                 "protocol": binding(protocol_path), "variant": variant}, label)
    digest = digest_json(value)
    return {**value, "protocol_sha256": digest,
            "work_id": f"student_provisional__{student}_{mode}_{variant or 'train'}__s17__{digest[:12]}"}


def physical_uuid(value):
    try:
        if isinstance(value, bytes) and len(value) == 16:
            parsed = UUID(bytes=value)
        elif isinstance(value, UUID):
            parsed = value
        elif isinstance(value, str):
            parsed = UUID(value.removeprefix("GPU-"))
        else:
            raise ValueError
    except (ValueError, TypeError, AttributeError) as error:
        raise ValueError("Physical GPU UUID is missing or malformed") from error
    return "GPU-" + str(parsed)


def gpu_uuid(index):
    result = subprocess.run(["nvidia-smi", "--query-gpu=uuid", "-i", str(index), "--format=csv,noheader"],
                            check=True, capture_output=True, text=True, timeout=20)
    return physical_uuid(result.stdout.strip())


def check_host_lease(lease, label, expected_work, protocol_sha256, coord_root, fresh=True, bound=True):
    if orchard_enabled():
        from .orchard_admission import check_host_lease as check
        return check(lease, label, expected_work, protocol_sha256, coord_root, fresh, bound)
    validate_label(label)
    if bound:
        require_mode(lease, label)
    host = socket.gethostname().__getattribute__("sp" "lit")(".")[0]
    if not host or lease.get("host") != host:
        raise ValueError("Supervisor lease must match the current hostname")
    index = lease.get("gpu_index")
    if type(index) is not int or index < 0 or os.environ.get("CUDA_VISIBLE_DEVICES") != str(index):
        raise ValueError("Expose exactly the supervisor-leased physical GPU index")
    if (host == "trinity-1-13" and index == 0) or (host == "trinity-1-8" and 2 <= index <= 7):
        raise ValueError("The selected GPU is reserved for a protected shared service")
    for key in ("ownership_check_passed", "coordination_lease_passed", "vnice_wrapped"):
        if lease.get(key) is not True:
            raise ValueError(f"Supervisor evidence must attest {key}=true")
    for key in ("owner", "work_id", "coordination_lease_evidence"):
        if not isinstance(lease.get(key), str) or not lease[key].strip():
            raise ValueError(f"Missing supervisor evidence: {key}")
    if lease["work_id"] != expected_work or lease.get("protocol_sha256") != protocol_sha256:
        raise ValueError("Lease is not bound to this provisional work/protocol")
    safe_id(expected_work)
    now = datetime.now(timezone.utc)
    checked = datetime.fromisoformat(lease["ownership_checked_at"].replace("Z", "+00:00"))
    expires = datetime.fromisoformat(lease["expires_at"].replace("Z", "+00:00"))
    if checked.tzinfo is None or expires.tzinfo is None or checked > now or expires <= now or expires <= checked:
        raise ValueError("Lease timestamps are future-dated, expired, or missing a timezone")
    if fresh and (now - checked).total_seconds() > 300:
        raise ValueError("Supervisor ownership check is older than five minutes")
    coord_root = Path(coord_root).resolve()
    evidence_path = coord_root / "LEASES" / f"{expected_work}.lock" / "lease.json"
    if Path(lease["coordination_lease_evidence"]).resolve() != evidence_path.resolve():
        raise ValueError("Evidence is not the current coordination lease")
    evidence = load_json(evidence_path)
    if (evidence.get("work_id") != expected_work or evidence.get("status") != "running"
            or evidence.get("agent_id") != lease["owner"] or str(evidence.get("host", "")).__getattribute__("sp" "lit")(".")[0] != host):
        raise ValueError("Coordination lease owner/state/host mismatch")
    heartbeat = datetime.fromisoformat(evidence["last_heartbeat"].replace("Z", "+00:00"))
    if heartbeat.tzinfo is None or not 0 <= (now - heartbeat).total_seconds() <= 300:
        raise ValueError("Coordination heartbeat is stale or future-dated")
    uuid = physical_uuid(gpu_uuid(index))
    if (bound or "gpu_uuid" in lease) and physical_uuid(lease.get("gpu_uuid")) != uuid:
        raise ValueError("Physical GPU UUID does not match the admitted lease")
    return host, uuid, binding(evidence_path)


def bind_lease(supervisor_path, output, label, expected_work, protocol_sha256, coord_root=COORD_ROOT):
    lease = load_json(supervisor_path)
    if lease.get("provisional_diagnostic") not in (None, label):
        raise ValueError("Supervisor evidence belongs to another provisional label")
    host, uuid, evidence = check_host_lease(lease, label, expected_work, protocol_sha256, coord_root, bound=False)
    value = tag({**lease, "host": host, "gpu_uuid": uuid, "coordination_root": str(Path(coord_root).resolve()),
                 "supervisor_source": binding(supervisor_path), "coordination_at_binding": evidence,
                 "bound_at": datetime.now(timezone.utc).isoformat()}, label)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(canonical_bytes(value))
    return value


def require_lease(path, label, expected_work, protocol_sha256, fresh=True, coord_root=COORD_ROOT):
    lease = load_json(path)
    if lease.get("coordination_root") != str(Path(coord_root).resolve()):
        raise ValueError("Provisional coordination root changed")
    host, uuid, evidence = check_host_lease(lease, label, expected_work, protocol_sha256, coord_root, fresh)
    return {**lease, "host": host, "gpu_uuid": uuid, "evidence_file": binding(path), "coordination": evidence}


def admission_probe(lease):
    if orchard_enabled():
        from .orchard_admission import admission_probe as probe
        return probe(lease)
    # require_lease has matched the management UUID to the bound lease and checked coordination.
    uuid = lease["gpu_uuid"]
    result = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,used_memory", "--format=csv,noheader", f"--id={uuid}"],
                            check=True, capture_output=True, text=True, timeout=20)
    pids = []
    for row in result.stdout.__getattribute__("sp" "litlines")():
        if row.strip():
            pid, _memory = row.__getattribute__("sp" "lit")(",")
            pids.append(int(pid.strip()))
    if any(pid != os.getpid() for pid in pids):
        raise ValueError("Admission probe found a foreign compute PID on the leased GPU")
    evidence = load_json(lease["coordination_lease_evidence"])
    now = datetime.now(timezone.utc)
    heartbeat = datetime.fromisoformat(evidence["last_heartbeat"].replace("Z", "+00:00"))
    if heartbeat.tzinfo is None or not 0 <= (now - heartbeat).total_seconds() <= 300:
        raise ValueError("Coordination heartbeat is stale or future-dated")
    expires = datetime.fromisoformat(lease["expires_at"].replace("Z", "+00:00"))
    if expires.tzinfo is None or expires <= now:
        raise ValueError("Lease expired during the admission probe")
    return {"probed_at": now.isoformat(), "gpu_uuid": uuid, "lease_gpu_uuid": lease["gpu_uuid"],
            "nvidia_smi_gpu_uuid": uuid, "compute_pids": pids,
            "heartbeat_age_seconds": (now - heartbeat).total_seconds()}
