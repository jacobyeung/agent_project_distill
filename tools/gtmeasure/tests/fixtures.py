import os
from pathlib import Path
import struct
import uuid
import zlib

import numpy as np

from tools.gtmeasure.assets import load_scene
from tools.gtmeasure.io import OUTPUT_ROOT, new_output, pin, write_json, write_jsonl
from tools.gtmeasure.split import SplitPolicy


def fixture_root():
    base = Path(os.environ.get('GTMEASURE_TEST_OUTPUT', OUTPUT_ROOT / 'gtmeasure_synthetic_tests'))
    return new_output(base / uuid.uuid4().hex)


def make_room_labels(root, scene, answer='16.0'):
    from tools.gtmeasure.room_labels import RoomLabels

    dataset, name = scene.receipt['dataset'], scene.receipt['scene_name']
    path = root / 'room_labels.jsonl'
    write_jsonl(path, [{'question_type': 'absolute_size_room', 'video': f'{dataset}/{name}.mp4', 'conversations': [
        {'from': 'human', 'value': 'What is the room size in square meters?'}, {'from': 'gpt', 'value': answer}]}])
    policy = SplitPolicy({'seed': 17, 'validation_fraction': .1, 'train_scenes': [f'{dataset}/{name}'], 'heldout_scenes': []})
    return RoomLabels(pin(path), [(dataset, name)], policy, set())


def png_bytes():
    def chunk(kind, value):
        payload = kind + value
        return struct.pack('>I', len(value)) + payload + struct.pack('>I', zlib.crc32(payload))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 64, 64, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress((b'\x00' + b'\x60\x80\xa0' * 64) * 64)) + chunk(b'IEND', b''))


def make_scene(root, name='scene0000_00'):
    root.mkdir(parents=True, exist_ok=False)
    vertices, faces, memberships, groups, annotations = [], [], [], [], []
    for iid, label in enumerate(['chair', 'chair', 'table', 'lamp', 'desk', 'door', 'window', 'floor']):
        x, z = -6. + iid * 2, 8.
        points = np.array([[x - .5, -.5, z], [x + .5, -.5, z], [x + .5, .5, z], [x - .5, .5, z]])
        if label == 'floor':
            points = np.array([[0., 0., 0.], [4., 0., 0.], [4., 4., 0.], [0., 4., 0.]])
        lower, upper = points.min(axis=0), points.max(axis=0)
        obb = {'centroid': ((lower + upper) / 2).tolist(), 'axesLengths': np.maximum((upper - lower) / 2, .001).tolist(),
               'normalizedAxes': np.eye(3).ravel().tolist()}
        groups.append({'id': iid, 'objectId': iid, 'label': label, 'obb': obb})
        annotations.append({'instance_id': iid, 'label': label})
        start = len(vertices)
        vertices.extend(points)
        faces.extend([[start, start + 1, start + 2], [start, start + 2, start + 3]])
        memberships.extend([iid, iid])
    vertices, faces = np.array(vertices), np.array(faces, dtype=np.int32)
    intrinsic = np.array([[32., 0., 32.], [0., 32., 32.], [0., 0., 1.]])
    depth = np.full((64, 64), 10., dtype=np.float32)
    for point in vertices[vertices[:, 2] > 0]:
        projected = intrinsic @ point
        x, y = (projected[:2] / projected[2]).astype(int)
        depth[y, x] = point[2]
    yy, xx = np.indices((64, 64))
    world = np.stack([(xx - 32) * depth / 32, (yy - 32) * depth / 32, depth], axis=-1).astype(np.float32)
    arrays = {'pts3d_world': np.repeat(world[None], 32, axis=0), 'depth_z': np.repeat(depth[None], 32, axis=0),
              'intrinsics': np.repeat(intrinsic[None], 32, axis=0), 'camera_poses': np.repeat(np.eye(4)[None], 32, axis=0),
              'mask': np.ones((32, 64, 64), dtype=bool), 'conf': np.ones((32, 64, 64), dtype=np.float32),
              'indices': np.arange(32, dtype=np.int64)}
    np.savez_compressed(root / 'dense.npz', **arrays)
    np.savez_compressed(root / 'calibration.npz', **{key: arrays[key] for key in ('intrinsics', 'camera_poses', 'indices')}, raster_hw=np.array([64, 64]))
    np.savez_compressed(root / 'mesh.npz', vertices_world=vertices, faces=faces, face_instance_ids=np.array(memberships, dtype=np.int32))
    frames = []
    for index in range(32):
        path = root / f'frame_{index:06d}.png'
        path.write_bytes(png_bytes())
        frames.append({**pin(path), 'ordinal': index, 'stem': path.stem, 'timestamp_sec': index / 2})
    write_json(root / 'instances.json', {'segGroups': groups})
    write_json(root / 'annotations.json', {'instances': annotations})
    write_json(root / 'alignment.json', {'validated_slots': 32, 'pose_field': 'aligned_pose', 'estimated_geometry_used': False,
                                        'frames': [{'ordinal': index} for index in range(32)]})
    write_json(root / 'source_provenance.json', {'fixture': True, 'box_convention': 'half_extents'})
    video = root / 'video.fixture'
    video.write_bytes(b'CPU fixture; RGB evidence is pinned separately.')
    receipt = {'schema': 'r1313-scene-assets-v1', 'round': 1313, 'dataset': 'scannet', 'scene_name': name,
               'runtime_scene_id': 'scannet__' + name, 'coordinate_frame': 'source_world_meters_opencv_camera_to_world',
               'gravity_up': [0, 0, 1], 'geometry_source': 'official_aligned_pose_intrinsic_mesh_gt_valid_support',
               'frames': frames, 'image_count': 32, 'selected_frames': [frame['stem'] for frame in frames],
               'video': {**pin(video), 'fps': 2., 'decoded_frame_count': 32}}
    for key, filename in [('dense', 'dense.npz'), ('calibration', 'calibration.npz'), ('instance_mesh', 'mesh.npz'),
                          ('instances', 'instances.json'), ('annotations', 'annotations.json'), ('alignment', 'alignment.json'),
                          ('source_provenance', 'source_provenance.json')]:
        receipt[key] = pin(root / filename)
    write_json(root / 'scene_receipt.json', receipt)
    return load_scene(root / 'scene_receipt.json')
