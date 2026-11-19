"""All-frame pose bank with unchanged 16-frame first-hit depth queries."""
import numpy as np

from .camera_targets import check_record, trajectory_scale, rotation_from_xyzw
from .compact_label_bank import ARRAYS, BANK_SCHEMA, validate_bank as validate_legacy
from .gate_eval import geodesic_deg

SCHEMA = 'student_pilot/all_frame_bank/v1'
DEPTH_ANCHORS = np.arange(1, 32, 2)


def validate_bank(bank):
    if (set(bank) != set(ARRAYS) | {'depth_anchor_frames'} or str(bank['schema'].item()) != SCHEMA
            or not np.array_equal(bank['anchor_frames'], np.arange(32))
            or not np.array_equal(bank['depth_anchor_frames'], DEPTH_ANCHORS)):
        raise ValueError('All-frame bank schema or anchors differ')
    n = len(bank['scene_tokens'])
    if bank['camera'].shape != (n, 32, 9) or bank['camera_mask'].shape != (n, 32):
        raise ValueError('All-frame camera shape differs')
    origin = bank['camera_mask'][:, 0]
    if (np.any(np.abs(bank['camera'][origin, 0, :3]) > 1e-5)
            or np.any(np.abs(bank['camera'][origin, 0, 3:7] - [0, 0, 0, 1]) > 1e-5)):
        raise ValueError('Frame one must be the identity pose origin')
    # The pinned A1 policy permits only d1's unavailable odd (one-based) GT.
    for dataset, camera, mask in zip(bank['dataset_tokens'], bank['camera'], bank['camera_mask']):
        partial = dataset == 'd1' and np.array_equal(mask, np.arange(32) % 2 == 1)
        if not mask.all() and not partial:
            raise ValueError('Only d1 odd-frame GT may be masked')
        if partial and np.any(camera[~mask] != 0):
            raise ValueError('Unavailable GT must be zero and masked')
    for i in range(n):
        check_record(dict(camera=bank['camera'][i], camera_mask=bank['camera_mask'][i],
                          trajectory_scale=float(bank['trajectory_scale'][i]), metric=True), max_groups=32)
    legacy = {k: v for k, v in bank.items() if k != 'depth_anchor_frames'}
    legacy.update(schema=np.array(BANK_SCHEMA), anchor_frames=DEPTH_ANCHORS,
                  camera=bank['camera'][:, 1::2], camera_mask=bank['camera_mask'][:, 1::2],
                  trajectory_scale=np.array([trajectory_scale(c[1::2], m[1::2])
                                             for c, m in zip(bank['camera'], bank['camera_mask'])]))
    validate_legacy(legacy)
    return bank


def read_bank(path):
    with np.load(path, allow_pickle=False) as z:
        return validate_bank({k: z[k] for k in z.files})


def compare_even(bank, original):
    """Check raw selections, depth bytes and original even-frame GT; never fit alignment."""
    for key in ('dataset_tokens', 'scene_tokens', 'frame_indices', 'frame_set_sha256',
                'point_depth_uv', 'point_depth_gt', 'point_depth_mask', 'depth_source'):
        if bank[key].dtype != original[key].dtype or not np.array_equal(bank[key], original[key]):
            raise ValueError('Original bank changed: ' + key)
    a, b = bank['camera'][:, 1::2].astype(float), original['camera'].astype(float)
    if not np.array_equal(bank['camera_mask'][:, 1::2], original['camera_mask']):
        raise ValueError('Even-frame masks differ')
    ra = np.array([rotation_from_xyzw(q) for q in a[..., 3:7].reshape(-1, 4)])
    rb = np.array([rotation_from_xyzw(q) for q in b[..., 3:7].reshape(-1, 4)])
    rotation = float(np.max(geodesic_deg(ra, rb)))
    translation = float(np.max(np.abs(a[..., :3] - b[..., :3])))
    result = dict(rotation_deg_max=rotation, translation_element_m_max=translation,
                  translation_l2_m_max=float(np.linalg.norm(a[..., :3] - b[..., :3], axis=-1).max()),
                  fov_rad_max=float(np.max(np.abs(a[..., 7:] - b[..., 7:]))),
                  gravity_element_max=float(np.max(np.abs(bank['gravity'] - original['gravity']))))
    if rotation > .02 or translation > 2e-4 or result['fov_rad_max'] > 2e-5 or result['gravity_element_max'] > 2e-4:
        raise ValueError('Even-frame GT differs: ' + str(result))
    return result


