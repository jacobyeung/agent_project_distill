"""Deterministic clip/label targets from first-hit instance rasters."""
import argparse
import collections
import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


STRUCTURAL = re.compile(r'(^|\b)(wall|floor|ceiling|object|otherfurniture|otherstructure|otherprop|remove|split|unknown|'
                        r'structure|room|background|stuff|misc)(\b|$)')
MIN_VIS = 0.002
SHAPE = (32, 240, 320)


@dataclass
class ClipUnits:
    scene: str
    qid: str
    labels: list[str]
    kind: list[str]
    presence: np.ndarray
    mass: np.ndarray
    point: np.ndarray
    largest: np.ndarray
    _inst: np.ndarray = field(default=None, repr=False)
    _label_ids: dict = field(default_factory=dict, repr=False)
    _rgb_wh: tuple = (320, 240)


def _hash(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _label(value):
    return str(value).strip().lower()


def _labels(z):
    if not {'ids', 'labels'} <= set(z.files):
        raise NotImplementedError('p013 rasters need external SCENE_VISIBILITY labels and recording aggregation; use r7')
    ids, labels = z['ids'], z['labels']
    if (ids.ndim != 1 or labels.shape != ids.shape or not np.issubdtype(ids.dtype, np.integer)
            or labels.dtype.kind != 'U' or np.any(ids < 0) or len(np.unique(ids)) != len(ids)):
        raise ValueError('Expected unique nonnegative instance ids and aligned string labels')
    return {int(i): _label(label) for i, label in zip(ids, labels)}


def _rows(path):
    with Path(path).open() as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def _source(source):
    """Accept an index row (absolute path), or resolve a native c/scene/clip13.npz via clips.jsonl."""
    if isinstance(source, dict):
        return Path(source['path']), str(source['scene']), str(source['qid']), tuple(source['rgb_wh'])
    path = Path(source)
    embedded = None
    with np.load(path, allow_pickle=False) as z:
        _labels(z)
        if {'scene', 'qid'} <= set(z.files):
            embedded = path, str(z['scene'].item()), str(z['qid'].item()), tuple(z['rgb_wh']) if 'rgb_wh' in z else (320, 240)
    for index in dict.fromkeys((path.parent / 'clips.jsonl', path.parent.parent.parent / 'clips.jsonl')):
        if index.is_file():
            for row in _rows(index):
                if (index.parent / row['path']).resolve() == path.resolve():
                    return path, str(row['scene']), str(row['qid']), tuple(row['rgb_wh'])
    if embedded is not None:
        return embedded
    raise ValueError('r7 filenames shorten qid; provide its clips.jsonl index or a row with path, scene and full qid')


def _raster(source):
    path, scene, qid, rgb_wh = _source(source)
    if len(rgb_wh) != 2 or any(int(v) != v or v <= 0 for v in rgb_wh):
        raise ValueError('Expected positive RGB width and height')
    with np.load(path, allow_pickle=False) as z:
        labels = _labels(z)
        if not {'inst', 'used'} <= set(z.files):
            raise ValueError('r7 requires inst and used arrays')
        inst, used = z['inst'], z['used']
    if (inst.shape != SHAPE or not np.issubdtype(inst.dtype, np.integer)
            or used.shape != (32,) or used.dtype != np.bool_):
        raise ValueError('Expected integer inst[32,240,320] and boolean used[32]')
    if np.any(inst < -2) or np.any(inst[used] == -2):
        raise ValueError('Failed-gate pixels cannot appear in used frames')
    if not set(int(i) for i in np.unique(inst) if i >= 0) <= set(labels):
        raise ValueError('Raster instance missing from recording aggregation')
    return scene, qid, inst, used, labels, tuple(map(int, rgb_wh))


def _visible(inst, used, aggregation, ignored=()):
    by_label = collections.defaultdict(list)
    for iid, label in aggregation.items():
        if label and not STRUCTURAL.search(label):
            by_label[label].append(iid)
    counts = []
    for index, (frame, valid) in enumerate(zip(inst, used)):
        ids, nums = np.unique(frame, return_counts=True) if valid else ([], [])
        counts.append({i: n for i, n in zip(ids, nums) if (index, int(i)) not in ignored})
    visible = [label for label, ids in by_label.items()
               if any(max((c.get(i, 0) for i in ids), default=0) / (240 * 320) >= MIN_VIS for c in counts)]
    return by_label, counts, visible


def clip_ineligibility(source):
    """Return the admission filter reason, or None for an eligible clip."""
    _, _, inst, used, aggregation, _ = _raster(source)
    if used.sum() < 8:
        return 'n_used_lt_8'
    from .ground_target_filter import ignored_targets
    if not _visible(inst, used, aggregation, ignored_targets(source))[2]:
        return 'no_visible_label'
    return None


def grid_for(rgb_wh, processor_settings=None):
    """Merged grid for C1 duplicate layout; size, when supplied, is the total video budget."""
    from transformers.models.qwen3_vl.video_processing_qwen3_vl import smart_resize
    from .pose_samples import DEFAULT_PIXELS
    settings = processor_settings or {}
    w, h = rgb_wh
    patch, merge = settings.get('patch_size', 16), settings.get('merge_size', 2)
    temporal = settings.get('temporal_patch_size', 2)
    count = settings.get('num_frames', 64)
    pixels = settings.get('pixels_per_frame', DEFAULT_PIXELS)
    size = settings.get('size', dict(shortest_edge=count * pixels[0], longest_edge=count * pixels[1]))
    if patch != 16 or merge != 2 or temporal != 2 or count <= 0 or count % temporal:
        raise ValueError('Expected Qwen3.5 patch 16, merge 2 and an even positive video frame count')
    h, w = smart_resize(num_frames=count, height=h, width=w, temporal_factor=temporal,
                        factor=patch * merge, min_pixels=size['shortest_edge'], max_pixels=size['longest_edge'])
    return h // (patch * merge), w // (patch * merge)


def _point(mask):
    """Match carrier_c1_data.mask_target's integer, stable centroid-nearest in-mask point."""
    from .carrier_c1_data import _grid_hits
    yx = np.argwhere(mask)
    for y, x in yx[np.square(yx - yx.mean(axis=0)).sum(axis=1).argsort(kind='stable')]:
        u, v = int((x + .5) / mask.shape[1] * 1000), int((y + .5) / mask.shape[0] * 1000)
        if _grid_hits(mask, u, v):
            return u, v
    raise ValueError('No integer grid point maps back inside the GT mask')


def units_for_clip(npz_path, grid, vocab, *, max_visible=24, absent_share=0.10, seed_key):
    if (len(grid) != 2 or any(int(v) != v or v <= 0 for v in grid)
            or int(max_visible) != max_visible or max_visible < 0 or not 0 <= absent_share < 1):
        raise ValueError('Invalid grid, visible limit or absent share')
    gh, gw = (int(v) for v in grid)
    scene, qid, inst, used, aggregation, rgb_wh = _raster(npz_path)
    from .ground_target_filter import ignored_targets
    ignored = ignored_targets(npz_path)
    by_label, counts, visible = _visible(inst, used, aggregation, ignored)
    visible = sorted(visible, key=lambda label: (_hash(f'{qid}|{label}'), label))[:max_visible]
    absent = {_label(v) for v in vocab} - set(aggregation.values())
    absent = {v for v in absent if v and not STRUCTURAL.search(v)}
    n_absent = math.ceil(absent_share / (1 - absent_share) * len(visible))
    absent = sorted(absent, key=lambda label: (_hash(f'{seed_key}|{label}'), label))[:n_absent]
    labels = visible + absent
    presence = np.full((len(labels), 32), np.nan, np.float32)
    mass = np.zeros((len(labels), 32, 2 * gh, 2 * gw), np.float32)
    point = np.full((len(labels), 32, 2), np.nan, np.float32)
    largest = np.full((len(labels), 32), -1, np.int32)
    cells = ((np.arange(240)[:, None] + .5) / 240 * (2 * gh)).astype(int) * (2 * gw)
    cells = cells + ((np.arange(320)[None, :] + .5) / 320 * (2 * gw)).astype(int)
    for q, label in enumerate(labels):
        ids = sorted(by_label.get(label, []))
        for f in np.flatnonzero(used):
            if any((int(f), iid) in ignored for iid in ids):
                continue
            best = max(ids, key=lambda i: (counts[f].get(i, 0), -i)) if ids else -1
            area = counts[f].get(best, 0) if best >= 0 else 0
            if not area:
                presence[q, f] = 0
                continue
            largest[q, f] = best
            if area / (240 * 320) < MIN_VIS:
                continue
            presence[q, f] = 1
            union = np.isin(inst[f], ids)
            values = np.bincount(cells[union], minlength=4 * gh * gw).astype(np.float32)
            mass[q, f] = (values / values.sum()).reshape(2 * gh, 2 * gw)
            point[q, f] = _point(inst[f] == best)
    return ClipUnits(scene, qid, labels, ['visible'] * len(visible) + ['clip_absent'] * len(absent),
                     presence, mass, point, largest, inst, dict(by_label), rgb_wh)


def to_tensors(units):
    import torch
    valid = np.isfinite(units.presence)
    point_valid = (units.presence == 1) & np.isfinite(units.point).all(axis=-1)
    return dict(presence=torch.from_numpy(np.nan_to_num(units.presence)), presence_valid=torch.from_numpy(valid),
                mass=torch.from_numpy(units.mass), point=torch.from_numpy(np.nan_to_num(units.point)),
                point_valid=torch.from_numpy(point_valid))


def eval_masks(units, q, f):
    """Union instances after RGB nearest resize and evalx's two cross erosions."""
    if not 0 <= q < len(units.labels) or not 0 <= f < 32:
        raise IndexError('Query or frame outside clip')
    if units._inst is None:
        raise ValueError('Evaluation masks require units loaded from an instance raster')
    from PIL import Image
    w, h = units._rgb_wh
    union = np.zeros((h, w), bool)
    for iid in units._label_ids.get(units.labels[q], []):
        mask = np.asarray(Image.fromarray(units._inst[f] == iid).resize((w, h), Image.Resampling.NEAREST))
        eroded = erode_cross(mask, iterations=2)
        union |= eroded if eroded.sum() >= 8 else mask
    return union


def erode_cross(mask, iterations=2):
    """Match scipy.ndimage.binary_erosion's default 2-D structure and border."""
    result = np.asarray(mask, dtype=bool).copy()
    for _ in range(iterations):
        padded = np.pad(result, 1, constant_values=False)
        result = (padded[1:-1, 1:-1] & padded[:-2, 1:-1] & padded[2:, 1:-1]
                  & padded[1:-1, :-2] & padded[1:-1, 2:])
    return result


def in_mask(points, masks):
    """Broadcast canvas [...,2] points against boolean [...,H,W] masks; invalid points miss."""
    points, masks = np.asarray(points), np.asarray(masks)
    if points.shape[-1:] != (2,) or masks.ndim < 2 or masks.dtype != np.bool_:
        raise ValueError('Expected canvas xy points and boolean masks')
    shape = np.broadcast_shapes(points.shape[:-1], masks.shape[:-2])
    points = np.broadcast_to(points, shape + (2,))
    masks = np.broadcast_to(masks, shape + masks.shape[-2:])
    valid = np.isfinite(points).all(axis=-1) & ((points >= 0) & (points <= 1000)).all(axis=-1)
    safe = np.clip(np.nan_to_num(points), 0, 1000)
    h, w = masks.shape[-2:]
    x = np.minimum((safe[..., 0] / 1000 * w).astype(int), w - 1)
    y = np.minimum((safe[..., 1] / 1000 * h).astype(int), h - 1)
    flat = masks.reshape((-1, h * w))
    return (flat[np.arange(flat.shape[0]), (y * w + x).reshape(-1)].reshape(shape) & valid)


def build_index(clips_jsonl_paths, *, exclude_scenes, holdout_fraction=0.05, seed=17, root=None,
                remove_files=(), ground_target_filter=False):
    """Split whole recordings before counting the >=20-training-recording vocabulary."""
    if not 0 <= holdout_fraction < 1:
        raise ValueError('Holdout fraction must lie in [0,1)')
    paths = [clips_jsonl_paths] if isinstance(clips_jsonl_paths, (str, Path)) else clips_jsonl_paths
    excluded = set(exclude_scenes)
    rows, identities = [], set()
    filtered = collections.Counter()
    from .ground_target_filter import TargetFilter
    targets = TargetFilter(remove_files, shape_filter=ground_target_filter) if remove_files or ground_target_filter else None
    for index in paths:
        for row in _rows(index):
            if row['scene'] in excluded:
                continue
            identity = (row['scene'], row['qid'])
            if identity in identities:
                raise ValueError('Duplicate clip identity')
            identities.add(identity)
            base = Path(root) if root is not None else Path(index).parent
            row = {**row, 'path': str((base / row['path']).resolve())}
            if targets is not None:
                row = targets.clip({**row, 'source_index': str(Path(index).resolve())})
            reason = clip_ineligibility(row)
            if reason:
                filtered[reason] += 1
                continue
            rows.append(row)
    scenes = sorted({r['scene'] for r in rows}, key=lambda scene: (_hash(scene), scene))
    held = set(scenes[:math.ceil(len(scenes) * holdout_fraction)])
    train = [r for r in rows if r['scene'] not in held]
    val = [r for r in rows if r['scene'] in held]
    assert not ({r['scene'] for r in train} & {r['scene'] for r in val})
    assert not ({r['scene'] for r in rows} & excluded)
    recordings = collections.defaultdict(set)
    for row in train:
        with np.load(row['path'], allow_pickle=False) as z:
            for label in set(_labels(z).values()):
                if label and not STRUCTURAL.search(label):
                    recordings[label].add(row['scene'])
    order = lambda row: (_hash(f'{seed}|{row["qid"]}'), row['scene'], row['qid'])
    result = dict(train=sorted(train, key=order), val=sorted(val, key=order),
                vocab=sorted(label for label, scenes in recordings.items() if len(scenes) >= 20),
                filtered_clips=dict(total=sum(filtered.values()), **dict(filtered)))
    if targets is not None:
        result['target_filter'] = targets.report()
    return result


def audit(clips, root, n=50):
    if n < 0:
        raise ValueError('Audit sample count must be nonnegative')
    index = build_index(clips, exclude_scenes=[], root=root)
    rows = sorted(index['train'] + index['val'], key=lambda row: (_hash(row['qid']), row['qid']))[:n]
    reports = []
    for row in rows:
        units = units_for_clip(row, grid_for(row['rgb_wh']), index['vocab'], seed_key=f'17|{row["qid"]}')
        positive = units.presence == 1
        values = units.mass[positive]
        entropy = -(values * np.log(np.maximum(values, np.finfo(np.float32).tiny))).sum(axis=(-2, -1))
        areas = np.array([np.count_nonzero(eval_masks(units, q, f)) / np.prod(units._rgb_wh)
                          for q, f in zip(*np.where(positive))])
        reports.append(dict(scene=units.scene, qid=units.qid, label_count=len(units.labels),
                            visible_count=units.kind.count('visible'), clip_absent_count=units.kind.count('clip_absent'),
                            presence={'1': int(positive.sum()), '0': int((units.presence == 0).sum()),
                                      'ignore': int(np.isnan(units.presence).sum())},
                            mean_mass_entropy=float(entropy.mean()) if len(entropy) else None,
                            size_bins={'<1%': int((areas < .01).sum()),
                                       '1-5%': int(((areas >= .01) & (areas <= .05)).sum()),
                                       '>5%': int((areas > .05).sum())}))
    return dict(clips=reports, vocab=index['vocab'], clip_count=len(reports))


def main(argv=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    cmd = sub.add_parser('audit')
    cmd.add_argument('--clips', required=True)
    cmd.add_argument('--root', required=True)
    cmd.add_argument('--n', type=int, default=50)
    cmd.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    result = audit(args.clips, args.root, args.n)
    with Path(args.out).open('x') as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write('\n')


if __name__ == '__main__':
    main()
