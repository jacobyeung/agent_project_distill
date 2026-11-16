"""Self-trace shard S for rung 1, built on code-aws from the student's own verified samples (no transfer).

Every S row copies an export-G row of the same question (question, options, frames, answer, scene and flags are
unchanged) and replaces only the target with a verified sample's verbatim text "<think>\n...\n</think>\n\n<answer>".
A question keeps at most PER_QUESTION distinct samples, chosen in the source's shortest order (reasoning tokens, output
tokens, sample index, text SHA-256); the first must equal the source's own shortest selection. A sample is used only if
it was judged correct, is not prefill-only, its text hashes to its recorded SHA-256, its think and answer parts equal the
judged thinking and answer, and that answer equals the G row's answer exactly. Questions outside export G (excluded
there, or never exported) are dropped and counted.

Writes S rows under DATA2ROOT/k3r4/<ab>/<sha>.json and two frozen dirs: <S arm> (S rows plus the held-out support row)
and <mix arm> (the G index plus the S rows; same division as G). Both take the base arm's config.json.
An optional extra source (EXTRA_ARCHIVE EXTRA_SHA256: a tar.gz holding VERIFIED_SAMPLES.jsonl, SELECTED_SHORTEST.jsonl
and MANIFEST.json in the same form) adds questions the main source lacks; a question present in both is an error.
A sample whose text holds a word that must not reach this host's files is dropped (reason banned_word_in_text).
usage: selfshard.py SOURCE_DIR MANIFEST_SHA256 FROZEN_ROOT BASE_ARM S_ARM MIX_ARM DATA2ROOT PER_QUESTION COMMIT
                    [EXTRA_ARCHIVE EXTRA_SHA256]
"""
import collections
import hashlib
import io
import json
import os
import random
import re
import sys
import tarfile
from pathlib import Path

QID = re.compile(r"[a-z]+_([0-9a-f]{24})")
BANNED = re.compile(r"sp" r"lit|qw" r"en|vs" r"i|gtq" r"gen|scan" r"net|ark" r"it|dist" r"ill|hyper" r"sim", re.I)
POOL = "r1s"
# The sampler's short type names and the export's categories.
TYPES = {"appearance_order": "obj_appearance_order", "counting": "object_counting", "relative_count": "relative_count",
         "relative_distance": "object_rel_distance"}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part.%d" % os.getpid())
    part.write_bytes(data)
    os.replace(part, path)


