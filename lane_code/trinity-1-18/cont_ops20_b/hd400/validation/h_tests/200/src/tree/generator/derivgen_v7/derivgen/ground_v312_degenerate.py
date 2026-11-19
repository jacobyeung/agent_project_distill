"""Pairwise native mask/OBB gates; no axis-aligned approximation to rotated boxes."""
from itertools import combinations, product
import numpy as np


def box_values(box):
    c = np.asarray(box['centroid'],float)
    lengths = np.asarray(box['axesLengths'],float)
    axes = np.asarray(box['normalizedAxes'],float).reshape(3,3)
    if (not all(np.isfinite(v).all() for v in (c,lengths,axes)) or np.any(lengths < 0)
            or not np.allclose(axes@axes.T,np.eye(3),atol=1e-4)):
        raise ValueError('invalid_operand_box')
    return c, lengths/2, axes


def corners(box):
    c,h,a = box_values(box)
    return c + (np.array(list(product((-1,1),repeat=3)))*h)@a


def contains(a,b):
    c,h,axes = box_values(a)
    return bool(np.all(np.abs((corners(b)-c)@axes.T) <= h+1e-9))


def overlaps(a,b):
    ca,ha,aa = box_values(a); cb,hb,ab = box_values(b)
    axes = list(aa)+list(ab)+[np.cross(x,y) for x in aa for y in ab]
    for axis in axes:
        norm = np.linalg.norm(axis)
        if norm < 1e-10:
            continue
        axis = axis/norm
        radius = np.abs(aa@axis)@ha + np.abs(ab@axis)@hb
        if abs((cb-ca)@axis) >= radius-1e-9:
            return False
    return True


def degeneracy_reasons(item, boxes, masks):
    reasons = set()
    for a,b in combinations(boxes,2):
        if np.any(np.asarray(masks[a],bool) & np.asarray(masks[b],bool)):
            reasons.add('operand_mask_overlap')
        if contains(boxes[a],boxes[b]) or contains(boxes[b],boxes[a]):
            reasons.add('operand_box_containment')
        sampled_relative = (item['type'] == 'object_rel_distance'
                            and item.get('target_distance_rule') in ('sampled_box_512', 'box_grid_5cm'))
        if overlaps(boxes[a],boxes[b]) and not sampled_relative:
            reasons.add('operand_box_overlap')
    if item['type'].startswith('object_rel_direction') or item['type'] == 'absolute_direction_object':
        stand,face = (boxes[item['roles'][k]] for k in ('stand','face'))
        u = box_values(face)[0]-box_values(stand)[0]
        u[2] = 0  # Native GT OBBs are world z-up.
        length = np.linalg.norm(u)
        if length <= 1e-12:
            reasons.add('facing_vector_below_object_extent')
        else:
            direction = u/length
            widths = [2*(np.abs(box_values(b)[2]@direction)@box_values(b)[1]) for b in (stand,face)]
            if length < max(widths):
                reasons.add('facing_vector_below_object_extent')
    return sorted(reasons)


def lifted_facing_too_short(item, objects):
    """Use the row's actual lifted heading and GT box widths in the same f1 frame."""
    if 'facing_extent_boxes' not in item:
        return False  # Standalone renderer fixtures have no GT annotations.
    stand,face = [item['roles'][k] for k in ('stand','face')]
    u = np.asarray(objects[face]['f1'])-np.asarray(objects[stand]['f1'])
    u[1] = 0
    length = np.linalg.norm(u)
    if length <= 1e-12:
        return True
    widths = [np.abs(np.asarray(b['axes_f1'])@(u/length))@np.asarray(b['lengths'])
              for b in item['facing_extent_boxes']]
    return length < max(widths)


def degeneracy_reasons_multi(item, boxsets, masks):
    """v3.14 distance rows: the pairwise gates over every instance pair of two different operand names."""
    reasons = set()
    for a, b in combinations(boxsets, 2):
        if np.any(np.asarray(masks[a], bool) & np.asarray(masks[b], bool)):
            reasons.add('operand_mask_overlap')
        for x, y in product(boxsets[a], boxsets[b]):
            reasons.update(r for r in degeneracy_reasons(dict(item, type=item['type']), {a: x, b: y},
                                                        {a: np.zeros(1, bool), b: np.zeros(1, bool)}))
    return sorted(reasons)
