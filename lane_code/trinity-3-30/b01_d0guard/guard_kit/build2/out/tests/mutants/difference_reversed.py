#!/usr/bin/env python3
"""Guard read of a D0 candidate export against step 544 (init rule items 3, 5 and 6).

INTERNAL INSTRUMENT. The native arm is served by a Python runtime with fitted parts (selector,
scale rule, guard, mask cache); the user ruled on 2026-11-16 that such a runtime is harness. The
numbers choose the next leg's init and are never a claimed result.

Inputs are two R1.json bundles (schema legs1-r1-nomdg-v1): the candidate's native arm and step
544's native arm of Orchard job 170056 (arm "unflagged"). Statistics: paired differences,
candidate minus step 544, percentile 95% intervals from a bootstrap over physical rooms,
10,000 draws, seed 20261115. A refusal or a non-answer scores 0 and stays in the denominator.
Units come from question text alone, through the parser of brief 02 (unit_from_question.py).

Guards (rule item 5): camera displacement, movement direction and rotation each have no
interval wholly below zero; every one of the 450 camera items draws a call; metre distance on
the frozen list has no interval wholly below zero and a call on at least 95% of its items. Room
and non-metre distance are printed and decide nothing.

Standard library only. Exit 0 with a report (PASS or FAIL per guard); exit 3 when the inputs do
not support the paired read (missing items, list or parser mismatch, wrong arm identity).
"""
import argparse
import hashlib
import importlib.util
import json
import random
import re
import sys
from pathlib import Path

FIRST_LINE = ("INTERNAL INSTRUMENT, NOT A CLAIMED RESULT: guard read for choosing the next leg's "
              "init; the native arm is served by a harness runtime (fitted selector, scale rule, "
              "guard, mask cache).")
STEP544_ARTIFACT = "1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef"
CAMERA_TYPES = ("camera_displacement", "camera_movement_direction", "camera_rotation")
DISTANCE = "object_abs_distance"
ROOM = "room_size_estimation"
ALIASES = {"absolute_distance_object": DISTANCE, "absolute_size_room": ROOM}
CAMERA_ITEMS_PER_TYPE = 150
ROOM_ITEMS = 36
DRAWS = 10000
SEED = 20261115
METRE_CALL_RATE_MIN = 0.95
ARM = "unflagged"
REQUIRED_FLAGS = ("called", "no_answer")
OPTIONAL_FLAGS = ("parse_failed", "strict_no_answer")
REFUSAL_FLAGS = ("geometry_refusal", "refusal")


class Refusal(ValueError):
    """The inputs do not support the paired guard read."""


