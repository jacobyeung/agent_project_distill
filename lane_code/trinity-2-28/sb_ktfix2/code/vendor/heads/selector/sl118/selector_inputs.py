"""Per-candidate inputs of the stage-1 selector head: fixed math on SAM 3 proposals and the scaled G3T geometry.

No fitted constant and no name rule lives here. The call hook and the table builder call the same function
inside `routed_features.accept_features`' scope:

    vec = candidate_vectors(tracks, raw_frames, geometry, accepted)   # list[N] of float lists, len F_IN

  tracks      the linked `routed_candidates.Candidate` list for one name (input of accept_features)
  raw_frames  32 lists of SAM 3 detections for that name (dict mask[480,640] bool, score, presence)
  geometry    the `routed_features.Geometry` wrapper over the scaled G3T geometry (`exact` in extract())
  accepted    accept_features(tracks, raw_frames, geometry) output (same order as the returned vectors)

Socket fields (zeros today): SAM 3 mask tokens and own-ViT features pooled in the mask need a GPU pass and are not
in the K1 cache; they enter as separate tensors of the head (`mask_tokens`, `vit_feats`), not in this vector.
"""
import math

import numpy as np

PORTABLE = ['peak', 'logit_peak', 'support', 'n_members', 'exclusivity_margin', 'inst_score_mean', 'inst_score_max',
            'log_area_mean', 'log_area_max', 'sam_presence_members',
            'has_3d', 'member_spread_m', 'multi_view_3d', 'log_extent_max', 'log_extent_mid', 'reproj_vis',
            'reproj_vis_other', 'reproj_det', 'reproj_det_ratio', 'reproj_hit_score', 'dist_to_top_m', 'n_dupes_05m',
            'n_cands_name', 'peak_rank', 'peak_rank_frac', 'peak_rel', 'coverage', 'log_members']
# Counts with heavy tails enter as log1p (fixed transform).
LOG1P = {'support', 'n_members', 'reproj_vis', 'reproj_vis_other', 'reproj_det', 'n_dupes_05m', 'n_cands_name',
         'peak_rank', 'member_spread_m', 'dist_to_top_m'}
EXTRA = ['consensus', 'log_visible_count', 'log_best_view_area',
         'joint_min', 'joint_median', 'joint_std', 'score_min', 'score_median', 'presence_min', 'presence_max',
         'rank_in_frame_mean', 'top_in_frame_frac', 'name_frames_frac', 'name_max_score_mean',
         'member_frames_frac', 'frame_span_frac',
         'log_depth_mean', 'log_depth_std', 'log_depth_min', 'log_depth_max',
         'log_member_extent_median', 'log_member_extent_max',
         'height_rel_camera', 'log_horiz_dist_camera',
         'bbox_u_mean', 'bbox_v_mean', 'bbox_w_mean', 'bbox_h_mean', 'fill_mean', 'border_frac']
FIELDS = PORTABLE + EXTRA
F_IN = len(FIELDS)


def _portable(features):
    out = []
    for key in PORTABLE:
        value = float(features[key])
        out.append(math.log1p(max(value, 0.)) if key in LOG1P else value)
    return out


def _cameras(geometry):
    centres = [np.asarray(geometry.source.cam(k)[1], float) for k in geometry.frames]
    return np.median(np.stack(centres), 0) if centres else np.zeros(3)


def _bbox(mask):
    ys, xs = np.nonzero(mask)
    if not len(ys):
        return None
    h, w = mask.shape
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    border = float(y0 == 0 or x0 == 0 or y1 == h or x1 == w)
    return ((x0 + x1) / 2 / w, (y0 + y1) / 2 / h, (x1 - x0) / w, (y1 - y0) / h,
            len(ys) / max((y1 - y0) * (x1 - x0), 1), border)


def candidate_vectors(tracks, raw_frames, geometry, accepted):
    by_id = {t.id: t for t in tracks}
    cam = _cameras(geometry)
    name_frames = sum(any(float(e['score']) >= .3 for e in frame) for frame in raw_frames) / 32.
    name_max = float(np.mean([max((float(e['score']) for e in frame), default=0.) for frame in raw_frames]))
    out = []
    for item in accepted:
        track = by_id[item['candidate_id']]
        p = track.proposals
        joints = np.array([v.joint for v in p], float)
        scores = np.array([v.score for v in p], float)
        pres = np.array([v.presence for v in p], float)
        idx = np.array([v.index for v in p], float)
        frames = np.array([v.frame for v in p], float)
        depths = np.log(np.clip(np.array([v.depth for v in p], float), 1e-3, None))
        ext = np.log(np.clip(np.array([v.extent for v in p], float), 1e-3, None))
        centre = np.asarray(track.center, float)
        boxes = [b for b in (_bbox(m) for m in item['masks'].values()) if b is not None]
        boxes = np.array(boxes, float) if boxes else np.zeros((1, 6))
        f = track.features
        extra = [float(f.get('consensus', 0.)), math.log1p(float(f.get('visible_count', 0.))),
                 math.log(max(float(f.get('best_view_area', 0.)), 1e-6)),
                 joints.min(), float(np.median(joints)), joints.std(), scores.min(), float(np.median(scores)),
                 pres.min(), pres.max(), idx.mean(), float(np.mean(idx == 0)), name_frames, name_max,
                 len(set(frames.tolist())) / 32., (frames.max() - frames.min()) / 31.,
                 depths.mean(), depths.std(), depths.min(), depths.max(), float(np.median(ext)), ext.max(),
                 float(centre[2] - cam[2]), math.log(max(float(np.linalg.norm(centre[:2] - cam[:2])), 1e-2)),
                 *boxes[:, :5].mean(0).tolist(), float(boxes[:, 5].mean())]
        vec = _portable(item['features']) + [float(x) for x in extra]
        if len(vec) != F_IN or not np.isfinite(vec).all():
            raise ValueError('selector input vector is malformed')
        out.append(vec)
    return out


def name_key(name):
    """The name as written; the only normalization is lowercase and strip."""
    return str(name).strip().lower()
