"""Offline ScanNet corpus adapter; no teacher, tool, or collector changes."""
from __future__ import annotations
import json
from pathlib import Path
import cv2
import numpy as np
from gt_scene_assets import (SCHEMA, data_path, pin, verify, read_json, write_json,
                             save_arrays, scene_id, validate_dense, validate_scene)
from scannet_sens import SensReader, calibrated_header, rigid
from scannet_contract import authenticated_frames, verify_contract

RAW_ROOT = Path('/data2/jjyeung/raw_datasets/scannet/scans')
BOX_CONVENTION = 'source_derived_raw_world_AABB_all_member_vertices_center_midrange_half_extents_v1'


def source_paths(scene):
    scene_id('scannet', scene)
    root = RAW_ROOT / scene
    return {'sensor': root / (scene + '.sens'), 'mesh': root / (scene + '_vh_clean_2.ply'),
            'aggregation': root / (scene + '.aggregation.json'),
            'segmentation': root / (scene + '_vh_clean_2.0.010000.segs.json'),
            'metadata': root / (scene + '.txt')}


def metadata(path):
    result = {}
    for line in Path(path).read_text().splitlines():
        key, value = line.split('=', 1)
        if key.strip() in result:
            raise ValueError('duplicate source metadata field')
        result[key.strip()] = value.strip()
    if 'axisAlignment' not in result:
        raise ValueError('missing released axisAlignment metadata')
    axis = np.asarray([float(x) for x in result['axisAlignment'].split()]).reshape(4, 4)
    rigid(axis, 'axisAlignment')
    return result, axis


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


def correspondence(source, vsi, selected):
    if selected is None or not np.array_equal(vsi, selected):
        raise ValueError('authenticated selected PNG differs from its VSI video ordinal')
    vh, vw = vsi.shape[:2]
    resized = cv2.resize(source, (vw, vh), interpolation=cv2.INTER_AREA)
    correlation = float(np.corrcoef(resized.reshape(-1), vsi.reshape(-1))[0, 1])
    mae = float(np.abs(resized.astype(np.float32) - vsi).mean())
    return correlation, mae


