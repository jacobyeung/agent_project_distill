import argparse
import json
import os
import time
from collections import defaultdict
from multiprocessing import get_context
from pathlib import Path

import numpy as np

from .contract import camera_arrays, load_export, raster_depth
from .io import ROOT, check_space, dump_json, local_output, progress, sha256, utc, json_hash
from .pricing import GT, TOWER, VSI_FIX, VSTI_FIX, raw_metrics, summarize
from .reference import modules
from .selectors import RAW, TYPES, MaskContext, TowerGeometry, deployed_masks, deployed_tables, item_names
from .protocol import PRIMARY, calibration_label, policy_scope
from .resume import prepare_stage, preserve_files, fingerprint
from .provenance import PRICING_FILES


SETTINGS = None
TABLES = None
DIRECT = None
TYPE_MEANS = None
ABSOLUTE = {"object_abs_distance", "camera_obj_abs_dist"}


def initialize(settings):
    global SETTINGS, TABLES, DIRECT, TYPE_MEANS
    os.environ["GEO_BAKEOFF_FUSION_SOURCE"] = "policy"
    SETTINGS = settings
    ref = modules()
    DIRECT = ref["ladder_table"].load_direct()
    grouped = defaultdict(list)
    for (set_name, _), row in DIRECT.items():
        grouped[(set_name, row[2])].append(row[1])
    TYPE_MEANS = {key: float(np.mean(values)) for key, values in grouped.items()}
    TABLES = deployed_tables() if settings["mode"] == "selector" else None


def rule_for(question_type, fusion):
    return "all" if fusion == "all" else "best1" if question_type in ABSOLUTE else "voteb5"


def missing_selector_names(question, context, parser):
    return any(name not in context.name2ids for name in item_names(parser(question)))


def row_membership(rows):
    return json_hash(sorted((r["set"], str(r["id"]), r["mask"], r["type"], r["scene"]) for r in rows))


def validate_pricing(rows, config, parity):
    keys = [(r["set"], str(r["id"]), r["mask"]) for r in rows]
    if parity or len(rows) != config["items_expected"] or len(keys) != len(set(keys)):
        raise ValueError(f"Pricing integrity failure: parity={len(parity)}, rows={len(rows)}")
    if row_membership(rows) != config["membership_sha256"]:
        raise ValueError("Pricing membership differs from the requested items")


def load_scene_result(path, scene, expected, configuration):
    envelope = json.loads(Path(path).read_text())
    result = envelope["result"]
    if envelope["configuration_fingerprint"] != configuration or envelope["result_sha256"] != json_hash(result):
        raise ValueError("Pricing scene receipt differs")
    if result["scene"] != scene or row_membership(result["rows"]) != row_membership(expected):
        raise ValueError("Pricing scene membership differs")
    return result


