import math

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from transformers import AutoProcessor
from transformers.video_utils import VideoMetadata

from .common import MODEL, binding

INPUT_FIELDS = {"question", "options", "frames", "frame_indices", "timestamps", "fps", "total_num_frames"}


def assistant_labels(input_ids, attention_mask, prompt_length, answer_length):
    if input_ids.ndim != 2 or input_ids.shape[0] != 1 or attention_mask.shape != input_ids.shape:
        raise ValueError("The smoke uses one example per microbatch")
    end = prompt_length + answer_length
    if prompt_length < 1 or answer_length < 1 or end > input_ids.shape[1]:
        raise ValueError("A complete prompt and nonempty assistant target are required")
    if not torch.all(attention_mask[:, :end] == 1) or torch.any(attention_mask[:, end:] != 0):
        raise ValueError("Only right padding after the complete assistant target is allowed")
    labels = torch.full_like(input_ids, -100)
    labels[:, prompt_length:end] = input_ids[:, prompt_length:end]
    labels[attention_mask == 0] = -100
    return labels


def prediction_positions(labels):
    if labels.ndim != 2 or labels.shape[0] != 1 or labels[0, 0] != -100:
        raise ValueError("Expected a single assistant-masked causal sequence")
    positions = torch.where(labels[0, 1:] != -100)[0]
    if not positions.numel():
        raise ValueError("The target has no supervised tokens")
    return positions


def assistant_loss(logits, labels, positions):
    targets = labels[:, positions + 1]
    if logits.shape[:2] != targets.shape or torch.any(targets == -100):
        raise ValueError("Selected causal logits do not align with assistant-only labels")
    return F.cross_entropy(logits.reshape(-1, logits.shape[-1]).float(), targets.reshape(-1))


def load_processor():
    processor = AutoProcessor.from_pretrained(MODEL, local_files_only=True, trust_remote_code=False)
    processor.tokenizer.padding_side = "right"
    if processor.tokenizer.pad_token_id is None:
        raise ValueError("Pinned tokenizer must define its padding token")
    return processor


def load_rgb(inputs):
    if set(inputs) != INPUT_FIELDS:
        raise ValueError(f"Student input contains unexpected or missing fields: {set(inputs) ^ INPUT_FIELDS}")
    indices, timestamps, frames = inputs["frame_indices"], inputs["timestamps"], inputs["frames"]
    fps = inputs["fps"]
    if len(frames) != 32 or len(indices) != 32 or len(timestamps) != 32:
        raise ValueError("The smoke requires exactly 32 original RGB frames")
    if not isinstance(fps, (int, float)) or not math.isfinite(fps) or fps <= 0:
        raise ValueError("Original source FPS is required; no inferred 24 FPS fallback")
    if any(type(index) is not int or index < 0 for index in indices) or any(a >= b for a, b in zip(indices, indices[1:])):
        raise ValueError("Frame indices must be original, unique, and increasing")
    if inputs["total_num_frames"] <= indices[-1]:
        raise ValueError("Original frame indices exceed the source frame count")
    if any(not math.isclose(timestamp, index / fps, rel_tol=0, abs_tol=1e-6) for timestamp, index in zip(timestamps, indices)):
        raise ValueError("Source timestamps and original frame indices/FPS disagree")
    images, sizes = [], []
    for frame in frames:
        binding(frame["path"], frame["sha256"])
        with Image.open(frame["path"]) as image:
            if image.mode != "RGB":
                raise ValueError(f"Source is not RGB: {frame['path']}")
            sizes.append(list(image.size))
            images.append(np.asarray(image).copy())
    if len({tuple(size) for size in sizes}) != 1:
        raise ValueError("Video frames have inconsistent original resolutions")
    return np.stack(images), sizes


