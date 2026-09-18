"""Sparse official memberships over unique source faces; no geometry duplication."""
import numpy as np

SPARSE_KEYS = {'membership_instance_ids', 'membership_face_offsets', 'membership_face_indices',
               'segment_ids', 'segment_offsets', 'segment_instance_ids'}


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


def instance_faces(mesh, iid):
    if 'membership_instance_ids' not in mesh:
        return np.flatnonzero(mesh['instance_ids'] == int(iid))
    ids = mesh['membership_instance_ids']
    slot = np.searchsorted(ids, iid)
    if slot == len(ids) or ids[slot] != iid:
        return np.empty(0, np.int64)
    start, end = mesh['membership_face_offsets'][slot:slot + 2]
    return mesh['membership_face_indices'][start:end]


def instance_counts(mesh):
    if 'membership_instance_ids' in mesh:
        return mesh['membership_instance_ids'], np.diff(mesh['membership_face_offsets'])
    return np.unique(mesh['instance_ids'], return_counts=True)


def validate_memberships(mesh, annotation_ids):
    for key in SPARSE_KEYS:
        if mesh[key].ndim != 1 or mesh[key].dtype.kind not in 'iu':
            raise ValueError('membership arrays must be one-dimensional integers')
    ids = mesh['membership_instance_ids']
    if set(ids.tolist()) != annotation_ids or np.any(ids < 0) or np.any(np.diff(ids) <= 0):
        raise ValueError('sparse instance census differs from official annotations')
    for keys, offsets, values, bound in (
        (ids, mesh['membership_face_offsets'], mesh['membership_face_indices'], len(mesh['faces'])),
        (mesh['segment_ids'], mesh['segment_offsets'], mesh['segment_instance_ids'], None),
    ):
        if np.any(np.diff(keys) <= 0) or len(offsets) != len(keys) + 1 or offsets[0] != 0 or offsets[-1] != len(values) or np.any(np.diff(offsets) < 0):
            raise ValueError('invalid membership CSR offsets or key ordering')
        if bound is not None and (np.any(values < 0) or np.any(values >= bound)):
            raise ValueError('membership face index outside unique source geometry')
        if bound is None and not set(values.tolist()).issubset(annotation_ids):
            raise ValueError('segment membership contains an unofficial ID')
        # Adjacent entries must increase except across CSR row boundaries.
        bad = np.flatnonzero(np.diff(values) <= 0) + 1
        if len(np.setdiff1d(bad, offsets)):
            raise ValueError('membership rows must be sorted and duplicate-free')


def mesh_candidate(provider, mesh, iid, pose, intrinsics, height, width):
    selected = instance_faces(mesh, iid)
    if not len(selected):
        return False
    points = mesh['vertices'][np.unique(mesh['faces'][selected])]
    # Reject only a mesh wholly behind the donor near plane. This intentionally
    # over-accepts off-screen and crossing meshes; the unchanged renderer decides.
    depth = (points.astype(np.float64) - pose[:3, 3]) @ pose[:3, 2]
    return bool(np.any(depth > 0.05))
