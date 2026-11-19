"""Scene-level label bank for pose, gravity, scale and point-depth supervision: the trainer-side loader.

The bank (`.npz`, schema v2) is built on Trinity by tools/label_bank_build.py from mesh-raycast
first-hit depth and official camera poses only. It holds opaque dataset and scene tokens (the same
tokens the training rows carry), never source names or paths. Per scene it stores:

- frame_indices [32] and frame_set_sha256: the 32 sampled source frames the labels describe;
- camera [16, 9], camera_mask [16], trajectory_scale: group g's anchor frame 2g+1 relative to frame 0;
- gravity [3], gravity_mask: world up in the frame-0 camera;
- point_depth_uv [16, K, 2] (float16, [0, 1000] grid, (0, 0) top-left), point_depth_gt [16, K] (float16,
  metres along the optical axis), point_depth_mask [16, K], and depth_source ('first_hits' or 'none').

A row receives labels only when its (dataset, scene) tokens are in the bank and its own 32 frame
indices hash to the scene's frame set; every other row is masked out and counted, never filled in.
"""
import hashlib
import json
import math

import numpy as np

from .camera_config import POSE_ENCODING
from .camera_targets import ANCHOR_FRAMES, FRAMES, GROUPS, ORIGIN_FRAME, POSE_ONLY_CATEGORY, check_record
from .point_depth_head import point_depth_enabled

BANK_SCHEMA = 'student_pilot/compact_label_bank/v2'
DEPTH_SOURCES = ('first_hits', 'none')
MIN_DEPTH_M = 0.05
MAX_DEPTH_M = 25.0
ARRAYS = ('schema', 'pose_encoding', 'translation_unit_m', 'origin_frame', 'anchor_frames', 'dataset_tokens',
          'scene_tokens', 'frame_indices', 'frame_set_sha256', 'camera', 'camera_mask', 'trajectory_scale', 'gravity',
          'gravity_mask', 'depth_source', 'point_depth_uv', 'point_depth_gt', 'point_depth_mask')


def frame_set_sha256(frame_indices):
    """SHA-256 of the canonical JSON list of the 32 sampled source-frame indices."""
    values = [int(v) for v in frame_indices]
    if len(values) != FRAMES or any(b <= a for a, b in zip(values, values[1:])):
        raise ValueError('A frame set must hold 32 increasing frame indices')
    return hashlib.sha256(json.dumps(values, separators=(',', ':')).encode()).hexdigest()


def read_bank(npz_path):
    """Load and validate a v2 bank; returns a dict of arrays. Refuses any other schema or convention."""
    with np.load(npz_path, allow_pickle=False) as data:
        if set(data.files) != set(ARRAYS):
            raise ValueError('Label bank arrays differ from schema v2')
        bank = {key: data[key] for key in ARRAYS}
    return validate_bank(bank)


def validate_bank(bank):
    if (str(bank['schema'].item()) != BANK_SCHEMA or str(bank['pose_encoding'].item()) != POSE_ENCODING
            or float(bank['translation_unit_m'].item()) != 1.0 or int(bank['origin_frame'].item()) != ORIGIN_FRAME
            or tuple(int(v) for v in bank['anchor_frames']) != ANCHOR_FRAMES):
        raise ValueError('Label bank schema, pose encoding, unit, origin or anchor frames mismatch')
    n = bank['scene_tokens'].shape[0]
    k = bank['point_depth_uv'].shape[2] if bank['point_depth_uv'].ndim == 4 else -1
    shapes = {'dataset_tokens': (n,), 'frame_indices': (n, FRAMES), 'frame_set_sha256': (n,), 'camera': (n, GROUPS, 9),
              'camera_mask': (n, GROUPS), 'trajectory_scale': (n,), 'gravity': (n, 3), 'gravity_mask': (n,),
              'depth_source': (n,), 'point_depth_uv': (n, GROUPS, k, 2), 'point_depth_gt': (n, GROUPS, k),
              'point_depth_mask': (n, GROUPS, k)}
    if n < 1 or k < 1 or any(bank[key].shape != shape for key, shape in shapes.items()):
        raise ValueError('Label bank array shapes are inconsistent')
    keys = list(zip(bank['dataset_tokens'].tolist(), bank['scene_tokens'].tolist()))
    if len(set(keys)) != n:
        raise ValueError('Label bank scene tokens repeat')
    for i in range(n):
        if frame_set_sha256(bank['frame_indices'][i]) != str(bank['frame_set_sha256'][i]):
            raise ValueError('Label bank frame-set hash differs from its frame indices')
        source = str(bank['depth_source'][i])
        if source not in DEPTH_SOURCES:
            raise ValueError('Label bank depth source is not first-hit raycast depth: ' + source)
        depth_mask = bank['point_depth_mask'][i]
        if source == 'none' and depth_mask.any():
            raise ValueError('Label bank holds depth labels without a first-hit source')
        gt = bank['point_depth_gt'][i].astype(np.float32)[depth_mask]
        uv = bank['point_depth_uv'][i].astype(np.float32)[depth_mask]
        if (not np.isfinite(gt).all() or np.any(gt < MIN_DEPTH_M * 0.999) or np.any(gt > MAX_DEPTH_M * 1.001)
                or not np.isfinite(uv).all() or np.any(uv < 0) or np.any(uv > 1000)):
            raise ValueError('Label bank depth labels fall outside their contract')
        if bool(bank['gravity_mask'][i]) and not math.isclose(float(np.linalg.norm(bank['gravity'][i])), 1.0, abs_tol=1e-3):
            raise ValueError('Label bank gravity must be a unit vector')
        check_record({'camera': bank['camera'][i].astype(np.float64), 'camera_mask': bank['camera_mask'][i],
                      'trajectory_scale': float(bank['trajectory_scale'][i]), 'metric': True})
    return bank


