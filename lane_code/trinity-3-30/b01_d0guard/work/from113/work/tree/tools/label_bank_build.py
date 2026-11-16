"""Build the v2 pose + point-depth label bank on Trinity (never on AWS).

Sources, and nothing else:
- official camera calibration per scene (camera_poses [32, 4, 4] OpenCV camera-to-world in metres,
  intrinsics [32, 3, 3], indices [32] sampled source frames, raster_hw), and the scene receipt
  (gravity_up, coordinate frame, dataset and scene name, checked against the index);
- mesh-raycast first-hit depth (FIRST_HITS.npz: depth [32, H, W] camera z in metres, face_index
  [32, H, W] with -1 for misses), sampled at the anchor frames 1, 3, ..., 31.

A scene without calibration or receipt is deferred with its reason; a scene without first-hit
depth keeps pose labels and gets depth_source 'none' with all-False depth masks. No depth or
intrinsics are ever synthesized. Rebase mode reuses the depth samples of a verified v1 bank (whose
anchors are the same odd frames) for scenes whose v1 depth source was first-hit depth, and
recomputes every pose field from calibration.

The bank carries only opaque tokens; the Trinity-only manifest beside it maps names to tokens and
records every source path and SHA-256.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from student_pilot.camera_config import POSE_ENCODING  # noqa: E402
from student_pilot.camera_targets import (ANCHOR_FRAMES, FRAMES, GROUPS, ORIGIN_FRAME, encode_cameras,  # noqa: E402
                                          encode_gravity)
from student_pilot.compact_label_bank import (ARRAYS, BANK_SCHEMA, MAX_DEPTH_M, MIN_DEPTH_M, frame_set_sha256,  # noqa: E402
                                              read_bank)

DATASET_TOKENS = {'scannet': 'd1', 'scannetppv2': 'd2'}
DATASET_ALIASES = {'scannet': 'scannet', 'scannetv2': 'scannet', 'scannetpp': 'scannetppv2', 'scannetppv2': 'scannetppv2'}
COORDINATE_FRAME = 'source_world_meters_opencv_camera_to_world'
DEFAULT_POINTS_PER_FRAME = 64


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def scene_token(dataset, scene):
    """The training rows' opaque scene token (rung-1 builder convention)."""
    return 'v' + hashlib.sha256(('rung1 scene ' + dataset + '/' + scene).encode()).hexdigest()[:12]


def sample_continuous_depth_points(depth_map, valid_mask, num_points=DEFAULT_POINTS_PER_FRAME, rng=None):
    """Sample `num_points` [0, 1000] x [0, 1000] ((0, 0) top-left) points with depth from one raster.

    Valid pixels are spread evenly over the raster's valid set. Each point is jittered by up to 0.35 px;
    its depth is the bilinear interpolation of its four valid neighbours when they agree within 15%
    (one continuous surface), otherwise the point snaps back to its pixel centre and that pixel's depth.
    """
    if rng is None:
        rng = np.random.default_rng(17)
    depth = np.asarray(depth_map, dtype=np.float64)
    valid = np.asarray(valid_mask, dtype=bool) & np.isfinite(depth) & (depth >= MIN_DEPTH_M) & (depth <= MAX_DEPTH_M)
    height, width = depth.shape
    uv = np.zeros((num_points, 2), dtype=np.float32)
    gt = np.zeros((num_points,), dtype=np.float32)
    mask = np.zeros((num_points,), dtype=bool)
    ys, xs = np.nonzero(valid)
    if ys.size == 0:
        return uv, gt, mask
    if ys.size >= num_points:
        order = rng.permutation(np.linspace(0, ys.size - 1, num_points, dtype=np.int64))
    else:
        order = np.concatenate([np.arange(ys.size, dtype=np.int64), rng.integers(0, ys.size, size=num_points - ys.size)])
    sel_y, sel_x = ys[order].astype(np.float64), xs[order].astype(np.float64)
    jitter_y, jitter_x = rng.uniform(-0.35, 0.35, size=num_points), rng.uniform(-0.35, 0.35, size=num_points)
    for k in range(num_points):
        y0, x0 = int(sel_y[k]), int(sel_x[k])
        yf, xf = np.clip(y0 + jitter_y[k], 0.0, height - 1.0), np.clip(x0 + jitter_x[k], 0.0, width - 1.0)
        yi0, xi0 = int(math.floor(yf)), int(math.floor(xf))
        yi1, xi1 = min(yi0 + 1, height - 1), min(xi0 + 1, width - 1)
        if valid[yi0, xi0] and valid[yi0, xi1] and valid[yi1, xi0] and valid[yi1, xi1]:
            c00, c01, c10, c11 = depth[yi0, xi0], depth[yi0, xi1], depth[yi1, xi0], depth[yi1, xi1]
            low, high = min(c00, c01, c10, c11), max(c00, c01, c10, c11)
            if high - low <= 0.15 * max(low, 0.1):
                wy, wx = yf - yi0, xf - xi0
                value = (1 - wy) * ((1 - wx) * c00 + wx * c01) + wy * ((1 - wx) * c10 + wx * c11)
                uv[k] = [np.clip((xf + 0.5) / width * 1000.0, 0, 1000), np.clip((yf + 0.5) / height * 1000.0, 0, 1000)]
                gt[k], mask[k] = np.clip(value, MIN_DEPTH_M, MAX_DEPTH_M), True
                continue
        uv[k] = [(x0 + 0.5) / width * 1000.0, (y0 + 0.5) / height * 1000.0]
        gt[k], mask[k] = np.clip(depth[y0, x0], MIN_DEPTH_M, MAX_DEPTH_M), True
    return uv, gt, mask


