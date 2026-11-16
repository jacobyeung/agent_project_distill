"""Answer-free, training-scene-only asset authentication."""
from __future__ import annotations
import hashlib
import json
import os
import re
from pathlib import Path
import numpy as np

DATA_ROOT = Path('/data2/jjyeung/agent_project_data/vsi_distill_training_20260917')
SCHEMA = 'r1313-scene-assets-v1'
ARRAY_KEYS = {'pts3d_world', 'depth_z', 'intrinsics', 'conf', 'mask', 'camera_poses', 'indices'}
ASSET_KEYS = ('video', 'dense', 'calibration', 'instances', 'instance_mesh', 'annotations',
              'alignment', 'source_provenance')


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def data_path(path):
    resolved = Path(path).resolve()
    if not resolved.is_relative_to(DATA_ROOT):
        raise ValueError(f'asset/output is outside training DATA: {resolved}')
    return resolved


def scene_id(dataset, scene):
    for value in (dataset, scene):
        if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', value):
            raise ValueError('scene identity must be a corpus-qualified source basename')
    return dataset + '__' + scene


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha(path), 'size_bytes': path.stat().st_size}


def verify(spec, *, prepared=True):
    path = data_path(spec['path']) if prepared else Path(spec['path']).resolve()
    if not path.is_file() or Path(spec['path']).is_symlink():
        raise ValueError(f'asset must be a regular, non-symlink file: {path}')
    if path.stat().st_size != spec.get('size_bytes', spec.get('bytes')) or sha(path) != spec['sha256']:
        raise ValueError(f'asset digest/size drift: {path}')
    return path


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    path = data_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())
    return pin(path)


def save_arrays(path, **arrays):
    path = data_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        np.savez_compressed(handle, **arrays)
        handle.flush()
        os.fsync(handle.fileno())
    return pin(path)


def save_mask(path, mask):
    path = data_path(path)
    if path.exists():
        if not np.array_equal(np.load(path, allow_pickle=False), mask):
            raise ValueError('immutable mask collision')
    else:
        with path.open('xb') as handle:
            np.save(handle, mask)
            handle.flush()
            os.fsync(handle.fileno())


def load_arrays(spec):
    with np.load(verify(spec), allow_pickle=False) as stored:
        return {key: stored[key] for key in stored.files}


def validate_dense(data, frames):
    if set(data) != ARRAY_KEYS:
        raise ValueError('unexpected GT dense array census')
    mask = data['mask']
    if mask.ndim != 3 or mask.shape[0] != 32 or mask.dtype != np.bool_:
        raise ValueError('GT support must be a boolean 32-frame raster')
    shape = mask.shape
    if data['pts3d_world'].shape != (*shape, 3) or any(data[k].shape != shape for k in ('depth_z', 'conf')):
        raise ValueError('GT dense raster shape mismatch')
    if data['indices'].tolist() != [row['ordinal'] for row in frames]:
        raise ValueError('GT dense/RGB ordinals disagree')
    poses, intrinsics = data['camera_poses'], data['intrinsics']
    if poses.shape != (32, 4, 4) or intrinsics.shape != (32, 3, 3):
        raise ValueError('GT camera array shape mismatch')
    if not np.isfinite(poses).all() or not np.isfinite(intrinsics).all():
        raise ValueError('nonfinite official camera')
    if not np.allclose(poses[:, 3], [0, 0, 0, 1]) or not np.allclose(poses[:, :3, :3].transpose(0, 2, 1) @ poses[:, :3, :3], np.eye(3), atol=1e-4) or not np.allclose(np.linalg.det(poses[:, :3, :3]), 1, atol=1e-4):
        raise ValueError('aligned_pose is not a proper camera-to-world transform')
    if not np.all(mask.sum(axis=(1, 2)) > 0) or not np.isfinite(data['pts3d_world'][mask]).all():
        raise ValueError('GT raster has no support or nonfinite valid points')
    if not np.all(data['depth_z'][mask] > 0.05) or not np.array_equal(data['conf'], mask.astype(np.float32)):
        raise ValueError('GT confidence must represent GT-valid support alone')
    return data


def validate_scene(receipt, *, load_dense=False):
    if receipt.get('schema') != SCHEMA or receipt.get('round') != 1313:
        raise ValueError('wrong training GT receipt identity')
    allowed = set(ASSET_KEYS) | {'schema', 'round', 'dataset', 'scene_name', 'runtime_scene_id', 'frames', 'image_count',
        'selected_frames', 'geometry_source', 'coordinate_frame', 'gravity_up', 'student_observations',
        'teacher_initial_observations', 'rendering_proof'}
    if set(receipt) != allowed:
        raise ValueError('unexpected training scene fields; question/answer mappings are forbidden')
    if receipt['runtime_scene_id'] != scene_id(receipt['dataset'], receipt['scene_name']):
        raise ValueError('runtime scene must preserve the qualified source scene ID')
    if receipt.get('geometry_source') != 'official_aligned_pose_intrinsic_mesh_gt_valid_support':
        raise ValueError('scene is not official-K/GT-support geometry')
    if receipt.get('coordinate_frame') != 'source_world_meters_opencv_camera_to_world' or receipt.get('gravity_up') != [0, 0, 1]:
        raise ValueError('unsupported source coordinate contract')
    frames = receipt['frames']
    if len(frames) != 32 or [r['stem'] for r in frames] != receipt['selected_frames']:
        raise ValueError('exactly32 authenticated RGB frames are required for student targets')
    ordinals = [r['ordinal'] for r in frames]
    if sorted(set(ordinals)) != ordinals or ordinals[0] < 0:
        raise ValueError('invalid selected ordinals')
    for row in [receipt[k] for k in ASSET_KEYS] + frames:
        verify(row)
    if receipt['dataset'] == 'scannet':
        from scannet_checks import validate_box_receipt, validate_identity_receipt
        validate_box_receipt(receipt)
        validate_identity_receipt(receipt)
    alignment = read_json(receipt['alignment']['path'])
    if alignment.get('validated_slots') != 32 or [r['ordinal'] for r in alignment['frames']] != ordinals:
        raise ValueError('all32 official camera/RGB associations must be validated')
    if alignment.get('pose_field') != 'aligned_pose' or alignment.get('estimated_geometry_used') is not False:
        raise ValueError('official alignment provenance is missing')
    calibration = load_arrays(receipt['calibration'])
    if set(calibration) != {'camera_poses', 'intrinsics', 'indices', 'raster_hw'} or calibration['indices'].tolist() != ordinals:
        raise ValueError('official camera carrier census mismatch')
    if load_dense:
        data = validate_dense(load_arrays(receipt['dense']), frames)
        if not np.array_equal(data['camera_poses'], calibration['camera_poses']) or not np.array_equal(data['intrinsics'], calibration['intrinsics']) or list(data['mask'].shape[1:]) != calibration['raster_hw'].tolist():
            raise ValueError('geometry and grounding cameras/canvas differ')
    return receipt