def selected_camera_alignment(sensor, frames, output):
    source_k = calibrated_header(sensor.header)
    items = frames['frames']
    ordinals = [item['ordinal'] for item in items]
    if (len(items) != 32 or frames['image_count'] != 32 or any(type(i) is not int for i in ordinals)
            or sorted(set(ordinals)) != ordinals or ordinals[0] < 0
            or ordinals[-1] >= len(sensor.records) or [x['stem'] for x in items] != frames['selected_frames']):
        raise ValueError('exactly 32 ordered unique sensor ordinals are required')
    indices = read_json(verify(frames['indices']))
    if indices.get('schema') != 'r1308-selected-indices-v1' or indices.get('indices') != ordinals:
        raise ValueError('selected indices asset disagrees with RGB receipt')
    video = cv2.VideoCapture(str(verify(frames['video'])))
    rows, poses, intrinsics, rgb, errors = [], [], [], [], []
    hw = None
    try:
        if not video.isOpened():
            raise ValueError('VSI video cannot be decoded')
        count, fps = int(video.get(cv2.CAP_PROP_FRAME_COUNT)), float(video.get(cv2.CAP_PROP_FPS))
        if count != len(sensor.records) or count != frames['video']['decoded_frame_count'] or not np.isclose(fps, frames['video']['fps']) or fps <= 0:
            raise ValueError('sensor/VSI ordinal count or VSI timebase mismatch')
        for slot, item in enumerate(items, 1):
            ordinal = item['ordinal']
            if item['stem'] != f'frame_{ordinal:06d}' or not np.isclose(item['timestamp_sec'], ordinal / fps):
                raise ValueError('RGB receipt stem/time does not bind its VSI ordinal')
            selected = cv2.imread(str(verify(item)), cv2.IMREAD_COLOR)
            if not video.set(cv2.CAP_PROP_POS_FRAMES, ordinal):
                raise ValueError('VSI ordinal seek failed')
            ok, vsi = video.read()
            if not ok or abs(video.get(cv2.CAP_PROP_POS_FRAMES) - ordinal - 1) > .1:
                raise ValueError('VSI seek returned a different ordinal')
            source, depth, record = sensor.decode(ordinal)
            pose = rigid(record['camera_to_world'], 'sensor camera_to_world')
            correlation, mae = correspondence(source, vsi, selected)
            if not np.isfinite(correlation) or correlation < .99:
                errors.append(f'raw/VSI ordinal correlation failed at slot {slot}: {correlation}')
            sh, sw = source.shape[:2]; vh, vw = vsi.shape[:2]
            scale = np.diag([vw / sw, vh / sh, 1.0])
            k = scale @ source_k
            if hw is not None and hw != (vh, vw):
                raise ValueError('selected RGB canvases differ')
            hw = vh, vw
            row = dict(record, slot_1based=slot, ordinal=ordinal, stem=item['stem'],
                timestamp_sec=ordinal / fps, raw_source_canvas_wh=[sw, sh], vsi_canvas_wh=[vw, vh],
                source_intrinsic=source_k.tolist(), source_to_vsi=scale.tolist(),
                vsi_to_target_resize_crop=np.eye(3).tolist(), crop_xyxy=[0, 0, vw, vh],
                target_intrinsic=k.tolist(), aligned_pose=pose.tolist(),
                raw_to_vsi_correlation=correlation if np.isfinite(correlation) else None,
                raw_to_vsi_mae=mae, selected_png_matches_vsi_decode=True, selected_rgb_sha256=item['sha256'])
            rows.append(row); poses.append(pose); intrinsics.append(k); rgb.append(selected)
            with (output / 'ORDINAL_PROGRESS.jsonl').open('a') as log:
                log.write(json.dumps(row, allow_nan=False) + '\n'); log.flush()
            print(json.dumps({'stage': 'sensor_ordinal', 'slot': slot, 'correlation': row['raw_to_vsi_correlation']}), flush=True)
        attempt = write_json(output / 'ordinal_proof.json', {'frames': rows, 'errors': errors,
            'correlation_threshold': .99, 'validated_slots': 32 - len(errors), 'source_header': sensor.header})
        if errors:
            raise ValueError('; '.join(errors))
        return np.asarray(poses, np.float32), np.asarray(intrinsics, np.float32), hw, rows, rgb, attempt
    finally:
        video.release()


