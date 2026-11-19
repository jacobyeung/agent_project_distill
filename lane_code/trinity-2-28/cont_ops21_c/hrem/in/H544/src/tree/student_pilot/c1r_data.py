"""Plan-bound lazy RGB and teacher loading for exactly 32 camera viewpoints."""
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile
import time

import numpy as np
from PIL import Image
import torch

from . import pose_samples, c1r_align
from .carrier_c1_data import C1_B, insert_frame_carriers
from .p3_provenance import digest, file_pin, load, pinned, sha256, write


def processor_identity(manifest):
    """Use the authenticated base inventory to match the producer's processor seal."""
    names = ('config.json', 'processor_config.json', 'preprocessor_config.json', 'video_preprocessor_config.json',
             'tokenizer_config.json', 'tokenizer.json', 'special_tokens_map.json', 'chat_template.jinja',
             'chat_template.json', 'added_tokens.json', 'vocab.json', 'merges.txt')
    files = {name: manifest['files'][name] for name in names if name in manifest['files']}
    if 'tokenizer_config.json' not in files:
        raise ValueError('Base manifest lacks processor assets')
    return dict(schema='c1r-processor-v1', files=files, pixels=list(pose_samples.DEFAULT_PIXELS),
                prompt=pose_samples.PROMPT, target=pose_samples.TARGET, spatial_merge=2, temporal_patch=2)


def check_row(row, index, cfg):
    from .c1r_clips import validate_row_v2
    validate_row_v2(row)
    if (row['i'] != index or index != 32*row['step'] + 8*row['micro'] + row['rank']
            or not 0 <= row['micro'] < 4 or not 0 <= row['rank'] < 8
            or row['layout'] != cfg['frames']['layout'] or not re.fullmatch(r'[0-9a-f]{2,64}', row['qid'])):
        raise ValueError('Clip row plan index or layout differs')
    return len(row['ordinals'])


def check_receipt(plan, cfg, require_complete=False):
    """Bind the immutable plan, never the growing cache census."""
    from .c1r_clips import validate_plan
    from . import c1r_ref
    if 'dense_plan' in cfg['streams']:
        return check_dense_receipt(plan, cfg)
    if plan.get('schema') != 'c1r-clip-plan-v2':
        raise ValueError('Expected fixed-viewpoint clip plan v2')
    validate_plan(plan)
    if (plan.get('seed') != 17 or plan.get('steps') != cfg['recipe']['steps']
            or plan['frames']['layout'] != cfg['frames']['layout']
            or plan['frames'].get('pixels_per_frame') != list(pose_samples.DEFAULT_PIXELS)
            or plan['frames'].get('pair_gap_seconds', .5) != cfg['frames'].get('pair_gap_seconds', .5)):
        raise ValueError('Clip plan recipe or frame settings differ')
    teacher = load(pinned(cfg['teacher']))
    if (teacher.get('repository') != c1r_ref.REPOSITORY or teacher.get('revision') != c1r_ref.REVISION
            or teacher.get('layer') != 23 or teacher.get('input') != c1r_ref.INPUT
            or teacher.get('weights') != cfg['head_init']['weights']
            or teacher.get('weights_sha256') != teacher['weights']['sha256']):
        raise ValueError('Teacher identity or head initialization pin differs')
    root = Path(cfg['cache_root'])
    if not root.is_absolute():
        raise ValueError('Cache root must be absolute')
    return dict(schema='c1r-plan-binding-v2', plan=cfg['streams']['clips_plan'],
                teacher=cfg['teacher'], cache_root=str(root), count=len(plan['rows']),
                recordings_sha256=plan['recordings_sha256'],
                processor=processor_identity(load(pinned(cfg['model']))))


def clip_plan(cfg):
    """Authenticate either the legacy JSON plan or B2's layout JSONL."""
    path = pinned(cfg['streams']['clips_plan'])
    if 'dense_plan' not in cfg['streams']:
        return load(path)
    from .p3_provenance import unique
    with path.open() as stream:
        return [json.loads(line, object_pairs_hook=unique) for line in stream]


