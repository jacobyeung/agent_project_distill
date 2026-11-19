"""Head-call evaluation summary of one scored cell: strict accuracy, a lenient rescore reported apart, and call metrics.

Inputs: the cell's score directory (orchard_eval score: scores.json) and its run directory (generations.jsonl and, for
a head-call arm, headcalls/<qid>.json from orchard_eval generate --headcall decode).

Strict: the evaluator's own parse (student-answer-v1: the last non-empty line after the last </think> is one option
letter or one bare finite number) and the canonical scorer, read from scores.json and per_question_scores.jsonl.

Lenient (reported apart, never the primary score): this tree has no lenient answer parser, so the rule is documented
here. After the last </think> (the whole text when there is none), with <|im_end|>/<|endoftext|> removed:
  multiple choice: the last supplied option letter that stands alone (A, (A), A., A:, A), "answer: A", "option A") on the
  last non-empty line, else anywhere in that suffix;
  numeric: the last finite number on the last non-empty line, else anywhere in the suffix (a trailing unit is ignored).
A strict parse is kept as is; the lenient rule only fills strict failures. The lenient answer is scored with the same
canonical scorer entry (_score_entry) and aggregated with the same category rule.

Call metrics (head-call arms): calls per item, valid, strict, lenient (executed after a parser repair), refused
(error responses, by code), items with zero calls, the value-used-downstream rate (headcall.eval_hook.downstream_usage:
a response's literal or a value derived from it appears later in the trace), per question type.

usage: python tools/headcall_eval_summary.py --score SCORE_DIR --run RUN_DIR --out SUMMARY.json
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCHEMA = "headcall-eval-summary-v1"
NUMBER = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")


def visible_suffix(raw):
    text = re.split(r"</think\s*>", raw or "", flags=re.IGNORECASE)[-1]
    return re.sub(r"<\|(?:im_end|endoftext)\|>", "", text).strip()


def lenient_payload(raw, letters):
    """The lenient answer text (a letter or a number) of one generation, or None."""
    suffix = visible_suffix(raw)
    if not suffix:
        return None
    lines = [line.strip() for line in suffix.splitlines() if line.strip()]
    scopes = [lines[-1], suffix] if lines else [suffix]
    for scope in scopes:
        if letters:
            pattern = r"(?<![A-Za-z])\(?([%s])\)?(?![A-Za-z])" % "".join(letters)
            found = re.findall(pattern, scope)
            if found:
                return found[-1].upper()
        else:
            found = NUMBER.findall(scope)
            if found:
                return found[-1]
    return None


def lenient_answer(raw, options):
    """(answer, how): the strict parse when it succeeds, else the lenient rule normalized by the strict parser."""
    from student_pilot.orchard_eval.answers import option_letters, parse_answer

    strict = parse_answer(raw, options)
    if strict["answer"] is not None:
        return strict["answer"], "strict"
    payload = lenient_payload(raw, option_letters(options))
    if payload is None:
        return None, "none"
    normalized = parse_answer(payload, options)["answer"]
    return normalized, "lenient" if normalized is not None else "none"


def call_metrics(records, raws, categories):
    from headcall.eval_hook import downstream_usage

    totals, by_type = Counter(), defaultdict(Counter)
    errors = Counter()
    for qid, record in records.items():
        summary = record["summary"]
        usage = downstream_usage(raws[qid])
        used = sum(item["used"] for item in usage)
        row = Counter(items=1, calls=summary["calls"], valid_calls=summary["valid_calls"],
                      strict_calls=summary["strict_calls"], lenient_calls=summary["lenient_calls"],
                      refused_calls=summary["calls"] - summary["valid_calls"], inserted_tokens=summary["inserted_tokens"],
                      zero_call_items=int(summary["calls"] == 0), exchanges=len(usage), used_exchanges=used,
                      items_with_used_value=int(used > 0), capped_items=int(summary["finish_reason"] == "max_new_tokens"))
        totals.update(row)
        by_type[categories.get(qid, "unknown")].update(row)
        errors.update(call["error_code"] for call in record["calls"] if call["error_code"] is not None)

    def rates(counts):
        items, calls = max(1, counts["items"]), max(1, counts["calls"])
        return {**dict(counts), "calls_per_item": counts["calls"] / items, "valid_call_rate": counts["valid_calls"] / calls,
                "strict_call_rate": counts["strict_calls"] / calls, "lenient_call_rate": counts["lenient_calls"] / calls,
                "refused_call_rate": counts["refused_calls"] / calls,
                "value_used_rate": counts["used_exchanges"] / max(1, counts["exchanges"]),
                "items_with_used_value_rate": counts["items_with_used_value"] / items,
                "zero_call_item_rate": counts["zero_call_items"] / items}
    return {"overall": rates(totals), "error_codes": dict(sorted(errors.items())),
            "by_question_type": {name: rates(counts) for name, counts in sorted(by_type.items())}}


def summarize(score_dir, run_dir):
    from student_pilot.common import load_json
    from student_pilot.orchard_eval.contracts import load_generation, load_jsonl, safe_id
    from student_pilot.orchard_eval.score import aggregate_categories, canonical_scorer

    score_dir, run_dir = Path(score_dir), Path(run_dir)
    scores = load_json(score_dir / "scores.json")
    manifest = load_json(scores["scoring_manifest"]["path"])
    labels = load_jsonl(manifest["labels"]["path"])
    _, rows, _ = load_generation(manifest["generation"]["path"])
    receipts = {row["qid"]: row for row in load_jsonl(run_dir / "generations.jsonl")}
    strict_rows = {row["qid"]: row for row in load_jsonl(scores["per_question_scores"]["path"])}
    scorer, core = canonical_scorer(manifest["scorer"])
    credits, counts, how = defaultdict(list), Counter(), Counter()
    per_question = []
    for row, label in zip(rows, labels):
        qid = row["qid"]
        receipt = receipts.get(qid)
        raw = receipt["raw_generation"] if receipt and receipt["status"] == "ok" else ""
        answer, source = lenient_answer(raw, row["student_input"]["options"]) if raw else (None, "none")
        projection = {"question_id": qid, "trace": {"messages": [
            {"role": "ai", "content": f"<ANSWER>{answer}</ANSWER>" if answer is not None else "", "tool_calls": []}]}}
        record, _ = scorer._score_entry(projection, label, strict=True)
        credit = record["accuracy"] if "accuracy" in record else record["MRA"]
        credits[label["question_type"]].append(credit)
        counts[label["question_type"]] += 1
        how[source] += 1
        per_question.append({"qid": qid, "category": label["question_type"], "strict_credit": strict_rows[qid]["credit"],
                             "lenient_credit": credit, "lenient_answer": answer, "answer_source": source})
    values = {name: scorer.canonical_mean(items) for name, items in sorted(credits.items())}
    lenient = aggregate_categories(values, manifest["benchmark"], scorer, core, counts, paper=False)
    result = {"schema": SCHEMA, "score": str(score_dir), "run": str(run_dir), "benchmark": manifest["benchmark"],
              "strict": {"primary_score": scores["primary_score"], "category_scores": scores["category_scores"],
                         "parse_failures": scores["parse_failures"], "cap_count": scores["cap_count"]},
              "lenient": {"primary_score": lenient["primary_score"], "category_scores": lenient["category_scores"],
                          "answer_sources": dict(how),
                          "rule": "strict parse, else the last standalone option letter / finite number after </think>"},
              "per_question": per_question}
    headcalls = run_dir / "headcalls"
    if headcalls.is_dir():
        records = {}
        for row in rows:
            path = headcalls / f"{safe_id(row['qid'])}.json"
            if path.exists():
                records[row["qid"]] = load_json(path)
        ok = {qid for qid, receipt in receipts.items() if receipt["status"] == "ok"}
        if set(records) != ok:
            raise ValueError(f"Head-call records cover {len(records)} items, {len(ok)} generations are ok")
        categories = {label["id"]: label["question_type"] for label in labels}
        result["calls"] = call_metrics(records, {qid: receipts[qid]["raw_generation"] for qid in records}, categories)
    return result


def main(argv=None):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('tools/headcall_eval_summary.py:main')
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--score", required=True)
    parser.add_argument("--run", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    out = Path(args.out)
    if out.exists():
        raise SystemExit("the summary already exists: " + str(out))
    result = summarize(args.score, args.run)
    out.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"strict": result["strict"]["primary_score"], "lenient": result["lenient"]["primary_score"],
                      "calls": result.get("calls", {}).get("overall", {}).get("calls_per_item")}))


if __name__ == "__main__":
    main()
