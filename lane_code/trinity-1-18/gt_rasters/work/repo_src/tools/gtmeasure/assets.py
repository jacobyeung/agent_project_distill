# Adapted from tools/vstigen/assets.py at e2f387e (vstigen-membership-v4-20260922).
from dataclasses import dataclass
from pathlib import Path
import re

import numpy as np

from collector.gt_scene_assets import ASSET_KEYS, validate_dense
from .mesh_membership import SPARSE_KEYS, instance_faces, validate_memberships
from .conventions import box_corners, camera_points
from .io import read_json, verify_pin


EXCLUDED = {'', 'wall', 'floor', 'ceiling', 'object', 'other', 'unknown', '(null)', 'remove'}


@dataclass
class Scene:
    receipt_path: Path
    receipt: dict
    arrays: dict
    mesh: dict
    objects: list

    def observations(self, frame_index):
        if type(frame_index) is not int or not 1 <= frame_index <= 32:
            raise ValueError('frame index must be a selected one-based slot')
        slot = frame_index - 1
        pose, intrinsic = self.arrays['camera_poses'][slot], self.arrays['intrinsics'][slot]
        height, width = self.arrays['mask'].shape[1:]
        scale = np.asarray([width, height])
        result = []
        for obj in self.objects:
            if obj['label'] in EXCLUDED or not len(obj['vertices']):
                continue
            corners = camera_points(obj['corners'], pose)
            if np.any(corners[:, 2] <= .05):
                continue
            projected = corners @ intrinsic.T
            uv = projected[:, :2] / projected[:, 2, None]
            lo, hi = uv.min(axis=0), uv.max(axis=0)
            if np.any(hi < 0) or np.any(lo >= scale):
                continue
            points = camera_points(obj['vertices'], pose)
            homogeneous = points @ intrinsic.T
            positive = points[:, 2] > .05
            pixels = homogeneous[:, :2] / np.where(positive, homogeneous[:, 2], 1)[:, None]
            keep = positive & np.all(pixels >= 0, axis=1) & np.all(pixels < scale, axis=1)
            xy, z = pixels[keep].astype(np.int64), points[keep, 2]
            if not len(xy):
                continue
            x, y = xy.T
            world_gap = np.linalg.norm(obj['vertices'][keep] - self.arrays['pts3d_world'][slot, y, x], axis=1)
            visible = self.arrays['mask'][slot, y, x] & (np.abs(z - self.arrays['depth_z'][slot, y, x]) <= .15) & (world_gap <= .15)
            visible_pixels = len(np.unique(y[visible] * width + x[visible]))
            if visible_pixels < max(3, int(width * height * .0001)):
                continue
            bounds = np.stack([np.maximum(lo - 1, 0) / scale, np.minimum(hi + 1, scale) / scale])
            screen = np.column_stack([bounds, np.zeros(2)])
            result.append({'id': obj['id'], 'label': obj['label'], 'camera_bounds': corners,
                           'screen_bounds': screen, 'visible_pixels': visible_pixels})
        return result

    def student_input(self, question, options):
        video, frames = self.receipt['video'], self.receipt['frames']
        fps, total = video['fps'], video['decoded_frame_count']
        indices = [row['ordinal'] for row in frames]
        timestamps = [row['timestamp_sec'] for row in frames]
        if (not np.isfinite(fps) or fps <= 0 or type(total) is not int or total <= indices[-1]
                or not np.allclose(timestamps, np.asarray(indices) / fps, rtol=1e-9, atol=1e-9)):
            raise ValueError('RGB timing metadata disagrees with video receipt')
        return {'fps': fps, 'frame_indices': indices,
                'frames': [{'path': row['path'], 'sha256': row['sha256']} for row in frames],
                'options': options, 'question': question, 'timestamps': timestamps, 'total_num_frames': total}


def read_arrays(spec):
    with np.load(verify_pin(spec), allow_pickle=False) as stored:
        return {key: stored[key] for key in stored.files}


def receipt_candidates(scene, job_roots, registry_paths=()):
    candidates = [Path(root) / scene['scene_name'] / 'assets/scene_receipt.json' for root in job_roots]
    for registry in registry_paths:
        for spec in read_json(registry)['receipts']:
            path = Path(spec['path'])
            if path.parent.parent.name == scene['scene_name']:
                verify_pin(spec)
                candidates.append(path)
    return list(dict.fromkeys(candidates))


