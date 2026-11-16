"""Verbatim official protocol functions; source pins in SOURCE_PINS.json."""

from typing import Any, Dict, List, Optional, Tuple

from collections import Counter, defaultdict

from decimal import Decimal, InvalidOperation

import hashlib, json, math, os, re, time

CANONICAL_IDS_FILE = os.path.join(os.path.dirname(__file__), "canonical_cell_ids.json")

DEFAULT_ANSWER_FORMAT_INSTRUCTION = (
    "Think it through, then finish with the final answer alone on the last line: "
    "the option letter for a multiple-choice question, or the number for a numeric question."
)

_BLOCK_RE = re.compile(r"<answer\s*>(.*?)</answer\s*>", re.IGNORECASE | re.DOTALL)

def build_prompt_context(row: Dict[str, Any], prompt_mode: str) -> str:
    question_text = str(row["question"])
    options = row.get("options")
    has_options = isinstance(options, list) and len(options) > 0

    if prompt_mode == "official":
        pre_prompt = "These are frames of a video."
        if has_options:
            options_prompt = "Options:\n" + "\n".join(str(x) for x in options)
            post_prompt = "Answer with the option's letter from the given choices directly."
            return f"{pre_prompt}\n{question_text}\n{options_prompt}\n{post_prompt}"
        else:
            post_prompt = "Please answer the question using a single word or phrase."
            return f"{pre_prompt}\n{question_text}\n{post_prompt}"
    elif prompt_mode == "ours":
        opt_block = "\n".join(str(x) for x in options) if has_options else ""
        constructed = (
            question_text
            + ("\n" + opt_block if opt_block else "")
            + "\n\n"
            + DEFAULT_ANSWER_FORMAT_INSTRUCTION
        )
        if "text" in row and row["text"]:
            if row["text"] != constructed:
                raise ValueError(
                    f"Constructed prompt does not match row['text'] for {row.get('example_id')}: "
                    f"{constructed!r} != {row['text']!r}"
                )
        return constructed
    else:
        raise ValueError(f"Unsupported prompt_mode: {prompt_mode}")

def extract_q35_final_answer(raw_text: str, enable_thinking: bool) -> Tuple[str, str]:
    if not isinstance(raw_text, str) or not raw_text.strip():
        return "", "empty_generation"
    close_matches = list(re.finditer(r"</think\s*>", raw_text, flags=re.IGNORECASE))
    if enable_thinking and not close_matches:
        return "", "unclosed_thinking"
    text = raw_text[close_matches[-1].end() :] if close_matches else raw_text
    if re.search(r"<think\s*>", text, flags=re.IGNORECASE):
        return "", "unclosed_thinking"
    text = re.sub(r"(?:\s*<\|(?:im_end|endoftext)\|>)+\s*$", "", text).strip()
    matches = list(_BLOCK_RE.finditer(text))
    if matches:
        return matches[-1].group(1).strip(), "tag"
    lines = [m.group(0).strip() for m in re.finditer(r"[^\r\n]+", text) if m.group(0).strip()]
    if not lines:
        return "", "empty_visible_suffix"
    payload = re.sub(
        r"^(?:final\s+answer|answer)\s*:\s*", "", lines[-1], flags=re.IGNORECASE
    ).strip()
    return payload, "final_line"

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
