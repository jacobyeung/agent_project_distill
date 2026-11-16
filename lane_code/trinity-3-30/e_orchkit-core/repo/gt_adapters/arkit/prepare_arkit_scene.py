from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from arkit_alignment import selected_camera_alignment
from arkit_source import DATASET, MASK_SEMANTICS, UPSTREAM_COMMIT, associate_mesh, parse_annotations, regular, timestamped_files, timeline_sha
from gt_scene_assets import SCHEMA, data_path, pin, save_arrays, scene_id, validate_dense, validate_scene, verify, write_json
from prepare_gt_scene import load_mesh, render_geometry, rendering_proof

SOURCE_FILES = ('prepare_corpus.py', 'prepare_arkit_scene.py', 'arkit_source.py', 'arkit_alignment.py',
                'prepare_gt_scene.py', 'gt_scene_assets.py', 'gt_training_r1313.py', 'donor_geometry.py',
                'donor_grounding.py', 'frame_alignment.py', 'gt_label_matcher_r1313.py', 'gt_errors.py')


def prepare(args):
    runtime_id = scene_id(DATASET, args.scene)
    if not args.scene.isdigit():
        raise ValueError('ARKitScenes scene name must be the official numeric video ID')
    output = data_path(args.output)
    if output.exists():
        raise FileExistsError('prepared scene outputs are immutable; choose a new output directory')
    sequence = Path(args.sequence_dir)
    if sequence.is_symlink() or not sequence.is_dir() or sequence.name != args.scene or sequence.parent.name not in ('Training', 'Validation') or sequence.parent.parent.name != 'raw':
        raise ValueError('sequence must use raw/<Training|Validation>/<video_id> layout')
    sequence = sequence.resolve()
    annotation_path = regular(sequence / f'{args.scene}_3dod_annotation.json')
    mesh_path = regular(sequence / f'{args.scene}_3dod_mesh.ply')
    raw_pins = {annotation_path.name: pin(annotation_path), mesh_path.name: pin(mesh_path)}
    code_pins = {name: pin(Path(__file__).with_name(name)) for name in SOURCE_FILES}
    groups, identities = parse_annotations(annotation_path)
    vertices, faces = load_mesh(mesh_path)
    face_ids, association = associate_mesh(vertices, faces, groups)
    frames, poses, intrinsics, raster_hw, alignment, rgb, camera_pins, evidence = selected_camera_alignment(
        sequence, args.scene, args.frames_receipt, args.correspondence)
    raw_pins.update(camera_pins)
    ordinals = [row['ordinal'] for row in frames['frames']]
    data, render_audits = render_geometry(vertices, poses, intrinsics, raster_hw, ordinals)
    validate_dense(data, frames['frames'])
    output.mkdir(parents=True, exist_ok=False)
    instances = write_json(output / 'instances.json', {'segGroups': groups})
    annotations = write_json(output / 'annotations.json', {'instances': identities, 'mask_semantics': MASK_SEMANTICS})
    mesh = save_arrays(output / 'instance_mesh.npz', vertices_world=vertices, faces=faces, face_instance_ids=face_ids)
    calibration = save_arrays(output / 'official_cameras.npz', camera_poses=poses, intrinsics=intrinsics,
                              indices=np.asarray(ordinals, dtype=np.int64), raster_hw=np.asarray(raster_hw, dtype=np.int64))
    dense = save_arrays(output / 'gt_dense_source_world.npz', **data)
    timeline = write_json(output / 'source_timeline.json', {'schema': 'r1313-arkit-source-timeline-v1',
        'dataset': DATASET, 'scene_name': args.scene, 'source_stream': 'lowres_wide',
        'frames': evidence['source_timeline'], 'timeline_sha256': evidence['source_timeline_sha256']})
    alignment_pin = write_json(output / 'alignment.json', {'schema': 'r1313-official-alignment-v1',
        'pose_field': 'aligned_pose', 'native_pose_source': 'inverse(lowres_wide.traj world_to_camera)',
        'estimated_geometry_used': False, 'validated_slots': 32, 'frames': alignment,
        'render_audits': render_audits, 'mapping_basis': evidence['mapping_basis'],
        'correspondence': evidence['correspondence'], 'mapping_authority': evidence['mapping_authority'],
        'source_timeline': timeline, 'correlation_minimum': evidence['correlation_minimum'],
        'mae_maximum': evidence['mae_maximum'], 'timestamp_tolerance_sec': evidence['timestamp_tolerance_sec'],
        'target_grid': 'authenticated_selected_RGB_canvas; declared aspect_preserving_resize; no_crop',
        'grounding_projection': 'source_world_meters',
        'returned_geometry': 'canonical_geometry(data,[0,0,1]); rigid points/poses transform; scale1'})
    provenance = write_json(output / 'source_provenance.json', {'schema': 'r1313-source-provenance-v1',
        'dataset': DATASET, 'source_scene_id': args.scene, 'raw_sources': raw_pins,
        'source_frames_receipt': evidence['source_frames_receipt'], 'correspondence': evidence['correspondence'],
        'mapping_authority': evidence['mapping_authority'], 'source_timeline': timeline,
        'source_timeline_sha256': evidence['source_timeline_sha256'], 'upstream_commit': UPSTREAM_COMMIT,
        'source_release': 'ARKitScenes raw v1; one raw export, never mixed with 3dod frames',
        'source_coordinate_convention': 'meters; XY heading plane, Z vertical; official world_to_camera trajectory inverted once',
        'source_to_receipt_world': np.eye(4).tolist(), 'gravity_estimator_used': False,
        'official_obb_source_lengths': 'full_extents', 'provider_axesLengths': 'half_extents',
        'source_obb_scale_factor': 0.5, 'obb_estimator_used': False, 'native_instance_segmentation_available': False,
        'mask_semantics': MASK_SEMANTICS, 'association': association, 'instance_uid_mapping': identities,
        'unsupported_instances': 'refuse_scene; never permit donor OBB fallback',
        'inherited_rasterization': {'vertex_splat_hole_fill_passes': 3, 'occlusion_tolerance_m': 0.15, 'max_instance_faces': 30000},
        'preprocessor': pin(__file__), 'source_closure': code_pins,
        'adaptation': 'official K and source mesh support only; no learned geometry, pose interpolation, or image registration'})
    receipt = {'schema': SCHEMA, 'round': 1313, 'dataset': DATASET, 'scene_name': args.scene,
        'runtime_scene_id': runtime_id, 'frames': frames['frames'], 'image_count': 32,
        'selected_frames': frames['selected_frames'], 'video': frames['video'], 'dense': dense,
        'calibration': calibration, 'instances': instances, 'instance_mesh': mesh, 'annotations': annotations,
        'alignment': alignment_pin, 'source_provenance': provenance,
        'geometry_source': 'official_aligned_pose_intrinsic_mesh_gt_valid_support',
        'coordinate_frame': 'source_world_meters_opencv_camera_to_world', 'gravity_up': [0, 0, 1],
        'student_observations': 'question_and_authenticated32RGB_only',
        'teacher_initial_observations': 'text_question_and_choices; zero_inline_RGB; evidence_from_tools'}
    receipt['rendering_proof'] = rendering_proof(output, receipt, rgb, data)
    for spec in list(raw_pins.values()) + list(code_pins.values()):
        verify(spec, prepared=False)
    for name in ('source_frames_receipt', 'correspondence', 'mapping_authority'):
        verify(evidence[name])
    if timeline_sha(timestamped_files(sequence / 'lowres_wide', args.scene, '.png')) != evidence['source_timeline_sha256']:
        raise ValueError('source RGB timeline changed during preparation')
    for proof in receipt['rendering_proof']:
        verify(proof['arrays'])
        verify(proof['side_by_side'])
    validate_scene(receipt, load_dense=True)
    final = write_json(output / 'scene_receipt.json', receipt)
    registry = write_json(output / 'registry.json', {'schema': 'r1313-assets-registry-v1', 'round': 1313, 'receipts': [final]})
    result = {'scene_ready': True, 'scene': runtime_id, 'frames': 32, 'instances': len(groups),
              'receipt': final, 'registry': registry, 'mask_semantics': MASK_SEMANTICS,
              'minimum_correlation': min(row['raw_to_vsi_correlation'] for row in alignment)}
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return result
