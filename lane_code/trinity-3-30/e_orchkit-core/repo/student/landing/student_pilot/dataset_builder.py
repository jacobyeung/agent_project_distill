import argparse
import hashlib
import io
import json
import math
import os
import re
import unicodedata
from collections import Counter
from pathlib import Path

from PIL import Image

from .common import canonical_bytes, digest_json
from .split import physical_group


SCHEMA = "student-rgb32-training-shards-v1"
INPUT_FIELDS = {"question", "options", "frames", "frame_indices", "timestamps", "fps", "total_num_frames"}
PURPOSES = {"setup", "observations", "derivation", "qualifications", "conclusion"}
TOOL_WORDS = (
    "tool", "tools", "planner", "code", "python", "function", "functions", "api", "sam3", "mapanything", "unik3d",
    "find_frames_with_object", "predict_2d_segmentation_masks_video", "predict_2d_segmentation_masks",
    "predict_2d_points", "predict_2d_bounding_box", "execute_python_code", "verify_plan_pre_execution",
    "verify_plan_post_execution", "teacher measurement", "teacher measurements",
)
NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
TRIPLE = re.compile(r"[\[(]\s*" + NUMBER + r"\s*,\s*" + NUMBER + r"\s*,\s*" + NUMBER + r"\s*[\])]")
AXES = re.compile(r"\bx\s*[:=]\s*" + NUMBER + r"[\s,;]+y\s*[:=]\s*" + NUMBER + r"[\s,;]+z\s*[:=]\s*" + NUMBER, re.I)
IDENTIFIER = re.compile(r"\b[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+\b")
ARTIFACT = re.compile(r"```|<[^>]+>|data:image|(?:/data2/|/home/)|\be\d{3,}\b|\bevidence[_ -]?id\b", re.I)
SHA256 = re.compile(r"[0-9a-f]{64}")


class DatasetBuildError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise DatasetBuildError(message)


