"""Ready-to-run builder (run only on ORCH's word) for the 790-item dev-S1 primary distance list.
Same row schema as DISTANCE_LIST_DEVS1_150.jsonl; unit from question text alone.
  --items  dev-S1 ITEMS.jsonl (sha256 30d4beb0...), --fixed150 the frozen 150 list, --out dir
Outputs: DISTANCE_LIST_DEVS1_790.jsonl, LIST_790.sha256, BUILD_CHECKS_790.json. Stdlib; py3.6+."""
import argparse, hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from unit_from_question import DISTANCE_TYPE, is_metre, parse_unit  # noqa: E402
from build_lists import dumps, write_lines  # noqa: E402

ITEMS_SHA = "30d4beb0827c4f2b7f10fcc8f2623fd8519666d6736cac91b6b5f3f131eb0725"
FIXED_SHA = "028273ec3bfd1d3cd2d64f15c0fdab10fd8f905beb49fe09c3aa822a491a702e"
EXPECT = {"items": 790, "rooms": 59, "units": {"meters": 203, "centimeters": 182, "feet": 213, "inches": 192}}
NAME = "DISTANCE_LIST_DEVS1_790.jsonl"


def build(items_path, fixed_path, out_dir):
    b = open(items_path, "rb").read()
    if hashlib.sha256(b).hexdigest() != ITEMS_SHA:
        raise SystemExit("ITEMS sha256 mismatch")
    fb = open(fixed_path, "rb").read()
    if hashlib.sha256(fb).hexdigest() != FIXED_SHA:
        raise SystemExit("fixed list sha256 mismatch")
    rows = [json.loads(l) for l in b.decode("utf-8").splitlines() if l.strip()]
    prim = sorted((r for r in rows if r["question_type"] == DISTANCE_TYPE and r["stratum"] == "primary"),
                  key=lambda r: r["qid"])
    ids = [r["qid"] for r in prim]
    if len(ids) != len(set(ids)) or len(ids) != EXPECT["items"]:
        raise SystemExit("primary distance ids: %d rows, %d unique" % (len(ids), len(set(ids))))
    out, units = [], {}
    for r in prim:
        p = parse_unit(r["question"], DISTANCE_TYPE)
        units[p["unit"] or p["status"]] = units.get(p["unit"] or p["status"], 0) + 1
        out.append({"question_id": r["qid"], "capture": r["native"], "room": r["room"],
                    "unit": p["unit"], "unit_status": p["status"], "metre": is_metre(p, DISTANCE_TYPE)})
    fixed_lines = set(fb.decode("ascii").splitlines())
    fixed_ids = set(r["qid"] for r in prim if r["fixed"])
    sub = [dumps(o) for o in out if o["question_id"] in fixed_ids]
    checks = {"items": len(out), "rooms": len(set(o["room"] for o in out)), "units": units,
              "metre_items": sum(o["metre"] for o in out),
              "fixed_rows_identical": len(fixed_ids) == 150 and set(sub) == fixed_lines,
              "items_sha256": ITEMS_SHA, "fixed150_sha256": FIXED_SHA}
    ok = (checks["rooms"] == EXPECT["rooms"] and units == EXPECT["units"] and checks["fixed_rows_identical"])
    checks["pass"] = ok
    os.makedirs(out_dir, exist_ok=True)
    sha = write_lines(os.path.join(out_dir, NAME), out)
    checks["list_sha256"] = sha
    open(os.path.join(out_dir, "LIST_790.sha256"), "w").write("%s  %s\n" % (sha, NAME))
    open(os.path.join(out_dir, "BUILD_CHECKS_790.json"), "w").write(json.dumps(checks, indent=1, sort_keys=True) + "\n")
    if not ok:
        raise SystemExit("checks failed: %s" % json.dumps(checks))
    return checks


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--items", required=True); a.add_argument("--fixed150", required=True); a.add_argument("--out", required=True)
    x = a.parse_args()
    print(json.dumps(build(x.items, x.fixed150, x.out), sort_keys=True))
