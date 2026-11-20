"""Per-frame carrier placement and deterministic, scene-audited C1 streams."""
from contextlib import contextmanager
import json
import math
import random
import sqlite3
from pathlib import Path

import numpy as np
import torch

from .camera_targets import carrier_id, VIDEO_TOKEN
from .decoupled_v import target_tensors
from .decoupled_v_run import READOUT_TARGET
from .p3_provenance import file_pin, load, pinned, write

STREAM_SEGMENTS = ('pointing_coord', 'pointing_format', 'pointing_null', 'vqa_answer', 'vqa_trace')


def pointing_token_weights(labels, decode, decision=5.0, row_mean=2.0):
    """Per-token loss weights for one pointing row's shifted labels (config pointing_weights).

    The decision token, the first supervised token after '"point_2d":' (the '[' of a point or the
    null), weighs `decision`; every other supervised token weighs 1; unsupervised tokens weigh 0.
    Supervised weights are then scaled so their mean equals `row_mean`."""
    flat = labels.reshape(-1)
    weights = torch.zeros(flat.shape, dtype=torch.float32)
    positions = (flat != -100).nonzero().flatten().tolist()
    text, chosen = '', None
    for i in positions:
        piece = decode(int(flat[i]))
        if chosen is None and '"point_2d":' in text and piece.strip():
            chosen = i
        text += piece
        weights[i] = 1.0
    if chosen is not None:
        weights[chosen] = float(decision)
    if positions:
        weights *= row_mean * len(positions) / float(weights.sum())
    return weights.reshape(labels.shape)


def segment_tags(labels, stream, decode):
    """Per-token logging tags (index into STREAM_SEGMENTS; -1 unsupervised) for one row's labels.

    Pointing: coordinate digits vs format tokens on visible rows; every token of a row without
    digits (the `null` target) is pointing_null. VQA: tokens after `</think>` are the answer,
    the rest the trace. Logging only: the loss never reads these tags.
    """
    flat = labels.reshape(-1)
    tags = torch.full_like(flat, -1)
    positions = (flat != -100).nonzero().flatten().tolist()
    texts = {i: decode(int(flat[i])) for i in positions}
    if stream == 'pointing':
        digits = {i for i, text in texts.items() if text.strip().isdigit()}
        for i in positions:
            tags[i] = STREAM_SEGMENTS.index('pointing_coord' if i in digits else
                                            'pointing_format' if digits else 'pointing_null')
    elif stream == 'vqa':
        closing = next((i for i in positions if '</think>' in texts[i]), None)
        for i in positions:
            tags[i] = STREAM_SEGMENTS.index('vqa_answer' if closing is not None and i > closing else 'vqa_trace')
    return tags.reshape(labels.shape)


C1_A = 'append_after_temporal_group_video_tokens_v1'
C1_B = 'append_all_after_video_frame_embeddings_v1'
C1_C = 'append_after_temporal_group_video_tokens_bidirectional_v1'
PLACEMENTS = (C1_A, C1_B, C1_C)


def layout_settings(cfg):
    layout, gap = cfg.get('frame_layout', 'spread'), cfg.get('frame_pair_gap_seconds')
    if layout not in ('spread', 'duplicate', 'paired'):
        raise ValueError('frame_layout must be spread, duplicate or paired')
    if layout == 'paired' and (type(gap) not in (int, float) or not math.isfinite(gap) or gap <= 0):
        raise ValueError('paired frame_layout requires positive frame_pair_gap_seconds')
    if layout != 'paired' and gap is not None:
        raise ValueError('frame_pair_gap_seconds is only valid for paired frame_layout')
    return layout, gap