def row_key(row):
    dataset, scene = row.get('dataset'), row.get('scene')
    return (dataset, scene) if isinstance(dataset, str) and isinstance(scene, str) else None


def sample_depth(bank, index, row, k_want):
    """Point-depth queries of an N-frame pose-only sample from its scene's bank entry.

    Sample group j fuses the sample's frames 2j and 2j + 1 and, like every row, describes its second frame. The bank
    holds first-hit depth at the scene's 0-based frames 1, 3, ..., 31 (group g describes frame 2g + 1), so group j takes
    bank group p // 2 when its second frame sits at an odd scene position p, and no depth otherwise."""
    positions = row['pose_sample']['positions']
    indices = (row.get('student_input') or {}).get('frame_indices')
    frames = [int(value) for value in bank['frame_indices'][index]]
    if not isinstance(indices, list) or len(indices) != len(positions) or any(
            type(p) is not int or not 0 <= p < FRAMES or frames[p] != indices[k] for k, p in enumerate(positions)):
        raise ValueError("A pose-only sample's frames differ from its scene's bank frames")
    uv = np.zeros((GROUPS, k_want, 2), dtype=np.float32)
    depth = np.zeros((GROUPS, k_want), dtype=np.float32)
    mask = np.zeros((GROUPS, k_want), dtype=bool)
    for group in range(len(positions) // 2):
        position = positions[2 * group + 1]
        if position % 2:
            uv[group] = bank['point_depth_uv'][index, position // 2, :k_want]
            depth[group] = bank['point_depth_gt'][index, position // 2, :k_want]
            mask[group] = bank['point_depth_mask'][index, position // 2, :k_want]
    return {'uv': uv.tolist(), 'depth': depth.tolist(), 'mask': mask.tolist()}


def load_bank_for_rows(npz_path, rows, cfg):
    """Per-row camera records in training order, plus the label audit (counts only, no names).

    Rows whose scene is absent from the bank, or whose frames differ from the bank's frame set,
    receive all-False masks: they contribute no head loss and no head gradient. Under Cambrian-P routing
    (cfg row_routing) question rows receive all-False masks too, and pose-only samples carry the bank's depth queries
    at their frames (sample_depth)."""
    from .camera_config import CAMBRIAN_P_ROUTING
    bank = read_bank(npz_path)
    cambrian = cfg.get('row_routing') == CAMBRIAN_P_ROUTING
    lookup = {key: i for i, key in enumerate(zip(bank['dataset_tokens'].tolist(), bank['scene_tokens'].tolist()))}
    want_depth = point_depth_enabled(cfg.get('point_depth'))
    k_want = min(bank['point_depth_uv'].shape[2], int(cfg['point_depth']['num_points_per_frame'])) if want_depth else 0
    zero = {'camera': np.zeros((GROUPS, 9)).tolist(), 'camera_mask': [False] * GROUPS, 'trajectory_scale': 0.0,
            'lm_weight': 1.0, 'gravity': [0.0, 0.0, 0.0], 'gravity_mask': False}
    if want_depth:
        zero['point_depth'] = {'uv': np.zeros((GROUPS, k_want, 2)).tolist(), 'depth': np.zeros((GROUPS, k_want)).tolist(),
                               'mask': np.zeros((GROUPS, k_want), dtype=bool).tolist()}
    audit = {'rows': len(rows), 'pose_rows': 0, 'gravity_rows': 0, 'depth_rows': 0, 'scene_not_in_bank': 0,
             'frame_set_missing': 0, 'frame_set_mismatch': 0, 'scenes_in_bank': len(lookup), 'scenes_used': 0}
    if cambrian:
        audit.update(row_routing=CAMBRIAN_P_ROUTING, question_rows_lm_only=0, pose_depth_groups=0)
    used, result = set(), []
    for row in rows:
        pose_only = row.get('category') == POSE_ONLY_CATEGORY
        if pose_only and 'pose_sample' in row:
            # An N-frame pose-only sample carries its own GT pose targets (pose_samples.check_sample); its depth
            # queries come from the bank under Cambrian-P routing and are absent otherwise.
            from .pose_samples import check_sample
            entry = check_sample(row, cfg.get('max_groups', GROUPS))
            groups = len(entry['camera'])
            if groups > GROUPS:
                entry['max_groups'] = cfg['max_groups']
            if want_depth:
                entry['point_depth'] = zero['point_depth']
                all_frames = row['pose_sample'].get('temporal_grouping') == 'fused_pairs_all_frames'
                if all_frames or 'point_depth' in cfg.get('freeze_modules', []):
                    if groups > GROUPS:
                        entry['point_depth'] = {'uv': np.zeros((groups, k_want, 2)).tolist(),
                                                'depth': np.zeros((groups, k_want)).tolist(),
                                                'mask': np.zeros((groups, k_want), dtype=bool).tolist()}
                        entry['frozen_depth'] = True
                elif groups > GROUPS:
                    raise ValueError('Long recording rows require frozen point_depth with empty targets')
                # A frozen depth branch consumes no depth labels. Its empty
                # targets retain the tensor schema while pose-only rows may
                # use frames outside the bank's original 32-frame snapshot.
                if cambrian and not all_frames and 'point_depth' not in cfg.get('freeze_modules', []):
                    key = row_key(row)
                    if key not in lookup:
                        raise ValueError('A pose-only sample has no bank entry for its depth queries')
                    entry['point_depth'] = sample_depth(bank, lookup[key], row, k_want)
                    groups = int(np.asarray(entry['point_depth']['mask']).any(axis=1).sum())
                    audit['pose_depth_groups'] += groups
                    audit['depth_rows'] += bool(groups)
                    used.add(lookup[key])
            audit['pose_rows'] += 1
            audit['gravity_rows'] += entry['gravity_mask']
            audit['pose_only_samples'] = audit.get('pose_only_samples', 0) + 1
            result.append(entry)
            continue
        if cambrian and not pose_only:
            # Cambrian-P: question rows carry no camera tokens and train the next-token loss alone.
            audit['question_rows_lm_only'] += 1
            result.append(dict(zero))
            continue
        key = row_key(row)
        index = lookup.get(key) if key is not None else None
        reason = None
        if index is None:
            reason = 'scene_not_in_bank'
        else:
            indices = (row.get('student_input') or {}).get('frame_indices')
            if not isinstance(indices, list) or len(indices) != FRAMES:
                reason = 'frame_set_missing'
            elif frame_set_sha256(indices) != str(bank['frame_set_sha256'][index]):
                reason = 'frame_set_mismatch'
        if reason is not None:
            if pose_only:
                raise ValueError('A pose-only row has no matching camera labels in the bank: ' + reason)
            audit[reason] += 1
            result.append(dict(zero))
            continue
        mask = bank['camera_mask'][index]
        if pose_only and not mask.any():
            raise ValueError('A pose-only row has no camera supervision in the bank')
        entry = {'camera': bank['camera'][index].astype(np.float64).tolist(), 'camera_mask': mask.tolist(),
                 'trajectory_scale': float(bank['trajectory_scale'][index]), 'lm_weight': 0.0 if pose_only else 1.0,
                 'gravity': bank['gravity'][index].astype(np.float64).tolist(),
                 'gravity_mask': bool(bank['gravity_mask'][index])}
        audit['pose_rows'] += bool(mask.any())
        audit['gravity_rows'] += entry['gravity_mask']
        if want_depth:
            depth_mask = bank['point_depth_mask'][index, :, :k_want]
            entry['point_depth'] = {'uv': bank['point_depth_uv'][index, :, :k_want].astype(np.float32).tolist(),
                                    'depth': bank['point_depth_gt'][index, :, :k_want].astype(np.float32).tolist(),
                                    'mask': depth_mask.tolist()}
            audit['depth_rows'] += bool(depth_mask.any())
        used.add(index)
        result.append(entry)
    audit['scenes_used'] = len(used)
    if not audit['pose_rows'] and not audit['depth_rows']:
        raise ValueError('Camera supervision is enabled but no training row matched a supervised bank scene')
    return result, audit
