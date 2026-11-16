#!/usr/bin/env python3
"""Benchmark-agnostic core for content-addressed, mechanically authoritative score records.

Shared by ``score_index.py`` (VSIBench) and ``score_index_vstibench.py`` (VSTIBench). Each wrapper
owns everything benchmark-specific (VSIBench's frozen ``group`` record type, each wrapper's own
``ROLE_POLICIES``, its own ``INDEX_RELATIVE_PATH``, and its own scorer manifest/id). This module
holds only what is genuinely benchmark-agnostic: hashing/canonicalization primitives, dataset and
raw-trace loading, the ``category`` record builder/validator, and the ``seed_mean``/``composite``
record types plus the closed ``AGGREGATION_FORMULAS`` registry that both wrappers reuse.

This module deliberately does not decide whether a run is scientifically strict, deployed, or
best -- that judgment stays in each wrapper's hand-reviewed nomination manifest.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from evaluation import scoring  # type: ignore[no-redef]
else:
    from . import scoring


RECORD_SCHEMA = "mechanical-score-record-v1"
RECORDS_RELATIVE_DIR = Path("agent/evaluation/records")
STRICT_TRACE_RE = re.compile(r"trace_(0|[1-9][0-9]*)\.json\Z")
SHA256_RE = re.compile(r"sha256:([0-9a-f]{64})\Z")

# Additive relaxation only: still "r" + digits (`r221...`), now also "r" + "v" + digits
# (`rv3...`, this project's real VSTIBench round-naming convention). `vote`/`synthetic`
# substrings remain banned in ``_source`` regardless of which branch matches.
SOURCE_ID_RE = re.compile(r"r(?:v)?[0-9]+[A-Za-z0-9_.-]*")

SEED_MEAN_AGGREGATION_SCHEMA = "canonical-mean-of-single-run-category-scores-v1"

DEVELOPMENT_CATEGORIES = (
    "obj_appearance_order",
    "object_abs_distance",
    "object_counting",
    "object_rel_direction_easy",
    "object_rel_direction_hard",
    "object_rel_direction_medium",
    "object_rel_distance",
    "object_size_estimation",
    "room_size_estimation",
    "route_planning",
)

VSTI_CATEGORIES = (
    "camera_displacement",
    "camera_movement_direction",
    "camera_obj_abs_dist",
    "camera_obj_rel_dist_v1",
    "camera_obj_rel_dist_v2",
    "camera_obj_rel_dist_v3",
    "obj_obj_relative_pos_lr",
    "obj_obj_relative_pos_nf",
    "obj_obj_relative_pos_ud",
)

# Closed contract: an `aggregation.schema` string not listed here is rejected outright by
# `_validate_composite_payload`. This is the only way a `composite` record's score can be
# recomputed -- no free-form formula strings accepted.
AGGREGATION_FORMULAS = {
    "vsibench-official-8task-v1": {
        "categories": DEVELOPMENT_CATEGORIES,
        "collapse_groups": [
            ("object_rel_direction_easy", "object_rel_direction_medium", "object_rel_direction_hard"),
        ],
    },
    "vstibench-official-5subtask-v1": {
        "categories": VSTI_CATEGORIES,
        "collapse_groups": [
            ("camera_obj_rel_dist_v1", "camera_obj_rel_dist_v2", "camera_obj_rel_dist_v3"),
            ("obj_obj_relative_pos_lr", "obj_obj_relative_pos_nf", "obj_obj_relative_pos_ud"),
        ],
    },
}

STRICT_SELECTION_CONTRACT = {
    "schema": "strict-trace-selection-v1",
    "filename": r"trace_(0|[1-9][0-9]*)\.json",
    "directory_scope": "direct_children_only",
    "answer_source": "last_non_tool_ai_message_or_blank_no_answer",
    "forbidden_fallbacks": ["response", "prediction"],
    "required_identity": ["filename_qid", "payload_qid", "dataset_qid", "question_type"],
    "membership": "exact_category_qid_set",
    "source_kind": "single_run",
}

CATEGORY_KEYS = {
    "dataset", "inputs", "question_scores", "record_id", "record_type",
    "schema_version", "scope", "score", "scorer_id", "semantic_integrity", "source",
}
SEED_MEAN_KEYS = {
    "aggregation", "constituents", "dataset", "record_id", "record_type",
    "schema_version", "scope", "score", "scorer_id", "semantic_integrity", "source",
}
COMPOSITE_KEYS = {
    "aggregation", "category_sources", "dataset", "record_id", "record_type",
    "schema_version", "scope", "score", "scorer_id", "semantic_integrity",
}


class ScoreIndexError(ValueError):
    """Raised when a score artifact violates the closed score contract."""


def canonical_json_bytes(value: Any) -> bytes:
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ScoreIndexError(f"value is not canonical JSON: {exc}") from exc
    return (text + "\n").encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _duplicate_key_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ScoreIndexError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _loads_json(data: bytes, label: str) -> Any:
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_duplicate_key_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ScoreIndexError(f"invalid JSON in {label}: {exc}") from exc


def _read_stable_bytes(path: Path) -> bytes:
    try:
        before = path.stat()
        data = path.read_bytes()
        after = path.stat()
    except OSError as exc:
        raise ScoreIndexError(f"cannot read {path}: {exc}") from exc
    before_identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    after_identity = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if before_identity != after_identity or len(data) != after.st_size:
        raise ScoreIndexError(f"file changed while being read: {path}")
    return data


def _canonical_qid(value: Any, label: str) -> str:
    if isinstance(value, bool):
        raise ScoreIndexError(f"{label} is not an integer question id")
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str) and re.fullmatch(r"0|[1-9][0-9]*", value):
        return value
    raise ScoreIndexError(f"{label} is not a canonical integer question id: {value!r}")


def _load_dataset(dataset_path: Path) -> tuple[bytes, list[dict[str, Any]], dict[str, dict[str, Any]]]:
    data = _read_stable_bytes(dataset_path)
    parsed = _loads_json(data, str(dataset_path))
    if not isinstance(parsed, list):
        raise ScoreIndexError("dataset must be a JSON list")
    items: list[dict[str, Any]] = []
    by_qid: dict[str, dict[str, Any]] = {}
    for offset, item in enumerate(parsed):
        if not isinstance(item, dict):
            raise ScoreIndexError(f"dataset item {offset} is not an object")
        for key in ("id", "question_type", "ground_truth"):
            if key not in item:
                raise ScoreIndexError(f"dataset item {offset} is missing {key!r}")
        qid = _canonical_qid(item["id"], f"dataset item {offset} id")
        if qid in by_qid:
            raise ScoreIndexError(f"duplicate dataset question id {qid}")
        normalized = dict(item)
        normalized["id"] = qid
        items.append(normalized)
        by_qid[qid] = normalized
    return data, items, by_qid


def _discover_strict_traces(artifact_dir: Path) -> list[tuple[str, Path]]:
    if not artifact_dir.is_dir():
        raise ScoreIndexError(f"artifact directory does not exist: {artifact_dir}")
    selected: list[tuple[str, Path]] = []
    for path in artifact_dir.iterdir():
        if not path.is_file():
            continue
        match = STRICT_TRACE_RE.fullmatch(path.name)
        if match:
            selected.append((match.group(1), path))
    selected.sort(key=lambda item: int(item[0]))
    if not selected:
        raise ScoreIndexError(f"missing strict raw traces in {artifact_dir}")
    return selected


def _payload_qid(payload: Mapping[str, Any], path: Path) -> str:
    present = [key for key in ("id", "question_id") if key in payload]
    if not present:
        raise ScoreIndexError(f"{path.name} has no id or question_id")
    values = {_canonical_qid(payload[key], f"{path.name} {key}") for key in present}
    if len(values) != 1:
        raise ScoreIndexError(f"{path.name} has conflicting id and question_id")
    return values.pop()


def _validate_trace(
    filename_qid: str,
    path: Path,
    dataset_item: Mapping[str, Any],
    category: str,
) -> tuple[dict[str, Any], dict[str, str]]:
    data = _read_stable_bytes(path)
    payload = _loads_json(data, str(path))
    if not isinstance(payload, dict):
        raise ScoreIndexError(f"{path.name} must contain one JSON object")
    payload_qid = _payload_qid(payload, path)
    if payload_qid != filename_qid:
        raise ScoreIndexError(
            f"{path.name} payload question id {payload_qid} does not match filename"
        )
    if payload_qid != str(dataset_item["id"]):
        raise ScoreIndexError(f"{path.name} does not match its dataset question")
    payload_category = payload.get("question_type")
    if payload_category != category:
        raise ScoreIndexError(
            f"{path.name} question_type {payload_category!r} does not match {category!r}"
        )
    if dataset_item["question_type"] != category:
        raise ScoreIndexError(f"dataset question {payload_qid} is not in category {category}")
    try:
        scoring.extract_response(payload, strict=True)
    except scoring.ScoringError as exc:
        raise ScoreIndexError(str(exc)) from exc
    trace_input = {
        "basename": path.name,
        "question_id": payload_qid,
        "sha256": _sha256_bytes(data),
    }
    return payload, trace_input


def _safe_logical_key(value: str, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ScoreIndexError(f"{label} must be a non-empty string")
    path = Path(value)
    if path.is_absolute() or "." in path.parts or ".." in path.parts or "\\" in value:
        raise ScoreIndexError(f"{label} must be a normalized relative POSIX key")
    return value


def _source(source_id: str, artifact_key: str, source_kind: str) -> dict[str, str]:
    if source_kind != "single_run":
        raise ScoreIndexError(f"unsupported source kind {source_kind!r}")
    if not SOURCE_ID_RE.fullmatch(source_id):
        raise ScoreIndexError(f"invalid single-run source id {source_id!r}")
    lowered = source_id.lower()
    if "vote" in lowered or "synthetic" in lowered:
        raise ScoreIndexError("vote and synthetic sources are not supported")
    return {
        "artifact_key": _safe_logical_key(artifact_key, "artifact_key"),
        "kind": "single_run",
        "source_id": source_id,
    }


def _record_id(record_without_id: Mapping[str, Any]) -> str:
    return _sha256_bytes(canonical_json_bytes(record_without_id))


def _with_record_id(body: dict[str, Any]) -> dict[str, Any]:
    record = dict(body)
    record["record_id"] = _record_id(body)
    return record


def _expect_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise ScoreIndexError(
            f"{label} keys differ: missing={sorted(expected - actual)}, extra={sorted(actual - expected)}"
        )


def _validate_sha256(value: Any, label: str) -> None:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise ScoreIndexError(f"{label} is not a sha256 identifier")


def _require_positive_int(value: Any, label: str) -> int:
    """Fail closed on anything that is not an exact positive JSON integer.

    ``bool`` is an ``int`` subclass and JSON floats compare equal to ints (``500.0 == 500``),
    so bare ``isinstance``/``==`` checks silently accept forged count metadata. Every
    ``question_count`` field must pass through here.
    """

    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ScoreIndexError(f"{label} must be a positive integer")
    return value


def core_manifest_fragment(scoring_module: Any) -> dict[str, Any]:
    """The benchmark-agnostic slice of a wrapper's scorer manifest.

    Each wrapper (``score_index.py``, ``score_index_vstibench.py``) adds exactly one more key --
    the sha256 of its own file -- so editing one wrapper's file never staless the other's
    scorer_id, while editing this shared core (or ``scoring.py``) staless both.
    """

    scoring_path = Path(scoring_module.__file__).resolve()
    core_path = Path(__file__).resolve()
    return {
        "record_schema": RECORD_SCHEMA,
        "score_record_core_py_sha256": _sha256_bytes(core_path.read_bytes()),
        "scoring_contract": scoring_module.SCORING_CONTRACT,
        "scoring_py_sha256": _sha256_bytes(scoring_path.read_bytes()),
        "strict_selection_contract": STRICT_SELECTION_CONTRACT,
    }


def build_category_record(
    dataset_path: str | Path,
    artifact_dir: str | Path,
    *,
    dataset_id: str,
    category: str,
    source_id: str,
    artifact_key: str,
    scorer_id: str,
    source_kind: str = "single_run",
) -> dict[str, Any]:
    """Build one raw-only category record without writing it."""

    dataset_path = Path(dataset_path)
    artifact_dir = Path(artifact_dir)
    dataset_bytes, dataset, by_qid = _load_dataset(dataset_path)
    expected = {
        qid: item for qid, item in by_qid.items() if item["question_type"] == category
    }
    if not expected:
        raise ScoreIndexError(f"dataset has no questions for category {category!r}")

    payloads: list[dict[str, Any]] = []
    trace_inputs: list[dict[str, str]] = []
    seen: set[str] = set()
    for filename_qid, path in _discover_strict_traces(artifact_dir):
        if filename_qid in seen:
            raise ScoreIndexError(f"duplicate trace question id {filename_qid}")
        if filename_qid not in expected:
            raise ScoreIndexError(f"unexpected trace question id {filename_qid} for {category}")
        payload, trace_input = _validate_trace(
            filename_qid, path, expected[filename_qid], category
        )
        seen.add(filename_qid)
        payloads.append(payload)
        trace_inputs.append(trace_input)
    missing = sorted(set(expected) - seen, key=int)
    if missing:
        raise ScoreIndexError(f"missing trace question ids for {category}: {missing}")

    payloads.sort(key=lambda value: int(_payload_qid(value, artifact_dir)))
    trace_inputs.sort(key=lambda value: int(value["question_id"]))
    category_dataset = [expected[qid] for qid in sorted(expected, key=int)]
    evaluated = scoring.evaluate_entries(payloads, category_dataset, strict=True)
    question_scores = []
    for qid in sorted(expected, key=int):
        metrics = evaluated["question_metrics"][qid]
        is_mca = category in scoring.MCA_QUESTION_TYPES or "direction" in category
        question_scores.append(
            {
                "question_id": qid,
                "value": scoring.canonical_score(float(metrics["is_correct"]))
                if is_mca
                else scoring.canonical_score(float(metrics["MRA:.5:.95:.05"])),
            }
        )

    score_value = scoring.canonical_mean(
        item["value"] for item in question_scores
    )
    metric = "exact_match" if category in scoring.MCA_QUESTION_TYPES or "direction" in category else "mra_0.50_0.95_0.05"
    body = {
        "dataset": {
            "dataset_id": _safe_logical_key(dataset_id, "dataset_id"),
            "question_count": len(dataset),
            "sha256": _sha256_bytes(dataset_bytes),
        },
        "inputs": {
            "set_sha256": _sha256_bytes(canonical_json_bytes(trace_inputs)),
            "traces": trace_inputs,
        },
        "question_scores": question_scores,
        "record_type": "category",
        "schema_version": RECORD_SCHEMA,
        "scope": {"category": category, "question_count": len(expected)},
        "score": {"metric": metric, "value": float(score_value)},
        "scorer_id": scorer_id,
        "semantic_integrity": "not_evaluated",
        "source": _source(source_id, artifact_key, source_kind),
    }
    return _with_record_id(body)


def build_seed_mean_record(
    constituent_records: Iterable[Mapping[str, Any]],
    *,
    scorer_id: str,
) -> dict[str, Any]:
    """Build a ``seed_mean`` record averaging >=2 same-category single-run category records."""

    records = sorted(
        (dict(record) for record in constituent_records),
        key=lambda record: record["source"]["source_id"],
    )
    if len(records) < 2:
        raise ScoreIndexError("seed_mean requires at least two constituent records")
    first = records[0]
    if first.get("record_type") != "category":
        raise ScoreIndexError("seed_mean constituents must be category records")
    category = first["scope"]["category"]
    dataset = first["dataset"]
    metric = first["score"]["metric"]
    source_ids: list[str] = []
    constituents: list[dict[str, Any]] = []
    values: list[float] = []
    for record in records:
        if record.get("record_type") != "category":
            raise ScoreIndexError("seed_mean constituents must be category records")
        if record["scorer_id"] != scorer_id:
            raise ScoreIndexError("seed_mean constituent does not use the given scorer")
        if record["dataset"] != dataset:
            raise ScoreIndexError("seed_mean constituents do not share one dataset")
        if record["scope"]["category"] != category:
            raise ScoreIndexError("seed_mean constituents do not share one category")
        # Every constituent's count must be an exact positive int BEFORE comparing —
        # bare == would accept a 50/50.0 int/float mix (JSON floats compare equal to ints).
        constituent_count = _require_positive_int(
            record["scope"]["question_count"], "seed_mean constituent question_count"
        )
        if constituent_count != _require_positive_int(
            first["scope"]["question_count"], "seed_mean constituent question_count"
        ):
            raise ScoreIndexError("seed_mean constituents do not share one question count")
        source_id = record["source"]["source_id"]
        if source_id in source_ids:
            raise ScoreIndexError("seed_mean constituents repeat a source_id")
        source_ids.append(source_id)
        value = float(record["score"]["value"])
        values.append(value)
        constituents.append(
            {"record_id": record["record_id"], "source_id": source_id, "value": value}
        )

    body = {
        "aggregation": {"schema": SEED_MEAN_AGGREGATION_SCHEMA},
        "constituents": constituents,
        "dataset": dataset,
        "record_type": "seed_mean",
        "schema_version": RECORD_SCHEMA,
        "scope": {
            "category": category,
            "question_count": _require_positive_int(
                first["scope"]["question_count"], "seed_mean question_count"
            ),
        },
        "score": {"metric": metric, "value": scoring.canonical_mean(values)},
        "scorer_id": scorer_id,
        "semantic_integrity": "not_evaluated",
        "source": {"kind": "seed_mean"},
    }
    return _with_record_id(body)


def build_composite_record(
    aggregation_schema: str,
    category_source_records: Mapping[str, Mapping[str, Any]],
    *,
    scorer_id: str,
) -> dict[str, Any]:
    """Build a ``composite`` record from a per-category map of category/seed_mean records."""

    formula = AGGREGATION_FORMULAS.get(aggregation_schema)
    if formula is None:
        raise ScoreIndexError(f"unsupported aggregation schema {aggregation_schema!r}")
    categories = formula["categories"]
    if set(category_source_records) != set(categories):
        raise ScoreIndexError("composite category_source_records do not match its aggregation scope")

    category_sources: dict[str, dict[str, str]] = {}
    values: dict[str, float] = {}
    dataset: Mapping[str, Any] | None = None
    total_questions = 0
    for category in categories:
        record = category_source_records[category]
        record_type = record.get("record_type")
        if record_type not in ("category", "seed_mean"):
            raise ScoreIndexError(f"composite category {category} has an unsupported record_type")
        if record["scorer_id"] != scorer_id:
            raise ScoreIndexError(f"composite category {category} does not use the given scorer")
        if record["scope"]["category"] != category:
            raise ScoreIndexError(f"composite category {category} scope mismatch")
        if dataset is None:
            dataset = record["dataset"]
        elif record["dataset"] != dataset:
            raise ScoreIndexError("composite category sources do not share one dataset")
        category_sources[category] = {"record_type": record_type, "record_id": record["record_id"]}
        values[category] = float(record["score"]["value"])
        total_questions += _require_positive_int(
            record["scope"]["question_count"], f"composite category {category} question_count"
        )
    assert dataset is not None

    pseudo_task_values = []
    collapsed_names: set[str] = set()
    for group in formula["collapse_groups"]:
        pseudo_task_values.append(scoring.canonical_mean(values[c] for c in group))
        collapsed_names.update(group)
    official_tasks = pseudo_task_values + [
        values[c] for c in categories if c not in collapsed_names
    ]

    body = {
        "aggregation": {"schema": aggregation_schema},
        "category_sources": category_sources,
        "dataset": dataset,
        "record_type": "composite",
        "schema_version": RECORD_SCHEMA,
        "scope": {"categories": list(categories), "question_count": total_questions},
        "score": {
            "official": scoring.canonical_mean(official_tasks),
            "raw_category_macro": scoring.canonical_mean(values.values()),
        },
        "scorer_id": scorer_id,
        "semantic_integrity": "not_evaluated",
    }
    return _with_record_id(body)


def write_record_bytes(record: Mapping[str, Any], records_dir: str | Path) -> Path:
    """Atomically create a content-addressed record file; never overwrite. No validation."""

    match = SHA256_RE.fullmatch(str(record["record_id"]))
    assert match is not None
    records_dir = Path(records_dir)
    records_dir.mkdir(parents=True, exist_ok=True)
    destination = records_dir / f"{match.group(1)}.json"
    data = canonical_json_bytes(record)
    fd, temporary_name = tempfile.mkstemp(prefix=".score-record-", dir=records_dir)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary_name, destination)
        except FileExistsError as exc:
            raise ScoreIndexError(f"record already exists: {destination}") from exc
        directory_fd = os.open(records_dir, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
    return destination


def validate_dataset_field(dataset: Any) -> None:
    if not isinstance(dataset, Mapping):
        raise ScoreIndexError("record dataset is not an object")
    _expect_keys(dataset, {"dataset_id", "question_count", "sha256"}, "dataset")
    _safe_logical_key(dataset["dataset_id"], "dataset_id")
    _validate_sha256(dataset["sha256"], "dataset sha256")
    _require_positive_int(dataset["question_count"], "dataset question_count")


def validate_envelope(
    record: Mapping[str, Any],
    expected_keys: set[str],
    *,
    expected_scorer_id: str | None,
) -> None:
    _expect_keys(record, expected_keys, "record")
    if record["schema_version"] != RECORD_SCHEMA:
        raise ScoreIndexError("unsupported record schema")
    if record["semantic_integrity"] != "not_evaluated":
        raise ScoreIndexError("records cannot claim semantic eligibility")
    _validate_sha256(record["record_id"], "record_id")
    _validate_sha256(record["scorer_id"], "scorer_id")
    body = dict(record)
    claimed_id = body.pop("record_id")
    if _record_id(body) != claimed_id:
        raise ScoreIndexError("record content does not match record_id")
    if expected_scorer_id is not None and record["scorer_id"] != expected_scorer_id:
        raise ScoreIndexError("record scorer_id is stale")


def _validate_category_payload(record: Mapping[str, Any]) -> None:
    validate_dataset_field(record["dataset"])
    source = record["source"]
    if not isinstance(source, Mapping):
        raise ScoreIndexError("record source is not an object")
    _expect_keys(source, {"artifact_key", "kind", "source_id"}, "source")
    if source != _source(source["source_id"], source["artifact_key"], source["kind"]):
        raise ScoreIndexError("source is not canonical")
    scope = record["scope"]
    _expect_keys(scope, {"category", "question_count"}, "category scope")
    _require_positive_int(scope["question_count"], "category question_count")
    inputs = record["inputs"]
    _expect_keys(inputs, {"set_sha256", "traces"}, "inputs")
    _validate_sha256(inputs["set_sha256"], "input set_sha256")
    traces = inputs["traces"]
    scores = record["question_scores"]
    if not isinstance(traces, list) or not isinstance(scores, list):
        raise ScoreIndexError("traces and question_scores must be lists")
    if len(traces) != scope["question_count"] or len(scores) != scope["question_count"]:
        raise ScoreIndexError("category record question counts disagree")
    if _sha256_bytes(canonical_json_bytes(traces)) != inputs["set_sha256"]:
        raise ScoreIndexError("trace input set hash does not match")
    trace_qids: list[str] = []
    for trace in traces:
        _expect_keys(trace, {"basename", "question_id", "sha256"}, "trace input")
        qid = _canonical_qid(trace["question_id"], "trace question_id")
        if trace["basename"] != f"trace_{qid}.json":
            raise ScoreIndexError("trace basename does not match question id")
        _validate_sha256(trace["sha256"], "trace sha256")
        trace_qids.append(qid)
    score_qids: list[str] = []
    for question_score in scores:
        _expect_keys(question_score, {"question_id", "value"}, "question score")
        qid = _canonical_qid(question_score["question_id"], "score question_id")
        value = question_score["value"]
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
            raise ScoreIndexError("question score value must be in [0, 1]")
        score_qids.append(qid)
    if trace_qids != sorted(trace_qids, key=int) or score_qids != sorted(score_qids, key=int):
        raise ScoreIndexError("question ids must be sorted")
    if len(set(trace_qids)) != len(trace_qids) or trace_qids != score_qids:
        raise ScoreIndexError("trace and score question ids do not match exactly")
    score = record["score"]
    _expect_keys(score, {"metric", "value"}, "category score")
    expected_metric = "exact_match" if scope["category"] in scoring.MCA_QUESTION_TYPES or "direction" in scope["category"] else "mra_0.50_0.95_0.05"
    if score["metric"] != expected_metric:
        raise ScoreIndexError("category metric does not match question type")
    expected_value = scoring.canonical_mean(float(item["value"]) for item in scores)
    if score["value"] != expected_value:
        raise ScoreIndexError("category score does not match question scores")


def _validate_seed_mean_payload(record: Mapping[str, Any], *, resolve: Callable[[str], Mapping[str, Any]]) -> None:
    validate_dataset_field(record["dataset"])
    if record["source"] != {"kind": "seed_mean"}:
        raise ScoreIndexError("seed_mean source is not canonical")
    scope = record["scope"]
    _expect_keys(scope, {"category", "question_count"}, "seed_mean scope")
    _require_positive_int(scope["question_count"], "seed_mean question_count")
    aggregation = record["aggregation"]
    _expect_keys(aggregation, {"schema"}, "seed_mean aggregation")
    if aggregation["schema"] != SEED_MEAN_AGGREGATION_SCHEMA:
        raise ScoreIndexError("unsupported seed_mean aggregation schema")
    constituents = record["constituents"]
    if not isinstance(constituents, list) or len(constituents) < 2:
        raise ScoreIndexError("seed_mean requires at least two constituents")
    source_ids: list[str] = []
    values: list[float] = []
    for item in constituents:
        _expect_keys(item, {"record_id", "source_id", "value"}, "seed_mean constituent")
        _validate_sha256(item["record_id"], "constituent record_id")
        value = item["value"]
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
            raise ScoreIndexError("seed_mean constituent value must be in [0, 1]")
        loaded = resolve(item["record_id"])
        if loaded.get("record_type") != "category":
            raise ScoreIndexError("seed_mean constituent must be a category record")
        if loaded["dataset"] != record["dataset"]:
            raise ScoreIndexError("seed_mean constituent dataset mismatch")
        if loaded["scope"]["category"] != scope["category"]:
            raise ScoreIndexError("seed_mean constituent category mismatch")
        # Constituents are same-category re-runs over the same qid set, so this record's
        # question_count must be the IDENTITY of every leaf's validated count, never trusted
        # from the seed_mean's own scope metadata (a forged 49/51 split otherwise passes).
        if loaded["scope"]["question_count"] != scope["question_count"]:
            raise ScoreIndexError(
                "seed_mean question_count does not match its constituents' validated counts"
            )
        if loaded["source"]["source_id"] != item["source_id"]:
            raise ScoreIndexError("seed_mean constituent source_id mismatch")
        if float(loaded["score"]["value"]) != float(value):
            raise ScoreIndexError("seed_mean constituent value does not match its record")
        source_ids.append(item["source_id"])
        values.append(float(value))
    if len(set(source_ids)) != len(source_ids):
        raise ScoreIndexError("seed_mean constituents repeat a source_id")
    if source_ids != sorted(source_ids):
        raise ScoreIndexError("seed_mean constituents must be sorted by source_id")
    score = record["score"]
    _expect_keys(score, {"metric", "value"}, "seed_mean score")
    category = scope["category"]
    expected_metric = "exact_match" if category in scoring.MCA_QUESTION_TYPES or "direction" in category else "mra_0.50_0.95_0.05"
    if score["metric"] != expected_metric:
        raise ScoreIndexError("seed_mean metric does not match category")
    if score["value"] != scoring.canonical_mean(values):
        raise ScoreIndexError("seed_mean score does not match constituent mean")


def _validate_composite_payload(record: Mapping[str, Any], *, resolve: Callable[[str], Mapping[str, Any]]) -> None:
    validate_dataset_field(record["dataset"])
    aggregation = record["aggregation"]
    _expect_keys(aggregation, {"schema"}, "composite aggregation")
    formula = AGGREGATION_FORMULAS.get(aggregation["schema"])
    if formula is None:
        raise ScoreIndexError(f"unsupported aggregation schema {aggregation['schema']!r}")
    categories = formula["categories"]
    scope = record["scope"]
    _expect_keys(scope, {"categories", "question_count"}, "composite scope")
    _require_positive_int(scope["question_count"], "composite question_count")
    if scope["categories"] != list(categories):
        raise ScoreIndexError("composite categories do not match its aggregation schema")
    category_sources = record["category_sources"]
    if not isinstance(category_sources, Mapping) or set(category_sources) != set(categories):
        raise ScoreIndexError("composite category_sources map is incomplete")

    values: dict[str, float] = {}
    total_questions = 0
    for category in categories:
        entry = category_sources[category]
        if not isinstance(entry, Mapping):
            raise ScoreIndexError(f"composite category {category} source entry is not an object")
        _expect_keys(entry, {"record_type", "record_id"}, f"composite category_sources[{category}]")
        if entry["record_type"] not in ("category", "seed_mean"):
            raise ScoreIndexError(f"composite category {category} names an unsupported record_type")
        _validate_sha256(entry["record_id"], f"composite category {category} record_id")
        loaded = resolve(entry["record_id"])
        if loaded.get("record_type") != entry["record_type"]:
            raise ScoreIndexError(f"composite category {category} record_type mismatch")
        if loaded["scope"]["category"] != category:
            raise ScoreIndexError(f"composite category {category} scope mismatch")
        if loaded["dataset"] != record["dataset"]:
            raise ScoreIndexError(f"composite category {category} dataset mismatch")
        if loaded["scorer_id"] != record["scorer_id"]:
            raise ScoreIndexError(f"composite category {category} scorer_id mismatch")
        values[category] = float(loaded["score"]["value"])
        # Recompute the total from the validated constituents; the claimed scope value is
        # checked against it below and never trusted (no int() laundering of forged floats).
        total_questions += _require_positive_int(
            loaded["scope"]["question_count"], f"composite category {category} question_count"
        )
    if scope["question_count"] != total_questions:
        raise ScoreIndexError("composite question_count does not match its category sources")

    pseudo_task_values = []
    collapsed_names: set[str] = set()
    for group in formula["collapse_groups"]:
        pseudo_task_values.append(scoring.canonical_mean(values[c] for c in group))
        collapsed_names.update(group)
    official_tasks = pseudo_task_values + [
        values[c] for c in categories if c not in collapsed_names
    ]
    expected_official = scoring.canonical_mean(official_tasks)
    expected_macro = scoring.canonical_mean(values.values())
    score = record["score"]
    _expect_keys(score, {"official", "raw_category_macro"}, "composite score")
    if score["official"] != expected_official:
        raise ScoreIndexError("composite official score does not match its category sources")
    if score["raw_category_macro"] != expected_macro:
        raise ScoreIndexError("composite raw_category_macro does not match its category sources")


def validate_record(
    record: Mapping[str, Any],
    *,
    expected_scorer_id: str | None,
    resolve: Callable[[str], Mapping[str, Any]] | None = None,
) -> None:
    """Validate a ``category``/``seed_mean``/``composite`` record. Never handles ``group``.

    ``group`` is VSIBench-only frozen history and stays entirely inside ``score_index.py``.
    """

    if not isinstance(record, Mapping):
        raise ScoreIndexError("record is not an object")
    record_type = record.get("record_type")
    if record_type == "category":
        validate_envelope(record, CATEGORY_KEYS, expected_scorer_id=expected_scorer_id)
        _validate_category_payload(record)
    elif record_type == "seed_mean":
        validate_envelope(record, SEED_MEAN_KEYS, expected_scorer_id=expected_scorer_id)
        if resolve is None:
            raise ScoreIndexError("seed_mean validation requires a record resolver")
        _validate_seed_mean_payload(record, resolve=resolve)
    elif record_type == "composite":
        validate_envelope(record, COMPOSITE_KEYS, expected_scorer_id=expected_scorer_id)
        if resolve is None:
            raise ScoreIndexError("composite validation requires a record resolver")
        _validate_composite_payload(record, resolve=resolve)
    else:
        raise ScoreIndexError(f"unsupported record_type {record_type!r}")


def _record_path_in_dir(records_dir: Path, record_id: str) -> Path:
    match = SHA256_RE.fullmatch(record_id)
    if match is None:
        raise ScoreIndexError(f"invalid record id {record_id!r}")
    return records_dir / f"{match.group(1)}.json"


def read_canonical_record(records_dir: Path, record_id: str) -> dict[str, Any]:
    """Read + canonical-JSON-check + record_id-match-check one record. No semantic validation."""

    path = _record_path_in_dir(Path(records_dir), record_id)
    data = _read_stable_bytes(path)
    parsed = _loads_json(data, str(path))
    if data != canonical_json_bytes(parsed):
        raise ScoreIndexError(f"{path} is not canonical JSON")
    if not isinstance(parsed, dict):
        raise ScoreIndexError(f"record {record_id} is not an object")
    if parsed.get("record_id") != record_id:
        raise ScoreIndexError(f"record filename/id mismatch for {record_id}")
    return parsed


def safe_repo_file(repo_root: Path, relative_path: str) -> Path:
    logical = _safe_logical_key(relative_path, "evidence path")
    root = repo_root.resolve()
    resolved = (repo_root / logical).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ScoreIndexError("evidence path escapes repository") from exc
    return resolved


def artifact_path(artifact_root: Path, artifact_key: str) -> Path:
    logical_key = _safe_logical_key(artifact_key, "artifact_key")
    resolved_root = artifact_root.resolve()
    resolved_path = (artifact_root / logical_key).resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ScoreIndexError("artifact_key escapes artifact_root") from exc
    return resolved_path


def leaf_category_records(
    loaded_record: Mapping[str, Any], resolve: Callable[[str], Mapping[str, Any]]
) -> list[Mapping[str, Any]]:
    """Return the underlying category record(s) backing a ``category``/``seed_mean`` record."""

    record_type = loaded_record.get("record_type")
    if record_type == "category":
        return [loaded_record]
    if record_type == "seed_mean":
        return [resolve(item["record_id"]) for item in loaded_record["constituents"]]
    raise ScoreIndexError(f"unsupported record_type for leaf resolution: {record_type!r}")


def validate_composite_role_policy(
    composite: Mapping[str, Any],
    policy: Mapping[str, Any],
    resolve: Callable[[str], Mapping[str, Any]],
) -> None:
    """Cross-check an already-loaded-and-validated composite record against a role's
    ``category_policy`` (kind + source_id set + artifact-key convention + exact qid set per
    category), generalizing ``_validate_role``'s per-category checks to composite roles.
    """

    category_policy = policy["category_policy"]
    for category, source_policy in category_policy.items():
        entry = composite["category_sources"][category]
        loaded = resolve(entry["record_id"])
        kind = source_policy["kind"]
        if loaded["record_type"] != kind:
            raise ScoreIndexError(f"composite category {category} kind does not match policy")
        expected_source_ids = set(source_policy["source_ids"])
        if kind == "category":
            actual_source_ids = {loaded["source"]["source_id"]}
            expected_key = f"{category}/experiment_{loaded['source']['source_id']}"
            if loaded["source"]["artifact_key"] != expected_key:
                raise ScoreIndexError(f"composite category {category} artifact key is not approved")
        elif kind == "seed_mean":
            actual_source_ids = {item["source_id"] for item in loaded["constituents"]}
            for item in loaded["constituents"]:
                leaf = resolve(item["record_id"])
                expected_key = f"{category}/experiment_{item['source_id']}"
                if leaf["source"]["artifact_key"] != expected_key:
                    raise ScoreIndexError(f"composite category {category} artifact key is not approved")
        else:
            raise ScoreIndexError(f"unsupported policy kind {kind!r}")
        if actual_source_ids != expected_source_ids:
            raise ScoreIndexError(f"composite category {category} names unapproved sources")
        leaves = leaf_category_records(loaded, resolve)
        leaf_qid_sets = [
            [item["question_id"] for item in leaf["question_scores"]] for leaf in leaves
        ]
        first_qids = leaf_qid_sets[0]
        for other in leaf_qid_sets[1:]:
            if other != first_qids:
                raise ScoreIndexError(f"composite category {category} constituents disagree on question ids")
        if _sha256_bytes(canonical_json_bytes(first_qids)) != source_policy["qid_set_sha256"]:
            raise ScoreIndexError(f"composite category {category} question ids are not exact")


def verify_composite_role_sources(
    *,
    dataset_path: str | Path,
    artifact_root: str | Path,
    checked_composite: Mapping[str, Any],
    policy: Mapping[str, Any],
    load_record: Callable[[str], Mapping[str, Any]],
    scorer_id: str,
) -> dict[str, Any]:
    """Replay one composite role from raw traces and require exact record equality."""

    artifact_root = Path(artifact_root)
    formula = AGGREGATION_FORMULAS[policy["aggregation_schema"]]
    rebuilt_category_sources: dict[str, dict[str, Any]] = {}
    for category in formula["categories"]:
        source_policy = policy["category_policy"][category]
        checked_entry = checked_composite["category_sources"][category]
        checked_leaf = load_record(checked_entry["record_id"])
        if source_policy["kind"] == "category":
            source_id = next(iter(source_policy["source_ids"]))
            artifact_key = checked_leaf["source"]["artifact_key"]
            rebuilt = build_category_record(
                dataset_path,
                artifact_path(artifact_root, artifact_key),
                dataset_id=policy["dataset_id"],
                category=category,
                source_id=source_id,
                artifact_key=artifact_key,
                scorer_id=scorer_id,
            )
            if rebuilt != checked_leaf or canonical_json_bytes(rebuilt) != canonical_json_bytes(checked_leaf):
                raise ScoreIndexError(f"composite category {category} does not match its raw source")
            rebuilt_category_sources[category] = rebuilt
        elif source_policy["kind"] == "seed_mean":
            constituent_records = []
            for constituent in checked_leaf["constituents"]:
                leaf_checked = load_record(constituent["record_id"])
                artifact_key = leaf_checked["source"]["artifact_key"]
                rebuilt_leaf = build_category_record(
                    dataset_path,
                    artifact_path(artifact_root, artifact_key),
                    dataset_id=policy["dataset_id"],
                    category=category,
                    source_id=constituent["source_id"],
                    artifact_key=artifact_key,
                    scorer_id=scorer_id,
                )
                if rebuilt_leaf != leaf_checked or canonical_json_bytes(rebuilt_leaf) != canonical_json_bytes(
                    leaf_checked
                ):
                    raise ScoreIndexError(
                        f"composite category {category} constituent {constituent['source_id']} "
                        "does not match its raw source"
                    )
                constituent_records.append(rebuilt_leaf)
            rebuilt_seed_mean = build_seed_mean_record(constituent_records, scorer_id=scorer_id)
            if rebuilt_seed_mean != checked_leaf or canonical_json_bytes(rebuilt_seed_mean) != canonical_json_bytes(
                checked_leaf
            ):
                raise ScoreIndexError(f"composite category {category} seed_mean does not match its raw sources")
            rebuilt_category_sources[category] = rebuilt_seed_mean
        else:
            raise ScoreIndexError(f"unsupported policy kind {source_policy['kind']!r}")

    rebuilt_composite = build_composite_record(
        policy["aggregation_schema"], rebuilt_category_sources, scorer_id=scorer_id
    )
    if rebuilt_composite != checked_composite or canonical_json_bytes(rebuilt_composite) != canonical_json_bytes(
        checked_composite
    ):
        raise ScoreIndexError("composite does not match its raw sources")
    return rebuilt_composite
