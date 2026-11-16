"""Per-frame carrier placement and deterministic, scene-audited C1 streams."""
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


def layout_inputs(row, layout='spread', gap=None, verify_partners=False):
    """Keep target slots in sampled-viewpoint order; expand only the RGB input.

    Paired rows supply student_input.partner_frames: one {path, sha256,
    recording_id, frame_index, timestamp} per anchor, in the same recording_id.
    """
    layout_settings(dict(frame_layout=layout, frame_pair_gap_seconds=gap))
    inputs = row['student_input']
    if layout == 'spread':
        return inputs
    count = len(inputs['frames'])
    if not 1 <= count <= 32 or any(len(inputs[k]) != count for k in ('frame_indices', 'timestamps')):
        raise ValueError('C1 layouts require at most 32 aligned sampled viewpoints')
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


def encode_layout_row(processor, row, layout, gap):
    from transformers.video_utils import VideoMetadata
    from .pose_samples import CATEGORY, DEFAULT_PIXELS, augment, check_sample, encode_frames, load_frames
    inputs = layout_inputs(row, layout, gap)
    is_pose = row.get('category') == CATEGORY and 'pose_sample' in row
    if is_pose:
        check_sample(row, max_groups=32)
    # Duplicate after augmentation so each temporal patch contains identical bytes.
    original = row['student_input'] if layout == 'duplicate' else inputs
    arrays = load_frames(original)
    if is_pose:
        arrays = augment(arrays, row['pose_sample']['augment'])
    if layout == 'duplicate':
        arrays = np.repeat(arrays, 2, axis=0)
    metadata = VideoMetadata(total_num_frames=inputs['total_num_frames'], fps=inputs['fps'],
        frames_indices=inputs['frame_indices'], width=arrays.shape[2], height=arrays.shape[1])
    batch, audit = encode_frames(processor, inputs['question'], inputs.get('options') or [], arrays,
                                 metadata, row['target'], DEFAULT_PIXELS, 16384)
    return batch, {**audit, 'frame_layout': layout, 'frame_pair_gap_seconds': gap,
                   'viewpoint_timestamps_seconds': row['student_input']['timestamps']}


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


def insert_frame_carriers(batch, tokenizer, merge_size=2, carrier_placement=C1_A, frame_layout='spread'):
    """B appends all carriers after the final video patch in every layout.

    A/C keep two local carriers per fused pair in spread and one per viewpoint
    in duplicate/paired. Each B carrier retains its own frame identity and RoPE.
    Native mRoPE is recomputed on the extended input. Never reuse position_ids.
    A processor with `_c1_frame_markers` set (receipt frame_markers) first inserts
    `Frame k: ` before each group, identically in every stream and evaluator path.
    """
    if getattr(tokenizer, '_c1_frame_markers', False):
        batch = insert_frame_markers(batch, tokenizer, frame_layout)
    if carrier_placement not in PLACEMENTS:
        raise ValueError('Unknown carrier_placement')
    if frame_layout not in ('spread', 'duplicate', 'paired'):
        raise ValueError('Unknown frame_layout')
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
    if not 1 <= groups <= 32 // slots or h % merge_size or w % merge_size:
        raise ValueError('C1 requires at most 32 frames and a complete native grid')
    per_group = h * w // merge_size**2
    visual = torch.where(ids[0, :length] == video)[0]
    if len(visual) != groups * per_group:
        raise ValueError('Video tokens disagree with the native temporal grid')
    blocks = visual.reshape(groups, per_group)
    if per_group > 1 and not (blocks[:, 1:] - blocks[:, :-1] == 1).all():
        raise ValueError('A fused visual group contains intervening text')
    ends = blocks[:, -1].tolist()
    labels = batch.get('labels')
    if labels is not None:
        supervised = torch.where(labels[0] != -100)[0]
        if supervised.numel() and ends[-1] >= int(supervised[0]):
            raise ValueError('Visual prefix overlaps the supervised answer')
    insertions = {end + 1: slots for end in ends}
    if append_all:
        insertions = {ends[-1] + 1: slots * groups}
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
    positions = [end + 1 + slots*g + j for g, end in enumerate(ends) for j in range(slots)]
    if append_all:
        positions = list(range(ends[-1] + 1, ends[-1] + 1 + slots*groups))
    result['aux_camera_positions'] = torch.tensor([positions + [-1]*(32-len(positions))],
                                                 device=ids.device, dtype=torch.long)
    # Reference visual tokens identify each frame's native temporal coordinate.
    refs = [int(blocks[g, 0]) + sum(n for cut, n in insertions.items() if cut <= int(blocks[g, 0]))
            for g in range(groups) for _ in range(slots)]
    result['aux_camera_rope_sources'] = torch.tensor([refs + [-1]*(32-len(refs))], device=ids.device)
    result['aux_video_prefix_end'] = torch.tensor([max(positions)], device=ids.device)
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


