import math
import numpy as np
from scipy import ndimage

from . import routed_candidates as candidates


SHAPE = (480, 640)
OUTPUT_SHAPE = (240, 320)


def array(value):
    return value.detach().cpu().numpy() if hasattr(value, "detach") else np.asarray(value)


def resize(mask, shape):
    mask = np.asarray(mask, bool)
    if mask.ndim != 2 or not all(mask.shape):
        raise ValueError("Routed policy requires a nonempty two-dimensional mask")
    return (mask.copy() if mask.shape == shape else
            ndimage.zoom(mask, (shape[0]/mask.shape[0], shape[1]/mask.shape[1]), order=0, prefilter=False))


def rle(mask):
    values = np.asarray(mask, bool).ravel(order="F")
    boundaries = np.flatnonzero(np.diff(values.astype(np.int8))) + 1
    counts = np.diff(np.r_[0, boundaries, len(values)]).tolist()
    return dict(size=list(mask.shape), counts=([0] + counts if values[0] else counts))


def detections(source, name, frame_map):
    if hasattr(source, "cache"):
        codec, cache = source.reader, source.cache
        if codec.phrase(name) not in cache["phrases"]:
            if source.live is None:
                return [[] for _ in range(32)], "sam3"
            codec, cache = source.live.codec, source.live._detect(name)
    elif hasattr(source, "_detect"):
        codec, cache = source.codec, source._detect(name)
    else:
        batch = source.masks_for(name)
        frame_map.require(batch.frame_indices)
        if batch.state is not None:
            if str(batch.state).lower() in ("not_seen", "state.not_seen"):
                return [[] for _ in range(32)], "native_mask"
            raise ValueError("Routed policy received an unresolved mask source")
        masks, probabilities = array(batch.masks), array(batch.probabilities)
        if masks.ndim != 3 or masks.shape[0] != 32 or probabilities.shape != (32,):
            raise ValueError("Routed policy mask-frame layout differs")
        out = []
        for mask, probability in zip(masks, probabilities, strict=True):
            if not np.isfinite(probability) or not 0 <= probability <= 1:
                raise ValueError("Routed policy received an invalid mask probability")
            labels, count = ndimage.label(np.asarray(mask, bool))
            out.append([dict(mask=resize(labels == i, SHAPE), score=float(probability), presence=1.)
                        for i in range(1, count+1)] if probability >= batch.tau else [])
        return out, "native_mask"
    frame_map.require(source.frame_indices)
    phrase = codec.phrase(name)
    out = []
    for slot in range(32):
        record = cache["frames"][str(slot)]["phrases"].get(phrase)
        if record is None:
            out.append([])
            continue
        presence = float(record["presence"])
        frame = []
        for entry in sorted(record.get("instances") or [], key=lambda value: -float(value["score"])):
            score = float(entry["score"])
            if not np.isfinite([score, presence]).all() or not 0 <= score <= 1 or not 0 <= presence <= 1:
                raise ValueError("Routed policy received invalid proposal probabilities")
            frame.append(dict(mask=resize(codec.rle_decode(entry["mask"]), SHAPE),
                              score=score, presence=presence))
        out.append(frame)
    return out, "sam3"


def cache_for(name, frames):
    return dict(phrases=[name], frames={str(k): dict(phrases={name: dict(
        presence=values[0]["presence"] if values else 0.,
        instances=[dict(score=value["score"], mask=rle(value["mask"])) for value in values])})
        for k, values in enumerate(frames)})


