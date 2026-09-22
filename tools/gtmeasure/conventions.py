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


OBSERVATION_TEMPLATES_V2 = {
    'object_extents': {
        'families': ['gtm_object_size'],
        'template': "The {target}'s official-box extents (length, width, height) are ({length}, {width}, {height}) meters."},
    'object_geometry': {
        'families': ['gtm_object_distance', 'gtm_camera_object_distance'],
        'template': 'The {target} (instance {instance_id}) has center ({x}, {y}, {z}) meters in the camera0 frame '
                    'and official-box extents (length, width, height) of ({length}, {width}, {height}) meters.'},
    'camera_position': {
        'families': ['gtm_camera_object_distance'],
        'template': 'In frame {frame_index}, the camera position is ({x}, {y}, {z}) meters in the camera0 frame.'},
    'floor_bounds': {
        'families': ['gtm_room_size'],
        'template': 'The floor bounds in camera0 XY are X [{xmin}, {xmax}] meters and Y [{ymin}, {ymax}] meters, '
                    'with extents ({xextent}, {yextent}) meters.'},
    'instance_center': {
        'families': ['gtm_object_count'],
        'template': 'The {target} instance {instance_id} has center ({x}, {y}, {z}) meters in the camera0 frame.'},
}


def structure_conventions(conventions, structure):
    if structure == 'v1':
        return conventions
    if structure != 'v2':
        raise ValueError('structure must be v1 or v2')
    templates = {name: {**spec, 'id': 'gtmeasure-v2-' + name, 'origin': 'lane_authored',
                        'authored_by': 'gt_measurement_v2_20260922T0735Z',
                        'source': 'tools/gtmeasure/conventions.py', 'units': 'meters', 'decimal_places': 2}
                 for name, spec in OBSERVATION_TEMPLATES_V2.items()}
    return {**conventions, 'observation_templates': templates, 'structure_v2': {
        'wording_authority': 'templates remain harvested question wording with original source lines; '
                             'observation_templates are lane-authored intermediate wording, not harvested authority; '
                             'final measurement lines and answers retain the v1 renderer',
        'coordinate_frame': 'first_camera_origin_heading_gravity_up_camera_to_world_opencv',
        'coordinate_implementation': 'collector/frame_alignment.py:canonical_geometry',
        'coordinate_origin': 'camera_poses[0, :3, 3], the first selected RGB camera (one-based frame 1)',
        'coordinate_axes': '+X right, +Y initial horizontal view, +Z gravity up; teacher vertical-view fallback',
        'coordinate_precision': 'reuse the teacher canonical_geometry float32 outputs before text formatting',
        'instance_centers': 'official obb.centroid in the teacher coordinate frame, not the visible pixel-depth points returned by predict_2d_points',
        'box_extents': 'length, width, height name 2 * axesLengths[0:3] in stored normalizedAxes row order; '
                       'full object-local oriented-box sides, not camera0-aligned bounding-box spans or inferred semantic axes',
        'floor_bounds': 'min/max of all selected official floor triangle vertices in camera0 XY; '
                        'extents are max minus min, not a replacement for the triangle-union floor area',
        'instance_order': 'ascending official instance ID; MC distances include every instance in each option category once',
        'numeric_format': 'meters, fixed two decimals; Decimal(str(float(value))) with ROUND_HALF_EVEN; '
                          'normalize negative zero; intermediate rounding ties never filter rows; answers keep harvested rounding',
        'schema_compatibility': 'structure is an opt-in rendering mode; gtmeasure_v1 remains the dataset and row source schema',
    }}


def camera0_points(points, poses, gravity_up):
    from collector.frame_alignment import canonical_geometry

    return canonical_geometry({'pts3d_world': points, 'camera_poses': poses}, gravity_up)['pts3d_world']


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
