import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from . import conversion
from .common import binding, canonical_bytes, digest_json, load_json


RULE_VERSION = "answer-envelope-infra-v1"


def local_file(root, relative):
    path = root / relative
    if path.is_symlink() or not path.resolve().is_relative_to(root):
        raise ValueError("Archive files must stay inside the supplied run directory")
    return path


def publish_sidecar(path, value):
    data = canonical_bytes(value)
    if path.is_symlink():
        raise ValueError("A re-decision output cannot be a symlink")
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f"Refusing to overwrite a re-decision; use a new revision/output: {path}")
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
    return path


def archived_payload(request):
    contents = request["contents"]
    if request.get("model") != conversion.MODEL or len(contents) != 1 or contents[0]["role"] != "user" or len(contents[0]["parts"]) != 1:
        raise ValueError("Unexpected archived converter request envelope")
    part = contents[0]["parts"][0]
    if set(part) != {"text"}:
        raise ValueError("Expected the exact archived text-only request")
    payload = json.loads(part["text"])
    if set(payload) != {"question", "options", "native_final_provenance", "frame_metadata", "evidence"}:
        raise ValueError("Archived converter payload is not the allowlisted projection")
    return payload


def redecide(run_directory, output, revision="envelope-infra-v1"):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", revision):
        raise ValueError("Use a simple revision name, not a path")
    run_directory = Path(run_directory).resolve()
    output = Path(output).absolute()
    run_path = local_file(run_directory, "run.json")
    header = load_json(run_path)
    if header.get("schema") != "grounded-conversion-run-v1":
        raise ValueError("Not an archived grounded conversion run")
    rule = {"version": RULE_VERSION,
            "source": [binding(Path(conversion.__file__)), binding(Path(__file__))]}
    directories = sorted((path for path in run_directory.iterdir() if re.fullmatch(r"[0-9]+", path.name) and path.is_dir()),
                         key=lambda path: int(path.name))
    if not directories:
        raise ValueError("No archived per-question responses found")
    summary_path = local_file(run_directory, "summary.json")
    original_summary = load_json(summary_path) if summary_path.exists() else None
    if original_summary is not None and original_summary.get("scheduled") != len(directories):
        raise ValueError("Archived run membership is incomplete")
    plans, results = [], []
    for directory in directories:
        directory = local_file(run_directory, directory.name)
        prior_path = local_file(run_directory, f"{directory.name}/decision.json")
        prior = load_json(prior_path)
        if prior.get("qid") != directory.name:
            raise ValueError("Archived question identity changed")
        request_path = local_file(run_directory, f"{directory.name}/request.json")
        provider_path = local_file(run_directory, f"{directory.name}/provider.json")
        started_path = local_file(run_directory, f"{directory.name}/started.json")
        request_pin = binding(request_path, prior["request"]["sha256"])
        provider_pin = binding(provider_path, prior["provider"]["sha256"])
        request, response, started = load_json(request_path), load_json(provider_path), load_json(started_path)
        if digest_json(request) != prior["request_sha256"] or started["request_sha256"] != prior["request_sha256"]:
            raise ValueError("Archived request/start binding changed")
        count = prior.get("attempt_count", 1)
        if type(count) is not int or not 1 <= count <= conversion.RETRY_POLICY["max_attempts"]:
            raise ValueError("Archived attempt count exceeds the bounded policy")
        attempts = prior.get("attempts", [])
        if count != len(attempts) and (attempts or count != 1):
            raise ValueError("Archived attempt count is inconsistent")
        for index, pin in enumerate(attempts, 1):
            attempt_path = local_file(run_directory, f"{directory.name}/attempts/{index:03d}/decision.json")
            binding(attempt_path, pin["sha256"])
            attempt = load_json(attempt_path)
            for name in ("request", "provider"):
                binding(local_file(run_directory, f"{directory.name}/attempts/{index:03d}/{name}.json"), attempt[name]["sha256"])
            if attempt["attempt"] != index or attempt["qid"] != directory.name:
                raise ValueError("Archived attempt identity changed")
        if attempts and attempt["provider"]["sha256"] != provider_pin["sha256"]:
            raise ValueError("Archived terminal provider is not the last attempt")
        decision, candidate = conversion.response_decision(response, archived_payload(request), "v1")
        record = {"schema": "offline-conversion-redecision-v1", "qid": directory.name,
                  "rule": rule, "original_decision": binding(prior_path), "run": binding(run_path),
                  "request": request_pin, "provider": provider_pin, "started": binding(started_path),
                  "request_sha256": prior["request_sha256"], "sources": prior["sources"],
                  "attempt_count": count, "provider_calls": 0, "training_eligible": False,
                  "source_authorities_revalidated": False, **decision}
        if candidate is not None:
            candidate_path = local_file(run_directory, f"{directory.name}/candidate.redecision.{revision}.json")
            plans.append((candidate_path, candidate))
            record["candidate"] = {"path": str(candidate_path), "sha256": digest_json(candidate)}
        if record["status"] == "INFRA_REQUEUE":
            now = datetime.fromisoformat(started["started_at"].replace("Z", "+00:00"))
            if now.tzinfo is None:
                raise ValueError("Archived start timestamp must include its timezone")
            record.update(retry_policy=conversion.RETRY_POLICY, retry_exhausted=count == conversion.RETRY_POLICY["max_attempts"],
                          retry_after_seconds=conversion.retry_delay_seconds(response, count, now),
                          remaining_attempts=conversion.RETRY_POLICY["max_attempts"] - count,
                          retry_requires_new_supervisor_admission=True)
            record["unavailable_provider_diagnostics"] = [key for key in (
                "status_code", "response_body", "response_headers", "retry_after", "elapsed_ms",
                "requested_model", "provider_served_model") if response.get(key) is None]
        decision_path = local_file(run_directory, f"{directory.name}/decision.redecision.{revision}.json")
        plans.append((decision_path, record))
        results.append({"qid": directory.name, "status": record["status"], "reason": record.get("reason"),
                        "decision": {"path": str(decision_path), "sha256": digest_json(record)}})
    summary = {"schema": "offline-conversion-redecision-summary-v1", "run": binding(run_path), "rule": rule,
               "questions": len(results), "counts": dict(Counter(row["status"] for row in results)),
               "results": results, "provider_calls": 0, "accepted_targets": 0,
               "training_eligible": False, "source_authorities_revalidated": False}
    plans.append((output, summary))
    if len({str(path.resolve()) for path, _ in plans}) != len(plans):
        raise ValueError("Re-decision output paths collide")
    for path, value in plans:
        if path.is_symlink() or path.exists() and path.read_bytes() != canonical_bytes(value):
            raise ValueError(f"Refusing to overwrite an artifact: {path}; use a new revision/output")
    for path, value in plans:
        publish_sidecar(path, value)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description="Re-decide archived conversion responses offline; never call a provider or admit a target")
    parser.add_argument("--run", required=True)
    parser.add_argument("--output", required=True, help="New immutable summary JSON path")
    parser.add_argument("--revision", default="envelope-infra-v1", help="Namespace for new decision/candidate sidecars")
    args = parser.parse_args(argv)
    result = redecide(args.run, args.output, args.revision)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"BLOCKED: {type(error).__name__}: {error}", file=sys.stderr)
        sys.exit(2)
