import copy
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from PIL import Image


SOURCES = Path(__file__).parent / "fixtures/dataset_builder_sources.json"
SENTENCES = (
    "This synthetic explanation describes a packaging fixture rather than a solved scene.",
    "The synthetic observation is supplied only to exercise the stored citation boundary.",
    "The fixture preserves the recorded answer without calculating any new measurement.",
    "The synthetic conclusion checks serialization and makes no claim about the depicted scene.",
)
PURPOSES = ("setup", "observations", "derivation", "conclusion")


def canonical(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(value if isinstance(value, bytes) else canonical(value))
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def fixture_directory(label):
    root = Path(os.environ["STUDENT_DATASET_TEST_OUTPUT"]).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=label + "_", dir=root))


def make_fixture(root, count=3):
    sources = json.loads(SOURCES.read_text())["source_requests"][:count]
    entries, bindings, targets = [], [], []
    for number, source in enumerate(sources):
        identity = source["identity"]
        directory = root / identity["qid"]
        directory.mkdir(parents=True)
        frames = []
        for position in range(32):
            image = Image.new("RGB", (32, 32), (position * 7, number * 60, 255 - position * 5))
            path = directory / f"rgb_{position:02d}.png"
            image.save(path)
            frames.append({"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        payload = copy.deepcopy(source["payload"])
        evidence_text = " ".join(SENTENCES)
        evidence = {"id": "e9000", "kind": "archived_tool_result", "source_pointer": "/fixture/synthetic_evidence",
                    "text": evidence_text, "text_sha256": hashlib.sha256(evidence_text.encode()).hexdigest()}
        payload["evidence"] = [evidence, {"id": "e9001", "kind": "assistant_tool_argument",
            "source_pointer": "/fixture/leakage_sentinel", "text": "planner execute_python_code (1.25, -2.0, 3e2) teacher measurement 987.654 meters",
            "text_sha256": hashlib.sha256(b"planner execute_python_code (1.25, -2.0, 3e2) teacher measurement 987.654 meters").hexdigest()}]
        request = {"converter_version": "v2", "contents": [{"role": "user", "parts": [{"text": canonical(payload).decode()}]}]}
        request_pin = save(directory / "request.json", request)
        answer = re.fullmatch(r"<ANSWER>(.*?)</ANSWER>", payload["native_final_provenance"], flags=re.S).group(1)
        terminal = save(directory / "terminal.json", {"question_id": identity["qid"], "episode_id": identity["qid"] + "__fixture", "return_code": 0, "fixture_only": True})
        metadata = {key: payload["frame_metadata"][key] for key in ("frame_indices", "timestamps", "fps", "total_num_frames")}
        binding = {"schema": "student-source-binding-v1", "source_pool": "synthetic-fixture", "fixture_only": True,
                   **identity, "native_answer": answer, "request": request_pin, "source_terminal": terminal,
                   "student_input": {"question": payload["question"], "options": payload["options"], "frames": frames, **metadata}}
        binding_pin = save(directory / "binding.json", binding)
        claims, paragraphs = [], []
        for i, (purpose, text) in enumerate(zip(PURPOSES, SENTENCES), 1):
            start = evidence_text.index(text)
            claims.append({"id": f"c{i}", "text": text, "citations": [{"evidence_id": "e9000", "start": start,
                           "end": start + len(text), "quote": text, "source_pointer": evidence["source_pointer"],
                           "evidence_kind": evidence["kind"], "text_sha256": evidence["text_sha256"], "match_method": "exact"}]})
            paragraphs.append({"purpose": purpose, "claim_ids": [f"c{i}"], "text": text})
        text = "\n\n".join(SENTENCES) + "\n\n<answer>" + answer + "</answer>"
        target = {"converter_version": "v2", "answer": answer, "explanation": paragraphs, "claims": claims,
                  "target": text, "target_sha256": hashlib.sha256(text.encode()).hexdigest(),
                  "exact_citations_verified": True, "native_final_agreement": True,
                  "semantic_grounding_verified": False, "training_eligible": False, "fixture_only": True}
        target_pin = save(directory / "target.json", target)
        review = {"schema": "student-target-review-v1", "qid": identity["qid"], "admitted": True,
                  "independent_of_converter": True, "reviewer": "synthetic-test-reviewer", "fixture_only": True,
                  "target": target_pin, "binding": binding_pin, "supported_claim_ids": [c["id"] for c in claims]}
        review_pin = save(directory / "review.json", review)
        entries.append({"admitted": True, "target": target_pin, "binding": binding_pin, "review": review_pin})
        bindings.append(binding)
        targets.append(target)
    index = save(root / "admission.json", {"schema": "student-admission-index-v1", "rows": entries})
    return {"index": Path(index["path"]), "entries": entries, "bindings": bindings, "targets": targets}


def revised_fixture(fixture, root, entry_index=0, binding_update=None, target_update=None, entry_update=None, review_update=None):
    root.mkdir(parents=True, exist_ok=True)
    entries = copy.deepcopy(fixture["entries"])
    entry = entries[entry_index]
    binding = copy.deepcopy(fixture["bindings"][entry_index])
    target = copy.deepcopy(fixture["targets"][entry_index])
    if binding_update:
        binding_update(binding)
    if target_update:
        target_update(target)
    entry["binding"] = save(root / "binding.json", binding)
    entry["target"] = save(root / "target.json", target)
    review = {"schema": "student-target-review-v1", "qid": binding["qid"], "admitted": True,
              "independent_of_converter": True, "reviewer": "synthetic-test-reviewer", "fixture_only": True,
              "binding": entry["binding"], "target": entry["target"], "supported_claim_ids": [c["id"] for c in target["claims"]]}
    if review_update:
        review_update(review)
    entry["review"] = save(root / "review.json", review)
    if entry_update:
        entry_update(entry)
    index = save(root / "admission.json", {"schema": "student-admission-index-v1", "rows": entries})
    return Path(index["path"])


def cloned_entry(fixture, root, qid="3919_repeat", scene="scene0643_01", change_options=False, answer=None):
    binding = copy.deepcopy(fixture["bindings"][0])
    target = copy.deepcopy(fixture["targets"][0])
    binding.update(qid=qid, scene=scene)
    question = "  " + binding["student_input"]["question"].upper().replace(" ", "\t") + "\n"
    binding["student_input"]["question"] = question
    request = json.loads(Path(binding["request"]["path"]).read_text())
    payload = json.loads(request["contents"][0]["parts"][0]["text"])
    payload["question"] = question
    if change_options:
        binding["student_input"]["options"] = payload["options"] = ["A. Synthetic alternative", "B. Another synthetic alternative"]
    if answer is not None:
        binding["native_answer"] = target["answer"] = answer
        payload["native_final_provenance"] = "<ANSWER>" + answer + "</ANSWER>"
        target["target"] = "\n\n".join(SENTENCES) + "\n\n<answer>" + answer + "</answer>"
        target["target_sha256"] = hashlib.sha256(target["target"].encode()).hexdigest()
    request["contents"][0]["parts"][0]["text"] = canonical(payload).decode()
    binding["request"] = save(root / "request.json", request)
    binding["source_terminal"] = save(root / "terminal.json", {"question_id": qid, "return_code": 0, "fixture_only": True})
    binding_pin = save(root / "binding.json", binding)
    target_pin = save(root / "target.json", target)
    review = save(root / "review.json", {"schema": "student-target-review-v1", "qid": qid, "admitted": True,
                  "independent_of_converter": True, "reviewer": "synthetic-test-reviewer", "fixture_only": True,
                  "target": target_pin, "binding": binding_pin, "supported_claim_ids": [c["id"] for c in target["claims"]]})
    return {"admitted": True, "target": target_pin, "binding": binding_pin, "review": review}
