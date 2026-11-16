from __future__ import annotations
import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
import cv2
import numpy as np
from gt_scene_assets import read_json

DATASET = 'arkitscenes'
UPSTREAM_COMMIT = '474aaa83d7b1c9080619d8485de2d7c885c01fc5'
TIMESTAMP_TOLERANCE = Decimal('0.001')
CONTAINMENT_EPSILON_M = 1e-6
MASK_SEMANTICS = 'official_box_conditioned_mesh_projection_not_native_instance_segmentation'


def timestamp(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?', value):
        raise ValueError('timestamp must be a literal nonnegative decimal string')
    try:
        result = Decimal(value)
    except InvalidOperation as error:
        raise ValueError('invalid source timestamp') from error
    if not result.is_finite():
        raise ValueError('nonfinite source timestamp')
    return result


def regular(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'required regular source file missing: {path}')
    return path


def timestamped_files(directory, scene, suffix):
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError(f'required source directory missing: {directory}')
    pattern = re.compile(re.escape(scene) + r'_([0-9]+(?:\.[0-9]+)?)' + re.escape(suffix))
    rows = []
    for path in directory.glob('*' + suffix):
        match = pattern.fullmatch(path.name)
        if match is None:
            raise ValueError(f'unsupported timestamped filename: {path.name}')
        regular(path)
        rows.append({'path': path, 'timestamp': match[1], 'time': timestamp(match[1])})
    rows.sort(key=lambda row: row['time'])
    if not rows or len({row['time'] for row in rows}) != len(rows):
        raise ValueError('empty or duplicate source timestamp census')
    for ordinal, row in enumerate(rows):
        row['ordinal'] = ordinal
    return rows


def timeline_rows(rows):
    return [{'ordinal': row['ordinal'], 'filename': row['path'].name, 'timestamp': row['timestamp']} for row in rows]


def timeline_sha(rows):
    payload = json.dumps(timeline_rows(rows), sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(payload).hexdigest()


def parse_trajectory(path):
    rows = []
    for line_number, line in enumerate(regular(path).read_text().splitlines(), 1):
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) != 7:
            raise ValueError(f'malformed trajectory line {line_number}: expected seven fields')
        time = timestamp(fields[0])
        values = np.asarray([float(value) for value in fields[1:]], dtype=np.float64)
        if not np.isfinite(values).all() or (rows and time <= rows[-1]['time']):
            raise ValueError('trajectory must be finite with strictly increasing unique timestamps')
        rotation = cv2.Rodrigues(values[:3])[0]
        if not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-8) or not np.isclose(np.linalg.det(rotation), 1, atol=1e-8):
            raise ValueError('trajectory rotation is not proper rigid')
        pose = np.eye(4, dtype=np.float64)
        pose[:3, :3] = rotation.T
        pose[:3, 3] = -rotation.T @ values[3:]
        rows.append({'timestamp': fields[0], 'time': time, 'pose': pose,
                     'line_1based': line_number, 'world_to_camera_axis_angle_translation': values.tolist()})
    if not rows:
        raise ValueError('trajectory is empty')
    return rows


def match_timestamp(rows, wanted, kind):
    candidates = [row for row in rows if abs(row['time'] - wanted) <= TIMESTAMP_TOLERANCE]
    if not candidates:
        raise ValueError(f'missing {kind} within 0.001 seconds of {wanted}')
    if len(candidates) != 1:
        raise ValueError(f'ambiguous {kind} within 0.001 seconds of {wanted}')
    return candidates[0]


def parse_intrinsic(path):
    values = np.asarray([float(value) for value in regular(path).read_text().split()], dtype=np.float64)
    if values.shape != (6,) or not np.isfinite(values).all():
        raise ValueError('pincam must contain six finite values')
    width, height, fx, fy, cx, cy = values
    if width != int(width) or height != int(height) or min(width, height, fx, fy) <= 0 or not (0 <= cx < width and 0 <= cy < height):
        raise ValueError('invalid official pincam dimensions or focal/principal values')
    return np.asarray([[fx, 0, cx], [0, fy, cy], [0, 0, 1]], dtype=np.float64), (int(height), int(width))


