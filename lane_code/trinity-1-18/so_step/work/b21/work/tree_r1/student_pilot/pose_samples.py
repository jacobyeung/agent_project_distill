"""Cambrian-P pose-only samples at the rows' 32 frames: sampling, GT targets, augmentation and encoding.

A pose-only sample (category camera_pose_only) shows N of a scene's 32 sampled frames and trains only the heads: the
camera head (pose, gravity, scale) and, under Cambrian-P routing, the point-depth head at the groups whose frame has
bank depth (compact_label_bank.sample_depth); its language-model loss is zero and it leaves the LM row mean (ddp_core
lm_scale).
Cambrian-P (arXiv 2605.22819, Sec. 3.3) samples N frames with CUT3R's two modes, 50/50:
  - temporal: a contiguous run at a random stride s in 1..floor(L / N), its order flipped with probability 0.5;
  - collection: N frames uniformly at random without replacement, in a random permutation;
and applies image-level augmentation. Here L = 32 (the row's frames) and N is even, uniform over {8, 16, 24, 32}
(L/frames64_20261030/PLAN.md section 3). Only photometric augmentation is applied (colour jitter 0.3/0.3/0.3/0.05,
Gaussian blur p 0.1, grayscale p 0.05): rescaling and rotation would change the pose targets.

Targets follow the trainer's convention: sample position 0 is the origin; temporal group g (positions 2g, 2g+1)
targets position 2g + 1 with the VGGT encoding of inv(C_{2g+1}) @ C_0; gravity is world up in the origin camera;
the trajectory scale is the mean step between consecutive targets. A sample has G = N / 2 groups, padded to 16
slots (mask False); the camera head masks the padded tokens. Poses come from the scene's metric GT calibration.
"""
import hashlib
import json
import math
import random

import numpy as np

from .camera_targets import GROUPS, FRAMES, quaternion_xyzw, rigid, trajectory_scale

CATEGORY = "camera_pose_only"
SCHEMA = "pose-only-sample-v1"
SAMPLE_SIZES = (8, 16, 24, 32)
MODES = ("temporal", "collection")
AUGMENT = {"brightness": 0.3, "contrast": 0.3, "saturation": 0.3, "hue": 0.05, "blur_p": 0.1, "grayscale_p": 0.05,
           "blur_kernel": 5, "blur_sigma": [0.1, 2.0]}
PROMPT = "Describe this scene."
TARGET = "<think>\n\n</think>\n\n"
# Training pixel budget per frame (the RGB32 contract: shortest 32 x 128^2, longest 32 x 384^2 over 32 frames).
DEFAULT_PIXELS = (128 * 128, 384 * 384)