def encode_arrays(processor, question, options, frames, metadata, target, max_length=16384):
    if not isinstance(question, str) or not isinstance(options, list) or not all(isinstance(option, str) for option in options):
        raise ValueError("Question and options must be unchanged source strings")
    if not target or any(token in target for token in ("<|im_start|>", "<|im_end|>", "<|video_pad|>", "<|image_pad|>")):
        raise ValueError("Target is empty or contains conversation/media control tokens")
    text = question + ("\n" + "\n".join(options) if options else "")
    messages = [{"role": "user", "content": [{"type": "video"}, {"type": "text", "text": text}]}]
    prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    full = processor.apply_chat_template(messages + [{"role": "assistant", "content": target}], tokenize=False, add_generation_prompt=False)
    suffix = target + processor.tokenizer.eos_token
    if full != prompt + suffix + "\n":
        raise ValueError("Pinned chat-template assistant boundary changed")
    plain_prompt = processor.tokenizer.encode(prompt, add_special_tokens=False)
    suffix_ids = processor.tokenizer.encode(suffix, add_special_tokens=False)
    if processor.tokenizer.encode(prompt + suffix, add_special_tokens=False) != plain_prompt + suffix_ids:
        raise ValueError("Tokenizer merges across the assistant boundary; refusing ambiguous masks")
    batch = processor(
        text=[prompt],
        videos=[frames],
        video_metadata=[metadata],
        do_sample_frames=False,
        size={"shortest_edge": 32 * 128 * 128, "longest_edge": 32 * 384 * 384},
        return_tensors="pt",
        return_metadata=True,
    )
    returned_metadata = batch.pop("video_metadata", None)
    if returned_metadata is not None:
        observed = returned_metadata[0]
        if list(observed.frames_indices) != list(metadata.frames_indices) or observed.fps != metadata.fps:
            raise ValueError("Processor resampled frames or changed original timing")
    grid = batch["video_grid_thw"]
    if grid.shape != (1, 3) or int(grid[0, 0]) * processor.video_processor.temporal_patch_size != 32:
        raise ValueError("Processor changed the 32-frame temporal grid")
    prompt_length = batch["input_ids"].shape[1]
    suffix_tensor = torch.tensor([suffix_ids], dtype=torch.long)
    input_ids = torch.cat((batch["input_ids"], suffix_tensor), dim=1)
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
    if int((batch["labels"] != -100).sum()) != len(suffix_ids) or suffix_ids[-1] != processor.tokenizer.eos_token_id:
        raise ValueError("Assistant supervision omitted content or the end-of-turn token")
    allowed = {"input_ids", "attention_mask", "mm_token_type_ids", "pixel_values_videos", "video_grid_thw", "labels"}
    if set(batch) - allowed:
        raise ValueError(f"Unexpected processor fields: {set(batch) - allowed}")
    timestamps = [index / metadata.fps for index in metadata.frames_indices]
    patch_timestamps = [(timestamps[i] + timestamps[i + 1]) / 2 for i in range(0, 32, 2)]
    decoded_prompt = processor.tokenizer.decode(batch["input_ids"][0, :prompt_length], skip_special_tokens=False)
    if any(f"<{timestamp:.1f} seconds>" not in decoded_prompt for timestamp in patch_timestamps):
        raise ValueError("Original temporal-patch timestamps are absent from the model prompt")
    return dict(batch), {
        "frame_count": 32,
        "original_frame_indices": list(metadata.frames_indices),
        "original_timestamps_seconds": timestamps,
        "fps": metadata.fps,
        "temporal_patch_timestamps_seconds": patch_timestamps,
        "processor_timestamp_precision_seconds": 0.1,
        "do_sample_frames": False,
        "video_grid_thw": grid.tolist(),
        "processed_height_width": [int(grid[0, 1]) * 16, int(grid[0, 2]) * 16],
        "visual_tokens": visual_tokens,
        "prompt_tokens": prompt_length,
        "assistant_tokens_including_eos": len(suffix_ids),
        "padding_tokens": padding,
        "sequence_tokens": padded_length,
        "assistant_only_mask_verified": True,
        "target_truncated": False,
    }


def encode_row(processor, row):
    inputs = row["student_input"]
    frames, sizes = load_rgb(inputs)
    metadata = VideoMetadata(
        total_num_frames=inputs["total_num_frames"], fps=inputs["fps"],
        frames_indices=list(inputs["frame_indices"]), width=sizes[0][0], height=sizes[0][1],
    )
    batch, audit = encode_arrays(processor, inputs["question"], inputs["options"], frames, metadata, row["target"])
    return batch, {"qid": row["qid"], "original_width_height_per_frame": sizes, **audit}
