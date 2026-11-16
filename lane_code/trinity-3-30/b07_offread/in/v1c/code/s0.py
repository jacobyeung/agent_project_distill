#!/usr/bin/env python3
"""Scoring and aggregation for external baselines and Qwen3.5-9B students on VSI-Bench.

Supports two evaluation modes:
1. `official_full`: Official full VSI-Bench (5,130 questions) scoring using the exact
   Cambrian `vsibench_doc_to_results` + `vsibench_aggregate_results` logic:
   - `fuzzy_matching(pred)`: `pred.split(' ')[0].rstrip('.').strip()`
   - MCA: exact match (`pred.lower() == target.lower()`)
   - NA: `mean_relative_accuracy(to_float(pred), to_float(target), .5, .95, .05)`
   - Aggregation: combine `object_rel_direction_{easy,medium,hard}` into
     `object_rel_direction` by averaging their 3 sub-task means, then average
     across the 8 primary tasks.
   - When `--results_dir` and `--cell_name` are provided, also writes
     `<cell_name>.items.json`, `<cell_name>.per_question_scores.jsonl`, and
     updates `SUMMARY.tsv` / `SUMMARY.json` with `benchmark="vsibench_full"`.
2. `our_cell`: Our VSI-500 (`vsibench_answerable500`) and VSTI-450 v3
   (`vstibench_repr450_v3`) cell scorer using our `student-answer-v1` parser
   (plus official fuzzy parser side-by-side for diagnostic decomposition),
   producing `.items.json` and `.per_question_scores.jsonl` compatible with
   `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/awstrain_20261027/results/`.
"""

import argparse
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple


_BLOCK_RE = re.compile(r"<answer\s*>(.*?)</answer\s*>", re.IGNORECASE | re.DOTALL)
_UNIT_RE = re.compile(
    r"^\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*"
    r"(?:m|meter|meters|metre|metres|cm|centimeter|centimeters|mm|ft|feet|foot|"
    r"in|inch|inches|deg|degree|degrees|°|s|sec|second|seconds|%)?\s*\.?\s*$",
    re.IGNORECASE,
)
_NUMBER_RE = re.compile(r"([+-]?(?:\d+(?:\.\d+)?|\.\d+))")
_CHOICE_PATTERNS = (
    re.compile(r"^\s*\(?([A-Z])\)?\s*\.?\s*$"),
    re.compile(r"^\s*\(?([A-Z])\)?(?:\s*[:.)\-]\s+|\s+).+\S\s*$"),
    re.compile(
        r"(?:the\s+)?(?:correct\s+|final\s+|best\s+)?(?:answer|option|choice)\s+"
        r"(?:is|would\s+be)\s*\(?([A-Z])\)?(?:\b|\s*[:.)\-])",
        re.IGNORECASE,
    ),
)

OFFICIAL_MCA_TYPES = {
    "object_rel_direction_easy",
    "object_rel_direction_medium",
    "object_rel_direction_hard",
    "object_rel_distance",
    "route_planning",
    "obj_appearance_order",
}
OFFICIAL_NA_TYPES = {
    "object_abs_distance",
    "object_counting",
    "object_size_estimation",
    "room_size_estimation",
}

VSI_PRIMARY_GROUPS = {
    "obj_appearance_order": ["obj_appearance_order"],
    "object_abs_distance": ["object_abs_distance"],
    "object_counting": ["object_counting"],
    "object_rel_direction": [
        "object_rel_direction_easy",
        "object_rel_direction_medium",
        "object_rel_direction_hard",
    ],
    "object_rel_distance": ["object_rel_distance"],
    "object_size_estimation": ["object_size_estimation"],
    "room_size_estimation": ["room_size_estimation"],
    "route_planning": ["route_planning"],
}

VSTI_PRIMARY_GROUPS = {
    "camera_displacement": ["camera_displacement"],
    "camera_movement_direction": ["camera_movement_direction"],
    "camera_obj_abs_dist": ["camera_obj_abs_dist"],
    "camera_obj_rel_dist": [
        "camera_obj_rel_dist_v1",
        "camera_obj_rel_dist_v2",
        "camera_obj_rel_dist_v3",
    ],
    "obj_obj_relative_pos": [
        "obj_obj_relative_pos_lr",
        "obj_obj_relative_pos_nf",
        "obj_obj_relative_pos_ud",
    ],
}

CANONICAL_IDS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "canonical_cell_ids.json"
)