def text_sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scoped_path(path, workspace_root, base=None):
    require(isinstance(path, (str, Path)) and bool(str(path)), "A nonempty local path is required")
    root = Path(workspace_root).absolute()
    candidate = Path(os.path.abspath(Path(base or root) / path))
    require(candidate.is_relative_to(root), f"Path is outside the allowed workspace: {candidate}")
    resolved = candidate.resolve()
    require(resolved.is_relative_to(root.resolve()), f"Symlink escapes the allowed workspace: {candidate}")
    return resolved


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json(data):
    def invalid_constant(value):
        raise DatasetBuildError(f"Nonfinite JSON number: {value}")

    try:
        return json.loads(data, object_pairs_hook=_unique_object, parse_constant=invalid_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetBuildError(f"Invalid UTF-8 JSON: {error}") from error


def read_pin(pin, workspace_root, base):
    require(isinstance(pin, dict) and isinstance(pin.get("sha256"), str) and SHA256.fullmatch(pin["sha256"]),
            "Every source file requires a SHA-256 binding")
    path = scoped_path(pin.get("path", ""), workspace_root, base)
    require(path.is_file(), f"Bound source file is unavailable: {path}")
    data = path.read_bytes()
    require(hashlib.sha256(data).hexdigest() == pin["sha256"], f"Source SHA-256 mismatch: {path}")
    if "size_bytes" in pin:
        require(type(pin["size_bytes"]) is int and len(data) == pin["size_bytes"], f"Source size mismatch: {path}")
    return data, {"path": str(path), "sha256": pin["sha256"]}


def bound_json(pin, workspace_root, base):
    data, resolved = read_pin(pin, workspace_root, base)
    return parse_json(data), resolved


def bare_answer(value):
    require(isinstance(value, str) and bool(value.strip()), "Target requires a nonempty bare-body answer")
    require(not re.search(r"<\s*/?\s*answer\b|<\|[^>]+\|>", value, re.I), "Answer must be a bare body, not an envelope or control token")
    return value


def native_answer(value):
    require(isinstance(value, str), "Native answer provenance must be a string")
    match = re.fullmatch(r"\s*<answer>(.*?)</answer>\s*", value, re.I | re.S)
    return bare_answer(match.group(1) if match else value)


def validate_prompt(question, options, evidence_ids=(), tool_names=()):
    require(isinstance(question, str) and bool(question.strip()), "Question must be a nonempty source string")
    require(options is None or isinstance(options, list) and all(isinstance(value, str) for value in options),
            "Options must be source strings or null")
    text = question + ("\n" + "\n".join(options) if options else "")
    require(not ARTIFACT.search(text) and not TRIPLE.search(text) and not AXES.search(text) and not IDENTIFIER.search(text),
            "Prompt-side leakage: code, coordinates, evidence IDs, paths, or control tokens")
    for token in (*TOOL_WORDS, *evidence_ids, *tool_names):
        if token and re.search(r"(?<!\w)" + re.escape(token) + r"(?!\w)", text, re.I):
            raise DatasetBuildError(f"Prompt-side leakage: forbidden reference {token!r}")
    return text


def _target_structure(target):
    require(isinstance(target, dict) and target.get("converter_version") == "v2", "Expected a code-resolved converter v2 target")
    answer = bare_answer(target.get("answer"))
    claims, paragraphs = target.get("claims"), target.get("explanation")
    require(isinstance(claims, list) and 4 <= len(claims) <= 128, "A detailed target requires 4 to 128 code-resolved claims")
    require(isinstance(paragraphs, list) and 4 <= len(paragraphs) <= 64, "A detailed target requires 4 to 64 explanation paragraphs")
    require(all(isinstance(claim, dict) and claim.get("id") == f"c{i}" for i, claim in enumerate(claims, 1)),
            "Claim IDs must follow converter reading order")
    by_id = {claim["id"]: claim for claim in claims}
    for claim in claims:
        text = claim.get("text")
        require(isinstance(text, str) and bool(text.strip()) and text == text.strip(), "Claim text must be unchanged nonempty prose")
        validate_prompt(text, [])
        require(isinstance(claim.get("citations"), list) and bool(claim["citations"]), "Every claim requires code-resolved citations")
        for citation in claim["citations"]:
            require(isinstance(citation, dict) and isinstance(citation.get("evidence_id"), str)
                    and type(citation.get("start")) is int and type(citation.get("end")) is int
                    and 0 <= citation["start"] < citation["end"] and isinstance(citation.get("quote"), str)
                    and citation["end"] - citation["start"] == len(citation["quote"]), "Citation offsets are missing or invalid")
    purposes, ordered_ids, texts = [], [], []
    for paragraph in paragraphs:
        require(isinstance(paragraph, dict) and paragraph.get("purpose") in PURPOSES
                and isinstance(paragraph.get("claim_ids"), list) and bool(paragraph["claim_ids"]), "Invalid resolved paragraph schema")
        ids = paragraph["claim_ids"]
        require(all(isinstance(cid, str) and cid in by_id for cid in ids), "Paragraph refers to an unknown claim")
        text = " ".join(by_id[cid]["text"] for cid in ids)
        require(paragraph.get("text") == text, "Paragraph text differs from its ordered claims")
        purposes.append(paragraph["purpose"])
        ordered_ids.extend(ids)
        texts.append(text)
    require(ordered_ids == list(by_id), "Paragraphs must include every claim exactly once in reading order")
    require(purposes[0] == "setup" and purposes[-1] == "conclusion"
            and {"setup", "observations", "derivation", "conclusion"} <= set(purposes), "Detailed explanation purposes are missing or out of order")
    original = "\n\n".join(texts) + "\n\n<answer>" + answer + "</answer>"
    require("target" not in target or target["target"] == original, "Converter target differs from paragraph rendering")
    require("target_sha256" not in target or target["target_sha256"] == text_sha256(original), "Converter target text hash differs")
    return texts, answer


def render_target(target, answer_tag="ANSWER"):
    require(answer_tag in ("ANSWER", "answer"), "Answer tag must be explicitly ANSWER or answer")
    paragraphs, answer = _target_structure(target)
    return "\n\n".join(paragraphs) + f"\n\n<{answer_tag}>" + answer + f"</{answer_tag}>"


def canonical_scene(dataset, scene):
    require(isinstance(dataset, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.+-]*", dataset), "A source dataset identity is required")
    require(isinstance(scene, str) and bool(scene) and all(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.+-]*", part)
            and part not in (".", "..") for part in scene.split("/")), "A physical scene identity is required")
    dataset = dataset.casefold()
    for separator in ("/", "__"):
        if scene.casefold().startswith(dataset + separator):
            scene = scene[len(dataset) + len(separator):]
    if dataset == "scannet":
        scene = scene.casefold()
    return physical_group(dataset, scene)


def scene_partition(physical_scene_id, seed=17, validation_fraction=0.1):
    require(type(seed) is int, "Split seed must be an integer")
    require(type(validation_fraction) in (int, float) and math.isfinite(validation_fraction) and 0 < validation_fraction < 1,
            "Validation fraction must lie strictly between zero and one")
    require(isinstance(physical_scene_id, str) and "/" in physical_scene_id, "Scene IDs must be namespaced by dataset")
    dataset, scene = physical_scene_id.split("/", 1)
    group = canonical_scene(dataset, scene)
    score = int(digest_json(["student-scene-split-v1", seed, group]), 16)
    return "validation" if score < int(validation_fraction * 2**256) else "train"


def _request_payload(request):
    require(isinstance(request, dict) and request.get("converter_version") == "v2", "Source request is not converter v2")
    contents = request.get("contents")
    require(isinstance(contents, list) and len(contents) == 1 and isinstance(contents[0], dict)
            and contents[0].get("role") == "user", "Source request user envelope is malformed")
    parts = contents[0].get("parts")
    require(isinstance(parts, list) and len(parts) == 1 and isinstance(parts[0], dict)
            and set(parts[0]) == {"text"} and isinstance(parts[0]["text"], str), "Source request payload is malformed")
    payload = parse_json(parts[0]["text"])
    require(isinstance(payload, dict), "Source request payload must be an object")
    return payload


def _validate_citations(target, payload):
    require(isinstance(payload.get("evidence"), list), "Source request has no evidence list")
    evidence = {}
    for item in payload["evidence"]:
        require(isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"] not in evidence
                and isinstance(item.get("text"), str) and item.get("text_sha256") == text_sha256(item["text"]),
                "Evidence identity or text hash is invalid")
        evidence[item["id"]] = item
    cited_kinds = set()
    for claim in target["claims"]:
        for citation in claim["citations"]:
            item = evidence.get(citation["evidence_id"])
            require(item is not None and citation["end"] <= len(item["text"])
                    and item["text"][citation["start"]:citation["end"]] == citation["quote"], "Resolved citation disagrees with bound evidence")
            for key, expected in (("text_sha256", item["text_sha256"]), ("source_pointer", item.get("source_pointer")), ("evidence_kind", item.get("kind"))):
                require(citation.get(key) == expected, f"Resolved citation {key} differs from bound evidence")
            cited_kinds.add(item.get("kind"))
    require(cited_kinds & {"archived_tool_result", "assistant_tool_argument", "provider_thought_summary"},
            "Question/options alone cannot support an explanation")
    return evidence


def _frames(inputs, root, base, media):
    frames, indices, timestamps = inputs.get("frames"), inputs.get("frame_indices"), inputs.get("timestamps")
    require(all(isinstance(items, list) and len(items) == 32 for items in (frames, indices, timestamps)),
            "Each example requires exactly 32 RGB frames, indices, and timestamps")
    require(all(type(index) is int and index >= 0 for index in indices) and all(a < b for a, b in zip(indices, indices[1:])),
            "Original frame indices must be unique and increasing")
    fps = inputs.get("fps")
    require(type(fps) in (int, float) and math.isfinite(fps) and fps > 0, "Original positive FPS is required")
    require(type(inputs.get("total_num_frames")) is int and inputs["total_num_frames"] > indices[-1], "Original frame count is invalid")
    require(all(type(stamp) in (int, float) and math.isfinite(stamp) and math.isclose(stamp, index / fps, rel_tol=0, abs_tol=1e-6)
                for stamp, index in zip(timestamps, indices)), "Original timestamps and frame indices/FPS disagree")
    packed, order, sizes = [], [], []
    cache = media.setdefault("verified", {})
    files = media.setdefault("files", {})
    for position, pin in enumerate(frames):
        require(isinstance(pin, dict) and isinstance(pin.get("sha256"), str) and SHA256.fullmatch(pin["sha256"]), "Every frame requires a SHA-256 binding")
        path = scoped_path(pin.get("path", ""), root, base)
        state = path.stat()
        if "size_bytes" in pin:
            require(type(pin["size_bytes"]) is int and pin["size_bytes"] == state.st_size, "Frame size binding mismatch")
        key = (str(path), pin["sha256"], state.st_dev, state.st_ino, state.st_size, state.st_mtime_ns, state.st_ctime_ns)
        if key not in cache:
            data, source = read_pin(pin, root, base)
            try:
                with Image.open(io.BytesIO(data)) as image:
                    require(image.mode == "RGB" and getattr(image, "n_frames", 1) == 1, "Every frame must be a single authenticated RGB image")
                    suffix = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}.get(image.format)
                    require(suffix is not None, "RGB frame format must be PNG, JPEG, or WEBP")
                    size = list(image.size)
                    image.load()
            except (OSError, SyntaxError, Image.DecompressionBombError) as error:
                raise DatasetBuildError(f"Frame is not a decodable RGB image: {source['path']}") from error
            cache[key] = source, suffix, size
        source, suffix, size = cache[key]
        digest = source["sha256"]
        name = f"media/{digest}{suffix}"
        files.setdefault(name, source)
        packed.append({"path": name, "sha256": digest})
        order.append({"position": position, "original_frame_index": indices[position], "timestamp": timestamps[position], "sha256": digest})
        sizes.append(size)
    require(len({tuple(size) for size in sizes}) == 1, "Original frame resolutions must agree for the smoke video encoder")
    return packed, order, sizes


