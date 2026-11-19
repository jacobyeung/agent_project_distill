"""Carried-track files: one gzipped JSON per (seed set, frame set, capture) with RLE anchor masks. numpy only."""
import gzip, json
from pathlib import Path
import numpy as np
import mc_common as C


def track_dir(seed_set, frame_set, root=None):
    return Path(root or C.OUT/'track')/f'{seed_set}_{frame_set}'


def track_path(seed_set, frame_set, canonical, root=None):
    return track_dir(seed_set, frame_set, root)/(C.stub(canonical)+'.json.gz')


def load_seeds(canonical):
    """Seed masks of one capture from out/seeds, keyed like 'S_A0_3'."""
    path = C.OUT/'seeds'/(C.stub(canonical)+'.npz')
    C.read(path)
    with np.load(path) as z:
        shape = tuple(int(x) for x in z['shape'])
        return {k: C.unpack(shape, z[k]) for k in z.files if k != 'shape'}


def object_record(k, name, instance, seed_slot, tracker_frames, anchor_positions, result, seed_mask):
    """Anchor slot s (1..32) sits at tracker frame anchor_positions[s-1] (None: outside the tracked frames).
    The seed anchor keeps the seed mask itself."""
    anchors = []
    for s, t in enumerate(anchor_positions, 1):
        if s == seed_slot:
            anchors.append(dict(slot=s, seed=True, carried=True, score=result[t][1], rle=C.rle_encode(seed_mask)))
            continue
        if t is None:
            anchors.append(dict(slot=s, seed=False, carried=False, score=None, rle=None, tracked=False))
            continue
        mask, score = result[t]
        carried = bool(score > 0 and mask.any())
        anchors.append(dict(slot=s, seed=False, carried=carried, score=score, rle=C.rle_encode(mask) if carried else None,
                            positive_empty=bool(score > 0 and not mask.any())))
    return dict(k=k, name=name, instance=instance, seed_slot=seed_slot, shape=list(seed_mask.shape), tracker_frames=list(tracker_frames),
                scores=[result[t][1] for t in range(len(tracker_frames))], anchors=anchors)


def anchor_masks(obj):
    """(32, H, W) bool stack of the carried track; empty anchors are zero."""
    shape = tuple(obj['shape'])
    if any(a['rle'] is not None and tuple(a['rle']['size']) != shape for a in obj['anchors']):
        raise ValueError(f'anchor mask size differs from {shape}')
    out = np.zeros((32,)+shape, bool)
    for a in obj['anchors']:
        if a['carried'] and a['rle'] is not None:
            out[a['slot']-1] = C.rle_decode(a['rle'])
    return out


def read_track(path):
    return C.read_json(path)
