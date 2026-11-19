"""Contiguous-clip pose readout, separate from sparse head_acc anchors.

Cambrian-P Table 5 / section 5.1 uses Sim(3), ATE and adjacent-frame RPE.
This arm uses the requested first 32 frames at raw stride 3 (0,3,...,93),
not the paper's 90-frame inference length. MonST3R's evo protocol reports
RMSE for ATE (m), RPE translation (m), and RPE rotation (degrees).
"""
import numpy as np

from .all_frame_readout import decode
from .p3_provenance import digest, load, pinned, write

PROTOCOL = 'c1-contiguous32-stride3-sim3-v1'
METRICS = ('ate_rmse_m', 'rpe_trans_rmse_m', 'rpe_rot_rmse_deg')
ORDINALS = list(range(0, 96, 3))


def rigid_poses(value):
    poses = np.asarray(value, dtype=np.float64)
    if (poses.ndim != 3 or poses.shape[1:] != (4, 4) or len(poses) < 3 or not np.isfinite(poses).all()
            or not np.allclose(poses[:, 3], [0, 0, 0, 1], atol=1e-6)
            or not np.allclose(poses[:, :3, :3].transpose(0, 2, 1) @ poses[:, :3, :3], np.eye(3), atol=1e-5)
            or not np.allclose(np.linalg.det(poses[:, :3, :3]), 1., atol=1e-5)):
        raise ValueError('Expected finite rigid camera-to-world poses')
    return poses


def pose_vectors_to_c2w(camera):
    """The head predicts world-to-camera relative to frame 0: invert [R,t]."""
    camera = np.asarray(camera, dtype=np.float64)
    if camera.shape != (32, 9):
        raise ValueError('Clip readout needs all 32 pose vectors')
    rotation, centre = decode(camera)
    result = np.tile(np.eye(4), (32, 1, 1))
    result[:, :3, :3], result[:, :3, 3] = rotation, centre
    return result


def sim3(prediction, reference):
    """Umeyama least-squares proper similarity, fitted only to camera centres."""
    x, y = np.asarray(prediction, float), np.asarray(reference, float)
    if x.shape != y.shape or x.ndim != 2 or x.shape[1] != 3 or not np.isfinite([x, y]).all():
        raise ValueError('Sim(3) requires finite matching Nx3 centres')
    xc, yc = x - x.mean(0), y - y.mean(0)
    variance = np.square(xc).sum()/len(x)
    if variance <= 1e-15:
        raise ValueError('Sim(3) is undefined for a stationary predicted trajectory')
    u, singular, vt = np.linalg.svd(yc.T @ xc / len(x))
    sign = np.ones(3)
    sign[-1] = 1. if np.linalg.det(u @ vt) > 0 else -1.
    rotation = (u * sign) @ vt
    scale = float(singular @ sign / variance)
    if not np.isfinite(scale) or scale <= 1e-12:
        raise ValueError('Sim(3) has no positive trajectory scale')
    return scale, rotation, y.mean(0) - scale*rotation @ x.mean(0)


def trajectory_metrics(prediction, reference):
    pred, gt = rigid_poses(prediction), rigid_poses(reference)
    if pred.shape != gt.shape:
        raise ValueError('Trajectory lengths differ')
    scale, rotation, translation = sim3(pred[:, :3, 3], gt[:, :3, 3])
    aligned = pred.copy()
    aligned[:, :3, :3] = rotation @ pred[:, :3, :3]
    aligned[:, :3, 3] = scale*(pred[:, :3, 3] @ rotation.T) + translation
    # E_i = inv(inv(G_i) G_{i+1}) (inv(P_i) P_{i+1}), delta=1 sampled frame.
    gt_delta = np.linalg.inv(gt[:-1]) @ gt[1:]
    pred_delta = np.linalg.inv(aligned[:-1]) @ aligned[1:]
    errors = np.linalg.inv(gt_delta) @ pred_delta
    angles = np.degrees(np.arccos(np.clip((np.trace(errors[:, :3, :3], axis1=1, axis2=2)-1)/2, -1, 1)))
    return dict(ate_rmse_m=float(np.sqrt(np.square(aligned[:, :3, 3]-gt[:, :3, 3]).sum(1).mean())),
                rpe_trans_rmse_m=float(np.sqrt(np.square(errors[:, :3, 3]).sum(1).mean())),
                rpe_rot_rmse_deg=float(np.sqrt(np.square(angles).mean())),
                alignment_scale=scale, frames=len(pred), relative_pairs=len(pred)-1)


