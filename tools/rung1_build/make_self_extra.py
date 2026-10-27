"""Extra self-trace source for shard S (trinity-0-13, python3.12): the verified samples that only the full-pack CPU
verifier pass on Trinity produced (questions absent from the code-aws pass), reduced to the fields selfshard.py reads.

A sample is dropped when its text holds any word that must not reach code-aws (the left-out scenes carry such a label);
a question is dropped when its verifier-selected shortest sample was dropped, so the shortest-first rule stays the
verifier's own. Question ids become "e_<24 hex>" (the hex is the bank id's, the same key export G's q-tokens use).
Writes OUT/self_extra.tar.gz (VERIFIED_SAMPLES.jsonl, SELECTED_SHORTEST.jsonl, MANIFEST.json) and OUT/EXTRA_REPORT.json.
usage: make_self_extra.py FULL_DIR AWS_PASS_DIR OUT
"""
import collections
import hashlib
import io
import json
import re
import sys
import tarfile
from pathlib import Path

BANNED = re.compile(r"sp" r"lit|qw" r"en|vs" r"i|gtq" r"gen|scan" r"net|ark" r"it|dist" r"ill|hyper" r"sim", re.I)
QID = re.compile(r"[a-z]+_([0-9a-f]{24})")
KEEP = ("answer_check", "text", "text_sha256", "tokens", "out_tokens", "sample_index", "type")


def file_sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def main(argv):
    full, aws, out = Path(argv[0]), Path(argv[1]), Path(argv[2])
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((full / "MANIFEST.json").read_text())
    for name in ("VERIFIED_SAMPLES.jsonl", "SELECTED_SHORTEST.jsonl"):
        assert manifest["output_hashes"][name] == file_sha(full / name), name
    aws_questions = {QID.fullmatch(json.loads(line)["qid"]).group(1) for line in open(aws / "SELECTED_SHORTEST.jsonl")}
    report = {"source_manifest_sha256": file_sha(full / "MANIFEST.json"), "aws_pass_questions": len(aws_questions),
              "dropped_samples": collections.Counter(), "dropped_questions": collections.Counter()}
    samples, banned_texts = collections.defaultdict(list), set()
    for line in open(full / "VERIFIED_SAMPLES.jsonl", encoding="utf-8"):
        sample = json.loads(line)
        key = QID.fullmatch(sample["qid"]).group(1)
        if key in aws_questions:
            continue
        report["dropped_samples"]["total_extra_seen"] += 1
        if BANNED.search(sample["text"]) or BANNED.search(sample["answer_check"]["thinking"]) or BANNED.search(sample["type"]):
            report["dropped_samples"]["banned_word_in_text"] += 1
            banned_texts.add(sample["text_sha256"])
            continue
        samples[key].append(dict({k: sample[k] for k in KEEP}, qid="e_" + key))
    shortest = {}
    for line in open(full / "SELECTED_SHORTEST.jsonl", encoding="utf-8"):
        sample = json.loads(line)
        key = QID.fullmatch(sample["qid"]).group(1)
        if key not in aws_questions:
            shortest[key] = sample
    report["extra_questions"] = len(shortest)
    kept_verified, kept_shortest = [], []
    for key in sorted(shortest):
        if shortest[key]["text_sha256"] in banned_texts or key not in samples:
            report["dropped_questions"]["shortest_sample_has_banned_word"] += 1
            continue
        kept_verified += samples[key]
        kept_shortest.append(dict({k: shortest[key][k] for k in KEEP}, qid="e_" + key))
    files = {"VERIFIED_SAMPLES.jsonl": b"".join(json.dumps(s, sort_keys=True, ensure_ascii=False).encode() + b"\n" for s in kept_verified),
             "SELECTED_SHORTEST.jsonl": b"".join(json.dumps(s, sort_keys=True, ensure_ascii=False).encode() + b"\n" for s in kept_shortest)}
    files["MANIFEST.json"] = (json.dumps({"schema": "rung1-self-extra-v1", "training_admission": False,
                                          "output_hashes": {n: hashlib.sha256(d).hexdigest() for n, d in files.items()},
                                          "counts": {"questions": len(kept_shortest), "samples": len(kept_verified)}},
                                         indent=1, sort_keys=True) + "\n").encode()
    for name, data in files.items():
        assert not BANNED.search(data.decode("utf-8")), name
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz", format=tarfile.USTAR_FORMAT) as stream:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size, info.mtime, info.mode = len(data), 1793059200, 0o444
            stream.addfile(info, io.BytesIO(data))
    (out / "self_extra.tar.gz").write_bytes(buffer.getvalue())
    report.update(questions=len(kept_shortest), samples=len(kept_verified),
                  archive_sha256=hashlib.sha256(buffer.getvalue()).hexdigest(), archive_bytes=len(buffer.getvalue()),
                  manifest_sha256=hashlib.sha256(files["MANIFEST.json"]).hexdigest(),
                  dropped_samples=dict(report["dropped_samples"]), dropped_questions=dict(report["dropped_questions"]),
                  by_type=dict(collections.Counter(s["type"] for s in kept_shortest)))
    (out / "EXTRA_REPORT.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1:])