def sample_order(rng, frames=FRAMES, sizes=SAMPLE_SIZES):
    """(mode, N, positions into the scene's frames, stride, reversed) for one pose-only sample."""
    size = rng.choice(sizes)
    if rng.random() < 0.5:
        stride = rng.randint(1, frames // size)
        start = rng.randint(0, frames - stride * (size - 1) - 1)
        order = [start + stride * k for k in range(size)]
        flipped = rng.random() < 0.5
        return "temporal", size, (order[::-1] if flipped else order), stride, flipped
    order = rng.sample(range(frames), size)
    return "collection", size, order, None, False


def encode_sample(c2w, intrinsics, raster_hw, order, world_up=(0.0, 0.0, 1.0), max_groups=GROUPS, all_frames=False):
    """Camera [max(16,N/2),9], mask, mean anchor step and origin-camera gravity, with opt-in long rows."""
    c2w, intrinsics = np.asarray(c2w, dtype=np.float64), np.asarray(intrinsics, dtype=np.float64)
    order = list(order)
    if (type(max_groups) is not int or not (GROUPS <= max_groups <= 48 or max_groups == 64) or len(order) % 2
            or not 2 <= len(order) <= 2 * max_groups or len(set(order)) != len(order)):
        raise ValueError("A pose-only sample needs distinct even frames within max_groups")
    if c2w.shape[1:] != (4, 4) or intrinsics.shape[1:] != (3, 3) or len(c2w) != len(intrinsics):
        raise ValueError("Pose-only targets need 4x4 camera-to-world poses and 3x3 intrinsics per frame")
    if all_frames:
        from .camera_targets import encode_cameras, encode_gravity
        if len(order) not in (32,64) or len(order)>max_groups:
            raise ValueError('All-frame samples require a supported pinned frame count')
        camera, mask, scale = encode_cameras(c2w[order], intrinsics[order], raster_hw, all_frames=True)
        gravity, valid = encode_gravity(c2w[order], world_up)
        if not valid or mask.sum() < 2:
            raise ValueError('All-frame sample has invalid origin or poses')
        return camera, mask, scale, gravity
    height, width = raster_hw
    groups = max(GROUPS, len(order) // 2)
    camera, mask = np.zeros((groups, 9)), np.zeros(groups, bool)
    origin = c2w[order[0]]
    if not rigid(origin):
        raise ValueError("The sample's origin frame has no rigid metric pose")
    for g in range(len(order) // 2):
        frame = order[2 * g + 1]
        fx, fy = intrinsics[frame, 0, 0], intrinsics[frame, 1, 1]
        if not (rigid(c2w[frame]) and np.isfinite(intrinsics[frame]).all() and fx > 0 and fy > 0):
            continue
        relative = np.linalg.inv(c2w[frame]) @ origin
        camera[g, :3] = relative[:3, 3]
        camera[g, 3:7] = quaternion_xyzw(relative[:3, :3])
        camera[g, 7] = 2 * math.atan(height / (2 * fy))
        camera[g, 8] = 2 * math.atan(width / (2 * fx))
        mask[g] = True
    if mask.sum() < 2:
        raise ValueError("A pose-only sample needs at least two supervised groups")
    up = origin[:3, :3].T @ np.asarray(world_up, dtype=np.float64)
    gravity = up / np.linalg.norm(up)
    return camera, mask, trajectory_scale(camera, mask), gravity


def sample_qid(scene_token, index, seed):
    return "p" + hashlib.sha256(f"pose-only {scene_token} {index} {seed}".encode()).hexdigest()[:24]


def build_row(source_row, poses, index, seed, world_up=(0.0, 0.0, 1.0)):
    """One pose-only row from a 32-frame QA row of the scene and the scene's 32 metric poses.

    poses: {"c2w": [32, 4, 4], "intrinsics": [32, 3, 3] on the RGB raster, "raster_hw": [H, W]}."""
    rng = random.Random(f"{seed}:{source_row['scene']}:{index}")
    inputs = source_row["student_input"]
    if len(inputs["frames"]) != FRAMES:
        raise ValueError("Pose-only samples are drawn from a 32-frame row")
    mode, size, order, stride, flipped = sample_order(rng)
    camera, mask, scale, gravity = encode_sample(poses["c2w"], poses["intrinsics"], poses["raster_hw"], order, world_up)
    augment_seed = rng.randrange(2**31)
    student_input = {"question": PROMPT, "options": [], "frames": [inputs["frames"][k] for k in order],
                     "frame_indices": [inputs["frame_indices"][k] for k in order],
                     "timestamps": [inputs["timestamps"][k] for k in order], "fps": inputs["fps"],
                     "total_num_frames": inputs["total_num_frames"]}
    sample = {"schema": SCHEMA, "mode": mode, "frames": size, "positions": order, "stride": stride, "reversed": flipped,
              "augment": {**AUGMENT, "seed": augment_seed}, "camera": camera.tolist(), "camera_mask": mask.tolist(),
              "trajectory_scale": scale, "gravity": gravity.tolist(), "gravity_mask": True, "metric": True}
    return {"qid": sample_qid(source_row["scene"], index, seed), "dataset": source_row["dataset"],
            "scene": source_row["scene"], "category": CATEGORY, "answer": "", "target": TARGET,
            "student_input": student_input, "pose_sample": sample}


def check_sample(row, max_groups=GROUPS):
    """The inline record of a pose-only row, validated; returns the camera record the head consumes."""
    from .camera_targets import check_record
    sample = row.get("pose_sample")
    if row.get("category") != CATEGORY or not isinstance(sample, dict) or sample.get("schema") != SCHEMA:
        raise ValueError("A pose-only row needs its pose-only-sample-v1 record")
    frames = len(row["student_input"]["frames"])
    if (sample["frames"] != frames or frames not in (*SAMPLE_SIZES, 64, 96)
            or frames > 2 * max_groups or len(sample["positions"]) != frames):
        raise ValueError("Pose-only sample frame count disagrees with its frames")
    all_frames = sample.get('temporal_grouping') == 'fused_pairs_all_frames'
    if all_frames and (frames != 32 or sample.get('anchors') != list(range(1, 33))):
        raise ValueError('All-frame sample contract differs')
    slots = 32 if all_frames else max(GROUPS, frames // 2)
    mask = np.asarray(sample["camera_mask"], dtype=bool)
    if mask[frames if all_frames else frames // 2:].any():
        raise ValueError("Pose-only targets beyond the sample's groups")
    record = {"camera": sample["camera"], "camera_mask": mask, "trajectory_scale": sample["trajectory_scale"],
              "metric": sample["metric"]}
    check_record(record, max_groups)
    if len(sample['camera']) != slots:
        raise ValueError('Pose-only target slots disagree with the frame count')
    gravity = np.asarray(sample["gravity"], dtype=np.float64)
    if gravity.shape != (3,) or not math.isclose(float(np.linalg.norm(gravity)), 1.0, abs_tol=1e-3):
        raise ValueError("Pose-only gravity must be a unit vector")
    return {"camera": sample["camera"], "camera_mask": mask.tolist(), "trajectory_scale": float(sample["trajectory_scale"]),
            "lm_weight": 0.0, "gravity": gravity.tolist(), "gravity_mask": bool(sample["gravity_mask"])}


def augment(arrays, settings):
    """Photometric augmentation, one draw per frame (DUSt3R/CUT3R's per-view colour jitter), seeded by the row."""
    if all(settings.get(key) == 0 for key in ('brightness','contrast','saturation','hue','blur_p','grayscale_p')):
        return np.array(arrays, copy=True)
    import torch
    from torchvision.transforms.v2 import functional as TF

    rng = random.Random(settings["seed"])
    result = []
    for frame in arrays:
        image = torch.from_numpy(np.ascontiguousarray(frame)).permute(2, 0, 1)
        image = TF.adjust_brightness(image, rng.uniform(1 - settings["brightness"], 1 + settings["brightness"]))
        image = TF.adjust_contrast(image, rng.uniform(1 - settings["contrast"], 1 + settings["contrast"]))
        image = TF.adjust_saturation(image, rng.uniform(1 - settings["saturation"], 1 + settings["saturation"]))
        image = TF.adjust_hue(image, rng.uniform(-settings["hue"], settings["hue"]))
        if rng.random() < settings["blur_p"]:
            image = TF.gaussian_blur(image, [settings["blur_kernel"]] * 2, [rng.uniform(*settings["blur_sigma"])] * 2)
        if rng.random() < settings["grayscale_p"]:
            image = TF.rgb_to_grayscale(image, num_output_channels=3)
        result.append(image.permute(1, 2, 0).numpy())
    return np.stack(result)


def load_frames(inputs):
    from .c1_switches import get as performance_switch
    cache_enabled = performance_switch('C1_DECODED_CACHE_MIB') != '0'
    from PIL import Image
    from .r2_frames import verify_frame

    images = []
    for frame in inputs["frames"]:
        if cache_enabled:
            from .c1_decoded_cache import read
            images.append(read(verify_frame(frame), frame['path'], frame['sha256']))
            continue
        with Image.open(verify_frame(frame)) as image:
            if image.mode != "RGB":
                raise ValueError(f"Source is not RGB: {frame['path']}")
            images.append(np.asarray(image).copy())
    if len({image.shape for image in images}) != 1:
        raise ValueError("Pose-only frames have inconsistent resolutions")
    return np.stack(images)


def encode_frames(processor, question, options, arrays, metadata, target, pixels=DEFAULT_PIXELS, max_length=16384):
    """batches.encode_arrays for any even frame count with an explicit per-frame pixel budget.

    The processor's size dict is a budget summed over the frames, so it scales with N: every frame keeps the
    32-frame contract's resolution (no silent resize). With 32 frames and DEFAULT_PIXELS the size dict, tensors
    and audit equal encode_arrays'."""
    import torch
    import torch.nn.functional as F
    from .batches import assistant_labels, training_stop_token, training_text

    count = len(arrays)
    prompt, suffix = training_text(processor, question, options, target)
    plain_prompt = processor.tokenizer.encode(prompt, add_special_tokens=False)
    suffix_ids = processor.tokenizer.encode(suffix, add_special_tokens=False)
    merged_boundary = processor.tokenizer.encode(prompt + suffix, add_special_tokens=False) != plain_prompt + suffix_ids
    if merged_boundary and not (prompt.endswith("<think>\n") and suffix.startswith("\n</think>\n\n")):
        raise ValueError("Tokenizer merges across the assistant boundary; refusing ambiguous masks")
    if processor.tokenizer.decode(plain_prompt + suffix_ids, skip_special_tokens=False) != prompt + suffix:
        raise ValueError("Native generation-prefix continuation changed the assistant text")
    batch = processor(text=[prompt], videos=[arrays], video_metadata=[metadata], do_sample_frames=False,
                      size={"shortest_edge": count * pixels[0], "longest_edge": count * pixels[1]},
                      return_tensors="pt", return_metadata=True)
    returned = batch.pop("video_metadata", None)
    if returned is not None and (list(returned[0].frames_indices) != list(metadata.frames_indices)
                                 or returned[0].fps != metadata.fps):
        raise ValueError("Processor resampled frames or changed original timing")
    grid = batch["video_grid_thw"]
    if grid.shape != (1, 3) or int(grid[0, 0]) * processor.video_processor.temporal_patch_size != count:
        raise ValueError(f"Processor changed the {count}-frame temporal grid")
    prompt_length = batch["input_ids"].shape[1]
    input_ids = torch.cat((batch["input_ids"], torch.tensor([suffix_ids], dtype=torch.long)), dim=1)
    length = input_ids.shape[1]
    padded_length = math.ceil(length / 8) * 8
    if padded_length > max_length:
        raise ValueError(f"Complete example requires {padded_length} tokens; truncation is forbidden")
    padding = padded_length - length
    batch["input_ids"] = F.pad(input_ids, (0, padding), value=processor.tokenizer.pad_token_id)
    batch["attention_mask"] = F.pad(torch.ones_like(input_ids), (0, padding), value=0)
    if "mm_token_type_ids" in batch:
        batch["mm_token_type_ids"] = F.pad(batch["mm_token_type_ids"], (0, len(suffix_ids) + padding), value=0)
    batch["labels"] = assistant_labels(batch["input_ids"], batch["attention_mask"], prompt_length, len(suffix_ids))
    visual_tokens = int((batch["input_ids"] == processor.video_token_id).sum())
    if visual_tokens != int(grid.prod()) // processor.video_processor.merge_size**2:
        raise ValueError("Visual placeholder count and pixel grid disagree")
    stop_id = training_stop_token(processor)[1]
    ending = [processor.tokenizer.eos_token_id] + ([stop_id] if stop_id != processor.tokenizer.eos_token_id else [])
    if int((batch["labels"] != -100).sum()) != len(suffix_ids) or suffix_ids[-len(ending):] != ending:
        raise ValueError("Assistant supervision omitted content or a required stop token")
    timestamps = [index / metadata.fps for index in metadata.frames_indices]
    patch_timestamps = [(timestamps[i] + timestamps[i + 1]) / 2 for i in range(0, count, 2)]
    decoded_prompt = processor.tokenizer.decode(batch["input_ids"][0, :prompt_length], skip_special_tokens=False)
    if any(f"<{timestamp:.1f} seconds>" not in decoded_prompt for timestamp in patch_timestamps):
        raise ValueError("Original temporal-patch timestamps are absent from the model prompt")
    return dict(batch), {
        "frame_count": count, "original_frame_indices": list(metadata.frames_indices),
        "original_timestamps_seconds": timestamps, "fps": metadata.fps,
        "temporal_patch_timestamps_seconds": patch_timestamps, "processor_timestamp_precision_seconds": 0.1,
        "do_sample_frames": False, "video_grid_thw": grid.tolist(),
        "processed_height_width": [int(grid[0, 1]) * 16, int(grid[0, 2]) * 16], "visual_tokens": visual_tokens,
        "prompt_tokens": prompt_length, "assistant_tokens_including_eos": len(suffix_ids), "padding_tokens": padding,
        "sequence_tokens": padded_length, "assistant_only_mask_verified": True, "target_truncated": False}


def encode_pose_row(processor, row, pixels=DEFAULT_PIXELS, max_length=16384):
    from transformers.video_utils import VideoMetadata

    capacity = 32 if row['pose_sample'].get('temporal_grouping') == 'fused_pairs_all_frames' else max(
        GROUPS, len(row['student_input']['frames']) // 2)
    check_sample(row, max_groups=capacity)
    inputs = row["student_input"]
    arrays = augment(load_frames(inputs), row["pose_sample"]["augment"])
    metadata = VideoMetadata(total_num_frames=inputs["total_num_frames"], fps=inputs["fps"],
                             frames_indices=list(inputs["frame_indices"]), width=arrays.shape[2], height=arrays.shape[1])
    batch, audit = encode_frames(processor, inputs["question"], inputs["options"], arrays, metadata, row["target"],
                                 pixels, max_length)
    return batch, {"qid": row["qid"], "pose_only_sample": True, "augment_seed": row["pose_sample"]["augment"]["seed"], **audit}


FRAME_COUNTS = (32, 64, 96)
DEFAULT_FRAMES = {"count": 32, "pixels_per_frame": list(DEFAULT_PIXELS)}
_configured = {"frames": None}


def normalize_frames(value):
    """The training config's frame setting: frame count and per-frame pixel budget [min, max].

    64 frames at 224x288 (L/frames64_20261030/PLAN.md, the ~1x-cost cell) is {"count": 64, "pixels_per_frame":
    [16384, 73728]}; the processor budget is the per-frame budget times the frame count, so no frame is resized
    silently. Absent means the 32-frame RGB contract."""
    if (not isinstance(value, dict) or set(value) != {"count", "pixels_per_frame"} or value["count"] not in FRAME_COUNTS
            or not isinstance(value["pixels_per_frame"], list) or len(value["pixels_per_frame"]) != 2
            or any(type(v) is not int or v < 32 * 32 for v in value["pixels_per_frame"])
            or value["pixels_per_frame"][0] > value["pixels_per_frame"][1]):
        raise ValueError("frames must be {count: 32 | 64 | 96, pixels_per_frame: [min, max] integer pixels}")
    return {"count": value["count"], "pixels_per_frame": list(value["pixels_per_frame"])}


def configure_frames(frames):
    """Set this process's frame setting (train() calls it once from the frozen settings)."""
    _configured["frames"] = None if frames is None else normalize_frames(frames)


def load_video(inputs, count):
    """Original frames of a row in its own order (strictly increasing for question rows)."""
    if len(inputs["frames"]) != count or len(inputs["frame_indices"]) != count or len(inputs["timestamps"]) != count:
        raise ValueError(f"The frame setting requires exactly {count} original RGB frames")
    indices = inputs["frame_indices"]
    if any(type(index) is not int or index < 0 for index in indices) or any(a >= b for a, b in zip(indices, indices[1:])):
        raise ValueError("Frame indices must be original, unique, and increasing")
    return load_frames(inputs)


def encode_row(processor, row, frames=None):
    """The trainer's and admission's row encoder. Pose-only samples use their own N frames; question rows use
    the frame setting; without a setting (or with the 32-frame default) every row encodes exactly as before."""
    frames = _configured["frames"] if frames is None else normalize_frames(frames)
    pixels = tuple(frames["pixels_per_frame"]) if frames is not None else DEFAULT_PIXELS
    if (row.get("category") == CATEGORY and "pose_sample" in row) or not (frames is None or frames == DEFAULT_FRAMES):
        from .diagnostic_data import TRAINING
    if row.get("category") == CATEGORY and "pose_sample" in row:
        if frames is not None and row["pose_sample"]["frames"] > frames["count"]:
            raise ValueError("A pose-only sample has more frames than the frame setting")
        return encode_pose_row(processor, row, pixels, max_length=TRAINING["max_sequence_tokens"])
    if frames is None or frames == DEFAULT_FRAMES:
        from .diagnostic_data import encode_training
        return encode_training(processor, row)
    from transformers.video_utils import VideoMetadata
    inputs = row["student_input"]
    arrays = load_video(inputs, frames["count"])
    metadata = VideoMetadata(total_num_frames=inputs["total_num_frames"], fps=inputs["fps"],
                             frames_indices=list(inputs["frame_indices"]), width=arrays.shape[2], height=arrays.shape[1])
    batch, audit = encode_frames(processor, inputs["question"], inputs["options"] or [], arrays, metadata, row["target"],
                                 pixels, TRAINING["max_sequence_tokens"])
    return batch, {"qid": row["qid"], "original_width_height_per_frame": [[arrays.shape[2], arrays.shape[1]]] * len(arrays),
                   "null_options_normalized_to_empty": inputs["options"] is None, **audit}


def manifest_line(row):
    return json.dumps(row, sort_keys=True, separators=(",", ":"))