class Geometry:
    def __init__(self, source):
        self.source = source
        self.frames = tuple(k for k in range(1, 33) if source.has(k))
        self.grids = {}

    def depth(self, frame, shape=OUTPUT_SHAPE):
        key = frame, tuple(shape)
        if key not in self.grids:
            if frame not in self.frames:
                raise ValueError("exact_depth_frame_unavailable")
            y, x = np.indices(shape)
            u, v = (x+.5)/shape[1]*1000, (y+.5)/shape[0]*1000
            values = np.asarray(self.source._depth(frame-1, u.ravel(), v.ravel()), float).reshape(shape)
            if not np.isfinite(values).all():
                raise ValueError("nonfinite_depth_grid")
            self.grids[key] = values.astype(np.float32)
        return self.grids[key]

    def project(self, frame, points, *, pixels=False):
        rotation, centre = self.source.cam(frame)
        local = (np.asarray(points, float)-centre) @ rotation
        fh, fw = self.source.fov_of(frame)
        z = local[..., 2]
        denominator = np.maximum(z, 1e-6) if pixels else z
        with np.errstate(divide="ignore", invalid="ignore"):
            u = 500*(local[..., 0]/denominator/math.tan(fw/2)+1)
            v = 500*(local[..., 1]/denominator/math.tan(fh/2)+1)
        if pixels:
            return u/1000*OUTPUT_SHAPE[1]-.5, v/1000*OUTPUT_SHAPE[0]-.5, z
        return u, v, z

    def points(self, frame, mask):
        depth = self.depth(frame)
        sampled = mask[::2, ::2] & (depth[::2, ::2] > 0)
        if sampled.sum() < 3:
            return None
        y, x = np.indices(OUTPUT_SHAPE)
        fh, fw = self.source.fov_of(frame)
        rays = np.stack([(((x+.5)/OUTPUT_SHAPE[1]*1000)/500-1)*math.tan(fw/2),
                         (((y+.5)/OUTPUT_SHAPE[0]*1000)/500-1)*math.tan(fh/2), np.ones_like(x)], -1)
        rotation, centre = self.source.cam(frame)
        return (rays[::2, ::2][sampled]*depth[::2, ::2][sampled, None]) @ rotation.T + centre


def member_points(geometry, frame, mask, rng):
    interior = ndimage.binary_erosion(mask, structure=np.ones((3, 3)))
    y, x = np.nonzero(interior if interior.sum() >= 10 else mask)
    if len(y) > 300:
        subset = rng.choice(len(y), 300, replace=False)
        y, x = y[subset], x[subset]
    uv = np.column_stack(((x+.5)/SHAPE[1]*1000, (y+.5)/SHAPE[0]*1000))
    uv = uv[((uv >= 20) & (uv <= 980)).all(1)]
    if not len(uv):
        return np.empty((0, 3))
    points, local, spread = geometry.lift(frame, uv, mode="center")
    valid = np.isfinite(points).all(1) & (local[:, 2] > 0) & np.isfinite(spread) & (spread <= .25)
    return points[valid]


def reprojection(geometry, centre, frames, own_frames):
    visible = other = detected = 0
    scores = []
    for frame in geometry.frames:
        u, v, z = geometry.project(frame, centre)
        if not (z > .1 and 20 <= u <= 980 and 20 <= v <= 980):
            continue
        depth = float(geometry.source._depth(frame-1, np.array([u]), np.array([v]))[0])
        if z > depth*1.15+.3:
            continue
        visible += 1
        other += frame not in own_frames
        y, x = int(v/1000*SHAPE[0]), int(u/1000*SHAPE[1])
        hits = [value["score"] for value in frames[frame-1]
                if value["mask"][max(y-6, 0):min(y+7, SHAPE[0]), max(x-6, 0):min(x+7, SHAPE[1])].any()]
        if hits:
            detected += 1
            scores.append(max(hits))
    return dict(reproj_vis=visible, reproj_vis_other=other, reproj_det=detected,
                reproj_det_ratio=detected/visible if visible else 0.,
                reproj_hit_score=float(np.mean(scores)) if scores else 0.)


