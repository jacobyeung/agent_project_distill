"""Read prep_v2 memberships without collapsing faces shared by official instances."""
import numpy as np

SPARSE_KEYS = {
    'membership_instance_ids', 'membership_face_offsets', 'membership_face_indices',
    'segment_ids', 'segment_offsets', 'segment_instance_ids',
}


def instance_faces(mesh, instance_id):
    if 'membership_instance_ids' not in mesh:
        return np.where(mesh['instance_ids'] == int(instance_id))[0]
    ids = mesh['membership_instance_ids']
    slot = np.searchsorted(ids, instance_id)
    if slot == len(ids) or ids[slot] != instance_id:
        return np.empty(0, dtype=np.int64)
    start, end = mesh['membership_face_offsets'][slot:slot + 2]
    return mesh['membership_face_indices'][start:end]


def validate_memberships(mesh, annotation_ids):
    for key in SPARSE_KEYS:
        if mesh[key].ndim != 1 or mesh[key].dtype.kind not in 'iu':
            raise ValueError('membership arrays must be one-dimensional integers')
    ids = mesh['membership_instance_ids']
    if (not annotation_ids or set(ids.tolist()) != annotation_ids
            or np.any(ids < 0) or np.any(ids > np.iinfo(np.int32).max)):
        raise ValueError('sparse instance census differs from official annotations')
    for keys, offsets, values, bound in (
        (ids, mesh['membership_face_offsets'], mesh['membership_face_indices'], len(mesh['faces'])),
        (mesh['segment_ids'], mesh['segment_offsets'], mesh['segment_instance_ids'], None),
    ):
        # Direct comparisons also reject descending unsigned integers; diff can wrap.
        if (np.any(keys[1:] <= keys[:-1]) or len(offsets) != len(keys) + 1
                or offsets[0] != 0 or offsets[-1] != len(values)
                or np.any(offsets[1:] < offsets[:-1])):
            raise ValueError('invalid membership CSR offsets or key ordering')
        if bound is not None and (np.any(values < 0) or np.any(values >= bound)):
            raise ValueError('membership face index outside unique source geometry')
        if bound is None and not set(values.tolist()).issubset(annotation_ids):
            raise ValueError('segment membership contains an unofficial ID')
        bad = np.flatnonzero(values[1:] <= values[:-1]) + 1
        if len(np.setdiff1d(bad, offsets)):
            raise ValueError('membership rows must be sorted and duplicate-free')