def check_clips(document, heldout, training):
    if document.get('schema') != PROTOCOL or document.get('frame_ordinals') != ORDINALS:
        raise ValueError('Missing contiguous32 stride-3 clip manifest; parent must stage full recordings')
    expected = {tuple(k) for k in heldout}
    if len(expected) != 38 or expected & {tuple(k) for k in training}:
        raise ValueError('Clip readout needs exactly the 38 disjoint held-out scenes')
    seen = set()
    for clip in document['clips']:
        key = (clip['dataset'], clip['scene'])
        inputs = clip['student_input']
        if (key in seen or key not in expected or inputs['frame_indices'] != ORDINALS
                or len(inputs['frames']) != 32 or inputs['total_num_frames'] < 94
                or not isinstance(clip.get('qid'), str) or not clip['qid']
                or clip.get('source_kind') != 'full_recording'
                or not clip.get('recording_id') or not clip.get('source_frames') or not clip.get('source_poses')):
            raise ValueError('Invalid, duplicate or sparse-anchor clip input')
        if rigid_poses(clip['gt_c2w']).shape != (32, 4, 4):
            raise ValueError('Clip GT must cover all 32 frames')
        if not np.isfinite(inputs['fps']) or inputs['fps'] <= 0:
            raise ValueError('Clip FPS must be positive')
        if not np.allclose(inputs['timestamps'], np.asarray(ORDINALS)/inputs['fps']):
            raise ValueError('Clip timestamps differ from raw ordinals')
        seen.add(key)
    if seen != expected:
        raise ValueError('Missing full-recording clip for a held-out scene')
    return document['clips']


def build_clips(cfg):
    """Parent CPU data job: pin full RGB inventories and metric c2w NPZs.

    Each recording supplies frames={frames:[{path,sha256}, ...]} in zero-based
    raw ordinal order and poses NPZ={c2w:[N,4,4],frame_indices:arange(N)}.
    No recordings are decoded here and no sparse anchor is substituted.
    """
    sources = load(pinned(cfg['recordings']))['recordings']
    clips = []
    for source in sources:
        frames = load(pinned(source['frames']))['frames']
        with np.load(pinned(source['poses']), allow_pickle=False) as pack:
            poses, ordinals = pack['c2w'], pack['frame_indices']
        total = source['total_num_frames']
        if (total < 94 or len(frames) != total or len(poses) != total
                or not np.array_equal(ordinals, np.arange(total))):
            raise ValueError('Parent data job needs full-recording frames/poses, not 32 sparse anchors')
        selected = [frames[i] for i in ORDINALS]
        for pin in selected:
            pinned(pin)
        qid = digest([PROTOCOL, source['dataset'], source['scene'], source['recording_id'], ORDINALS])
        clips.append(dict(qid=qid, dataset=source['dataset'], scene=source['scene'], recording_id=source['recording_id'],
            source_kind='full_recording', source_frames=source['frames'], source_poses=source['poses'],
            gt_c2w=rigid_poses(poses[ORDINALS]).tolist(),
            student_input=dict(frames=selected, frame_indices=ORDINALS, fps=source['fps'],
                timestamps=[i/source['fps'] for i in ORDINALS], total_num_frames=total,
                question='Describe this scene.', options=[])))
    document = dict(schema=PROTOCOL, frame_ordinals=ORDINALS, source=cfg['recordings'], clips=clips)
    check_clips(document, load(pinned(cfg['heldout_scenes']))['scenes'],
                load(pinned(cfg['training_scenes']))['scenes'])
    write(cfg['output'], document)
    return document


def summarize(records):
    if len(records) != 38 or len({(r['dataset'], r['scene']) for r in records}) != 38:
        raise ValueError('Clip denominator must remain 38 scenes')
    if not all(np.isfinite(r[k]) and r[k] >= 0 for r in records for k in METRICS):
        raise ValueError('Nonfinite clip metric')
    return dict(protocol=PROTOCOL, scenes=38, clips=38, frames_per_clip=32, raw_stride=3,
                relative_delta=1, aggregation='equal-scene mean of per-clip RMSE',
                mean={k: float(np.mean([r[k] for r in records])) for k in METRICS}, per_scene=records)
