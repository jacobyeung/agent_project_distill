import math
from pathlib import Path

from .clean_source import require
from .common import digest_json


def finite_positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def decode_selected(path, fps, count, indices):
    import av

    selected = {}
    with av.open(str(path), mode="r") as container:
        require(len(container.streams.video) == 1, "Expected one authenticated video stream")
        stream = container.streams.video[0]
        require(stream.average_rate is not None and math.isclose(float(stream.average_rate), fps, rel_tol=0, abs_tol=1e-8), "Original source FPS mismatch")
        require(stream.frames in (0, count), "Original source frame-count mismatch")
        dimensions = [stream.width, stream.height]
        decoded = 0
        for index, frame in enumerate(container.decode(stream)):
            require(frame.pts is not None and frame.time_base is not None, "Video lacks native presentation timestamps")
            timestamp = float(frame.pts * frame.time_base)
            tolerance = max(1e-6, float(frame.time_base) / 2 + 1e-9)
            require(math.isclose(timestamp, index / fps, rel_tol=0, abs_tol=tolerance), "Original video timestamps are not zero-origin constant-rate ordinals")
            require([frame.width, frame.height] == dimensions, "Video dimensions changed during decoding")
            if index in indices:
                selected[index] = (frame.to_ndarray(format="rgb24"), timestamp)
            decoded += 1
        require(decoded == count and set(selected) == set(indices), "Incomplete original video/frame census")
    return dimensions, selected


