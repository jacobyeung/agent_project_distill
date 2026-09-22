# Camera transforms and box corners come from tools/vstigen/conventions.py at e2f387e (vstigen-membership-v4-20260922).
import itertools

import numpy as np


FAMILIES = ('gtm_object_count', 'gtm_object_size', 'gtm_object_distance',
            'gtm_camera_object_distance', 'gtm_room_size')
MEASURES = {
    'gtm_object_count': {'measure': 'distinct official instance IDs with the exact queried category label',
                         'scope': 'all category instances must have authenticated RGB visibility in the selected clip'},
    'gtm_object_size': {'measure': 'longest full dimension of the official prepared instance box',
                        'formula': '2 * max(obb.axesLengths); prepared axesLengths are half-extents'},
    'gtm_object_distance': {'measure': 'minimum Euclidean distance between complete official instance triangle surfaces',
                            'formula': 'minimum triangle-triangle distance, including vertex-face, edge-edge, and intersections',
                            'multiple_instances': 'absolute questions require unique labels; MC options use the nearest instance'},
    'gtm_camera_object_distance': {'measure': 'minimum Euclidean distance from camera origin to the complete official instance triangle surface',
                                   'formula': 'camera-to-world translation to nearest triangle point; radial distance, not optical-axis depth',
                                   'frame_index': 'one-based slot among the 32 supplied RGB frames'},
    'gtm_room_size': {'measure': 'area of the union of official floor triangles projected into gravity-aligned world XY',
                       'formula': 'planar polygon union; preserve concavities and holes; never fill unobserved floor',
                       'limitation': 'measures the annotated mesh footprint; incomplete floor geometry cannot certify the full physical room area'},
}


def camera_points(points, pose):
    pose = np.asarray(pose, dtype=np.float64)
    return (np.asarray(points, dtype=np.float64) - pose[:3, 3]) @ pose[:3, :3]


def box_corners(obb):
    center = np.asarray(obb['centroid'], dtype=np.float64)
    half = np.asarray(obb['axesLengths'], dtype=np.float64)
    axes = np.asarray(obb['normalizedAxes'], dtype=np.float64).reshape(3, 3)
    if center.shape != (3,) or half.shape != (3,) or not np.isfinite([center, half]).all() or np.any(half <= 0):
        raise ValueError('invalid official instance box')
    if not np.isfinite(axes).all() or not np.allclose(axes @ axes.T, np.eye(3), atol=1e-4):
        raise ValueError('instance box axes are not orthonormal')
    return center + (np.asarray(list(itertools.product((-1, 1), repeat=3))) * half) @ axes
