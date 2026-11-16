import argparse
import json
import re
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import map_coordinates

from .backends import Backend
from .contract import camera_arrays, centre_projection, load_export, make_export, sample_grid, validate_frames, write_export
from .consensus import temporal_scales
from .hybrids import hybrid
from .inputs import TOWER, dense_tower, images_for_entry, frame_hashes
from .provenance import verify_export_receipt
from .io import ROOT, check_space, check_lane_budget, dump_json, local_output, json_hash, progress, sha256, utc
from .metrics import centre_scatter, depth_statistics, pose_statistics
from .reference import modules
from .safety import offline_model, validate_device
from .paths import mapped
from .native import native_preflight, resample, write_native
from .resume import prepare_stage, resume_scene, finish_summary


def code_pin():
    return {p.name: sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))}


def read_manifest(path):
    manifest = json.loads(Path(path).read_text())
    digest = manifest.pop("manifest_sha256")
    if json_hash(manifest) != digest:
        raise ValueError("Input manifest digest differs")
    manifest["manifest_sha256"] = digest
    if manifest["schema"] != "geometry-bakeoff-native64-v1":
        raise ValueError("Unknown input manifest schema")
    return manifest


def preflight_entries(entries):
    if not entries:
        raise ValueError("No input scenes selected")
    seen = set()
    for entry in entries:
        scene = entry["scene"]
        if scene in seen or not re.fullmatch(r"scene[0-9]+_[0-9]+", scene):
            raise ValueError("Invalid or duplicate scene identifier")
        seen.add(scene)
        baseline = load_export(TOWER / f"scannet__{scene}.npz")
        validate_frames(entry["dense_indices"], entry["anchor_slots"], baseline["anchor_frame_indices"])
        if entry["images"] is not None:
            if len(entry["images"]) != len(entry["dense_indices"]):
                raise ValueError("Incomplete dense image manifest")
            if [f["index"] for f in entry["images"]] != entry["dense_indices"]:
                raise ValueError("Image manifest ordinals differ")
            if any(not Path(f["path"]).is_file() for f in entry["images"]):
                raise FileNotFoundError(f"Missing dense image files for {scene}")
        elif not entry["video"] or not Path(entry["video"]).is_file():
            raise FileNotFoundError(entry.get("source_gate_reason") or f"Missing native video for {scene}; 32-frame substitutes are forbidden")


def resize_depth(depth, hw):
    h, w = hw
    ih, iw = depth.shape[-2:]
    yy, xx = np.meshgrid((np.arange(h) + .5) / h * ih - .5, (np.arange(w) + .5) / w * iw - .5, indexing="ij")
    return np.stack([map_coordinates(d, [yy, xx], order=1, mode="nearest", prefilter=False) for d in depth]).astype(np.float32)


def native_metrics(scene, prediction, exported, slots):
    ref = modules()
    base = ref["programs"].GTSource(mapped(f"/scratch/jjyeung/orch_cd/toolprog/work/gt/scannet/{scene}.npz"))
    depth = resize_depth(prediction.depth[slots], base.depth.shape[-2:])
    cameras, _ = camera_arrays(exported, base.depth.shape[-2:])
    k = prediction.intrinsics[slots].copy()
    k[:, 0] *= base.depth.shape[2] / prediction.source_hw[1]
    k[:, 1] *= base.depth.shape[1] / prediction.source_hw[0]
    aligned = ref["geomswap"].aligned_pose(cameras, base.c2w, base.valid, 1.)
    objects = centre_scatter(depth, aligned, k, base.inst, base.valid)
    gt_k = np.repeat(base.K[None], len(base.valid), axis=0)
    reference_objects = {r["instance"]: r for r in centre_scatter(base.depth, base.c2w, gt_k, base.inst, base.valid)}
    for row in objects:
        gt = reference_objects.get(row["instance"])
        row["gt_median_scatter_m"] = gt["median_scatter_m"] if gt else None
    native_depth = prediction.depth[slots]
    gt_native = resample(base.depth, native_depth.shape[-2:], order=0)
    labels_native = resample(base.inst, native_depth.shape[-2:], order=0)
    gy, gx = np.meshgrid(np.linspace(0, base.depth.shape[1], 51)-.5,
                         np.linspace(0, base.depth.shape[2], 51)-.5, indexing="ij")
    gt_grid = np.stack([map_coordinates(d, [gy, gx], order=0, mode="nearest") for d in base.depth])
    labels_grid = np.stack([map_coordinates(d, [gy, gx], order=0, mode="nearest") for d in base.inst])
    return {
        "scene": scene, "geometry_representation": "native_model_depth_resized_to_GT_240x320",
        "depth": depth_statistics(depth, base.depth, base.valid, base.inst),
        "native_grid": depth_statistics(native_depth, gt_native, base.valid, labels_native),
        "grid51": depth_statistics(exported["depth_grid"], gt_grid, base.valid, labels_grid),
        "gt_sampling": "nearest-neighbour from the available 240x320 GT; upsampling adds no GT detail",
        "raster_hw": {"native": list(native_depth.shape[-2:]), "grid51": [51, 51], "gt": list(base.depth.shape[-2:])},
        "pose": pose_statistics(cameras, base.c2w, base.valid), "objects": objects,
    }