def _check_review(entry, target, binding, target_pin, binding_pin, root, base):
    require(entry.get("admitted") is True, "Only explicitly admitted targets may be packaged")
    review, review_pin = bound_json(entry.get("review"), root, base)
    require(isinstance(review, dict) and review.get("schema") == "student-target-review-v1"
            and review.get("admitted") is True and review.get("independent_of_converter") is True
            and isinstance(review.get("reviewer"), str) and bool(review["reviewer"].strip()), "An independent admission review is required")
    require(review.get("qid") == binding["qid"], "Review question identity mismatch")
    for key, expected in (("target", target_pin), ("binding", binding_pin)):
        supplied = review.get(key)
        require(isinstance(supplied, dict) and supplied.get("sha256") == expected["sha256"]
                and str(scoped_path(supplied.get("path", ""), root, Path(review_pin["path"]).parent)) == expected["path"],
                f"Review does not bind this exact {key}")
    require(review.get("supported_claim_ids") == [claim["id"] for claim in target["claims"]], "Every claim requires an independent supported verdict")
    return review_pin


def _prepare_entry(entry, root, base, media, answer_tag):
    require(isinstance(entry, dict), "Admission entries must be objects")
    target, target_pin = bound_json(entry.get("target"), root, base)
    binding, binding_pin = bound_json(entry.get("binding"), root, base)
    require(isinstance(binding, dict) and binding.get("schema") == "student-source-binding-v1", "Unexpected source binding schema")
    require(isinstance(binding.get("qid"), str) and bool(binding["qid"].strip()), "Source binding requires a question ID")
    _target_structure(target)
    review_pin = _check_review(entry, target, binding, target_pin, binding_pin, root, base)
    return prepare_bound_target(target, target_pin, binding, binding_pin, review_pin, root, media, answer_tag)


