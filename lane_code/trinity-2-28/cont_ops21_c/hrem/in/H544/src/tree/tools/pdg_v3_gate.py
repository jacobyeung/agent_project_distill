"""Score a partial eval cell (one shard) against reference cells on the same items, and apply the PDG v3 S1->S2 gate.

Credits follow the evaluator's canonical scorer: a multiple-choice item scores 1 when the parsed letter equals the
ground truth; a numeric item scores VSI-Bench's mean relative accuracy, the share of the 10 thresholds
linspace(0.5, 0.95, 10) with |pred - gt| / gt <= 1 - threshold. Ground truth and category come from a complete
reference cell's per_question_scores.jsonl. `--validate` re-scores a complete cell's own question records and must
reproduce its official credits.

Gate (PDG_V3_DESIGN.md): the candidate fails when it scores below the base on the paired items and the paired
bootstrap 95% interval of (candidate - base) lies entirely below 0, when fewer than --min-items items are scored, or when
every answer is unparsed. Exit status 0 = PASS, 3 = FAIL.

With --base-questions, the candidate also fails when its median generated length on the paired items is under half the
base's (a model that stops thinking, the PDG v1/v2 stage-1 signature).

usage: pdg_v3_gate.py QUESTIONS_DIR --base BASE_PQS [--base-questions DIR] [--compare NAME=PQS ...] [--validate OWN_PQS]
                      [--out JSON]
"""
import argparse
import json
import random
import re
import statistics
import sys
from pathlib import Path

THRESHOLDS = [0.5 + 0.05 * i for i in range(10)]
LETTER = re.compile(r"[A-Z]")


def credit(parsed, gt):
    if parsed is None:
        return 0.0
    if LETTER.fullmatch(str(gt)):
        return float(str(parsed).upper() == str(gt))
    try:
        pred, target = float(parsed), float(gt)
    except ValueError:
        return 0.0
    if target == 0:
        return float(pred == 0)
    distance = abs(pred - target) / abs(target)
    return sum(distance <= 1 - t + 1e-12 for t in THRESHOLDS) / len(THRESHOLDS)


def load_pqs(path):
    out = {}
    for line in Path(path).read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            out[str(row["qid"])] = row
    return out


def load_questions(directory):
    records = {}
    for path in sorted(Path(directory).glob("*.json")):
        record = json.loads(path.read_text())
        if record.get("status") == "ok" or record.get("raw_generation") is not None:
            records[str(record["qid"])] = record
    return records


def bootstrap(diffs, draws=10000, seed=17):
    rng = random.Random(seed)
    n = len(diffs)
    means = sorted(sum(diffs[rng.randrange(n)] for _ in range(n)) / n for _ in range(draws))
    return means[int(0.025 * draws)], means[int(0.975 * draws) - 1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("questions")
    parser.add_argument("--base", required=True)
    parser.add_argument("--compare", action="append", default=[])
    parser.add_argument("--validate")
    parser.add_argument("--base-questions", help="the base cell's question records: adds the generation-length check")
    parser.add_argument("--min-items", type=int, default=100, help="fail with fewer scored (and length-paired) items")
    parser.add_argument("--out")
    args = parser.parse_args()
    base = load_pqs(args.base)
    records = load_questions(args.questions)
    qids = sorted(q for q in records if q in base)
    scores = {q: credit(records[q].get("parsed_answer"), base[q]["canonical_metrics"]["gt_ans"]) for q in qids}
    report = {"items": len(qids), "candidate": statistics.mean(scores.values()) if qids else None,
              "parse_failures": sum(records[q].get("parsed_answer") is None for q in qids),
              "cap_hits": sum(records[q].get("finish_reason") != "eos" for q in qids),
              "median_generated_tokens": statistics.median(records[q].get("generated_tokens", 0) for q in qids) if qids else None}
    if args.validate:
        own = load_pqs(args.validate)
        bad = [q for q in qids if q in own and abs(own[q]["credit"] - scores[q]) > 1e-9]
        report["validate"] = {"checked": sum(q in own for q in qids), "mismatches": len(bad), "first": bad[:5]}
    diffs = [scores[q] - base[q]["credit"] for q in qids]
    report["base"] = statistics.mean(base[q]["credit"] for q in qids) if qids else None
    report["diff_vs_base"] = statistics.mean(diffs) if qids else None
    report["diff_ci95"] = bootstrap(diffs) if qids else None
    for item in args.compare:
        name, _, path = item.partition("=")
        other = load_pqs(path)
        paired = [q for q in qids if q in other]
        if paired:
            report[f"compare_{name}"] = {"items": len(paired), "score": statistics.mean(other[q]["credit"] for q in paired),
                                         "candidate_on_same": statistics.mean(scores[q] for q in paired)}
    categories = {}
    for q in qids:
        categories.setdefault(base[q]["category"], []).append((scores[q], base[q]["credit"]))
    report["per_category"] = {c: {"n": len(v), "candidate": round(statistics.mean(a for a, _ in v), 3),
                                  "base": round(statistics.mean(b for _, b in v), 3)} for c, v in sorted(categories.items())}
    low, high = report["diff_ci95"] or (0, 0)
    failed = report["diff_vs_base"] is not None and report["diff_vs_base"] < 0 and high < 0
    reasons = ["score below base with the 95% interval below 0"] if failed else []
    if len(qids) < args.min_items or (qids and report["parse_failures"] == len(qids)):
        failed = True
        reasons.append(f"{len(qids)} scored items (minimum {args.min_items}) or every answer unparsed")
    if args.base_questions:
        base_records = load_questions(args.base_questions)
        paired = [q for q in qids if q in base_records]
        base_tokens = statistics.median(base_records[q].get("generated_tokens", 0) for q in paired) if paired else None
        cand_tokens = statistics.median(records[q].get("generated_tokens", 0) for q in paired) if paired else None
        report["length_check"] = {"items": len(paired), "base_median_tokens": base_tokens, "candidate_median_tokens": cand_tokens}
        if len(paired) < args.min_items or cand_tokens < 0.5 * base_tokens:
            failed = True
            reasons.append("generation length under half the base's, or too few length-paired items")
    report["gate"] = "FAIL" if failed else "PASS"
    report["gate_reasons"] = reasons
    text = json.dumps(report, indent=1, sort_keys=True)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n")
    sys.exit(3 if report["gate"] == "FAIL" else 0)


if __name__ == "__main__":
    main()