def parse_annotations(path):
    raw = read_json(regular(path))
    if not isinstance(raw, dict) or raw.get('skipped') is not False or not isinstance(raw.get('data'), list) or not raw['data']:
        raise ValueError('official annotation must be non-skipped with nonempty data')
    parsed = []
    for index, item in enumerate(raw['data']):
        try:
            uid, label = item['uid'], item['label']
            obb = item['segments']['obbAligned']
            center = np.asarray(obb['centroid'], dtype=np.float64)
            lengths = np.asarray(obb['axesLengths'], dtype=np.float64)
            axes = np.asarray(obb['normalizedAxes'], dtype=np.float64).reshape(3, 3)
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f'malformed official annotation at index {index}') from error
        if not isinstance(uid, str) or not uid.strip() or not isinstance(label, str) or not label.strip():
            raise ValueError('official instance UID and label must be nonempty strings')
        if center.shape != (3,) or lengths.shape != (3,) or not all(np.isfinite(value).all() for value in (center, lengths, axes)) or np.any(lengths <= 0):
            raise ValueError('malformed annotation OBB: finite center and positive full extents required')
        if not np.allclose(axes @ axes.T, np.eye(3), atol=1e-4) or not np.isclose(abs(np.linalg.det(axes)), 1, atol=1e-4):
            raise ValueError('malformed annotation OBB axes: expected orthonormal row axes')
        if not np.allclose(np.abs(axes[2]), [0, 0, 1], atol=1e-3):
            raise ValueError('unsupported annotation world convention: obbAligned must be Z vertical')
        parsed.append((uid, index, label, center, lengths, axes))
    if len({row[0] for row in parsed}) != len(parsed):
        raise ValueError('duplicate official annotation UID')
    groups, identities = [], []
    for iid, (uid, index, label, center, lengths, axes) in enumerate(sorted(parsed, key=lambda row: row[0])):
        groups.append({'id': iid, 'objectId': iid, 'label': label,
                       'obb': {'centroid': center.tolist(), 'axesLengths': (lengths / 2).tolist(), 'normalizedAxes': axes.reshape(-1).tolist()}})
        identities.append({'instance_id': iid, 'source_uid': uid, 'source_annotation_index': index,
                           'label': label, 'source_full_extents_m': lengths.tolist()})
    return groups, identities


def associate_mesh(vertices, faces, groups):
    vertices = np.asarray(vertices, dtype=np.float64)
    faces = np.asarray(faces, dtype=np.int64)
    if vertices.ndim != 2 or vertices.shape[1] != 3 or not np.isfinite(vertices).all() or faces.ndim != 2 or faces.shape[1] != 3 or not len(faces):
        raise ValueError('malformed source triangle mesh')
    if faces.min() < 0 or faces.max() >= len(vertices):
        raise ValueError('source triangle index is out of bounds')
    memberships = np.zeros(len(vertices), dtype=np.int32)
    owners = np.full(len(vertices), -1, dtype=np.int32)
    for group in groups:
        obb = group['obb']
        local = (vertices - obb['centroid']) @ np.asarray(obb['normalizedAxes']).reshape(3, 3).T
        inside = np.all(np.abs(local) <= np.asarray(obb['axesLengths']) + CONTAINMENT_EPSILON_M, axis=1)
        owners[inside] = group['id']
        memberships += inside
    owners[memberships != 1] = -1
    tri_owners = owners[faces]
    face_ids = np.where(np.all(tri_owners == tri_owners[:, :1], axis=1), tri_owners[:, 0], -1).astype(np.int32)
    for group in groups:
        candidates = np.flatnonzero((face_ids >= 0) & (face_ids != group['id']))
        if not len(candidates):
            continue
        obb = group['obb']
        local = (vertices - obb['centroid']) @ np.asarray(obb['normalizedAxes']).reshape(3, 3).T
        triangles = local[faces[candidates]]
        half = np.asarray(obb['axesLengths']) + CONTAINMENT_EPSILON_M
        possible_intersection = np.all((triangles.max(axis=1) >= -half) & (triangles.min(axis=1) <= half), axis=1)
        face_ids[candidates[possible_intersection]] = -1
    diagnostics = []
    for group in groups:
        count = int(np.count_nonzero(face_ids == group['id']))
        if count == 0:
            raise ValueError(f'unsupported annotated instance {group["id"]}: no unambiguous mesh faces; OBB fallback forbidden')
        diagnostics.append({'instance_id': group['id'], 'face_count': count})
    return face_ids, {'instances': diagnostics, 'unassigned_faces': int(np.count_nonzero(face_ids < 0)),
                      'overlapping_vertices': int(np.count_nonzero(memberships > 1)),
                      'containment_epsilon_m': CONTAINMENT_EPSILON_M,
                      'association': 'all_three_vertices_in_one_OBB_and_no_other_OBB_axis_interval_overlap',
                      'mask_semantics': MASK_SEMANTICS}
