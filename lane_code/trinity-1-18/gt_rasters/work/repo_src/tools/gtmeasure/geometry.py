from dataclasses import dataclass
import heapq
import itertools

import numpy as np
from scipy.spatial import cKDTree
import shapely

from .conventions import box_corners


EDGES = ((0, 1), (1, 2), (2, 0))


def dot(a, b):
    return np.sum(a * b, axis=-1)


def segment_squared(point, a, b):
    edge = b - a
    length = dot(edge, edge)
    t = np.clip(dot(point - a, edge) / np.where(length > 0, length, 1), 0, 1)
    delta = point - a - t[..., None] * edge
    return dot(delta, delta)


def point_triangle_squared(point, triangle):
    a, b, c = triangle[..., 0, :], triangle[..., 1, :], triangle[..., 2, :]
    u, v, w = b - a, c - a, point - a
    uu, uv, vv, wu, wv = dot(u, u), dot(u, v), dot(v, v), dot(w, u), dot(w, v)
    denominator = uu * vv - uv * uv
    safe = np.where(denominator > 0, denominator, 1)
    s, t = (vv * wu - uv * wv) / safe, (uu * wv - uv * wu) / safe
    normal = np.cross(u, v)
    normal_squared = dot(normal, normal)
    plane = dot(w, normal) ** 2 / np.where(normal_squared > 0, normal_squared, 1)
    inside = (denominator > 0) & (s >= 0) & (t >= 0) & (s + t <= 1)
    edges = np.minimum.reduce([segment_squared(point, a, b), segment_squared(point, b, c), segment_squared(point, c, a)])
    return np.maximum(np.where(inside, plane, edges), 0)


def segment_pair_squared(a, b, c, d):
    u, v, w = b - a, d - c, a - c
    aa, bb, cc, dd, ee = dot(u, u), dot(u, v), dot(v, v), dot(u, w), dot(v, w)
    denominator = aa * cc - bb * bb
    safe = np.where(denominator > 0, denominator, 1)
    s, t = (bb * ee - cc * dd) / safe, (aa * ee - bb * dd) / safe
    delta = w + s[..., None] * u - t[..., None] * v
    interior = np.where((denominator > 0) & (s >= 0) & (s <= 1) & (t >= 0) & (t <= 1), dot(delta, delta), np.inf)
    return np.minimum.reduce([interior, segment_squared(a, c, d), segment_squared(b, c, d),
                              segment_squared(c, a, b), segment_squared(d, a, b)])


def crosses_triangle(a, b, triangle):
    normal = np.cross(triangle[..., 1, :] - triangle[..., 0, :], triangle[..., 2, :] - triangle[..., 0, :])
    denominator = dot(b - a, normal)
    t = dot(triangle[..., 0, :] - a, normal) / np.where(denominator != 0, denominator, 1)
    point = a + t[..., None] * (b - a)
    return (denominator != 0) & (t >= 0) & (t <= 1) & (point_triangle_squared(point, triangle) <= 1e-22)


def triangle_pair_squared(a, b):
    result = np.full(np.broadcast_shapes(a.shape[:-2], b.shape[:-2]), np.inf)
    for vertex in range(3):
        result = np.minimum(result, point_triangle_squared(a[..., vertex, :], b))
        result = np.minimum(result, point_triangle_squared(b[..., vertex, :], a))
    for i, j in EDGES:
        result = np.where(crosses_triangle(a[..., i, :], a[..., j, :], b), 0, result)
        result = np.where(crosses_triangle(b[..., i, :], b[..., j, :], a), 0, result)
        for k, l in EDGES:
            result = np.minimum(result, segment_pair_squared(a[..., i, :], a[..., j, :], b[..., k, :], b[..., l, :]))
    return np.maximum(result, 0)


def triangles(obj):
    result = np.asarray(obj['triangles'], dtype=np.float64)
    if result.ndim != 3 or result.shape[1:] != (3, 3) or not len(result) or not np.isfinite(result).all():
        raise ValueError('measurement requires finite nonempty official instance triangles')
    return result


@dataclass
class Node:
    lower: np.ndarray
    upper: np.ndarray
    count: int
    faces: np.ndarray | None = None
    children: tuple = ()


def bvh(faces):
    lower, upper = faces.min(axis=(0, 1)), faces.max(axis=(0, 1))
    if len(faces) <= 8:
        return Node(lower, upper, len(faces), faces=faces)
    centers = faces.mean(axis=1)
    order = np.argsort(centers[:, np.argmax(np.ptp(centers, axis=0))], kind='stable')
    mid = len(order) // 2
    return Node(lower, upper, len(faces), children=(bvh(faces[order[:mid]]), bvh(faces[order[mid:]])))


def bound(a, b):
    gap = np.maximum(0, np.maximum(a.lower - b.upper, b.lower - a.upper))
    return float(dot(gap, gap))


def object_count(objects, label):
    ids = [obj['id'] for obj in objects if obj['label'] == label]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate official instance identity')
    return len(ids)


def object_size(obj):
    box_corners(obj['obb'])
    return float(2 * np.max(obj['obb']['axesLengths']))


def object_distance(a, b):
    aa, bb = triangles(a), triangles(b)
    if '_bvh' not in a:
        a['_bvh'] = bvh(aa)
    if '_bvh' not in b:
        b['_bvh'] = bvh(bb)
    tree_a, tree_b = a['_bvh'], b['_bvh']
    upper = float(np.min(cKDTree(aa.reshape(-1, 3)).query(bb.reshape(-1, 3), workers=1)[0])) ** 2
    serial = itertools.count()
    pending = [(bound(tree_a, tree_b), next(serial), tree_a, tree_b)]
    while pending and upper > 0:
        lower, _, left, right = heapq.heappop(pending)
        if lower >= upper:
            continue
        if left.faces is not None and right.faces is not None:
            upper = min(upper, float(triangle_pair_squared(left.faces[:, None], right.faces[None, :]).min()))
            continue
        pairs = ((child, right) for child in left.children) if left.children and (not right.children or left.count >= right.count) else ((left, child) for child in right.children)
        for child_a, child_b in pairs:
            lower = bound(child_a, child_b)
            if lower < upper:
                heapq.heappush(pending, (lower, next(serial), child_a, child_b))
    return float(np.sqrt(upper))


def camera_object_distance(obj, pose):
    pose = np.asarray(pose, dtype=np.float64)
    if pose.shape != (4, 4) or not np.isfinite(pose).all():
        raise ValueError('invalid camera-to-world pose')
    return float(np.sqrt(point_triangle_squared(pose[:3, 3], triangles(obj)).min()))


def room_area(objects):
    floors = [triangles(obj) for obj in objects if obj['label'] == 'floor']
    if not floors:
        raise ValueError('no official floor triangles')
    xy = np.concatenate(floors)[:, :, :2]
    polygons = shapely.polygons(xy)
    polygons = polygons[shapely.area(polygons) > 0]
    if not len(polygons):
        raise ValueError('official floor has zero projected area')
    return float(shapely.area(shapely.union_all(polygons)))