def visibility_proof(output, receipt, rgb, data):
    from gt_training_r1313 import TrainingGrounding
    provider = TrainingGrounding(receipt)
    scene = receipt['runtime_scene_id']
    inventory = provider._inventory(scene)
    mesh = provider._instance_mesh(scene)
    ids, counts = np.unique(mesh['instance_ids'], return_counts=True)
    candidates = [iid for count, iid in sorted((int(n), int(i)) for i, n in zip(ids, counts) if i >= 0)]
    rows, proofs = [], []
    for slot in range(1, 33):
        pose, k, h, w = provider._camera(scene, slot)
        if not np.array_equal(pose, data['camera_poses'][slot - 1]) or not np.array_equal(k, data['intrinsics'][slot - 1]):
            raise ValueError('teacher geometry/grounding camera mismatch')
        chosen = None
        for iid in candidates:
            rendered = provider._render_instance(scene, slot, iid)
            if rendered is not None and rendered['mask_pixel_count'] >= 32:
                chosen = iid, rendered
                break
        if chosen is None:
            raise ValueError(f'no annotated mesh instance has 32 visible pixels at slot {slot}')
        iid, rendered = chosen
        label = inventory['labels'][iid]
        if iid not in provider.match_instances(scene, label):
            raise ValueError('unchanged label matcher lost official instance')
        # Exercise the unchanged geometry and grounding observation interfaces.
        boxes = provider.boxes(scene, slot, label)
        points = provider.points(scene, slot, label)
        x0, y0, x1, y1 = rendered['bbox_pixels']
        expected_box = [round(x0 / w, 3), round(y0 / h, 3), round(x1 / w, 3), round(y1 / h, 3)]
        if expected_box not in boxes or iid not in [x['instance_id'] for x in points]:
            raise ValueError('unchanged grounding interface lost visible instance')
        mask = rendered['mask']
        row = dict(slot_1based=slot, instance_id=iid, label=label, visible_mask_pixels=int(mask.sum()),
                   boxes_returned=len(boxes), points_returned=len(points), mesh_faces=int((mesh['instance_ids'] == iid).sum()))
        rows.append(row)
        with (output / 'VISIBILITY_PROGRESS.jsonl').open('a') as log:
            log.write(json.dumps(row) + '\n'); log.flush()
        if slot in (1, 17):
            arrays = save_arrays(output / f'proof_slot{slot:02d}.npz', mask=mask,
                                 depth_z=data['depth_z'][slot - 1], valid=data['mask'][slot - 1])
            overlay = rgb[slot - 1].copy()
            overlay[mask] = (.55 * overlay[mask] + .45 * np.array([0, 255, 0])).astype(np.uint8)
            depth = data['depth_z'][slot - 1]
            upper = float(np.percentile(depth[data['mask'][slot - 1]], 99))
            heat = cv2.applyColorMap(np.clip(depth / upper * 255, 0, 255).astype(np.uint8), cv2.COLORMAP_TURBO)
            heat[~data['mask'][slot - 1]] = 0
            image = np.concatenate([overlay, heat], axis=1)
            ok, payload = cv2.imencode('.png', image)
            if not ok:
                raise ValueError('cannot encode rendering proof')
            path = output / f'proof_slot{slot:02d}_rgb_gt.png'
            with path.open('xb') as f:
                f.write(payload.tobytes())
            proofs.append(dict(row, arrays=arrays, side_by_side=pin(path)))
        print(json.dumps({'stage': 'visibility', **row}), flush=True)
    return proofs, write_json(output / 'all_frame_visibility.json', {'validated_slots': 32, 'frames': rows})