def accept_features(tracks, raw, geometry):
    rng = np.random.default_rng(17)
    out, centres = [], {}
    ordered = sorted(tracks, key=lambda value: (-value.features["peak"], value.id))
    for candidate in ordered:
        members = [(p.frame, raw[p.frame-1][p.index]) for p in candidate.proposals]
        masks = [(frame, entry["mask"]) for frame, entry in members]
        scores = [entry["score"] for _, entry in members]
        areas = [float(mask.mean()) for _, mask in masks]
        points = [member_points(geometry.source, frame, mask, rng) for frame, mask in masks]
        medians = [np.median(value, 0) for value in points if len(value) >= 5]
        all_points = np.concatenate([value for value in points if len(value)]) if any(map(len, points)) else np.empty((0, 3))
        peak = float(candidate.features["peak"])
        safe = np.clip(peak, 1e-6, 1-1e-6)
        features = dict(peak=peak, logit_peak=float(np.log(safe/(1-safe))), support=candidate.features["support"],
                        n_members=len(members), exclusivity_margin=candidate.features["exclusivity_margin"],
                        inst_score_mean=float(np.mean(scores)), inst_score_max=float(np.max(scores)),
                        log_area_mean=math.log(max(np.mean(areas), 1e-6)), log_area_max=math.log(max(np.max(areas), 1e-6)),
                        sam_presence_members=float(np.mean([entry["presence"] for _, entry in members])))
        if medians:
            centre = np.median(np.stack(medians), 0)
            extent = np.sort(np.percentile(all_points, 90, 0)-np.percentile(all_points, 10, 0))[::-1]
            features.update(has_3d=1., member_spread_m=float(max(np.linalg.norm(value-centre) for value in medians)) if len(medians)>1 else 0.,
                            multi_view_3d=float(len(medians)>1), log_extent_max=math.log(max(extent[0], 1e-2)),
                            log_extent_mid=math.log(max(extent[1], 1e-2)),
                            **reprojection(geometry, centre, raw, {frame for frame, _ in masks}))
            centres[candidate.id] = centre
        else:
            features.update(has_3d=0., member_spread_m=0., multi_view_3d=0., log_extent_max=0., log_extent_mid=0.,
                            reproj_vis=0., reproj_vis_other=0., reproj_det=0., reproj_det_ratio=0., reproj_hit_score=0.)
        out.append(dict(candidate_id=candidate.id, features=features,
                        masks={frame: mask[::2, ::2].copy() for frame, mask in masks}))
    if not out:
        return out
    top = max(ordered, key=lambda candidate: (candidate.features["peak"], candidate.id)).id
    peaks = np.asarray([value["features"]["peak"] for value in out])
    order = (-peaks).argsort(kind="stable")
    ranks = np.empty(len(out))
    ranks[order] = np.arange(len(out))
    for value, rank in zip(out, ranks, strict=True):
        features = value["features"]
        centre = centres.get(value["candidate_id"])
        distances = ([np.linalg.norm(centre-other) for key, other in centres.items() if key != value["candidate_id"]]
                     if centre is not None else [])
        features.update(dist_to_top_m=float(np.linalg.norm(centre-centres[top])) if centre is not None and top in centres else 5.,
                        n_dupes_05m=float(sum(distance < .5 for distance in distances)),
                        n_cands_name=float(len(out)), peak_rank=float(rank), peak_rank_frac=float(rank/max(len(out)-1, 1)),
                        peak_rel=float(features["peak"]/max(peaks.max(), 1e-6)),
                        coverage=float(features["n_members"]/max(features["reproj_vis"], 1)),
                        log_members=float(np.log1p(features["n_members"])))
    return out


def geometry_of(geometry, masks):
    points = [geometry.points(frame, mask) for frame, mask in masks.items() if frame in geometry.frames]
    points = [value for value in points if value is not None]
    if not points:
        return None
    combined = np.concatenate(points)
    low, high = np.percentile(combined, (10, 90), axis=0)
    centre = np.median(np.stack([np.median(value, 0) for value in points]), 0)
    if len(combined) > 1500:
        combined = combined[np.random.default_rng(0).choice(len(combined), 1500, replace=False)]
    return centre, float(np.max(high-low)), low, high, combined


def pair_reprojection(geometry, points, masks):
    values = []
    for frame, mask in masks.items():
        if frame not in geometry.frames:
            continue
        x, y, z = geometry.project(frame, points, pixels=True)
        finite = np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
        x, y = np.rint(np.where(finite, x, -1)).astype(int), np.rint(np.where(finite, y, -1)).astype(int)
        valid = finite & (z > .1) & (x >= 0) & (x < OUTPUT_SHAPE[1]) & (y >= 0) & (y < OUTPUT_SHAPE[0])
        if valid.sum() < 20:
            continue
        depth = geometry.depth(frame)[y[valid], x[valid]]
        visible = (depth <= 0) | (z[valid] <= depth*1.05+.05)
        if visible.sum() >= 20:
            values.append(float(mask[y[valid][visible], x[valid][visible]].mean()))
    return float(np.mean(values)) if values else 0.


