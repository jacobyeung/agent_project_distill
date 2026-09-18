"""Fail-closed ScanNet source identity and derived-box declarations."""
from pathlib import Path
from gt_scene_assets import read_json, verify

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
