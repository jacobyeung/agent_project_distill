"""Raw preparation functions preserved from the staged r1313 adapter sources."""

from pathlib import Path

import numpy as np

_PLY_DTYPES = {'float': '<f4', 'double': '<f8', 'uchar': 'u1', 'char': 'i1', 'int': '<i4', 'uint': '<u4', 'short': '<i2', 'ushort': '<u2'}


# Source: /scratch/jjyeung/distill_sync/repo/lane_code/trinity-1-18/gt_rasters/work/repo_src/gt_adapters/scannetpp_multilabel/prepare_gt_scene.py

def load_mesh(path):
    with Path(path).open('rb') as handle:
        element, counts, properties = None, {}, []
        face_type = None
        while True:
            raw = handle.readline()
            if not raw:
                raise ValueError('unterminated mesh header')
            fields = raw.decode('ascii').strip().split()
            if not fields:
                continue
            if fields[0] == 'format' and fields[1:] != ['binary_little_endian', '1.0']:
                raise ValueError('only the donor binary-little-endian PLY format is supported')
            if fields[0] == 'element':
                element = fields[1]
                counts[element] = int(fields[2])
            elif fields[0] == 'property' and element == 'vertex':
                if len(fields) != 3 or fields[1] not in _PLY_DTYPES:
                    raise ValueError('unsupported mesh vertex property')
                properties.append((fields[2], _PLY_DTYPES[fields[1]]))
            elif fields[0] == 'property' and element == 'face':
                if fields[1:4] != ['list', 'uchar', 'int'] or fields[4] not in ('vertex_indices', 'vertex_index'):
                    raise ValueError('unsupported mesh face list')
                face_type = np.dtype([('count', 'u1'), ('vertices', '<i4', (3,))])
            elif fields[0] == 'end_header':
                break
        dtype = np.dtype(properties)
        vertices = np.frombuffer(handle.read(counts['vertex'] * dtype.itemsize), dtype=dtype)
        if face_type is None:
            raise ValueError('triangle faces are required')
        faces = np.frombuffer(handle.read(counts['face'] * face_type.itemsize), dtype=face_type)
    if len(vertices) != counts['vertex'] or len(faces) != counts['face'] or not np.all(faces['count'] == 3):
        raise ValueError('mesh counts or triangle topology disagree with the header')
    xyz = np.column_stack([vertices[k] for k in ('x', 'y', 'z')]).astype(np.float32)
    indices = faces['vertices'].astype(np.int32)
    if not np.isfinite(xyz).all() or indices.min() < 0 or indices.max() >= len(xyz):
        raise ValueError('invalid source mesh vertices or indices')
    return xyz, indices


# Source: /scratch/jjyeung/distill_sync/repo/lane_code/trinity-1-18/gt_rasters/work/repo_src/gt_adapters/scannetpp_multilabel/mesh_membership.py

def build_memberships(faces, segment_ids, groups, face_basis):
    mapping = {}
    by_id = {}
    for group in groups:
        iid = int(group['objectId'] if 'objectId' in group else group['id'])
        if iid < 0 or iid > np.iinfo(np.int32).max or iid in by_id:
            raise ValueError('official instance IDs must be unique nonnegative int32 values')
        by_id[iid] = group
        for segment in group['segments']:
            mapping.setdefault(int(segment), set()).add(iid)
    keys = sorted(mapping)
    memberships = [sorted(mapping[key]) for key in keys]
    ids, offsets, indices = sorted(by_id), [0], []
    for iid in ids:
        # For a vertex basis, AND is exactly the intersection of vertex ID sets.
        belongs = np.isin(segment_ids, by_id[iid]['segments'])
        selected = np.flatnonzero(belongs if face_basis else belongs[faces].all(axis=1))
        indices.append(selected)
        offsets.append(offsets[-1] + len(selected))
    return {
        'membership_instance_ids': np.asarray(ids, dtype=np.int32),
        'membership_face_offsets': np.asarray(offsets, dtype=np.int64),
        'membership_face_indices': np.concatenate(indices).astype(np.int64) if indices else np.empty(0, np.int64),
        'segment_ids': np.asarray(keys, dtype=np.int64),
        'segment_offsets': np.r_[0, np.cumsum([len(row) for row in memberships])].astype(np.int64),
        'segment_instance_ids': np.asarray([iid for row in memberships for iid in row], dtype=np.int32),
    }


# Source: /scratch/jjyeung/distill_sync/repo/lane_code/trinity-1-18/gt_rasters/work/repo_src/gt_adapters/scannet_v1/scannet_adapter.py

def membership_boxes(vertices, faces, segmentation, aggregation, scene):
    """Preserve every official vertex membership; derive boxes without pose fitting."""
    if aggregation.get('sceneId') != 'scannet.' + scene:
        raise ValueError('aggregation source scene mismatch')
    segment_ids = np.asarray(segmentation['segIndices'])
    if segment_ids.shape != (len(vertices),) or segment_ids.dtype.kind not in 'iu' or np.any(segment_ids < 0):
        raise ValueError('ScanNet segmentation must label every source mesh vertex')
    groups = aggregation['segGroups']
    if not groups:
        raise ValueError('empty official instance aggregation')
    assigned = np.full(len(vertices), -1, dtype=np.int32)
    ids, group_ids, segments_seen = set(), set(), set()
    prepared, diagnostics = [], []
    for group in groups:
        iid, gid = group['objectId'], group['id']
        if (type(iid) is not int or type(gid) is not int or not 0 <= iid < 2**31
                or iid in ids or gid in group_ids or not isinstance(group['label'], str) or not group['label'].strip()):
            raise ValueError('invalid/duplicate official instance identity or label')
        ids.add(iid); group_ids.add(gid)
        segs = group['segments']
        if not segs or any(type(s) is not int or s < 0 for s in segs) or len(set(segs)) != len(segs):
            raise ValueError('invalid official segment list')
        if set(segs) & segments_seen:
            raise ValueError('source segment belongs to multiple instance groups')
        segments_seen.update(segs)
        present = set(np.unique(segment_ids).tolist())
        if not set(segs) <= present:
            raise ValueError('official instance refers to absent mesh segment')
        selected = np.isin(segment_ids, segs)
        assigned[selected] = iid
        points = vertices[selected].astype(np.float64)
        lo, hi = points.min(axis=0), points.max(axis=0)
        half = (hi - lo) / 2
        if not np.isfinite(points).all() or np.any(half <= 0):
            raise ValueError('source-derived box is degenerate/nonfinite; no padding is allowed')
        prepared.append({'id': iid, 'objectId': iid, 'label': group['label'],
            'obb': {'centroid': ((lo + hi) / 2).tolist(), 'axesLengths': half.tolist(),
                    'normalizedAxes': np.eye(3).ravel().tolist()}})
        diagnostics.append({'instance_id': iid, 'source_group_id': gid, 'segments': segs,
                            'member_vertex_count': int(selected.sum()), 'min_world': lo.tolist(), 'max_world': hi.tolist()})
    tri = assigned[faces]
    face_ids = np.where((tri == tri[:, :1]).all(axis=1), tri[:, 0], -1).astype(np.int32)
    for row in diagnostics:
        row['face_count'] = int((face_ids == row['instance_id']).sum())
        if not row['face_count']:
            # The unchanged donor falls back to box triangles for empty instances.
            raise ValueError('official instance has no fully associated triangle; box fallback is not admitted')
    return prepared, face_ids, assigned, diagnostics
