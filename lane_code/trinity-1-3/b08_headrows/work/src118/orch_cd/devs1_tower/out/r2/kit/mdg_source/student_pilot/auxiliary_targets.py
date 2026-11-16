"""Build and consume training-only GT sidecars and query-token targets; never alter student inputs."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from . import auxiliary_reason as reason
from .auxiliary_config import SIDECAR_OBJECTIVES, enabled, normalize, reason_enabled, sidecar_enabled, weight


SCHEMA = 'rgb-student-auxiliary-v1'
# v2 = v1 plus per-row 'queries': four category entries (masked entries pad the list).
SCHEMA_V2 = 'rgb-student-auxiliary-v2'
QUERY_SLOTS = 4
QUERY_FIELDS = frozenset({'name', 'span', 'group_count', 'group_count_mask', 'scene_count', 'scene_count_mask',
                          'object', 'object_mask'})
VISION_END = '<|vision_end|>'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def pin(path):
    path = Path(path)
    with path.open('rb') as handle:
        sha = hashlib.file_digest(handle, 'sha256').hexdigest()
    return {'path': str(path.resolve()), 'sha256': sha}


def verify(spec):
    path = Path(spec['path'])
    if pin(path)['sha256'] != spec['sha256']:
        raise ValueError('Auxiliary source hash mismatch: ' + str(path))
    return path


def input_identity(row):
    inputs = row['student_input']
    # Paths may change during host staging; content and timing may not.
    return digest({'qid': row['qid'], 'dataset': row['dataset'], 'scene': row['scene'],
                   'input': {**inputs, 'frames': [f['sha256'] for f in inputs['frames']]}})


def pose_targets(camera_poses, unit_m=1.0):
    poses = np.asarray(camera_poses, dtype=np.float64)
    if poses.shape != (32, 4, 4) or not np.isfinite(poses).all():
        raise ValueError('Expected 32 finite camera-to-world poses')
    rotations = poses[:, :3, :3]
    if not np.allclose(poses[:, 3], [0, 0, 0, 1], atol=1e-5) or not np.allclose(rotations.transpose(0, 2, 1) @ rotations, np.eye(3), atol=1e-4) or not np.allclose(np.linalg.det(rotations), 1, atol=1e-4):
        raise ValueError('Camera poses are not rigid proper transforms')
    if not np.isfinite(unit_m) or unit_m <= 0:
        raise ValueError('Translation unit must be positive and finite')
    # A Qwen temporal token represents two RGB frames. Use the second observed
    # camera in each pair, explicitly, instead of pretending there are 32 tokens.
    poses = poses[1::2]
    relative = np.linalg.inv(poses[0]) @ poses
    rotation6 = relative[:, :3, :2].transpose(0, 2, 1).reshape(16, 6)
    target = np.concatenate([rotation6, relative[:, :3, 3] / unit_m], axis=-1).astype(np.float32)
    mask = np.ones(16, dtype=bool)
    mask[0] = False  # The reference identity is a tautology, not a useful target.
    return target, mask


def quarters(length):
    """Four contiguous index runs; the first length % 4 runs hold one extra index."""
    base, extra = divmod(length, 4)
    bounds = [i * base + min(i, extra) for i in range(5)]
    return [np.arange(bounds[i], bounds[i + 1]) for i in range(4)]


def depth_targets(depth_z, valid):
    depth, mask = np.asarray(depth_z), np.asarray(valid)
    if depth.ndim != 3 or depth.shape[0] != 32 or depth.shape != mask.shape or mask.dtype != np.bool_ or min(depth.shape[1:]) < 4:
        raise ValueError('Expected 32 aligned optical-axis depth maps and boolean masks')
    targets, masks = np.zeros((16, 4, 4), np.float32), np.zeros((16, 4, 4), bool)
    for i, frame in enumerate(range(1, 32, 2)):
        for y, yy in enumerate(quarters(depth.shape[1])):
            for x, xx in enumerate(quarters(depth.shape[2])):
                values = depth[frame][np.ix_(yy, xx)]
                keep = mask[frame][np.ix_(yy, xx)] & np.isfinite(values) & (values > .05) & (values < 20.)
                if keep.mean() >= .25:
                    targets[i, y, x] = np.median(np.log(values[keep]))
                    masks[i, y, x] = True
    return targets, masks


def blank(row):
    return {'qid': row['qid'], 'input_sha256': input_identity(row),
            'pose': np.zeros((16, 9)).tolist(), 'pose_mask': [False] * 16,
            'depth': np.zeros((16, 4, 4)).tolist(), 'depth_mask': np.zeros((16, 4, 4), bool).tolist(),
            'sources': {}, 'deferred': {}}


def build_row(row, receipt_pin, unit_m=1.0, include_depth=False):
    result = blank(row)
    if receipt_pin is None:
        result['deferred']['pose'] = 'No exact-frame scene receipt supplied'
        result['deferred']['depth'] = 'No exact-frame scene receipt supplied'
        return result
    try:
        receipt = json.loads(verify(receipt_pin).read_text())
        if (receipt['dataset'], receipt['scene_name']) != (row['dataset'], row['scene']):
            raise ValueError('Receipt and training row scene identities differ')
        if receipt['coordinate_frame'] != 'source_world_meters_opencv_camera_to_world':
            raise ValueError('Unsupported camera convention')
        if receipt['geometry_source'] != 'official_aligned_pose_intrinsic_mesh_gt_valid_support':
            raise ValueError('Expected official aligned geometry')
        inputs, frames = row['student_input'], receipt['frames']
        if len(frames) != 32 or [f['ordinal'] for f in frames] != inputs['frame_indices'] or [f['sha256'] for f in frames] != [f['sha256'] for f in inputs['frames']] or not np.allclose([f['timestamp_sec'] for f in frames], inputs['timestamps'], atol=1e-8, rtol=0):
            raise ValueError('Receipt does not match the exact sampled RGB frames and timestamps')
        alignment = json.loads(verify(receipt['alignment']).read_text())
        if alignment.get('estimated_geometry_used') is not False or alignment.get('validated_slots') != 32 or alignment.get('pose_field') != 'aligned_pose' or [f['ordinal'] for f in alignment['frames']] != inputs['frame_indices']:
            raise ValueError('Official camera-to-RGB correspondence is not authenticated')
        # Verify the source provenance carrier too; no published QA answer is read.
        verify(receipt['source_provenance'])
        with np.load(verify(receipt['calibration']), allow_pickle=False) as data:
            if data['indices'].tolist() != inputs['frame_indices']:
                raise ValueError('Calibration frame order mismatch')
            pose, mask = pose_targets(data['camera_poses'], unit_m)
        result.update(pose=pose.tolist(), pose_mask=mask.tolist())
        result['sources'] = {k: receipt[k] for k in ('calibration', 'alignment', 'source_provenance')}
        result['sources']['receipt'] = receipt_pin
    except (ValueError, OSError, KeyError, TypeError) as error:
        result['deferred']['pose'] = str(error)
        result['deferred']['depth'] = 'Camera/RGB alignment unavailable'
        return result
    if include_depth:
        try:
            with np.load(verify(receipt['dense']), allow_pickle=False) as data:
                if data['indices'].tolist() != inputs['frame_indices']:
                    raise ValueError('Depth frame order mismatch')
                depth, mask = depth_targets(data['depth_z'], data['mask'])
            result.update(depth=depth.tolist(), depth_mask=mask.tolist())
            result['sources']['dense'] = receipt['dense']
        except (ValueError, OSError, KeyError, TypeError) as error:
            result['deferred']['depth'] = str(error)
    else:
        result['deferred']['depth'] = 'Depth supervision not requested'
    return result


def number(value):
    return type(value) in (int, float) and np.isfinite(value)


def check_queries(queries, question):
    """Validate one row's v2 category queries against its question text."""
    if not isinstance(queries, list) or len(queries) != QUERY_SLOTS:
        raise ValueError('Sidecar v2 rows need exactly four category query entries')
    for query in queries:
        if not isinstance(query, dict) or set(query) != QUERY_FIELDS:
            raise ValueError('Malformed category query fields')
        counts, masks = query['group_count'], query['group_count_mask']
        if (not isinstance(counts, list) or len(counts) != 16 or not all(number(c) and c >= 0 for c in counts)
                or not isinstance(masks, list) or len(masks) != 16 or not all(type(m) is bool for m in masks)):
            raise ValueError('Malformed per-group visible count target')
        if not number(query['scene_count']) or query['scene_count'] < 0 or type(query['scene_count_mask']) is not bool:
            raise ValueError('Malformed scene count target')
        if (not isinstance(query['object'], list) or len(query['object']) != 6 or not all(number(v) for v in query['object'])
                or type(query['object_mask']) is not bool):
            raise ValueError('Malformed object centroid/extent target')
        if any(masks) or query['scene_count_mask'] or query['object_mask']:
            span = query['span']
            if (not isinstance(query['name'], str) or not query['name'] or not isinstance(span, list) or len(span) != 2
                    or any(type(v) is not int for v in span) or not 0 <= span[0] < span[1] <= len(question)):
                raise ValueError('Category span must lie inside the question text')


