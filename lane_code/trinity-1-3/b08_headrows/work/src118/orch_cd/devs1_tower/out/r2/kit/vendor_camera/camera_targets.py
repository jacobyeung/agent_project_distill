"""Camera-pose targets and camera-token insertion for the Cambrian-P style head.

Qwen3.5's temporal patch merge fuses sampled frames 2g and 2g+1 (0-based) into temporal
group g. Group g's targets describe its second frame, 2g+1 (the anchor), and every pose is
expressed in the camera of sampled frame 0 (the origin; phase 2's "camera 1"):
E_g = inv(C_{2g+1}) @ C_0 for camera-to-world C (OpenCV axes). Each group's 9-D target is
[t (m), q (xyzw, q_w >= 0), fov_h, fov_w (rad)]. The origin camera is not a group target:
its pose is the identity by definition.
"""
import json
import math

import numpy as np

from .camera_config import CARRIER_TOKEN, POSE_ENCODING, enabled, normalize

SCHEMA = 'rgb-student-camera-v2'
POSE_ONLY_CATEGORY = 'camera_pose_only'
GROUPS, FRAMES = 16, 32
ORIGIN_FRAME = 0
ANCHOR_FRAMES = tuple(2 * g + 1 for g in range(GROUPS))
VIDEO_TOKEN = '<|video_pad|>'
RECORD_FIELDS = frozenset({'qid', 'input_sha256', 'camera', 'camera_mask', 'trajectory_scale', 'metric', 'sources', 'deferred'})
OPTIONAL_RECORD_FIELDS = frozenset({'gravity', 'gravity_mask'})