def safe_scene(row):
    for key in ('dataset', 'scene_name'):
        if not isinstance(row.get(key), str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', row[key]):
            raise ValueError('invalid corpus-qualified scene identity')
    return row['dataset'], row['scene_name']


def load_scene(path):
    path = Path(path).resolve()
    receipt = read_json(path)
    dataset, name = safe_scene(receipt)
    if (receipt.get('schema') != 'r1313-scene-assets-v1' or receipt.get('round') != 1313
            or receipt.get('runtime_scene_id') != dataset + '__' + name
            or receipt.get('coordinate_frame') != 'source_world_meters_opencv_camera_to_world'
            or receipt.get('gravity_up') != [0, 0, 1]
            or receipt.get('geometry_source') != 'official_aligned_pose_intrinsic_mesh_gt_valid_support'):
        raise ValueError('unsupported official scene receipt')
    frames = receipt['frames']
    ordinals = [row['ordinal'] for row in frames]
    if (receipt.get('image_count') != 32 or len(frames) != 32
            or [row['stem'] for row in frames] != receipt['selected_frames']
            or any(type(value) is not int or value < 0 for value in ordinals)
            or sorted(set(ordinals)) != ordinals):
        raise ValueError('selected frames must bind exactly 32 ordered RGB slots')
    for key in ASSET_KEYS:
        if key not in ('dense', 'calibration', 'instance_mesh'):
            verify_pin(receipt[key])
    for frame in frames:
        verify_pin(frame)
    arrays = read_arrays(receipt['dense'])
    validate_dense(arrays, frames)
    calibration = read_arrays(receipt['calibration'])
    if (set(calibration) != {'camera_poses', 'intrinsics', 'indices', 'raster_hw'}
            or any(not np.array_equal(calibration[key], arrays[key]) for key in ('camera_poses', 'intrinsics', 'indices'))
            or calibration['raster_hw'].tolist() != list(arrays['mask'].shape[1:])):
        raise ValueError('calibration and dense selected-frame binding disagree')
    if np.any(arrays['intrinsics'][:, (0, 1), (0, 1)] <= 0):
        raise ValueError('camera focal lengths must be positive')
    alignment = read_json(receipt['alignment']['path'])
    if (alignment.get('validated_slots') != 32 or alignment.get('pose_field') != 'aligned_pose'
            or alignment.get('estimated_geometry_used') is not False
            or [row['ordinal'] for row in alignment['frames']] != ordinals):
        raise ValueError('official RGB/pose alignment is incomplete')
    groups = read_json(receipt['instances']['path'])['segGroups']
    mesh = read_arrays(receipt['instance_mesh'])
    legacy = {'vertices_world', 'faces', 'face_instance_ids'}
    sparse = {'vertices_world', 'faces'} | SPARSE_KEYS
    if set(mesh) not in (legacy, sparse):
        raise ValueError('unexpected instance mesh schema')
    vertices, faces = mesh['vertices_world'], mesh['faces']
    if (vertices.ndim != 2 or vertices.shape[1] != 3 or not np.isfinite(vertices).all()
            or faces.ndim != 2 or faces.shape[1] != 3 or faces.dtype.kind not in 'iu'
            or np.any(faces < 0) or np.any(faces >= len(vertices))):
        raise ValueError('invalid instance mesh geometry')
    annotations = read_json(receipt['annotations']['path'])['instances']
    annotation_ids = {int(row['instance_id']) for row in annotations}
    if len(annotation_ids) != len(annotations):
        raise ValueError('duplicate annotation instance identity')
    if set(mesh) == sparse:
        validate_memberships(mesh, annotation_ids)
    else:
        mesh['instance_ids'] = mesh['face_instance_ids']
        if len(faces) != len(mesh['instance_ids']) or not set(mesh['instance_ids'][mesh['instance_ids'] >= 0].tolist()).issubset(annotation_ids):
            raise ValueError('instance mesh and annotations disagree')
    ids = [group.get('objectId', group['id']) for group in groups]
    if any(type(iid) is not int or iid < 0 for iid in ids) or len(ids) != len(set(ids)) or set(ids) != annotation_ids:
        raise ValueError('invalid, duplicate, or incomplete object identity census')
    annotation_labels = {row['instance_id']: row['label'].lower().strip() for row in annotations}
    objects = []
    for group in sorted(groups, key=lambda item: item.get('objectId', item['id'])):
        iid, label = group.get('objectId', group['id']), group['label'].lower().strip()
        if annotation_labels[iid] != label:
            raise ValueError('instance and annotation labels disagree')
        if label in EXCLUDED - {'floor'} or re.search(r'[\d\n\r\[\]{}?]', label):
            continue
        selected = instance_faces(mesh, iid)
        points = vertices[np.unique(faces[selected])]
        corners = box_corners(group['obb'])
        local = (points - np.asarray(group['obb']['centroid'])) @ np.asarray(group['obb']['normalizedAxes']).reshape(3, 3).T
        if np.any(np.abs(local) > np.asarray(group['obb']['axesLengths']) + .02):
            raise ValueError(f'official half-extent box does not enclose instance {iid}')
        objects.append({'id': iid, 'label': label, 'corners': corners, 'vertices': points,
                        'triangles': vertices[faces[selected]].astype(np.float64), 'obb': group['obb'],
                        'face_indices': selected.tolist()})
    return Scene(path, receipt, arrays, mesh, objects)
