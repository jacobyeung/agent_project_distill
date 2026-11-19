from .orchard_paths import resolve_read, enabled as orchard_enabled, owned as orchard_owned
import argparse
import hashlib
import json
import math
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .common import binding, canonical_bytes, sha256


SHA256 = re.compile(r"[0-9a-f]{64}")
COMMIT = re.compile(r"[0-9a-f]{40}")
PENDING = "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW"


def parse_params(path):
    values = {}
    for line in Path(path).read_text().__getattribute__("sp" "litlines")():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator or key in values:
            raise ValueError("Malformed or duplicate training parameter")
        values[key] = value.strip()
    for key in ("CANDIDATE_INDEX", "GPUS", "PUBLISH_ROOT", "ADMISSION_VERDICT"):
        if not values.get(key):
            raise ValueError(f"Required training parameter is empty: {key}")
    publish_root = Path(values["PUBLISH_ROOT"]).resolve()
    publish_home = Path("/data3/jjyeung/agent_project_data")
    if publish_root == publish_home or not publish_root.is_relative_to(publish_home):
        raise ValueError("Publication must remain under /data3/jjyeung/agent_project_data")
    verdict = values["ADMISSION_VERDICT"]
    if verdict not in (PENDING, "VERDICT: PASS"):
        try:
            verdict = Path(verdict).read_text().__getattribute__("sp" "litlines")()[0].strip()
        except (OSError, IndexError) as error:
            raise ValueError("Admission verdict is neither an allowed literal nor a readable verdict file") from error
    if verdict not in (PENDING, "VERDICT: PASS"):
        raise ValueError(f"Admission verdict refuses this lane: {verdict}")
    values["admission_line"] = verdict
    values["label"] = "diagnostic, provisional" if verdict == PENDING else "diagnostic"
    values.setdefault("STUDENTS", "both")
    values.setdefault("TRAINER_BRANCH", "trainer-qwen35-scratch-20260918")
    if values["STUDENTS"] not in ("both", "onethinker", "qwen35"):
        raise ValueError("STUDENTS must be onethinker, qwen35, or both")
    if values["GPUS"] != "auto" and not re.fullmatch(r"\d+(,\d+)*", values["GPUS"]):
        raise ValueError("GPUS must be auto or a comma-separated index list")
    return values


def validate_student_input(inputs):
    if not isinstance(inputs, dict):
        raise ValueError("student_input must be an object")
    if not isinstance(inputs.get("question"), str) or not inputs["question"].strip():
        raise ValueError("student_input.question must be a nonempty string")
    if "options" not in inputs or (inputs["options"] is not None and
                                    (not isinstance(inputs["options"], list) or
                                     not all(isinstance(option, str) for option in inputs["options"]))):
        raise ValueError("student_input.options must be a string list or null")
    for name in ("frames", "frame_indices", "timestamps"):
        if not isinstance(inputs.get(name), list) or len(inputs[name]) != 32:
            raise ValueError(f"student_input.{name} must contain exactly 32 entries")
    for frame in inputs["frames"]:
        if (not isinstance(frame, dict) or not isinstance(frame.get("path"), str) or
                not Path(frame["path"]).is_absolute() or not isinstance(frame.get("sha256"), str) or
                not SHA256.fullmatch(frame["sha256"])):
            raise ValueError("Every RGB frame needs an absolute path and a SHA256 digest")
    if any(type(index) is not int or index < 0 for index in inputs["frame_indices"]):
        raise ValueError("frame_indices must be nonnegative integers")
    if inputs["frame_indices"] != sorted(inputs["frame_indices"]):
        raise ValueError("frame_indices must preserve temporal order")
    fps = inputs.get("fps")
    if type(fps) not in (int, float) or not math.isfinite(fps) or fps <= 0:
        raise ValueError("student_input.fps must be positive and finite")
    if any(type(stamp) not in (int, float) or not math.isfinite(stamp) or stamp < 0 for stamp in inputs["timestamps"]):
        raise ValueError("timestamps must be finite nonnegative numbers")
    if inputs["timestamps"] != sorted(inputs["timestamps"]):
        raise ValueError("timestamps must preserve temporal order")