def anchor_depth(first_hits_path, frame_indices):
    """[16, H, W] depth and validity at anchor frames from FIRST_HITS.npz (depth + face_index only)."""
    with np.load(first_hits_path, allow_pickle=False) as data:
        if 'depth' not in data.files or 'face_index' not in data.files:
            raise ValueError('FIRST_HITS lacks depth or face_index')
        for key in ('indices', 'frame_indices'):
            if key in data.files and [int(v) for v in data[key]] != [int(v) for v in frame_indices]:
                raise ValueError('FIRST_HITS frames differ from the calibration frames')
        depth, face = np.asarray(data['depth'], dtype=np.float64), np.asarray(data['face_index'])
    if depth.ndim != 3 or depth.shape[0] != FRAMES or face.shape != depth.shape:
        raise ValueError('FIRST_HITS depth must be [32, H, W] with a matching face_index')
    anchors = list(ANCHOR_FRAMES)
    depth, face = depth[anchors], face[anchors]
    valid = (face >= 0) & np.isfinite(depth) & (depth >= MIN_DEPTH_M) & (depth <= MAX_DEPTH_M)
    return np.where(valid, depth, 0.0), valid


def scene_cameras(entry):
    """Calibration and receipt of one scene, checked against the index entry; raises with a reason."""
    receipt_path = entry.get('receipt_path')
    if not receipt_path or not Path(receipt_path).is_file():
        raise ValueError('receipt missing')
    receipt = json.loads(Path(receipt_path).read_text())
    if DATASET_ALIASES.get(str(receipt.get('dataset'))) != entry['dataset'] or receipt.get('scene_name') != entry['scene']:
        raise ValueError('receipt names another scene')
    if receipt.get('coordinate_frame') != COORDINATE_FRAME:
        raise ValueError('receipt coordinate frame is not OpenCV camera-to-world metres')
    up = receipt.get('gravity_up')
    if not isinstance(up, list) or len(up) != 3:
        raise ValueError('receipt gravity_up missing')
    calibration = entry.get('calibration_path') or (receipt.get('calibration') or {}).get('path')
    if not calibration or not Path(calibration).is_file():
        raise ValueError('calibration missing')
    with np.load(calibration, allow_pickle=False) as cal:
        if not {'camera_poses', 'intrinsics', 'indices', 'raster_hw'} <= set(cal.files):
            raise ValueError('calibration lacks poses, intrinsics, indices or raster size')
        poses, intrinsics = np.asarray(cal['camera_poses'], np.float64), np.asarray(cal['intrinsics'], np.float64)
        indices, raster = [int(v) for v in cal['indices']], [int(v) for v in cal['raster_hw']]
    if poses.shape != (FRAMES, 4, 4) or intrinsics.shape != (FRAMES, 3, 3) or len(indices) != FRAMES or len(raster) != 2:
        raise ValueError('calibration arrays have the wrong shapes')
    valid = np.isfinite(poses).all(axis=(1, 2)) & np.isfinite(intrinsics).all(axis=(1, 2))
    return {'poses': poses, 'intrinsics': intrinsics, 'indices': indices, 'raster_hw': raster, 'valid': valid,
            'gravity_up': np.asarray(up, dtype=np.float64), 'calibration_path': calibration, 'receipt_path': receipt_path}