def load_canonical_id_set(benchmark_name: str) -> Optional[List[str]]:
    if not os.path.isfile(CANONICAL_IDS_FILE):
        return None
    with open(CANONICAL_IDS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if benchmark_name in data:
        return [str(x) for x in data[benchmark_name]]
    return None


def _visible_candidate(raw: str) -> Tuple[Optional[str], Optional[str], str]:
    if not isinstance(raw, str) or not raw.strip():
        return None, "empty_generation", ""
    parts = re.split(r"</think\s*>", raw, flags=re.IGNORECASE)
    text = parts[-1]
    if re.search(r"<think\s*>", text, flags=re.IGNORECASE):
        return None, "unclosed_thinking", ""
    text = re.sub(r"(?:\s*<\|(?:im_end|endoftext)\|>)+\s*$", "", text).strip()
    matches = list(_BLOCK_RE.finditer(text))
    if matches:
        return matches[-1].group(1).strip(), None, "tag"
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None, "empty_visible_suffix", ""
    payload = re.sub(
        r"^(?:final\s+answer|answer)\s*:\s*", "", lines[-1], flags=re.IGNORECASE
    ).strip()
    return payload, None, "final_line"


def _parse_multiple_choice_v1(
    payload: str, options: Optional[List[str]]
) -> Tuple[Optional[str], Optional[str]]:
    valid: Optional[set] = None
    if options:
        letters = set()
        for idx, option in enumerate(options):
            m = re.match(r"^\s*\(?([A-Za-z])\)?(?:\s*[:.)\-]|\s+|$)", str(option))
            letters.add(m.group(1).upper() if m else chr(ord("A") + idx))
        valid = letters

    def _admissible(letter: str) -> bool:
        return valid is None or letter in valid

    for pattern in _CHOICE_PATTERNS:
        m = pattern.match(payload)
        if m:
            letter = m.group(1).upper()
            if _admissible(letter):
                return letter, None
    tokens = re.findall(r"\b([A-Z])\b", payload)
    unique = sorted({tok for tok in tokens if _admissible(tok)})
    if len(unique) == 1 and len( payload.split() ) <= 6:
        return unique[0], None
    return None, "not_one_supplied_option_letter"


def _format_decimal(raw: str) -> Optional[str]:
    try:
        value = Decimal(raw)
    except InvalidOperation:
        return None
    if not value.is_finite():
        return None
    if value == 0:
        return "0"
    rendered = format(value.normalize(), "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered or "0"


def _parse_numeric_v1(payload: str) -> Tuple[Optional[str], Optional[str]]:
    cleaned = payload.replace(",", "").strip()
    m = _UNIT_RE.match(cleaned)
    if m:
        normalized = _format_decimal(m.group(1))
        if normalized is not None:
            return normalized, None
    numbers = _NUMBER_RE.findall(cleaned)
    if len(numbers) == 1 and len(cleaned.split()) <= 6:
        normalized = _format_decimal(numbers[0])
        if normalized is not None:
            return normalized, None
    return None, "not_one_finite_number"


def parse_answer_v1(
    raw_text: str, answer_type: str, options: Optional[List[str]] = None
) -> Dict[str, Any]:
    payload, err, branch = _visible_candidate(raw_text)
    if err is not None or payload is None:
        return {
            "parsed_answer": None,
            "parse_status": "failed",
            "parse_error_reason": err,
            "parser_branch": None,
        }
    if answer_type == "multiple_choice":
        ans, reason = _parse_multiple_choice_v1(payload, options)
    elif answer_type in ("numeric", "integer", "float"):
        ans, reason = _parse_numeric_v1(payload)
    else:
        raise ValueError(f"Unsupported answer_type: {answer_type!r}")
    if ans is None:
        return {
            "parsed_answer": None,
            "parse_status": "failed",
            "parse_error_reason": reason,
            "parser_branch": None,
        }
    return {
        "parsed_answer": ans,
        "parse_status": "ok",
        "parse_error_reason": None,
        "parser_branch": branch,
    }


def official_fuzzy_matching(pred: str) -> str:
    if not isinstance(pred, str):
        return ""
    return pred.split(" ")[0].rstrip(".").strip()


def official_exact_match(pred: str, target: str) -> float:
    return 1.0 if pred.lower() == target.lower() else 0.0


def official_to_float(pred: str) -> Optional[float]:
    try:
        val = float(pred)
        if not math.isfinite(val):
            return None
        return val
    except (ValueError, TypeError):
        return None


def official_mra(
    pred: Optional[float],
    target: Optional[float],
    start: float = 0.5,
    end: float = 0.95,
    interval: float = 0.05,
) -> float:
    if pred is None or target is None or not math.isfinite(pred) or not math.isfinite(target):
        return 0.0
    if target == 0.0:
        return 1.0 if pred == 0.0 else 0.0
    num_pts = int((end - start) / interval + 2)
    conf_intervs = [start + i * (end - start) / (num_pts - 1) for i in range(num_pts)]
    rel_err = abs(pred - target) / abs(target)
    hits = [1.0 if rel_err <= (1.0 - c) else 0.0 for c in conf_intervs]
    return sum(hits) / len(hits)


def infer_answer_type(rec: Dict[str, Any]) -> str:
    at = rec.get("answer_type")
    if at in ("multiple_choice", "numeric", "integer", "float"):
        return str(at)
    qtype = str(rec.get("question_type", ""))
    if qtype in OFFICIAL_MCA_TYPES:
        return "multiple_choice"
    if qtype in OFFICIAL_NA_TYPES:
        return "numeric"
    opts = rec.get("options")
    if isinstance(opts, list) and len(opts) > 0:
        return "multiple_choice"
    gt = str(rec.get("ground_truth", "")).strip()
    if re.match(r"^[A-D]$", gt, flags=re.IGNORECASE):
        return "multiple_choice"
    return "numeric"


def load_predictions_with_protocol(
    input_path: str,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    proto: Dict[str, Any] = {}

    if os.path.isdir(input_path):
        out_dir = input_path
        proto_path = os.path.join(out_dir, "protocol.json")
        if os.path.isfile(proto_path):
            with open(proto_path, "r", encoding="utf-8") as f:
                proto = json.load(f)
        merged = os.path.join(out_dir, "predictions.jsonl")
        shard_files = sorted(
            os.path.join(out_dir, fn)
            for fn in os.listdir(out_dir)
            if fn.startswith("shard_") and fn.endswith(".jsonl")
        )
        if shard_files:
            seen = set()
            for sf in shard_files:
                with open(sf, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        rec = json.loads(line)
                        ex_id = str(rec["example_id"])
                        if ex_id in seen:
                            raise RuntimeError(
                                f"Duplicate example_id {ex_id} in {sf}"
                            )
                        seen.add(ex_id)
                        records.append(rec)
        elif os.path.isfile(merged):
            seen = set()
            with open(merged, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    ex_id = str(rec["example_id"])
                    if ex_id in seen:
                        raise RuntimeError(
                            f"Duplicate example_id {ex_id} in {merged}"
                        )
                    seen.add(ex_id)
                    records.append(rec)
        else:
            raise FileNotFoundError(
                f"No shard_*.jsonl or predictions.jsonl found in {out_dir}"
            )
    else:
        out_dir = os.path.dirname(os.path.abspath(input_path))
        proto_path = os.path.join(out_dir, "protocol.json")
        if os.path.isfile(proto_path):
            with open(proto_path, "r", encoding="utf-8") as f:
                proto = json.load(f)
        seen = set()
        with open(input_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                ex_id = str(rec["example_id"])
                if ex_id in seen:
                    raise RuntimeError(
                        f"Duplicate example_id {ex_id} in {input_path}"
                    )
                seen.add(ex_id)
                records.append(rec)

    if proto:
        expected_sha = proto.get("config_sha256")
        expected_arch = proto.get("arch")
        expected_fs = proto.get("frame_source")
        expected_pm = proto.get("prompt_mode")
        expected_tok = proto.get("max_new_tokens")
        for rec in records:
            if expected_sha and rec.get("config_sha256") != expected_sha:
                raise RuntimeError(
                    f"Record {rec.get('example_id')} has config_sha256={rec.get('config_sha256')}, "
                    f"expected {expected_sha} from protocol.json"
                )
            if expected_arch and rec.get("arch") != expected_arch:
                raise RuntimeError(
                    f"Record {rec.get('example_id')} has arch={rec.get('arch')}, expected {expected_arch}"
                )
            if expected_fs and rec.get("frame_source") != expected_fs:
                raise RuntimeError(
                    f"Record {rec.get('example_id')} has frame_source={rec.get('frame_source')}, expected {expected_fs}"
                )
            if expected_pm and rec.get("prompt_mode") != expected_pm:
                raise RuntimeError(
                    f"Record {rec.get('example_id')} has prompt_mode={rec.get('prompt_mode')}, expected {expected_pm}"
                )
            if expected_tok and rec.get("max_new_tokens") != expected_tok:
                raise RuntimeError(
                    f"Record {rec.get('example_id')} has max_new_tokens={rec.get('max_new_tokens')}, expected {expected_tok}"
                )
    else:
        cfg_shas = {rec.get("config_sha256") for rec in records if rec.get("config_sha256")}
        if len(cfg_shas) > 1:
            raise RuntimeError(f"Mixed config_sha256 values across records: {cfg_shas}")

    return records, proto


def score_official_vsibench(
    records: List[Dict[str, Any]],
    expected_count: int = 5130,
) -> Dict[str, Any]:
    if expected_count > 0 and len(records) != expected_count:
        raise RuntimeError(
            f"Incomplete official VSI-Bench run: got {len(records)} records, expected {expected_count}"
        )
    if expected_count == 5130:
        canon_ids = load_canonical_id_set("vsibench_full")
        if canon_ids is not None:
            actual_ids = sorted(str(r["example_id"]) for r in records)
            if actual_ids != sorted(canon_ids):
                missing = sorted(set(canon_ids) - set(actual_ids))[:5]
                extra = sorted(set(actual_ids) - set(canon_ids))[:5]
                raise RuntimeError(
                    f"Question ID set mismatch for vsibench_full: missing={missing}, extra={extra}"
                )

    by_qtype: Dict[str, List[float]] = defaultdict(list)
    scored_records: List[Dict[str, Any]] = []
    cap_count = 0
    cap_without_answer_count = 0
    failure_counts: Counter = Counter()

    for rec in records:
        qtype = str(rec["question_type"])
        gt = str(rec["ground_truth"]).strip()
        pred_text = str(rec.get("response_text", ""))
        fuzzy_pred = official_fuzzy_matching(pred_text)

        out_tok = int(rec.get("output_tokens") or 0)
        max_tok = int(rec.get("max_new_tokens") or 0)
        hit_cap = bool(max_tok > 0 and out_tok >= max_tok)
        if hit_cap:
            cap_count += 1

        extract_branch = rec.get("extract_branch") or "direct"
        status_str = "ok"
        if not fuzzy_pred:
            reason = str(extract_branch) if extract_branch != "direct" else "empty_prediction"
            status_str = f"parse_failed:{reason}"
            failure_counts[status_str] += 1
            if hit_cap:
                cap_without_answer_count += 1

        if qtype in OFFICIAL_MCA_TYPES:
            score = official_exact_match(fuzzy_pred, gt)
        elif qtype in OFFICIAL_NA_TYPES:
            fpred = official_to_float(fuzzy_pred)
            fgt = official_to_float(gt)
            if fuzzy_pred and fpred is None:
                status_str = "parse_failed:not_float"
                failure_counts[status_str] += 1
                if hit_cap:
                    cap_without_answer_count += 1
            score = official_mra(fpred, fgt, 0.5, 0.95, 0.05)
        else:
            raise ValueError(f"Unknown VSI-Bench question_type: {qtype}")

        by_qtype[qtype].append(score)
        srec = dict(rec)
        srec["official_fuzzy_pred"] = fuzzy_pred
        srec["official_score"] = score
        srec["official_status"] = status_str
        srec["hit_token_cap"] = hit_cap
        scored_records.append(srec)

    output: Dict[str, float] = {}
    for qtype, vals in by_qtype.items():
        output[f"{qtype}_accuracy"] = sum(vals) / len(vals)

    rel_dir_keys = [
        "object_rel_direction_easy_accuracy",
        "object_rel_direction_medium_accuracy",
        "object_rel_direction_hard_accuracy",
    ]
    if all(k in output for k in rel_dir_keys):
        output["object_rel_direction_accuracy"] = (
            output.pop("object_rel_direction_easy_accuracy")
            + output.pop("object_rel_direction_medium_accuracy")
            + output.pop("object_rel_direction_hard_accuracy")
        ) / 3.0

    overall = sum(output.values()) / len(output) if output else 0.0
    output["overall"] = overall

    per_task_pct = {
        k.replace("_accuracy", ""): round(v * 100.0, 2)
        for k, v in sorted(output.items())
        if k != "overall"
    }
    raw_cat_scores = {
        qtype: (sum(vals) / len(vals)) for qtype, vals in sorted(by_qtype.items())
    }
    return {
        "benchmark": "vsibench_full",
        "metric": "vsibench-official-8task-v1",
        "total_questions": len(records),
        "overall_score": overall,
        "overall_score_pct": round(overall * 100.0, 2),
        "per_task_score_pct": per_task_pct,
        "raw_subtask_score_pct": {
            qtype: round((sum(vals) / len(vals)) * 100.0, 2)
            for qtype, vals in sorted(by_qtype.items())
        },
        "raw_category_scores": raw_cat_scores,
        "cap_count": cap_count,
        "cap_without_answer_count": cap_without_answer_count,
        "parse_failures": sum(failure_counts.values()),
        "failure_counts": dict(failure_counts),
        "scored_records": scored_records,
    }


def write_official_full_to_results_dir(
    res: Dict[str, Any],
    proto: Dict[str, Any],
    cell_name: str,
    results_dir: str,
) -> Dict[str, Any]:
    scored_records = res["scored_records"]
    scored_records_sorted = sorted(
        scored_records, key=lambda r: str(r["example_id"])
    )
    items_list: List[List[Any]] = []
    pq_lines: List[str] = []

    for srec in scored_records_sorted:
        ex_id = str(srec["example_id"])
        qtype = str(srec["question_type"])
        score = float(srec["official_score"])
        status_str = str(srec.get("official_status") or "ok")
        items_list.append([ex_id, qtype, score, status_str])

        pq_row = {
            "example_id": ex_id,
            "raw_id": srec.get("raw_id"),
            "dataset": srec.get("dataset"),
            "scene_name": srec.get("scene_name"),
            "question_type": qtype,
            "answer_type": infer_answer_type(srec),
            "ground_truth": str(srec["ground_truth"]).strip(),
            "response_text": srec.get("response_text", ""),
            "official_fuzzy_pred": srec.get("official_fuzzy_pred"),
            "score": score,
            "status": status_str,
            "num_frames": srec.get("num_frames"),
            "input_tokens": srec.get("input_tokens"),
            "output_tokens": srec.get("output_tokens"),
            "hit_token_cap": srec.get("hit_token_cap", False),
            "elapsed_s": srec.get("elapsed_s"),
        }
        if "extract_branch" in srec:
            pq_row["extract_branch"] = srec["extract_branch"]
        pq_lines.append(json.dumps(pq_row, sort_keys=True, ensure_ascii=False))

    pq_blob = ("\n".join(pq_lines) + "\n").encode("utf-8")
    pq_sha256 = hashlib.sha256(pq_blob).hexdigest()
    scores_sha256 = hashlib.sha256(
        json.dumps(items_list, sort_keys=True).encode("utf-8")
    ).hexdigest()

    category_scores = res["raw_category_scores"]
    raw_category_macro = (
        sum(category_scores.values()) / len(category_scores)
        if category_scores
        else 0.0
    )
    cfg_sha = proto.get("config_sha256") or (
        scored_records[0].get("config_sha256") if scored_records else ""
    )

    items_doc = {
        "benchmark": "vsibench_full",
        "cap_count": res["cap_count"],
        "cap_without_answer_count": res["cap_without_answer_count"],
        "category_scores": category_scores,
        "per_task_score_pct": res["per_task_score_pct"],
        "cell": cell_name,
        "config_sha256": cfg_sha,
        "protocol": proto,
        "coverage_complete": len(scored_records) == 5130,
        "expected_count": 5130,
        "failure_counts": res["failure_counts"],
        "items": items_list,
        "metric": "vsibench-official-8task-v1",
        "missing_count": max(0, 5130 - len(scored_records)),
        "official_aggregation_complete": True,
        "parse_failures": res["parse_failures"],
        "per_question_bound": True,
        "per_question_sha256": pq_sha256,
        "primary_score": res["overall_score"],
        "pulled_pt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "raw_category_macro": raw_category_macro,
        "recompute_matches_official": True,
        "recomputed_primary_score": res["overall_score"],
        "result_status": "COMPLETE",
        "scores_sha256": scores_sha256,
        "started_count": len(scored_records),
        "terminal_count": len(scored_records),
    }

    os.makedirs(results_dir, exist_ok=True)
    items_path = os.path.join(results_dir, f"{cell_name}.items.json")
    pq_path = os.path.join(results_dir, f"{cell_name}.per_question_scores.jsonl")
    with open(pq_path, "wb") as f:
        f.write(pq_blob)
    with open(items_path, "w", encoding="utf-8") as f:
        json.dump(items_doc, f, sort_keys=True)
        f.write("\n")

    update_summary_files(results_dir, cell_name, "vsibench_full", items_doc)
    return items_doc


def score_our_cell(
    records: List[Dict[str, Any]],
    cell_name: str,
    benchmark_name: str,
    expected_count: int,
    proto: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    if benchmark_name == "vsibench_answerable500":
        primary_groups = VSI_PRIMARY_GROUPS
        metric_name = "vsibench-official-8task-v1"
    elif benchmark_name in ("vstibench_repr450_v3", "vstibench_repr450_v2"):
        primary_groups = VSTI_PRIMARY_GROUPS
        metric_name = "vstibench-official-5task-v1"
    else:
        raise ValueError(f"Unsupported benchmark_name: {benchmark_name}")

    if expected_count > 0 and len(records) != expected_count:
        raise RuntimeError(
            f"Incomplete cell {cell_name} ({benchmark_name}): got {len(records)} records, expected {expected_count}"
        )
    canon_ids = load_canonical_id_set(benchmark_name)
    if canon_ids is not None and expected_count == len(canon_ids):
        actual_ids = sorted(str(r["example_id"]) for r in records)
        if actual_ids != sorted(canon_ids):
            missing = sorted(set(canon_ids) - set(actual_ids))[:5]
            extra = sorted(set(actual_ids) - set(canon_ids))[:5]
            raise RuntimeError(
                f"Question ID set mismatch for {cell_name} ({benchmark_name}): missing={missing}, extra={extra}"
            )

    records_sorted = sorted(
        records,
        key=lambda r: (
            int(str(r["example_id"]))
            if str(r["example_id"]).isdigit()
            else str(r["example_id"])
        ),
    )

    by_cat_strict: Dict[str, List[float]] = defaultdict(list)
    by_cat_fuzzy: Dict[str, List[float]] = defaultdict(list)
    failure_counts: Counter = Counter()
    parse_failures = 0
    cap_count = 0
    cap_without_answer_count = 0
    items_list: List[List[Any]] = []
    per_question_rows: List[Dict[str, Any]] = []

    for rec in records_sorted:
        ex_id = str(rec["example_id"])
        qtype = str(rec["question_type"])
        gt = str(rec["ground_truth"]).strip()
        ans_type = infer_answer_type(rec)
        resp_text = str(rec.get("response_text", ""))
        opts = rec.get("options")
        out_tok = int(rec.get("output_tokens") or 0)
        max_tok = int(rec.get("max_new_tokens") or 0)

        hit_cap = bool(max_tok > 0 and out_tok >= max_tok)
        if hit_cap:
            cap_count += 1

        parsed = parse_answer_v1(resp_text, ans_type, opts)
        p_ans = parsed["parsed_answer"]
        p_status = parsed["parse_status"]
        p_err = parsed["parse_error_reason"]

        if p_status != "ok" or p_ans is None:
            parse_failures += 1
            status_str = f"parse_failed:{p_err}"
            failure_counts[status_str] += 1
            if hit_cap:
                cap_without_answer_count += 1
            strict_score = 0.0
        else:
            status_str = "ok"
            if ans_type == "multiple_choice":
                strict_score = official_exact_match(p_ans, gt)
            else:
                strict_score = official_mra(
                    official_to_float(p_ans), official_to_float(gt), 0.5, 0.95, 0.05
                )

        fuzzy_pred = official_fuzzy_matching(resp_text)
        if ans_type == "multiple_choice":
            fuzzy_score = official_exact_match(fuzzy_pred, gt)
        else:
            fuzzy_score = official_mra(
                official_to_float(fuzzy_pred), official_to_float(gt), 0.5, 0.95, 0.05
            )

        by_cat_strict[qtype].append(strict_score)
        by_cat_fuzzy[qtype].append(fuzzy_score)
        items_list.append([ex_id, qtype, strict_score, status_str])

        pq_row = {
            "example_id": ex_id,
            "raw_id": rec.get("raw_id"),
            "dataset": rec.get("dataset"),
            "scene_name": rec.get("scene_name"),
            "question_type": qtype,
            "answer_type": ans_type,
            "ground_truth": gt,
            "response_text": resp_text,
            "parsed_answer": p_ans,
            "parse_status": p_status,
            "parse_error_reason": p_err,
            "parser_branch": parsed["parser_branch"],
            "score": strict_score,
            "official_fuzzy_pred": fuzzy_pred,
            "official_fuzzy_score": fuzzy_score,
            "status": status_str,
            "num_frames": rec.get("num_frames"),
            "input_tokens": rec.get("input_tokens"),
            "output_tokens": out_tok,
            "hit_token_cap": hit_cap,
            "elapsed_s": rec.get("elapsed_s"),
        }
        per_question_rows.append(pq_row)

    category_scores = {
        cat: (sum(vals) / len(vals)) for cat, vals in sorted(by_cat_strict.items())
    }
    fuzzy_category_scores = {
        cat: (sum(vals) / len(vals)) for cat, vals in sorted(by_cat_fuzzy.items())
    }

    primary_task_scores: Dict[str, float] = {}
    fuzzy_primary_task_scores: Dict[str, float] = {}
    for group_name, sub_cats in primary_groups.items():
        present = [category_scores[c] for c in sub_cats if c in category_scores]
        if present:
            primary_task_scores[group_name] = sum(present) / len(present)
        present_f = [
            fuzzy_category_scores[c] for c in sub_cats if c in fuzzy_category_scores
        ]
        if present_f:
            fuzzy_primary_task_scores[group_name] = sum(present_f) / len(present_f)

    primary_score = (
        sum(primary_task_scores.values()) / len(primary_task_scores)
        if primary_task_scores
        else 0.0
    )
    fuzzy_primary_score = (
        sum(fuzzy_primary_task_scores.values()) / len(fuzzy_primary_task_scores)
        if fuzzy_primary_task_scores
        else 0.0
    )
    raw_category_macro = (
        sum(category_scores.values()) / len(category_scores)
        if category_scores
        else 0.0
    )

    items_sorted_for_json = sorted(items_list, key=lambda x: str(x[0]))
    pq_lines = [
        json.dumps(r, sort_keys=True, ensure_ascii=False) for r in per_question_rows
    ]
    pq_blob = ("\n".join(pq_lines) + "\n").encode("utf-8")
    pq_sha256 = hashlib.sha256(pq_blob).hexdigest()
    scores_sha256 = hashlib.sha256(
        json.dumps(items_sorted_for_json, sort_keys=True).encode("utf-8")
    ).hexdigest()

    cfg_sha = (proto or {}).get("config_sha256") or (
        records_sorted[0].get("config_sha256") if records_sorted else ""
    )
    items_doc = {
        "benchmark": benchmark_name,
        "cap_count": cap_count,
        "cap_without_answer_count": cap_without_answer_count,
        "category_scores": category_scores,
        "fuzzy_category_scores": fuzzy_category_scores,
        "primary_task_scores": primary_task_scores,
        "fuzzy_primary_task_scores": fuzzy_primary_task_scores,
        "cell": cell_name,
        "config_sha256": cfg_sha,
        "protocol": proto or {},
        "coverage_complete": len(records_sorted) == expected_count,
        "expected_count": expected_count,
        "failure_counts": dict(failure_counts),
        "items": items_sorted_for_json,
        "metric": metric_name,
        "missing_count": max(0, expected_count - len(records_sorted)),
        "official_aggregation_complete": len(primary_task_scores) == len(primary_groups),
        "parse_failures": parse_failures,
        "per_question_bound": True,
        "per_question_sha256": pq_sha256,
        "primary_score": primary_score,
        "fuzzy_primary_score": fuzzy_primary_score,
        "pulled_pt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "raw_category_macro": raw_category_macro,
        "recompute_matches_official": True,
        "recomputed_primary_score": primary_score,
        "result_status": "COMPLETE"
        if len(records_sorted) == expected_count
        else "PARTIAL",
        "scores_sha256": scores_sha256,
        "started_count": len(records_sorted),
        "terminal_count": len(records_sorted),
    }
    return items_doc, per_question_rows


def update_summary_files(
    results_dir: str, cell_name: str, benchmark_name: str, items_doc: Dict[str, Any]
) -> None:
    tsv_path = os.path.join(results_dir, "SUMMARY.tsv")
    json_path = os.path.join(results_dir, "SUMMARY.json")
    score_pct = round(items_doc["primary_score"] * 100.0, 2)
    count = items_doc["terminal_count"]

    rows_by_cell: Dict[str, str] = {}
    header = "cell\tbenchmark\tprimary_score_pct\titems"
    if os.path.exists(tsv_path):
        with open(tsv_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                line = line.rstrip("\n")
                if not line:
                    continue
                if idx == 0 and line.startswith("cell\t"):
                    header = line
                    continue
                parts = line.split("\t")
                if parts:
                    rows_by_cell[parts[0]] = line

    rows_by_cell[cell_name] = f"{cell_name}\t{benchmark_name}\t{score_pct}\t{count}"
    with open(tsv_path, "w", encoding="utf-8") as f:
        f.write(header + "\n")
        for k in sorted(rows_by_cell.keys()):
            f.write(rows_by_cell[k] + "\n")

    summary_json: Dict[str, Any] = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                summary_json = json.load(f)
        except Exception:
            summary_json = {}

    summary_json[cell_name] = [benchmark_name, score_pct, count]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary_json, f, indent=2, sort_keys=True)
        f.write("\n")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["official_full", "our_cell"], required=True)
    p.add_argument(
        "--input", required=True, help="predictions.jsonl file or directory of shards"
    )
    p.add_argument("--output_dir", default="", help="Output directory for official_full")
    p.add_argument(
        "--results_dir",
        default="",
        help="Results directory for our_cell or official_full (.items.json / SUMMARY.tsv)",
    )
    p.add_argument("--cell_name", default="", help="Cell name for our_cell or official_full")
    p.add_argument(
        "--benchmark",
        default="vsibench_answerable500",
        help="vsibench_answerable500, vstibench_repr450_v3, or vsibench_full",
    )
    p.add_argument("--expected_count", type=int, default=0)
    p.add_argument("--update_summary", action="store_true")
    args = p.parse_args()

    records, proto = load_predictions_with_protocol(args.input)
    if args.mode == "official_full":
        exp = args.expected_count if args.expected_count > 0 else 5130
        res = score_official_vsibench(records, expected_count=exp)
        scored_records = res.pop("scored_records")
        res["config_sha256"] = proto.get("config_sha256", "")
        res["protocol"] = proto
        if args.output_dir:
            os.makedirs(args.output_dir, exist_ok=True)
            with open(
                os.path.join(args.output_dir, "summary.json"), "w", encoding="utf-8"
            ) as f:
                json.dump(res, f, indent=2, sort_keys=True)
            with open(
                os.path.join(args.output_dir, "scored_predictions.jsonl"),
                "w",
                encoding="utf-8",
            ) as f:
                for srec in scored_records:
                    f.write(json.dumps(srec, ensure_ascii=False) + "\n")
        if args.results_dir and args.cell_name:
            res_with_records = dict(res)
            res_with_records["scored_records"] = scored_records
            items_doc = write_official_full_to_results_dir(
                res_with_records, proto, args.cell_name, args.results_dir
            )
            res["items_json_path"] = os.path.join(
                args.results_dir, f"{args.cell_name}.items.json"
            )
            res["primary_score"] = items_doc["primary_score"]
        print(json.dumps(res, indent=2, sort_keys=True))
    elif args.mode == "our_cell":
        if not args.cell_name:
            raise ValueError("--cell_name is required for --mode our_cell")
        exp = args.expected_count
        if exp <= 0:
            exp = 500 if "vsi" in args.benchmark and "vsti" not in args.benchmark else 450
        items_doc, pq_rows = score_our_cell(
            records, args.cell_name, args.benchmark, exp, proto=proto
        )
        if args.results_dir:
            os.makedirs(args.results_dir, exist_ok=True)
            items_path = os.path.join(args.results_dir, f"{args.cell_name}.items.json")
            pq_path = os.path.join(
                args.results_dir, f"{args.cell_name}.per_question_scores.jsonl"
            )
            with open(items_path, "w", encoding="utf-8") as f:
                json.dump(items_doc, f, sort_keys=True)
                f.write("\n")
            with open(pq_path, "w", encoding="utf-8") as f:
                for r in pq_rows:
                    f.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")
            if args.update_summary:
                update_summary_files(
                    args.results_dir, args.cell_name, args.benchmark, items_doc
                )
        summary_out = {
            "cell": args.cell_name,
            "benchmark": args.benchmark,
            "items": len(pq_rows),
            "strict_primary_score_pct": round(items_doc["primary_score"] * 100.0, 2),
            "fuzzy_primary_score_pct": round(
                items_doc["fuzzy_primary_score"] * 100.0, 2
            ),
            "parse_failures": items_doc["parse_failures"],
            "cap_count": items_doc["cap_count"],
            "primary_task_scores_pct": {
                k: round(v * 100.0, 2)
                for k, v in items_doc["primary_task_scores"].items()
            },
            "fuzzy_primary_task_scores_pct": {
                k: round(v * 100.0, 2)
                for k, v in items_doc["fuzzy_primary_task_scores"].items()
            },
        }
        print(json.dumps(summary_out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
