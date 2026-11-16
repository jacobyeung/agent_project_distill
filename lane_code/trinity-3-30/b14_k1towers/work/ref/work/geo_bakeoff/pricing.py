import argparse
import json
import os
import time
from collections import defaultdict
from multiprocessing import get_context
from pathlib import Path

import numpy as np

from .contract import camera_arrays, load_export, raster_depth
from .io import ROOT, dump_json, progress, sha256, utc, local_output
from .metrics import centre_scatter, depth_statistics, paired_bootstrap, pose_statistics
from .reference import modules
from .paths import path as data_path


TOWER = data_path("/scratch/jjyeung/orch_cd/ttower/work/geo/heads_g3s64_vcd")
GT = data_path("/scratch/jjyeung/orch_cd/toolprog/work/gt/scannet")
VSI_FIX = "frameidx,axes,memory,extent,identity,round,vocab,gbox0".split(",")
VSTI_FIX = "frameidx,axes,memory,extent,identity,round".split(",")
_SETTINGS = None
_SELECTOR = None
_DIRECT = None


def initialize(settings):
    global _SETTINGS, _SELECTOR, _DIRECT
    _SETTINGS = settings
    modules()
    _DIRECT = direct_scores()
    if settings["mode"] == "selector":
        from .selectors import load_tables
        _SELECTOR = load_tables()


def direct_scores():
    path = modules()["common"].D_VSI
    with open(path) as f:
        return {str(r["raw_id"]): float(r["score"]) for r in map(json.loads, f)}


def with_fallback(rows, direct):
    result = []
    for row in rows:
        if row["set"] != "vsi":
            continue
        value = row["score"] if row["pred"] is not None else direct.get(str(row["id"]))
        if value is None:
            raise ValueError(f"Missing fixed direct fallback for VSI item {row['id']}")
        result.append({**row, "score": value})
    return result


def raw_metrics(scene, data, base):
    d = raster_depth(data["depth_grid"], base.depth.shape[-2:])
    c, k = camera_arrays(data, base.depth.shape[-2:])
    g = modules()["geomswap"]
    aligned = g.aligned_pose(c, base.c2w, base.valid, 1.)
    pred_scatter = centre_scatter(d, aligned, k, base.inst, base.valid)
    gt_k = np.repeat(base.K[None], len(base.valid), axis=0)
    gt_scatter = {r["instance"]: r for r in centre_scatter(base.depth, base.c2w, gt_k, base.inst, base.valid)}
    for row in pred_scatter:
        ref = gt_scatter.get(row["instance"])
        row["gt_median_scatter_m"] = ref["median_scatter_m"] if ref else None
        if ref:
            by_frame = dict(zip(ref["frames"], ref["centres"]))
            residuals = [np.array(c0) - by_frame[f] for f, c0 in zip(row["frames"], row["centres"]) if f in by_frame]
            row["median_centre_error_m"] = float(np.median(np.linalg.norm(residuals, axis=-1))) if residuals else None
    return {
        "scene": scene, "depth": depth_statistics(d, base.depth, base.valid, base.inst),
        "pose": pose_statistics(c, base.c2w, base.valid), "objects": pred_scatter,
        "raster_hw": list(base.depth.shape[-2:]), "geometry_representation": "51x51_export_bilinear",
    }