def infer(args):
    manifest = read_manifest(args.manifest)
    entries = [s for s in manifest["scenes"] if not args.scenes or s["scene"] in args.scenes]
    if args.scenes and {s["scene"] for s in entries} != set(args.scenes):
        raise ValueError("Requested scene is absent from the frozen manifest")
    preflight_entries(entries)
    validate_device(args.device, args.go_file)
    native_root = native_preflight(args.native_output_root, len(entries), args.device, args.run_host) if args.native_output_root else None
    reserve = len(entries) * 2_500_000
    check_lane_budget(args.out, reserve)
    check_space(reserve)
    settings = vars(args).copy()
    settings.update(code_sha256=code_pin(), input_sha256=manifest["manifest_sha256"])
    root = prepare_stage(args.out, settings, args.resume)
    reused = {}
    if args.resume:
        for entry in entries:
            receipt = resume_scene(root, entry["scene"], native_root, entry)
            if receipt is not None:
                reused[entry["scene"]] = receipt
    progress(root / "progress.json", state="loading", model=args.model, scenes_done=0, scenes_total=len(entries))
    began = time.monotonic()
    written, receipts = 0, []
    try:
        with offline_model():
            backend = None
            for done, entry in enumerate(entries):
                scene = entry["scene"]
                if scene in reused:
                    receipts.append(reused[scene])
                    progress(root / "progress.json", state="resumed_verified", scene=scene,
                             scenes_done=done+1, scenes_total=len(entries))
                    continue
                if backend is None:
                    backend = Backend(args.model, args.device, args.threads, args.go_file)
                check_space(2_500_000)
                start = time.monotonic()
                progress(root / "progress.json", state="decoding", scene=scene, scenes_done=done, scenes_total=len(entries))
                images = images_for_entry(entry)
                decoded_hashes = frame_hashes(images)
                baseline, tower_cameras, frames, slots, hw = dense_tower(scene)
                if len(images) != len(frames):
                    raise ValueError("Not every dense frame reached the backend")
                progress(root / "progress.json", state="inference", scene=scene, scenes_done=done, scenes_total=len(entries))
                if args.device == "cuda":
                    backend.torch.cuda.reset_peak_memory_stats()
                def beat(frame, total):
                    progress(root / "progress.json", state="inference", scene=scene, scenes_done=done,
                             scenes_total=len(entries), dense_frames_done=frame, dense_frames_total=total)
                prediction = backend.predict(images, progress=beat, resolution=args.resolution, tokens=args.tokens)
                cameras = prediction.c2w if prediction.c2w is not None else tower_cameras
                intrinsics = prediction.intrinsics
                if args.project_principal_point:
                    intrinsics, projection = centre_projection(intrinsics, hw)
                    prediction.metadata["legacy_calibration_projection"] = projection
                data = make_export(cameras, intrinsics, prediction.depth, frames, slots, hw, baseline["gravity_up"])
                native_k = prediction.intrinsics.copy()
                native_k[:, 0] *= prediction.depth.shape[2] / hw[1]
                native_k[:, 1] *= prediction.depth.shape[1] / hw[0]
                scales, consensus = temporal_scales(prediction.depth, cameras, native_k)
                native_receipt = write_native(native_root, args.model, scene, prediction, frames, slots,
                                              args.device, args.run_id) if native_root else None
                progress(root / "progress.json", state="exporting", scene=scene, scenes_done=done, scenes_total=len(entries))
                path = root / f"scannet__{scene}.npz"
                write_export(path, data)
                dense_path = root / "dense" / f"scannet__{scene}.npz"
                dense_path.parent.mkdir(exist_ok=True)
                with dense_path.open("xb") as f:
                    np.savez_compressed(f, frame_indices=frames, anchor_slots=slots, c2w=cameras,
                                        intrinsics=prediction.intrinsics, depth_grid=sample_grid(prediction.depth),
                                        source_hw=np.array(hw), consensus_scales=scales)
                dump_json(root / "consensus" / f"{scene}.json", consensus)
                metrics_path = root / "native_metrics" / f"{scene}.json"
                dump_json(metrics_path, native_metrics(scene, prediction, data, slots))
                receipt = {
                    "scene": scene, "model": args.model, "device": args.device, "dense_frames": len(images),
                    "anchors": len(slots), "frame_indices": frames.tolist(), "seconds": time.monotonic()-start,
                    "decoded_frame_sha256": decoded_hashes,
                    "export_sha256": sha256(path), "dense_sha256": sha256(dense_path),
                    "native_metrics_sha256": sha256(metrics_path), "metadata": prediction.metadata,
                    "pose_source": args.model if prediction.c2w is not None else "g3t_frozen_vc_scale",
                    "gravity_source": "frozen_g3t_predicted_reference_up", "gt_used_at_inference": False,
                    "native_depth": native_receipt, "consensus_sha256": sha256(root / "consensus" / f"{scene}.json"),
                }
                if args.device == "cuda":
                    receipt.update(peak_allocated_bytes=backend.torch.cuda.max_memory_allocated(),
                                   peak_reserved_bytes=backend.torch.cuda.max_memory_reserved())
                dump_json(root / "receipts" / f"{scene}.json", receipt)
                receipts.append(receipt)
                written += path.stat().st_size + dense_path.stat().st_size + metrics_path.stat().st_size
                check_lane_budget(root)
                progress(root / "progress.json", state="running", scene=scene, scenes_done=done+1,
                         scenes_total=len(entries), bytes_written=written)
                print(json.dumps(receipt), flush=True)
        finish_summary(root, {"status": "complete", "scenes": len(receipts), "receipts": receipts,
                              "seconds": time.monotonic()-began, "verified_reused_scenes": len(reused)})
        progress(root / "progress.json", state="complete", scenes_done=len(entries), scenes_total=len(entries))
    except Exception as exc:
        dump_json(root / "failures" / f"{time.time_ns()}.json",
                  {"checked_at": utc(), "error": f"{type(exc).__name__}: {exc}", "scenes_complete": len(receipts)})
        progress(root / "progress.json", state="failed", scenes_done=len(receipts), scenes_total=len(entries), error=str(exc))
        raise