def scene_job(job):
    scene, questions = job
    ref, settings = modules(), SETTINGS
    v, g, c, pr = [ref[key] for key in ("prog_v2", "geomswap", "common", "programs")]
    base = pr.GTSource(str(GT / f"{scene}.npz"))
    with np.load(GT / f"{scene}.npz", allow_pickle=False) as z:
        frames = z["frame_indices"]
    data = load_export(Path(settings["exports"]) / f"scannet__{scene}.npz", frames)
    depth, (cameras, intrinsics) = raster_depth(data["depth_grid"]), camera_arrays(data)
    cameras = g.aligned_pose(cameras, base.c2w, base.valid, 1.)
    mask_geometry = TowerGeometry(Path(settings["exports"]) / f"scannet__{scene}.npz")
    if settings.get("native"):
        from .native import NativeGeometry
        mask_geometry = NativeGeometry(Path(settings["exports"]), scene, settings["native"],
                                       full_intrinsics=settings["native_calibration"] == "full")
        depth = np.stack([mask_geometry.depth(k) for k in range(1, 33)])
        intrinsics = mask_geometry.intrinsics
    contexts, mask_contexts = {}, {}
    selected = [q for _, q in questions if q["question_type"] in TYPES]
    masks = deployed_masks(scene, selected, base, TABLES) if settings["mode"] == "selector" and selected else None
    rows, errors = [], []
    for set_name, question in questions:
        typ = question["question_type"]
        rule = rule_for(typ, settings["fusion"])
        g.ROOM_VOTE = (2, .05) if settings["fusion"] == "policy" else None
        context_key = (set_name, rule)
        if context_key not in contexts:
            geo = g.Geo(base, depth, cameras, intrinsics, rule=rule, mods=("dc",) if settings["fusion"] == "policy" else ())
            contexts[context_key] = v.Ctx(geo, VSI_FIX if set_name == "vsi" else VSTI_FIX, "B")
        for mask in (("gt", "selector") if settings["mode"] == "selector" else ("gt",)):
            error = None
            if settings["mode"] == "gt" or typ == "room_size_estimation":
                ctx = contexts[context_key]
            else:
                key = (mask, rule, typ == "object_counting")
                if key not in mask_contexts:
                    source = masks[0] if mask == "gt" else masks[2] if typ == "object_counting" else masks[1]
                    cut = settings["fusion"] == "policy" if mask == "gt" else typ != "object_counting"
                    mask_contexts[key] = MaskContext(mask_geometry, source, cut=cut, rule=rule)
                ctx = mask_contexts[key]
            try:
                if isinstance(ctx, MaskContext) and missing_selector_names(question, ctx, ref["tplib"].parse_vsi):
                    prediction = None
                else:
                    prediction = (v.run_vsi if set_name == "vsi" else v.run_vsti)(question, ctx)[0]
                    prediction = v.finalize(typ, prediction, ctx.fixes)
                score = c.score(typ, prediction, question["ground_truth"])
                if not np.isfinite(score):
                    raise ValueError("Program produced a nonfinite score")
            except Exception as exc:
                prediction, error = None, f"{type(exc).__name__}: {exc}"
                score = c.score(typ, None, question["ground_truth"])
                errors.append({"set": set_name, "id": str(question["id"]), "type": typ, "mask": mask, "error": error})
            direct = DIRECT.get((set_name, str(question["id"])))
            fallback = float(direct[1]) if direct else TYPE_MEANS.get((set_name, typ), 0.)
            rows.append({"set": set_name, "id": str(question["id"]), "type": typ, "scene": scene, "mask": mask,
                         "pred": prediction, "score": score, "fb": score if prediction is not None else fallback,
                         "fusion": settings["fusion"], "rule": rule, "error": error,
                         "policy_scope": policy_scope(set_name, settings["fusion"]),
                         "mask_free": typ == "room_size_estimation"})
    parity = []
    if settings["parity"] and settings["mode"] == "gt":
        tower = settings["parity"]
        prefix = "dT+pT+kT" + ("+tw_g3t" if tower == "g3t" else "")
        if settings["fusion"] == "all":
            conditions = [prefix]
        else:
            conditions = [prefix + "+f_best1+dc+rv", prefix + "+f_voteb5+dc+rv"]
        ref["run_tg"].ARGS = argparse.Namespace(conds=conditions)
        authority = ref["run_tg"].run_scene((scene, questions))
        lookup = {(r["set"], r["id"], r["cond"]): r for r in authority if r["arm"] == "main"}
        for row in rows:
            cond = prefix if settings["fusion"] == "all" else prefix + "+f_" + row["rule"] + "+dc+rv"
            original = lookup[(row["set"], row["id"], cond)]
            if row["pred"] != original["pred"] or row["score"] != original["score"]:
                parity.append({"set": row["set"], "id": row["id"], "ours": row, "authority": original})
    return {"scene": scene, "rows": rows, "errors": errors, "parity": parity,
            "raw": raw_metrics(scene, data, base) if settings["raw"] else None}


