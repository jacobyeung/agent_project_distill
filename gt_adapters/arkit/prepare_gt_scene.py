"""Prepare one released ScanNet++ training scene on the authenticated RGB canvas."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import cv2
import numpy as np
from donor_geometry import Renderer, _PLY_DTYPES
from frame_alignment import canonical_geometry
from gt_scene_assets import DATA_ROOT, SCHEMA, data_path, pin, verify, read_json, write_json, save_arrays, scene_id, validate_dense
from gt_training_r1313 import TrainingGrounding

RAW_ROOT = Path('/data2/jjyeung/raw_datasets/scannetpp/data')
RAW_NAMES = ('scans/mesh_aligned_0.05.ply', 'scans/segments.json', 'scans/segments_anno.json',
             'iphone/pose_intrinsic_imu.json', 'iphone/rgb.mkv')


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


def instance_associations(vertices, faces, segments, groups):
    segment_ids = np.asarray(segments['segIndices'], dtype=np.int64)
    if segment_ids.shape == (len(faces),) and len(faces) != len(vertices):
        basis = 'face_segIndices'
    elif segment_ids.shape == (len(vertices),) and len(faces) != len(vertices):
        basis = 'vertex_segIndices_all_three_vertices_agree'
    else:
        raise ValueError('segIndices must map unambiguously to source mesh faces or vertices')
    mapping = {}
    for group in groups:
        iid = int(group.get('objectId', group['id']))
        for segment in group['segments']:
            segment = int(segment)
            if segment in mapping and mapping[segment] != iid:
                raise ValueError('source segment belongs to multiple instance groups')
            mapping[segment] = iid
    keys = np.array(sorted(mapping), dtype=np.int64)
    values = np.array([mapping[int(key)] for key in keys], dtype=np.int32)
    slots = np.searchsorted(keys, segment_ids)
    valid = slots < len(keys)
    valid &= keys[np.minimum(slots, len(keys) - 1)] == segment_ids
    assigned = np.full(len(segment_ids), -1, dtype=np.int32)
    assigned[valid] = values[slots[valid]]
    if basis.startswith('face'):
        face_ids = assigned
    else:
        tri_ids = assigned[faces]
        face_ids = np.where((tri_ids == tri_ids[:, :1]).all(axis=1), tri_ids[:, 0], -1).astype(np.int32)
    diagnostics = []
    for group in groups:
        iid = int(group.get('objectId', group['id']))
        selected = faces[face_ids == iid]
        obb = group['obb']
        axes = np.asarray(obb['normalizedAxes'], dtype=np.float64).reshape(3, 3)
        center = np.asarray(obb['centroid'], dtype=np.float64)
        lengths = np.asarray(obb['axesLengths'], dtype=np.float64)
        if not np.isfinite(axes).all() or not np.allclose(axes @ axes.T, np.eye(3), atol=1e-4) or not np.isfinite(center).all() or not np.isfinite(lengths).all() or np.any(lengths <= 0):
            raise ValueError('invalid official OBB')
        points = vertices[np.unique(selected)] if len(selected) else np.empty((0, 3))
        local = np.abs((points.astype(np.float64) - center) @ axes.T)
        ratios = (local.max(axis=0) / lengths).tolist() if len(local) else None
        diagnostics.append({'instance_id': iid, 'face_count': len(selected), 'max_axis_ratio_to_source_axesLengths': ratios})
    return face_ids, basis, diagnostics


def inputs(args):
    root = RAW_ROOT / args.scene
    raw = {name: root / name for name in RAW_NAMES}
    frames = read_json(args.frames_receipt)
    if frames['dataset'] != 'scannetppv2' or frames['scene_name'] != args.scene or len(frames['frames']) != 32:
        raise ValueError('frame receipt does not bind the requested source scene')
    vertices, faces = load_mesh(raw['scans/mesh_aligned_0.05.ply'])
    groups = read_json(raw['scans/segments_anno.json'])['segGroups']
    face_ids, basis, diagnostics = instance_associations(vertices, faces, read_json(raw['scans/segments.json']), groups)
    return raw, frames, vertices, faces, groups, face_ids, basis, diagnostics


def inspect(args):
    raw, frames, vertices, faces, groups, face_ids, basis, diagnostics = inputs(args)
    values = np.array([r['max_axis_ratio_to_source_axesLengths'] for r in diagnostics if r['max_axis_ratio_to_source_axesLengths'] is not None])
    result = {'schema': 'r1313-source-inspection-v1', 'scene': args.scene, 'vertices': len(vertices),
              'faces': len(faces), 'segGroups': len(groups), 'association': basis,
              'annotated_faces': int((face_ids >= 0).sum()), 'obb_axis_ratio_percentiles': np.percentile(values, [0, 10, 50, 90, 100], axis=0).tolist(),
              'instances': diagnostics}
    write_json(args.output, result)
    print(json.dumps({k: v for k, v in result.items() if k != 'instances'}, indent=2))


def selected_camera_alignment(raw, receipt):
    cameras = read_json(raw['iphone/pose_intrinsic_imu.json'])
    raw_video = cv2.VideoCapture(str(raw['iphone/rgb.mkv']))
    vsi_video = cv2.VideoCapture(str(verify(receipt['video'])))
    try:
        if not raw_video.isOpened() or not vsi_video.isOpened():
            raise ValueError('source or VSI video cannot be decoded')
        counts = [int(c.get(cv2.CAP_PROP_FRAME_COUNT)) for c in (raw_video, vsi_video)]
        fps = [float(c.get(cv2.CAP_PROP_FPS)) for c in (raw_video, vsi_video)]
        if counts[0] != counts[1] or counts[0] != receipt['video']['decoded_frame_count'] or len(cameras) != counts[0] or not np.allclose(fps, receipt['video']['fps']):
            raise ValueError('raw/VSI/pose ordinal or timebase mismatch')
        rows, poses, intrinsics, rgb = [], [], [], []
        raster_hw = None
        for slot, item in enumerate(receipt['frames']):
            selected = cv2.imread(str(verify(item)), cv2.IMREAD_COLOR)
            ordinal = item['ordinal']
            if item['stem'] != f'frame_{ordinal:06d}':
                raise ValueError('selected frame stem does not encode its source ordinal')
            decoded = []
            for capture in (raw_video, vsi_video):
                if not capture.set(cv2.CAP_PROP_POS_FRAMES, ordinal):
                    raise ValueError('video ordinal seek failed')
                ok, image = capture.read()
                if not ok or abs(capture.get(cv2.CAP_PROP_POS_FRAMES) - ordinal - 1) > 0.1:
                    raise ValueError('video seek did not return the selected ordinal')
                decoded.append(image)
            source, vsi = decoded
            if selected is None or not np.array_equal(vsi, selected):
                raise ValueError('authenticated selected PNG differs from its VSI video ordinal')
            sh, sw = source.shape[:2]
            vh, vw = vsi.shape[:2]
            if (sw, sh, vw, vh) != (1920, 1440, 640, 480):
                raise ValueError('unsupported source/VSI canvas; provide a separately validated corpus adapter')
            resized = cv2.resize(source, (vw, vh), interpolation=cv2.INTER_AREA)
            correlation = float(np.corrcoef(resized.reshape(-1), vsi.reshape(-1))[0, 1])
            mae = float(np.abs(resized.astype(np.float32) - vsi).mean())
            if not np.isfinite(correlation) or correlation < 0.99:
                raise ValueError(f'raw/VSI ordinal correlation failed at slot {slot + 1}')
            official = cameras[item['stem']]
            pose = np.asarray(official['aligned_pose'], dtype=np.float64)
            source_k = np.asarray(official['intrinsic'], dtype=np.float64)
            if pose.shape != (4, 4) or source_k.shape != (3, 3):
                raise ValueError('official aligned_pose/intrinsic shape mismatch')
            scale = np.diag([vw / sw, vh / sh, 1.0])
            grid_transform = np.eye(3)
            k = grid_transform @ scale @ source_k
            if not np.isfinite(k).all() or not np.allclose(k[2], [0, 0, 1]) or min(k[0, 0], k[1, 1]) <= 0 or not np.allclose([k[0, 1], k[1, 0]], 0):
                raise ValueError('official K is incompatible with the donor zero-skew renderer')
            if raster_hw is not None and raster_hw != (vh, vw):
                raise ValueError('selected RGB canvases differ')
            raster_hw = (vh, vw)
            rows.append({'slot_1based': slot + 1, 'ordinal': ordinal, 'stem': item['stem'],
                         'timestamp_sec': ordinal / fps[0], 'raw_source_canvas_wh': [sw, sh],
                         'vsi_canvas_wh': [vw, vh], 'target_canvas_wh': [vw, vh],
                         'source_intrinsic': source_k.tolist(), 'source_to_vsi': scale.tolist(),
                         'vsi_to_target_resize_crop': grid_transform.tolist(), 'crop_xyxy': [0, 0, vw, vh],
                         'target_intrinsic': k.tolist(), 'aligned_pose': pose.tolist(),
                         'raw_to_vsi_correlation': correlation, 'raw_to_vsi_mae': mae,
                         'selected_png_matches_vsi_decode': True, 'selected_rgb_sha256': item['sha256']})
            poses.append(pose)
            intrinsics.append(k)
            rgb.append(selected)
            print(json.dumps({'stage': 'aligned_rgb', 'slot': slot + 1, 'ordinal': ordinal, 'correlation': correlation}), flush=True)
        return np.asarray(poses, dtype=np.float32), np.asarray(intrinsics, dtype=np.float32), raster_hw, rows, rgb
    finally:
        raw_video.release()
        vsi_video.release()


def render_geometry(vertices, poses, intrinsics, raster_hw, ordinals):
    points, masks, depths, audits = [], [], [], []
    height, width = raster_hw
    yy, xx = np.indices(raster_hw, dtype=np.float64)
    for slot in range(32):
        pose, k = poses[slot].astype(np.float64), intrinsics[slot].astype(np.float64)
        depth, mask = Renderer._render(vertices, pose, k, height, width)
        z = depth.astype(np.float64)
        camera = np.stack([(xx - k[0, 2]) * z / k[0, 0], (yy - k[1, 2]) * z / k[1, 1], z], axis=-1)
        world = (camera @ pose[:3, :3].T + pose[:3, 3]).astype(np.float32)
        world[~mask] = np.nan
        if not mask.any():
            raise ValueError(f'no GT render support at slot {slot + 1}')
        projected = (world[mask].astype(np.float64) - pose[:3, 3]) @ pose[:3, :3]
        uv = projected[:, :2] / projected[:, 2:]
        uv = uv * [k[0, 0], k[1, 1]] + [k[0, 2], k[1, 2]]
        residual = np.linalg.norm(uv - np.column_stack([xx[mask], yy[mask]]), axis=1)
        maximum = float(residual.max())
        if maximum > 0.05:
            raise ValueError('GT ray-lift/reprojection residual exceeds0.05 pixels')
        points.append(world)
        masks.append(mask)
        depths.append(depth)
        audits.append({'slot_1based': slot + 1, 'valid_pixels': int(mask.sum()), 'max_reprojection_px': maximum})
    mask = np.stack(masks)
    data = {'pts3d_world': np.stack(points), 'mask': mask, 'depth_z': np.stack(depths),
            'conf': mask.astype(np.float32), 'camera_poses': poses, 'intrinsics': intrinsics,
            'indices': np.asarray(ordinals, dtype=np.int64)}
    canonical = canonical_geometry(data, [0, 0, 1])
    if not np.allclose(canonical['camera_poses'][0, :3, 3], 0, atol=1e-6):
        raise ValueError('canonical camera origin is inconsistent')
    return data, audits


def rendering_proof(output, receipt, rgb, data):
    provider = TrainingGrounding(receipt)
    scene = receipt['runtime_scene_id']
    inventory = provider._inventory(scene)
    mesh = provider._instance_mesh(scene)
    ids, counts = np.unique(mesh['instance_ids'], return_counts=True)
    candidates = sorted((int(count), int(iid)) for iid, count in zip(ids, counts) if iid >= 0 and count >= 32)
    proofs = []
    for slot in (0, 16):
        chosen = None
        attempts = 0
        pose, k, height, width = provider._camera(scene, slot + 1)
        for count, iid in candidates:
            corners = provider._obb_corners(scene, iid)
            u, v, z = provider._project(corners, pose, k)
            if not np.all(z > 0.05) or u.max() < 0 or u.min() >= width or v.max() < 0 or v.min() >= height:
                continue
            rendered = provider._render_instance(scene, slot + 1, iid)
            attempts += 1
            if rendered is not None and rendered['mask_pixel_count'] >= 32:
                chosen = (iid, rendered)
                break
            if attempts >= 16:
                break
        if chosen is None:
            raise ValueError('bounded proof could not find a visible annotated instance')
        iid, rendered = chosen
        label = inventory['labels'][iid]
        if iid not in provider.match_instances(scene, label):
            raise ValueError('donor label matcher lost a source annotation instance')
        mask = rendered['mask']
        mask_pin = save_arrays(output / f'proof_slot{slot + 1:02d}.npz', mask=mask, depth_z=data['depth_z'][slot], valid=data['mask'][slot])
        overlay = rgb[slot].copy()
        overlay[mask] = (0.55 * overlay[mask] + 0.45 * np.array([0, 255, 0])).astype(np.uint8)
        depth = data['depth_z'][slot]
        upper = float(np.percentile(depth[data['mask'][slot]], 99))
        heat = cv2.applyColorMap(np.clip(depth / upper * 255, 0, 255).astype(np.uint8), cv2.COLORMAP_TURBO)
        heat[~data['mask'][slot]] = 0
        outline = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)).astype(bool)
        heat[outline] = [255, 255, 255]
        image = np.concatenate([overlay, heat], axis=1)
        image = cv2.resize(image, (960, 360), interpolation=cv2.INTER_AREA)
        png = output / f'proof_slot{slot + 1:02d}_rgb_gt.png'
        ok, payload = cv2.imencode('.png', image)
        if not ok:
            raise ValueError('cannot encode rendering proof')
        with png.open('xb') as handle:
            handle.write(payload.tobytes())
        proofs.append({'slot_1based': slot + 1, 'instance_id': iid, 'label': label,
                       'visible_mask_pixels': int(mask.sum()), 'arrays': mask_pin, 'side_by_side': pin(png)})
    return proofs


def prepare(args):
    output = data_path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    raw, frames, vertices, faces, groups, face_ids, basis, diagnostics = inputs(args)
    raw_pins = {name: pin(path) for name, path in raw.items()}
    if args.obb_lengths not in ('full', 'half'):
        raise ValueError('declare the verified official OBB length convention')
    factor = 0.5 if args.obb_lengths == 'full' else 1.0
    prepared_groups = []
    for group, diagnostic in zip(groups, diagnostics):
        ratio = diagnostic['max_axis_ratio_to_source_axesLengths']
        if ratio is not None and max(ratio) > factor * 1.05:
            raise ValueError(f'official OBB convention fails mesh containment for instance {diagnostic["instance_id"]}')
        obb = dict(group['obb'], axesLengths=(np.asarray(group['obb']['axesLengths']) * factor).tolist())
        prepared_groups.append({'id': diagnostic['instance_id'], 'objectId': diagnostic['instance_id'],
                                'label': group['label'], 'obb': obb})
    iid = scene_id('scannetppv2', args.scene)
    instances = write_json(output / 'instances.json', {'segGroups': prepared_groups})
    mesh = save_arrays(output / 'instance_mesh.npz', vertices_world=vertices, faces=faces, face_instance_ids=face_ids)
    annotations = write_json(output / 'annotations.json', {'instances': [{'instance_id': g['id'], 'label': g['label']} for g in prepared_groups]})
    poses, intrinsics, raster_hw, alignment, rgb = selected_camera_alignment(raw, frames)
    ordinals = [row['ordinal'] for row in frames['frames']]
    calibration = save_arrays(output / 'official_cameras.npz', camera_poses=poses, intrinsics=intrinsics,
                              indices=np.array(ordinals), raster_hw=np.array(raster_hw))
    data, render_audits = render_geometry(vertices, poses, intrinsics, raster_hw, ordinals)
    validate_dense(data, frames['frames'])
    dense = save_arrays(output / 'gt_dense_source_world.npz', **data)
    alignment_pin = write_json(output / 'alignment.json', {'schema': 'r1313-official-alignment-v1',
        'pose_field': 'aligned_pose', 'estimated_geometry_used': False, 'validated_slots': 32,
        'source_to_vsi_scale': [1 / 3, 1 / 3], 'target_grid': 'authenticated640x480_RGB_canvas; identity resize/crop after VSI scaling',
        'frames': alignment, 'render_audits': render_audits, 'grounding_projection': 'source_world_meters',
        'returned_geometry': 'canonical_geometry(data,[0,0,1]); points and camera poses transformed together; scale1'})
    source_provenance = write_json(output / 'source_provenance.json', {'schema': 'r1313-source-provenance-v1',
        'dataset': 'scannetppv2', 'source_scene_id': args.scene, 'raw_sources': raw_pins,
        'source_frames_receipt': pin(args.frames_receipt), 'association': basis, 'instances': diagnostics,
        'official_obb_source_lengths': args.obb_lengths, 'provider_axesLengths': 'half_extents',
        'source_obb_scale_factor': factor, 'obb_estimator_used': False,
        'adaptation': 'official aligned_pose and intrinsic; source K/3; target canvas640x480 with identity resize/crop; GT-valid support only; no estimatedK or estimated/common support',
        'preprocessor': pin(__file__), 'renderer': pin(Path(__file__).with_name('donor_geometry.py')),
        'grounding_kernel': pin(Path(__file__).with_name('donor_grounding.py'))})
    receipt = {'schema': SCHEMA, 'round': 1313, 'dataset': 'scannetppv2', 'scene_name': args.scene,
        'runtime_scene_id': iid, 'frames': frames['frames'], 'image_count': 32,
        'selected_frames': frames['selected_frames'], 'video': frames['video'],
        'dense': dense, 'calibration': calibration, 'instances': instances, 'instance_mesh': mesh,
        'annotations': annotations, 'alignment': alignment_pin, 'source_provenance': source_provenance,
        'geometry_source': 'official_aligned_pose_intrinsic_mesh_gt_valid_support',
        'coordinate_frame': 'source_world_meters_opencv_camera_to_world', 'gravity_up': [0, 0, 1],
        'student_observations': 'question_and_authenticated32RGB_only',
        'teacher_initial_observations': 'text_question_and_choices; zero_inline_RGB; evidence_from_tools'}
    receipt['rendering_proof'] = rendering_proof(output, receipt, rgb, data)
    final = write_json(output / 'scene_receipt.json', receipt)
    registry = write_json(output / 'registry.json', {'schema': 'r1313-assets-registry-v1', 'round': 1313, 'receipts': [final]})
    print(json.dumps({'scene_ready': True, 'scene': iid, 'frames': 32, 'instances': len(groups),
                      'receipt': final, 'registry': registry, 'min_correlation': min(row['raw_to_vsi_correlation'] for row in alignment)}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('inspect', 'prepare'))
    parser.add_argument('--scene', required=True)
    parser.add_argument('--frames-receipt', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--obb-lengths', choices=('full', 'half'))
    args = parser.parse_args()
    scene_id('scannetppv2', args.scene)
    (inspect if args.command == 'inspect' else prepare)(args)


if __name__ == '__main__':
    main()
