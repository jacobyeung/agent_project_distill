"""Build the frozen dev-S1 150-item distance list and step 544's native arm on it.

Inputs
  --tasks  TASKS.jsonl of Orchard job 170056 (sha256 a2f3fdbd...)
  --r1     native/R1.json from the return of job 170056 (sha256 75669a63..., inside result.tar.gz
           5c150baf...), or an extract of it with the same arms/rows structure whose field
           "source_sha256" names that digest
  --out    output directory
Outputs (byte-stable): DISTANCE_LIST_DEVS1_150.jsonl, LIST_150.sha256, STEP544_ARM_150.jsonl,
  STEP544_ARM_150.sha256, BUILD_CHECKS.json
Standard library only; Python 3.6+.
"""
import argparse
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from unit_from_question import DISTANCE_TYPE, ROOM_TYPE, is_metre, parse_unit  # noqa: E402

TASKS_SHA = "a2f3fdbdab06ab81942d44044d85090df8ec5b86908cf010cdbcb17e35637f5e"
R1_SHA = "75669a6300aeeaf1ec98ef1dbd2b5276a7607422d92d9624af0d64a9c82154c0"
RETURN_SHA = "5c150bafb333117b2e026def36564b26cecf25bcdf9d536e5350c84fdef972a1"
ARM = "unflagged"  # step 544's native arm; "scripted" is the reference arm
SCORE_LABEL = "released_answer"
EXPECT = {"distance_items": 150, "metre_items": 43, "metre_mean_pct": 61.628, "all_mean_pct": 29.867,
          "distance_units": {"meters": 43, "centimeters": 28, "feet": 46, "inches": 33},
          "room_units": {"square meters": 29, "square feet": 7}}
LIST_NAME = "DISTANCE_LIST_DEVS1_150.jsonl"
ARM_NAME = "STEP544_ARM_150.jsonl"
ANSWER_RE = re.compile(r"<answer>(.*?)</answer>", re.DOTALL)


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def dumps(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(", ", ": "))


def write_lines(path, rows):
    data = "".join(dumps(r) + "\n" for r in rows).encode("ascii")
    with open(path, "wb") as f:
        f.write(data)
    return sha256_bytes(data)


def final_answer(row):
    dec = row.get("decode")
    if not isinstance(dec, dict):
        return None
    text = dec.get("text")
    if isinstance(text, dict):  # extract: long text shrunk to head/tail; the answer span is at the end
        text = text.get("tail")
    if not isinstance(text, str):
        return None
    spans = ANSWER_RE.findall(text)
    return spans[-1].strip() if spans else None


def mra(pred, gt):
    """Mean relative accuracy, 10 thresholds 0.50, 0.55, ..., 0.95 (scores are multiples of 0.1).

    Sanity check only; the job's recorded score is the authority. A relative error exactly on a
    threshold (e.g. 2.09 vs 1.9, rel 0.1) counts as a hit, as the job's scorer records it; a 1e-9
    tolerance absorbs float rounding there."""
    try:
        p = float(pred)
    except (TypeError, ValueError):
        return 0.0
    g = float(gt)
    rel = abs(p - g) / abs(g)
    hits = sum(1 for i in range(10) if rel <= 1.0 - (0.50 + 0.05 * i) + 1e-9)
    return hits / 10.0


def refusal_of(row):
    gr = row.get("geometry_refusal")
    if gr:
        return "geometry_refusal:%s" % gr.get("code")
    pr = row.get("program_refusal")
    if pr:
        return "program_refusal:%s" % (pr.get("code") if isinstance(pr, dict) else pr)
    return None


