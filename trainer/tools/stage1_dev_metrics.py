"""Held-out geometry error of a stage-1 checkpoint and the growth rule for the stage-1 question set.

Input: the dev rows (their `category` and `answer`) and one predictions JSONL per evaluated checkpoint
({"qid", "prediction"} with the raw final answer text). Scoring per category:
  - multiple choice (one option letter): error = 1 - accuracy;
  - one number (metres, degrees): error = 1 - MRA, MRA = mean over thresholds 0.50..0.95 of
    [|pred - gt| / |gt| < 1 - threshold] (the VSI-Bench numeric metric);
  - a 3D point "(x, y, z)" (optionally "label (x, y, z)"): error = 1 - MRA of the Euclidean distance
    relative to the ground-truth point's distance from the origin (frame 1's camera), floored at 0.5 m;
  - a signed heading in degrees (camera_heading_vs_frame1): error = 1 - MRA of the wrapped angular difference
    relative to |gt|, floored at 10 degrees.
An unparseable prediction scores error 1. The aggregate is the mean of the category errors.

Growth rule (USER 10-30): train on block 0 (200k); at the end of each epoch compare the aggregate with the
evaluation one quarter-epoch earlier. Grow by one more 200k block only if the error is still falling by more
than max(0.005, 2 x its paired bootstrap standard error); otherwise stop stage 1 at this checkpoint.

  python tools/stage1_dev_metrics.py --dev DEV.jsonl --earlier PRED_A.jsonl --end PRED_B.jsonl
"""
import argparse
import json
import math
import random
import re
import sys
from pathlib import Path

THRESHOLDS = [0.5 + 0.05 * index for index in range(10)]
NUMBER = re.compile(r"[-+]?\d+(?:\.\d+)?")
POINT = re.compile(r"\(\s*([-+]?\d+(?:\.\d+)?)\s*,\s*([-+]?\d+(?:\.\d+)?)\s*,\s*([-+]?\d+(?:\.\d+)?)\s*\)")
LETTER = re.compile(r"^[A-Z]$")
MIN_DELTA = 0.005
POINT_FLOOR_M = 0.5


def kind(answer):
    if LETTER.fullmatch(answer.strip()):
        return "choice"
    if POINT.search(answer):
        return "point"
    if NUMBER.fullmatch(answer.strip()):
        return "number"
    raise ValueError(f"Unsupported stage-1 answer form: {answer!r}")


def final_answer(text):
    """The text after the last </think>, last non-empty line (the student's answer line)."""
    tail = text.rsplit("</think>", 1)[-1]
    lines = [line.strip() for line in tail.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def mra(error, scale):
    relative = error / max(scale, 1e-9)
    return sum(relative < 1 - threshold for threshold in THRESHOLDS) / len(THRESHOLDS)


HEADING_FLOOR_DEG = 10.0


def item_error(answer, prediction, category=None):
    form, text = kind(answer), final_answer(prediction)
    if form == "choice":
        letters = re.findall(r"\b([A-Z])\b", text)
        return 0.0 if letters and letters[-1] == answer.strip() else 1.0
    if form == "number":
        found = NUMBER.findall(text)
        if not found:
            return 1.0
        gt, value = float(answer), float(found[-1])
        if category == "camera_heading_vs_frame1":
            difference = abs((value - gt + 180.0) % 360.0 - 180.0)
            return 1.0 - mra(difference, max(abs(gt), HEADING_FLOOR_DEG))
        return 1.0 - mra(abs(value - gt), abs(gt))
    found = POINT.findall(text)
    if not found:
        return 1.0
    gt = [float(v) for v in POINT.search(answer).groups()]
    pred = [float(v) for v in found[-1]]
    return 1.0 - mra(math.dist(pred, gt), max(math.hypot(*gt), POINT_FLOOR_M))


def errors(dev_rows, predictions):
    by_qid = {item["qid"]: item["prediction"] for item in predictions}
    result = {}
    for row in dev_rows:
        result[row["qid"]] = (row["category"], item_error(row["answer"], by_qid.get(row["qid"], ""), row["category"]))
    return result


def aggregate(item_errors):
    categories = {}
    for category, error in item_errors.values():
        categories.setdefault(category, []).append(error)
    per = {category: sum(values) / len(values) for category, values in sorted(categories.items())}
    return sum(per.values()) / len(per), per


def paired_bootstrap(earlier, end, reps=2000, seed=17):
    """Standard error of aggregate(end) - aggregate(earlier), resampling dev items within category."""
    qids = sorted(earlier)
    by_category = {}
    for qid in qids:
        by_category.setdefault(earlier[qid][0], []).append(qid)
    rng = random.Random(seed)
    deltas = []
    for _ in range(reps):
        sample = [rng.choice(members) for members in by_category.values() for _ in members]
        a = aggregate({index: earlier[qid] for index, qid in enumerate(sample)})[0]
        b = aggregate({index: end[qid] for index, qid in enumerate(sample)})[0]
        deltas.append(b - a)
    mean = sum(deltas) / len(deltas)
    return math.sqrt(sum((d - mean) ** 2 for d in deltas) / (len(deltas) - 1))


def decide(dev_rows, earlier_predictions, end_predictions, reps=2000):
    earlier, end = errors(dev_rows, earlier_predictions), errors(dev_rows, end_predictions)
    before, per_before = aggregate(earlier)
    after, per_after = aggregate(end)
    se = paired_bootstrap(earlier, end, reps)
    margin = max(MIN_DELTA, 2 * se)
    falling = before - after > margin
    return {"decision": "GROW" if falling else "STOP", "error_earlier": before, "error_end": after,
            "drop": before - after, "margin": margin, "bootstrap_se": se,
            "per_category_earlier": per_before, "per_category_end": per_after}


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def main(argv=None):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('tools/stage1_dev_metrics.py:main')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dev", required=True)
    parser.add_argument("--earlier", required=True, help="predictions a quarter-epoch before the epoch end")
    parser.add_argument("--end", required=True, help="predictions at the epoch end")
    args = parser.parse_args(argv)
    result = decide(read_jsonl(args.dev), read_jsonl(args.earlier), read_jsonl(args.end))
    json.dump(result, sys.stdout, indent=1, sort_keys=True)
    print()


if __name__ == "__main__":
    main()