def active(query):
    return any(query['group_count_mask']) or query['scene_count_mask'] or query['object_mask']


def load_for_rows(rows, config):
    if not enabled(config):
        return None
    cfg = normalize(config)
    records = [{} for _ in rows]
    if sidecar_enabled(cfg):
        records = load_sidecar(rows, cfg)
    if reason_enabled(cfg):
        census = reason.validate_rows(rows)
        if not census['rows_with_queries']:
            raise ValueError('Enabled query-token heads have no training row with a query token')
        records = [{**record, 'reason': True} for record in records]
    return records


def load_sidecar(rows, cfg):
    payload = json.loads(verify(cfg['supervision']).read_text())
    category = weight(cfg, 'count') > 0 or weight(cfg, 'object') > 0
    if payload.get('schema') not in (SCHEMA, SCHEMA_V2) or (category and payload.get('schema') != SCHEMA_V2):
        raise ValueError('Auxiliary sidecar schema does not serve the enabled objectives')
    if payload.get('translation_unit_m') != cfg['translation_unit_m']:
        raise ValueError('Auxiliary sidecar convention mismatch')
    records = payload['rows']
    if len(records) != len(rows) or [r['qid'] for r in records] != [r['qid'] for r in rows] or len({r['qid'] for r in records}) != len(records):
        raise ValueError('Auxiliary sidecar must retain the exact training row census and order')
    counts = {name: 0 for name in SIDECAR_OBJECTIVES}
    for row, record in zip(rows, records):
        if record['input_sha256'] != input_identity(row):
            raise ValueError('Auxiliary sidecar RGB input changed')
        for key, shape in [('pose', (16, 9)), ('pose_mask', (16,)), ('depth', (16, 4, 4)), ('depth_mask', (16, 4, 4))]:
            array = np.asarray(record[key])
            if array.shape != shape or ('mask' in key and array.dtype != bool) or ('mask' not in key and not np.isfinite(array).all()):
                raise ValueError('Malformed auxiliary target: ' + key)
        for name in ('pose', 'depth'):
            counts[name] += int(np.asarray(record[name + '_mask']).any())
        if payload['schema'] == SCHEMA_V2:
            check_queries(record['queries'], row['student_input']['question'])
            counts['count'] += any(any(q['group_count_mask']) or q['scene_count_mask'] for q in record['queries'])
            counts['object'] += any(q['object_mask'] for q in record['queries'])
    for name, count in counts.items():
        if weight(cfg, name) and not count:
            raise ValueError('Enabled auxiliary objective has zero covered rows: ' + name)
    if not category:
        # Disabled category objectives never touch the tokenizer or the batch.
        records = [{key: value for key, value in record.items() if key != 'queries'} for record in records]
    return records


