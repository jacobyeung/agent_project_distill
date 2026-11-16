import math
DEFAULT_PIXELS = (128*128, 384*384)
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