def prepare_bound_target(target, target_pin, binding, binding_pin, review_pin, root, media, answer_tag):
    require(isinstance(binding.get("qid"), str) and bool(binding["qid"].strip()), "Source binding requires a question ID")
    fixture = binding.get("fixture_only") is True
    require(fixture or binding.get("source_pool") == "nyu-visionx/VSI-590K", "Production targets must bind the clean VSI-590K source pool")
    require(isinstance(binding.get("category", "unspecified"), str), "Source category must be a string")
    text = render_target(target, answer_tag)
    require(target.get("exact_citations_verified") is True and target.get("native_final_agreement") is True,
            "Only deterministically validated conversion candidates may be admitted")
    source_base = Path(binding_pin["path"]).parent
    request, request_pin = bound_json(binding.get("request"), root, source_base)
    payload = _request_payload(request)
    require(target["answer"] == bare_answer(binding.get("native_answer")) == native_answer(payload.get("native_final_provenance")),
            "Target answer disagrees byte-for-byte with the bound native answer")
    terminal, terminal_pin = bound_json(binding.get("source_terminal"), root, source_base)
    require(isinstance(terminal, dict) and terminal.get("question_id") == binding["qid"]
            and type(terminal.get("return_code")) is int and terminal["return_code"] == 0, "Source terminal identity or completion mismatch")
    inputs = binding.get("student_input")
    require(isinstance(inputs, dict) and set(inputs) == INPUT_FIELDS, "Student input must contain only RGB, question, options, and original timing")
    require(inputs["question"] == payload.get("question") and inputs["options"] == payload.get("options"), "Question/options differ from the bound source request")
    frame_metadata = payload.get("frame_metadata")
    require(isinstance(frame_metadata, dict) and all(inputs[key] == frame_metadata.get(key)
            for key in ("frame_indices", "timestamps", "fps", "total_num_frames")), "Frame timing differs from the bound source request")
    evidence = _validate_citations(target, payload)
    tool_names = {name for item in evidence.values() for name in IDENTIFIER.findall(item["text"])}
    validate_prompt(inputs["question"], inputs["options"], evidence, tool_names)
    group = canonical_scene(binding.get("dataset"), binding.get("scene"))
    require("physical_scene_id" not in binding or binding["physical_scene_id"] == group, "Explicit physical scene identity disagrees with source identity")
    packed, order, sizes = _frames(inputs, root, source_base, media)
    normalized_question = unicodedata.normalize("NFC", " ".join(inputs["question"].split())).casefold()
    return {"qid": binding["qid"], "dataset": binding["dataset"], "scene": binding["scene"], "physical_scene_id": group,
            "category": binding.get("category", "unspecified"), "fixture_only": fixture or target.get("fixture_only") is True,
            "student_input": {**inputs, "frames": packed}, "target_text": text, "answer": target["answer"],
            "dedup_key": digest_json([group, normalized_question]), "frame_order": order, "frame_sizes": sizes,
            "target": target_pin, "binding": binding_pin, "request": request_pin, "review": review_pin, "source_terminal": terminal_pin}