def category_positions(tokenizer, prompt_ids, question, spans):
    """Map character spans of the question to prompt token positions via tokenizer offsets.

    The rendered prompt places the question verbatim right after the last video
    placeholder, so the text after the final vision-end token re-tokenizes to the
    same ids and its offsets index the question directly.
    """
    vision_end = tokenizer.convert_tokens_to_ids(VISION_END)
    ends = [index for index, token in enumerate(prompt_ids) if token == vision_end]
    if not ends:
        raise ValueError('Prompt has no video placeholder end token')
    start = ends[-1] + 1
    tail = list(prompt_ids[start:])
    text = tokenizer.decode(tail, skip_special_tokens=False)
    if not text.startswith(question):
        raise ValueError('Question text does not follow the video placeholder verbatim')
    encoded = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
    if list(encoded['input_ids']) != tail:
        raise ValueError('Prompt question tokens do not re-tokenize identically')
    result = []
    for first, last in spans:
        hits = [start + index for index, (a, b) in enumerate(encoded['offset_mapping']) if a < last and b > first]
        if not hits:
            raise ValueError('Category span maps to no prompt token')
        result.append(hits)
    return result


def query_batch(batch, queries, question, tokenizer):
    import torch

    if tokenizer is None:
        raise ValueError('Category targets require the student tokenizer')
    ids, labels = batch['input_ids'][0].tolist(), batch['labels'][0].tolist()
    prompt_end = next(index for index, label in enumerate(labels) if label != -100)
    live = [index for index, query in enumerate(queries) if active(query)]
    positions = category_positions(tokenizer, ids[:prompt_end], question, [queries[i]['span'] for i in live]) if live else []
    tokens = torch.zeros(1, QUERY_SLOTS, len(ids), dtype=torch.bool)
    for slot, hits in zip(live, positions):
        tokens[0, slot, hits] = True
    def tensor(key, dtype):
        return torch.tensor([[query[key] for query in queries]], dtype=dtype)
    return {'aux_category_tokens': tokens,
            'aux_group_count': tensor('group_count', torch.float32), 'aux_group_count_mask': tensor('group_count_mask', torch.bool),
            'aux_scene_count': tensor('scene_count', torch.float32), 'aux_scene_count_mask': tensor('scene_count_mask', torch.bool),
            'aux_object': tensor('object', torch.float32), 'aux_object_mask': tensor('object_mask', torch.bool)}