def hybrids(args):
    validate_device("cpu")
    tower = Path(args.tower)
    paths = sorted(tower.glob("scannet__*.npz"))
    if args.scenes:
        paths = [p for p in paths if p.stem.split("__", 1)[1] in args.scenes]
    if not paths:
        raise ValueError("No baseline scenes")
    for path in paths:
        for directory in [args.candidate] + ([args.second] if args.second else []):
            if not (Path(directory) / path.name).is_file():
                raise FileNotFoundError(f"Missing paired geometry: {Path(directory) / path.name}")
            verify_export_receipt(directory, path.stem.split("__", 1)[1])
    check_space(len(paths) * 500_000)
    check_lane_budget(args.out, len(paths)*500_000)
    candidate_model = json.loads((Path(args.candidate) / "config.json").read_text())["model"]
    settings = {**vars(args), "code_sha256": code_pin(), "candidate_model": candidate_model,
                "parent_summary_sha256": sha256(Path(args.candidate) / "summary.json"),
                "second_summary_sha256": sha256(Path(args.second) / "summary.json") if args.second else None}
    root = prepare_stage(args.out, settings, args.resume)
    receipts = []
    for index, path in enumerate(paths):
        if args.resume:
            receipt = resume_scene(root, path.stem.split("__", 1)[1])
            if receipt is not None:
                receipts.append(receipt)
                progress(root / "progress.json", state="resumed_verified", scenes_done=index+1, scenes_total=len(paths))
                continue
        baseline = load_export(path)
        candidate_path = Path(args.candidate) / path.name
        parent = verify_export_receipt(args.candidate, path.stem.split("__", 1)[1])
        candidate = load_export(candidate_path, baseline["anchor_frame_indices"])
        second_path = Path(args.second) / path.name if args.second else None
        second = load_export(second_path, baseline["anchor_frame_indices"]) if second_path else None
        model = json.loads((Path(args.candidate) / "config.json").read_text())["model"]
        recipe = {"kind": args.kind, "candidate_model": model, "candidate_native": parent.get("native_depth")}
        if args.kind == "consensus":
            with np.load(Path(args.candidate) / "dense" / path.name, allow_pickle=False) as z:
                if "consensus_scales" not in z.files:
                    raise ValueError("Dense native consensus factors are missing; do not fit on the 32 anchors")
                scales = z["consensus_scales"][z["anchor_slots"]]
            result = {key: value.copy() for key, value in candidate.items()}
            result["depth_grid"] *= scales[:, None, None]
            parameters = {"kind": "consensus", "scales": scales.tolist(), "gt_used": False, "fit_frames": 64}
            recipe["scales"] = scales.tolist()
        else:
            result, parameters = hybrid(args.kind, baseline, candidate, second)
        if args.second:
            recipe["second_model"] = json.loads((Path(args.second) / "config.json").read_text())["model"]
            other_parent = verify_export_receipt(args.second, path.stem.split("__", 1)[1])
            if parent.get("decoded_frame_sha256") != other_parent.get("decoded_frame_sha256"):
                raise ValueError("Ensemble parents used different decoded frames")
            recipe["second_native"] = other_parent.get("native_depth")
        output = root / path.name
        write_export(output, result)
        dump_json(root / "native_recipes" / f"{path.stem.split('__', 1)[1]}.json", recipe)
        row = {
            "scene": path.stem.split("__", 1)[1], "parameters": parameters, "output_sha256": sha256(output),
            "tower_sha256": sha256(path), "candidate_sha256": sha256(candidate_path),
            "second_sha256": sha256(second_path) if second_path else None, "gt_used": False,
            "decoded_frame_sha256": parent.get("decoded_frame_sha256"),
            "native_recipe_sha256": sha256(root / "native_recipes" / f"{path.stem.split('__', 1)[1]}.json"),
        }
        dump_json(root / "receipts" / f"{row['scene']}.json", row)
        receipts.append(row)
        progress(root / "progress.json", state="running", scenes_done=index+1, scenes_total=len(paths))
    finish_summary(root, {"status": "complete", "scenes": len(paths), "receipts": receipts})
    progress(root / "progress.json", state="complete", scenes_done=len(paths), scenes_total=len(paths))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("infer")
    p.add_argument("--model", choices=("moge2", "moge3", "pi3x", "mapanything", "da3"), required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    p.add_argument("--go-file")
    p.add_argument("--native-output-root")
    p.add_argument("--run-host")
    p.add_argument("--run-id")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--project-principal-point", action="store_true")
    p.add_argument("--threads", type=int, default=8)
    p.add_argument("--resolution", type=int)
    p.add_argument("--tokens", type=int, default=3600)
    p.add_argument("--scenes", nargs="+")
    p = sub.add_parser("hybrid")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--kind", choices=("depth", "pose_g3t", "clip_scale", "clip_scale_depth_only", "frame_affine", "average", "consensus"), required=True)
    p.add_argument("--tower", default=str(TOWER))
    p.add_argument("--candidate", required=True)
    p.add_argument("--second")
    p.add_argument("--out", required=True)
    p.add_argument("--scenes", nargs="+")
    args = parser.parse_args()
    (infer if args.command == "infer" else hybrids)(args)


if __name__ == "__main__":
    main()
