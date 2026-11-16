"""Rung-2 fixture: the same 414 candidates as FXP_S17, rewritten in sharded-target form (rows inline in the index,
targets as byte ranges of two shared shard files under data2root), for trainer 9183d0d6."""
import hashlib, json, os
from pathlib import Path
FX = Path(os.environ["FX"])
src = FX / "runs/aws128p_20261025/frozen/FXP_S17"
dst = FX / "runs/aws128p_20261025/frozen/FXS_S17"
dst.mkdir(parents=True, exist_ok=True)
entries, blobs, spans = [], [bytearray(), bytearray()], []
rows = []
for line in open(src / "candidate_index.jsonl"):
    entry = json.loads(line)
    payload = json.loads((FX / "data2root" / Path(entry["row_path"]).relative_to("/data2")).read_text())
    rows.append((entry, payload))
for number, (entry, payload) in enumerate(rows):
    data = payload["target"].encode()
    blob = blobs[number % 2]
    spans.append((number % 2, len(blob), len(data), hashlib.sha256(data).hexdigest()))
    blob.extend(data)
paths = []
for number, blob in enumerate(blobs):
    digest = hashlib.sha256(bytes(blob)).hexdigest()
    logical = "/data2/k4s1/%s/%s.txt" % (digest[:2], digest)
    target = FX / "data2root" / Path(logical).relative_to("/data2")
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_bytes(bytes(blob))
    paths.append(logical)
out = []
for (entry, payload), (shard, offset, length, digest) in zip(rows, spans):
    new = dict(payload)
    new.update({"pool": entry["pool"], "question_type": entry["question_type"], "target_path": paths[shard],
                "target_offset": offset, "target_length": length, "sha256": digest})
    out.append(new)
(dst / "candidate_index.jsonl").write_text("".join(json.dumps(e, sort_keys=True) + "\n" for e in out))
for name in ("inherited_division.json", "config.json"):
    (dst / name).write_bytes((src / name).read_bytes())
print("sharded fixture", dst, len(out), "entries,", len(paths), "shards")