def validate_media(store, row, episode_receipt, scene):
    require(scene.get("schema") == "r1313-scene-assets-v1" and scene.get("round") == 1313, "Wrong scene receipt schema")
    physical_scene = row["dataset"] + "__" + row["scene_name"]
    require((scene.get("dataset"), scene.get("scene_name"), scene.get("runtime_scene_id")) ==
            (row["dataset"], row["scene_name"], physical_scene), "Cross-scene receipt identity mismatch")
    frames, video = scene["frames"], scene["video"]
    require(scene.get("image_count") == 32 and len(frames) == 32
            and episode_receipt.get("student_inputs", {}).get("frames") == frames, "All 32 trace frames must equal the scene receipt")
    require([p["stem"] for p in frames] == scene.get("selected_frames"), "Selected frame identities disagree")
    fps, count = video.get("fps"), video.get("decoded_frame_count")
    require(finite_positive(fps) and type(count) is int and count >= 32 and video.get("timestamp_basis") == "ordinal/fps", "Invalid original video timing contract")
    require(tuple(Path(video["path"]).parts[-2:]) == tuple(Path(row["video"]).parts), "Source video does not identify the question's physical scene")
    indices = [p["ordinal"] for p in frames]
    require(all(type(i) is int and 0 <= i < count for i in indices) and indices == sorted(set(indices)), "Original frame indices are duplicated, reordered, or outside the source video")
    for frame in frames:
        require(frame["stem"] == f"frame_{frame['ordinal']:06d}" and Path(frame["path"]).stem == frame["stem"], "Frame name does not encode its original index")
        timestamp = frame.get("timestamp_sec")
        require(type(timestamp) in (int, float) and math.isfinite(timestamp)
                and math.isclose(timestamp, frame["ordinal"] / fps, rel_tol=0, abs_tol=1e-6), "Frame timestamp differs from original index/FPS")
    cache_key = digest_json({"scene": scene, "video_identity": row["video"]})
    if cache_key in store.media_cache:
        return store.media_cache[cache_key]
    bindings = {"video": store.reference(video, "source_video"),
                "frames": [store.reference(frame, "source_RGB") for frame in frames],
                "alignment": store.reference(scene["alignment"], "frame_alignment"),
                "source_provenance": store.reference(scene["source_provenance"], "source_provenance")}
    provenance = store.json(bindings["source_provenance"])
    alignment = store.json(bindings["alignment"])
    source_frames = None
    if provenance is not None:
        require(provenance.get("schema") == "r1313-source-provenance-v1" and provenance.get("dataset") == row["dataset"]
                and provenance.get("source_scene_id") == row["scene_name"], "Physical scene/source provenance mismatch")
        bindings["source_frames_receipt"] = store.reference(provenance["source_frames_receipt"], "source_frames_receipt")
        source_frames = store.json(bindings["source_frames_receipt"])
        raw_sources = provenance.get("raw_sources", {})
        require("iphone/rgb.mkv" in raw_sources, "An authenticated raw-source video adapter is required for this corpus")
        bindings["raw_video"] = store.reference(raw_sources["iphone/rgb.mkv"], "original_camera_video")
        if source_frames is not None:
            require(source_frames.get("frames") == frames and source_frames.get("video") == video
                    and source_frames.get("selected_frames") == scene["selected_frames"], "Source provenance/frame receipt disagrees with selected RGB/video")
    if alignment is not None:
        require(alignment.get("schema") == "r1313-official-alignment-v1" and alignment.get("validated_slots") == 32
                and alignment.get("pose_field") == "aligned_pose" and alignment.get("estimated_geometry_used") is False,
                "Missing complete official frame alignment")
        align_rows = alignment.get("frames", [])
        require(len(align_rows) == 32, "Alignment must cover all 32 source frames")
        for slot, (frame, aligned) in enumerate(zip(frames, align_rows), 1):
            require((aligned.get("slot_1based"), aligned.get("ordinal"), aligned.get("stem"), aligned.get("selected_rgb_sha256")) ==
                    (slot, frame["ordinal"], frame["stem"], frame["sha256"]), "Frame alignment identity/hash mismatch")
            require(aligned.get("timestamp_sec") == frame["timestamp_sec"] and aligned.get("selected_png_matches_vsi_decode") is True,
                    "Source frame lacks a pixel/timestamp association")
            require(aligned.get("vsi_canvas_wh") == aligned.get("target_canvas_wh"), "Undeclared frame resizing/cropping")
    references = [value for key, value in bindings.items() if key != "frames"] + bindings["frames"]
    result = {"status": "requires_source_media", "pixels_verified": False, "physical_scene": physical_scene,
              "frame_path_discrepancy": any(physical_scene not in Path(frame["path"]).parts for frame in frames),
              "frame_indices": indices, "timestamps": [frame["timestamp_sec"] for frame in frames],
              "fps": fps, "total_num_frames": count, "bindings": bindings,
              "required_check": "Decode every selected RGB from authenticated VSI video; verify raw-source video alignment, all ordinals, dimensions, FPS and native timestamps"}
    if provenance is None or alignment is None or source_frames is None or any(p["availability"] != "verified" for p in references):
        return result
    import numpy as np
    from PIL import Image

    dimensions, selected = decode_selected(bindings["video"]["path"], fps, count, indices)
    raw_dimensions, original = decode_selected(bindings["raw_video"]["path"], fps, count, indices)
    proofs = []
    for frame, asset, aligned in zip(frames, bindings["frames"], alignment["frames"]):
        with Image.open(asset["path"]) as image:
            require(image.mode == "RGB" and list(image.size) == dimensions, "Source RGB format/dimensions differ from video")
            pixels = np.asarray(image)
        decoded, timestamp = selected[frame["ordinal"]]
        require(np.array_equal(pixels, decoded), "Cross-scene frame mismatch: selected PNG pixels differ from the authenticated source video")
        require(dimensions == aligned["vsi_canvas_wh"] and raw_dimensions == aligned["raw_source_canvas_wh"], "Decoded video dimensions differ from official provenance")
        original_pixels = original[frame["ordinal"]][0]
        resized = np.asarray(Image.fromarray(original_pixels).resize(tuple(dimensions), Image.Resampling.BOX))
        if np.array_equal(resized, decoded):
            correlation = 1.0
        else:
            correlation = float(np.corrcoef(resized.reshape(-1), decoded.reshape(-1))[0, 1])
        require(math.isfinite(correlation) and correlation >= 0.99, "Raw physical-scene video does not support selected RGB pixels")
        proofs.append({"ordinal": frame["ordinal"], "png_sha256": asset["sha256"], "timestamp_sec": timestamp,
                       "width_height": dimensions, "exact_vsi_pixels": True, "raw_source_correlation": correlation})
    result.update(status="verified", pixels_verified=True, source_width_height=dimensions,
                  raw_source_width_height=raw_dimensions, frame_proofs=proofs,
                  path_discrepancy_resolved_by_pixels=result["frame_path_discrepancy"])
    store.media_cache[cache_key] = result
    return result