def run(args):
    os.environ["GEO_BAKEOFF_FUSION_SOURCE"] = "policy"
    ref = modules()
    items = ref["run_tg"].items()
    if args.mode == "selector":
        eligible = {p.stem.split("__", 1)[1] for p in RAW.glob("scannet__*.npz")}
        items = [(s, q) for s, q in items if s == "vsi" and q["scene_name"] in eligible
                 and q["question_type"] in TYPES | {"room_size_estimation"}]
    by_scene = defaultdict(list)
    for set_name, question in items:
        if not args.scenes or question["scene_name"] in args.scenes:
            by_scene[question["scene_name"]].append((set_name, question))
    if args.raw:
        for path in TOWER.glob("scannet__*.npz"):
            scene = path.stem.split("__", 1)[1]
            if not args.scenes or scene in args.scenes:
                by_scene.setdefault(scene, [])
    if not by_scene:
        raise ValueError("No eligible items or scenes")
    missing = [s for s in by_scene if not (Path(args.exports) / f"scannet__{s}.npz").is_file()]
    if missing:
        raise ValueError(f"Missing exports for paired scenes: {missing}")
    check_space(64 * 1024 ** 2)
    settings = vars(args)
    membership = [{"set": set_name, "id": str(q["id"]), "type": q["question_type"], "scene": scene, "mask": mask}
                  for scene, questions in by_scene.items() for set_name, q in questions
                  for mask in (("gt", "selector") if args.mode == "selector" else ("gt",))]
    representation = "grid51" if not args.native else "native" if args.native_calibration == "full" else "native_centred"
    config = {**settings, "created_at": utc(), "scenes": sorted(by_scene),
              "items_expected": sum(map(len, by_scene.values())) * (2 if args.mode == "selector" else 1),
              "reference_pin_sha256": sha256(ROOT / "out/receipts/reference_policy_pin.json"),
              "program_revision": "fixed_v3.14", "selector": "DEPLOY portable_np logistic; tau .15; learned merge .2",
              "adapter_revision": "deployed_selector_missing_name_guard",
              "adapter_sha256": sha256(Path(__file__)),
              "code_sha256": {p.name: sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))},
              "baseline_sha256": sha256(args.baseline) if args.baseline else None,
              "geometry_summary_sha256": sha256(Path(args.exports) / "summary.json") if (Path(args.exports) / "summary.json").exists() else None,
              "membership_sha256": row_membership(membership), "representation": representation,
              "calibration": calibration_label(args.exports, representation),
              "primary_protocol": PRIMARY, "primary_protocol_sha256": json_hash(PRIMARY),
              "policy_scope": {"vsi": policy_scope("vsi", args.fusion), "vsti": policy_scope("vsti", args.fusion)},
              "vsti_selector": "deferred; no cache; never included in the real-mask total"}
    out = prepare_stage(args.out, config, args.resume)
    configuration = fingerprint(config)
    if args.resume and (out / "COMPLETE.json").exists():
        from .provenance import verify_pricing_cell
        try:
            verify_pricing_cell(out)
            return
        except (ValueError, KeyError, FileNotFoundError, json.JSONDecodeError):
            pass
    if args.resume:
        preserve_files(out, [out / name for name in
                            ("rows.jsonl", "raw.jsonl", "scores.json", "scores_fallback.json", "errors.json",
                             "errors_by_type.json", "parity.json", "raw_summary.json", "COMPLETE.json")], "pricing_aggregate")
    rows, raw, errors, parity = [], [], [], []
    start = time.monotonic()
    results = {}
    if args.resume:
        for scene in by_scene:
            path = out / "scene_results" / f"{scene}.json"
            if path.exists():
                try:
                    results[scene] = load_scene_result(path, scene, [r for r in membership if r["scene"] == scene], configuration)
                except (ValueError, KeyError, json.JSONDecodeError):
                    preserve_files(out, [path], scene)
    jobs = sorted(((scene, questions) for scene, questions in by_scene.items() if scene not in results),
                  key=lambda pair: (-len(pair[1]), pair[0]))
    reused = len(results)
    progress(out / "progress.json", state="running", scenes_done=reused, scenes_total=len(by_scene),
             items_done=sum(len(r["rows"]) for r in results.values()))
    if jobs:
        with get_context("spawn").Pool(args.workers, initializer=initialize, initargs=(settings,)) as pool:
            for result in pool.imap_unordered(scene_job, jobs):
                result = json.loads(json.dumps(result, allow_nan=False, default=float))
                dump_json(out / "scene_results" / f"{result['scene']}.json",
                          {"result": result, "result_sha256": json_hash(result), "configuration_fingerprint": configuration})
                results[result["scene"]] = result
                progress(out / "progress.json", state="running", scenes_done=len(results), scenes_total=len(by_scene),
                         items_done=sum(len(r["rows"]) for r in results.values()))
    with (out / "rows.jsonl").open("x") as row_file, (out / "raw.jsonl").open("x") as raw_file:
        for scene in sorted(results):
            result = results[scene]
            rows.extend(result["rows"])
            errors.extend(result["errors"])
            parity.extend(result["parity"])
            for row in result["rows"]:
                row_file.write(json.dumps(row, allow_nan=False, default=float) + "\n")
            if result["raw"]:
                raw.append(result["raw"])
                raw_file.write(json.dumps(result["raw"], allow_nan=False) + "\n")
    baseline = [json.loads(line) for line in open(args.baseline)] if args.baseline else None
    dump_json(out / "scores.json", summarize(rows, baseline))
    fb_rows = [{**r, "score": r["fb"]} for r in rows]
    fb_baseline = [{**r, "score": r["fb"]} for r in baseline] if baseline else None
    dump_json(out / "scores_fallback.json", summarize(fb_rows, fb_baseline))
    dump_json(out / "errors.json", errors)
    error_counts = defaultdict(int)
    for row in errors:
        error_counts["|".join((row["set"], row["type"], row["mask"]))] += 1
    dump_json(out / "errors_by_type.json", dict(error_counts))
    dump_json(out / "parity.json", {"mismatches": parity, "authority": args.parity})
    aggregate = {}
    for metric in ("frame_log_scale_std", "scale_ratio"):
        values = [r["depth"][metric] for r in raw if r["depth"][metric] is not None]
        aggregate[metric] = {"mean": float(np.mean(values)), "median": float(np.median(values))} if values else None
    for region in ("overall", "edge1", "edge5", "object_mask"):
        values = [r["depth"][region] for r in raw if region in r["depth"]]
        count = sum(v["n"] for v in values)
        if count:
            aggregate[region] = {"pixels": count, "absrel": sum(v["absrel_sum"] for v in values) / count,
                                 "delta1": sum(v["delta1_sum"] for v in values) / count}
    dump_json(out / "raw_summary.json", aggregate)
    progress(out / "progress.json", state="complete", scenes_done=len(by_scene), scenes_total=len(by_scene), items_done=len(rows),
             errors=len(errors), parity_mismatches=len(parity), seconds=time.monotonic()-start)
    validate_pricing(rows, config, parity)
    dump_json(out / "COMPLETE.json", {
        "finished_at": utc(), "rows": len(rows), "program_errors": len(errors), "errors_by_type": dict(error_counts),
        "calibration": config["calibration"], "membership_sha256": config["membership_sha256"],
        "verified_reused_scenes": reused,
        "files": {name: sha256(out / name) for name in PRICING_FILES},
    })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exports", default=str(TOWER))
    parser.add_argument("--out", required=True)
    parser.add_argument("--fusion", choices=("all", "policy"), required=True)
    parser.add_argument("--mode", choices=("gt", "selector"), default="gt")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--scenes", nargs="+")
    parser.add_argument("--baseline")
    parser.add_argument("--native")
    parser.add_argument("--native-calibration", choices=("full", "legacy"), default="full")
    parser.add_argument("--raw", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--parity", choices=("vcd", "g3t"))
    args = parser.parse_args()
    if not 1 <= args.workers <= 8:
        raise ValueError("At most eight single-threaded pricing workers")
    run(args)


if __name__ == "__main__":
    main()