def check_dense_receipt(rows, cfg):
    from . import c1r_dense, c1r_ref
    plan = c1r_dense.validate_plan(load(pinned(cfg['streams']['dense_plan'])))
    if (plan['seed'] != 17 or plan['steps'] != cfg['recipe']['steps']
            or plan['pixels'] != list(pose_samples.DEFAULT_PIXELS)
            or cfg['frames']['layout'] == 'paired' and cfg['frames'].get('pair_gap_seconds', .5) != .5
            or len(rows) != len(plan['schedule'])):
        raise ValueError('Dense plan recipe differs')
    for i, row in enumerate(rows):
        if (row['i'] != i or row['layout'] != cfg['frames']['layout']
                or row['dense_plan_sha256'] != cfg['streams']['dense_plan']['sha256']):
            raise ValueError('Dense clip order, layout or plan pin differs')
    c1r_dense.check_clips(plan, rows)
    teacher = load(pinned(cfg['teacher']))
    if (teacher.get('repository') != c1r_ref.REPOSITORY or teacher.get('revision') != c1r_ref.REVISION
            or teacher.get('layer') != 23 or teacher.get('input') != c1r_ref.INPUT
            or teacher.get('weights') != cfg['head_init']['weights']
            or teacher.get('weights_sha256') != cfg['head_init']['weights']['sha256']):
        raise ValueError('Dense teacher identity differs')
    root = Path(cfg['cache_root'])
    if not root.is_absolute():
        raise ValueError('Cache root must be absolute')
    return dict(schema='c1r-dense-binding-v2', plan=cfg['streams']['clips_plan'],
                dense_plan=cfg['streams']['dense_plan'], teacher=cfg['teacher'], cache_root=str(root),
                count=len(rows), recordings_sha256=plan['source_order_sha256'],
                processor=processor_identity(load(pinned(cfg['model']))))