def quaternion_xyzw(rotation):
    """Unit quaternion (x, y, z, w) of a proper rotation, canonicalized to w >= 0."""
    m = np.asarray(rotation, dtype=np.float64)
    trace = m[0, 0] + m[1, 1] + m[2, 2]
    if trace > 0:
        s = math.sqrt(trace + 1.0) * 2
        q = [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, 0.25 * s]
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        q = [0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s, (m[2, 1] - m[1, 2]) / s]
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        q = [(m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s, (m[0, 2] - m[2, 0]) / s]
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        q = [(m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s, (m[1, 0] - m[0, 1]) / s]
    q = np.asarray(q) / np.linalg.norm(q)
    return -q if q[3] < 0 else q


def rotation_from_xyzw(q):
    x, y, z, w = np.asarray(q, dtype=np.float64) / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def rigid(pose):
    pose = np.asarray(pose, dtype=np.float64)
    rotation = pose[:3, :3]
    return (pose.shape == (4, 4) and np.isfinite(pose).all() and np.allclose(pose[3], [0, 0, 0, 1], atol=1e-5)
            and np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-4) and abs(np.linalg.det(rotation) - 1) < 1e-4)


def trajectory_scale(camera, mask):
    """d-bar: mean distance between consecutive valid groups' target translations (0 if none)."""
    camera, mask = np.asarray(camera, dtype=np.float64), np.asarray(mask, dtype=bool)
    steps = [np.linalg.norm(camera[g, :3] - camera[g - 1, :3]) for g in range(1, len(camera)) if mask[g] and mask[g - 1]]
    return float(np.mean(steps)) if steps else 0.0


def encode_cameras(c2w, intrinsics, raster_hw, valid=None, all_frames=False):
    """Reference encoder for the label builders: 32 sampled frames -> (camera[16,9], mask[16], d-bar).

    c2w: 32 metric OpenCV camera-to-world 4x4 poses of the exact sampled frames.
    intrinsics: 32 pinhole 3x3 matrices scaled to the student RGB raster.
    raster_hw: (H, W) of that raster, or 32 such pairs.
    valid: optional 32 booleans; frames marked False are masked. Without a valid origin frame
    (sampled frame 0) no group is supervised.
    """
    c2w, intrinsics = np.asarray(c2w, dtype=np.float64), np.asarray(intrinsics, dtype=np.float64)
    if c2w.shape != (FRAMES, 4, 4) or intrinsics.shape != (FRAMES, 3, 3):
        raise ValueError('Expected 32 camera-to-world poses and 32 intrinsics matrices')
    raster = np.asarray(raster_hw, dtype=np.float64)
    raster = np.broadcast_to(raster, (FRAMES, 2)) if raster.shape == (2,) else raster
    if raster.shape != (FRAMES, 2) or not np.all(raster > 0):
        raise ValueError('Expected positive raster height and width')
    valid = np.ones(FRAMES, bool) if valid is None else np.asarray(valid, dtype=bool)
    anchors = tuple(range(FRAMES)) if all_frames else ANCHOR_FRAMES
    groups = len(anchors)
    camera, mask = np.zeros((groups, 9)), np.zeros(groups, bool)
    if not (valid[ORIGIN_FRAME] and rigid(c2w[ORIGIN_FRAME])):
        return camera, mask, 0.0
    for g, f in enumerate(anchors):
        fx, fy = intrinsics[f, 0, 0], intrinsics[f, 1, 1]
        mask[g] = bool(valid[f] and rigid(c2w[f]) and np.isfinite(intrinsics[f]).all() and fx > 0 and fy > 0)
    if mask.sum() < 2:
        return camera, np.zeros(groups, bool), 0.0
    reference = c2w[ORIGIN_FRAME]
    for g in np.flatnonzero(mask):
        f = anchors[g]
        relative = np.linalg.inv(c2w[f]) @ reference
        height, width = raster[f]
        camera[g, :3] = relative[:3, 3]
        camera[g, 3:7] = quaternion_xyzw(relative[:3, :3])
        camera[g, 7] = 2 * math.atan(height / (2 * intrinsics[f, 1, 1]))
        camera[g, 8] = 2 * math.atan(width / (2 * intrinsics[f, 0, 0]))
    return camera, mask, trajectory_scale(camera, mask)


def encode_gravity(c2w, world_up=(0.0, 0.0, 1.0)):
    """The origin camera's unit gravity-up vector u = R_0^T world_up in its OpenCV coordinates."""
    c2w = np.asarray(c2w, dtype=np.float64)
    pose = c2w[ORIGIN_FRAME] if c2w.ndim == 3 else c2w
    if not rigid(pose):
        return np.zeros(3, dtype=np.float64), False
    up_world = np.asarray(world_up, dtype=np.float64)
    if up_world.shape != (3,) or not np.isfinite(up_world).all() or np.linalg.norm(up_world) < 1e-6:
        raise ValueError('World up must be a finite nonzero 3-vector')
    up_world = up_world / np.linalg.norm(up_world)
    up_ref = pose[:3, :3].T @ up_world
    return up_ref / np.linalg.norm(up_ref), True


def gravity_reference_rotation(up_in_ref):
    """SO(3) matrix R_{grav <- ref} from origin-camera OpenCV coordinates to the frame-1 gravity reference.

    Frame-1 gravity reference (phase 2's frame; "frame 1" is sampled frame 0, the origin):
      +X: horizontal right of the origin camera
      +Y: horizontal forward of the origin camera (optical +Z with its gravity component removed)
      +Z: gravity up (up_in_ref)
    Raises when the up vector is degenerate or the camera looks straight along gravity."""
    ez = np.asarray(up_in_ref, dtype=np.float64)
    norm_z = float(np.linalg.norm(ez))
    if ez.shape != (3,) or not math.isfinite(norm_z) or norm_z < 1e-6:
        raise ValueError('The gravity up vector must be a finite nonzero 3-vector')
    ez = ez / norm_z
    forward = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    y_perp = forward - float(np.dot(forward, ez)) * ez
    if np.linalg.norm(y_perp) < 1e-6:
        raise ValueError('The origin camera looks along gravity: its horizontal forward is undefined')
    ey = y_perp / np.linalg.norm(y_perp)
    ex = np.cross(ey, ez)
    ex = ex / np.linalg.norm(ex)
    return np.stack((ex, ey, ez), axis=0)


def to_gravity_reference_frame(camera_targets, up_in_ref):
    """Convert [S, 9] (or [9]) encodings E = inv(C_k) @ C_0 into metric frame-1 gravity reference poses.

    Returns:
      R_grav: [S, 3, 3] camera-to-gravity-reference rotations
      t_grav: [S, 3] camera centres in the gravity reference (metres; origin at the origin camera)
      fov_hw: [S, 2] vertical and horizontal fields of view (radians)
    Translations are metric as supervised; no scale factor applies.
    """
    cam = np.asarray(camera_targets, dtype=np.float64)
    single = cam.ndim == 1
    if single:
        cam = cam[None, :]
    if cam.ndim != 2 or cam.shape[1] != 9 or not np.isfinite(cam).all():
        raise ValueError('Expected finite [S, 9] camera encodings')
    r_align = gravity_reference_rotation(up_in_ref)
    slots = cam.shape[0]
    r_grav = np.zeros((slots, 3, 3), dtype=np.float64)
    t_grav = np.zeros((slots, 3), dtype=np.float64)
    for k in range(slots):
        q_rel = cam[k, 3:7]
        if np.linalg.norm(q_rel) < 1e-6:
            raise ValueError('A camera encoding has a zero quaternion')
        r_rel = rotation_from_xyzw(q_rel)
        # E_k = [r_rel, t_rel] = inv(C_k) @ C_0, so C_0^{-1} C_k = [r_rel^T, -r_rel^T t_rel].
        r_c2ref = r_rel.T
        t_c2ref = -r_c2ref @ cam[k, :3]
        r_grav[k] = r_align @ r_c2ref
        t_grav[k] = r_align @ t_c2ref
    fov_hw = cam[:, 7:9].copy()
    if single:
        return r_grav[0], t_grav[0], fov_hw[0]
    return r_grav, t_grav, fov_hw


def probe_record(like=None):
    """A fully supervised record for memory probing only (worst case); its values never train anything.

    like: the row's own record, whose optional fields (gravity, point depth) the probe mirrors so
    every row of a probe micro-batch carries the same targets."""
    like = like or {}
    groups = len(like.get('camera', [None] * GROUPS))
    camera = np.zeros((groups, 9))
    camera[:, 0] = 0.1 * np.arange(groups)
    camera[:, 6], camera[:, 7], camera[:, 8] = 1.0, 1.0, 1.2
    mask = np.ones(groups, bool)
    record = {'camera': camera.tolist(), 'camera_mask': mask.tolist(), 'trajectory_scale': trajectory_scale(camera, mask),
              'lm_weight': 1.0}
    if groups > GROUPS:
        record['max_groups'] = like.get('max_groups', GROUPS)
    if 'gravity' in like:
        record.update(gravity=[0.0, -1.0, 0.0], gravity_mask=True)
    if like.get('point_depth') is not None:
        points = np.asarray(like['point_depth']['mask']).shape[1]
        uv = np.stack(np.meshgrid(np.linspace(10, 990, points), [500.0], indexing='xy'), axis=-1).reshape(points, 2)
        record['point_depth'] = {'uv': np.repeat(uv[None], groups, axis=0).tolist(),
                                 'depth': np.full((groups, points), 2.0).tolist(),
                                 'mask': np.full((groups, points), not like.get('frozen_depth', False), dtype=bool).tolist()}
        if like.get('frozen_depth'):
            record['point_depth'] = like['point_depth']
            record['frozen_depth'] = True
    return record


def check_record(record, max_groups=GROUPS):
    camera, mask = np.asarray(record['camera'], dtype=np.float64), np.asarray(record['camera_mask'])
    groups = len(camera)
    if (not GROUPS <= groups <= max_groups <= 48 or camera.shape != (groups, 9)
            or mask.shape != (groups,) or mask.dtype != bool or not np.isfinite(camera).all()):
        raise ValueError('Malformed camera target')
    if record.get('metric') is not True:
        raise ValueError('Camera targets must come from metric-scale scenes')
    scale = record['trajectory_scale']
    if type(scale) not in (int, float) or not math.isfinite(scale) or scale < 0:
        raise ValueError('Invalid camera trajectory scale')
    if mask.any():
        if mask.sum() < 2:
            raise ValueError('A supervised camera row needs at least two valid groups')
        rows = camera[mask]
        if (not np.allclose(np.linalg.norm(rows[:, 3:7], axis=1), 1, atol=1e-3) or np.any(rows[:, 6] < 0)
                or np.any(rows[:, 7:] <= 0) or np.any(rows[:, 7:] >= math.pi)):
            raise ValueError('Camera quaternion or field of view outside the contract')
        if not math.isclose(scale, trajectory_scale(camera, mask), rel_tol=1e-4, abs_tol=1e-6):
            raise ValueError('Camera trajectory scale differs from its recomputation')
    elif np.any(camera != 0) or scale != 0:
        raise ValueError('A camera row without supervision must hold zeros')
    return camera, mask


def load_for_rows(rows, config):
    """Verified per-row camera targets in training order, or None when the head is off."""
    if not enabled(config):
        return None
    from .auxiliary_targets import input_identity, verify

    cfg = normalize(config)
    verified = verify(cfg['supervision'])
    if 'row_routing' in cfg and not str(verified).endswith('.npz'):
        raise ValueError('Camera row routing reads its depth queries from a first-hit label bank (.npz)')
    if str(verified).endswith('.npz'):
        from .compact_label_bank import load_bank_for_rows
        result, audit = load_bank_for_rows(verified, rows, cfg)
        print(json.dumps({'event': 'camera_label_audit', **audit}, sort_keys=True), flush=True)
        return result
    from .point_depth_head import point_depth_enabled
    if point_depth_enabled(cfg['point_depth']):
        raise ValueError('Point-depth labels come only from a first-hit label bank (.npz)')
    payload = json.loads(verified.read_text())
    if (payload.get('schema') != SCHEMA or payload.get('pose_encoding') != POSE_ENCODING
            or payload.get('translation_unit_m') != 1.0):
        raise ValueError('Camera sidecar schema, pose encoding or unit mismatch')
    records = payload['rows']
    if len(records) != len(rows) or [r['qid'] for r in records] != [r['qid'] for r in rows] or len({r['qid'] for r in records}) != len(records):
        raise ValueError('Camera sidecar must retain the exact training row census and order')
    covered, result = 0, []
    for row, record in zip(rows, records):
        if not isinstance(record, dict) or not (RECORD_FIELDS <= set(record) <= (RECORD_FIELDS | OPTIONAL_RECORD_FIELDS)):
            raise ValueError('Malformed camera sidecar record fields')
        if record['input_sha256'] != input_identity(row):
            raise ValueError('Camera sidecar RGB input changed')
        camera, mask = check_record(record, cfg.get('max_groups', GROUPS))
        covered += bool(mask.any())
        # Pose-only rows (Cambrian-P) train the camera head alone: their text target gets no loss.
        pose_only = row.get('category') == POSE_ONLY_CATEGORY
        if pose_only and not mask.any():
            raise ValueError('A pose-only row has no camera supervision')
        entry = {'camera': camera.tolist(), 'camera_mask': mask.tolist(), 'trajectory_scale': float(record['trajectory_scale']),
                 'lm_weight': 0.0 if pose_only else 1.0}
        if len(camera) > GROUPS:
            entry['max_groups'] = cfg['max_groups']
        if 'gravity' in record or 'gravity_mask' in record:
            grav = np.asarray(record.get('gravity', [0.0, 0.0, 0.0]), dtype=np.float64)
            gmask = bool(record.get('gravity_mask', False))
            if grav.shape != (3,) or not np.isfinite(grav).all():
                raise ValueError('Malformed camera gravity target')
            if gmask and not math.isclose(float(np.linalg.norm(grav)), 1.0, rel_tol=1e-3, abs_tol=1e-3):
                raise ValueError('Supervised gravity target must be a unit vector')
            entry['gravity'] = grav.tolist()
            entry['gravity_mask'] = gmask
        result.append(entry)
    if not covered:
        raise ValueError('Camera supervision is enabled but no training row has camera targets')
    return result


def carrier_id(tokenizer):
    single = tokenizer.convert_tokens_to_ids(CARRIER_TOKEN)
    if type(single) is not int or tokenizer.encode(CARRIER_TOKEN, add_special_tokens=False) != [single]:
        raise ValueError('The camera carrier is not one tokenizer id')
    return single


def insert_tokens(batch, record, tokenizer, max_groups=GROUPS):
    """Append one carrier after each temporal group's video tokens; return the batch plus camera targets.

    Rows without camera supervision keep their encoding and get inert targets, as
    Cambrian-P inserts camera tokens only into pose-supervised samples.
    """
    import torch

    carrier, video = carrier_id(tokenizer), tokenizer.convert_tokens_to_ids(VIDEO_TOKEN)
    ids, labels, attention = batch['input_ids'], batch['labels'], batch['attention_mask']
    if ids.ndim != 2 or ids.shape[0] != 1:
        raise ValueError('Camera tokens are inserted into single-row encodings')
    length = int(attention[0].sum())
    if torch.any(ids[0, :length] == carrier):
        raise ValueError('A row already contains the camera carrier token')
    max_groups = record.get('max_groups', max_groups)
    groups = len(record['camera'])
    if not GROUPS <= groups <= max_groups <= 48 or len(record['camera_mask']) != groups:
        raise ValueError('Camera target exceeds the configured max_groups')
    mask = torch.tensor(record['camera_mask'], dtype=torch.bool)
    extra = {'aux_camera_target': torch.tensor(record['camera'], dtype=torch.float32)[None],
             'aux_camera_mask': mask[None], 'aux_camera_scale': torch.tensor([record['trajectory_scale']], dtype=torch.float32),
             'aux_camera_positions': torch.full((1, groups), -1, dtype=torch.long),
             'aux_lm_weight': torch.tensor([float(record.get('lm_weight', 1.0))], dtype=torch.float32)}
    if 'gravity' in record:
        extra['aux_gravity_target'] = torch.tensor(record['gravity'], dtype=torch.float32)[None]
        extra['aux_gravity_mask'] = torch.tensor([bool(record.get('gravity_mask', False))], dtype=torch.bool)
    if record.get('point_depth') is not None:
        pd_rec = record['point_depth']
        extra['aux_point_depth_uv'] = torch.tensor(pd_rec['uv'], dtype=torch.float32)[None]
        extra['aux_point_depth_gt'] = torch.tensor(pd_rec['depth'], dtype=torch.float32)[None]
        extra['aux_point_depth_mask'] = torch.tensor(pd_rec['mask'], dtype=torch.bool)[None]
    depth_supervised = 'aux_point_depth_mask' in extra and bool(extra['aux_point_depth_mask'].any())
    # force_carriers (headcall rows): the heads answer this row's calls, so its prompt holds the carriers even when
    # the bank has no label for its scene.
    if not mask.any() and not depth_supervised and not record.get('force_carriers'):
        return {**batch, **extra}
    result = insert_carriers(batch, tokenizer, max_groups=max_groups)
    if result['aux_camera_positions'].shape[1] != groups:
        raise ValueError('Camera target slots differ from the video temporal groups')
    extra['aux_camera_positions'] = result.pop('aux_camera_positions')
    return {**result, **extra}


def insert_carriers(batch, tokenizer, max_groups=GROUPS):
    """Append one carrier after each temporal group's video-token run, with an explicit training capacity.

    Slots are max(16, G), so RGB32 keeps [1,16] even with capacity 48. The phase-2 head API retains
    the default 16-group limit; only training callers explicitly expand capacity."""
    import torch

    carrier, video = carrier_id(tokenizer), tokenizer.convert_tokens_to_ids(VIDEO_TOKEN)
    ids, attention = batch['input_ids'], batch['attention_mask']
    if ids.ndim != 2 or ids.shape[0] != 1:
        raise ValueError('Camera tokens are inserted into single-row encodings')
    length = int(attention[0].sum())
    if torch.any(ids[0, :length] == carrier):
        raise ValueError('A row already contains the camera carrier token')
    positions = torch.where(ids[0, :length] == video)[0]
    if not positions.numel():
        raise ValueError('Camera tokens need a video row')
    breaks = torch.where(positions[1:] != positions[:-1] + 1)[0]
    ends = torch.cat((positions[breaks], positions[-1:])).tolist()
    sizes = torch.diff(torch.cat((torch.tensor([-1]), breaks, torch.tensor([positions.numel() - 1])))).tolist()
    labels = batch.get('labels')
    supervised = torch.where(labels[0] != -100)[0] if labels is not None else torch.zeros(0, dtype=torch.long)
    # 16 groups for a 32-frame row; an N-frame pose-only sample has N / 2 groups, padded to 16 slots with -1.
    if (type(max_groups) is not int or not GROUPS <= max_groups <= 48
            or not 1 <= len(ends) <= max_groups or len(set(sizes)) != 1
            or (supervised.numel() and ends[-1] >= int(supervised[0]))):
        raise ValueError('Camera tokens exceed max_groups or lack equal temporal-group video runs before the target')
    cuts = [0] + [end + 1 for end in ends] + [ids.shape[1]]
    fills = {'input_ids': carrier, 'labels': -100, 'attention_mask': 1, 'mm_token_type_ids': 0}
    result = dict(batch)
    for key, fill in fills.items():
        if key not in batch:
            continue
        tensor = batch[key]
        pieces = []
        for g in range(len(cuts) - 1):
            pieces.append(tensor[:, cuts[g]:cuts[g + 1]])
            if g < len(ends):
                pieces.append(tensor.new_full((1, 1), fill))
        result[key] = torch.cat(pieces, dim=1)
    positions = [end + 1 + g for g, end in enumerate(ends)] + [-1] * (max(GROUPS, len(ends)) - len(ends))
    result['aux_camera_positions'] = torch.tensor([positions], dtype=torch.long)
    return result
