"""Build the Cambrian-P pose-only rows (Pose-35K analogue) at the rows' 32 frames, on Trinity (CPU only).

Scenes: every training scene of the PD label bank (label_bank_1247_v2: the 1,247 d1/d2 training scenes; the held-out
38 and every benchmark authority are already excluded there). Samples: 28 per scene (~35k, the Pose-35K count at
beta = 1; L/frames64_20261030/PLAN.md section 3), drawn by student_pilot.pose_samples (CUT3R's two modes, N in
{8, 16, 24, 32}). Poses: the 32 metric camera-to-world poses and intrinsics of the scene's rung-1 snapshot (the
stage-1 builder's bundle, ScanNet++ intrinsics from official calibration); every scene's natural-order targets must
equal the bank's anchors (max position error and rotation error reported) or the scene is deferred.

  python tools/build_pose_rows.py --bundle B.json.gz --scannetpp-intrinsics I.json --bank label_bank_1247_v2.npz \
      --output-dir <new dir> [--samples-per-scene 28 --seed 17]
"""
import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from student_pilot import pose_samples  # noqa: E402
from student_pilot.camera_targets import FRAMES  # noqa: E402
from student_pilot.compact_label_bank import frame_set_sha256, read_bank  # noqa: E402
from tools.label_bank_build import DATASET_TOKENS, scene_token  # noqa: E402

SAMPLES_PER_SCENE = 28
POSITION_TOLERANCE_M = 1e-3
ROTATION_TOLERANCE = 1e-3  # quaternion component difference


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def scene_poses(snapshot, spp_intrinsics, key):
    intrinsics = snapshot.get("intrinsics")
    raster = snapshot.get("raster_hw")
    if key in spp_intrinsics:
        intrinsics, raster = spp_intrinsics[key]["intrinsics"], spp_intrinsics[key]["raster_hw"]
    if intrinsics is None or raster is None:
        return None
    intrinsics = np.asarray(intrinsics, dtype=np.float64)
    if intrinsics.ndim == 2:
        intrinsics = np.repeat(intrinsics[None], FRAMES, axis=0)
    return {"c2w": np.asarray(snapshot["camera_poses"], dtype=np.float64), "intrinsics": intrinsics,
            "raster_hw": tuple(int(v) for v in raster)}


def agreement(poses, bank, index):
    camera, mask, _, _ = pose_samples.encode_sample(poses["c2w"], poses["intrinsics"], poses["raster_hw"], list(range(FRAMES)))
    bank_mask = bank["camera_mask"][index].astype(bool)
    both = mask & bank_mask
    if not both.any():
        return None
    reference = bank["camera"][index].astype(np.float64)
    return {"position_m": float(np.abs(camera[both, :3] - reference[both, :3]).max()),
            "rotation": float(np.abs(camera[both, 3:7] - reference[both, 3:7]).max()),
            "fov": float(np.abs(camera[both, 7:] - reference[both, 7:]).max()),
            "groups": int(both.sum())}


def build(bundle_path, spp_path, bank_path, samples_per_scene, seed):
    bundle = json.load(gzip.open(bundle_path, "rt"))
    spp = json.loads(Path(spp_path).read_text())
    bank = read_bank(bank_path)
    lookup = {key: i for i, key in enumerate(zip(bank["dataset_tokens"].tolist(), bank["scene_tokens"].tolist()))}
    rows, deferred, checks = [], [], []
    seen = set()
    for key, snapshot in sorted(bundle["snapshots"].items()):
        dataset = DATASET_TOKENS.get(snapshot["dataset"])
        if dataset is None or snapshot.get("student_input") is None:
            continue
        token = scene_token(snapshot["dataset"], snapshot["scene"])
        index = lookup.get((dataset, token))
        if index is None:
            continue
        inputs = snapshot["student_input"]
        frames = [{"path": f"/data2/k3f8/{f['sha256'][:2]}/{f['sha256']}.png", "sha256": f["sha256"]} for f in inputs["frames"]]
        if frame_set_sha256(inputs["frame_indices"]) != str(bank["frame_set_sha256"][index]):
            deferred.append({"scene": token, "reason": "frame_set_differs_from_bank"})
            continue
        poses = scene_poses(snapshot, spp, key)
        if poses is None:
            deferred.append({"scene": token, "reason": "no_calibrated_intrinsics"})
            continue
        check = agreement(poses, bank, index)
        if (check is None or check["position_m"] > POSITION_TOLERANCE_M or check["rotation"] > ROTATION_TOLERANCE
                or check["fov"] > ROTATION_TOLERANCE):
            deferred.append({"scene": token, "reason": "poses_disagree_with_bank", "check": check})
            continue
        checks.append(check)
        source = {"qid": token, "dataset": dataset, "scene": token,
                  "student_input": {"question": "", "options": [], "frames": frames,
                                    "frame_indices": list(inputs["frame_indices"]), "timestamps": list(inputs["timestamps"]),
                                    "fps": float(inputs["fps"]), "total_num_frames": int(inputs["total_num_frames"])}}
        for sample in range(samples_per_scene):
            try:
                rows.append(pose_samples.build_row(source, poses, sample, seed))
            except ValueError as error:
                deferred.append({"scene": token, "sample": sample, "reason": str(error)})
        seen.add((dataset, token))
    missing = [list(key) for key in lookup if key not in seen and not any(item["scene"] == key[1] for item in deferred)]
    report = {"schema": "pose-only-rows-build-v1", "rows": len(rows), "scenes": len(seen), "bank_scenes": len(lookup),
              "samples_per_scene": samples_per_scene, "seed": seed, "deferred": deferred, "bank_scenes_without_snapshot": missing,
              "agreement_max": {key: max(item[key] for item in checks) for key in ("position_m", "rotation", "fov")} if checks else None,
              "modes": {mode: sum(r["pose_sample"]["mode"] == mode for r in rows) for mode in pose_samples.MODES},
              "sizes": {str(n): sum(r["pose_sample"]["frames"] == n for r in rows) for n in pose_samples.SAMPLE_SIZES},
              "inputs": {"bundle_sha256": sha256_file(bundle_path), "scannetpp_intrinsics_sha256": sha256_file(spp_path),
                         "bank_sha256": sha256_file(bank_path)}}
    return rows, report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--scannetpp-intrinsics", required=True)
    parser.add_argument("--bank", required=True)
    parser.add_argument("--samples-per-scene", type=int, default=SAMPLES_PER_SCENE)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    rows, report = build(args.bundle, args.scannetpp_intrinsics, args.bank, args.samples_per_scene, args.seed)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=False)
    payload = ("\n".join(pose_samples.manifest_line(row) for row in rows) + "\n").encode()
    (out / "pose_rows.jsonl").write_bytes(payload)
    report["pose_rows_sha256"] = hashlib.sha256(payload).hexdigest()
    (out / "BUILD_REPORT.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print(json.dumps({key: report[key] for key in ("rows", "scenes", "bank_scenes", "agreement_max", "modes", "sizes")}))


if __name__ == "__main__":
    main()