def build_bank(original, poses, *, masked_d1=False):
    """Encode exact-index metric OpenCV c2w sources; require every original scene."""
    from .camera_targets import encode_cameras, encode_gravity
    cameras, masks, scales, gravity = [], [], [], []
    wanted = set(zip(original['dataset_tokens'].tolist(), original['scene_tokens'].tolist()))
    required = {key for key in wanted if not (masked_d1 and key[0] == 'd1')}
    if set(poses) != required:
        raise ValueError('Per-frame source census differs from the original bank')
    for i, key in enumerate(zip(original['dataset_tokens'], original['scene_tokens'])):
        if masked_d1 and key[0] == 'd1':
            camera = np.zeros((32, 9), dtype=np.float32)
            mask = np.zeros(32, dtype=bool)
            camera[1::2], mask[1::2] = original['camera'][i], original['camera_mask'][i]
            cameras.append(camera); masks.append(mask); scales.append(0.)
            gravity.append(original['gravity'][i])
            continue
        source = poses[key]
        if (source['coordinate_frame'] != 'source_world_meters_opencv_camera_to_world'
                or not np.array_equal(source['frame_indices'], original['frame_indices'][i])):
            raise ValueError('Per-frame source convention or raw indices differ')
        camera, mask, scale = encode_cameras(source['c2w'], source['intrinsics'], source['raster_hw'], all_frames=True)
        up, valid = encode_gravity(source['c2w'], source['world_up'])
        if not mask.all() or not valid:
            raise ValueError('Every held-out frame needs valid calibrated GT')
        cameras.append(camera); masks.append(mask); scales.append(scale); gravity.append(up)
    result = {**original, 'schema': np.array(SCHEMA), 'anchor_frames': np.arange(32),
              'depth_anchor_frames': DEPTH_ANCHORS.copy(), 'camera': np.asarray(cameras, dtype=np.float32),
              'camera_mask': np.asarray(masks), 'trajectory_scale': np.asarray(scales, dtype=np.float32),
              'gravity': np.asarray(gravity, dtype=np.float32), 'gravity_mask': np.ones(len(cameras), bool)}
    validate_bank(result)
    compare_even(result, original)
    return result


def main():
    import argparse
    from .compact_label_bank import read_bank as read_original
    from .p3_provenance import load, pinned, file_pin, write
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True, help='Pinned original bank and one pinned exact-32-frame NPZ per scene')
    parser.add_argument('--output', required=True)
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    request = load(args.request)
    if request.get('schema') != 'all-frame-bank-request-v1':
        raise ValueError('Unknown bank build request')
    original = read_original(pinned(request['original']))
    poses = {}
    for source in request['sources']:
        key = source['dataset'], source['scene']
        if key in poses:
            raise ValueError('Duplicate per-frame source')
        with np.load(pinned(source['poses']), allow_pickle=False) as z:
            poses[key] = {k: z[k] for k in ('frame_indices', 'c2w', 'intrinsics', 'raster_hw', 'world_up')}
        poses[key]['coordinate_frame'] = source['coordinate_frame']
    bank = build_bank(original, poses)
    with open(args.output, 'xb') as stream:
        np.savez_compressed(stream, **bank)
    write(args.report, dict(bank=file_pin(args.output), request=file_pin(args.request),
                           comparison=compare_even(bank, original), scenes=len(poses), frames=32,
                           depth='original arrays unchanged'))


if __name__ == '__main__':
    main()