def scene_job(job):
    scene, questions = job
    settings, ref = _SETTINGS, modules()
    v, g, c, pr = [ref[x] for x in ("prog_v2", "geomswap", "common", "programs")]
    base = pr.GTSource(str(GT / f"{scene}.npz"))
    with np.load(GT / f"{scene}.npz", allow_pickle=False) as z:
        frames = z["frame_indices"]
    baseline = load_export(TOWER / f"scannet__{scene}.npz", frames)
    data = load_export(Path(settings["exports"]) / f"scannet__{scene}.npz", frames)
    rows, errors = [], []
    metrics = raw_metrics(scene, data, base) if settings["raw"] else None
    if settings["mode"] == "selector":
        from .selectors import GTGeometry, MaskContext, TowerGeometry, item_names, masks_for_scene
        masks_gt, unique, counting = masks_for_scene(scene, [q for _, q in questions], base, _SELECTOR)
        geometry = TowerGeometry(Path(settings["exports"]) / f"scannet__{scene}.npz")
        contexts = {
            "gt": MaskContext(geometry, masks_gt),
            "selector_unique": MaskContext(geometry, unique, cut=True),
            "selector_counting": MaskContext(geometry, counting),
        }
        if settings["gt_ceiling"]:
            contexts["ceiling"] = MaskContext(GTGeometry(base), masks_gt)
    else:
        depth = raster_depth(data["depth_grid"])
        cameras, intrinsics = camera_arrays(data)
        cameras = g.aligned_pose(cameras, base.c2w, base.valid, 1.)
        geo = g.Geo(base, depth, cameras, intrinsics)
        contexts = {"vsi": v.Ctx(geo, VSI_FIX, "B"), "vsti": v.Ctx(geo, VSTI_FIX, "B")}
    for set_name, q in questions:
        if settings["mode"] == "selector":
            keys = ["gt", "selector_counting" if q["question_type"] == "object_counting" else "selector_unique"]
            if settings["gt_ceiling"]:
                keys.append("ceiling")
        else:
            keys = [set_name]
        for key in keys:
            ctx = contexts[key]
            error = None
            try:
                missing = settings["mode"] == "selector" and any(n not in ctx.name2ids for n in item_names(v.T.parse_vsi(q)))
                prediction = None if missing else (v.run_vsi if set_name == "vsi" else v.run_vsti)(q, ctx)[0]
                prediction = v.finalize(q["question_type"], prediction, ctx.fixes)
            except Exception as exc:
                prediction, error = None, f"{type(exc).__name__}: {exc}"
                errors.append({"set": set_name, "id": str(q["id"]), "error": error})
            score = c.score(q["question_type"], prediction, q["ground_truth"])
            rows.append({
                "set": set_name, "id": str(q["id"]), "type": q["question_type"], "scene": scene,
                "mask": "selector" if key.startswith("selector") else "ceiling" if key == "ceiling" else "gt",
                "pred": prediction, "score": score, "error": error,
                "fb": score if prediction is not None else _DIRECT.get(str(q["id"])) if set_name == "vsi" else None,
            })
    parity = []
    if settings["reference_parity"] and settings["mode"] == "gt":
        ref["run_tg"].ARGS = argparse.Namespace(conds=["dT+pT+kT"])
        authority = ref["run_tg"].run_scene((scene, questions))
        expected = {(r["set"], r["id"]): r for r in authority if r["arm"] == "main"}
        for row in rows:
            original = expected[(row["set"], row["id"])]
            if row["score"] != original["score"] or row["pred"] != original["pred"]:
                parity.append({"id": row["id"], "set": row["set"], "ours": row, "authority": original})
    return {"scene": scene, "rows": rows, "raw": metrics, "errors": errors, "parity": parity}


def summarize(rows, baseline=None):
    group = defaultdict(list)
    ref_group = defaultdict(list)
    for row in rows:
        group[(row["set"], row["type"], row["mask"])].append(row)
    for row in baseline or rows:
        ref_group[(row["set"], row["type"], row["mask"])].append(row)
    return {"|".join(key): paired_bootstrap(values, ref_group[key]) for key, values in sorted(group.items())}