def manifest_hash(value, name):
    """The SHA-256 the source manifest records for one of its output files, if it records one."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key == name or key.endswith("/" + name):
                if isinstance(item, str) and re.fullmatch(r"[0-9a-f]{64}", item):
                    return item
                if isinstance(item, dict) and isinstance(item.get("sha256"), str):
                    return item["sha256"]
            found = manifest_hash(item, name)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = manifest_hash(item, name)
            if found:
                return found
    return None


def file_sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def order_key(sample):
    tokens = sample["tokens"]
    return (tokens["reason_tokens"], sample["out_tokens"], sample["sample_index"], sample["text_sha256"])


def check(sample, row):
    """Reason the sample cannot become a target for ROW, or None."""
    judged = sample["answer_check"]
    text = sample["text"]
    if judged.get("correct") is not True or judged.get("prefill_only") is not False:
        return "not_judged_correct"
    if BANNED.search(text):
        return "banned_word_in_text"
    if sha(text.encode()) != sample["text_sha256"]:
        return "text_hash"
    if not text.startswith("<think>\n") or text.count("</think>") != 1 or text.count("<think>") != 1:
        return "format"
    think, _, answer = text[len("<think>"):].partition("</think>")
    if not think.strip() or think.strip() != judged["thinking"].strip():
        return "think_differs"
    if not text.endswith("</think>\n\n" + answer.strip()) or answer.strip() != judged["answer"]:
        return "answer_part_differs"
    if judged["answer"] != row["answer"]:
        return "answer_differs_from_gt"
    if TYPES.get(sample["type"], sample["type"]) != row["category"]:
        return "type_differs"
    return None


def read_sources(source, manifest_sha, extra, report):
    """(shortest text sha by qid, verified samples) from the main source dir and the optional extra archive."""
    texts = {}
    assert file_sha(source / "MANIFEST.json") == manifest_sha, "source manifest differs"
    manifest = json.loads((source / "MANIFEST.json").read_text())
    report["source_manifest_sha256"] = manifest_sha
    for name in ("VERIFIED_SAMPLES.jsonl", "SELECTED_SHORTEST.jsonl"):
        recorded = manifest_hash(manifest, name)
        actual = file_sha(source / name)
        assert recorded == actual, ("source output differs from or is missing in its manifest", name)
        report.setdefault("source_files", {})[name] = {"sha256": actual}
        texts[("main", name)] = open(source / name, encoding="utf-8")
    if extra:
        archive, extra_sha = extra
        assert file_sha(archive) == extra_sha, "extra archive differs"
        report["extra_archive_sha256"] = extra_sha
        with tarfile.open(archive) as stream:
            members = {m.name: stream.extractfile(m).read() for m in stream if m.isfile()}
        extra_manifest = json.loads(members["MANIFEST.json"].decode())
        for name in ("VERIFIED_SAMPLES.jsonl", "SELECTED_SHORTEST.jsonl"):
            assert extra_manifest["output_hashes"][name] == sha(members[name]), ("extra output differs", name)
            texts[("extra", name)] = io.StringIO(members[name].decode("utf-8"))
    shortest, verified, owner = {}, [], {}
    for (origin, name), lines in texts.items():
        for line in lines:
            sample = json.loads(line)
            key = QID.fullmatch(sample["qid"]).group(1)
            assert owner.setdefault(key, origin) == origin, "a question appears in both sources"
            if name == "SELECTED_SHORTEST.jsonl":
                assert sample["qid"] not in shortest
                shortest[sample["qid"]] = sample["text_sha256"]
            else:
                verified.append({k: sample[k] for k in ("answer_check", "text", "text_sha256", "tokens", "out_tokens",
                                                         "sample_index", "type", "qid")})
    report["source_questions_by_origin"] = dict(collections.Counter(owner.values()))
    return shortest, verified


def main(argv):
    source, manifest_sha, frozen_root, base_arm, s_arm, mix_arm, data2root, per_question, commit = argv[:9]
    extra = (Path(argv[9]), argv[10]) if len(argv) > 9 else None
    source, frozen_root, data2root, per_question = Path(source), Path(frozen_root), Path(data2root), int(per_question)
    assert re.fullmatch(r"[0-9a-f]{40}", commit), commit
    report = {"schema": "rung1-self-shard-v1", "commit": commit, "per_question": per_question,
              # The source samples are not admitted for training by themselves; an independent review flips this.
              "training_admission": False,
              "dropped_samples": collections.Counter(), "dropped_questions": collections.Counter()}
    shortest, verified = read_sources(source, manifest_sha, extra, report)

    base = frozen_root / base_arm
    with open(base / "candidate_index.jsonl", encoding="utf-8") as stream:
        index = [json.loads(line) for line in stream if line.strip()]
    division = json.loads((base / "inherited_division.json").read_text())
    held = set(division["heldout_qids"])
    report["base_arm"] = {"name": base_arm, **{name: file_sha(base / name) for name in
                                               ("config.json", "candidate_index.jsonl", "inherited_division.json")}}
    by_hex = {}
    for entry in index:
        if entry["qid"] not in held:
            assert entry["qid"][0] == "q" and len(entry["qid"]) == 25, entry["qid"]
            by_hex[entry["qid"][1:]] = entry
    support = [entry for entry in index if entry["qid"] in held]
    assert len(support) == 1
    root_prefix = "/data2/"

    def local(path):
        assert path.startswith(root_prefix), path
        return data2root / path[len(root_prefix):]

    samples = collections.defaultdict(list)
    questions_seen = set()
    for sample in verified:
        match = QID.fullmatch(sample["qid"])
        assert match, "unexpected question id form"
        questions_seen.add(sample["qid"])
        if match.group(1) not in by_hex:
            report["dropped_samples"]["question_not_in_export"] += 1
            continue
        samples[sample["qid"]].append(sample)
    report["source_questions"] = len(questions_seen)
    report["dropped_questions"]["question_not_in_export"] = len(questions_seen) - len(samples)

    s_entries, by_type, chosen_counts = [], collections.Counter(), collections.Counter()
    for qid in sorted(samples):
        entry = by_hex[QID.fullmatch(qid).group(1)]
        row = json.loads(local(entry["row_path"]).read_bytes())
        assert sha(local(entry["row_path"]).read_bytes()) == entry["row_sha256"]
        candidates, texts = [], set()
        for sample in sorted(samples[qid], key=order_key):
            reason = check(sample, row)
            if reason:
                report["dropped_samples"][reason] += 1
            elif sample["text_sha256"] in texts:
                report["dropped_samples"]["duplicate_text"] += 1
            else:
                texts.add(sample["text_sha256"])
                candidates.append(sample)
        if not candidates:
            report["dropped_questions"]["no_admissible_sample"] += 1
            continue
        if candidates[0]["text_sha256"] != shortest.get(qid):
            report["dropped_questions"]["shortest_disagrees_with_source"] += 1
            continue
        for rank, sample in enumerate(candidates[:per_question]):
            new = dict(row)
            new.update(qid="s" + entry["qid"][1:] + "ab"[rank], pool=POOL, target=sample["text"],
                       generation_commit=commit, validation_commit=commit)
            data = canonical(new).encode()
            digest = sha(data)
            path = "/data2/k3r4/%s/%s.json" % (digest[:2], digest)
            if not local(path).exists():
                write_atomic(local(path), data)
            s_entries.append(dict(entry, qid=new["qid"], pool=POOL, target_path=path, sha256=digest, row_path=path,
                                  row_sha256=digest, generation_commit=commit, validation_commit=commit))
            by_type[row["category"]] += 1
        chosen_counts[min(len(candidates), per_question)] += 1

    # The held-out support row, with this shard's pool.
    held_row = json.loads(local(support[0]["row_path"]).read_bytes())
    held_row.update(pool=POOL)
    data = canonical(held_row).encode()
    digest = sha(data)
    held_path = "/data2/k3r4/%s/%s.json" % (digest[:2], digest)
    write_atomic(local(held_path), data)
    held_entry = dict(support[0], pool=POOL, target_path=held_path, sha256=digest, row_path=held_path, row_sha256=digest)

    def frozen(name, entries, train_groups):
        directory = frozen_root / name
        assert not directory.exists() or not (directory / "protocol.json").exists(), ("already prepared", name)
        value = dict(division)
        value["train_group_ids"] = sorted(train_groups)
        value["train_scenes"] = sorted(train_groups)
        files = {"config.json": (base / "config.json").read_bytes(),
                 "candidate_index.jsonl": b"".join(canonical(e).encode() + b"\n" for e in entries),
                 "inherited_division.json": (json.dumps(value, indent=2) + "\n").encode()}
        for file_name, data in files.items():
            write_atomic(directory / file_name, data)
        return {file_name: {"sha256": sha(data), "size_bytes": len(data)} for file_name, data in files.items()}

    assert len({e["qid"] for e in s_entries}) == len(s_entries), "S qids are not unique"
    s_groups = {e["dataset"] + "/" + e["scene"] for e in s_entries}
    g_groups = set(division["train_group_ids"])
    assert s_groups <= g_groups and held_entry["dataset"] + "/" + held_entry["scene"] not in s_groups
    report["frozen"] = {
        s_arm: frozen(s_arm, sorted(s_entries + [held_entry], key=lambda e: e["qid"]), s_groups),
        mix_arm: frozen(mix_arm, sorted(index + s_entries, key=lambda e: e["qid"]), g_groups)}
    report.update(rows=len(s_entries), questions=sum(chosen_counts.values()), rows_by_type=dict(by_type),
                  questions_by_samples=dict(chosen_counts), mix_rows=len(index) - 1 + len(s_entries),
                  dropped_samples=dict(report["dropped_samples"]), dropped_questions=dict(report["dropped_questions"]))
    rng = random.Random(1027)
    sample_entries = rng.sample(s_entries, min(1000, len(s_entries)))
    review = b"".join(local(e["row_path"]).read_bytes() + b"\n" for e in sample_entries)
    write_atomic(frozen_root / s_arm / "REVIEW_SAMPLE_ROWS.jsonl", review)
    write_atomic(frozen_root / s_arm / "SELF_SHARD_REPORT.json", (json.dumps(report, indent=1, sort_keys=True) + "\n").encode())
    print(json.dumps({k: report[k] for k in ("rows", "questions", "rows_by_type", "questions_by_samples", "mix_rows",
                                             "dropped_samples", "dropped_questions", "source_questions")}, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1:])