def require(condition, message):
    if not condition:
        raise Refusal(message)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_parser(path, expected_sha):
    require(sha256_file(path) == expected_sha, "unit parser sha256 differs from the pinned brief-02 parser")
    spec = importlib.util.spec_from_file_location("unit_from_question_pinned", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def family(row):
    return ALIASES.get(row["question_type"], row["question_type"])


def label(row):
    return "released_answer" if row.get("stratum") == "primary" else "answer"


def nonanswer(row):
    """Refusals and non-answers; each scores 0 and stays in the denominator."""
    decoded = row.get("decode") or {}
    if row.get("geometry_refusal") or row.get("refusal"):
        return True
    if decoded.get("finish") in ("program_refusal", "call_limit", "error") or row.get("finish_reason") in ("call_limit", "error"):
        return True
    if (row.get("no_answer") or row.get("parse_failed") or row.get("strict_no_answer")
            or decoded.get("strict_no_answer") or decoded.get("parse_failed")):
        return True
    if "text" in decoded and not re.search(r"</think\s*>", decoded["text"] or "", re.I):
        return True
    return False


def score(row):
    if nonanswer(row):
        return 0.0
    value = float(row["scores"][label(row)])
    require(0.0 <= value <= 1.0, "score outside [0, 1] for " + row["key"])
    return value


def called(row):
    return row.get("called") is True


def load_arm(path, arm=ARM):
    bundle = json.loads(Path(path).read_text())
    require(bundle.get("schema") == "legs1-r1-nomdg-v1", "unexpected R1 schema in " + str(path))
    rows = bundle.get("arms", {}).get(arm)
    require(isinstance(rows, list) and rows, "arm %s missing in %s" % (arm, path))
    index = {}
    for row in rows:
        require(row["key"] not in index, "duplicate key %s in %s" % (row["key"], path))
        require(row.get("arm", arm) == arm, "row arm differs from %s in %s" % (arm, path))
        for flag in REQUIRED_FLAGS:
            require(type(row.get(flag)) is bool,
                    "accounting flag %s of %s is missing or not a boolean in %s" % (flag, row["key"], path))
        for flag in OPTIONAL_FLAGS:
            require(flag not in row or type(row[flag]) is bool,
                    "accounting flag %s of %s is not a boolean in %s" % (flag, row["key"], path))
        for flag in REFUSAL_FLAGS:
            require(flag not in row or type(row[flag]) is bool or (isinstance(row[flag], dict) and row[flag]),
                    "refusal record %s of %s is neither a boolean nor a non-empty record in %s" % (flag, row["key"], path))
        require("decode" not in row or isinstance(row["decode"], dict),
                "decode of %s is not a record in %s" % (row["key"], path))
        for flag in ("strict_no_answer", "parse_failed"):
            require(flag not in row.get("decode", {}) or type(row["decode"][flag]) is bool,
                    "decode flag %s of %s is not a boolean in %s" % (flag, row["key"], path))
        index[row["key"]] = row
    artifacts = sorted({row.get("checkpoint_sha256") for row in rows})
    require(len(artifacts) == 1 and artifacts[0], "arm rows of %s carry %s checkpoint identities" % (path, artifacts))
    return index, artifacts[0]


def quantile(sorted_values, p):
    position = (len(sorted_values) - 1) * p
    lo = int(position)
    hi = min(lo + 1, len(sorted_values) - 1)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (position - lo)


def paired_interval(pairs, draws=DRAWS, seed=SEED):
    """pairs: (room, candidate score, baseline score). Item-weighted room-cluster bootstrap."""
    require(draws >= 10000, "at least 10,000 bootstrap draws are required")
    require(pairs, "empty comparison")
    clusters = {}
    for room, a, b in pairs:
        n, d = clusters.get(room, (0, 0.0))
        clusters[room] = (n + 1, d + (a - b))
    ordered = [clusters[r] for r in sorted(clusters)]
    rng = random.Random(seed)
    values = []
    for _ in range(draws):
        chosen = rng.choices(ordered, k=len(ordered))
        values.append(100.0 * sum(c[1] for c in chosen) / sum(c[0] for c in chosen))
    values.sort()
    n = len(pairs)
    a_mean = 100.0 * sum(p[1] for p in pairs) / n
    b_mean = 100.0 * sum(p[2] for p in pairs) / n
    return dict(items=n, rooms=len(ordered), candidate=a_mean, step544=b_mean,
                difference=100.0 * sum(p[2] - p[1] for p in pairs) / n,
                interval=[quantile(values, 0.025), quantile(values, 0.975)])


def wholly_below_zero(comparison):
    return comparison["interval"][1] < 0


def build_items(cand, base, list_rows, tasks, parser):
    """Item set: 450 camera items, the distance list, 36 room items; pairing checks."""
    camera = {t: sorted(k for k, r in base.items() if family(r) == t) for t in CAMERA_TYPES}
    for t, keys in camera.items():
        require(len(keys) == CAMERA_ITEMS_PER_TYPE, "step-544 arm has %d %s items, not 150" % (len(keys), t))
    room = sorted(k for k, r in base.items() if family(r) == ROOM)
    require(len(room) == ROOM_ITEMS, "step-544 arm has %d room items, not 36" % len(room))
    distance = []
    for row in list_rows:
        key = "devrows:" + row["question_id"]
        task = tasks.get(row["question_id"])
        require(task is not None, "list item %s absent from TASKS" % row["question_id"])
        require(task["question_type"] == DISTANCE, "list item %s is not a distance item" % row["question_id"])
        parsed = parser.parse_unit(task["question"], DISTANCE)
        require(parsed["unit"] == row["unit"] and parser.is_metre(parsed, DISTANCE) == bool(row["metre"]),
                "unit of %s from question text differs from the frozen list" % row["question_id"])
        require(task["room"] == row["room"] and task["native"] == row["capture"],
                "room or capture of %s differs between TASKS and the list" % row["question_id"])
        distance.append(dict(key=key, unit=parsed["unit"] or parsed["status"], metre=bool(row["metre"]),
                             room=row["room"]))
    room_units = {}
    for key in room:
        task = tasks.get(key.split(":", 1)[1])
        require(task is not None and task["question_type"] == ROOM, "room item %s absent from TASKS" % key)
        parsed = parser.parse_unit(task["question"], ROOM)
        room_units[key] = parsed["unit"] or parsed["status"]
    every = [k for t in CAMERA_TYPES for k in camera[t]] + [d["key"] for d in distance] + room
    require(len(set(every)) == len(every), "item set has repeated keys")
    missing_base = [k for k in every if k not in base]
    missing_cand = [k for k in every if k not in cand]
    require(not missing_base, "step-544 arm lacks %d items, e.g. %s" % (len(missing_base), missing_base[:3]))
    require(not missing_cand, "candidate arm lacks %d items, e.g. %s (incomplete read; no guard verdict)"
            % (len(missing_cand), missing_cand[:3]))
    for k in every:
        a, b = cand[k], base[k]
        require(family(a) == family(b), "question type of %s differs between arms" % k)
        require(a["room"] == b["room"], "physical room of %s differs between arms" % k)
        require(a.get("stratum") == b.get("stratum"), "stratum of %s differs between arms" % k)
    for d in distance:
        require(base[d["key"]]["room"] == d["room"], "list room of %s differs from the arms" % d["key"])
    return camera, distance, room, room_units


def pairs_for(keys, cand, base):
    return [(base[k]["room"], score(cand[k]), score(base[k])) for k in keys]


def call_count(keys, rows):
    return sum(called(rows[k]) for k in keys)


def analyze(cand_path, base_path, list_path, list_sha, tasks_path, parser_path, parser_sha,
            draws=DRAWS, seed=SEED, candidate_artifact=None, baseline_artifact=STEP544_ARTIFACT,
            fixed_list_path=None, fixed_list_sha=None, self_pair=False):
    require(draws == DRAWS and seed == SEED, "the rule fixes %d draws and seed %d" % (DRAWS, SEED))
    require(sha256_file(list_path) == list_sha, "distance list sha256 differs from the frozen value")
    parser = load_parser(parser_path, parser_sha)
    list_rows = [json.loads(line) for line in Path(list_path).read_text().splitlines() if line.strip()]
    tasks = {}
    for line in Path(tasks_path).read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            tasks[row["id"]] = row
    cand, cand_artifact = load_arm(cand_path)
    base, base_artifact = load_arm(base_path)
    if baseline_artifact:
        require(base_artifact == baseline_artifact, "baseline arm is not step 544 (%s)" % base_artifact)
    require(bool(candidate_artifact), "the candidate artifact sha256 is required")
    require(cand_artifact == candidate_artifact, "candidate arm artifact %s differs from %s" % (cand_artifact, candidate_artifact))
    require(self_pair or candidate_artifact != STEP544_ARTIFACT,
            "the candidate is step 544 itself; only the explicit self-pair check may pair it with itself")
    camera, distance, room, room_units = build_items(cand, base, list_rows, tasks, parser)
    comparisons, guards = {}, []

    for t in CAMERA_TYPES:
        c = paired_interval(pairs_for(camera[t], cand, base), draws, seed)
        comparisons[t] = c
        guards.append(dict(name="interval_" + t, pass_=not wholly_below_zero(c),
                           rule="paired 95% interval not wholly below zero",
                           value="%+.3f [%+.3f, %+.3f]" % (c["difference"], *c["interval"])))
    camera_keys = [k for t in CAMERA_TYPES for k in camera[t]]
    cam_calls = call_count(camera_keys, cand)
    guards.append(dict(name="camera_call_rate", pass_=cam_calls == len(camera_keys),
                       rule="every one of the 450 camera items draws a call",
                       value="%d of %d (step 544: %d of %d); uncalled: %s" % (
                           cam_calls, len(camera_keys), call_count(camera_keys, base), len(camera_keys),
                           sorted(k for k in camera_keys if not called(cand[k])))))
    metre = [d["key"] for d in distance if d["metre"]]
    require(metre, "the distance list has no metre items")
    c = paired_interval(pairs_for(metre, cand, base), draws, seed)
    comparisons["distance_metre"] = c
    guards.append(dict(name="interval_distance_metre", pass_=not wholly_below_zero(c),
                       rule="paired 95% interval not wholly below zero",
                       value="%+.3f [%+.3f, %+.3f]" % (c["difference"], *c["interval"])))
    m_calls = call_count(metre, cand)
    guards.append(dict(name="distance_metre_call_rate", pass_=m_calls >= METRE_CALL_RATE_MIN * len(metre),
                       rule="a call on at least 95% of the metre items",
                       value="%d of %d = %.3f%% (step 544: %d of %d)" % (
                           m_calls, len(metre), 100.0 * m_calls / len(metre), call_count(metre, base), len(metre))))

    printed = {}
    printed["distance_all"] = paired_interval(pairs_for([d["key"] for d in distance], cand, base), draws, seed)
    non_metre = [d["key"] for d in distance if not d["metre"]]
    if non_metre:
        printed["distance_non_metre"] = paired_interval(pairs_for(non_metre, cand, base), draws, seed)
    for unit in sorted({d["unit"] for d in distance if not d["metre"]}):
        keys = [d["key"] for d in distance if d["unit"] == unit]
        printed["distance_" + unit.replace(" ", "_")] = paired_interval(pairs_for(keys, cand, base), draws, seed)
    printed["room_all"] = paired_interval(pairs_for(room, cand, base), draws, seed)
    for unit in sorted(set(room_units.values())):
        keys = [k for k in room if room_units[k] == unit]
        printed["room_" + unit.replace(" ", "_")] = paired_interval(pairs_for(keys, cand, base), draws, seed)
    if fixed_list_path:
        require(sha256_file(fixed_list_path) == fixed_list_sha, "fixed-list sha256 differs")
        fixed = [json.loads(line) for line in Path(fixed_list_path).read_text().splitlines() if line.strip()]
        keys = ["devrows:" + r["question_id"] for r in fixed if r["metre"]]
        require(all(k in cand and k in base for k in keys), "fixed-list metre items missing from an arm")
        printed["distance_metre_fixed_list"] = paired_interval(pairs_for(keys, cand, base), draws, seed)
    calls = {}
    for name, keys in (("camera", camera_keys), ("distance_all", [d["key"] for d in distance]),
                       ("distance_metre", metre), ("room", room)):
        calls[name] = dict(candidate=call_count(keys, cand), step544=call_count(keys, base), items=len(keys))
    nonanswers = {arm: sum(nonanswer(rows[k]) for k in camera_keys + [d["key"] for d in distance] + room)
                  for arm, rows in (("candidate", cand), ("step544", base))}
    for g in guards:
        g["pass"] = g.pop("pass_")
    return dict(first_line=FIRST_LINE, schema="d0-guard-read-v1",
                candidate=dict(path=str(cand_path), sha256=sha256_file(cand_path), artifact=cand_artifact),
                step544=dict(path=str(base_path), sha256=sha256_file(base_path), artifact=base_artifact),
                distance_list=dict(path=str(list_path), sha256=list_sha, items=len(distance), metre_items=len(metre)),
                parser_sha256=parser_sha, method=dict(name="paired physical-room percentile bootstrap, item-weighted",
                draws=draws, seed=seed, interval="95% linear percentile", difference="candidate minus step 544, points"),
                guards=guards, verdict="PASS" if all(g["pass"] for g in guards) else "FAIL",
                comparisons=comparisons, printed_only=printed, calls=calls, nonanswers_scored_zero=nonanswers,
                self_pair=bool(self_pair))


def markdown(result):
    f = lambda c: "%.3f | %.3f | %+.3f [%+.3f, %+.3f] | %d / %d" % (
        c["candidate"], c["step544"], c["difference"], c["interval"][0], c["interval"][1], c["items"], c["rooms"])
    lines = [result["first_line"], ""] + (["SELF-PAIR CHECK OF STEP 544: not a guard read of any candidate.", ""]
                                          if result.get("self_pair") else []) + [
             "Candidate artifact %s; step 544 artifact %s. List %s (%d items, %d metre). %d draws, seed %d." % (
                 result["candidate"]["artifact"], result["step544"]["artifact"], result["distance_list"]["sha256"],
                 result["distance_list"]["items"], result["distance_list"]["metre_items"],
                 result["method"]["draws"], result["method"]["seed"]), "",
             "## Guards (rule item 5): overall %s" % result["verdict"], "",
             "| Guard | Rule | Value | Verdict |", "|---|---|---|---|"]
    for g in result["guards"]:
        lines.append("| %s | %s | %s | %s |" % (g["name"], g["rule"], g["value"], "PASS" if g["pass"] else "FAIL"))
    lines += ["", "## Intervals (candidate %, step 544 %, difference pp [95% interval], items / rooms)", "",
              "| Comparison | Candidate | Step 544 | Difference | Items / rooms |", "|---|---|---|---|---|"]
    for name, c in result["comparisons"].items():
        lines.append("| %s (guard) | %s |" % (name, f(c)))
    for name, c in result["printed_only"].items():
        lines.append("| %s (printed only) | %s |" % (name, f(c)))
    lines += ["", "Calls: " + json.dumps(result["calls"], sort_keys=True),
              "Refusals and non-answers scored 0: " + json.dumps(result["nonanswers_scored_zero"], sort_keys=True), ""]
    return "\n".join(lines)


def main(argv=None):
    here = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--candidate", required=True, help="candidate R1.json (native arm 'unflagged')")
    p.add_argument("--step544", required=True, help="R1.json of Orchard job 170056")
    p.add_argument("--list", default=str(here / "inputs/DISTANCE_LIST_DEVS1_150.jsonl"))
    p.add_argument("--list-sha256", default="028273ec3bfd1d3cd2d64f15c0fdab10fd8f905beb49fe09c3aa822a491a702e")
    p.add_argument("--fixed-list", default=str(here / "inputs/DISTANCE_LIST_DEVS1_150.jsonl"))
    p.add_argument("--fixed-list-sha256", default="028273ec3bfd1d3cd2d64f15c0fdab10fd8f905beb49fe09c3aa822a491a702e")
    p.add_argument("--tasks", default=str(here / "inputs/TASKS.jsonl"))
    p.add_argument("--parser", default=str(here / "inputs/unit_from_question.py"))
    p.add_argument("--parser-sha256", default="274f04a0d9590e2afbeada5d1f6003ab7d805c5e333b522ead22c23ff3396de5")
    p.add_argument("--candidate-artifact", required=True, help="artifact sha256 of the candidate export (CONFIG)")
    p.add_argument("--self-pair", action="store_true", help="the step-544 self-pair check only; never a guard read")
    p.add_argument("--draws", type=int, default=DRAWS)
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    try:
        result = analyze(a.candidate, a.step544, a.list, a.list_sha256, a.tasks, a.parser, a.parser_sha256,
                         a.draws, a.seed, a.candidate_artifact, STEP544_ARTIFACT, a.fixed_list, a.fixed_list_sha256,
                         a.self_pair)
    except Refusal as error:
        print("REFUSED: " + str(error), file=sys.stderr)
        return 3
    except (KeyError, TypeError, ValueError, AttributeError, IndexError) as error:
        print("REFUSED: malformed input: %s: %s" % (type(error).__name__, error), file=sys.stderr)
        return 3
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "GUARD_READ.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    text = markdown(result)
    (out / "GUARD_READ.md").write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
