"""Fail-closed ScanNet source identity and derived-box declarations."""
import json
from pathlib import Path
import numpy as np
from gt_scene_assets import read_json, verify

RECOVERY_FIELDS = ('interpolated_pose_slots', 'correlation_offset_slots')

BOX_CONVENTION = 'source_derived_raw_world_AABB_all_member_vertices_center_midrange_half_extents_v1'
BOX_DECLARATION = dict(box_convention=BOX_CONVENTION, released_boxes=False,
                       obb_estimator_used=True, provider_axesLengths='half_extents')


def annotation_identity(segmentation, aggregation, scene, segmentation_path=None):
    expected = scene + '_vh_clean_2.0.010000.segs.json'
    if aggregation.get('sceneId') != 'scannet.' + scene:
        raise ValueError('aggregation source scene mismatch')
    if segmentation.get('sceneId') != scene:
        raise ValueError('segmentation source scene mismatch')
    if aggregation.get('segmentsFile') != 'scannet.' + expected:
        raise ValueError('aggregation segmentsFile mismatch')
    if segmentation_path is not None and Path(segmentation_path).name != expected:
        raise ValueError('selected segmentation filename mismatch')


def source_identity(scene, frames, frames_pin, raw_pins, sensor):
    """Bind VSI identity to annotations and the actual sensor header bytes."""
    if frames.get('dataset') != 'scannet' or frames.get('scene_name') != scene:
        raise ValueError('VSI receipt official scene mismatch')
    if read_json(verify(frames_pin)) != frames:
        raise ValueError('VSI receipt binding mismatch')
    expected = {'sensor': scene + '.sens', 'mesh': scene + '_vh_clean_2.ply',
                'aggregation': scene + '.aggregation.json',
                'segmentation': scene + '_vh_clean_2.0.010000.segs.json',
                'metadata': scene + '.txt'}
    if set(raw_pins) != set(expected):
        raise ValueError('source file census mismatch')
    for key, name in expected.items():
        path = Path(raw_pins[key]['path'])
        if path.name != name or path.parent.name != scene or path.is_symlink():
            raise ValueError('source filename/scene directory mismatch: ' + key)
        if key != 'sensor':
            verify(raw_pins[key], prepared=False)
    if sensor.path.resolve() != Path(raw_pins['sensor']['path']).resolve():
        raise ValueError('selected sensor path mismatch')
    if sensor.size != raw_pins['sensor']['size_bytes']:
        raise ValueError('sensor size drift')
    annotation_identity(read_json(raw_pins['segmentation']['path']),
                        read_json(raw_pins['aggregation']['path']), scene,
                        raw_pins['segmentation']['path'])
    # SensorData names the device (e.g. StructureSensor), not the scene.
    return dict(schema='r1313-scannet-source-identity-v2', scene=scene,
                source_frames_receipt=frames_pin, raw_sources=raw_pins,
                sens_scene_name=sensor.path.stem, sens_header=sensor.header_pin)


def require_box_declaration(value, location):
    for key, expected in BOX_DECLARATION.items():
        if key not in value or type(value[key]) is not type(expected) or value[key] != expected:
            raise ValueError('derived box declaration mismatch at ' + location + ': ' + key)


def validate_box_receipt(receipt):
    """Use existing asset-pin fields so the collector receipt schema stays intact."""
    instances = read_json(verify(receipt['instances']))
    source = read_json(verify(receipt['source_provenance']))
    for location, value in [('instances carrier', instances), ('source provenance', source),
                            ('scene receipt instances pin', receipt['instances'])]:
        require_box_declaration(value, location)


def validate_identity_receipt(receipt, sensor=None):
    from scannet_sens import SensReader
    source = read_json(verify(receipt['source_provenance']))
    frames_pin = source['source_frames_receipt']
    frames = read_json(verify(frames_pin))
    if any(receipt[k] != frames[k] for k in ('frames', 'selected_frames', 'video')):
        raise ValueError('scene receipt/VSI frame binding mismatch')
    if source.get('dataset') != 'scannet' or source.get('source_scene_id') != receipt['scene_name']:
        raise ValueError('source provenance scene identity mismatch')
    if sensor is None:
        sensor = SensReader(source['raw_sources']['sensor']['path'], header_only=True)
    expected = source_identity(receipt['scene_name'], frames, frames_pin, source['raw_sources'], sensor)
    if source.get('source_identity') != expected or receipt['instances'].get('source_identity') != expected:
        raise ValueError('missing or inconsistent source identity receipt')
    if any(source['source_header'].get(k) != v for k, v in sensor.header.items()):
        raise ValueError('sensor header provenance mismatch')
    return expected