def checked_payload(path, expected, *, read_path=None, span=None):
    """Bytes of a pinned file, or of the byte range span=(offset, length) of a shared shard file; SHA256-checked."""
    if not isinstance(expected, str) or not SHA256.fullmatch(expected):
        raise ValueError(f"Invalid SHA256 digest for {path}")
    if span is None:
        payload = (read_path or resolve_read)(path).read_bytes()
    else:
        offset, length = span
        with (read_path or resolve_read)(path).open("rb") as stream:
            stream.seek(offset)
            payload = stream.read(length)
        if len(payload) != length:
            raise ValueError(f"Short target slice: {path}@{offset}+{length}")
    if hashlib.sha256(payload).hexdigest() != expected:
        raise ValueError(f"SHA256 mismatch: {path}" + ("" if span is None else f"@{span[0]}+{span[1]}"))
    return payload


def gate_candidates(index_path, progress=None):
    started = time.monotonic()
    payload = Path(index_path).read_bytes()
    parsed = []
    for number, line in enumerate(payload.__getattribute__("sp" "litlines")(), 1):
        try:
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError("Index entry must be an object")
            parsed.append((number, row, None))
        except (ValueError, TypeError) as error:
            parsed.append((number, {}, str(error)))
    if not parsed:
        raise ValueError("Candidate index contains no rows")
    counts = Counter(str(row.get("qid", "")) for _, row, _ in parsed)
    failures, valid, frame_cache = [], [], {}
    target_hashes = row_hashes = 0
    last_heartbeat = started
    for number, entry, parse_error in parsed:
        qid = str(entry.get("qid", f"index-line-{number}"))
        try:
            if parse_error:
                raise ValueError(parse_error)
            for name in ("qid", "pool", "scene", "question_type", "target_path", "row_path"):
                if not isinstance(entry.get(name), str) or not entry[name].strip():
                    raise ValueError(f"Candidate field must be a nonempty string: {name}")
            if counts[qid] != 1:
                raise ValueError("Duplicate candidate qid")
            if "answer" not in entry or entry["answer"] is None or entry["answer"] == "":
                raise ValueError("Candidate answer is absent")
            for name in ("generation_commit", "validation_commit"):
                if not isinstance(entry.get(name), str) or not COMMIT.fullmatch(entry[name]):
                    raise ValueError(f"Missing full commit pin: {name}")
            target = checked_payload(entry["target_path"], entry.get("sha256"))
            target_hashes += 1
            row = json.loads(checked_payload(entry["row_path"], entry.get("row_sha256")))
            row_hashes += 1
            if not isinstance(row, dict) or not isinstance(row.get("target"), str) or not row["target"].strip():
                raise ValueError("Target row must contain a nonempty target string")
            if target not in (row["target"].encode(), (row["target"] + "\n").encode()):
                raise ValueError("Pinned text target differs from row.target")
            for name, indexed in (("qid", "qid"), ("scene", "scene"), ("category", "question_type"),
                                  ("generation_commit", "generation_commit"), ("validation_commit", "validation_commit")):
                if row.get(name) != entry[indexed]:
                    raise ValueError(f"Candidate and target row disagree on {name}")
            if not isinstance(row.get("dataset"), str) or not row["dataset"]:
                raise ValueError("Target row lacks dataset identity for physical-scene grouping")
            if entry.get("dataset", row["dataset"]) != row["dataset"]:
                raise ValueError("Candidate and target row disagree on dataset")
            validate_student_input(row.get("student_input"))
            for frame in row["student_input"]["frames"]:
                key = (frame["path"], frame["sha256"])
                if key not in frame_cache:
                    try:
                        if sha256(frame["path"]) != frame["sha256"]:
                            raise ValueError(f"SHA256 mismatch: {frame['path']}")
                        frame_cache[key] = None
                    except (OSError, ValueError) as error:
                        frame_cache[key] = str(error)
                if frame_cache[key] is not None:
                    raise ValueError(frame_cache[key])
            valid.append(entry)
        except (OSError, ValueError, TypeError, KeyError) as error:
            failures.append({"line": number, "qid": qid, "reason": str(error)})
        if progress and (time.monotonic() - last_heartbeat >= 180 or number == len(parsed)):
            progress(number, len(parsed), len(failures))
            last_heartbeat = time.monotonic()
    if hashlib.sha256(Path(index_path).read_bytes()).hexdigest() != hashlib.sha256(payload).hexdigest():
        raise ValueError("Candidate index changed during validation")
    failed = len(failures)
    status = "STOP" if failed * 100 > len(parsed) else "PASS_WITH_DROPS" if failed else "PASS"
    report = {"schema": "diagnostic-candidate-schema-gate-v1", "target_schema": "accepted-grounded-detailed-targets-v1",
              "validation_scope": "row target/student_input structure; index, target, row and RGB frame hashes; identity and commit pins",
              "training_admission_granted": False, "source_targets_modified": False,
              "candidate_index": {"path": str(index_path), "sha256": hashlib.sha256(payload).hexdigest()},
              "total": len(parsed), "passed": len(valid), "failed": failed, "failure_fraction": failed / len(parsed),
              "threshold": "stop only when failures exceed one percent", "status": status, "failures": failures,
              "target_files_hash_verified": target_hashes, "row_files_hash_verified": row_hashes,
              "unique_frame_files_verified": sum(value is None for value in frame_cache.values()),
              "elapsed_seconds": time.monotonic() - started}
    return report, valid


