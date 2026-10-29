"""Old-vs-new startup parity on the local CPU fixture (lane startup_cpu_prestage).

  parity.py rank0 MODE RESULTS    rank-0 startup: lease-request identity, verified protocol and manifest, run store,
                                  frame staging (the trainer's localize_frames), payload
  parity.py mirror MODE RESULTS   a second node's mirror_staged_frames into the same (now empty) output path, then
                                  the encoded microbatches of optimizer steps 1-3 for every rank of world 4
MODE old runs the unhooked trainer; MODE new runs with the pre-stage hooks (env set by run_parity.sh).
"""
import hashlib
import json
import os
from pathlib import Path
import pickle
import sys
import time

sys.path.insert(0, os.environ["TRAINER"])
LABEL = "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW"
STUDENT = "qwen35"
FX = Path(os.environ["FX"])
FROZEN = FX / "runs/aws128p_20261025/frozen" / os.environ.get("R1FX_FROZEN", "FXP_S17")
SCRATCH = FX / "runs/r1fx_run"
OUTPUT = SCRATCH / "attempt-1/train"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def tree_digests(root):
    root = Path(root)
    return {str(path.relative_to(root)): sha(path.read_bytes()) for path in sorted(root.rglob("*")) if path.is_file()}


def fixed_provenance(storage, checkpoints=None):
    original = storage.code_provenance

    def code_provenance(config):
        value = original(config)
        value["recorded_at"] = "parity-fixture"
        return value

    storage.code_provenance = code_provenance


def rank0(mode, results):
    from student_pilot import ddp_admission as admission, ddp_training, provisional_data as data, storage
    from student_pilot.common import binding, digest_json, load_json
    from student_pilot.provisional import tag
    fixed_provenance(storage)
    timings, out = {}, {}
    now = time.monotonic()

    def mark(name):
        nonlocal now
        timings[name] = round(time.monotonic() - now, 3)
        now = time.monotonic()

    manifest_path, protocol_path = admission.input_path(FROZEN / "training.json"), admission.input_path(FROZEN / "protocol.json")
    request = admission.checked_request(admission.input_path(FROZEN / "request.json"), LABEL)
    identity = admission.request_identity(manifest_path, protocol_path, LABEL, STUDENT, 4)
    mark("lease_request_identity")
    protocol = data.load_protocol(protocol_path, LABEL, weights=True, student=STUDENT)
    mark("protocol_weight_verify")
    manifest = data.load_training(manifest_path, LABEL)
    mark("training_manifest_verify")
    SCRATCH.mkdir(parents=True, exist_ok=True)
    config = tag({"mode": "parity", "student": STUDENT, "manifest": binding(manifest_path), "protocol": binding(protocol_path),
                  "PROVISIONAL_DIVISION_SHA": protocol["PROVISIONAL_DIVISION_SHA"], "stage_frames": True,
                  "scratch_root": str(SCRATCH)}, LABEL)
    store = storage.RunArtifacts(OUTPUT, config, SCRATCH)
    localized = ddp_training.localize_frames(manifest["rows"], store, manifest_path, SCRATCH, True)
    mark("frame_staging")
    payload = {"protocol": protocol, "rows": localized, "audits": manifest["input_audits"], "counts": manifest["counts"],
               "frame_staging": load_json(store.root / "frame_staging.json"),
               "frame_staging_binding": binding(store.root / "frame_staging.json")}
    out.update(request=digest_json(request), identity=digest_json(identity), protocol=digest_json(protocol),
               manifest=digest_json(manifest), rows=digest_json(localized), audits=digest_json(manifest["input_audits"]),
               counts=manifest["counts"], row_qids=[row["qid"] for row in localized],
               store_files=tree_digests(store.root), timings=timings)
    (Path(results) / f"payload_{mode}.pkl").write_bytes(pickle.dumps(payload, protocol=5))
    (Path(results) / f"rank0_{mode}.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")


def mirror(mode, results):
    from student_pilot import ddp_training, storage
    from student_pilot.batches import load_processor
    from student_pilot.common import digest_json
    from student_pilot.ddp_core import global_batches, rank_slots
    fixed_provenance(storage)
    payload = pickle.loads((Path(results) / f"payload_{mode}.pkl").read_bytes())
    rows, audits = payload["rows"], {audit["qid"]: audit for audit in payload["audits"]}
    started = time.monotonic()
    record = ddp_training.mirror_staged_frames(payload["frame_staging"], payload["frame_staging_binding"], rows, OUTPUT,
                                               SCRATCH, 1, LABEL)
    seconds = round(time.monotonic() - started, 3)
    runtime = json.loads(Path(record["path"]).read_text())
    runtime.pop("verified_at")
    files = {name: digest for name, digest in tree_digests(OUTPUT).items() if not name.startswith("runtime/")}
    processor = load_processor(STUDENT)
    settings = payload["protocol"]["training"]
    world, microbatch = 4, 4
    steps = []
    for index, window in enumerate(global_batches(len(rows), 0, settings["effective_batch_size"], settings["seed"])):
        if index == 3:
            break
        for rank in range(world):
            slots = rank_slots(window["indices"], rank, world, microbatch)
            for start in range(0, len(slots), microbatch):
                chunk = slots[start:start + microbatch]
                batch = ddp_training.encode_microbatch(processor, rows, audits, [position for position, _ in chunk])
                steps.append({"step": index + 1, "rank": rank, "qids": [rows[position]["qid"] for position, _ in chunk],
                              "weights": [weight for _, weight in chunk],
                              "tensors": {name: [list(value.shape), str(value.dtype), sha(value.contiguous().numpy().tobytes())]
                                          for name, value in sorted(batch.items())},
                              "input_ids": batch["input_ids"].tolist()})
    out = {"mirror_seconds": seconds, "mirror_files": files, "mirror_record": digest_json(runtime), "steps": steps}
    (Path(results) / f"mirror_{mode}.json").write_text(json.dumps(out, sort_keys=True) + "\n")


if __name__ == "__main__":
    {"rank0": rank0, "mirror": mirror}[sys.argv[1]](sys.argv[2], sys.argv[3])
