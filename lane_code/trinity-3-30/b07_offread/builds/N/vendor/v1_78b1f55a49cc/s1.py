"""Shared VSIBench response extraction and metric implementation.

The historical ``evaluate_benchmark_v4.py`` command uses compatibility mode.
Authoritative score records use strict mode, which only scores committed AI
messages. A trace-native no-answer is scored as blank; flat ``response`` or
``prediction`` fallbacks are rejected rather than laundered into that score.
"""

from __future__ import annotations

import re
from collections import OrderedDict
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


MCA_QUESTION_TYPES = [
    "object_rel_direction_easy",
    "object_rel_direction_medium",
    "object_rel_direction_hard",
    "object_rel_distance",
    "route_planning",
    "obj_appearance_order",
    "camera_movement_direction",
    "camera_obj_rel_dist_v1",
    "camera_obj_rel_dist_v2",
    "camera_obj_rel_dist_v3",
    "obj_obj_relative_pos_lr",
    "obj_obj_relative_pos_nf",
    "obj_obj_relative_pos_ud",
]
NA_QUESTION_TYPES = [
    "object_abs_distance",
    "object_counting",
    "object_size_estimation",
    "room_size_estimation",
    "camera_obj_abs_dist",
    "camera_displacement",
]

SCORING_CONTRACT = {
    "schema": "vsibench-scoring-contract-v1",
    "answer_extraction": {
        "strict": "last_non_tool_ai_message_or_blank_no_answer",
        "strict_forbidden_fallbacks": ["response", "prediction"],
        "compatibility_fallbacks": ["response", "prediction"],
    },
    "mca": "exact_case_insensitive_after_fuzzy_matching_mca",
    "na": "mean_relative_accuracy_0.50_0.95_0.05",
    "overall": "macro_tasks_with_three_object_rel_direction_categories_collapsed",
    "aggregation": "decimal_mean_round_half_even_15_places",
}

SCORE_QUANTUM = Decimal("0.000000000000001")


class ScoringError(ValueError):
    """Raised when an entry cannot be scored under the selected contract."""


def canonical_score(value: int | float | Decimal) -> float:
    """Return a runtime-independent score rounded to the contract precision."""

    try:
        decimal_value = Decimal(str(value))
        with localcontext() as context:
            context.prec = 50
            rounded = decimal_value.quantize(SCORE_QUANTUM, rounding=ROUND_HALF_EVEN)
    except (InvalidOperation, ValueError) as exc:
        raise ScoringError(f"score is not a finite decimal: {value!r}") from exc
    if not rounded.is_finite():
        raise ScoringError(f"score is not finite: {value!r}")
    return float(rounded)


def canonical_mean(values: Iterable[int | float | Decimal]) -> float:
    """Average scores with exact decimal arithmetic, then round once."""

    decimal_values: list[Decimal] = []
    try:
        for value in values:
            decimal_value = Decimal(str(value))
            if not decimal_value.is_finite():
                raise ScoringError(f"score is not finite: {value!r}")
            decimal_values.append(decimal_value)
    except InvalidOperation as exc:
        raise ScoringError("score is not a finite decimal") from exc
    if not decimal_values:
        raise ScoringError("cannot average an empty score sequence")
    with localcontext() as context:
        context.prec = 50
        mean = sum(decimal_values, Decimal(0)) / Decimal(len(decimal_values))
        rounded = mean.quantize(SCORE_QUANTUM, rounding=ROUND_HALF_EVEN)
    return float(rounded)


def fuzzy_matching_mca(pred: Any, options: Sequence[str] | None = None) -> str:
    if not pred:
        return ""
    match = re.search(
        r"<(?:MCQ_)?answer>(.*?)</(?:MCQ_)?answer>",
        str(pred),
        re.DOTALL | re.IGNORECASE,
    )
    if match:
        pred = match.group(1).strip()
    match = re.search(r"Answer:\s*([A-Za-z])", str(pred), re.IGNORECASE)
    if match:
        return match.group(1).upper()
    if options:
        for opt in options:
            parts = opt.split(".")
            if len(parts) >= 2:
                letter, label = parts[0].strip(), parts[1].strip().lower()
                if letter in str(pred) and label in str(pred).lower():
                    return letter.upper()
    letters = re.findall(r"\b([A-Z])\b", str(pred))
    return letters[-1] if letters else ""


def to_float(pred: Any) -> float | None:
    if isinstance(pred, (int, float)):
        return float(pred)
    if not pred:
        return None
    match = re.search(r"<ANSWER>(.*?)</ANSWER>", str(pred), re.IGNORECASE)
    if match:
        floats = re.findall(r"[-+]?\d*\.\d+|\d+", match.group(1))
        if floats:
            return float(floats[-1])
    floats = re.findall(r"[-+]?\d*\.\d+|\d+", str(pred))
    return float(floats[-1]) if floats else None


def abs_dist_norm(pred: float, target: float) -> float:
    return abs(pred - target) / target if target != 0 else 0.0


