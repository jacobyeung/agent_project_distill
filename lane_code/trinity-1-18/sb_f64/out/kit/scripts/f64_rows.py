"""Dry-run inputs: two synthetic clips at real source resolutions and one row per stream and rank.

Rows follow the native C1 store layout. Text comes from real fixture rows (VQA) and the real
derivgen camera generator (routing). RGB is synthetic at 640x480 (ScanNet, 4:3) and 1280x720 (16:9).
The 64-viewpoint rows come from the 32-viewpoint rows through frame_input.nest_row.
"""
import json
import sqlite3
from pathlib import Path

import numpy as np
from PIL import Image

FIXTURES = Path('/scratch/jjyeung/orch_n30/sb_f64/pkg/fixtures/rows')
CLIPS = {'a43': dict(size=(640, 480), total=368, fps=24.0, seed=3),
         'b169': dict(size=(1280, 720), total=574, fps=24.0, seed=5)}


def make_clip(root, name):
    from student_pilot.carrier_c1_data import nested_indices
    from student_pilot.p3_provenance import file_pin
    spec = CLIPS[name]
    total, fps = spec['total'], spec['fps']
    anchors = [i * (total - 1) // 31 for i in range(32)]
    indices, _ = nested_indices(anchors)
    folder = Path(root) / 'frames' / name
    folder.mkdir(parents=True, exist_ok=True)
    width, height = spec['size']
    rng = np.random.default_rng(spec['seed'])
    yy, xx = np.mgrid[0:height, 0:width]
    pins = {}
    for ordinal in indices:
        path = folder / f'{ordinal:06d}.png'
        if not path.exists():
            phase = ordinal / total * 2 * np.pi
            base = np.stack([(xx / width * 255 + 40 * np.sin(phase)) % 256, (yy / height * 255) % 256,
                             np.full_like(xx, ordinal % 256)], -1)
            noise = rng.integers(0, 24, size=(height, width, 3))
            Image.fromarray(np.clip(base + noise, 0, 255).astype(np.uint8)).save(path, compress_level=1)
        pins[ordinal] = file_pin(path)
    return dict(name=name, anchors=anchors, pins=pins, total=total, fps=fps)


def student_input(clip, question, options):
    anchors, fps = clip['anchors'], clip['fps']
    return dict(frames=[dict(clip['pins'][k]) for k in anchors], frame_indices=list(anchors),
                timestamps=[k / fps for k in anchors], fps=fps, total_num_frames=clip['total'],
                question=question, options=list(options))


def vqa_row(clip, rank):
    source = json.loads((FIXTURES / 'slices_v3/d0_facing_hard.jsonl').read_text().splitlines()[0])
    question = (source.get('student_input') or {}).get('question') or source['question']
    options = (source.get('student_input') or {}).get('options') or source.get('options') or []
    return dict(qid=f'dry_vqa_{clip["name"]}_{rank}', dataset='d1', scene=f'dryrun_{clip["name"]}',
                question_type=source.get('question_type', 'object_rel_direction_hard'),
                answer=source['answer'], target=source['target'],
                student_input=student_input(clip, question, options))


def routing_row(clip, rank):
    from generator.derivgen_v7.derivgen import camera_rows as C
    from student_pilot import carrier_c1_routing as R
    count = 32
    codes = np.tile([0., 0., 0., 0., 0., 0., 1., .8, 1.], (count, 1))
    for i in range(count):
        angle = (i / 24) * np.pi / 4
        codes[i, :3] = [-np.cos(angle) * i / 24, 0., -np.sin(angle) * i / 24]
        codes[i, 3:7] = [0., -np.sin(angle / 2), 0., np.cos(angle / 2)]
    frames = [dict(clip['pins'][k], source_index=k) for k in clip['anchors']]
    source = dict(dataset='d1', scene=f'dryrun_{clip["name"]}', recording_id=clip['name'], frames=frames,
                  gt_pose9=codes.tolist(), gt_up=[0., -1., 0.], rgb_manifest=dict(path='dry-run', sha256='a' * 64))
    row = C._row(source, 'camera_displacement', 1, 25, C._Geometry(source).pair(1, 25))
    row['qid'] = f'dry_routing_{clip["name"]}_{rank}'
    return R.c1_row(row, dict(frames=frames, fps=clip['fps'], total_num_frames=clip['total']))


def pose_row(clip, rank):
    from student_pilot.camera_targets import trajectory_scale
    from student_pilot.pose_samples import AUGMENT, CATEGORY, SCHEMA, TARGET
    camera = [[0.02 * i, 0., 0.01 * i, 0., 0., 0., 1., 1.0, 1.25] for i in range(32)]
    mask = [True] * 32
    scale = trajectory_scale(camera, mask)
    sample = dict(schema=SCHEMA, recording=dict(sampling=dict(variant='all_frames32')), frames=32,
                  positions=list(range(32)), temporal_grouping='fused_pairs_all_frames', anchors=list(range(1, 33)),
                  augment={**AUGMENT, 'seed': 17 + rank}, metric=True, camera=camera, camera_mask=mask,
                  trajectory_scale=scale, gravity=[0., -1., 0.], gravity_mask=True)
    row = dict(qid=f'dry_pose_{clip["name"]}_{rank}', dataset='d1', scene=f'dryrun_{clip["name"]}',
               category=CATEGORY, answer='', target=TARGET, pose_sample=sample,
               student_input=student_input(clip, 'Describe this scene.', []))
    rng = np.random.default_rng(rank)
    uv = rng.uniform(50, 950, size=(32, 64, 2)).round(1).tolist()
    target = dict(camera=camera, camera_mask=mask, trajectory_scale=scale, gravity=[0., -1., 0.], gravity_mask=True,
                  metric=True, point_depth=dict(uv=uv, depth=rng.uniform(0.5, 6., size=(32, 64)).round(3).tolist(),
                                                mask=[[True] * 64] * 32))
    return row, target


def pointing_row(clip, rank):
    frame = 5
    question = f'In frame {frame}, point to the chair.'
    row = dict(qid=f'dry_pointing_{clip["name"]}_{rank}', dataset='d1', scene=f'dryrun_{clip["name"]}',
               question_type='pointing', answer='', target='<think>\n\n</think>\n\n{"point_2d": [512, 384]}',
               pointing=dict(frame=frame, kind='gt_instance_mask', instance_id='7',
                             rgb_sha256=clip['pins'][clip['anchors'][frame - 1]]['sha256']),
               student_input=student_input(clip, question, []))
    return row


def build(root, clip, nested, ranks=4):
    """One SQLite store per stream; rows for every rank; nested=True applies nest_row to every row."""
    from student_pilot.frame_input import nest_row
    from student_pilot.p3_provenance import file_pin
    root = Path(root)
    stores = {}
    for stream in ('pose', 'vqa', 'routing', 'pointing'):
        folder = root / ('f64' if nested else 'n32') / clip['name'] / stream
        folder.mkdir(parents=True, exist_ok=True)
        database = folder / 'rows.sqlite'
        wanted = []
        for rank in range(ranks):
            if stream == 'pose':
                row, target = pose_row(clip, rank)
            else:
                row, target = dict(vqa=vqa_row, routing=routing_row, pointing=pointing_row)[stream](clip, rank), {}
            if nested:
                row = nest_row(row, clip['pins'])
            wanted.append((rank, json.dumps(row), json.dumps(target)))
        if database.exists():
            # Stores are never deleted; an existing store is reused only when its rows are the ones wanted.
            with sqlite3.connect(f'file:{database}?mode=ro', uri=True) as connection:
                have = [tuple(r) for r in connection.execute('SELECT i, row, target FROM rows ORDER BY i')]
            if have != wanted:
                raise ValueError(f'existing store differs: {database}')
        else:
            with sqlite3.connect(database) as connection:
                connection.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY, row TEXT NOT NULL, target TEXT NOT NULL)')
                connection.executemany('INSERT INTO rows VALUES (?,?,?)', wanted)
        stores[stream] = dict(database=file_pin(database), count=ranks)
    return stores