def reason_batch(batch, row, tokenizer, audit):
    import torch

    if tokenizer is None or audit is None:
        raise ValueError('Query-token targets require the student tokenizer and the frozen row audit')
    length = int(batch['attention_mask'][0].sum())
    found = reason.parse_tokens(batch['input_ids'][0, :length].tolist(), batch['labels'][0, :length].tolist(),
                                reason.cached_table(tokenizer))
    if len(found) != len(reason.text_queries(row['target'])):
        raise ValueError('Query tokens in the encoded target differ from the target text')
    width = max(1, len(found))
    columns = [list(column) for column in zip(*found)] if found else [[], [], [], []]
    def padded(values, fill, dtype):
        return torch.tensor([values + [fill] * (width - len(values))], dtype=dtype)
    return {'aux_reason_pos': padded(columns[0], -1, torch.long), 'aux_reason_kind': padded(columns[1], -1, torch.long),
            'aux_reason_value': padded(columns[2], 0.0, torch.float32), 'aux_reason_span': padded(columns[3], 0, torch.long),
            'aux_group_times': torch.tensor([reason.displayed_times(audit['temporal_patch_timestamps_seconds'])],
                                            dtype=torch.float32)}


def add_to_batch(batch, row, tokenizer=None, audit=None):
    if '_auxiliary' not in row and '_camera' not in row:
        return batch
    if '_camera' in row:
        # Camera carriers go in first; every later position is computed on the extended row.
        if tokenizer is None:
            raise ValueError('Camera tokens require the student tokenizer')
        from .camera_targets import insert_tokens
        batch = insert_tokens(batch, row['_camera'], tokenizer)
    if '_auxiliary' not in row:
        return batch
    import torch
    record = row['_auxiliary']
    extra = {}
    if 'pose' in record:
        extra.update({'aux_' + key: torch.as_tensor(record[key], dtype=torch.bool if 'mask' in key else torch.float32).unsqueeze(0)
                      for key in ('pose', 'pose_mask', 'depth', 'depth_mask')})
    if 'queries' in record:
        extra.update(query_batch(batch, record['queries'], row['student_input']['question'], tokenizer))
    if record.get('reason'):
        extra.update(reason_batch(batch, row, tokenizer, audit))
    return {**batch, **extra}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--training', required=True)
    parser.add_argument('--receipt-map', required=True, help='JSON qid -> scene receipt pin; missing entries are deferred')
    parser.add_argument('--scene-policy', required=True, help='JSON allowed_groups/excluded_groups from the inherited scene division and benchmark exclusion audit')
    parser.add_argument('--output', required=True)
    parser.add_argument('--depth', action='store_true')
    parser.add_argument('--translation-unit-m', type=float, default=1.)
    args = parser.parse_args()
    training, mapping = json.loads(Path(args.training).read_text()), json.loads(Path(args.receipt_map).read_text())
    policy = json.loads(Path(args.scene_policy).read_text())
    allowed, excluded = set(policy['allowed_groups']), set(policy['excluded_groups'])
    rows = training['rows']
    if len({r['qid'] for r in rows}) != len(rows):
        raise ValueError('Duplicate training qids')
    result = []
    for row in rows:
        # Use the inherited physical-group identity supplied by the audited policy.
        group = policy['row_groups'][row['qid']]
        if group not in allowed or group in excluded:
            item = blank(row)
            item['deferred'] = {'pose': 'Scene policy excludes geometry supervision', 'depth': 'Scene policy excludes geometry supervision'}
        else:
            item = build_row(row, mapping.get(row['qid']), args.translation_unit_m, args.depth)
        result.append(item)
    payload = {'schema': SCHEMA, 'translation_unit_m': args.translation_unit_m,
               'training': pin(args.training), 'receipt_map': pin(args.receipt_map), 'scene_policy': pin(args.scene_policy),
               'rows': result, 'coverage': {name: sum(np.asarray(r[name + '_mask']).any().item() for r in result) for name in ('pose', 'depth')}}
    with Path(args.output).open('x') as handle:
        json.dump(payload, handle, sort_keys=True, allow_nan=False)
    print(json.dumps({'sidecar': pin(args.output), 'rows': len(rows), 'coverage': payload['coverage']}))


if __name__ == '__main__':
    main()