def mean_relative_accuracy(
    pred: float | None,
    target: float | None,
    start: float,
    end: float,
    interval: float,
) -> float:
    if pred is None or target is None or target == 0:
        return 0.0
    num_pts = (end - start) / interval + 2
    conf_intervs = np.linspace(start, end, int(num_pts))
    accuracy = abs_dist_norm(pred, target) <= 1 - conf_intervs
    return float(accuracy.mean())


def _message_text(content: Any) -> str:
    if isinstance(content, list):
        return "\n".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        )
    return str(content)


def committed_ai_response(entry: Mapping[str, Any]) -> str | None:
    trace = entry.get("trace", {})
    messages = trace.get("messages", []) if isinstance(trace, dict) else trace
    if not isinstance(messages, list):
        return None
    for message in reversed(messages):
        if not isinstance(message, dict):
            continue
        if message.get("role", "").lower() not in ("ai", "aimessage"):
            continue
        if message.get("tool_calls"):
            continue
        response = _message_text(message.get("content", ""))
        if response:
            return response
    return None


def extract_response(entry: Mapping[str, Any], *, strict: bool) -> str:
    response = committed_ai_response(entry)
    if response is not None:
        return response
    if strict:
        qid = entry.get("id", entry.get("question_id", "<unknown>"))
        fallback_fields = [name for name in ("response", "prediction") if name in entry]
        if fallback_fields:
            fields = ", ".join(fallback_fields)
            raise ScoringError(
                f"question {qid} has no committed AI response; strict scoring rejects {fields} fallback"
            )
        return ""

    if "response" in entry:
        raw = entry["response"]
        if isinstance(raw, list):
            response = "\n".join(
                item.get("text", str(item)) if isinstance(item, dict) else str(item)
                for item in raw
            )
        else:
            response = str(raw)
        if response:
            return response
    if "prediction" in entry:
        return str(entry["prediction"])
    return ""


def _score_entry(
    entry: Mapping[str, Any],
    item: Mapping[str, Any],
    *,
    strict: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    qid = str(item["id"])
    question_type = str(item["question_type"])
    ground_truth = item["ground_truth"]
    response = extract_response(entry, strict=strict)
    prediction: Any = None
    is_correct = False
    mra = 0.0

    if question_type in MCA_QUESTION_TYPES or "direction" in question_type:
        prediction = fuzzy_matching_mca(response, item.get("options"))
        is_correct = str(prediction).lower() == str(ground_truth).lower()
        record = {
            "id": qid,
            "is_correct": is_correct,
            "accuracy": 1.0 if is_correct else 0.0,
            "type": question_type,
        }
    elif question_type in NA_QUESTION_TYPES:
        prediction = to_float(response)
        target = to_float(ground_truth)
        if prediction is not None and target is not None:
            error = abs(prediction - target) / target if target != 0 else 0.0
            is_correct = error <= 0.2
            mra = mean_relative_accuracy(prediction, target, 0.5, 0.95, 0.05)
        record = {
            "id": qid,
            "is_correct": is_correct,
            "MRA": mra,
            "type": question_type,
        }
    else:
        raise ScoringError(f"unsupported question type {question_type!r} for question {qid}")

    metrics = {
        "is_correct": is_correct,
        "gt_ans": ground_truth,
        "pr_ans": prediction,
        "question_cat": question_type,
        "MRA:.5:.95:.05": mra,
    }
    return record, metrics


def aggregate_records(records: Iterable[Mapping[str, Any]]) -> OrderedDict[str, float]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for record in records:
        grouped.setdefault(str(record["type"]), []).append(record)

    summary: OrderedDict[str, float] = OrderedDict()
    for question_type in sorted(grouped):
        group = grouped[question_type]
        if question_type in MCA_QUESTION_TYPES or "direction" in question_type:
            value = canonical_mean(float(record["accuracy"]) for record in group)
        else:
            value = canonical_mean(float(record["MRA"]) for record in group)
        summary[f"{question_type}_score"] = float(value)

    direction_accuracies = []
    for task in (
        "object_rel_direction_easy",
        "object_rel_direction_medium",
        "object_rel_direction_hard",
        "object_rel_direction",
    ):
        key = f"{task}_score"
        if key in summary:
            direction_accuracies.append(summary.pop(key))
    if direction_accuracies:
        summary["object_rel_direction_accuracy"] = canonical_mean(direction_accuracies)
    if summary:
        summary["overall"] = canonical_mean(summary.values())
    return summary


def evaluate_entries(
    entries: Iterable[Mapping[str, Any]],
    dataset: Iterable[Mapping[str, Any]],
    *,
    strict: bool,
) -> dict[str, Any]:
    ground_truth = {str(item["id"]): item for item in dataset}
    records: list[dict[str, Any]] = []
    question_metrics: dict[str, dict[str, Any]] = {}

    for entry in entries:
        qid = str(entry.get("id", entry.get("question_id")))
        if qid not in ground_truth:
            if strict:
                raise ScoringError(f"question {qid} is not present in the dataset")
            continue
        record, metrics = _score_entry(entry, ground_truth[qid], strict=strict)
        records.append(record)
        question_metrics[qid] = metrics

    summary = aggregate_records(records)
    return {
        "results": summary,
        "overall_score": summary.get("overall", 0.0) * 100,
        "question_metrics": question_metrics,
    }
