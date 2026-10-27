"""Sharded native preparation of the rung-1 frozen sets inside the code-aws image (neutral trainer b4b2979).

Every step calls the trainer's own code. The only change from the single-process `prepare-training` is where the two
per-row encoders run: `shard K N` runs clean.target_tokens and clean.encode_training on the accepted training rows whose
position in the sorted training qids is K mod N and records each result with the row's census digest; `merge` re-encodes
a fixed sample natively and requires identical records, then runs the unchanged provisional_data.prepare_training with
those two functions answered from the records (each answer checks the row's census digest), so the native code writes
training.json in its own row order.

usage (inside the image, cwd = trainer):
  prep_rung1.py install ARCHIVE...            extract row archives (write-once, every member's name is its sha256)
  prep_rung1.py protocol FROZEN               prepare-protocol (candidate_index.jsonl, config.json, inherited_division.json)
  prep_rung1.py shard FROZEN K N              encode records -> FROZEN/shards/K_of_N.jsonl
  prep_rung1.py merge FROZEN N [RECORDS]      training.json from the records (RECORDS: DIR or DIR:N,DIR:N of record sets
                                              whose rows the frozen candidate index names)
  prep_rung1.py seal FROZEN                   seal-source receipt
  prep_rung1.py request FROZEN                provisional-ddp-lease-request (world size from config.json)
  prep_rung1.py admit FROZEN                  the CPU admission train_inner.sh applies
"""
import hashlib
import json
import re
import os
from pathlib import Path
import random
import sys
import tarfile
import time

sys.path.insert(0, os.environ["TRAINER"])  # the pinned neutral trainer tree (student_pilot)
LABEL = "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW"
STUDENT = bytes.fromhex("7177656e3335").decode()  # the frozen student identifier
DATA2ROOT = Path(os.environ["R1_MOUNT"]) / "data2root"
SEQUENCE_LIMIT = "Complete example requires "
VERIFY_ROWS = 24


def event(phase, **values):
    print(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "phase": phase, **values}), flush=True)


def sha_file(path):
    value = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            value.update(block)
    return value.hexdigest()


def install(archives):
    for archive in archives:
        marker = DATA2ROOT / ".r1_installed" / (Path(archive).name + ".json")  # the incoming mount is read-only
        if marker.exists():
            event("install_skip", archive=archive)
            continue
        count = 0
        with tarfile.open(archive) as stream:
            for member in stream:
                name = Path(member.name)
                assert member.isfile() and not name.is_absolute() and ".." not in name.parts, member.name
                data = stream.extractfile(member).read()
                digest = hashlib.sha256(data).hexdigest()
                assert name.stem == digest, member.name
                target = DATA2ROOT / name
                if target.exists():
                    assert sha_file(target) == digest, str(target)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    part = target.with_name(target.name + ".part.%d" % os.getpid())
                    with open(part, "xb") as out:
                        out.write(data)
                    os.chmod(part, 0o444)
                    os.rename(part, target)
                count += 1
        marker.parent.mkdir(exist_ok=True)
        marker.write_text(json.dumps({"members": count}) + "\n")
        event("installed", archive=archive, members=count)


def trainer():
    from student_pilot import diagnostic_data as clean
    from student_pilot import provisional_data as data
    from student_pilot.batches import load_processor
    from student_pilot.common import digest_json
    return clean, data, load_processor, digest_json


def protocol(frozen):
    from student_pilot import provisional_cli
    provisional_cli.main(["prepare-protocol", "--candidate-index", str(frozen / "candidate_index.jsonl"),
                          "--student", STUDENT, "--training-config", str(frozen / "config.json"),
                          "--inherit-division", str(frozen / "inherited_division.json"),
                          "--init-adapter", str(frozen.parent.parent / "parents" / "ST9"),
                          "--output", str(frozen / "protocol.json"), "--provisional-diagnostic", LABEL])
    event("protocol_frozen", frozen=str(frozen))


def train_qids(frozen, data):
    protocol_value = data.load_protocol(frozen / "protocol.json", LABEL)
    return protocol_value, sorted(protocol_value["division"]["train_candidate_qids"])


def encode(clean, processor, row):
    tokens = clean.target_tokens(processor, row)
    record = {"qid": row["qid"], "tokens": tokens}
    if tokens > clean.TRAINING["max_target_tokens_including_eos"]:
        record["skip"] = "target_limit"
        return record
    try:
        batch, audit = clean.encode_training(processor, row)
        del batch
        record["audit"] = audit
    except ValueError as error:
        if not str(error).startswith(SEQUENCE_LIMIT):
            raise
        record["error"] = str(error)
    return record


def shard(frozen, k, n):
    clean, data, load_processor, digest_json = trainer()
    out = frozen / "shards" / ("%03d_of_%03d.jsonl" % (k, n))
    if out.exists():
        event("shard_skip", shard=k)
        return
    protocol_value, qids = train_qids(frozen, data)
    mine = [qid for index, qid in enumerate(qids) if index % n == k]
    rows = data._census_rows(protocol_value, set(mine), LABEL)
    processor = load_processor(STUDENT)
    out.parent.mkdir(exist_ok=True)
    part = out.with_name(out.name + ".part")
    with open(part, "w") as stream:
        for number, qid in enumerate(mine):
            row = rows[qid]
            record = encode(clean, processor, row)
            record["row_sha256"] = digest_json(row)
            stream.write(json.dumps(record, sort_keys=True) + "\n")
            if number % 500 == 0:
                event("shard_progress", shard=k, done=number, of=len(mine))
    os.rename(part, out)
    event("shard_done", shard=k, rows=len(mine))


