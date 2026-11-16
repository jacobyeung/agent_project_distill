import hashlib
import fcntl
import json
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

from .contract import gravity_rotation, load_export, validate_frames
from .io import ROOT, dump_json, json_hash, sha256, utc
from .paths import path as data_path, mapped


TOWER = data_path("/scratch/jjyeung/orch_cd/ttower/work/geo/heads_g3s64_vcd")
RAW = data_path("/scratch/jjyeung/orch_cd/ttower/work/g3t/n64")
FIXTURE = data_path("/scratch/jjyeung/orch_cd/tower_read/work/inputs/camera_native64.json")
FRAME_MANIFEST = data_path("/scratch/jjyeung/orch_cd/frames/work/harness/x64.json")


def local_input(path):
    path = Path(path).resolve()
    if not (path.is_relative_to("/scratch") or path.is_relative_to("/dev/shm")):
        raise PermissionError(f"Inference inputs must be staged on node-local storage: {path}")
    return path


def dense_tower(scene):
    baseline = load_export(TOWER / f"scannet__{scene}.npz")
    with np.load(RAW / f"scannet__{scene}.npz", allow_pickle=False) as z:
        raw = z["raw_pose"].copy()
        frames, slots, hw = z["frame_indices"], z["anchor_slots"], z["source_hw"]
    validate_frames(frames, slots, baseline["anchor_frame_indices"])
    rr = Rotation.from_quat(raw[:, 3:7]).as_matrix().transpose(0, 2, 1)
    t = -np.einsum("nij,nj->ni", rr, raw[:, :3]) * float(baseline["scale"])
    gravity = gravity_rotation(baseline["gravity_up"])
    cameras = np.repeat(np.eye(4)[None], len(raw), axis=0)
    cameras[:, :3, :3] = gravity @ rr
    cameras[:, :3, 3] = t @ gravity.T
    if not np.allclose(cameras[slots, :3, 3], baseline["t_grav"], atol=2e-5):
        raise ValueError("Dense G3T pose scaling disagrees with the baseline export")
    return baseline, cameras, frames, slots, tuple(map(int, hw))


def fixture_images(count=8):
    data = json.loads(FIXTURE.read_text())
    frames = data["frames"][:count]
    for frame in frames:
        path = local_input(mapped(frame["path"]))
        if sha256(path) != frame["sha256"]:
            raise ValueError(f"Fixture RGB digest differs: {path}")
    return [data_path(f["path"]) for f in frames], np.array([f["index"] for f in frames]), data


def decode_selected(path, indices, expected_total, expected_hw):
    import av
    path = local_input(path)
    indices = np.asarray(indices, np.int64)
    if len(indices) < 64 or np.any(np.diff(indices) <= 0):
        raise ValueError("Video reconstruction requires at least 64 distinct native ordinals")
    wanted, images = set(indices.tolist()), {}
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        stream.thread_type = "SLICE"
        stream.codec_context.thread_count = 1
        if stream.frames and stream.frames != expected_total:
            raise ValueError(f"Native video count differs ({stream.frames} != {expected_total}); a 32-frame proxy is not admissible")
        if (stream.height, stream.width) != tuple(expected_hw):
            raise ValueError("Native video raster differs from the fixed frame contract")
        total = 0
        for ordinal, frame in enumerate(container.decode(video=0)):
            total = ordinal + 1
            if ordinal in wanted:
                images[ordinal] = frame.to_ndarray(format="rgb24")
        if total != expected_total or set(images) != wanted:
            raise ValueError("Decoded video ordinals do not cover the exact reconstruction input")
    return [images[i] for i in indices]


def rgb_array(image):
    if isinstance(image, np.ndarray):
        value = image
    else:
        from PIL import Image
        with Image.open(image) as source:
            value = np.asarray(source.convert("RGB"))
    if value.dtype != np.uint8 or value.ndim != 3 or value.shape[-1] != 3:
        raise ValueError("Decoded identity requires uint8 RGB")
    return np.ascontiguousarray(value)


def frame_hashes(images):
    return [hashlib.sha256(rgb_array(image).tobytes()).hexdigest() for image in images]


def verify_frame_hashes(images, expected):
    actual = frame_hashes(images)
    if actual != expected:
        raise ValueError("Decoded RGB bytes differ from the admitted frame identities")
    return actual


def compare_decoded(images, references, threshold=45.):
    if len(images) != 64 or len(references) != 64:
        raise ValueError("Decoder calibration requires all 64 reference frames")
    psnr = []
    for index, (image, reference) in enumerate(zip(images, references)):
        a, b = rgb_array(image), rgb_array(reference)
        if a.shape != b.shape:
            raise ValueError("Decoder calibration rasters differ")
        mse = float(np.mean((a.astype(np.float64)-b.astype(np.float64)) ** 2))
        value = float(10*np.log10(255.**2/mse)) if mse else None
        if value is not None and value <= threshold:
            raise ValueError(f"Decoder calibration failed at frame {index}: PSNR={value}")
        psnr.append(value)
    return {"status": "passed", "threshold_db": threshold, "psnr_db": psnr,
            "decoded_sha256": frame_hashes(images), "reference_sha256": frame_hashes(references)}