def index_entries(index_path, first_hits_dir=None):
    """Scene entries {dataset (native), scene, receipt_path, calibration_path, first_hits_path} from an index."""
    raw = json.loads(Path(index_path).read_text())
    entries = []
    if isinstance(raw.get('scenes'), list):
        for item in raw['scenes']:
            entries.append({'dataset': DATASET_ALIASES[item['dataset']], 'scene': item['scene'],
                            'receipt_path': item.get('receipt_path'), 'calibration_path': item.get('calibration_path'),
                            'first_hits_path': item.get('first_hits_path')})
    else:
        for item in raw.get('records', []):
            if item.get('status') != 'READY':
                continue
            dataset, _, scene = str(item['scene_key']).partition('__')
            receipt = item.get('scene_receipt')
            entries.append({'dataset': DATASET_ALIASES[dataset], 'scene': scene,
                            'receipt_path': receipt.get('path') if isinstance(receipt, dict) else receipt,
                            'calibration_path': item.get('calibration_path'), 'first_hits_path': item.get('first_hits_path')})
    for entry in entries:
        if first_hits_dir is not None:
            native = entry['dataset']
            entry['first_hits_path'] = str(Path(first_hits_dir) / f"{native}__{entry['scene']}" / 'FIRST_HITS.npz')
    return entries


def v1_depth(v1_path):
    """{(native dataset, scene): (uv, gt, mask)} of a v1 bank's first-hit scenes (frames 1, 3, ..., 31)."""
    with np.load(v1_path, allow_pickle=False) as data:
        if str(data['schema'].item()) != 'student_pilot/compact_label_bank/v1':
            raise ValueError('Rebase needs a v1 bank')
        result = {}
        for i, (dataset, scene, source) in enumerate(zip(data['datasets'].tolist(), data['scenes'].tolist(),
                                                         data['depth_sources'].tolist())):
            if source == 'first_hits':
                result[(DATASET_ALIASES[dataset], scene)] = (data['point_depth_uv'][i], data['point_depth_gt'][i],
                                                             data['point_depth_mask'][i])
    return result


