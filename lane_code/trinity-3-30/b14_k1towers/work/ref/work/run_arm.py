import argparse
import fcntl
import json
import os
import re
import subprocess
import sys
from uuid import uuid4
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def cpu_capacity(output):
    selected = None
    for index in range(2):
        handle = (output / f"cpu_capacity_{index}.lock").open("a")
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            selected = handle
            break
        except BlockingIOError:
            handle.close()
    if selected is None:
        raise RuntimeError("Both eight-thread reservations are occupied; no automatic relaunch")
    try:
        yield
    finally:
        selected.close()


def check_review(path, root, digest):
    if not path:
        raise PermissionError("An independent adapter review is required before GPU admission")
    path = Path(path).resolve()
    if not path.is_relative_to(root / "inbox"):
        raise PermissionError("Review approval must be inside the kit inbox")
    lines = [line.strip() for line in path.read_text().splitlines()]
    if "APPROVED" not in lines or f"kit_sha256: {digest}" not in lines:
        raise PermissionError("The independent review does not approve this exact kit seal")


def kit_roots(root, data=None, assets=None):
    expected = tuple((root / name).resolve() for name in ("data", "assets"))
    selected = tuple(Path(value).resolve() if value else fixed for value, fixed in zip((data, assets), expected))
    if selected != expected or any(not path.is_relative_to(root) for path in selected):
        raise PermissionError("Runtime data and assets must stay inside the sealed kit")
    return selected


def completed_exports(exports, scenes, native_root=None):
    from geo_bakeoff.contract import load_export
    from geo_bakeoff.native import verified_native
    from geo_bakeoff.provenance import verify_export_receipt
    exports = Path(exports)
    if not (exports / "summary.json").exists():
        return False
    try:
        summary = json.loads((exports / "summary.json").read_text())
        if {r["scene"] for r in summary["receipts"]} != set(scenes):
            return False
        for scene in scenes:
            row = verify_export_receipt(exports, scene)
            if row.get("native_depth"):
                if native_root is None:
                    return False
                frames = load_export(exports / f"scannet__{scene}.npz")["anchor_frame_indices"]
                verified_native(native_root, row["native_depth"], frames)
        return True
    except (ValueError, KeyError, OSError, AssertionError):
        return False


def check_resume_request(previous, identity):
    if previous.get("resume_identity") != identity:
        raise ValueError("Resume requires the same sealed epoch, source membership and native storage")


