"""Offline match of a response's accepted masks to GT instances (brief 08 part B).

GT raster format (rows_a2 / K1 rasters, npz): inst (F, H, W) int instance-id map with -1 background, ids, labels,
frame_indices. A response's accepted masks per operand: {operand: [{frame_index: bool (H, W)}, ...]}, one dict per
accepted candidate, frames keyed by the source frame index of the row's pins.

gt_instances(raster, operands)  -> {operand: [ids whose normalised label equals the operand]}
selected_ids(raster, accepted)  -> {operand: [GT id matched by each accepted candidate, or 'unmatched']}
A candidate matches the GT instance with the highest pixel-summed IoU over the frames it covers, if that IoU >= IOU_MIN.
"""
import re

import numpy as np

IOU_MIN = 0.5


def norm(s):
    return re.sub(r'\s+', ' ', str(s).strip().lower())


def gt_instances(raster, operands):
    labels = {int(i): str(l) for i, l in zip(raster['ids'], raster['labels'])}
    return {o: sorted(f'{norm(o)}:{i}' for i, l in labels.items() if norm(l) == norm(o)) for o in operands}


def match_candidate(raster, masks):
    frames = {int(f): k for k, f in enumerate(raster['frame_indices'])}
    inter, area = {}, 0
    for f, m in masks.items():
        if int(f) not in frames:
            raise ValueError(f'candidate frame {f} is not a raster pin')
        inst = raster['inst'][frames[int(f)]]
        m = np.asarray(m, bool)
        if m.shape != inst.shape:
            raise ValueError('mask and raster shapes differ')
        area += int(m.sum())
        ids, counts = np.unique(inst[m], return_counts=True)
        for i, c in zip(ids, counts):
            if i >= 0:
                inter[int(i)] = inter.get(int(i), 0) + int(c)
    best, best_iou = None, 0.0
    for i, c in inter.items():
        gt_area = sum(int((raster['inst'][frames[int(f)]] == i).sum()) for f in masks)
        iou = c / (area + gt_area - c)
        if iou > best_iou:
            best, best_iou = i, iou
    return (best if best_iou >= IOU_MIN else None), best_iou


def selected_ids(raster, accepted):
    labels = {int(i): str(l) for i, l in zip(raster['ids'], raster['labels'])}
    out = {}
    for operand, candidates in accepted.items():
        ids = []
        for masks in candidates:
            i, _ = match_candidate(raster, masks)
            ids.append('unmatched' if i is None else f'{norm(labels[i])}:{i}')
        out[operand] = ids
    return out