def encode(processor, row, record, stream, carrier_placement=C1_A, training_mode='mixed',
           frame_layout='spread', frame_pair_gap_seconds=None):
    from .pose_samples import encode_row
    if stream == 'pose':
        row = {**row, 'target': READOUT_TARGET}
    batch, audit = (encode_row(processor, row) if frame_layout == 'spread' else
                    encode_layout_row(processor, row, frame_layout, frame_pair_gap_seconds))
    batch = insert_frame_carriers(batch, processor.tokenizer,
                                  processor.video_processor.merge_size, carrier_placement, frame_layout)
    if batch['input_ids'].shape[1] > 16384:
        raise ValueError('Complete row plus carriers exceeds 16384 tokens; no truncation')
    targets = target_tensors(record, all_frames=True) if stream == 'pose' else None
    if stream == 'pose':
        batch['labels'].fill_(-100)
    if training_mode == 'pose_only':
        if stream != 'pose' or not targets['aux_camera_mask'].all() or not (batch['aux_camera_positions'] >= 0).all():
            raise ValueError('Pose-only batches require dense all-32-frame pose rows')
    return batch, targets, audit


def mixed_indices(counts, steps, seed=17, start_step=0, training_mode='mixed', mix=None, world=8):
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
        streams = ('pose',)*4 if training_mode == 'pose_only' else ('pose', 'pose', 'vqa', 'pointing')
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


def build_stream(source, division_pin, output, stream):
    """CPU parent data job: JSONL -> immutable native SQLite + audit receipt.

    Pointing rows supply pointing={kind:'gt_instance_mask'|'gt_absent',mask:{path,sha256},
    key, frame:1..32, rgb_sha256, instance_id|label}; masks remain target-side only.
    Frames and masks keep logical path strings and are read through the frame root map.
    """
    from PIL import Image
    from .common import binding
    from .orchard_paths import resolve_read
    if stream not in ('vqa', 'pointing'):
        raise ValueError('A1 supplies the pose database')
    division = load(pinned(division_pin))
    if division.get('schema') != 'diagnostic-whole-scene-division-v1' or division.get('training_only') is not True:
        raise ValueError('C1 requires the inherited training-only division')
    train, heldout = set(division['train_scenes']), set(division['heldout_scenes'])
    out = Path(output); out.mkdir(parents=True, exist_ok=False)
    conn = sqlite3.connect(out/'rows.sqlite')
    conn.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY, row TEXT NOT NULL, target TEXT NOT NULL)')
    seen, scenes, count = set(), set(), 0
    try:
        with pinned(source).open() as handle:
            for line in handle:
                row = json.loads(line)
                scene = row['dataset']+'/'+row['scene']
                if scene not in train or scene in heldout or row['qid'] in seen:
                    raise ValueError('C1 data violate scene division or unique row identity')
                seen.add(row['qid']); scenes.add(scene)
                inputs = row['student_input']
                if len(inputs['frames']) != 32 or len(inputs['frame_indices']) != 32:
                    raise ValueError('C1 preservation rows require 32 pinned native frames')
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
    write(out/'receipt.json', receipt)
    return receipt
