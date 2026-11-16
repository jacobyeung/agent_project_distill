import argparse
import json
import os
import re
from collections import Counter
from pathlib import Path

from . import conversion, conversion_v2
from .common import binding, canonical_bytes, digest_json, load_json


def scoped_path(path, root):
    path = Path(path).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Offline dry-run paths must stay inside the explicitly allowed workspace")
    return path


def check_request_boundary(request):
    if set(request) != {"converter_version", "model", "config", "contents"} or request["converter_version"] != "v2":
        raise ValueError("Unexpected dry-run request envelope")
    if request["model"] != conversion.MODEL or request["config"] != conversion.request_config("v2"):
        raise ValueError("Dry-run provider settings or schema changed")
    contents = request["contents"]
    if len(contents) != 1 or set(contents[0]) != {"role", "parts"} or contents[0]["role"] != "user" or len(contents[0]["parts"]) != 1 or set(contents[0]["parts"][0]) != {"text"}:
        raise ValueError("Unexpected dry-run content envelope")
    payload = json.loads(contents[0]["parts"][0]["text"])
    conversion_v2.check_boundary_fields(payload)
    if set(payload) != conversion_v2.PAYLOAD_FIELDS | {"conversion_contract"}:
        raise ValueError("request_boundary: unexpected model-visible payload fields")
    original = {key: payload[key] for key in conversion_v2.PAYLOAD_FIELDS}
    original["evidence"] = [{key: value for key, value in item.items() if key != "evidence_role"} for item in payload["evidence"]]
    if canonical_bytes(conversion_v2.request_payload(original)).decode() != contents[0]["parts"][0]["text"]:
        raise ValueError("request_boundary: payload is not the exact allowlisted projection")
    return {"passed": True, "converter_version": "v2", "request_sha256": digest_json(request),
            "forbidden_fields_found": [], "payload_fields": sorted(payload),
            "evidence_kind_counts": dict(Counter(item["kind"] for item in payload["evidence"])),
            "scope": "Model-visible structured fields only; teacher evidence text is preserved verbatim, not interpreted as labels or instructions."}


def build_dry_run(job_path, contexts_directory, output, workspace_root):
    if os.environ.get("PYTHONDONTWRITEBYTECODE") != "1":
        raise ValueError("Set PYTHONDONTWRITEBYTECODE=1 for the offline dry run")
    root = Path(workspace_root).resolve()
    job_path, contexts_directory, output = [scoped_path(path, root) for path in (job_path, contexts_directory, output)]
    if output.exists() or not output.parent.is_dir():
        raise ValueError("Choose a new output directory whose workspace parent already exists")
    job = load_json(job_path)
    if job.get("schema") != "grounded-conversion-job-v1" or job.get("model") != conversion.MODEL or job.get("settings") != conversion.SETTINGS:
        raise ValueError("Source job is not the pinned converter contract")
    qids = job["selected_qids"]
    if not qids or len(set(qids)) != len(qids) or any(not isinstance(qid, str) or not re.fullmatch(r"[0-9]+", qid) for qid in qids) or [item["qid"] for item in job["contexts"]] != qids:
        raise ValueError("Source job identities are not unique, safe, and ordered")
    prepared = []
    for item in job["contexts"]:
        qid = item["qid"]
        path = scoped_path(contexts_directory / f"{qid}.json", root)
        source_pin = binding(path, item["context"]["sha256"])
        context = load_json(path)
        version = conversion.context_version(context)
        if version != job.get("converter_version", "v1"):
            raise ValueError("Source job and context versions disagree")
        expected = conversion.make_request(context["payload"], version)
        if "converter_version" not in context["request"] and version == "v1":
            expected.pop("converter_version")
        if context["request"] != expected or digest_json(expected) != item["request_sha256"] or context["request_sha256"] != item["request_sha256"]:
            raise ValueError("Source request no longer matches its archived binding")
        if context["row"]["qid"] != qid or context["payload"]["native_final_provenance"] != context["row"]["native_answer_archive"]["native_final"]:
            raise ValueError("Source identity or native final changed")
        request = conversion.make_request(context["payload"], "v2")
        prepared.append((qid, source_pin, request, check_request_boundary(request)))
    output.mkdir()

    def save(path, value):
        data = value.encode() if isinstance(value, str) else canonical_bytes(value)
        with path.open("xb") as stream:
            stream.write(data)
        return binding(path)

    rows = []
    for qid, source_pin, request, boundary in prepared:
        directory = output / qid
        directory.mkdir()
        prompt = request["config"]["system_instruction"] + "\n\n--- USER PAYLOAD ---\n\n" + request["contents"][0]["parts"][0]["text"]
        rows.append({"qid": qid, "source_context": source_pin,
                     "request": save(directory / "request.json", request),
                     "rendered_prompt": save(directory / "prompt.txt", prompt),
                     "request_boundary": save(directory / "request_boundary.json", boundary)})
    save(output / "SYSTEM_PROMPT.txt", conversion_v2.SYSTEM + "\n")
    save(output / "RESPONSE_SCHEMA.json", conversion_v2.RESPONSE_SCHEMA)
    save(output / "CONTRACT.json", conversion_v2.CONTRACT)
    receipt = {"schema": "grounded-conversion-offline-dry-run-v2", "converter_version": "v2",
               "source_job": binding(job_path), "selected_qids": qids, "requests": rows,
               "provider_calls": 0, "training_eligible": False, "launch_admitted": False,
               "source_authorities_revalidated": False,
               "scope": "Verified the supplied workspace copies and rebuilt requests only; did not dereference external source, RGB, scoring, runtime, or lease paths.",
               "runtime": [binding(Path(__file__).parent / name) for name in ("conversion.py", "conversion_v2.py", "conversion_dry_run.py", "common.py", "admission.py", "split.py")]}
    save(output / "manifest.json", receipt)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description="Rebuild grounded v2 requests from local archived contexts; no provider or launch path")
    parser.add_argument("--job", required=True)
    parser.add_argument("--contexts", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--workspace-root", required=True)
    args = parser.parse_args(argv)
    receipt = build_dry_run(args.job, args.contexts, args.output, args.workspace_root)
    print(json.dumps({"status": "DRY_RUN_NO_PROVIDER_CALLS", "selected_qids": receipt["selected_qids"],
                      "manifest": str(Path(args.output) / "manifest.json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