def pair_features(first, second, geometry):
    a, b = geometry_of(geometry, first["masks"]), geometry_of(geometry, second["masks"])
    ma, mb = first["masks"], second["masks"]
    fa, fb = first["features"], second["features"]
    features = dict(peak_max=max(fa["peak"], fb["peak"]), peak_min=min(fa["peak"], fb["peak"]),
                    logm_max=max(np.log1p(len(ma)), np.log1p(len(mb))), logm_min=min(np.log1p(len(ma)), np.log1p(len(mb))),
                    reproj_max=0., reproj_min=0.)
    if a is not None and b is not None:
        distance = float(np.linalg.norm(a[0]-b[0]))
        intersection = float(np.prod(np.clip(np.minimum(a[3], b[3])-np.maximum(a[2], b[2]), 0, None)))
        va, vb = float(np.prod(np.clip(a[3]-a[2], 1e-4, None))), float(np.prod(np.clip(b[3]-b[2], 1e-4, None)))
        features.update(has_c=1., d_c=distance, d_rel=distance/(.3+.5*max(a[1], b[1])),
                        ext_max=max(a[1], b[1]), ext_min=min(a[1], b[1]),
                        box_iou3d=intersection/(va+vb-intersection), box_ov3d=intersection/min(va, vb))
        if distance < 3.:
            ab, ba = pair_reprojection(geometry, a[4], mb), pair_reprojection(geometry, b[4], ma)
            features.update(reproj_max=max(ab, ba), reproj_min=min(ab, ba))
    else:
        features.update(has_c=0., d_c=6., d_rel=10., ext_max=0., ext_min=0., box_iou3d=0., box_ov3d=0.)
    shared = sorted(ma.keys() & mb.keys())
    ious, overlaps = [], []
    for frame in shared:
        first_mask, second_mask = ma[frame], mb[frame]
        intersection = float(np.logical_and(first_mask, second_mask).sum())
        ious.append(intersection/max(float(np.logical_or(first_mask, second_mask).sum()), 1.))
        overlaps.append(intersection/max(min(float(first_mask.sum()), float(second_mask.sum())), 1.))
    features.update(n_shared=float(len(shared)), shared_frac=len(shared)/max(min(len(ma), len(mb)), 1),
                    n_union=float(len(ma.keys() | mb.keys())), iou2d_max=max(ious, default=0.),
                    iou2d_mean=float(np.mean(ious)) if ious else 0., ov2d_max=max(overlaps, default=0.),
                    ov2d_mean=float(np.mean(overlaps)) if overlaps else 0.,
                    n_disjoint=float(sum(value < .2 for value in overlaps)),
                    disjoint_frac=sum(value < .2 for value in overlaps)/max(len(overlaps), 1))
    return {key: float(value) for key, value in features.items()}


def select_instances(owner, name, exact_geometry):
    if getattr(owner, 'geometry_error', None):
        raise ValueError('live_ground_invalid_geometry')
    cache = getattr(owner, "_routed_candidate_cache", None)
    if cache is None:
        names = tuple(owner.config["candidate_universe"])
        if not names or name not in names:
            raise ValueError("Routed policy requires a fixed named candidate universe")
        geometry = Geometry(exact_geometry)
        grids = candidates.lift_grid(exact_geometry)
        raw, pools, origins = {}, {}, {}
        from trace_format.instance_policy314 import valid_mask
        for candidate_name in names:
            frames, origin = detections(owner.source, candidate_name, owner.scene.frames)
            if any(any(valid_mask(entry["mask"]) for entry in frame) and not exact_geometry.has(k)
                   for k, frame in enumerate(frames, 1)):
                raise ValueError("exact_depth_frame_unavailable")
            proposals, refused = candidates.lift(cache_for(candidate_name, frames), candidate_name,
                exact_geometry, floor=.3 if origin == "sam3" else 0., grids=grids, phrase=candidate_name)
            raw[candidate_name], origins[candidate_name] = frames, dict(source=origin, refused=refused)
            pools[candidate_name] = candidates.link(proposals, candidate_name)
        candidates.scene_candidates(pools, exact_geometry)
        cache = dict(geometry=geometry, candidates={key: accept_features(pools[key], raw[key], geometry) for key in names},
                     origins=origins)
        owner._routed_candidate_cache = cache
    if name not in cache["candidates"]:
        raise ValueError("Routed query lies outside the fixed candidate universe")
    geometry = cache["geometry"]
    selected, audit = owner.candidate_policy.select(cache["candidates"][name],
        lambda first, second: pair_features(first, second, geometry), geometry.depth)
    raw = []
    for value in selected:
        masks = np.zeros((32, *OUTPUT_SHAPE), bool)
        probabilities = np.zeros(32, float)
        for frame, mask in value["masks"].items():
            masks[frame-1] = mask
            probabilities[frame-1] = 1.
        raw.append(dict(instance_id=value["candidate_id"], masks=masks, prob=probabilities,
                        depth_cut_applied=audit["interior_depth_cut"]))
    return raw, {**audit, **cache["origins"][name], "mask_shape": list(OUTPUT_SHAPE),
                 "candidate_universe": list(owner.config["candidate_universe"])}