def bind_decoded_frames(entry, hashes):
    if entry.get("decoded_sha256") is not None and hashes != entry["decoded_sha256"]:
        raise ValueError("Decoded frames differ from the preflight reference")
    if not entry.get("decoded_registry"):
        return
    path = local_input(entry["decoded_registry"])
    path.parent.mkdir(parents=True, exist_ok=True)
    proof = {"scene": entry["scene"], "dense_indices": entry["dense_indices"],
             "source_hw": entry["source_hw"], "decoded_sha256": hashes,
             "video_sha256": entry.get("video_sha256"),
             "image_sha256": [r["sha256"] for r in entry["images"]] if entry["images"] else None}
    with path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if path.exists():
            if json.loads(path.read_text()) != proof:
                raise ValueError("Decoded input identities differ across candidates or resume")
        else:
            dump_json(path, proof)


def manifest_identity(manifest):
    return json_hash({key: value for key, value in manifest.items() if key not in ("created_at", "manifest_sha256")})


def build_manifest(video_roots, output=None, decoded_root=None):
    originals = json.loads(FRAME_MANIFEST.read_text())
    by_video = {row["video"]: row for row in originals["scenes"].values()}
    fixture = json.loads(FIXTURE.read_text())
    roots = [local_input(root) for root in video_roots]
    calibration = {"status": "unavailable", "reason": "The mirror has no scene0011_00 calibration video"}
    for root in roots:
        video = root / "scene0011_00.mp4"
        if video.is_file():
            reference, indices, _ = fixture_images(64)
            original = by_video["scene0011_00.mp4"]
            _, _, _, _, hw = dense_tower("scene0011_00")
            try:
                decoded = decode_selected(video, indices, original["total_num_frames"], hw)
                calibration = {**compare_decoded(decoded, reference), "scene": "scene0011_00",
                               "video_sha256": sha256(video), "fixture_sha256": sha256(FIXTURE)}
            except ValueError as exc:
                calibration = {"status": "failed", "reason": str(exc)}
            break
    scenes, missing, proxies = [], [], []
    for path in sorted(TOWER.glob("scannet__*.npz")):
        scene = path.stem.split("__", 1)[1]
        _, _, frames, slots, hw = dense_tower(scene)
        original = by_video[f"{scene}.mp4"]
        if not np.array_equal(frames, original["frame_indices"]):
            raise ValueError("The dense source frame manifest disagrees with the tower")
        entry = {
            "dataset": "scannet", "scene": scene, "dense_indices": frames.tolist(),
            "anchor_slots": slots.tolist(), "source_hw": list(hw), "total_frames": original["total_num_frames"],
            "video": None, "images": None,
        }
        if decoded_root:
            entry["decoded_registry"] = str(local_input(decoded_root) / f"{scene}.json")
        if scene == "scene0011_00" and not any((root / f"{scene}.mp4").is_file() for root in roots):
            if [f["index"] for f in fixture["frames"]] != frames.tolist():
                raise ValueError("Fixture and dense tower ordinals disagree")
            entry["images"] = [{**frame, "path": mapped(frame["path"])} for frame in fixture["frames"]]
            entry["decoded_sha256"] = frame_hashes([f["path"] for f in entry["images"]])
        else:
            import av
            for root in roots:
                candidate = root / f"{scene}.mp4"
                if not candidate.is_file():
                    continue
                if calibration["status"] != "passed":
                    entry["source_gate_reason"] = calibration["reason"]
                    continue
                with av.open(str(candidate)) as container:
                    stream = container.streams.video[0]
                    count = int(stream.frames)
                    if count and count != original["total_num_frames"]:
                        proxies.append({"scene": scene, "path": str(candidate), "frames": count})
                        continue
                    if (stream.height, stream.width) != hw:
                        continue
                entry["video"] = str(candidate)
                entry["video_sha256"] = sha256(candidate)
                if scene == "scene0011_00":
                    entry["decoded_sha256"] = calibration["decoded_sha256"]
                break
        if entry["video"] is None and entry["images"] is None:
            missing.append(scene)
        scenes.append(entry)
    body = {
        "created_at": utc(), "schema": "geometry-bakeoff-native64-v1", "scenes": scenes,
        "missing_native_inputs": missing, "rejected_proxies": proxies,
        "source_manifest_sha256": sha256(FRAME_MANIFEST), "video_roots": list(map(str, roots)),
        "decoder_calibration": calibration,
    }
    body["manifest_sha256"] = json_hash(body)
    if output is not None:
        dump_json(output, body)
    return body


def images_for_entry(entry):
    if entry["images"] is not None:
        paths = []
        for frame in entry["images"]:
            path = local_input(mapped(frame["path"]))
            if sha256(path) != frame["sha256"]:
                raise ValueError("Input image digest differs")
            paths.append(path)
        images = paths
    else:
        if entry["video"] is None:
            raise FileNotFoundError(f"No native video for {entry['scene']}")
        if entry.get("video_sha256") and sha256(entry["video"]) != entry["video_sha256"]:
            raise ValueError("The frozen native video changed after admission")
        images = decode_selected(entry["video"], entry["dense_indices"], entry["total_frames"], entry["source_hw"])
    bind_decoded_frames(entry, frame_hashes(images))
    return images
