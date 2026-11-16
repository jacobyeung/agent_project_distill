from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import cv2
import numpy as np
from gt_scene_assets import pin

SCENE = '47300001'
SOURCE_HW = (192, 256)
TARGET_HW = (96, 128)
ORDINALS = np.linspace(0, 39, 32).astype(int).tolist()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as handle:
        json.dump(value, handle, sort_keys=True, indent=2, allow_nan=False)
        handle.write('\n')
    return pin(path)


def write_png(path, image):
    ok, encoded = cv2.imencode('.png', image)
    if not ok:
        raise ValueError('fixture PNG encoding failed')
    with Path(path).open('xb') as handle:
        handle.write(encoded.tobytes())


def rotation_z(angle):
    c, s = np.cos(angle), np.sin(angle)
    return np.asarray([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=np.float64)


def pose_at(ordinal):
    pose = np.eye(4)
    pose[:3, :3] = rotation_z(0.35 + ordinal * 0.001) @ np.asarray([[1, 0, 0], [0, 0, 1], [0, -1, 0]])
    pose[:3, 3] = [1.2 + ordinal * 0.003, -1.1 + ordinal * 0.001, 1.4]
    return pose


def source_objects():
    pose = pose_at(0)
    rows = []
    for uid, label, camera_center, lengths, angle in (
            ('uid-b-chair', 'chair', [-0.65, 0.08, 3.0], [0.8, 0.64, 1.08], 0.55),
            ('uid-a-table', 'table', [0.7, 0.12, 3.6], [1.08, 0.7, 0.8], -0.2)):
        center = pose[:3, :3] @ camera_center + pose[:3, 3]
        rows.append({'uid': uid, 'label': label, 'segments': {'obbAligned': {
            'centroid': center.tolist(), 'axesLengths': lengths,
            'normalizedAxes': rotation_z(angle).T.reshape(-1).tolist()}}})
    return rows


def mesh_from_objects(objects):
    vertices, faces = [], []
    for item in objects:
        box = item['segments']['obbAligned']
        half = np.asarray(box['axesLengths']) / 2
        axes = np.asarray(box['normalizedAxes']).reshape(3, 3)
        for fixed in range(3):
            free = [axis for axis in range(3) if axis != fixed]
            for sign in (-1, 1):
                start = len(vertices)
                for y in range(9):
                    for x in range(9):
                        local = np.zeros(3)
                        local[fixed] = sign * half[fixed]
                        local[free[0]] = (x / 4 - 1) * half[free[0]]
                        local[free[1]] = (y / 4 - 1) * half[free[1]]
                        vertices.append(local @ axes + box['centroid'])
                for y in range(8):
                    for x in range(8):
                        a = start + y * 9 + x
                        faces.extend([[a, a + 1, a + 10], [a, a + 10, a + 9]])
    start = len(vertices)
    for y in range(13):
        for x in range(13):
            vertices.append([-4 + x * 2 / 3, -2 + y * 2 / 3, 0])
    for y in range(12):
        for x in range(12):
            a = start + y * 13 + x
            faces.extend([[a, a + 1, a + 14], [a, a + 14, a + 13]])
    return np.asarray(vertices, dtype='<f4'), np.asarray(faces, dtype='<i4')


def write_mesh(path, vertices, faces):
    header = ('ply\nformat binary_little_endian 1.0\n' + f'element vertex {len(vertices)}\n' +
              'property float x\nproperty float y\nproperty float z\n' + f'element face {len(faces)}\n' +
              'property list uchar int vertex_indices\nend_header\n')
    records = np.empty(len(faces), dtype=[('count', 'u1'), ('vertices', '<i4', (3,))])
    records['count'] = 3
    records['vertices'] = faces
    with Path(path).open('xb') as handle:
        handle.write(header.encode('ascii'))
        handle.write(vertices.tobytes())
        handle.write(records.tobytes())


def ray_box_oracle(objects, pose, height, width, pixel_offset=0.5):
    scale = width / SOURCE_HW[1]
    k = np.asarray([[180 * scale, 0, 128 * scale], [0, 184 * scale, 96 * scale], [0, 0, 1]])
    yy, xx = np.indices((height, width), dtype=np.float64)
    rays = np.stack([(xx + pixel_offset - k[0, 2]) / k[0, 0],
                     (yy + pixel_offset - k[1, 2]) / k[1, 1], np.ones_like(xx)], axis=-1)
    world_rays = rays @ pose[:3, :3].T
    depths = np.full((height, width), np.inf)
    instance = np.full((height, width), -1, dtype=np.int32)
    ids = {uid: index for index, uid in enumerate(sorted(item['uid'] for item in objects))}
    for item in objects:
        box = item['segments']['obbAligned']
        axes = np.asarray(box['normalizedAxes']).reshape(3, 3)
        origin = (pose[:3, 3] - box['centroid']) @ axes.T
        direction = world_rays @ axes.T
        half = np.asarray(box['axesLengths']) / 2
        near = np.full((height, width), -np.inf)
        far = np.full((height, width), np.inf)
        for axis in range(3):
            parallel = np.abs(direction[..., axis]) < 1e-12
            safe = np.where(parallel, 1, direction[..., axis])
            a = (-half[axis] - origin[axis]) / safe
            b = (half[axis] - origin[axis]) / safe
            near = np.maximum(near, np.where(parallel, -np.inf, np.minimum(a, b)))
            far = np.minimum(far, np.where(parallel, np.inf, np.maximum(a, b)))
            if abs(origin[axis]) > half[axis]:
                far[parallel] = -np.inf
        visible = (near > 0.05) & (far >= near) & (near < depths)
        depths[visible] = near[visible]
        instance[visible] = ids[item['uid']]
    return instance, depths.astype(np.float32), k


def make_fixture(root, fault=None, mapping_basis='equal_ordinal_export', codec='FFV1'):
    root = Path(root)
    sequence = root / 'raw/Training' / SCENE
    source_dir, intrinsic_dir = sequence / 'lowres_wide', sequence / 'lowres_wide_intrinsics'
    source_dir.mkdir(parents=True, exist_ok=False)
    intrinsic_dir.mkdir()
    selected_dir = root / 'selected'
    selected_dir.mkdir()
    objects = source_objects()
    vertices, faces = mesh_from_objects(objects)
    if fault != 'missing_mesh':
        write_mesh(sequence / f'{SCENE}_3dod_mesh.ply', vertices, faces)
    annotation = {'data': copy.deepcopy(objects), 'skipped': False, 'stats': {}}
    if fault == 'malformed_annotation':
        annotation['data'][0]['segments']['obbAligned']['axesLengths'][0] = -1
    if fault == 'unsupported_instance':
        annotation['data'][0]['segments']['obbAligned']['centroid'] = [100, 100, 100]
    write_json(sequence / f'{SCENE}_3dod_annotation.json', annotation)
    timestamps = [f'{100 + ordinal / 60:.3f}' for ordinal in range(40)]
    trajectory, expected_poses, expected_masks, expected_depths = [], [], [], []
    video_path = root / ('vsi.mp4' if codec == 'mp4v' else 'vsi.avi')
    writer = cv2.VideoWriter(str(video_path), cv2.VideoWriter_fourcc(*codec), 60, TARGET_HW[::-1])
    if not writer.isOpened():
        raise RuntimeError(f'CPU fixture video encoder unavailable: {codec}')
    try:
        for ordinal, stamp in enumerate(timestamps):
            pose = pose_at(ordinal)
            extrinsics = np.linalg.inv(pose)
            axis_angle = cv2.Rodrigues(extrinsics[:3, :3])[0].reshape(3)
            line = stamp + ' ' + ' '.join(f'{value:.12f}' for value in np.r_[axis_angle, extrinsics[:3, 3]])
            if not (fault == 'missing_pose' and ordinal == 0):
                trajectory.append(line)
            if fault == 'ambiguous_pose' and ordinal == 0:
                trajectory.append('100.0005' + line[len(stamp):])
            if not (fault == 'missing_intrinsics' and ordinal == 0):
                with (intrinsic_dir / f'{SCENE}_{stamp}.pincam').open('x') as handle:
                    handle.write('256 192 180 184 128 96\n')
            labels, _, _ = ray_box_oracle(objects, pose, *SOURCE_HW)
            yy, xx = np.indices(SOURCE_HW)
            image = np.stack([(xx + ordinal * 19) % 256, (yy * 2 + ordinal * 31) % 256,
                              (xx // 2 + yy + ordinal * 7) % 256], axis=-1).astype(np.uint8)
            for iid, color in ((0, [160, 195, 35]), (1, [35, 55, 220])):
                image[labels == iid] = color
            if codec == 'mp4v' and fault != 'compression_stress':
                image = cv2.cvtColor(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
            if fault == 'constant_rgb' and ordinal == 0:
                image[:] = [20, 80, 150]
            source_image = np.flip(image, axis=1).copy() if fault == 'misaligned_frame' and ordinal == 0 else image
            if fault == 'uint16_rgb' and ordinal == 0:
                source_image = source_image.astype(np.uint16) * 257
            write_png(source_dir / f'{SCENE}_{stamp}.png', source_image)
            writer.write(cv2.resize(image, TARGET_HW[::-1], interpolation=cv2.INTER_AREA))
            if ordinal in ORDINALS:
                mask, depth, _ = ray_box_oracle(objects, pose, *TARGET_HW)
                expected_poses.append(pose)
                expected_masks.append(mask)
                expected_depths.append(depth)
    finally:
        writer.release()
    with (sequence / 'lowres_wide.traj').open('x') as handle:
        handle.write('\n'.join(trajectory) + '\n')
    captured = cv2.VideoCapture(str(video_path))
    frames = []
    try:
        for ordinal in range(40):
            ok, image = captured.read()
            if not ok:
                raise ValueError('fixture video decode did not yield40 frames')
            if ordinal in ORDINALS:
                stem = f'frame_{ordinal:06d}'
                target = selected_dir / (stem + '.png')
                write_png(target, image)
                frames.append(dict(pin(target), stem=stem, ordinal=ordinal))
        if captured.read()[0]:
            raise ValueError('fixture encoder emitted extra frames')
    finally:
        captured.release()
    frame_receipt = {'schema': 'fixture-vsi-selected-rgb-v1', 'dataset': 'arkitscenes', 'scene_name': SCENE,
                     'frames': frames, 'selected_frames': [row['stem'] for row in frames],
                     'video': dict(pin(video_path), decoded_frame_count=40, fps=60.0)}
    frame_pin = write_json(root / 'frames_receipt.json', frame_receipt)
    authority = write_json(root / 'export_authority.json', {'schema': 'synthetic-export-authority-v1',
        'source_frame_count': 40, 'video_frame_count': 40, 'export': 'numeric timestamp ordered RGB, area resize256x192 to128x96, no crop',
        'mapping_basis': mapping_basis, 'source_generator': pin(__file__)})
    timeline = [{'ordinal': i, 'filename': f'{SCENE}_{stamp}.png', 'timestamp': stamp} for i, stamp in enumerate(timestamps)]
    digest = hashlib.sha256(json.dumps(timeline, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    mapping = {'schema': 'r1313-arkit-frame-map-v1', 'dataset': 'arkitscenes', 'scene_name': SCENE,
        'video': pin(video_path), 'source_frames_receipt': frame_pin, 'source_stream': 'lowres_wide',
        'mapping_basis': mapping_basis, 'mapping_authority': authority,
        'source_timeline_sha256': digest, 'source_frame_count': 40, 'resize': 'area',
        'frames': [{'vsi_ordinal': i, 'source_ordinal': i, 'source_timestamp': timestamps[i]} for i in ORDINALS]}
    if fault == 'timeline_drift':
        mapping['source_timeline_sha256'] = '0' * 64
    write_json(root / 'correspondence.json', mapping)
    with (root / 'analytic_oracle.npz').open('xb') as handle:
        np.savez_compressed(handle, camera_poses=np.asarray(expected_poses), instance_ids=np.asarray(expected_masks), depth_z=np.asarray(expected_depths))
    return SimpleNamespace(dataset='arkitscenes', scene=SCENE, sequence_dir=sequence,
                           frames_receipt=root / 'frames_receipt.json', correspondence=root / 'correspondence.json',
                           output=root / 'prepared', obb_lengths=None)