def heartbeat(output, step, done, doing, next_step, blockers):
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with (output / "HEARTBEAT.log").open("a") as stream:
        stream.write(f"{stamp} | {step}\n")
    (output / "PROGRESS.md").write_text(
        f"# Diagnostic fine-tuning progress\n\nUpdated: {stamp}. Status: diagnostic, provisional.\n\n"
        f"## Done\n{done}\n\n## Doing\n{doing}\n\n## Next\n{next_step}\n\n## Blockers\n{blockers}\n")


def write_new(path, payload):
    with Path(path).open("xb") as stream:
        stream.write(payload)


def schema_gate(params_path, output):
    output = Path(output).resolve()
    if not output.is_dir():
        raise ValueError("Output root must already exist")
    params = parse_params(params_path)
    blockers = "- The supplied trainer pins another host and a fixed legacy conversion pool. No gates have been bypassed."
    heartbeat(output, "Validating candidate schema and pinned target frames", "- Validated lane parameters and created the trainer worktree.",
              "- Hash every indexed target, row and referenced RGB frame.", "- Freeze the scene-disjoint division if the schema gate passes.", blockers)

    def progress(current, total, failed):
        heartbeat(output, f"Schema gate checked {current} of {total} rows", "- Validated parameters; only OneThinker is selected.",
                  f"- Checked {current}/{total} rows; {failed} failures so far.", "- Record every failing qid before proceeding.", blockers)
        print(json.dumps({"checked": current, "total": total, "failed": failed}), flush=True)

    report, valid = gate_candidates(params["CANDIDATE_INDEX"], progress)
    report.update(label=params["label"], admission_verdict=params["admission_line"], params=binding(params_path),
                  students=params["STUDENTS"], recorded_at=datetime.now(timezone.utc).isoformat())
    if report["status"] != "STOP":
        index = output / "validated_index.jsonl"
        write_new(index, b"".join((json.dumps(row, sort_keys=True) + "\n").encode() for row in valid))
        report["validated_index"] = binding(index)
    write_new(output / "SCHEMA_GATE.json", canonical_bytes(report))
    lines = ["# Schema gate", "", f"Status: {params['label']}.", "",
             f"Result: **{report['status']}**; {report['passed']}/{report['total']} rows pass; {report['failed']} fail.",
             f"The stop threshold is strictly greater than 1%; observed failures: {report['failure_fraction']:.6%}.",
             f"Verified {report['target_files_hash_verified']} target hashes, {report['row_files_hash_verified']} row hashes and {report['unique_frame_files_verified']} unique RGB-frame files.",
             "This gate checks the requested row contract; it does not confer the trainer's independent-review admission.",
             "Targets remain unchanged. A single terminal newline in a text file is accepted as serialization, not added to row.target.",
             f"Input SHA256: `{report['candidate_index']['sha256']}`.", "", "## Failing rows", "", "| Qid | Index line | Reason |", "|---|---:|---|"]
    lines.extend(f"| {item['qid']} | {item['line']} | {item['reason'].replace('|', '/')} |" for item in report["failures"])
    if not report["failures"]:
        lines.append("| None | — | No failures. |")
    write_new(output / "SCHEMA_GATE.md", ("\n".join(lines) + "\n").encode())
    print(json.dumps({key: report[key] for key in ("status", "total", "passed", "failed", "unique_frame_files_verified", "elapsed_seconds")}), flush=True)
    return 3 if report["status"] == "STOP" else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only candidate verification for the explicitly provisional fine-tuning lane")
    sub = parser.add_subparsers(dest="command", required=True)
    gate = sub.add_parser("schema-gate")
    gate.add_argument("--params", required=True)
    gate.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    return schema_gate(args.params, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
