import argparse
import json
import time
from pathlib import Path

import numpy as np

from .backends import Backend
from .contract import centre_projection, make_export, write_export
from .inputs import dense_tower, fixture_images, frame_hashes
from .io import ROOT, check_space, dump_json, progress, sha256, utc
from .reference import modules
from .safety import offline_model


def run(args):
    root = ROOT / "out/smoke" / args.name
    root.mkdir(parents=True, exist_ok=False)
    images, frames, fixture = fixture_images(8)
    baseline, tower_cameras, dense_frames, _, hw = dense_tower("scene0011_00")
    if not np.array_equal(frames, dense_frames[:8]):
        raise ValueError("CPU fixture does not use the exact dense tower inputs")
    start = time.monotonic()
    check_space(16 * 1024 ** 2)
    progress(root / "progress.json", state="loading", model=args.model, device="cpu", frames_done=0, frames_total=8)
    try:
        with offline_model():
            backend = Backend(args.model, device="cpu", threads=args.threads)
            def beat(done, total):
                progress(root / "progress.json", state="inference", model=args.model, device="cpu", frames_done=done, frames_total=total)
            prediction = backend.predict(images, progress=beat, resolution=args.resolution, tokens=args.tokens)
        cameras = prediction.c2w if prediction.c2w is not None else tower_cameras[:8]
        with (root / "native_prediction.npz").open("xb") as f:
            np.savez_compressed(f, depth=prediction.depth, intrinsics=prediction.intrinsics,
                                c2w=cameras, source_hw=prediction.source_hw, frame_indices=frames)
        intrinsics = prediction.intrinsics
        if args.project_principal_point:
            intrinsics, projection = centre_projection(intrinsics, hw)
            prediction.metadata["legacy_calibration_projection"] = projection
        data = make_export(cameras, intrinsics, prediction.depth, frames, np.arange(8), hw,
                           baseline["gravity_up"], production=False)
        path = root / "smoke.npz"
        write_export(path, data, expected_count=8)
        reader = modules()["programs"].load_heads(str(path))
        for k in range(1, 9):
            r, t = reader.cam(k)
            d = reader._depth(k - 1, np.array([100., 500., 900.]), np.array([100., 500., 900.]))
            if not np.isfinite(r).all() or not np.isfinite(t).all() or not np.isfinite(d).all():
                raise ValueError("The unchanged pricing loader rejected the smoke geometry")
        receipt = {
            "checked_at": utc(), "status": "passed", "model": args.model, "device": "cpu",
            "frames": frames.tolist(), "input_images": [str(p) for p in images], "fixture": str(fixture["source"]),
            "seconds": time.monotonic() - start, "native_shape": list(prediction.depth.shape),
            "positive_depth_fraction": float((prediction.depth > 0).mean()),
            "depth_quantiles_m": np.percentile(prediction.depth[prediction.depth > 0], [1, 50, 99]).tolist(),
            "output_sha256": sha256(path), "metadata": prediction.metadata,
            "decoded_frame_sha256": frame_hashes(images),
            "loader": modules()["programs"].__file__, "scope": "eight-frame CPU inference, not a 64-frame GPU memory test",
        }
        dump_json(root / "receipt.json", receipt)
        progress(root / "progress.json", state="complete", model=args.model, device="cpu", frames_done=8, frames_total=8)
        print(json.dumps(receipt, indent=2), flush=True)
    except Exception as exc:
        dump_json(root / "failure.json", {"checked_at": utc(), "model": args.model, "error": f"{type(exc).__name__}: {exc}",
                                         "device": "cpu", "seconds": time.monotonic() - start,
                                         "principal_points": prediction.intrinsics[:, :2, 2].tolist() if "prediction" in locals() else None})
        progress(root / "progress.json", state="failed", model=args.model, device="cpu", error=str(exc))
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=("moge2", "moge3", "mapanything", "pi3x", "da3"), required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--resolution", type=int)
    parser.add_argument("--tokens", type=int, default=1200)
    parser.add_argument("--project-principal-point", action="store_true")
    run(parser.parse_args())


if __name__ == "__main__":
    main()