def dense_coverage(cfg):
    """Count rows backed by published indices and fully authenticated records.

    Unpublished blobs and partial files never count. Each published blob is
    hashed once by the native reader; every record also passes its array guards.
    This is an explicit CPU data audit, not a training launch or a GPU probe.
    """
    from . import c1r_dense as dense
    rows = clip_plan(cfg)
    receipt = check_dense_receipt(rows, cfg)
    plan = dense.validate_plan(load(pinned(cfg['streams']['dense_plan'])))
    root = Path(cfg['cache_root'])
    ready, indices = set(), []
    if (root / 'a0.json').exists():
        binding = load(root / 'a0.json')
        if (binding.get('schema') != 'c1r-dense-cache-v2'
                or binding.get('dense_plan', {}).get('sha256') != cfg['streams']['dense_plan']['sha256']
                or binding.get('runtime') != dense.runtime_identity()
                or binding.get('teacher') != load(pinned(cfg['teacher']))
                or binding.get('processor') != receipt['processor']):
            raise ValueError('Dense coverage store binding differs')
        for shard in plan['shards']:
            expected = {plan['records'][i]['recording_fingerprint']: plan['records'][i]
                        for i in shard['recordings']}
            for path in dense._part_paths(root, shard):
                pin = file_pin(path)
                index = load(path)
                if (index.get('schema') != 'c1r-dense-shard-v2' or index.get('binding') != binding
                        or not index.get('records')):
                    raise ValueError('Dense coverage shard binding differs')
                index['blob']['path'] = str(root / Path(index['blob']['path']).name)
                for entry in index['records']:
                    key = entry['recording_fingerprint']
                    if key not in expected or key in ready:
                        raise ValueError('Unexpected or duplicate published recording')
                    record = expected[key]['variants'].get(str(entry['capacity']))
                    if record is None:
                        raise ValueError('Published recording capacity differs')
                    dense.read_record(index, record, binding)
                    ready.add(key)
                if file_pin(path) != pin:
                    raise ValueError('Published shard index changed during coverage audit')
                indices.append(dict(index=pin, blob=index['blob']))
    count = sum(row['recording_fingerprint'] in ready for row in rows)
    prefix = next((i for i, row in enumerate(rows) if row['recording_fingerprint'] not in ready), len(rows))
    return dict(schema='c1r-dense-coverage-v1', plan=cfg['streams']['clips_plan'],
                dense_plan=cfg['streams']['dense_plan'], cache_root=str(root),
                teacher=cfg['teacher'], steps=cfg['recipe']['steps'],
                count=count, steps_available=prefix // 32, published=indices)


def readout_inputs(row, source, cfg):
    """Keep the 32 scored anchors; obtain partners from their full recording."""
    import bisect
    from .c1r_clips import nearest
    layout = cfg['frames']['layout']
    inputs = row['student_input']
    anchors = inputs['frame_indices']
    if len(anchors) != 32 or len(inputs['frames']) != 32:
        raise ValueError('Readout needs exactly 32 original anchors')
    if layout == 'spread':
        return inputs
    if layout == 'duplicate':
        slots = [v for v in anchors for _ in (0, 1)]
        frames = [v for v in inputs['frames'] for _ in (0, 1)]
    else:
        if ((row['dataset'], row['scene']) != (source['dataset'], source['scene'])
                or inputs['fps'] != source['student_input']['fps']
                or inputs['total_num_frames'] != source['student_input']['total_num_frames']
                or row.get('recording_id', source['recording_id']) != source['recording_id']):
            raise ValueError('Readout recording identity differs')
        frames_all = load(pinned(source['source_frames']))['frames']
        total = inputs['total_num_frames']
        with np.load(pinned(source['source_poses']), allow_pickle=False) as pack:
            numbers = pack['frame_indices'].tolist()
            poses = pack['c2w']
            if (numbers != sorted(set(numbers)) or len(numbers) != len(poses)
                    or poses.shape[1:] != (4, 4) or not np.isfinite(poses).all()):
                raise ValueError('Readout posed-frame inventory differs')
        if (len(frames_all) != total or not numbers or numbers[0] < 0 or numbers[-1] >= total
                or not set(anchors) <= set(numbers)):
            raise ValueError('Readout full-recording inventory differs')
        slots, frames = [], []
        for anchor, frame in zip(anchors, inputs['frames']):
            if frames_all[anchor]['sha256'] != frame['sha256']:
                raise ValueError('Heldout anchor does not belong to the partner recording')
            minimum = bisect.bisect_right(numbers, anchor)
            if minimum == len(numbers):
                raise ValueError('Readout anchor has no later posed partner')
            partner = numbers[nearest(numbers, anchor + cfg['frames'].get('pair_gap_seconds', .5)*inputs['fps'], minimum)]
            slots.extend((anchor, partner))
            frames.extend((frame, frames_all[partner]))
    return {**inputs, 'frames': frames, 'frame_indices': slots,
            'timestamps': [v / inputs['fps'] for v in slots]}


def encode_readout(processor, row, source, cfg):
    from transformers.video_utils import VideoMetadata
    from .carrier_c1_data import READOUT_TARGET
    inputs = readout_inputs(row, source, cfg)
    arrays = pose_samples.load_frames(inputs)
    metadata = VideoMetadata(total_num_frames=inputs['total_num_frames'], fps=inputs['fps'],
                             frames_indices=inputs['frame_indices'])
    batch, audit = pose_samples.encode_frames(processor, inputs['question'], inputs['options'] or [],
        arrays, metadata, READOUT_TARGET, pixels=cfg['frames']['pixels_per_frame'],
        max_length=cfg.get('max_sequence_tokens', 32768))
    batch = insert_frame_carriers(batch, processor.tokenizer, carrier_placement=cfg['carrier_placement'],
                                  frame_layout=cfg['frames']['layout'])
    if (batch['input_ids'].shape[1] > cfg.get('max_sequence_tokens', 32768)
            or batch['aux_camera_positions'].shape != (1, 32)):
        raise ValueError('Readout carrier count or complete sequence limit differs')
    batch['labels'].fill_(-100)
    return batch, None, audit


def readout_layout(cfg):
    layout = cfg['frames']['layout']
    return dict(layout=layout, pair_gap_seconds=cfg['frames'].get('pair_gap_seconds', .5),
        partner_rule='nearest_later_posed_ordinal_lower_tie_v1' if layout == 'paired' else layout,
        anchors_per_row=32, rgb_frames_per_row=32 if layout == 'spread' else 64,
        source='pinned_full_recording_inventories', reference_layout='spread',
        comparison_confounds=['layout', 'anchor_sampling', 'teacher'])


def wait_for_clip(loader, timeout=2700., poll=15., *, clock=time.monotonic, sleep=time.sleep):
    """Re-read published shard indices; corruption is never a readiness condition."""
    deadline = clock() + timeout
    while True:
        try:
            return loader()
        except FileNotFoundError as error:
            left = deadline - clock()
            if left <= 0:
                raise TimeoutError('Dense recording wait expired') from error
            sleep(min(poll, left))


def wait_for_files(paths, timeout=2700., poll=15., *, clock=time.monotonic, sleep=time.sleep):
    deadline = clock() + timeout
    while True:
        missing = [p for p in paths if not p.is_file()]
        if not missing:
            return
        left = deadline - clock()
        if left <= 0:
            raise TimeoutError('Cache wait expired: ' + ', '.join(str(p) for p in missing))
        sleep(min(poll, left))


def load_g3t(path, row, tar_sha256, processor_sha256=None, include_patch=False):
    """Validate the complete NPZ and select the 32 anchor camera tokens."""
    n = len(row['ordinals'])
    with np.load(path, allow_pickle=False) as cache:
        from .c1r_ref import KEYS_V2, validate_cache_v2
        if set(cache.files) != KEYS_V2:
            raise ValueError('Teacher cache keys differ')
        validate_cache_v2(cache, row)
        if processor_sha256 is not None and str(cache['processor_sha256'].item()) != processor_sha256:
            raise ValueError('Teacher processor identity differs')
        expected = dict(cam_token_l23=(n, 2048), local_pose_enc=(n, 6),
                        global_pose_enc=(n, 5), coords_1024=(n, 4), camera=(32, 9),
                        gravity=(3,))
        arrays = {}
        for key, shape in expected.items():
            value = cache[key]
            if value.shape != shape or value.dtype.kind != 'f' or not np.isfinite(value).all():
                raise ValueError('Teacher cache shape or values differ: ' + key)
            arrays[key] = value.copy()
        if cache['cam_token_l23'].dtype != np.float16:
            raise ValueError('Teacher camera cache must use float16')
        for key, expected_value in dict(qid=row['qid'], layout=row['layout'], frames_tar_sha256=tar_sha256).items():
            if cache[key].shape != () or str(cache[key].item()) != expected_value:
                raise ValueError('Teacher cache row identity differs: ' + key)
        for key in ('ordinals', 'anchor_slots'):
            if cache[key].dtype.kind not in 'iu' or cache[key].tolist() != row[key]:
                raise ValueError('Teacher cache row identity differs: ' + key)
        grid = cache['video_grid_thw']
        if (grid.shape != (3,) or grid.dtype.kind not in 'iu' or (grid <= 0).any()
                or int(grid[0]) != len(row['slots'])//2 or int(grid[1]) % 2 or int(grid[2]) % 2):
            raise ValueError('Teacher video grid differs')
        patch = cache['patch_pooled']
        if (patch.shape != (int(grid[0]), int(grid[1])//2, int(grid[2])//2, 2048)
                or patch.dtype != np.float16 or not np.isfinite(patch).all()):
            raise ValueError('Teacher patch grid differs')
        record = dict(camera=arrays['camera'], camera_mask=cache['camera_mask'].copy(),
                      trajectory_scale=cache['trajectory_scale'].item(), gravity=arrays['gravity'],
                      gravity_mask=cache['gravity_mask'].item(), metric=True)
        targets = target_tensors(record, 32)
        anchors = np.asarray(row['slot_map'])[row['anchor_slots']]
        targets['aux_g3t_cam'] = torch.from_numpy(arrays['cam_token_l23'][anchors].astype(np.float32))[None]
        return targets, grid.copy(), patch.astype(np.float32) if include_patch else None


def target_tensors(record, n=32):
    camera = np.asarray(record['camera'], dtype=np.float32)
    mask = np.asarray(record['camera_mask'])
    gravity = np.asarray(record['gravity'], dtype=np.float32)
    if (camera.shape != (n, 9) or mask.shape != (n,) or mask.dtype != np.bool_
            or not mask.any() or not np.isfinite(camera).all() or gravity.shape != (3,)
            or not np.isfinite(gravity).all() or type(record.get('gravity_mask')) is not bool
            or record.get('metric') is not True or not np.isfinite(record['trajectory_scale'])
            or record['trajectory_scale'] < 0):
        raise ValueError('Clip pose target shape or values differ')
    return dict(aux_camera_target=torch.from_numpy(camera)[None],
                aux_camera_mask=torch.from_numpy(mask)[None],
                aux_camera_scale=torch.tensor([record['trajectory_scale']], dtype=torch.float32),
                aux_gravity_target=torch.from_numpy(gravity)[None],
                aux_gravity_mask=torch.tensor([record['gravity_mask']], dtype=torch.bool))


def read_frames(path, row):
    """Decode distinct frames once; authenticate every member before augmentation."""
    from .p3_provenance import digest, unique
    import json
    arrays = []
    with tarfile.open(path, mode='r:') as archive:
        names = [f'{k:06d}.jpg' for k in range(len(row['ordinals']))]
        members = archive.getmembers()
        if [m.name for m in members] != names + ['frames.json'] or not all(m.isfile() for m in members):
            raise ValueError('Frame archive member layout differs')
        manifest = json.loads(archive.extractfile('frames.json').read(), object_pairs_hook=unique)
        if (manifest.get('schema') != 'c1r-frames-v2' or manifest.get('qid') != row['qid']
                or any(manifest.get(k) != row[k] for k in ('ordinals', 'slot_map', 'anchor_slots', 'layout', 'slots', 'viewpoints'))
                or manifest.get('row_sha256') != digest(row)
                or manifest.get('recording_fingerprint') != row['recording_fingerprint']
                or len(manifest.get('members', [])) != len(names)):
            raise ValueError('Frame manifest identity differs')
        for name, entry in zip(names, manifest['members']):
            raw = archive.extractfile(name).read()
            if entry['name'] != name or hashlib.sha256(raw).hexdigest() != entry['sha256']:
                raise ValueError('Frame member digest differs')
            with Image.open(io.BytesIO(raw)) as image:
                if image.format != 'JPEG' or image.mode != 'RGB' or [image.height, image.width] != entry['raster_hw']:
                    raise ValueError('Frame raster or RGB format differs')
                arrays.append(np.asarray(image).copy())
    if len({image.shape for image in arrays}) != 1:
        raise ValueError('Clip frames have unequal raster sizes')
    return np.stack(arrays)


PATCH_ARRAYS = ('patch_full', 'patch_pooled')


def lean_read_record(index, record, binding):
    """c1r_dense.read_record for runs without a patch term.

    The shard blob is not rehashed: the index pins each header's SHA-256 and
    every header pins its arrays' SHA-256. Every array the run reads is hashed
    once per process; the patch arrays stay unread memory maps (shape-checked).
    """
    from . import c1r_dense, c1r_ref
    import math
    import struct
    if index.get('schema') != 'c1r-dense-shard-v2' or index['binding'] != binding:
        raise ValueError('Shard binding mismatch')
    blob = index['blob']
    signature = c1r_dense._signature(blob['path'])
    digest_ = c1r_dense.clips.sha256(c1r_dense.clips.canonical(record))
    cache_key = ('lean', signature, digest_, c1r_dense.clips.sha256(c1r_dense.clips.canonical(index)))
    if cache_key in c1r_dense._LOADED:
        return c1r_dense._LOADED[cache_key]
    expected_offset, found, seen = len(c1r_dense.MAGIC), None, set()
    for entry in index['records']:
        key = entry['recording_fingerprint']
        if (key in seen or entry['offset'] != expected_offset or entry['length'] < 8
                or entry['payload_offset'] <= entry['offset'] + 8):
            raise ValueError('Invalid recording index offsets')
        expected_offset += entry['length']
        seen.add(key)
        if key == record['recording_fingerprint']:
            found = entry
    if expected_offset != signature[1] or found is None:
        raise ValueError('Shard index extent mismatch')
    with open(blob['path'], 'rb') as stream:
        if stream.read(len(c1r_dense.MAGIC)) != c1r_dense.MAGIC:
            raise ValueError('Shard magic mismatch')
        stream.seek(found['offset'])
        length = struct.unpack('<Q', stream.read(8))[0]
        if length > 1024 * 1024 or found['offset'] + 8 + length != found['payload_offset']:
            raise ValueError('Invalid recording header length')
        raw = stream.read(length)
    header = json.loads(raw)
    if (c1r_dense.clips.sha256(raw) != found['header_sha256'] or header['record_sha256'] != digest_
            or found['record_sha256'] != digest_ or header['recording_fingerprint'] != record['recording_fingerprint']
            or found['capacity'] != record['capacity']
            or found['payload_offset'] + header['payload_bytes'] != found['offset'] + found['length']):
        raise ValueError('Recording header binding mismatch')
    arrays, cursor = {}, 0
    allowed = {'<f2', '<f4', '<f8', '<i8', '<u2', '|u1'}
    for name, spec in sorted(header['arrays'].items()):
        dtype = np.dtype(spec['dtype'])
        shape = spec['shape']
        if (spec['dtype'] not in allowed or not shape or any(type(k) is not int or k < 1 for k in shape)
                or spec['offset'] != cursor or math.prod(shape) * dtype.itemsize != spec['nbytes']
                or cursor + spec['nbytes'] > header['payload_bytes']
                or (name == 'patch_full' and spec.get('logical_dtype') != 'bfloat16')):
            raise ValueError('Invalid array offsets or dtype')
        array = np.memmap(blob['path'], dtype=dtype, mode='r', shape=tuple(shape),
                          offset=found['payload_offset'] + cursor)
        if name not in PATCH_ARRAYS and c1r_dense.clips.sha256(memoryview(array).cast('B')) != spec['sha256']:
            raise ValueError('Array SHA-256 mismatch')
        arrays[name] = array
        cursor += spec['nbytes']
    if cursor != header['payload_bytes']:
        raise ValueError('Array payload extent mismatch')
    n = record['n']
    c1r_ref.validate_arrays(arrays, n)
    grid = arrays['grid_hw']
    if grid.shape != (2,) or grid.dtype != np.int64 or (grid <= 0).any():
        raise ValueError('Invalid spatial grid')
    h, w = map(int, grid)
    if arrays['patch_pooled'].shape != (n, h, w, c1r_dense.WIDTH) or arrays['patch_pooled'].dtype != np.float16:
        raise ValueError('Invalid pooled tokens')
    if arrays['ordinals'].dtype != np.int64 or arrays['ordinals'].tolist() != record['ordinals']:
        raise ValueError('Recording frame identity changed')
    for name, shape, dtype in (('c2w', (n, 4, 4), np.float64), ('intrinsics', (n, 3, 3), np.float64),
                               ('raster_hw', (n, 2), np.int64), ('world_up', (3,), np.float64)):
        a = arrays[name]
        if a.shape != shape or a.dtype != dtype or not np.isfinite(a).all():
            raise ValueError('Invalid pose array: ' + name)
    if (arrays['raster_hw'] <= 0).any() or not np.all(arrays['raster_hw'] == arrays['raster_hw'][0]):
        raise ValueError('Invalid raster')
    offsets, rgb = arrays['rgb_offsets'], arrays['rgb_bytes']
    if (rgb.ndim != 1 or rgb.dtype != np.uint8 or offsets.shape != (n+1,) or offsets.dtype != np.int64
            or offsets[0] != 0 or offsets[-1] != len(rgb) or (np.diff(offsets) <= 0).any()):
        raise ValueError('Invalid RGB offsets')
    roi = arrays['coords_1024']
    if (roi[:, :2] < 0).any() or (roi[:, 2:] > 1024).any() or (roi[:, 2:] <= roi[:, :2]).any():
        raise ValueError('Invalid square-pad ROI')
    expected = {'cam_token_l23', 'local_pose_enc', 'global_pose_enc', 'coords_1024', 'patch_pooled', 'grid_hw',
                'ordinals', 'raster_hw', 'c2w', 'intrinsics', 'world_up', 'rgb_bytes', 'rgb_offsets'}
    if record['full_tokens']:
        expected.add('patch_full')
        full = arrays['patch_full']
        if full.shape != (n, 37, 37, c1r_dense.WIDTH) or full.dtype != np.uint16:
            raise ValueError('Invalid bf16 full tokens')
    if set(arrays) != expected:
        raise ValueError('Recording array keys changed')
    if len(c1r_dense._LOADED) >= 8:
        c1r_dense._LOADED.pop(next(iter(c1r_dense._LOADED)))
    c1r_dense._LOADED[cache_key] = arrays
    return arrays


class ClipRows:
    def __init__(self, receipt, processor, cfg, *, augment_fn=None, wait_timeout=2700., wait_poll=15.):
        self.dense = 'dense_plan' in cfg['streams']
        expected_schema = 'c1r-dense-binding-v2' if self.dense else 'c1r-plan-binding-v2'
        if (receipt.get('schema') != expected_schema or receipt['plan'] != cfg['streams']['clips_plan']
                or receipt['teacher'] != cfg['teacher'] or receipt['cache_root'] != cfg['cache_root']):
            raise ValueError('Clip plan binding differs')
        if self.dense and receipt.get('dense_plan') != cfg['streams']['dense_plan']:
            raise ValueError('Dense plan binding differs')
        self.plan = clip_plan(cfg)
        if self.dense:
            self.dense_plan = load(pinned(receipt['dense_plan']))
        self.teacher = load(pinned(receipt['teacher']))
        self.processor_identity = processor_identity(load(pinned(cfg['model'])))
        if receipt.get('processor') != self.processor_identity:
            raise ValueError('Clip processor binding differs')
        self.root = Path(receipt['cache_root'])
        self.processor, self.cfg = processor, cfg
        self.augment = pose_samples.augment if augment_fn is None else augment_fn
        self.wait_timeout, self.wait_poll = wait_timeout, wait_poll

    def get(self, index):
        if self.dense:
            return self.get_dense(index)
        from transformers.video_utils import VideoMetadata
        if type(index) is not int or not 0 <= index < len(self.plan['rows']):
            raise ValueError('Missing planned clip')
        row = self.plan['rows'][index]
        check_row(row, index, self.cfg)
        qid = row['qid']
        tar = self.root / 'f' / qid[:2] / (qid + '.tar')
        npz = self.root / 'g' / qid[:2] / (qid + '.npz')
        binding = self.root / 'binding.json'
        wait_for_files([binding, tar, npz], self.wait_timeout, self.wait_poll)
        if load(binding) != dict(schema='c1r-cache-binding-v2', teacher=self.teacher,
                                 recordings_sha256=self.plan['recordings_sha256'],
                                 plan_sha256=self.cfg['streams']['clips_plan']['sha256'],
                                 processor=self.processor_identity):
            raise ValueError('Cache teacher or recording identity differs')
        targets, grid, patch = load_g3t(npz, row, sha256(tar), digest(self.processor_identity),
                                      include_patch=c1r_align.patch_enabled(self.cfg['align']))
        arrays = read_frames(tar, row)
        # Use the plan's distinct-frame seeds; duplicate copies share the result.
        arrays = np.concatenate([self.augment(arrays[k:k+1], {**pose_samples.AUGMENT, 'seed': seed})
                                 for k, seed in enumerate(row['augment_seeds'])])
        arrays = arrays[row['slot_map']]
        metadata = VideoMetadata(total_num_frames=row['total_num_frames'], fps=row['fps'],
                                 frames_indices=row['slots'])
        batch, audit = pose_samples.encode_frames(self.processor, pose_samples.PROMPT, [], arrays,
            metadata, pose_samples.TARGET, pixels=list(pose_samples.DEFAULT_PIXELS),
            max_length=self.cfg.get('max_sequence_tokens', 32768))
        if batch['video_grid_thw'].tolist() != [grid.tolist()]:
            raise ValueError('Processor video_grid_thw differs from teacher NPZ')
        batch = insert_frame_carriers(batch, self.processor.tokenizer, carrier_placement=self.cfg['carrier_placement'],
                                      frame_layout=row['layout'])
        if batch['input_ids'].shape[1] > self.cfg.get('max_sequence_tokens', 32768):
            raise ValueError('Carriers exceed complete sequence token limit')
        if batch['aux_camera_positions'].shape != (1, 32):
            raise ValueError('Clip must have exactly 32 camera tokens')
        batch['labels'].fill_(-100)
        if c1r_align.patch_enabled(self.cfg['align']):
            targets['aux_g3t_patch'] = torch.from_numpy(patch.reshape(-1, 2048))
        return batch, targets, {**audit, 'qid': qid, 'layout': row['layout'], 'N': 32,
                                'frame_count': len(row['slots']), 'sequence_tokens': batch['input_ids'].shape[1]}

    def get_dense(self, index):
        from . import c1r_dense
        from transformers.video_utils import VideoMetadata
        if type(index) is not int or not 0 <= index < len(self.plan):
            raise ValueError('Missing planned clip')
        row = self.plan[index]
        if row['i'] != index or row['layout'] != self.cfg['frames']['layout']:
            raise ValueError('Dense clip row differs')

        def read():
            binding = load(self.root / 'a0.json')
            if (binding.get('schema') != 'c1r-dense-cache-v2'
                    or binding['dense_plan']['sha256'] != self.cfg['streams']['dense_plan']['sha256']
                    or binding.get('teacher') != self.teacher
                    or binding.get('processor') != self.processor_identity):
                raise ValueError('Dense store identity differs')
            # Without a patch term the loader never reads patch payloads; the
            # pinned loader file stays byte-identical to the cache runtime binding.
            native = c1r_dense.read_record
            if not c1r_align.patch_enabled(self.cfg['align']):
                c1r_dense.read_record = lean_read_record
            try:
                return c1r_dense.load_clip(row, self.root)
            except FileNotFoundError as error:
                if str(error) == 'Recording is not ready':
                    raise
                raise ValueError('Published dense store file is missing') from error
            finally:
                c1r_dense.read_record = native

        slots, record, tokens, patch = wait_for_clip(read, self.wait_timeout, self.wait_poll)
        position = self.dense_plan['schedule'][index]
        shard = next(s for s in self.dense_plan['shards'] if position in s['recordings'])
        entries = [entry for path in c1r_dense._part_paths(self.root, shard)
                   for entry in load(path)['records']
                   if entry['recording_fingerprint'] == row['recording_fingerprint']]
        if len(entries) != 1:
            raise ValueError('Dense recording index differs')
        capacity = str(entries[0]['capacity'])
        variant = row['variants'][capacity]
        dense_record = self.dense_plan['records'][position]['variants'][capacity]
        unique = {}
        for image, j, ordinal in zip(slots, variant['slot_dense_indices'], variant['slots']):
            if j not in unique:
                seed = int(hashlib.sha256(f'c1r-aug:17:{index}:{ordinal}'.encode()).hexdigest()[:8], 16)
                unique[j] = self.augment(image[None], {**pose_samples.AUGMENT, 'seed': seed})[0]
        arrays = np.stack([unique[j] for j in variant['slot_dense_indices']])
        metadata = VideoMetadata(total_num_frames=dense_record['ordinals'][-1]+1,
                                 fps=dense_record['fps'], frames_indices=variant['slots'])
        batch, audit = pose_samples.encode_frames(self.processor, pose_samples.PROMPT, [], arrays,
            metadata, pose_samples.TARGET, pixels=list(pose_samples.DEFAULT_PIXELS),
            max_length=self.cfg.get('max_sequence_tokens', 32768))
        grid = [len(slots)//2, patch.shape[1]*2, patch.shape[2]*2]
        if batch['video_grid_thw'].tolist() != [grid]:
            raise ValueError('Processor video_grid_thw differs from dense store')
        batch = insert_frame_carriers(batch, self.processor.tokenizer, carrier_placement=self.cfg['carrier_placement'],
                                      frame_layout=row['layout'])
        if (batch['input_ids'].shape[1] > self.cfg.get('max_sequence_tokens', 32768)
                or batch['aux_camera_positions'].shape != (1, 32)):
            raise ValueError('Dense clip carrier count or sequence limit differs')
        batch['labels'].fill_(-100)
        targets = target_tensors(record)
        targets['aux_g3t_cam'] = torch.from_numpy(tokens.astype(np.float32))[None]
        if c1r_align.patch_enabled(self.cfg['align']):
            targets['aux_g3t_patch'] = torch.from_numpy(patch.astype(np.float32).reshape(-1, 2048))
        return batch, targets, {**audit, 'qid': row['qid'], 'layout': row['layout'], 'N': 32,
            'frame_count': len(slots), 'sequence_tokens': batch['input_ids'].shape[1],
            'capacity': int(capacity), 'anchor_ordinals': variant['target_ordinals']}

    def close(self):
        pass


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['coverage'])
    parser.add_argument('--config', required=True)
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    write(args.report, dense_coverage(load(args.config)))


if __name__ == '__main__':
    main()
