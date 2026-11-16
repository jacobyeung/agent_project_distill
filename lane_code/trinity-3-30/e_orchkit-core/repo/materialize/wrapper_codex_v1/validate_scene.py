from __future__ import annotations

import argparse
import time
from pathlib import Path
from types import SimpleNamespace

import common as b


def validate(scene, dry=False):
    b.require_env()
    started = time.monotonic()
    source_before = b.verify_sources()
    plan = b.scene_plan(scene, dry=dry)
    expected_convention = b.CONFIG['obb_lengths']
    b.verify_scripts()
    if not dry: b.lease(scene)
    import cv2
    import numpy as np
    from collect import registry_rows
    from donor_geometry import Renderer
    from gt_scene_assets import load_arrays, validate_dense, validate_scene, verify
    from gt_training_r1313 import TrainingGrounding
    from prepare_gt_scene import RAW_NAMES, RAW_ROOT, inputs, selected_camera_alignment
    from training_assets import bind_runtime_row

    cv2.setNumThreads(2)
    output = Path(plan['output'])
    registry_path = output / 'registry.json'
    receipt_path = output / 'scene_receipt.json'
    receipt_pin = b.pin(receipt_path)
    receipt = validate_scene(b.read_json(receipt_path), load_dense=True)
    b.require((receipt['dataset'], receipt['scene_name'], receipt['runtime_scene_id']) == ('scannetppv2', scene, plan['runtime_scene_id']), 'receipt/membership scene identity mismatch')
    registry = registry_rows({'assets_registry': str(registry_path)})
    b.require(registry == {('scannetppv2', scene): receipt_pin}, 'source registry validator rejected exact single-scene identity')
    b.require(b.read_json(registry_path)['round'] == 1313, 'registry round mismatch')
    b.verify_pin(plan['frames_receipt'])
    provenance = b.read_json(verify(receipt['source_provenance']))
    b.require(provenance['source_scene_id'] == scene and provenance['dataset'] == 'scannetppv2', 'provenance scene mismatch')
    b.require(provenance['source_frames_receipt'] == plan['frames_receipt'], 'source frames receipt mismatch')
    b.require(set(provenance['raw_sources']) == set(RAW_NAMES), 'official source census mismatch')
    for name, spec in provenance['raw_sources'].items():
        b.require(Path(spec['path']).resolve() == (RAW_ROOT / scene / name).resolve(), 'official source path mismatch')
        verify(spec, prepared=False)
    for field, name in (('preprocessor', 'prepare_gt_scene.py'), ('renderer', 'donor_geometry.py'), ('grounding_kernel', 'donor_grounding.py')):
        b.require(provenance[field] == b.pin(b.PACKAGE / name), 'source kernel provenance drift')
    inspect_path = Path(plan['inspection'])
    inspection = b.read_json(inspect_path)
    b.require(inspection['scene'] == scene, 'inspection scene mismatch')
    witnessed = b.convention(inspection, expected_convention)
    factor = witnessed['factor']
    b.require(provenance['official_obb_source_lengths'] == expected_convention and provenance['source_obb_scale_factor'] == factor, 'OBB convention differs from witnessed source')
    b.require(provenance['provider_axesLengths'] == 'half_extents' and provenance['obb_estimator_used'] is False, 'unreviewed OBB adaptation')
    raw, frames, vertices, faces, groups, face_ids, basis, diagnostics = inputs(SimpleNamespace(scene=scene, frames_receipt=Path(plan['frames_receipt']['path'])))
    b.require(receipt['frames'] == frames['frames'] and receipt['selected_frames'] == frames['selected_frames'] and receipt['video'] == frames['video'], 'prepared scene changed RGB/video membership')
    b.require(diagnostics == inspection['instances'] == provenance['instances'] and basis == inspection['association'] == provenance['association'], 'source association diagnostics drift')
    b.require(len(vertices) == inspection['vertices'] and len(faces) == inspection['faces'] and int((face_ids >= 0).sum()) == inspection['annotated_faces'], 'mesh inspection census mismatch')
    mesh = load_arrays(receipt['instance_mesh'])
    b.require(set(mesh) == {'vertices_world', 'faces', 'face_instance_ids'}, 'mesh array census mismatch')
    b.require(np.array_equal(vertices, mesh['vertices_world']) and np.array_equal(faces, mesh['faces']) and np.array_equal(face_ids, mesh['face_instance_ids']), 'prepared mesh/instance association differs from official source')
    adapted = b.read_json(verify(receipt['instances']))['segGroups']
    b.require(len(adapted) == len(groups) == inspection['segGroups'], 'instance inventory size mismatch')
    for source, target, diagnostic in zip(groups, adapted, diagnostics):
        b.require(target['id'] == target['objectId'] == diagnostic['instance_id'] and source['label'] == target['label'], 'instance identity or label mismatch')
        for field in ('normalizedAxes', 'centroid'):
            b.require(source['obb'][field] == target['obb'][field], 'official OBB axes/center were changed')
        b.require(np.array_equal(np.asarray(source['obb']['axesLengths']) * factor, target['obb']['axesLengths']), 'OBB lengths are not the exact declared conversion')
    annotations = b.read_json(verify(receipt['annotations']))
    b.require(annotations == {'instances': [{'instance_id': g['id'], 'label': g['label']} for g in adapted]}, 'annotation inventory mismatch')
    poses, intrinsics, hw, rows, _ = selected_camera_alignment(raw, frames)
    calibration = load_arrays(receipt['calibration'])
    b.require(np.array_equal(poses, calibration['camera_poses']) and np.array_equal(intrinsics, calibration['intrinsics']), 'official camera calibration mismatch')
    b.require(list(hw) == calibration['raster_hw'].tolist() == [480, 640], 'authenticated RGB canvas mismatch')
    alignment = b.read_json(verify(receipt['alignment']))
    b.require(rows == alignment['frames'] and alignment['validated_slots'] == 32 and alignment['estimated_geometry_used'] is False, 'all32 independent RGB/camera associations must match')
    dense = validate_dense(load_arrays(receipt['dense']), frames['frames'])
    b.require(np.array_equal(dense['camera_poses'], poses) and np.array_equal(dense['intrinsics'], intrinsics), 'geometry/grounding cameras differ')
    b.require(len(alignment['render_audits']) == 32, 'missing per-frame render audit')
    reprojections = []
    for slot, audit in enumerate(alignment['render_audits']):
        mask = dense['mask'][slot]
        yy, xx = np.nonzero(mask)
        camera = (dense['pts3d_world'][slot][mask].astype(np.float64) - poses[slot, :3, 3]) @ poses[slot, :3, :3]
        projected = camera[:, :2] / camera[:, 2:]
        projected = projected * [intrinsics[slot, 0, 0], intrinsics[slot, 1, 1]] + [intrinsics[slot, 0, 2], intrinsics[slot, 1, 2]]
        residual = float(np.linalg.norm(projected - np.column_stack([xx, yy]), axis=1).max())
        b.require(audit['slot_1based'] == slot + 1 and audit['valid_pixels'] == int(mask.sum()) and residual <= 0.05, 'independent dense reprojection failed')
        b.require(abs(audit['max_reprojection_px'] - residual) <= 1e-9, 'stored render audit differs from recomputed residual')
        reprojections.append(residual)
    provider = TrainingGrounding(receipt)
    inventory = provider._inventory(receipt['runtime_scene_id'])
    provider._instance_mesh(receipt['runtime_scene_id'])
    b.require(len(inventory['labels']) == len(groups), 'grounding inventory mismatch')
    b.require([p['slot_1based'] for p in receipt['rendering_proof']] == [1, 17], 'required rendering proof slots missing')
    proofs = []
    for proof in receipt['rendering_proof']:
        verify(proof['side_by_side'])
        arrays = load_arrays(proof['arrays'])
        b.require(set(arrays) == {'mask', 'depth_z', 'valid'}, 'rendering proof array census mismatch')
        slot = proof['slot_1based'] - 1
        depth, mask = Renderer._render(vertices, poses[slot].astype(np.float64), intrinsics[slot].astype(np.float64), *hw)
        b.require(np.array_equal(depth, arrays['depth_z']) and np.array_equal(mask, arrays['valid']), 'independent source renderer disagrees with proof')
        b.require(np.array_equal(depth, dense['depth_z'][slot]) and np.array_equal(mask, dense['mask'][slot]), 'proof is not bound to saved dense geometry')
        rendered = provider._render_instance(receipt['runtime_scene_id'], slot + 1, proof['instance_id'])
        b.require(rendered is not None and np.array_equal(rendered['mask'], arrays['mask']), 'independent instance mask disagrees with proof')
        b.require(int(arrays['mask'].sum()) == proof['visible_mask_pixels'] >= 32, 'visible proof support mismatch')
        b.require(proof['label'] == inventory['labels'][proof['instance_id']] and proof['instance_id'] in provider.match_instances(receipt['runtime_scene_id'], proof['label']), 'official label-to-instance proof mismatch')
        image = cv2.imread(proof['side_by_side']['path'])
        b.require(image is not None and image.shape == (360, 960, 3), 'rendering proof image is invalid')
        proofs.append({'slot_1based': slot + 1, 'instance_id': proof['instance_id'], 'visible_pixels': proof['visible_mask_pixels'], 'arrays': proof['arrays'], 'side_by_side': proof['side_by_side']})
    selected = b.selected_rows(scene)
    membership = b.membership_summary(selected)
    b.require(all(membership[k] == plan[k] for k in membership), 'exact qids/taskmix/rows differ from immutable plan')
    for row in selected:
        bound = bind_runtime_row(row, receipt)
        b.require(bound['scene_name'] == plan['runtime_scene_id'] and bound['id'] == row['id'] and bound['source_scene_name'] == scene, 'source runtime row binding mismatch')
        b.require(row['video'] == f'scannetppv2/{scene}.mp4', 'membership video does not match official scene')
    source_after = b.verify_sources()
    b.require(source_before['source_files'] == source_after['source_files'], 'source changed during independent validation')
    files = {p.name: b.pin(p) for p in sorted(output.iterdir()) if p.is_file()}
    result = {'schema': 'req232-additional-gt-validation-v1', 'status': 'PASS', 'checked_at': b.utc(),
              'scene': scene, 'runtime_scene_id': receipt['runtime_scene_id'], 'validated_slots': 32,
              'membership': membership, 'scene_receipt': receipt_pin, 'scene_registry': b.pin(registry_path),
              'inspection': b.pin(inspect_path), 'source_contract': b.pin(b.CONTRACT),
              'script_manifest': b.pin(b.ROOT / 'CONTRACT.json'),
              'source_verification_before': source_before, 'source_verification_after': source_after,
              'raw_sources_rehashed': provenance['raw_sources'], 'frames_receipt': plan['frames_receipt'],
              'official_instances': len(groups), 'mesh_association': basis, 'obb_witness': witnessed,
              'min_raw_vsi_correlation': min(r['raw_to_vsi_correlation'] for r in rows),
              'max_dense_reprojection_px': max(reprojections), 'rendering_proofs_reproduced': proofs,
              'output_files': files, 'output_size_bytes': sum(p['size_bytes'] for p in files.values()),
              'elapsed_seconds': time.monotonic() - started, 'process': b.identity(),
              'checks': ['reviewed validate_scene(load_dense=True)', 'reviewed registry_rows (this package has no SceneRegistry class)',
                         'official raw source hashes and mesh/instance reconstruction', 'exact OBB conversion without estimation',
                         'all32 independent raw/VSI pixel and camera checks', 'all32 dense reprojection checks',
                         'both source renderer and instance mask proofs', 'exact answer-free qids/taskmix/runtime binding', 'all40 source files unchanged'],
              'training_only': True, 'benchmark_score_claim': False}
    target = (b.ROOT / 'dry_run' if dry else b.JOBS / scene) / 'VALIDATION.json'
    b.publish(target, result)
    print(b.canonical({'status': 'PASS', 'scene': scene, 'validation': b.pin(target), 'question_count': len(selected)}).decode(), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--scene', required=True)
    parser.add_argument('--dry', action='store_true')
    args = parser.parse_args()
    validate(args.scene, dry=args.dry)