def run(args):
    ref = modules()
    all_questions = ref["run_tg"].items()
    if args.sets != "vsi,vsti":
        all_questions = [(s, q) for s, q in all_questions if s in args.sets.split(",")]
    if args.mode == "selector":
        from .selectors import RAW, TYPES
        all_questions = [(s, q) for s, q in all_questions if s == "vsi" and q["question_type"] in TYPES
                         and (RAW / f"scannet__{q['scene_name']}.npz").is_file()]
    by_scene = defaultdict(list)
    for set_name, question in all_questions:
        if not args.scenes or question["scene_name"] in args.scenes:
            by_scene[question["scene_name"]].append((set_name, question))
    if args.raw:
        for path in sorted(TOWER.glob("scannet__*.npz")):
            scene = path.stem.split("__", 1)[1]
            if not args.scenes or scene in args.scenes:
                by_scene.setdefault(scene, [])
    out = local_output(args.out)
    out.mkdir(parents=True, exist_ok=False)
    missing = [scene for scene in by_scene if not (Path(args.exports) / f"scannet__{scene}.npz").is_file()]
    if missing:
        dump_json(out / "missing.json", {"scenes": missing, "status": "blocked_not_silently_excluded"})
        raise ValueError(f"Missing geometry for {len(missing)} required scenes")
    settings = dict(exports=args.exports, mode=args.mode, raw=args.raw, reference_parity=args.reference_parity,
                    gt_ceiling=args.gt_ceiling, sets=args.sets)
    dump_json(out / "config.json", {
        "time": utc(), "settings": settings, "scenes": sorted(by_scene),
        "items": sum(map(len, by_scene.values())),
        "code_sha256": {p.name: sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))},
        "reference_pin_sha256": sha256(ROOT / "out/receipts/reference_pin.json"),
    })
    rows, raw, parity, errors = [], [], [], []
    started = time.monotonic()
    with (out / "rows.jsonl").open("x") as item_file, (out / "raw.jsonl").open("x") as raw_file:
        with get_context("spawn").Pool(args.workers, initializer=initialize, initargs=(settings,)) as pool:
            for done, result in enumerate(pool.imap_unordered(scene_job, sorted(by_scene.items())), 1):
                rows.extend(result["rows"])
                errors.extend(result["errors"])
                parity.extend(result["parity"])
                for row in result["rows"]:
                    item_file.write(json.dumps(row, allow_nan=False, default=float) + "\n")
                item_file.flush()
                if result["raw"]:
                    raw.append(result["raw"])
                    raw_file.write(json.dumps(result["raw"], allow_nan=False, default=float) + "\n")
                    raw_file.flush()
                progress(out / "progress.json", state="running", scenes_done=done, scenes_total=len(by_scene),
                         items_done=len(rows), last_scene=result["scene"])
                if done % 10 == 0 or done == len(by_scene):
                    print(f"{done}/{len(by_scene)} scenes, {len(rows)} rows, {time.monotonic()-started:.1f}s", flush=True)
    baseline = [json.loads(line) for line in open(args.baseline)] if args.baseline else None
    summary = summarize(rows, baseline)
    dump_json(out / "scores.json", summary)
    direct = direct_scores()
    fb_rows, fb_baseline = with_fallback(rows, direct), with_fallback(baseline, direct) if baseline else None
    if fb_rows:
        dump_json(out / "scores_fallback.json", summarize(fb_rows, fb_baseline))
    dump_json(out / "parity.json", {"reference": "gt_ceiling.run_tg.run_scene", "mismatches": parity, "checked": args.reference_parity})
    dump_json(out / "errors.json", errors)
    aggregate_raw = {}
    for region in ("overall", "edge5", "object_mask"):
        values = [r["depth"][region] for r in raw if region in r["depth"]]
        count = sum(v["n"] for v in values)
        if count:
            aggregate_raw[region] = {
                "pixels": count, "absrel": sum(v["absrel_sum"] for v in values) / count,
                "delta1": sum(v["delta1_sum"] for v in values) / count,
                "prediction_coverage": sum(v["predicted"] for v in values) / count,
            }
    for metric in ("scale_ratio", "frame_log_scale_std"):
        values = [r["depth"][metric] for r in raw if r["depth"][metric] is not None]
        aggregate_raw[metric] = float(np.median(values)) if values else None
    for metric in ("rotation_deg", "translation_m", "centre_relative"):
        values = [r["pose"][metric] for r in raw if r["pose"][metric] is not None]
        aggregate_raw[metric] = float(np.median(values)) if values else None
    dump_json(out / "raw_summary.json", {"scenes": len(raw), "metrics": aggregate_raw})
    progress(out / "progress.json", state="complete", scenes_done=len(by_scene), scenes_total=len(by_scene),
             items_done=len(rows), errors=len(errors), parity_mismatches=len(parity), seconds=time.monotonic()-started)
    print(json.dumps(summary, indent=2), flush=True)
    if parity:
        raise ValueError(f"{len(parity)} item-level parity differences")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exports", default=str(TOWER))
    parser.add_argument("--out", required=True)
    parser.add_argument("--mode", choices=("gt", "selector"), default="gt")
    parser.add_argument("--sets", default="vsi,vsti")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--scenes", nargs="+")
    parser.add_argument("--baseline")
    parser.add_argument("--raw", action="store_true")
    parser.add_argument("--reference-parity", action="store_true")
    parser.add_argument("--gt-ceiling", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.workers <= 8:
        raise ValueError("Pricing uses at most eight single-threaded workers")
    run(args)


if __name__ == "__main__":
    main()