def nested_indices(anchors, count=64):
    """Nested frame set: the anchors plus repeated bisection of the largest gap (ties to the earliest
    index, midpoint (a+b)//2), as the frames lane's 64-frame reads. Returns (indices, anchor_slots)."""
    indices = sorted(anchors)
    if len(set(indices)) != len(indices) or any(type(k) is not int or k < 0 for k in indices):
        raise ValueError('Nested anchors must be distinct non-negative integers')
    while len(indices) < count:
        slot = max(range(len(indices) - 1), key=lambda i: indices[i + 1] - indices[i])
        a, b = indices[slot:slot + 2]
        if b - a < 2:
            raise ValueError('Nested bisection cannot reach the requested frame count')
        indices.insert(slot + 1, (a + b) // 2)
    anchor_set = set(anchors)
    return indices, [i for i, k in enumerate(indices) if k in anchor_set]


def anchor_slots(inputs, layout='duplicate'):
    """Nested rows (more than 32 viewpoints, duplicate layout only) name the 32 anchor viewpoints that keep
    carriers: student_input.anchor_slots, strictly increasing 0-based viewpoint positions."""
    slots = inputs.get('anchor_slots')
    if slots is None:
        return None
    count = len(inputs['frames'])
    if (layout != 'duplicate' or not isinstance(slots, list) or not 1 <= len(slots) <= 32 or count > 64
            or any(type(k) is not int for k in slots) or slots != sorted(set(slots))
            or slots[0] < 0 or slots[-1] >= count):
        raise ValueError('anchor_slots needs the duplicate layout and at most 32 increasing viewpoint positions')
    return slots


def layout_inputs(row, layout='spread', gap=None, verify_partners=False, frame_count=32):
    """Keep target slots in sampled-viewpoint order; expand only the RGB input.

    Paired rows supply student_input.partner_frames: one {path, sha256,
    recording_id, frame_index, timestamp} per anchor, in the same recording_id.
    """
    layout_settings(dict(frame_layout=layout, frame_pair_gap_seconds=gap))
    inputs = row['student_input']
    if layout == 'spread':
        return inputs
    count = len(inputs['frames'])
    limit = 64 if anchor_slots(inputs, layout) is not None else frame_count
    if not 1 <= count <= limit or any(len(inputs[k]) != count for k in ('frame_indices', 'timestamps')):
        raise ValueError('C1 layouts require at most 32 aligned sampled viewpoints (64 with anchor_slots)')
    fps, total = inputs['fps'], inputs['total_num_frames']
    if not math.isfinite(fps) or fps <= 0:
        raise ValueError('C1 layouts require a positive source fps')
    partners = inputs.get('partner_frames', [])
    if layout == 'paired' and (len(partners) != count or not inputs.get('recording_id')):
        raise ValueError('paired frame_layout requires prepared partner_frames and recording_id for every viewpoint')
    frames, indices, timestamps = [], [], []
    for i, frame in enumerate(inputs['frames']):
        index, timestamp = inputs['frame_indices'][i], inputs['timestamps'][i]
        if type(index) is not int or not 0 <= index < total or not math.isclose(timestamp, index / fps, abs_tol=1e-6):
            raise ValueError('C1 layouts require true source indices/timestamps')
        partner, partner_index, partner_time = frame, index, timestamp
        if layout == 'paired':
            partner = partners[i]
            partner_index, partner_time = partner.get('frame_index'), partner.get('timestamp')
            if (partner.get('recording_id') != inputs['recording_id']
                    or type(partner_index) is not int or not index < partner_index < total
                    or type(partner_time) not in (int, float)
                    or not math.isclose(partner_time, partner_index / fps, abs_tol=1e-6)
                    or not math.isclose(partner_time - timestamp, gap, rel_tol=0, abs_tol=1e-6)
                    or not partner.get('path') or not partner.get('sha256')):
                raise ValueError('paired partner must be pinned in the same recording at the configured gap')
            if verify_partners:
                pinned({k: partner[k] for k in ('path', 'sha256')})
        frames.extend((frame, partner))
        indices.extend((index, partner_index))
        timestamps.extend((timestamp, partner_time))
    return {**inputs, 'frames': frames, 'frame_indices': indices, 'timestamps': timestamps}


def encode_layout_row(processor, row, layout, gap, native_g3t=False, gf1=None):
    from transformers.video_utils import VideoMetadata
    from .pose_samples import CATEGORY, DEFAULT_PIXELS, augment, check_sample, encode_frames, load_frames
    frame_count = getattr(getattr(processor, 'tokenizer', None), '_c1_frame_count', 32)
    if hasattr(processor, '_b7_layout'):
        from .r0_exclusion import reserve
        reserve().check(row, 'dense_frames')
        if len(row['student_input']['frames']) != frame_count:
            raise ValueError('row_training_frame_count_mismatch')
    inputs = layout_inputs(row, layout, gap, frame_count=frame_count)
    is_pose = row.get('category') == CATEGORY and 'pose_sample' in row
    if is_pose:
        check_sample(row, max_groups=frame_count)
    # Duplicate after augmentation so each temporal patch contains identical bytes.
    original = row['student_input'] if layout == 'duplicate' else inputs
    geometry = {}
    bank_audit = special = None
    if gf1:
        from .gf1 import dense_inputs, ClipCache
        from .g3t_online import native_square_518
        dense, indices = dense_inputs(row, gf1)
        if gf1.get('cached_bank') or 'geometry_bank_donor' in row['student_input']:
            # Opt-in cached bank or shuffled-bank read; pose rows and uncached clips stay online.
            from .gf1_cache import row_bank
            special, bank_audit = row_bank(row, gf1, dense, indices, is_pose)
    if special is not None:
        geometry, arrays = special
    elif gf1:
        arrays = load_frames(dense)
        if is_pose:
            # Keep the checkpoint's sparse-frame jitter draws unchanged, and give
            # the tower those exact augmented RGB bytes at the nested slots.
            sparse_arrays = augment(arrays[indices], row['pose_sample']['augment'])
            arrays = augment(arrays, row['pose_sample']['augment'])
            arrays[indices] = sparse_arrays
        images, coords = native_square_518(arrays, expected_frames=gf1['dense_frames'])
        geometry = dict(aux_gf1_cache=ClipCache(), aux_g3t_images=images[None], aux_g3t_coords=coords[None],
                        aux_gf1_lm_indices=torch.tensor([indices], dtype=torch.long))
        arrays = arrays[indices]
    else:
        arrays = load_frames(original)
        if is_pose:
            arrays = augment(arrays, row['pose_sample']['augment'])
    if native_g3t:
        from .g3t_online import native_square_518
        images, coords = native_square_518(arrays[::2] if layout == 'paired' else arrays)
        geometry = dict(aux_g3t_images=images[None], aux_g3t_coords=coords[None])
    if layout == 'duplicate':
        arrays = np.repeat(arrays, 2, axis=0)
    metadata = VideoMetadata(total_num_frames=inputs['total_num_frames'], fps=inputs['fps'],
        frames_indices=inputs['frame_indices'], width=arrays.shape[2], height=arrays.shape[1])
    batch, audit = encode_frames(processor, inputs['question'], inputs.get('options') or [], arrays,
                                 metadata, row['target'], (processor._b7_layout['min_pixels'], processor._b7_layout['max_pixels']) if hasattr(processor,'_b7_layout') else DEFAULT_PIXELS, 16384)
    batch.update(geometry)
    return batch, {**audit, 'frame_layout': layout, 'frame_pair_gap_seconds': gap,
                   'viewpoint_timestamps_seconds': row['student_input']['timestamps'],
                   **({'gf1_bank': bank_audit} if bank_audit is not None else {})}


def insert_frame_markers(batch, tokenizer, frame_layout):
    """Text marker `Frame k: ` (k = viewpoint, 1-based) before each temporal group's
    <|vision_start|>, so prompts that name frames by number need not count groups.
    Duplicate/paired layouts only (one viewpoint per group). Markers are unsupervised text."""
    if frame_layout not in ('duplicate', 'paired'):
        raise ValueError('Frame markers need one viewpoint per temporal group')
    ids = batch['input_ids']
    video = tokenizer.convert_tokens_to_ids(VIDEO_TOKEN)
    start = tokenizer.convert_tokens_to_ids('<|vision_start|>')
    visual = torch.where(ids[0] == video)[0].tolist()
    firsts = [i for n, i in enumerate(visual) if n == 0 or visual[n-1] != i - 1]
    groups = int(batch['video_grid_thw'][0, 0])
    if len(firsts) != groups or any(i == 0 or int(ids[0, i-1]) != start for i in firsts):
        raise ValueError('Frame markers need one <|vision_start|> before each temporal group')
    cuts = [i - 1 for i in firsts]
    markers = [tokenizer.encode(f'Frame {k}: ', add_special_tokens=False) for k in range(1, groups + 1)]
    result = dict(batch)
    for key, fill in dict(input_ids=None, labels=-100, attention_mask=1, mm_token_type_ids=0).items():
        if key not in batch:
            continue
        value, pieces, previous = batch[key], [], 0
        for cut, marker in zip(cuts, markers):
            pieces.append(value[:, previous:cut])
            pieces.append(torch.tensor([marker], dtype=value.dtype, device=value.device) if fill is None
                          else value.new_full((1, len(marker)), fill))
            previous = cut
        pieces.append(value[:, previous:])
        result[key] = torch.cat(pieces, dim=1)
    return result


def insert_frame_carriers(batch, tokenizer, merge_size=2, carrier_placement=C1_A, frame_layout='spread', anchors=None):
    """B appends all carriers after the final video patch in every layout.

    A/C keep two local carriers per fused pair in spread and one per viewpoint
    in duplicate/paired. Each B carrier retains its own frame identity and RoPE.
    Native mRoPE is recomputed on the extended input. Never reuse position_ids.
    A processor with `_c1_frame_markers` set (receipt frame_markers) first inserts
    `Frame k: ` before each group, identically in every stream and evaluator path.
    `anchors` (duplicate layout, up to 64 groups): only those groups carry carriers.
    """
    if getattr(tokenizer, '_c1_frame_markers', False):
        batch = insert_frame_markers(batch, tokenizer, frame_layout)
    if carrier_placement not in PLACEMENTS:
        raise ValueError('Unknown carrier_placement')
    if frame_layout not in ('spread', 'duplicate', 'paired'):
        raise ValueError('Unknown frame_layout')
    frame_count = getattr(tokenizer, '_c1_frame_count', 32)
    if frame_count not in (32,64): raise ValueError('Unsupported frame count')
    slots = 2 if frame_layout == 'spread' else 1
    append_all = carrier_placement == C1_B
    ids, attention = batch['input_ids'], batch['attention_mask']
    grid = batch['video_grid_thw']
    if ids.shape[0] != 1 or grid.shape != (1, 3) or 'position_ids' in batch:
        raise ValueError('C1 requires one video row with native recomputed positions')
    length = int(attention.sum())
    if not torch.equal(attention[0].bool(), torch.arange(ids.shape[1], device=ids.device) < length):
        raise ValueError('C1 requires right padding')
    carrier, video = carrier_id(tokenizer), tokenizer.convert_tokens_to_ids(VIDEO_TOKEN)
    if (ids == carrier).any():
        raise ValueError('Duplicate carriers')
    groups, h, w = grid[0].tolist()
    if anchors is not None and (frame_layout != 'duplicate' or not 1 <= len(anchors) <= 32
                                or anchors != sorted(set(anchors)) or anchors[0] < 0 or anchors[-1] >= groups
                                or groups > 64):
        raise ValueError('Anchor carriers need the duplicate layout and at most 32 of at most 64 groups')
    if (not 1 <= groups <= (64 if anchors is not None else frame_count // slots)) or h % merge_size or w % merge_size:
        raise ValueError('C1 requires at most 32 frames and a complete native grid')
    per_group = h * w // merge_size**2
    visual = torch.where(ids[0, :length] == video)[0]
    if len(visual) != groups * per_group:
        raise ValueError('Video tokens disagree with the native temporal grid')
    blocks = visual.reshape(groups, per_group)
    if per_group > 1 and not (blocks[:, 1:] - blocks[:, :-1] == 1).all():
        raise ValueError('A fused visual group contains intervening text')
    ends = blocks[:, -1].tolist()
    carried = list(range(groups)) if anchors is None else list(anchors)
    labels = batch.get('labels')
    if labels is not None:
        supervised = torch.where(labels[0] != -100)[0]
        if supervised.numel() and ends[-1] >= int(supervised[0]):
            raise ValueError('Visual prefix overlaps the supervised answer')
    insertions = {ends[g] + 1: slots for g in carried}
    if append_all:
        insertions = {ends[-1] + 1: slots * len(carried)}
    cuts = [0] + list(insertions) + [ids.shape[1]]
    result = dict(batch)
    for key, fill in dict(input_ids=carrier, labels=-100, attention_mask=1, mm_token_type_ids=0).items():
        if key not in batch:
            continue
        value, pieces = batch[key], []
        for i, (a, b) in enumerate(zip(cuts, cuts[1:])):
            pieces.append(value[:, a:b])
            if i < len(insertions):
                pieces.append(value.new_full((1, insertions[b]), fill))
        result[key] = torch.cat(pieces, dim=1)
    positions = [ends[g] + 1 + slots*n + j for n, g in enumerate(carried) for j in range(slots)]
    if append_all:
        positions = list(range(ends[-1] + 1, ends[-1] + 1 + slots*len(carried)))
    result['aux_camera_positions'] = torch.tensor([positions + [-1]*(frame_count-len(positions))],
                                                 device=ids.device, dtype=torch.long)
    # Reference visual tokens identify each frame's native temporal coordinate.
    refs = [int(blocks[g, 0]) + sum(n for cut, n in insertions.items() if cut <= int(blocks[g, 0]))
            for g in carried for _ in range(slots)]
    result['aux_camera_rope_sources'] = torch.tensor([refs + [-1]*(frame_count-len(refs))], device=ids.device)
    last_visual = ends[-1] + sum(n for cut, n in insertions.items() if cut <= ends[-1])
    result['aux_video_prefix_end'] = torch.tensor([max(max(positions), last_visual)], device=ids.device)
    result['aux_carrier_placement'] = torch.tensor([PLACEMENTS.index(carrier_placement)], device=ids.device)
    if frame_layout != 'spread':
        result['aux_frame_layout'] = torch.tensor([('spread', 'duplicate', 'paired').index(frame_layout)], device=ids.device)
    return result


def standard_attention_mask(batch, bidirectional=False):
    """Boolean SDPA mask. Only video-prefix queries may see future prefix keys.

    Gated DeltaNet receives the original 2D padding mask and remains recurrent.
    Text after the final CAM stays causal; no question or answer enters the prefix.
    """
    valid = batch['attention_mask'].bool()
    length = valid.shape[1]
    index = torch.arange(length, device=valid.device)
    allowed = (index[:, None] >= index[None, :])[None].expand(valid.shape[0], -1, -1)
    if bidirectional:
        prefix = index[None] <= batch['aux_video_prefix_end'][:, None]
        allowed = allowed | (prefix[:, :, None] & prefix[:, None, :])
    return (allowed & valid[:, None, :])[:, None]


def frame_position_ids(native, batch):
    """Anchor CAM_k to frame k's first visual token in all three M-RoPE axes.

    Qwen's temporal patch fuses two RGB frames, which therefore share a native
    temporal ID and grid origin. Learned embeddings distinguish ordered slots.
    Keeping appended-text spatial IDs would rotate those query components far
    from their frame's grid. Preserve non-CAM IDs and the separate text/cache
    axis, when native generation supplies four axes; sequence order stays causal.
    """
    result = native.clone()
    temporal = 1 if native.shape[0] == 4 else 0
    for row, positions in enumerate(batch['aux_camera_positions']):
        valid = positions >= 0
        result[temporal:, row, positions[valid]] = native[
            temporal:, row, batch['aux_camera_rope_sources'][row, valid]]
    return result


def single_image_row(row, stream, *, training_mode='mixed', geometry_online=None):
    """Keep native pointing admission; only final GX admits explicit image VQA."""
    image_vqa = stream == 'vqa' and training_mode == 'final' and bool(geometry_online) and 'pointing' not in row
    if (not (stream == 'pointing' or image_vqa)
            or row.get('provenance', {}).get('input') != 'single_image'):
        return False
    inputs = row['student_input']
    if (any(len(inputs[k]) != 1 for k in ('frames', 'frame_indices', 'timestamps'))
            or (stream == 'pointing' and (type(row['pointing']['frame']) is not int or row['pointing']['frame'] != 1))):
        raise ValueError('Single-image pointing requires one aligned frame and pointing.frame 1'
                         if stream == 'pointing' else 'Single-image VQA requires one aligned frame')
    return True


def encode_image_row(processor, row, *, allow_readout=False):
    from PIL import Image
    from torch.nn import functional as F
    from .batches import assistant_labels, training_stop_token
    from .pose_samples import load_frames
    inputs = row['student_input']
    array = load_frames(inputs)[0]
    messages = [{'role': 'user', 'content': [{'type': 'image'},
                {'type': 'text', 'text': inputs['question']}]}]
    prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    # The non-thinking generation prefix already contains the empty think block.
    target = row['target'].removeprefix(READOUT_TARGET)
    if ((not target and not (allow_readout and row['target'] == READOUT_TARGET))
            or any(token in target for token in ('<|im_start|>', '<|im_end|>', '<|video_pad|>', '<|image_pad|>'))):
        raise ValueError('Target is empty or contains conversation/media control tokens')
    full = processor.apply_chat_template(messages + [{'role': 'assistant', 'content': target}],
        tokenize=False, add_generation_prompt=False, enable_thinking=False)
    eos = processor.tokenizer.eos_token
    if full != prompt + target + eos + '\n':
        raise ValueError('Single-image chat-template assistant boundary changed')
    stop, stop_id = training_stop_token(processor)
    if stop_id != processor.tokenizer.eos_token_id and stop in target:
        raise ValueError('Target contains the generation-stop token')
    suffix = target + eos + (stop if stop_id != processor.tokenizer.eos_token_id else '')
    plain = processor.tokenizer.encode(prompt, add_special_tokens=False)
    suffix_ids = processor.tokenizer.encode(suffix, add_special_tokens=False)
    if (processor.tokenizer.encode(prompt + suffix, add_special_tokens=False) != plain + suffix_ids
            or processor.tokenizer.decode(plain + suffix_ids, skip_special_tokens=False) != prompt + suffix):
        raise ValueError('Single-image assistant token boundary changed')
    batch = processor(text=[prompt], images=[Image.fromarray(array)], return_tensors='pt')
    grid = batch['image_grid_thw']
    visual_tokens = int((batch['input_ids'] == processor.image_token_id).sum())
    if (grid.shape != (1, 3) or int(grid[0, 0]) != 1
            or visual_tokens != int(grid.prod()) // processor.image_processor.merge_size**2):
        raise ValueError('Single-image placeholders disagree with the native image grid')
    prompt_length = batch['input_ids'].shape[1]
    ids = torch.cat((batch['input_ids'], torch.tensor([suffix_ids], dtype=torch.long)), dim=1)
    length = math.ceil(ids.shape[1] / 8) * 8
    if length > 16384:
        raise ValueError('Complete single-image row exceeds 16384 tokens; no truncation')
    padding = length - ids.shape[1]
    batch['input_ids'] = F.pad(ids, (0, padding), value=processor.tokenizer.pad_token_id)
    batch['attention_mask'] = F.pad(torch.ones_like(ids), (0, padding), value=0)
    if 'mm_token_type_ids' in batch:
        batch['mm_token_type_ids'] = F.pad(batch['mm_token_type_ids'], (0, len(suffix_ids) + padding), value=0)
    batch['labels'] = assistant_labels(batch['input_ids'], batch['attention_mask'], prompt_length, len(suffix_ids))
    ending = [processor.tokenizer.eos_token_id] + ([stop_id] if stop_id != processor.tokenizer.eos_token_id else [])
    if suffix_ids[-len(ending):] != ending:
        raise ValueError('Assistant supervision omitted a required stop token')
    return dict(batch), dict(qid=row['qid'], frame_count=1, input='single_image', image_grid_thw=grid.tolist(),
        original_frame_indices=inputs['frame_indices'], original_timestamps_seconds=inputs['timestamps'],
        original_width_height_per_frame=[[array.shape[1], array.shape[0]]], visual_tokens=visual_tokens,
        prompt_tokens=prompt_length, assistant_tokens_including_eos=len(suffix_ids), padding_tokens=padding,
        sequence_tokens=length, assistant_only_mask_verified=True, target_truncated=False)


def encode(processor, row, record, stream, carrier_placement=C1_A, training_mode='mixed',
           frame_layout='spread', frame_pair_gap_seconds=None, geometry_online=None):
    from .pose_samples import encode_row
    from .g3t_online import NATIVE_INPUT
    readout = stream == 'vqa' and row.get('target') == READOUT_TARGET
    if readout and geometry_online is None:
        geometry_online = getattr(processor, '_c1_readout_geometry_online', None)
    gf1 = (geometry_online or {}).get('gf1')
    native_g3t = not gf1 and (stream == 'pose' or readout) and (
        geometry_online or {}).get('input') == NATIVE_INPUT
    if single_image_row(row, stream, training_mode=training_mode, geometry_online=geometry_online):
        if training_mode == 'pose_only':
            raise ValueError('Pose-only batches require dense all-32-frame pose rows')
        batch, audit = encode_image_row(processor, row, allow_readout=training_mode == 'final' and bool(geometry_online))
        return batch, None, audit
    if stream == 'pose':
        row = {**row, 'target': READOUT_TARGET}
    options = dict(gf1=gf1) if gf1 else dict(native_g3t=True) if native_g3t else {}
    batch, audit = (encode_row(processor, row) if frame_layout == 'spread' and not native_g3t else
                    encode_layout_row(processor, row, frame_layout, frame_pair_gap_seconds, **options))
    batch = insert_frame_carriers(batch, processor.tokenizer, processor.video_processor.merge_size, carrier_placement,
                                  frame_layout, anchors=anchor_slots(row.get('student_input') or {}, frame_layout))
    if batch['input_ids'].shape[1] > 16384:
        raise ValueError('Complete row plus carriers exceeds 16384 tokens; no truncation')
    targets = target_tensors(record, all_frames=True) if stream == 'pose' else None
    if stream == 'pose':
        batch['labels'].fill_(-100)
    if training_mode == 'pose_only':
        if stream != 'pose' or not targets['aux_camera_mask'].all() or not (batch['aux_camera_positions'] >= 0).all():
            raise ValueError('Pose-only batches require dense all-32-frame pose rows')
    return batch, targets, audit


def mixed_indices(counts, steps, seed=17, start_step=0, training_mode='mixed', mix=None, world=8, r2_sampling=None, require_r2=False):
    if require_r2 and not r2_sampling:
        raise ValueError('Missing bound r2_sampling table')
    if r2_sampling is not None:
        from .r2_mix import plans
        yield from plans(r2_sampling, counts, steps, start_step, world)
        return
    """All ranks use the same stream per microstep (FSDP collective order).

    Mixed: four microsteps per optimizer update across eight ranks: 16 pose, 8 VQA,
    8 pointing rows. Final: the recipe's mix, one row per rank per microstep.
    Each stream has independent deterministic shuffled epochs.
    Replaying integer indices on resume does not decode skipped rows.
    """
    if training_mode not in ('mixed', 'pose_only', 'final'):
        raise ValueError('Unknown training_mode')
    if training_mode == 'final':
        streams = tuple(mix or ())
    else:
        # Pose-only takes its microstep count from the recipe mix (four at world 8; eight at world 4).
        streams = ('pose',)*(len(mix) if mix else 4) if training_mode == 'pose_only' else ('pose', 'pose', 'vqa', 'pointing')
    if type(world) is not int or world < 1:
        raise ValueError('world must be a positive integer')
    if set(counts) != set(streams) or any(type(n) is not int or n < 1 for n in counts.values()):
        raise ValueError('C1 streams must match training_mode and be nonempty')
    orders = {k: list(range(v)) for k, v in counts.items()}
    rng = {k: random.Random(seed + 1009*i) for i, k in enumerate(counts)}
    cursor = dict.fromkeys(counts, 0)
    for k in counts:
        rng[k].shuffle(orders[k])
    for step in range(steps):
        plan = []
        for stream in streams:
            indices = []
            for _ in range(world):
                if cursor[stream] == counts[stream]:
                    rng[stream].shuffle(orders[stream]); cursor[stream] = 0
                indices.append(orders[stream][cursor[stream]])
                cursor[stream] += 1
            plan.append((stream, indices))
        if step >= start_step:
            yield plan


POINTING_KINDS = ('gt_instance_mask', 'gt_absent')


def _load_mask(pin, key):
    from .common import binding
    from .orchard_paths import resolve_read
    binding(pin['path'], pin['sha256'])
    with np.load(resolve_read(pin['path']), allow_pickle=False) as data:
        mask = data[key]
    if mask.dtype != np.bool_ or mask.ndim != 2:
        raise ValueError('Pointing requires a boolean GT raster')
    return mask


def _grid_hits(mask, u, v):
    """Both floor and nearest back-projections of a 0-1000 grid point land inside the mask."""
    h, w = mask.shape
    for x, y in ((u * w / 1000, v * h / 1000), (u * w / 1000 + .5, v * h / 1000 + .5)):
        if not mask[min(int(y), h - 1), min(int(x), w - 1)]:
            return False
    return True


def mask_target(pin, key='mask', kind='gt_instance_mask'):
    """Base Qwen's native integer JSON point on the 0-1000 grid, or null for an absent object.

    Visible: the foreground pixel nearest the centroid whose grid point maps back inside the
    mask (concave and thin masks stay safe). Absent: the pinned raster of the named label in
    that frame has zero pixels.
    """
    mask = _load_mask(pin, key)
    if kind == 'gt_absent':
        if mask.any():
            raise ValueError('Absent-object evidence raster must be empty')
        return '{"point_2d": null}', dict(uv=None, pixel_yx=None, shape=list(mask.shape))
    if kind != 'gt_instance_mask' or not mask.any():
        raise ValueError('Pointing requires a nonempty boolean GT instance mask')
    yx = np.argwhere(mask)
    h, w = mask.shape
    for y, x in yx[np.square(yx - yx.mean(axis=0)).sum(axis=1).argsort(kind='stable')]:
        y, x = int(y), int(x)
        u, v = min(int((x + .5) / w * 1000), 1000), min(int((y + .5) / h * 1000), 1000)
        if _grid_hits(mask, u, v):
            text = json.dumps({'point_2d': [u, v]})
            return text, dict(uv=[u, v], pixel_yx=[y, x], shape=list(mask.shape))
    raise ValueError('No integer grid point maps back inside the GT mask')


@contextmanager
def _source_lines(source, source_receipt, stream):
    if type(source_receipt) is not bool:
        raise ValueError('source_receipt must be boolean')
    if not source_receipt:
        with pinned(source).open() as handle:
            yield handle
        return
    receipt = load(pinned(source))
    if receipt.get('schema') != 'c1-stream-v1' or receipt.get('stream') != stream:
        raise ValueError('Rebuilding requires a native receipt for the same stream')
    path = pinned(receipt['database'])
    connection = sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)
    try:
        count, low, high = connection.execute('SELECT count(*),min(i),max(i) FROM rows').fetchone()
        if count != receipt.get('count') or low != 0 or high != count-1:
            raise ValueError('Source stream database inventory differs')
        yield (row for row, in connection.execute('SELECT row FROM rows ORDER BY i'))
    finally:
        connection.close()


def build_stream(source, division_pin, output, stream, *, training_mode='mixed', geometry_online=None,
                 remove_files=(), ground_target_filter=False, source_receipt=False, scene_filter=None):
    """CPU parent data job: JSONL -> immutable native SQLite + audit receipt.

    Pointing rows supply pointing={kind:'gt_instance_mask'|'gt_absent',mask:{path,sha256},
    key, frame:1..32, rgb_sha256, instance_id|label}; masks remain target-side only.
    Frames and masks keep logical path strings and are read through the frame root map.
    """
    from PIL import Image
    from .common import binding
    from .orchard_paths import resolve_read
    from .row_removals import Removals
    from .ground_target_filter import TargetFilter, pointing_key
    targets = TargetFilter(remove_files, shape_filter=ground_target_filter) if stream == 'pointing' else None
    removals = targets.removals if targets is not None else Removals(remove_files, stream=stream)
    if stream not in ('vqa', 'pointing'):
        raise ValueError('A1 supplies the pose database')
    division = load(pinned(division_pin))
    if division.get('schema') != 'diagnostic-whole-scene-division-v1' or division.get('training_only') is not True:
        raise ValueError('C1 requires the inherited training-only division')
    train, heldout = set(division['train_scenes']), set(division['heldout_scenes'])
    if scene_filter is not None:
        with _source_lines(source, source_receipt, stream) as handle:
            scene_filter.expect(stream, (json.loads(line) for line in handle),
                                dict(source=source, source_receipt=source_receipt))
    out = Path(output); out.mkdir(parents=True, exist_ok=False)
    conn = sqlite3.connect(out/'rows.sqlite')
    conn.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY, row TEXT NOT NULL, target TEXT NOT NULL)')
    seen, scenes, count = set(), set(), 0
    try:
        with _source_lines(source, source_receipt, stream) as handle:
            for line in handle:
                row = json.loads(line)
                if scene_filter is not None and not scene_filter.keep(row, stream):
                    continue
                if targets is not None and (remove_files or ground_target_filter) and row['pointing']['kind'] == 'gt_instance_mask':
                    key = pointing_key(row)
                    mask = _load_mask(row['pointing']['mask'], row['pointing'].get('key', 'mask'))
                    keep, quality = targets.keep(mask, key, source['path'] if isinstance(source, dict) else source)
                    if not keep:
                        continue
                    row['pointing'] = {**row['pointing'], 'row_key': key, 'shape_quality': quality}
                if not removals.keep(row):
                    continue
                scene = row['dataset']+'/'+row['scene']
                if scene not in train or scene in heldout or row['qid'] in seen:
                    raise ValueError('C1 data violate scene division or unique row identity')
                seen.add(row['qid']); scenes.add(scene)
                inputs = row['student_input']
                nested = stream == 'vqa' and anchor_slots(inputs) is not None and len(inputs['frames']) == 64
                if (not single_image_row(row, stream, training_mode=training_mode, geometry_online=geometry_online)
                        and not nested and (len(inputs['frames']) not in (32, 64) or len(inputs['frame_indices']) != len(inputs['frames']))):
                    raise ValueError('C1 preservation rows require 32 pinned native frames or 64 pinned native frames')
                if nested:
                    anchors = [inputs['frame_indices'][k] for k in inputs['anchor_slots']]
                    if (len(anchors) != 32 or nested_indices(anchors) != (inputs['frame_indices'], inputs['anchor_slots'])):
                        raise ValueError('Nested VQA rows must hold the 32 anchors plus their bisection frames')
                for frame in inputs['frames']:
                    if set(frame) != {'path', 'sha256'}:
                        raise ValueError('Input requires an exact path/SHA256 pin')
                    binding(frame['path'], frame['sha256'])
                if stream == 'pointing':
                    point = row['pointing']
                    frame = point['frame']
                    identity = point.get('label') if point['kind'] == 'gt_absent' else point.get('instance_id')
                    if (point['kind'] not in POINTING_KINDS or type(frame) is not int
                            or not 1 <= frame <= len(inputs['frames']) or identity in (None, '')
                            or point['rgb_sha256'] != inputs['frames'][frame-1]['sha256']):
                        raise ValueError('GT-mask frame/RGB provenance mismatch')
                    target, audit = mask_target(point['mask'], point.get('key', 'mask'), point['kind'])
                    with Image.open(resolve_read(inputs['frames'][frame-1]['path'])) as rgb:
                        if list(reversed(rgb.size)) != audit['shape']:
                            raise ValueError('GT mask raster differs from the pinned RGB frame')
                    row = {**row, 'target': READOUT_TARGET + target,
                           'pointing': {**point, 'selected': audit}}
                    if not inputs['question']:
                        raise ValueError('Pointing question must identify the object and frame')
                elif not isinstance(row.get('target'), str) or not row['target'].strip():
                    raise ValueError('VQA requires an admitted answer target')
                conn.execute('INSERT INTO rows VALUES (?,?,?)', (count, json.dumps(row), '{}'))
                count += 1
        if not count:
            raise ValueError('Empty C1 preservation stream')
        conn.commit()
    finally:
        conn.close()
    receipt = dict(schema='c1-stream-v1', stream=stream, count=count, scenes=len(scenes),
                   source=source, division=division_pin, database=file_pin(out/'rows.sqlite'),
                   gt_masks_only=stream == 'pointing', heldout_overlap=0)
    if remove_files:
        receipt['removals'] = removals.report()
    if targets is not None and (remove_files or ground_target_filter):
        receipt['target_filter'] = targets.report()
    if source_receipt:
        receipt['source_receipt'] = source
    if scene_filter is not None:
        receipt['source_scene_exclusions'] = scene_filter.report()
    write(out/'receipt.json', receipt)
    return receipt