def build(entries, output, num_points=DEFAULT_POINTS_PER_FRAME, seed=17, rebase_from=None):
    output = Path(output)
    if output.exists():
        raise ValueError('The output bank already exists')
    rebased = v1_depth(rebase_from) if rebase_from else None
    columns = {key: [] for key in ('dataset_tokens', 'scene_tokens', 'frame_indices', 'frame_set_sha256', 'camera',
                                   'camera_mask', 'trajectory_scale', 'gravity', 'gravity_mask', 'depth_source',
                                   'point_depth_uv', 'point_depth_gt', 'point_depth_mask')}
    scenes, deferred = [], []
    for entry in entries:
        name = f"{entry['dataset']}/{entry['scene']}"
        try:
            cams = scene_cameras(entry)
        except ValueError as error:
            deferred.append({'scene': name, 'reason': str(error)})
            continue
        camera, mask, scale = encode_cameras(cams['poses'], cams['intrinsics'], cams['raster_hw'], cams['valid'])
        gravity, gravity_ok = encode_gravity(cams['poses'], cams['gravity_up'])
        gravity_ok = bool(gravity_ok and cams['valid'][ORIGIN_FRAME])
        uv = np.zeros((GROUPS, num_points, 2), np.float16)
        gt = np.zeros((GROUPS, num_points), np.float16)
        depth_mask = np.zeros((GROUPS, num_points), bool)
        source, source_record = 'none', None
        if rebased is not None:
            if (entry['dataset'], entry['scene']) in rebased:
                old_uv, old_gt, old_mask = rebased[(entry['dataset'], entry['scene'])]
                if old_uv.shape[1] < num_points:
                    raise ValueError('The v1 bank has fewer points per frame than requested')
                uv, gt, depth_mask = old_uv[:, :num_points], old_gt[:, :num_points], old_mask[:, :num_points]
                source, source_record = 'first_hits', {'v1_bank': str(rebase_from), 'v1_bank_sha256': sha256_file(rebase_from)}
        elif entry.get('first_hits_path') and Path(entry['first_hits_path']).is_file():
            depth, valid = anchor_depth(entry['first_hits_path'], cams['indices'])
            rng = np.random.default_rng(int(hashlib.sha256(name.encode()).hexdigest()[:8], 16) ^ int(seed))
            for g in range(GROUPS):
                u, d, m = sample_continuous_depth_points(depth[g], valid[g], num_points, rng)
                uv[g], gt[g], depth_mask[g] = u.astype(np.float16), d.astype(np.float16), m
            source = 'first_hits'
            source_record = {'path': entry['first_hits_path'], 'sha256': sha256_file(entry['first_hits_path'])}
        token = (DATASET_TOKENS[entry['dataset']], scene_token(entry['dataset'], entry['scene']))
        for key, value in (('dataset_tokens', token[0]), ('scene_tokens', token[1]), ('frame_indices', cams['indices']),
                           ('frame_set_sha256', frame_set_sha256(cams['indices'])), ('camera', camera.astype(np.float32)),
                           ('camera_mask', mask), ('trajectory_scale', np.float32(scale)),
                           ('gravity', gravity.astype(np.float32)), ('gravity_mask', gravity_ok), ('depth_source', source),
                           ('point_depth_uv', uv), ('point_depth_gt', gt), ('point_depth_mask', depth_mask)):
            columns[key].append(value)
        scenes.append({'scene': name, 'dataset_token': token[0], 'scene_token': token[1], 'depth_source': source,
                       'depth': source_record, 'calibration': {'path': cams['calibration_path'], 'sha256': sha256_file(cams['calibration_path'])},
                       'receipt': {'path': cams['receipt_path'], 'sha256': sha256_file(cams['receipt_path'])},
                       'pose_groups': int(mask.sum()), 'depth_points': int(depth_mask.sum())})
    if not scenes:
        raise ValueError('No scene could be labelled')
    arrays = {'schema': np.array(BANK_SCHEMA), 'pose_encoding': np.array(POSE_ENCODING),
              'translation_unit_m': np.array(1.0), 'origin_frame': np.array(ORIGIN_FRAME),
              'anchor_frames': np.array(ANCHOR_FRAMES, dtype=np.int64),
              'dataset_tokens': np.array(columns['dataset_tokens'], dtype='<U8'),
              'scene_tokens': np.array(columns['scene_tokens'], dtype='<U16'),
              'frame_indices': np.array(columns['frame_indices'], dtype=np.int64),
              'frame_set_sha256': np.array(columns['frame_set_sha256'], dtype='<U64'),
              'camera': np.stack(columns['camera']), 'camera_mask': np.stack(columns['camera_mask']),
              'trajectory_scale': np.array(columns['trajectory_scale'], dtype=np.float32),
              'gravity': np.stack(columns['gravity']), 'gravity_mask': np.array(columns['gravity_mask'], dtype=bool),
              'depth_source': np.array(columns['depth_source'], dtype='<U16'),
              'point_depth_uv': np.stack(columns['point_depth_uv']).astype(np.float16),
              'point_depth_gt': np.stack(columns['point_depth_gt']).astype(np.float16),
              'point_depth_mask': np.stack(columns['point_depth_mask'])}
    assert set(arrays) == set(ARRAYS)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as handle:
        np.savez_compressed(handle, **arrays)
    read_bank(output)
    manifest = {'schema': BANK_SCHEMA, 'trinity_only': True, 'path': str(output), 'sha256': sha256_file(output),
                'bytes': output.stat().st_size, 'num_scenes': len(scenes), 'num_points_per_frame': num_points, 'seed': seed,
                'rebased_from_v1': str(rebase_from) if rebase_from else None, 'pose_encoding': POSE_ENCODING,
                'origin_frame': ORIGIN_FRAME, 'anchor_frames': list(ANCHOR_FRAMES),
                'dataset_tokens': DATASET_TOKENS, 'depth_source_counts': {s: sum(x['depth_source'] == s for x in scenes)
                                                                         for s in ('first_hits', 'none')},
                'scenes': scenes, 'deferred': deferred}
    manifest_path = output.with_suffix('.manifest.json')
    with manifest_path.open('x') as handle:
        handle.write(json.dumps(manifest, indent=1) + '\n')
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scene-index', required=True)
    parser.add_argument('--first-hits-dir', default=None, help='Directory of <dataset>__<scene>/FIRST_HITS.npz')
    parser.add_argument('--rebase-v1-bank', default=None, help='Reuse first-hit depth samples of a verified v1 bank')
    parser.add_argument('--num-points-per-frame', type=int, default=DEFAULT_POINTS_PER_FRAME)
    parser.add_argument('--seed', type=int, default=17)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    if args.rebase_v1_bank and args.first_hits_dir:
        raise ValueError('Choose one depth source: --first-hits-dir or --rebase-v1-bank')
    manifest = build(index_entries(args.scene_index, args.first_hits_dir), args.output, args.num_points_per_frame,
                     args.seed, args.rebase_v1_bank)
    print(json.dumps({key: manifest[key] for key in ('path', 'sha256', 'bytes', 'num_scenes', 'depth_source_counts')}
                     | {'deferred': len(manifest['deferred'])}))


if __name__ == '__main__':
    main()
