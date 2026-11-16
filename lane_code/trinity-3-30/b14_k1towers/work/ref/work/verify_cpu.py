import json
import os
from collections import defaultdict
from pathlib import Path

import numpy as np

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["GEO_BAKEOFF_FUSION_SOURCE"] = "policy"

from geo_bakeoff.contract import validate_export
from geo_bakeoff.io import ROOT, sha256, utc
from geo_bakeoff.pricing_policy import rule_for
from geo_bakeoff.reference import modules
from geo_bakeoff.paths import path as data_path
from geo_bakeoff.selectors import TYPES


ref = modules()
questions = {(s, str(q["id"])): q for s, q in ref["run_tg"].items()}
direct = ref["ladder_table"].load_direct()
grouped = defaultdict(list)
for (set_name, _), row in direct.items():
    grouped[(set_name, row[2])].append(row[1])
means = {key: float(np.mean(values)) for key, values in grouped.items()}
authority_path = data_path("/scratch/jjyeung/orch_cd/gt_ceiling/work/out/TG_SEL.json")
authority_rows = json.loads(authority_path.read_text())
authority = {(r["geom"], r["rule"], r["arm"], str(r["id"])): r for r in authority_rows}
results = []
index_path = ROOT / "out/baseline_index.json"
paths = [ROOT / "out/baselines" / name for name in json.loads(index_path.read_text()).values()] if index_path.exists() else (ROOT / "out/baselines").glob("*")
for path in sorted(paths):
    if not path.is_dir():
        continue
    if not index_path.exists() and path.name == "g3t_policy_gt":
        continue
    state = json.loads((path / "progress.json").read_text())
    if state["state"] != "complete":
        results.append({"run": path.name, "verdict": "UNKNOWN", "reason": "Active output is not a terminal artifact"})
        continue
    cfg = json.loads((path / "config.json").read_text())
    if not index_path.exists() and cfg["mode"] == "selector" and not path.name.endswith("_verified"):
        continue
    rows = [json.loads(line) for line in (path / "rows.jsonl").read_text().splitlines()]
    selected = {key: q for key, q in questions.items() if q["scene_name"] in cfg["scenes"]
                and (cfg["mode"] == "gt" or key[0] == "vsi" and q["question_type"] in TYPES | {"room_size_estimation"})}
    masks = ("gt",) if cfg["mode"] == "gt" else ("gt", "selector")
    expected = {(s, qid, mask) for s, qid in selected for mask in masks}
    keys = [(r["set"], r["id"], r["mask"]) for r in rows]
    assert len(keys) == len(set(keys)) and set(keys) == expected
    assert len(rows) == cfg["items_expected"] == state["items_done"]
    assert state["scenes_done"] == state["scenes_total"] == len(cfg["scenes"])
    assert cfg["reference_pin_sha256"] == sha256(ROOT / "out/receipts/reference_policy_pin.json")
    assert json.loads((path / "errors.json").read_text()) == []
    assert json.loads((path / "parity.json").read_text())["mismatches"] == []
    compared = 0
    for row in rows:
        key = row["set"], row["id"]
        score = ref["common"].score(row["type"], row["pred"], questions[key]["ground_truth"])
        assert abs(row["score"] - score) < 1e-12
        fallback = direct[key][1] if key in direct else means.get((row["set"], row["type"]), 0.)
        assert abs(row["fb"] - (score if row["pred"] is not None else fallback)) < 1e-12
        if cfg["mode"] == "selector" and row["type"] != "room_size_estimation":
            arm = "route" if row["mask"] == "selector" else "gt_dc" if cfg["fusion"] == "policy" else "gt"
            original = authority[(path.name.split("_")[0], rule_for(row["type"], cfg["fusion"]), arm, row["id"])]
            assert row["pred"] == original["pred"], (path.name, row["id"], row["mask"], row["pred"], original["pred"])
            assert abs(row["score"] - original["score"]) < 1e-12
            assert abs(row["fb"] - original["fb"]) < 1e-12
            compared += 1
    for name, field in (("scores.json", "score"), ("scores_fallback.json", "fb")):
        summary = json.loads((path / name).read_text())
        for group, value in summary.items():
            subset = [r for r in rows if "|".join((r["set"], r["type"], r["mask"])) == group]
            assert value["items"] == len(subset)
            assert abs(value["score_points"] - 100 * np.mean([r[field] for r in subset])) < 1e-9
    if cfg["raw"]:
        raw = [json.loads(line) for line in (path / "raw.jsonl").read_text().splitlines()]
        assert len(raw) == len(cfg["scenes"]) and {r["scene"] for r in raw} == set(cfg["scenes"])
    results.append({"run": path.name, "verdict": "COMPLETE", "items": len(rows), "scenes": len(cfg["scenes"]),
                    "selector_predictions_checked": compared, "parity_mismatches": 0,
                    "rows_sha256": sha256(path / "rows.jsonl")})
smokes = []
for path in sorted((ROOT / "out/smoke").glob("*/receipt.json")):
    receipt = json.loads(path.read_text())
    output = path.parent / "smoke.npz"
    assert receipt["status"] == "passed" and receipt["device"] == "cpu"
    assert sha256(output) == receipt["output_sha256"]
    with np.load(output, allow_pickle=False) as z:
        validate_export(dict(z), np.array(receipt["frames"]), expected_count=8)
    smokes.append({"run": path.parent.name, "verdict": "COMPLETE", "frames": 8, "seconds": receipt["seconds"],
                   "scope": receipt["scope"], "model": receipt["model"]})
print(json.dumps({"checked_at": utc(), "baselines": results, "smokes": smokes,
                  "selector_authority_sha256": sha256(authority_path)}, indent=2))