def build(tasks_path, r1_path, out_dir):
    tasks_bytes = open(tasks_path, "rb").read()
    tasks_sha = sha256_bytes(tasks_bytes)
    if tasks_sha != TASKS_SHA:
        raise SystemExit("TASKS sha256 %s != %s" % (tasks_sha, TASKS_SHA))
    r1_bytes = open(r1_path, "rb").read()
    r1 = json.loads(r1_bytes.decode("utf-8"))
    r1_file_sha = sha256_bytes(r1_bytes)
    r1_source_sha = r1_file_sha if r1_file_sha == R1_SHA else r1.get("source_sha256")
    if r1_source_sha != R1_SHA:
        raise SystemExit("R1 digest %s (file %s) != %s" % (r1_source_sha, r1_file_sha, R1_SHA))

    tasks = [json.loads(l) for l in tasks_bytes.decode("utf-8").splitlines() if l.strip()]
    dist = sorted([t for t in tasks if t["question_type"] == DISTANCE_TYPE], key=lambda t: t["id"])
    rooms = [t for t in tasks if t["question_type"] == ROOM_TYPE]
    ids = [t["id"] for t in dist]
    if len(ids) != len(set(ids)) or len(ids) != EXPECT["distance_items"]:
        raise SystemExit("distance ids: %d rows, %d unique" % (len(ids), len(set(ids))))

    arm_rows = {}
    for r in r1["arms"][ARM]:
        if r["question_type"] == DISTANCE_TYPE:
            if r["key"] in arm_rows:
                raise SystemExit("duplicate R1 key %s" % r["key"])
            arm_rows[r["key"]] = r

    list_rows, arm_out = [], []
    unit_counts, room_counts = {}, {}
    disagree_job_unit, mra_mismatch, field_mismatch = [], [], []
    for t in dist:
        p = parse_unit(t["question"], DISTANCE_TYPE)
        unit_counts[p["unit"] or p["status"]] = unit_counts.get(p["unit"] or p["status"], 0) + 1
        metre = is_metre(p, DISTANCE_TYPE)
        list_rows.append({"question_id": t["id"], "capture": t["native"], "room": t["room"],
                          "unit": p["unit"], "unit_status": p["status"], "metre": metre})
        key = "devrows:" + t["id"]
        r = arm_rows.pop(key, None)
        if r is None:
            raise SystemExit("no %s row for %s" % (ARM, key))
        if r["room"] != t["room"] or r["stratum"] != t["stratum"]:
            field_mismatch.append(t["id"])
        if (r.get("question_unit") or {}).get("unit") != p["unit"]:
            disagree_job_unit.append(t["id"])
        fa = final_answer(r)
        score = float(r["scores"][SCORE_LABEL])
        if r.get("decode") is not None and abs(mra(fa, t[SCORE_LABEL]) - score) > 1e-9:
            mra_mismatch.append(t["id"])
        arm_out.append({"question_id": t["id"], "key": key, "unit": p["unit"], "metre": metre,
                        "score": score, "called": bool(r.get("called")),
                        "call_count": int(r.get("call_count", 0)),
                        "refusal": refusal_of(r), "no_answer": bool(r.get("no_answer")),
                        "capped": bool(r.get("capped")), "final_answer": fa})
    if arm_rows:
        raise SystemExit("R1 has %d distance rows not in TASKS" % len(arm_rows))
    for t in rooms:
        p = parse_unit(t["question"], ROOM_TYPE)
        room_counts[p["unit"] or p["status"]] = room_counts.get(p["unit"] or p["status"], 0) + 1

    def mean_pct(rows):
        return round(100.0 * sum(r["score"] for r in rows) / len(rows), 3)

    metre_rows = [r for r in arm_out if r["metre"]]
    checks = {
        "distance_items": len(arm_out), "metre_items": len(metre_rows),
        "distance_units": unit_counts, "room_units": room_counts,
        "metre_mean_pct": mean_pct(metre_rows), "all_mean_pct": mean_pct(arm_out),
        "excluded_from_metre_set_for_unit_status": sorted(r["question_id"] for r in list_rows
                                                          if r["unit_status"] != "ok"),
        "parser_vs_job_question_unit_disagreements": disagree_job_unit,
        "room_or_stratum_mismatch_vs_r1": field_mismatch,
        "mra_recompute_mismatch": mra_mismatch,
        "called_items": sum(r["called"] for r in arm_out),
        "refusals": sorted((r["question_id"], r["refusal"]) for r in arm_out if r["refusal"]),
        "no_answer_items": sum(r["no_answer"] for r in arm_out),
        "capped_items": sum(r["capped"] for r in arm_out),
        "final_answer_none": sum(r["final_answer"] is None for r in arm_out),
    }
    failures = [k for k in ("distance_items", "metre_items", "metre_mean_pct", "all_mean_pct",
                            "distance_units", "room_units") if checks[k] != EXPECT[k]]
    failures += [k for k in ("parser_vs_job_question_unit_disagreements", "room_or_stratum_mismatch_vs_r1",
                             "mra_recompute_mismatch") if checks[k]]

    os.makedirs(out_dir, exist_ok=True)
    list_sha = write_lines(os.path.join(out_dir, LIST_NAME), list_rows)
    arm_sha = write_lines(os.path.join(out_dir, ARM_NAME), arm_out)
    with open(os.path.join(out_dir, "LIST_150.sha256"), "wb") as f:
        f.write(("%s  %s\n" % (list_sha, LIST_NAME)).encode("ascii"))
    with open(os.path.join(out_dir, "STEP544_ARM_150.sha256"), "wb") as f:
        f.write(("%s  %s\n" % (arm_sha, ARM_NAME)).encode("ascii"))
    report = {"status": "PASS" if not failures else "FAIL", "failures": failures, "expected": EXPECT,
              "checks": checks, "arm": ARM, "score_label": SCORE_LABEL,
              "inputs": {"tasks_sha256": tasks_sha, "r1_sha256": r1_source_sha, "r1_file_sha256": r1_file_sha,
                         "return_archive_sha256": RETURN_SHA, "job": "170056"},
              "outputs": {LIST_NAME: list_sha, ARM_NAME: arm_sha}}
    with open(os.path.join(out_dir, "BUILD_CHECKS.json"), "wb") as f:
        f.write((json.dumps(report, sort_keys=True, indent=1) + "\n").encode("ascii"))
    return report


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--r1", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    rep = build(a.tasks, a.r1, a.out)
    print(json.dumps({"status": rep["status"], "failures": rep["failures"], "outputs": rep["outputs"],
                      "metre_mean_pct": rep["checks"]["metre_mean_pct"],
                      "all_mean_pct": rep["checks"]["all_mean_pct"]}, sort_keys=True))
    return 0 if rep["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