def chat_record(row):
    inputs = row["student_input"]
    prompt = validate_prompt(inputs["question"], inputs["options"])
    return {"qid": row["qid"], "physical_scene_id": row["physical_scene_id"], "split": row["split"], "student_input": inputs,
            "messages": [{"role": "user", "content": [{"type": "image", "image": frame["path"]} for frame in inputs["frames"]]
                          + [{"type": "text", "text": prompt}]}, {"role": "assistant", "content": row["target_text"]}]}


def record_bytes(record):
    return (json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _deduplicate(rows):
    groups, identities, duplicates = {}, {}, []
    for row in sorted(rows, key=lambda value: (value["qid"], value["target"]["sha256"], value["binding"]["sha256"])):
        signature = (row["dedup_key"], digest_json(row["student_input"]["options"] or []), row["answer"])
        require(row["qid"] not in identities or identities[row["qid"]] == signature, "A question ID refers to conflicting scene/question/options/answer bindings")
        identities[row["qid"]] = signature
        if row["dedup_key"] in groups:
            kept = groups[row["dedup_key"]]
            require((kept["student_input"]["options"] or []) == (row["student_input"]["options"] or []) and kept["answer"] == row["answer"],
                    "Duplicate question/scene has conflicting options or native answers")
            duplicates.append({"dedup_key": row["dedup_key"], "kept_qid": kept["qid"], "dropped_qid": row["qid"],
                               "dropped_target": row["target"], "dropped_binding": row["binding"], "dropped_review": row["review"]})
        else:
            groups[row["dedup_key"]] = row
    return sorted(groups.values(), key=lambda row: (row["physical_scene_id"], row["dedup_key"], row["qid"])), duplicates


def split_proof(rows, seed, validation_fraction):
    partitions = {name: [row for row in rows if row["split"] == name] for name in ("train", "validation")}
    train, validation = partitions["train"], partitions["validation"]
    groups = {name: sorted({row["physical_scene_id"] for row in values}) for name, values in partitions.items()}
    qids = {name: sorted(row["qid"] for row in values) for name, values in partitions.items()}
    scene_intersection = sorted(set(groups["train"]) & set(groups["validation"]))
    qid_intersection = sorted(set(qids["train"]) & set(qids["validation"]))
    require(not scene_intersection and not qid_intersection, "Train/validation identities overlap")
    return {"schema": "student-physical-scene-split-proof-v1", "seed": seed, "validation_fraction": validation_fraction,
            "policy": "SHA256(canonical JSON [student-scene-split-v1, seed, physical_scene_id]) < fraction * 2^256 selects validation; no rebalancing",
            "group_policy": "Dataset-namespaced physical scene; ScanNet sceneNNNN scan suffixes share one group",
            "assignment_independent_of_admission_order": True, "selection_uses_correctness": False,
            "validation_scope": "Admitted-target validation loss only; not an unbiased held-out question-answering evaluation",
            "unknown_renamed_or_building_aliases_checked": False, "training_groups": groups["train"], "heldout_groups": groups["validation"],
            "training_qids": qids["train"], "heldout_qids": qids["validation"], "training_questions": len(train), "heldout_questions": len(validation),
            "training_scenes": len(groups["train"]), "heldout_scenes": len(groups["validation"]),
            "scene_intersection": scene_intersection, "qid_intersection": qid_intersection,
            "category_counts": dict(sorted(Counter(row["category"] for row in rows).items())),
            "partition_category_counts": {name: dict(sorted(Counter(row["category"] for row in values).items())) for name, values in partitions.items()}}


def _write_file(path, data):
    with path.open("xb") as stream:
        stream.write(data)
    return {"path": path.name, "sha256": hashlib.sha256(data).hexdigest()}


def build_dataset(admission_index, output, workspace_root, validation_fraction=0.1, seed=17, shard_size=1000, answer_tag="ANSWER", fixture_only=False):
    root = Path(workspace_root).absolute()
    source = scoped_path(admission_index, root, Path.cwd())
    output = scoped_path(output, root, Path.cwd())
    require(not output.exists() and output.parent.is_dir(), "Choose a new output directory with an existing workspace parent")
    require(type(shard_size) is int and shard_size > 0, "Shard size must be a positive integer")
    scene_partition("fixture/validation", seed, validation_fraction)
    raw_index = source.read_bytes()
    index = parse_json(raw_index)
    media, prepared = {}, []
    if isinstance(index, dict) and index.get("schema") == "clean-vsi590k-admission-index-v1":
        from .dataset_admission import prepare_clean_index

        prepared = prepare_clean_index(index, source, root, media, answer_tag)
    else:
        if isinstance(index, dict):
            require(index.get("schema") == "student-admission-index-v1", "Expected a clean converter admission index or admitted target/binding/review entries")
            entries = index.get("rows")
        else:
            entries = index
        require(isinstance(entries, list) and bool(entries), "Admission index must contain at least one admitted target")
        for position, entry in enumerate(entries):
            try:
                prepared.append(_prepare_entry(entry, root, source.parent, media, answer_tag))
            except (DatasetBuildError, OSError) as error:
                raise DatasetBuildError(f"Admission entry {position}: {error}") from error
    require(bool(prepared), "Admission index must contain at least one admitted target")
    require(type(fixture_only) is bool, "fixture_only must be a boolean")
    if fixture_only:
        for row in prepared:
            row["fixture_only"] = True
    rows, duplicates = _deduplicate(prepared)
    for row in rows:
        row["split"] = scene_partition(row["physical_scene_id"], seed, validation_fraction)
    proof = split_proof(rows, seed, validation_fraction)
    output.mkdir()
    (output / "media").mkdir()
    needed_media = {frame["path"] for row in rows for frame in row["student_input"]["frames"]}
    for name in sorted(needed_media):
        digest = hashlib.sha256()
        with Path(media["files"][name]["path"]).open("rb") as original, (output / name).open("xb") as copied:
            for chunk in iter(lambda: original.read(1024 * 1024), b""):
                digest.update(chunk)
                copied.write(chunk)
        require(digest.hexdigest() == media["files"][name]["sha256"], "Source frame changed while packaging; incomplete output has no manifest")
    proof_pin = _write_file(output / "split_proof.json", canonical_bytes(proof))
    shards, examples = [], []
    for partition in ("train", "validation"):
        selected = [row for row in rows if row["split"] == partition]
        for start in range(0, len(selected), shard_size):
            name = f"{partition}-{start // shard_size:05d}.jsonl"
            digest = hashlib.sha256()
            chunk = selected[start:start + shard_size]
            with (output / name).open("xb") as stream:
                for offset, row in enumerate(chunk):
                    data = record_bytes(chat_record(row))
                    stream.write(data)
                    digest.update(data)
                    examples.append({key: row[key] for key in ("qid", "dataset", "scene", "physical_scene_id", "split", "category", "fixture_only", "dedup_key", "target", "binding", "request", "review", "source_terminal")}
                                    | {"question_sha256": text_sha256(row["student_input"]["question"]),
                                       "options_sha256": digest_json(row["student_input"]["options"]),
                                       "rendered_target_sha256": text_sha256(row["target_text"]),
                                       "frames": row["student_input"]["frames"], "frame_order": row["frame_order"],
                                       "frame_order_sha256": digest_json(row["frame_order"]), "frame_sizes": row["frame_sizes"],
                                       "shard": name, "record_index": offset, "record_sha256": hashlib.sha256(data).hexdigest()})
            shards.append({"path": name, "sha256": digest.hexdigest(), "split": partition, "rows": len(chunk)})
    fixture_only = any(row["fixture_only"] for row in prepared)
    manifest = {"schema": SCHEMA, "admission_index": {"path": str(source), "sha256": hashlib.sha256(raw_index).hexdigest()},
                "admitted_count": len(prepared), "example_count": len(rows), "fixture_only": fixture_only, "training_eligible": not fixture_only,
                "source_pool": "synthetic-fixture" if fixture_only else "nyu-visionx/VSI-590K", "original_weights_required": True,
                "answer_tag": answer_tag, "frame_count": 32, "target_truncation": False,
                "hash_encoding": "UTF-8 question/target; canonical sorted indent=2 JSON plus LF for options/order; file bytes for source/media/shards",
                "dedup_policy": "NFC and whitespace-normalized casefolded question plus physical scene; conflicting options/answers refuse; lexicographic qid,target SHA,binding SHA selects keeper",
                "split_proof": proof_pin, "split_seed": seed, "validation_fraction": validation_fraction,
                "shard_size": shard_size, "shards": shards, "examples": examples, "duplicates": duplicates}
    manifest_pin = _write_file(output / "manifest.json", canonical_bytes(manifest))
    return {"manifest": str(output / "manifest.json"), "sha256": manifest_pin["sha256"], "example_count": len(rows),
            "training_questions": proof["training_questions"], "validation_questions": proof["heldout_questions"], "fixture_only": fixture_only}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Package independently admitted v2 targets and authenticated RGB32 into deterministic training shards")
    parser.add_argument("--admission-index", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--validation-fraction", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--shard-size", type=int, default=1000)
    parser.add_argument("--answer-tag", choices=("ANSWER", "answer"), default="ANSWER")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--num-examples", type=int, default=8)
    parser.add_argument("--tokenizer", action="append", default=[], metavar="MODEL=LOCAL_PATH")
    parser.add_argument("--allow-fixtures", action="store_true")
    parser.add_argument("--fixture-only", action="store_true", help="Mark generated shards ineligible for training even when the upstream test admission resembles production")
    args = parser.parse_args(argv)
    result = build_dataset(args.admission_index, args.output, args.workspace_root, args.validation_fraction, args.seed, args.shard_size, args.answer_tag, args.fixture_only)
    if args.dry_run:
        from .dataset_loader import StudentDataset, dry_run, tokenizer_arguments

        dataset = StudentDataset(result["manifest"], workspace_root=args.workspace_root, split="all", allow_fixtures=args.allow_fixtures)
        report = dry_run(dataset, args.num_examples, tokenizer_arguments(args.tokenizer))
        report_path = Path(args.output) / "token_lengths.json"
        _write_file(report_path, canonical_bytes(report))
        result["token_lengths"] = str(report_path)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