def main():
    from geo_bakeoff.arms import ARMS
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=sorted(ARMS), required=True)
    parser.add_argument("--video-root")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--asset-root")
    parser.add_argument("--data-root")
    parser.add_argument("--gpu")
    parser.add_argument("--go-file")
    parser.add_argument("--review-file")
    parser.add_argument("--native-output-root")
    parser.add_argument("--run-host")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--vnice", default="/data3/shared/scripts/vnice/vnice.sh")
    parser.add_argument("--scenes", nargs="+")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--skip-pricing", action="store_true")
    parser.add_argument("--price-only", action="store_true")
    args = parser.parse_args()
    if args.gpu is not None:
        if not args.gpu.isdecimal():
            raise ValueError("--gpu must be one physical GPU ordinal")
        args.gpu = str(int(args.gpu))
    root = Path(__file__).resolve().parents[1]
    output = Path(args.output_root).resolve()
    data, assets = kit_roots(root, args.data_root, args.asset_root)
    for path in (root, output, data, assets):
        if not (path.is_relative_to("/scratch") or path.is_relative_to("/dev/shm")):
            raise PermissionError(f"Node-local paths are required: {path}")
    if not data.is_dir() or not assets.is_dir() or not output.parent.is_dir():
        raise FileNotFoundError("Stage the payload and create the output's parent directory before launch")
    os.environ.update(GEO_BAKEOFF_ROOT=str(root), GEO_BAKEOFF_OUTPUT_ROOT=str(output),
                      GEO_BAKEOFF_ASSETS=str(assets), GEO_BAKEOFF_DATA_ROOT=str(data))
    os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu or ""
    from geo_bakeoff.backends import weight_file
    from geo_bakeoff.contract import load_export
    from geo_bakeoff.exporting import preflight_entries, read_manifest
    from geo_bakeoff.guard import guarded
    from geo_bakeoff.inputs import TOWER, build_manifest, manifest_identity
    from geo_bakeoff.provenance import verify_export_receipt, verify_arm_epoch, verify_pricing_cell
    from geo_bakeoff.protocol import calibration_label
    from geo_bakeoff.io import check_space, dump_json, json_hash, sha256, utc
    from geo_bakeoff.resume import preserve_files
    from geo_bakeoff.safety import validate_device
    config = ARMS[args.arm]
    seal = root / "KIT_SEAL.json"
    if not seal.is_file():
        raise FileNotFoundError("The validated kit seal is missing")
    for name, digest in json.loads(seal.read_text())["files"].items():
        if sha256(root / name) != digest:
            raise ValueError(f"Sealed code differs: {name}")
    output.mkdir(exist_ok=True)
    run_name = args.arm + ("_pricing" if args.price_only else "")
    run = output / run_name
    if run.exists() and not args.resume:
        raise FileExistsError("Use --resume explicitly to reuse verified files in an existing run")
    if args.resume and not run.exists():
        raise FileNotFoundError("There is no run to resume")
    run_id = json_hash({"output": str(output), "kit": sha256(seal)})[:16]
    requested = set(args.scenes or [p.stem.split("__", 1)[1] for p in TOWER.glob("scannet__*.npz")])
    if not requested:
        raise ValueError("No paired scenes")
    scene_names, deferred = set(), []
    input_identity, needs_inference = None, False
    check_space(1024 ** 3)
    if config["kind"] == "native" and not args.price_only:
        if not args.video_root:
            raise ValueError("--video-root is required for a native model")
        if not args.native_output_root:
            raise ValueError("--native-output-root is required; native and 51-grid results stay separate")
        name = config["model"]
        weight = weight_file(name, "model.pt" if name.startswith("moge") else "model.safetensors")
        stamp = json_hash({"video_root": str(Path(args.video_root).resolve()), "scenes": sorted(requested)})[:12]
        manifest_path = output / "preflight" / f"{args.arm}_{stamp}.json"
        fresh = build_manifest([args.video_root], decoded_root=output / "preflight/decoded")
        if manifest_path.exists():
            manifest = read_manifest(manifest_path)
            if manifest_identity(manifest) != manifest_identity(fresh):
                raise ValueError("Native inputs changed; choose a fresh run epoch")
        else:
            dump_json(manifest_path, fresh)
            manifest = fresh
        input_identity = manifest_identity(manifest)
        entries = [r for r in manifest["scenes"] if r["scene"] in requested]
        if len(entries) != len(requested):
            raise ValueError("A requested scene is absent from the frozen frame contract")
        for entry in entries:
            try:
                preflight_entries([entry])
                scene_names.add(entry["scene"])
            except (ValueError, FileNotFoundError) as exc:
                deferred.append({"scene": entry["scene"], "reason": str(exc)})
        if not Path(args.vnice).is_file() or Path(args.vnice).resolve() != Path("/data3/shared/scripts/vnice/vnice.sh").resolve():
            raise FileNotFoundError(args.vnice)
        needs_inference = not (args.resume and completed_exports(run / "exports", scene_names, args.native_output_root))
        if not args.check_only and needs_inference:
            validate_device("cuda", args.go_file)
            check_review(args.review_file, root, sha256(seal))
            from geo_bakeoff.native import native_preflight
            native_preflight(args.native_output_root, len(scene_names), "cuda", args.run_host)
    else:
        for scene in requested:
            try:
                baseline = load_export(TOWER / f"scannet__{scene}.npz")
                if args.price_only and config["kind"] != "cached":
                    verify_arm_epoch(output / args.arm / "exports", sha256(seal))
                    verify_export_receipt(output / args.arm / "exports", scene)
                    load_export(output / args.arm / "exports" / f"scannet__{scene}.npz", baseline["anchor_frame_indices"])
                elif config["kind"] != "native":
                    load_export(TOWER.parent / config["baseline"] / f"scannet__{scene}.npz", baseline["anchor_frame_indices"])
                    for name in (config.get("candidate"), config.get("second")):
                        if name:
                            verify_arm_epoch(output / f"{name}_native/exports", sha256(seal))
                            verify_export_receipt(output / f"{name}_native/exports", scene)
                            load_export(output / f"{name}_native/exports/scannet__{scene}.npz", baseline["anchor_frame_indices"])
                scene_names.add(scene)
            except (ValueError, FileNotFoundError) as exc:
                deferred.append({"scene": scene, "reason": str(exc)})
    if not scene_names:
        raise ValueError(f"No admissible sources; all {len(requested)} remain deferred: {deferred}")
    extra = ["--scenes", *sorted(scene_names)]
    if args.check_only:
        print(json.dumps({"cpu_preflight": "passed", "arm": args.arm, "scenes": len(scene_names),
                          "requested": len(requested), "deferred": deferred, "gpu_launched": False,
                          "gpu_authorization": "GO, independent review and native storage are checked at GPU admission"}, indent=2))
        return
    identity = json_hash({"arm": args.arm, "run_id": run_id, "scenes": sorted(scene_names),
                          "requested": sorted(requested), "input": input_identity,
                          "native_root": str(Path(args.native_output_root).resolve()) if args.native_output_root else None})
    with cpu_capacity(output), (output / f"{run_name}.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        request = {**vars(args), "created_at": utc(), "kit_seal_sha256": sha256(seal),
                   "scenes": sorted(scene_names), "requested_scenes": sorted(requested),
                   "deferred_sources": deferred, "cpu_threads_maximum": 8, "run_id": run_id, "resume_identity": identity}
        if args.resume:
            check_resume_request(json.loads((run / "request.json").read_text()), identity)
            preserve_files(run, [run / "COMPLETE.json", run / "FAILED.json"], "terminal")
        else:
            run.mkdir()
            dump_json(run / "request.json", request)
        attempt = run / "attempts" / uuid4().hex
        dump_json(attempt / "request.json", request)
        env = {key: value for key, value in os.environ.items()
               if "API_KEY" not in key and "AUTH_TOKEN" not in key and key not in ("HF_TOKEN", "HUGGINGFACE_HUB_TOKEN")}
        events = root / "events"
        exports = run / "exports"
        calibrations, cells = {}, {}
        try:
            if args.price_only:
                exports = TOWER.parent / config["baseline"] if config["kind"] == "cached" else output / args.arm / "exports"
            elif config["kind"] == "native" and needs_inference:
                checkpoint_rows = [json.loads(line) for line in (assets / "downloads.jsonl").read_text().splitlines()]
                checkpoint = next(r for r in checkpoint_rows if r["path"].endswith(f"/{config['model']}/{weight.name}") and r["verified_expected_sha256"])
                if sha256(weight) != checkpoint["sha256"]:
                    raise ValueError("Checkpoint bytes differ from the authenticated download")
                command = [sys.executable, "-m", "geo_bakeoff.exporting", "infer", "--model", config["model"],
                           "--manifest", str(manifest_path), "--out", str(exports), "--device", "cuda",
                           "--go-file", args.go_file, "--threads", "8", "--tokens", "3600",
                           "--native-output-root", args.native_output_root, "--run-host", args.run_host,
                           "--run-id", run_id, *extra]
                if args.resume and exports.exists():
                    command += ["--resume"]
                if config["model"] == "mapanything":
                    command += ["--project-principal-point"]
                model_env = env.copy()
                if config["model"] == "moge3":
                    model_env["PYTHONPATH"] = str(root / "runtime/numpy2") + ":" + model_env["PYTHONPATH"]
                with (output / f"gpu_{args.gpu}.lock").open("a") as gpu_lock:
                    fcntl.flock(gpu_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    from geo_bakeoff.admission import free_card
                    admission = free_card(args.gpu, args.run_host)
                    dump_json(attempt / "gpu_admission.json", admission)
                    model_env["CUDA_VISIBLE_DEVICES"] = admission["uuid"]
                    guarded(command, exports / "progress.json", events, args.arm + "_native", run / "inference.log",
                            model_env, args.vnice, resume=args.resume)
            elif config["kind"] == "cached":
                exports = TOWER.parent / config["baseline"]
            elif config["kind"] != "native":
                command = [sys.executable, "-m", "geo_bakeoff.exporting", "hybrid", "--kind", config["kind"],
                           "--tower", str(TOWER.parent / config["baseline"]),
                           "--candidate", str(output / f"{config['candidate']}_native/exports"), "--out", str(exports), *extra]
                if config.get("second"):
                    command += ["--second", str(output / f"{config['second']}_native/exports")]
                if args.resume and exports.exists():
                    command += ["--resume"]
                cpu_env = {**env, "CUDA_VISIBLE_DEVICES": "", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
                guarded(command, exports / "progress.json", events, args.arm + "_hybrid", run / "hybrid.log", cpu_env, resume=args.resume)
            if config["kind"] != "cached":
                summary = json.loads((exports / "summary.json").read_text())
                receipts = {row["scene"]: row for row in summary["receipts"]}
                if summary["status"] != "complete" or not scene_names <= receipts.keys():
                    raise ValueError("Producer summary does not cover every admitted scene")
                for scene in scene_names:
                    verify_export_receipt(exports, scene)
            if not args.skip_pricing:
                cpu_env = {**env, "CUDA_VISIBLE_DEVICES": "", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
                representations = ["grid51"]
                if args.native_output_root and config["kind"] in ("native", "depth", "pose_g3t", "average", "consensus"):
                    representations.append("native")
                    if config.get("model", config.get("candidate")) == "mapanything" and config["kind"] in ("native", "consensus"):
                        representations.append("native_centred")
                from geo_bakeoff.pricing import summarize
                for fusion in ("all", "policy"):
                    for mode in ("gt", "selector"):
                        subsets = {}
                        for tower in ("g3t", "vcd"):
                            source = root / "out/baselines" / f"{tower}_{fusion}_{mode}" / "rows.jsonl"
                            subsets[tower] = [r for r in map(json.loads, source.read_text().splitlines()) if r["scene"] in scene_names]
                        if not subsets["g3t"]:
                            deferred_path = run / f"{fusion}_{mode}_DEFERRED.json"
                            if not deferred_path.exists():
                                dump_json(deferred_path, {"reason": "No selector-covered items in the admitted source subset"})
                            continue
                        baseline = run / f"{fusion}_{mode}_baseline.jsonl"
                        if baseline.exists():
                            if [json.loads(line) for line in baseline.read_text().splitlines()] != subsets["g3t"]:
                                raise ValueError("The paired baseline changed on resume")
                        else:
                            with baseline.open("x") as f:
                                for row in subsets["g3t"]:
                                    f.write(json.dumps(row) + "\n")
                        for representation in representations:
                            label = f"{fusion}_{mode}_{representation}"
                            destination = run / label
                            command = [sys.executable, "-m", "geo_bakeoff.pricing_policy", "--fusion", fusion, "--mode", mode,
                                       "--exports", str(exports), "--workers", "4", "--baseline", str(baseline),
                                       "--out", str(destination), *extra]
                            if representation != "grid51":
                                command += ["--native", args.native_output_root]
                                if representation == "native_centred":
                                    command += ["--native-calibration", "legacy"]
                            if fusion == "policy" and mode == "gt" and representation == "grid51":
                                command += ["--raw"]
                            if args.resume and destination.exists():
                                command += ["--resume"]
                            guarded(command, destination / "progress.json", events, args.arm + "_" + label,
                                    run / f"{label}.log", cpu_env, resume=args.resume)
                            rows, cell_config = verify_pricing_cell(destination)
                            calibrations[label] = cell_config["calibration"]
                            cells[label] = sha256(destination / "COMPLETE.json")
                            if args.resume:
                                preserve_files(destination, [destination / "scores_vs_vcd.json", destination / "scores_fallback_vs_vcd.json"], "secondary_comparison")
                            dump_json(destination / "scores_vs_vcd.json", summarize(rows, subsets["vcd"]))
                            dump_json(destination / "scores_fallback_vs_vcd.json",
                                      summarize([{**r, "score": r["fb"]} for r in rows],
                                                [{**r, "score": r["fb"]} for r in subsets["vcd"]]))
            dump_json(run / "COMPLETE.json", {"finished_at": utc(), "arm": args.arm, "scenes": sorted(scene_names),
                                              "requested_scenes": sorted(requested), "deferred_sources": deferred,
                                              "scope": "inference_only" if args.skip_pricing else "paired_pricing",
                                              "status": "partial_input_coverage" if deferred else "complete",
                                              "request_sha256": sha256(run / "request.json"),
                                              "attempt": str(attempt.relative_to(run)), "pricing_cells": cells,
                                              "export_calibration": calibration_label(exports, "grid51"),
                                              "calibration": calibrations})
        except Exception as exc:
            dump_json(run / "FAILED.json", {"checked_at": utc(), "error": f"{type(exc).__name__}: {exc}"})
            raise


if __name__ == "__main__":
    main()