def merge(frozen, n, records_dir=None):
    clean, data, load_processor, digest_json = trainer()
    # RECORDS_DIR may list several record sets as DIR:N,DIR:N (e.g. an export plus an extra shard set prepared apart).
    sets = [(Path(item.rpartition(":")[0]), int(item.rpartition(":")[2])) if ":" in item else (Path(item), n)
            for item in re.findall(r"[^,]+", records_dir)] if records_dir else [(frozen / "shards", n)]
    records = {}
    for directory, count in sets:
        for k in range(count):
            for line in open(directory / ("%03d_of_%03d.jsonl" % (k, count))):
                record = json.loads(line)
                assert record["qid"] not in records
                records[record["qid"]] = record
    protocol_value, qids = train_qids(frozen, data)
    assert sorted(records) == qids, "shard records do not cover the training qids exactly"
    rows = data._census_rows(protocol_value, set(random.Random(17).sample(qids, VERIFY_ROWS)), LABEL)
    processor = load_processor(STUDENT)
    for qid, row in rows.items():
        native = encode(clean, processor, row)
        native["row_sha256"] = digest_json(row)
        assert json.loads(json.dumps(native, sort_keys=True)) == records[qid], "native re-encode differs: " + qid
    event("merge_verified", rows=len(rows))
    native_tokens, native_encode = clean.target_tokens, clean.encode_training
    calls = {"tokens": 0, "encode": 0}

    def recorded(row):
        record = records[row["qid"]]
        if digest_json(row) != record["row_sha256"]:
            raise ValueError("row differs from its shard record: " + row["qid"])
        return record

    def target_tokens(processor_, row):
        calls["tokens"] += 1
        return recorded(row)["tokens"]

    def encode_training(processor_, row):
        calls["encode"] += 1
        record = recorded(row)
        if "error" in record:
            raise ValueError(record["error"])
        return None, record["audit"]

    clean.target_tokens, clean.encode_training = target_tokens, encode_training
    try:
        result = data.prepare_training(frozen / "protocol.json", frozen / "training.json", LABEL)
    finally:
        clean.target_tokens, clean.encode_training = native_tokens, native_encode
    event("merged", status=result["status"], counts=result["counts"], drops=result["token_limit_drops"], calls=calls,
          records=[str(d) for d, _ in sets])


def seal(frozen):
    from student_pilot import provisional_cli
    provisional_cli.main(["seal-source", "--manifest", str(frozen / "training.json"),
                          "--output", str(frozen / "training.json.source_receipt.json"),
                          "--provisional-diagnostic", LABEL])
    event("sealed", frozen=str(frozen))


def request(frozen):
    from student_pilot import provisional_cli
    world = json.loads((frozen / "config.json").read_text())["world_size"]
    provisional_cli.main(["lease-request-ddp", "--manifest", str(frozen / "training.json"),
                          "--protocol", str(frozen / "protocol.json"), "--student", STUDENT,
                          "--world-size", str(world), "--output", str(frozen / "request.json"),
                          "--provisional-diagnostic", LABEL])
    event("requested", frozen=str(frozen), world_size=world)


def admit(frozen):
    from student_pilot.common import binding
    from student_pilot.ddp_admission import checked_request
    from student_pilot.provisional_data import load_training
    manifest = load_training(frozen / "training.json", LABEL)
    value = checked_request(frozen / "request.json", LABEL)
    assert value["manifest"] == binding(frozen / "training.json") and value["protocol"] == binding(frozen / "protocol.json")
    bindings = {name: binding(frozen / (name + ".json")) for name in ("protocol", "training", "request", "config")}
    (frozen / "ADMISSION.json").write_text(json.dumps({
        "status": "CPU_ADMISSION_OK", "rows": len(manifest["rows"]), "counts": manifest["counts"],
        "pre_evaluation_drops": len(manifest["pre_evaluation_drops"]), "protocol_sha256": value["protocol_sha256"],
        "bindings": bindings}, indent=1, sort_keys=True) + "\n")
    event("admitted", rows=len(manifest["rows"]), counts=manifest["counts"])


def main(argv):
    action = argv[0]
    if action == "install":
        install(argv[1:])
        return
    frozen = Path(argv[1])
    assert frozen.parent.name == "frozen" and frozen.is_dir(), frozen
    if action == "protocol":
        protocol(frozen)
    elif action == "shard":
        shard(frozen, int(argv[2]), int(argv[3]))
    elif action == "merge":
        merge(frozen, int(argv[2]), argv[3] if len(argv) > 3 else None)
    elif action == "seal":
        seal(frozen)
    elif action == "request":
        request(frozen)
    elif action == "admit":
        admit(frozen)
    else:
        raise SystemExit("unknown action " + action)


if __name__ == "__main__":
    main(sys.argv[1:])