def prepare(args):
    from prepare_gt_scene import load_mesh, render_geometry
    output = data_path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    stage, context = 'authenticate_inputs', {}
    try:
        frames, contract = authenticated_frames(args)
        context.update(contract=pin(args.contract), frames_receipt=pin(args.frames_receipt))
        raw = source_paths(args.scene)
        raw_pins = {name: pin(path) for name, path in raw.items()}
        context['raw_sources'] = raw_pins
        write_json(output / 'INPUT_RECEIPT.json', context)
        stage = 'source_geometry'
        vertices, faces = load_mesh(raw['mesh'])
        groups, face_ids, vertex_ids, diagnostics = membership_boxes(vertices, faces,
            read_json(raw['segmentation']), read_json(raw['aggregation']), args.scene)
        text_metadata, axis = metadata(raw['metadata'])
        sensor = SensReader(raw['sensor'])
        write_json(output / 'sensor_header.json', sensor.header)
        association = save_arrays(output / 'vertex_membership.npz', vertex_instance_ids=vertex_ids,
                                  source_segment_ids=np.asarray(read_json(raw['segmentation'])['segIndices'], np.int64))
        instances = write_json(output / 'instances.json', {'segGroups': groups})
        mesh = save_arrays(output / 'instance_mesh.npz', vertices_world=vertices, faces=faces, face_instance_ids=face_ids)
        annotations = write_json(output / 'annotations.json', {'instances': [{'instance_id': g['objectId'], 'label': g['label']} for g in groups]})
        stage = 'all_32_sensor_ordinals'
        poses, intrinsics, hw, alignment, rgb, ordinal_proof = selected_camera_alignment(sensor, frames, output)
        ordinals = [r['ordinal'] for r in frames['frames']]
        calibration = save_arrays(output / 'official_cameras.npz', camera_poses=poses, intrinsics=intrinsics,
                                  indices=np.asarray(ordinals, np.int64), raster_hw=np.asarray(hw))
        stage = 'all_frame_reprojection'
        data, audits = render_geometry(vertices, poses, intrinsics, hw, ordinals)
        validate_dense(data, frames['frames'])
        dense = save_arrays(output / 'gt_dense_source_world.npz', **data)
        aligned = write_json(output / 'alignment.json', {'schema': 'r1313-scannet-alignment-v1',
            'pose_field': 'aligned_pose', 'pose_field_meaning': 'interface alias: identity_sensor_to_mesh @ sens.camera_to_world; no released aligned_pose field',
            'estimated_geometry_used': False, 'validated_slots': 32, 'frames': alignment, 'render_audits': audits,
            'sensor_to_mesh': np.eye(4).tolist(), 'axisAlignment_applied_to_mesh_and_pose': False,
            'axisAlignment_metadata': axis.tolist(), 'source_header': sensor.header,
            'target_grid': 'authenticated VSI RGB; source K scaled independently in x/y; identity target crop',
            'returned_geometry': 'unchanged canonical_geometry(data,[0,0,1]); metric scale 1'})
        source = write_json(output / 'source_provenance.json', {'schema': 'r1313-scannet-source-provenance-v1',
            'dataset': 'scannet', 'source_scene_id': args.scene, 'raw_sources': raw_pins,
            'source_frames_receipt': context['frames_receipt'], 'preparer_contract': context['contract'],
            'source_header': sensor.header, 'text_metadata': text_metadata,
            'calibration_authority': '.sens header; text metadata retained but never substitutes calibration',
            'association': 'vertex_segIndices; face has instance only when all three vertices agree',
            'vertex_membership': association, 'instances': diagnostics, 'ordinal_proof': ordinal_proof,
            'box_convention': BOX_CONVENTION, 'released_boxes': False, 'obb_estimator_used': True,
            'box_estimator': 'deterministic min/max of all officially associated mesh vertices; no fitted pose, padding or label change',
            'provider_axesLengths': 'half_extents', 'coordinate_frame': 'raw mesh/sensor world meters',
            'sensor_to_mesh': np.eye(4).tolist(), 'axisAlignment_applied_to_mesh_and_pose': False,
            'collector_admission': False})
        receipt = {'schema': SCHEMA, 'round': 1313, 'dataset': 'scannet', 'scene_name': args.scene,
            'runtime_scene_id': scene_id('scannet', args.scene), 'frames': frames['frames'], 'image_count': 32,
            'selected_frames': frames['selected_frames'], 'video': frames['video'], 'dense': dense,
            'calibration': calibration, 'instances': instances, 'instance_mesh': mesh, 'annotations': annotations,
            'alignment': aligned, 'source_provenance': source,
            'geometry_source': 'official_aligned_pose_intrinsic_mesh_gt_valid_support',
            'coordinate_frame': 'source_world_meters_opencv_camera_to_world', 'gravity_up': [0, 0, 1],
            'student_observations': 'question_and_authenticated32RGB_only',
            'teacher_initial_observations': 'text_question_and_choices; zero_inline_RGB; evidence_from_tools'}
        stage = 'all_frame_grounding_visibility'
        receipt['rendering_proof'], visibility = visibility_proof(output, receipt, rgb, data)
        stage = 'final_binding'
        validate_scene(receipt, load_dense=True)
        for spec in raw_pins.values():
            verify(spec, prepared=False)
        verify(context['frames_receipt'])
        verify_contract(args.contract, args.contract_sha256)
        final = write_json(output / 'scene_receipt.json', receipt)
        result = write_json(output / 'VALIDATION_RECEIPT.json', dict(context,
            schema='r1313-scannet-validation-v1', status='validated_not_admitted', scene=args.scene,
            scene_receipt=final, all_frame_visibility=visibility, paid_api_calls=0, gpu_runs=0))
        print(json.dumps({'scene': args.scene, 'status': 'validated_not_admitted', 'receipt': result}), flush=True)
    except Exception as error:
        failure = write_json(output / 'REFUSAL_RECEIPT.json', dict(context,
            schema='r1313-scannet-refusal-v1', status='refused', scene=args.scene, stage=stage,
            error_type=type(error).__name__, error=str(error), collector_admission=False,
            partial_artifacts={p.name: pin(p) for p in sorted(output.iterdir()) if p.is_file()}))
        print(json.dumps({'status': 'refused', 'receipt': failure}), flush=True)
        raise
