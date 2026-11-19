"""Nested 64-viewpoint input for 32-slot heads.

Each video row keeps its 32 sampled viewpoints as anchors and adds the 32 frames
that `carrier_c1_data.nested_indices` bisects between them. Carriers, `Frame k: `
markers (k = anchor ordinal), pose and depth slots, targets and the question text
stay on the anchors, so "frame k of 32" keeps one meaning in training and reads.
"""
import torch

NESTED = {'viewpoints': 64, 'anchors': 32, 'rule': 'nested_bisection_v1'}


def check_spec(value):
    """None keeps the 32-viewpoint input; the only other admitted value is NESTED."""
    if value is not None and value != NESTED:
        raise ValueError('FRAME_INPUT_UNSUPPORTED')
    return value


def nested(row):
    inputs = row.get('student_input') or {}
    return inputs.get('anchor_slots') is not None


def anchors(inputs):
    return [inputs['frame_indices'][k] for k in inputs['anchor_slots']]


def check_row(row, spec):
    """Every multi-frame row under NESTED carries the anchors plus exactly their bisection frames."""
    from .carrier_c1_data import nested_indices
    inputs = row.get('student_input') or {}
    count = len(inputs.get('frames') or ())
    if spec is None:
        if nested(row):
            raise ValueError('FRAME_INPUT_NESTED_ROW_UNDECLARED')
        return row
    if count <= 1:
        return row
    slots = inputs.get('anchor_slots')
    if (count != spec['viewpoints'] or not isinstance(slots, list) or len(slots) != spec['anchors']
            or any(len(inputs.get(k) or ()) != count for k in ('frame_indices', 'timestamps'))):
        raise ValueError('FRAME_INPUT_ROW_NOT_NESTED')
    if nested_indices(anchors(inputs), spec['viewpoints']) != (inputs['frame_indices'], slots):
        raise ValueError('FRAME_INPUT_ROW_RULE_DIFFERS')
    return row


def nest_row(row, pins, spec=NESTED):
    """32-viewpoint row -> nested row. `pins` maps source ordinal -> {path, sha256}; anchors keep their pins."""
    from copy import deepcopy
    from .carrier_c1_data import nested_indices
    result = deepcopy(row)
    inputs = result['student_input']
    if nested(row) or len(inputs['frames']) != spec['anchors']:
        raise ValueError('FRAME_INPUT_SOURCE_NOT_32')
    try:
        indices, slots = nested_indices(inputs['frame_indices'], spec['viewpoints'])
    except ValueError as error:
        raise ValueError(f'FRAME_INPUT_CLIP_TOO_SHORT:{error}') from None
    by_ordinal = dict(zip(inputs['frame_indices'], inputs['frames'], strict=True))
    for ordinal in indices:
        if ordinal in by_ordinal:
            continue
        pin = pins.get(ordinal)
        if not isinstance(pin, dict) or set(pin) != {'path', 'sha256'}:
            raise ValueError(f'FRAME_INPUT_DENSE_FRAME_MISSING:{ordinal}')
        by_ordinal[ordinal] = dict(pin)
    fps = inputs['fps']
    stamps = dict(zip(inputs['frame_indices'], inputs['timestamps'], strict=True))
    inputs.update(frames=[by_ordinal[k] for k in indices], frame_indices=indices,
                  timestamps=[stamps.get(k, k / fps) for k in indices], anchor_slots=slots)
    return result


def anchor_view(batch):
    """The anchor groups' patches only, so the 32-slot private depth ViT reads the anchors."""
    groups = batch.get('aux_anchor_groups')
    grid = batch.get('video_grid_thw')
    if groups is None or grid is None:
        return batch
    t, h, w = (int(v) for v in grid[0])
    chosen = [int(g) for g in groups[0]]
    if len(chosen) == t:
        return batch
    pixels = batch['pixel_values_videos']
    if grid.shape != (1, 3) or pixels.shape[0] != t * h * w or chosen != sorted(set(chosen)) or chosen[-1] >= t:
        raise ValueError('FRAME_INPUT_ANCHOR_VIEW_SHAPE')
    index = torch.cat([torch.arange(g * h * w, (g + 1) * h * w, device=pixels.device) for g in chosen])
    return {**batch, 'pixel_values_videos': pixels.index_select(0, index),
            'video_grid_thw': grid.new_tensor([[len(chosen), h, w]])}