def validate_recovery_receipt(receipt, alignment, calibration):
    from scannet_sens import rigid
    keys = ({'slot_1based', 'raw_frame_index', 'neighbor_frame_indices', 'frame_gap'},
            {'slot_1based', 'offset', 'correlation_before', 'correlation_after'})
    indexed = []
    for field, expected in zip(RECOVERY_FIELDS, keys):
        rows = receipt.get(field, [])
        if not isinstance(rows, list) or alignment.get(field, []) != rows:
            raise ValueError('recovery receipt/alignment mismatch: ' + field)
        slots = {}
        for row in rows:
            if not isinstance(row, dict) or set(row) != expected:
                raise ValueError('unexpected recovery fields: ' + field)
            slot = row['slot_1based']
            if type(slot) is not int or not 1 <= slot <= 32 or slot in slots:
                raise ValueError('invalid or duplicate recovery slot: ' + field)
            slots[slot] = row
        indexed.append(slots)
    interpolated, offsets = indexed
    for slot, row in offsets.items():
        before, after, offset = row['correlation_before'], row['correlation_after'], row['offset']
        if type(offset) is not int or not 1 <= abs(offset) <= 3:
            raise ValueError('correlation offset must be within -3..+3 and nonzero')
        if (before is not None and (type(before) not in (int, float) or not np.isfinite(before) or not -1 <= before < .99)
                or type(after) not in (int, float) or not np.isfinite(after) or not .99 <= after <= 1):
            raise ValueError('invalid correlation recovery before/after threshold')
        record = alignment['frames'][slot - 1]
        raw_index = receipt['frames'][slot - 1]['ordinal'] + offset
        if (not 0 <= raw_index < alignment['source_header']['num_frames']
                or record['source_frame_id'] != raw_index or record['raw_to_vsi_correlation'] != after):
            raise ValueError('correlation offset/source record mismatch')
    for slot, row in interpolated.items():
        raw_index, neighbors, gap = row['raw_frame_index'], row['neighbor_frame_indices'], row['frame_gap']
        if (type(raw_index) is not int or not 0 <= raw_index < alignment['source_header']['num_frames']
                or raw_index != receipt['frames'][slot - 1]['ordinal'] + offsets.get(slot, {}).get('offset', 0)
                or raw_index != alignment['frames'][slot - 1]['source_frame_id']
                or not isinstance(neighbors, list) or len(neighbors) not in (1, 2)
                or any(type(i) is not int or not 0 <= i < alignment['source_header']['num_frames']
                       or not 1 <= abs(i - raw_index) <= 5 for i in neighbors)):
            raise ValueError('invalid interpolated pose source or neighbors within 5 frames')
        expected_gap = abs(neighbors[0] - raw_index) if len(neighbors) == 1 else neighbors[1] - neighbors[0]
        if (len(neighbors) == 2 and not neighbors[0] < raw_index < neighbors[1]
                or type(gap) is not int or gap != expected_gap):
            raise ValueError('interpolated pose neighbor gap mismatch')
        pose = rigid(calibration['camera_poses'][slot - 1], 'interpolated camera carrier')
        aligned = rigid(alignment['frames'][slot - 1]['aligned_pose'], 'interpolated aligned pose')
        if not np.array_equal(pose.astype(np.float32), aligned.astype(np.float32)):
            raise ValueError('interpolated pose/alignment mismatch')
    return interpolated, offsets


def validate_registry_recovery(entry, receipt):
    for field in RECOVERY_FIELDS:
        if (field in entry and json.dumps(entry[field], sort_keys=True, allow_nan=False)
                != json.dumps(receipt.get(field, []), sort_keys=True, allow_nan=False)):
            raise ValueError('registry/scene recovery mismatch: ' + field)
