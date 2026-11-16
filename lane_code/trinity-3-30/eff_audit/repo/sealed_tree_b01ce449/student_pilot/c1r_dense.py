"""Exact recording-wide frame plans, authenticated caches, and lazy clip loading."""
import argparse
import bisect
import fcntl
from collections import Counter
import importlib
import io
import json
import math
import os
from pathlib import Path
import random
import struct
import time

import numpy as np

from . import c1r_clips as clips
from . import c1r_ref
from .c1r_targets import encode_target

MAGIC = b'C1RD0002'
WIDTH = 2048
PATCHES = 37 * 37
CAPACITIES = (224, 208)
LAYOUTS = ('spread', 'paired', 'paired-1', 'duplicate', 'paired-16')
LIMIT_BYTES = 76_000_000_000
_VERIFIED = {}
_LOADED = {}
_PLANS = {}
_RUNTIME = {}


def uniform(values, count):
    """Choose distinct positions on a uniform raw-time grid, including both ends."""
    if not 1 <= count <= len(values):
        raise ValueError('Invalid uniform count')
    if count == 1:
        return [values[0]]
    result, previous = [], -1
    for k in range(count):
        target = values[0] + k * (values[-1] - values[0]) / (count - 1)
        j = clips.nearest(values, target, previous + 1)
        j = min(j, len(values) - count + k)
        result.append(values[j])
        previous = j
    return result


def dense_frames(source, capacity=224):
    """Freeze anchors and both exact partner maps before constructing any clip."""
    if capacity not in CAPACITIES:
        raise ValueError('Capacity must be 224 or 208')
    numbers = clips.posed_ordinals(source)
    if len(numbers) < 34:
        raise ValueError('Recording needs at least 34 posed frames')
    # Reserve two tail ordinals so every anchor has two distinct later partners.
    anchors = uniform(numbers[:-2], min(capacity // 3, len(numbers) - 2))
    partners = {'0.5': [], '1.0': []}
    deviations = 0
    for anchor in anchors:
        minimum = bisect.bisect_right(numbers, anchor)
        half = clips.nearest(numbers, anchor + .5 * source['fps'], minimum)
        one = clips.nearest(numbers, anchor + source['fps'], minimum)
        if one == half:
            choices = [j for j in (one - 1, one + 1) if minimum <= j < len(numbers)]
            one = min(choices, key=lambda j: (abs(numbers[j] - anchor - source['fps']), numbers[j]))
            deviations += 1
        partners['0.5'].append(numbers[half])
        partners['1.0'].append(numbers[one])
    chosen = set(anchors + partners['0.5'] + partners['1.0'])
    count = min(capacity, len(numbers))
    fill = uniform([v for v in numbers if v not in chosen], count - len(chosen)) if count > len(chosen) else []
    ordinals = sorted(chosen.union(fill))
    return {'capacity': capacity, 'n': count, 'ordinals': ordinals, 'anchors': anchors,
            'partners': partners, 'fill': fill, 'origin_dense_index': 0,
            'shortfall': capacity - count, 'anchor_shortfall': capacity // 3 - len(anchors),
            'resolution': 'all_posed' if count < capacity else 'uniform_fill',
            'partner_collision_resolutions': deviations,
            'tail_reserved': numbers[-2:]}


def clip_variant(i, record, layout, seed=17):
    """Construct slots by exact lookup; no requested training frame is remapped."""
    if layout not in LAYOUTS:
        raise ValueError('Unknown layout')
    values = record['anchors']
    count = 16 if layout == 'paired-16' else 32
    rng = random.Random(f'c1r-dense:{seed}:{i}')
    # The first and last anchors stay fixed; interior bins jitter uniformly.
    positions = [0]
    for k in range(1, count - 1):
        low = 1 + (k - 1) * (len(values) - 2) // (count - 2)
        high = 1 + k * (len(values) - 2) // (count - 2)
        positions.append(rng.randrange(low, high))
    positions.append(len(values) - 1)
    anchors = [values[k] for k in positions]
    if layout == 'spread':
        slots, target_ordinals = anchors, anchors
    elif layout == 'duplicate':
        slots, target_ordinals = [v for a in anchors for v in (a, a)], anchors
    else:
        gap = '1.0' if layout == 'paired-1' else '0.5'
        slots = [v for k in positions for v in (values[k], record['partners'][gap][k])]
        target_ordinals = slots if layout == 'paired-16' else anchors
    lookup = {v: k for k, v in enumerate(record['ordinals'])}
    return {'capacity': record['capacity'], 'anchors': anchors, 'slots': slots,
            'slot_dense_indices': [lookup[v] for v in slots],
            'target_ordinals': target_ordinals, 'anchor_dense_indices': [lookup[v] for v in target_ordinals],
            'temporal_patches': len(slots) // 2}


def clip_row(plan, i, layout, plan_sha256):
    record = plan['records'][plan['schedule'][i]]
    return {'schema': 'c1r-dense-row-v2', 'i': i, 'step': i // 32, 'micro': i % 32 // 8,
            'rank': i % 8, 'qid': clips.sha256(f"c1r-qid:{plan['seed']}:{i}".encode())[:24],
            'layout': layout, 'dense_plan_sha256': plan_sha256,
            'recording_fingerprint': record['recording_fingerprint'],
            'variants': {str(n): clip_variant(i, record['variants'][str(n)], layout, plan['seed'])
                         for n in CAPACITIES}}


def build_plan(sources, a1, *, steps=800, seed=17, full_budget=10**12, recordings_per_shard=8):
    """Keep the admitted census and seeded recording order; freeze both capacities."""
    if (type(steps) is not int or steps < 1 or type(seed) is not int or seed != 17
            or type(full_budget) is not int or full_budget < 0
            or type(recordings_per_shard) is not int or recordings_per_shard < 1):
        raise ValueError('Invalid plan settings')
    records, remaining, prefix = [], full_budget, True
    for position, source in enumerate(sources):
        variants = {str(n): dense_frames(source, n) for n in CAPACITIES}
        cost = variants['224']['n'] * PATCHES * WIDTH * 2
        full = prefix and cost <= remaining
        prefix = full
        if full:
            remaining -= cost
        key = clips.fingerprint(source)
        for variant in variants.values():
            variant.update(recording_fingerprint=key, source_sha256=clips.sha256(clips.canonical(source)),
                           full_tokens=full, fps=source['fps'])
        records.append({'recording_fingerprint': key, 'source_position': position, 'variants': variants})
    ids = [r['recording_fingerprint'] for r in records]
    if not records or len(set(ids)) != len(ids):
        raise ValueError('Empty or duplicate recording census')
    schedule = []
    for epoch in range(math.ceil(steps * 32 / len(records))):
        order = list(range(len(records)))
        random.Random(f'c1r-record:{seed}:{epoch}').shuffle(order)
        schedule.extend(order)
    schedule = schedule[:steps * 32]
    first = {j: i for i, j in reversed(list(enumerate(schedule)))}
    order = sorted(range(len(records)), key=lambda j: (first.get(j, math.inf), j))
    shards = [{'id': f'{k // recordings_per_shard:08x}', 'recordings': order[k:k+recordings_per_shard]}
              for k in range(0, len(order), recordings_per_shard)]
    return {'schema': 'c1r-dense-plan-v2', 'a1_plan': a1, 'seed': seed, 'steps': steps,
            'records': records, 'schedule': schedule, 'shards': shards,
            'source_order_sha256': clips.sha256(clips.canonical(ids)),
            'full_budget_bytes': full_budget, 'full_used_bytes': full_budget - remaining,
            'sampling': 'uniform_anchors_exact_partners_uniform_fill', 'capacities': list(CAPACITIES),
            'layouts': list(LAYOUTS), 'pixels': list(clips.pose_samples.DEFAULT_PIXELS)}


def validate_plan(plan, sources=None):
    if plan.get('schema') != 'c1r-dense-plan-v2' or plan['capacities'] != list(CAPACITIES):
        raise ValueError('Dense plan binding mismatch')
    if sources is not None:
        expected = build_plan(sources, plan['a1_plan'], steps=plan['steps'], seed=plan['seed'],
                              full_budget=plan['full_budget_bytes'],
                              recordings_per_shard=max(len(s['recordings']) for s in plan['shards']))
        if clips.canonical(expected) != clips.canonical(plan):
            raise ValueError('Dense plan source or sampling mismatch')
    return plan


def check_clips(plan, rows):
    """Check every planned slot against its exact recording and frozen partner map."""
    count = slots = 0
    for row in rows:
        expected = clip_row(plan, row['i'], row['layout'], row['dense_plan_sha256'])
        if row != expected:
            raise ValueError('Exact clip binding mismatch')
        rec = plan['records'][plan['schedule'][row['i']]]
        for capacity, variant in row['variants'].items():
            record = rec['variants'][capacity]
            dense = record['ordinals']
            if (variant['slots'][0] != dense[0] or len(variant['anchor_dense_indices']) != 32
                    or variant['target_ordinals'][0] != dense[0]
                    or len(set(variant['anchors'])) != len(variant['anchors'])
                    or variant['slots'] != [dense[j] for j in variant['slot_dense_indices']]
                    or variant['target_ordinals'] != [dense[j] for j in variant['anchor_dense_indices']]):
                raise ValueError('Exact frame membership mismatch')
            slots += len(variant['slots'])
        count += 1
    return {'rows': count, 'slots_both_capacities': slots, 'exact': True}


def write_plans(plan, output):
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    path = root / 'a0.json'
    clips.write_json(path, plan)
    pin = clips.pin(path)
    result = {'plan': pin, 'layouts': {}}
    for k, layout in enumerate(LAYOUTS):
        destination = root / f'{k+1:02x}.jsonl'
        def write(stream):
            for i in range(len(plan['schedule'])):
                stream.write(clips.canonical(clip_row(plan, i, layout, pin['sha256'])) + b'\n')
        clips.atomic(destination, write)
        result['layouts'][layout] = clips.pin(destination)
    return result


def final_layer(aggregator, images):
    """Pinned upstream operation order with only the final concatenation retained."""
    import torch
    if (aggregator.training or aggregator.depth != 24 or aggregator.aa_block_size != 1
            or list(aggregator.aa_order) != ['frame', 'global'] or aggregator.patch_start_idx != 5
            or images.ndim != 5 or images.shape[2] != 3):
        raise ValueError('Unsupported final-layer aggregator contract')
    b, s, channels, h, w = images.shape
    normalized = (images - aggregator._resnet_mean) / aggregator._resnet_std
    normalized = normalized.view(b * s, channels, h, w)
    patches = aggregator.patch_embed(normalized)
    if isinstance(patches, dict):
        patches = patches['x_norm_patchtokens']
    def expand(value):
        query = value[:, 0:1].expand(b, 1, *value.shape[2:])
        others = value[:, 1:].expand(b, s - 1, *value.shape[2:])
        return torch.cat([query, others], dim=1).view(b * s, *value.shape[2:])
    tokens = torch.cat([expand(aggregator.camera_token), expand(aggregator.register_token), patches], dim=1)
    del patches, normalized
    pos = None
    if aggregator.rope is not None:
        pos = aggregator.position_getter(b * s, h // aggregator.patch_size, w // aggregator.patch_size,
                                         device=images.device)
        pos = pos + 1
        special = torch.zeros(b * s, aggregator.patch_start_idx, 2).to(images.device).to(pos.dtype)
        pos = torch.cat([special, pos], dim=1)
    _, p, c = tokens.shape
    fi = gi = 0
    for layer in range(24):
        tokens, fi, frame = aggregator._process_frame_attention(tokens, b, s, p, c, fi, pos=pos)
        tokens, gi, global_ = aggregator._process_global_attention(tokens, b, s, p, c, gi, pos=pos)
        if layer == 23:
            result = torch.cat([frame[0], global_[0]], dim=-1)
        del frame, global_
    return result, aggregator.patch_start_idx


def lean_forward(model, inputs):
    """Autocast the backbone; run FP32 heads on the final camera tokens only."""
    import torch
    cuda = inputs.device.type == 'cuda'
    with torch.inference_mode():
        with torch.autocast('cuda', dtype=torch.bfloat16, enabled=cuda):
            block, start = final_layer(model.aggregator, inputs[None])
        with torch.autocast('cuda', enabled=False):
            # CameraHead discards every patch. Avoid an FP32 copy of the entire block.
            camera = block[:, :, :1, :].float()
            local = model.local_camera_head([camera])[-1]
            global_ = model.global_camera_head([camera])[-1]
    return block, start, local, global_


def pool_frames(patches, coords, grid_hw):
    """Reuse the reviewed spatial ROI pooling, with no temporal fusion."""
    import torch
    h, w = map(int, grid_hw)
    if min(h, w) <= 0:
        raise ValueError('Invalid merged spatial grid')
    result = []
    for i in range(len(patches)):
        value = c1r_ref.pool_patches(patches[i:i+1], coords[i:i+1],
                                    np.array([1, 2*h, 2*w], np.int64), [0, 0])
        result.append(value[0].cpu())
    return torch.stack(result).numpy()


class DenseTeacher(c1r_ref.Teacher):
    def __init__(self, source_dir, weights_dir, device):
        import torch
        root = Path(weights_dir).resolve()
        cls = c1r_ref.source_import(source_dir)
        # Depth and point heads require earlier layers and are outside this cache.
        self.model = cls.from_pretrained(str(root), local_files_only=True,
                                         enable_depth=False, enable_point=False).eval().to(device)
        self.model.local_camera_head.float()
        self.model.global_camera_head.float()
        self.device = torch.device(device)
        self.preprocess = importlib.import_module('vggt.utils.load_fn').load_and_preprocess_images_square

    def extract(self, images, *, grid_hw, full_tokens=False):
        import torch
        import torch.nn.functional as functional
        measure = self.device.type == 'cuda' and not hasattr(self, 'peak_memory')
        if measure:
            torch.cuda.reset_peak_memory_stats(self.device)
        frames, coords = [], []
        with torch.inference_mode():
            # Keep the exact square-pad transform without a D x 1024 x 1024 GPU stack.
            for image in images:
                square, coordinate = self.preprocess([image], 1024)
                frames.append(functional.interpolate(square.to(self.device), size=(518, 518),
                              mode='bilinear', align_corners=False)[0])
                coords.append(coordinate[0, :4])
            inputs = torch.stack(frames)
            del frames
            coords = torch.stack(coords)
            block, start, local, global_ = lean_forward(self.model, inputs)
            if start != 5 or block.shape != (1, len(inputs), 1374, WIDTH):
                raise ValueError('Final teacher layer shape changed')
            patches = block[0, :, start:]
            result = {'cam_token_l23': block[0, :, 0].half().cpu().numpy(),
                      'local_pose_enc': local[0].float().cpu().numpy(),
                      'global_pose_enc': global_[0].float().cpu().numpy(),
                      'coords_1024': coords.float().numpy(),
                      'patch_pooled': pool_frames(patches, coords, grid_hw)}
            if full_tokens:
                # NumPy has no portable bf16 dtype: preserve its raw 16-bit words.
                full = np.empty((len(inputs), 37, 37, WIDTH), dtype='<u2')
                for i in range(len(inputs)):
                    full[i] = patches[i].reshape(37, 37, WIDTH).to(torch.bfloat16).view(torch.uint16).cpu().numpy()
                result['patch_full'] = full
        if measure:
            torch.cuda.synchronize(self.device)
            self.peak_memory = {'allocated_bytes': torch.cuda.max_memory_allocated(self.device),
                                'reserved_bytes': torch.cuda.max_memory_reserved(self.device)}
        return result



def pose_arrays(poses, source, record, raster):
    numbers = clips.posed_ordinals(source)
    lookup = {v: j for j, v in enumerate(numbers)}
    order = [lookup[v] for v in record['ordinals']]
    n = record['n']
    hw = np.asarray(poses['raster_hw'])
    hw = np.broadcast_to(hw, (len(numbers), 2)) if hw.shape == (2,) else hw
    selected_hw = np.asarray(hw[order], np.int64)
    if selected_hw.shape != (n, 2) or not np.all(selected_hw == raster):
        raise ValueError('RGB and pose raster mismatch')
    from .camera_targets import rigid
    if (not all(rigid(pose) for pose in poses['c2w'][order])
            or not np.isfinite(poses['intrinsics'][order]).all()
            or (poses['intrinsics'][order, 0, 0] <= 0).any()
            or (poses['intrinsics'][order, 1, 1] <= 0).any()):
        raise ValueError('Invalid dense pose or intrinsics')
    # Use the native encoder as the gravity admission check.
    probe = [record['ordinals'][j] for j in np.linspace(0, n-1, 32).astype(int)]
    encode_target(poses, probe, source)
    return {'c2w': np.asarray(poses['c2w'][order], np.float64),
            'intrinsics': np.asarray(poses['intrinsics'][order], np.float64),
            'raster_hw': selected_hw, 'world_up': np.asarray(poses['world_up'], np.float64)}


def jpeg_arrays(payloads):
    offsets = np.cumsum([0] + [len(v) for v in payloads], dtype=np.int64)
    return {'rgb_bytes': np.frombuffer(b''.join(payloads), dtype=np.uint8), 'rgb_offsets': offsets}


def validate_arrays(arrays, record):
    c1r_ref.validate_arrays(arrays, record['n'])
    n = record['n']
    grid = arrays['grid_hw']
    if grid.shape != (2,) or grid.dtype != np.int64 or (grid <= 0).any():
        raise ValueError('Invalid spatial grid')
    h, w = map(int, grid)
    pooled = arrays['patch_pooled']
    if pooled.shape != (n, h, w, WIDTH) or pooled.dtype != np.float16 or not np.isfinite(pooled).all():
        raise ValueError('Invalid pooled tokens')
    if arrays['ordinals'].dtype != np.int64 or arrays['ordinals'].tolist() != record['ordinals']:
        raise ValueError('Recording frame identity changed')
    for name, shape, dtype in (('c2w', (n, 4, 4), np.float64),
                               ('intrinsics', (n, 3, 3), np.float64),
                               ('raster_hw', (n, 2), np.int64), ('world_up', (3,), np.float64)):
        a = arrays[name]
        if a.shape != shape or a.dtype != dtype or not np.isfinite(a).all():
            raise ValueError('Invalid pose array: ' + name)
    if (arrays['raster_hw'] <= 0).any() or not np.all(arrays['raster_hw'] == arrays['raster_hw'][0]):
        raise ValueError('Invalid raster')
    offsets = arrays['rgb_offsets']
    raw = arrays['rgb_bytes']
    if (raw.ndim != 1 or raw.dtype != np.uint8 or offsets.shape != (n+1,)
            or offsets.dtype != np.int64 or offsets[0] != 0 or offsets[-1] != len(raw)
            or (np.diff(offsets) <= 0).any()):
        raise ValueError('Invalid RGB offsets')
    roi = arrays['coords_1024']
    if ((roi[:, :2] < 0).any() or (roi[:, 2:] > 1024).any() or (roi[:, 2:] <= roi[:, :2]).any()):
        raise ValueError('Invalid square-pad ROI')
    expected = {'cam_token_l23', 'local_pose_enc', 'global_pose_enc', 'coords_1024',
                'patch_pooled', 'grid_hw', 'ordinals', 'raster_hw', 'c2w', 'intrinsics',
                'world_up', 'rgb_bytes', 'rgb_offsets'}
    if record['full_tokens']:
        expected.add('patch_full')
        full = arrays['patch_full']
        if (full.shape != (n, 37, 37, WIDTH) or full.dtype != np.uint16
                or any(((frame & 0x7f80) == 0x7f80).any() for frame in full)):
            raise ValueError('Invalid bf16 full tokens')
    if set(arrays) != expected:
        raise ValueError('Recording array keys changed')


def write_shard(path, items, binding, execution=None):
    """Store multiple recordings in append order and publish the index last."""
    entries = []
    def write(stream):
        stream.write(MAGIC)
        seen = set()
        for record, arrays in items:
            validate_arrays(arrays, record)
            key = record['recording_fingerprint']
            if key in seen:
                raise ValueError('Duplicate recording in shard')
            seen.add(key)
            offset, cursor, descriptors = stream.tell(), 0, {}
            for name in sorted(arrays):
                array = np.ascontiguousarray(arrays[name], dtype=arrays[name].dtype.newbyteorder('<'))
                arrays[name] = array
                raw = memoryview(array).cast('B')
                descriptors[name] = {'offset': cursor, 'nbytes': len(raw), 'dtype': array.dtype.str,
                                     'shape': list(array.shape), 'sha256': clips.sha256(raw)}
                if name == 'patch_full':
                    descriptors[name]['logical_dtype'] = 'bfloat16'
                cursor += len(raw)
            header = {'recording_fingerprint': key, 'record_sha256': clips.sha256(clips.canonical(record)),
                      'arrays': descriptors, 'payload_bytes': cursor}
            raw_header = clips.canonical(header)
            stream.write(struct.pack('<Q', len(raw_header)))
            stream.write(raw_header)
            payload_offset = stream.tell()
            for name in sorted(arrays):
                stream.write(memoryview(arrays[name]).cast('B'))
            entries.append({'recording_fingerprint': key, 'capacity': record['capacity'], 'offset': offset,
                            'length': stream.tell() - offset, 'payload_offset': payload_offset,
                            'header_sha256': clips.sha256(raw_header), 'record_sha256': header['record_sha256']})
    clips.atomic(path, write)
    if not entries:
        raise ValueError('Empty shard retained')
    index = {'schema': 'c1r-dense-shard-v2', 'blob': clips.pin(path), 'binding': binding,
             'records': entries, 'execution': dict(execution or {})}
    clips.write_json(Path(path).with_suffix('.json'), index)
    return index


def _signature(path):
    p = Path(path).resolve()
    s = p.stat()
    return str(p), s.st_size, s.st_mtime_ns, s.st_ctime_ns


def verify_blob(pin):
    """Hash each immutable shard once per process; rehash after any stat change."""
    signature = _signature(pin['path'])
    if _VERIFIED.get(signature) != pin['sha256']:
        if clips.recording.file_sha(pin['path']) != pin['sha256']:
            raise ValueError('Shard SHA-256 mismatch')
        _VERIFIED[signature] = pin['sha256']
    return signature


def read_record(index, record, binding):
    """Authenticate offsets and all array hashes before returning read-only maps."""
    if index.get('schema') != 'c1r-dense-shard-v2' or index['binding'] != binding:
        raise ValueError('Shard binding mismatch')
    blob = index['blob']
    signature = verify_blob(blob)
    digest = clips.sha256(clips.canonical(record))
    cache_key = (signature, digest, clips.sha256(clips.canonical(index)))
    if cache_key in _LOADED:
        return _LOADED[cache_key]
    expected_offset, found, seen = len(MAGIC), None, set()
    size = Path(blob['path']).stat().st_size
    for entry in index['records']:
        key = entry['recording_fingerprint']
        if (key in seen or entry['offset'] != expected_offset or entry['length'] < 8
                or entry['payload_offset'] <= entry['offset'] + 8):
            raise ValueError('Invalid recording index offsets')
        expected_offset += entry['length']
        seen.add(key)
        if key == record['recording_fingerprint']:
            found = entry
    if expected_offset != size or found is None:
        raise ValueError('Shard index extent mismatch')
    with open(blob['path'], 'rb') as stream:
        if stream.read(len(MAGIC)) != MAGIC:
            raise ValueError('Shard magic mismatch')
        stream.seek(found['offset'])
        length = struct.unpack('<Q', stream.read(8))[0]
        if length > 1024 * 1024 or found['offset'] + 8 + length != found['payload_offset']:
            raise ValueError('Invalid recording header length')
        raw = stream.read(length)
    header = json.loads(raw)
    if (clips.sha256(raw) != found['header_sha256'] or header['record_sha256'] != digest
            or found['record_sha256'] != digest or header['recording_fingerprint'] != record['recording_fingerprint']
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
        if clips.sha256(memoryview(array).cast('B')) != spec['sha256']:
            raise ValueError('Array SHA-256 mismatch')
        arrays[name] = array
        cursor += spec['nbytes']
    if cursor != header['payload_bytes']:
        raise ValueError('Array payload extent mismatch')
    validate_arrays(arrays, record)
    if len(_LOADED) >= 8:
        _LOADED.pop(next(iter(_LOADED)))
    _LOADED[cache_key] = arrays
    return arrays


def target_for_row(arrays, variant, record):
    if (len(variant['anchor_dense_indices']) != 32 or variant['anchor_dense_indices'][0] != 0
            or variant['target_ordinals'] != [record['ordinals'][j] for j in variant['anchor_dense_indices']]):
        raise ValueError('Target origin or exact ordinal mismatch')
    source = {'frame_numbers': record['ordinals'], 'pose_count': record['n'],
              'total_num_frames': record['ordinals'][-1] + 1}
    return encode_target(arrays, variant['target_ordinals'], source)


def _part_paths(root, shard):
    return sorted(root.glob(shard['id'] + '[0-9a-f][0-9a-f][0-9a-f][0-9a-f].json'))


def runtime_identity():
    modules = (clips, c1r_ref, clips.recording, clips.pose_samples,
               importlib.import_module(encode_target.__module__),
               importlib.import_module('.camera_targets', __package__))
    paths = [m.__file__ for m in modules] + [__file__]
    signatures = tuple(_signature(path) for path in paths)
    if signatures not in _RUNTIME:
        _RUNTIME.clear()
        _RUNTIME[signatures] = {Path(path).name: clips.recording.file_sha(path) for path in paths}
    return dict(_RUNTIME[signatures])


def load_clip(row, cache_root):
    """Return RGB slots, native 32-camera targets, anchor tokens and fused patches."""
    root = Path(cache_root).resolve()
    binding = json.loads((root / 'a0.json').read_bytes())
    if binding['runtime'] != runtime_identity():
        raise ValueError('Loader runtime binding mismatch')
    pin = binding['dense_plan']
    signature = (_signature(pin['path']), pin['sha256'])
    if signature not in _PLANS:
        _PLANS.clear()
        _PLANS[signature] = json.loads(clips.read_pin(pin))
    plan = _PLANS[signature]
    if row['dense_plan_sha256'] != binding['dense_plan']['sha256']:
        raise ValueError('Clip plan binding mismatch')
    if not 0 <= row['i'] < len(plan['schedule']):
        raise ValueError('Clip row outside plan')
    check_clips(plan, [row])
    position = plan['schedule'][row['i']]
    record_set = plan['records'][position]
    shard = next(s for s in plan['shards'] if position in s['recordings'])
    found = None
    for path in _part_paths(root, shard):
        index = json.loads(path.read_bytes())
        for entry in index['records']:
            if entry['recording_fingerprint'] == row['recording_fingerprint']:
                if found is not None:
                    raise ValueError('Duplicate cached recording')
                found = index, entry
    if found is None:
        raise FileNotFoundError('Recording is not ready')
    index, entry = found
    record = record_set['variants'][str(entry['capacity'])]
    # Resolve by the containing cache directory, allowing intact cache relocation.
    index['blob']['path'] = str(root / Path(index['blob']['path']).name)
    arrays = read_record(index, record, binding)
    variant = row['variants'][str(record['capacity'])]
    from PIL import Image
    images = {}
    for j in set(variant['slot_dense_indices']):
        start, end = arrays['rgb_offsets'][j:j+2]
        with Image.open(io.BytesIO(arrays['rgb_bytes'][start:end].tobytes())) as image:
            value = np.asarray(image.convert('RGB')).copy()
        if list(value.shape[:2]) != arrays['raster_hw'][j].tolist():
            raise ValueError('Cached RGB raster mismatch')
        images[j] = value
    slots = [images[j] for j in variant['slot_dense_indices']]
    selected = arrays['patch_pooled'][variant['slot_dense_indices']].astype(np.float32)
    temporal = len(slots) // 2
    pooled = selected.reshape(temporal, 2, *selected.shape[1:]).mean(1).astype(np.float16)
    target = target_for_row(arrays, variant, record)
    tokens = arrays['cam_token_l23'][variant['anchor_dense_indices']].copy()
    return slots, target, tokens, pooled

def assignments(plan, chunk, chunks, worker, workers):
    if (any(type(v) is not int for v in (chunk, chunks, worker, workers))
            or not 0 <= chunk < chunks or not 0 <= worker < workers):
        raise ValueError('Invalid chunk or worker')
    shards = plan['shards']
    shards = shards[len(shards)*chunk//chunks:len(shards)*(chunk+1)//chunks]
    return shards[len(shards)*worker//workers:len(shards)*(worker+1)//workers]


def worker_lock(root, chunk, chunks, worker, workers):
    """Hold one persistent lock inode; closing releases ownership without removal."""
    path = Path(root) / (f'fe{chunk:08x}{chunks:08x}{worker:08x}{workers:08x}.lck')
    handle = path.open('a+b')
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BaseException:
        handle.close()
        raise
    return handle


def materialize(dense_plan, out, ref_source, ref_weights, processor_dir, *, chunk=0, chunks=1,
                worker=0, workers=1, deadline_seconds=3500, a1_plan=None, source_tar=None,
                teacher_factory=None, decoder=None, grid_factory=None, identity_factory=None,
                pose_loader=None, clock=time.monotonic):
    """Run once per recording; publish deadline prefixes without repeating inference."""
    started = clock()
    if not math.isfinite(deadline_seconds) or deadline_seconds < 0:
        raise ValueError('Invalid deadline')
    plan_pin = dense_plan if isinstance(dense_plan, dict) else clips.pin(dense_plan)
    plan = json.loads(clips.read_pin(plan_pin))
    a1 = a1_plan or plan['a1_plan']
    if a1['sha256'] != plan['a1_plan']['sha256']:
        raise ValueError('A1 content binding mismatch')
    sources = clips.load_a1(a1)
    validate_plan(plan, sources)
    assigned = assignments(plan, chunk, chunks, worker, workers)
    root = Path(out).resolve()
    root.mkdir(parents=True, exist_ok=True)
    # Configure the allocator before loading the CUDA teacher or creating tensors.
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
    if identity_factory is None:
        identity = {'teacher': clips.teacher_identity(ref_source, ref_weights, source_tar),
                    'processor': clips.processor_identity(processor_dir)}
    else:
        identity = identity_factory()
    runtime = runtime_identity()
    binding = {'schema': 'c1r-dense-cache-v2', 'dense_plan': plan_pin, 'runtime': runtime, **identity}
    binding_path = root / 'a0.json'
    if binding_path.exists():
        if json.loads(binding_path.read_bytes()) != binding:
            raise ValueError('Output binding mismatch')
    else:
        try:
            clips.write_json(binding_path, binding)
        except FileExistsError:
            if json.loads(binding_path.read_bytes()) != binding:
                raise ValueError('Concurrent output binding mismatch')
    report = {'schema': 'c1r-dense-worker-v2', 'binding': binding, 'chunk': chunk, 'chunks': chunks,
              'worker': worker, 'workers': workers, 'shards': [], 'runs': [], 'complete': False,
              'stopped_for_deadline': False, 'failures': []}
    state = {'capacity': 224, 'first_memory': None, 'chunk': chunk, 'chunks': chunks,
             'worker': worker, 'workers': workers}
    teacher, processor, last_seconds, cache = None, None, 0., {}
    lock = worker_lock(root, chunk, chunks, worker, workers)
    def expired():
        return clock() - started + max(2., last_seconds) >= deadline_seconds
    try:
        for shard in assigned:
            completed = []
            for path in _part_paths(root, shard):
                index = json.loads(path.read_bytes())
                execution = index['execution']
                if any(execution.get(k) != state[k] for k in ('chunk', 'chunks', 'worker', 'workers')):
                    raise ValueError('Worker ownership changed')
                for entry in index['records']:
                    position = shard['recordings'][len(completed)]
                    record = plan['records'][position]['variants'][str(entry['capacity'])]
                    if record['recording_fingerprint'] != entry['recording_fingerprint']:
                        raise ValueError('Existing shard consumption order changed')
                    index['blob']['path'] = str(root / Path(index['blob']['path']).name)
                    read_record(index, record, binding)
                    completed.append(position)
                state.update(execution)
                report['shards'].append(clips.pin(path))
            if len(completed) == len(shard['recordings']):
                continue
            if expired():
                report['stopped_for_deadline'] = True
                break
            path = root / (shard['id'] + f'{len(completed):04x}.bin')
            if path.exists() or list(root.glob(path.name + '.*.part')):
                raise ValueError('Incomplete inference output retained; operator action required')
            def items():
                nonlocal teacher, processor, last_seconds
                for offset, position in enumerate(shard['recordings'][len(completed):]):
                    if offset and expired():
                        report['stopped_for_deadline'] = True
                        break
                    t = clock()
                    record = plan['records'][position]['variants'][str(state['capacity'])]
                    source = sources[position]
                    decoded = (decoder or clips.decode_selected)(source, record['ordinals'])
                    if (decoded['decoded_frame_count'] != source['total_num_frames']
                            or set(decoded['frames']) != set(record['ordinals'])):
                        raise ValueError('Decoded ordinal or frame count mismatch')
                    frames = decoded['frames']
                    payloads, raster = [], None
                    from PIL import Image
                    for ordinal in record['ordinals']:
                        frame = frames[ordinal]
                        if frame.ndim != 3 or frame.shape[2] != 3 or frame.dtype != np.uint8:
                            raise ValueError('Invalid RGB frame')
                        shape = list(frame.shape[:2])
                        if raster is not None and raster != shape:
                            raise ValueError('Recording raster changed')
                        raster = shape
                        stream = io.BytesIO()
                        Image.fromarray(frame).save(stream, format='JPEG', quality=95)
                        payloads.append(stream.getvalue())
                    del frames, decoded
                    poses = pose_loader(source) if pose_loader else clips.recording.load_poses(source, cache)
                    arrays = pose_arrays(poses, source, record, raster)
                    del poses
                    if grid_factory:
                        grid_hw = grid_factory(source, payloads[0])
                    else:
                        if processor is None:
                            from .decoupled_v_run import processor_for
                            processor = processor_for(processor_dir)
                        ordinal = record['ordinals'][0]
                        grid = clips.processor_grid(processor, dict(total_num_frames=source['total_num_frames'],
                            fps=source['fps'], slots=[ordinal, ordinal], slot_map=[0, 0]), [payloads[0]])
                        if grid[0] != 1 or grid[1] % 2 or grid[2] % 2:
                            raise ValueError('Processor grid changed')
                        grid_hw = [int(grid[1]) // 2, int(grid[2]) // 2]
                    if teacher is None:
                        teacher = (teacher_factory or DenseTeacher)(ref_source, ref_weights, 'cuda')
                    arrays.update(teacher.extract([io.BytesIO(raw) for raw in payloads], grid_hw=grid_hw,
                                                  full_tokens=record['full_tokens']))
                    arrays.update(jpeg_arrays(payloads))
                    arrays.update(ordinals=np.asarray(record['ordinals'], np.int64),
                                  grid_hw=np.asarray(grid_hw, np.int64))
                    if state['first_memory'] is None:
                        memory = getattr(teacher, 'peak_memory', None)
                        if (not isinstance(memory, dict) or set(memory) != {'allocated_bytes', 'reserved_bytes'}
                                or any(type(v) is not int or v < 0 for v in memory.values())):
                            raise ValueError('First run memory receipt missing')
                        state['first_memory'] = dict(memory)
                        if max(memory.values()) > LIMIT_BYTES:
                            state['capacity'] = 208
                    last_seconds = clock() - t
                    report['runs'].append({'recording_fingerprint': record['recording_fingerprint'],
                                           'n': record['n'], 'capacity': record['capacity'], 'seconds': last_seconds})
                    yield record, arrays
            index = write_shard(path, items(), binding, state)
            report['shards'].append(clips.pin(path.with_suffix('.json')))
            if report['stopped_for_deadline']:
                break
        else:
            report['complete'] = True
    except Exception as error:
        report['failures'].append({'kind': type(error).__name__,
                                  'detail_sha256': clips.sha256(str(error).encode())})
    finally:
        clips.close_pose_cache(cache)
        lock.close()
    report['first_memory'] = state['first_memory']
    report['next_capacity'] = state['capacity']
    report['seconds'] = clock() - started
    import uuid
    destination = root / (uuid.uuid4().hex + '.json')
    clips.write_json(destination, report)
    return report, clips.pin(destination)


def teacher_flops(n):
    """Analytical FLOPs; these estimates are not measured run times."""
    c, p, image_p = 1024, 1374, 1369
    block = lambda tokens: 24 * tokens * c*c + 4 * tokens*tokens*c
    return 24 * (n * block(image_p) + n * block(p) + block(n*p))


def estimates(plan, capacity=224, pooled_cells=144, jpeg_bytes=250_000, sustained_tflops=100.):
    if capacity not in CAPACITIES or min(pooled_cells, jpeg_bytes, sustained_tflops) <= 0:
        raise ValueError('Invalid estimation assumptions')
    records = [r['variants'][str(capacity)] for r in plan['records']]
    frames = sum(r['n'] for r in records)
    pooled = frames * pooled_cells * WIDTH * 2
    rgb = frames * jpeg_bytes
    base = frames * (WIDTH * 2 + 15 * 4 + 25 * 8 + 2 * 8 + 2 * 8)
    full = sum(r['n'] * PATCHES * WIDTH * 2 for r in records if r['full_tokens'])
    return {'capacity': capacity, 'runs': len(records), 'frames': frames,
            'anchor_counts': dict(Counter(len(r['anchors']) for r in records)),
            'short_recordings': sum(bool(r['shortfall']) for r in records),
            'frame_shortfall': sum(r['shortfall'] for r in records),
            'partner_collision_resolutions': sum(r['partner_collision_resolutions'] for r in records),
            'pooled_tb': pooled / 1e12, 'rgb_tb': rgb / 1e12, 'base_tb': base / 1e12,
            'full_all_tb': frames * PATCHES * WIDTH * 2 / 1e12,
            'full_kept_tb': full / 1e12, 'full_recordings': sum(r['full_tokens'] for r in records),
            'total_kept_tb': (pooled + rgb + base + full) / 1e12,
            'shards': len(plan['shards']), 'data_and_index_files': len(plan['shards']) * 2,
            'base_files_with_plans_and_binding': len(plan['shards']) * 2 + 7,
            'files_with_one_worker_receipt_and_lock': len(plan['shards']) * 2 + 9,
            'gpu_hours_compute_only': sum(teacher_flops(r['n']) for r in records) / (sustained_tflops * 1e12 * 3600),
            'sustained_tflops_assumed': sustained_tflops, 'pooled_cells_assumed': pooled_cells,
            'jpeg_bytes_assumed': jpeg_bytes}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('--a1-plan', required=True)
    p.add_argument('--a1-plan-sha256', required=True)
    p.add_argument('--a1-runtime-path')
    p.add_argument('--out', required=True)
    p.add_argument('--steps', type=int, default=800)
    p.add_argument('--full-budget', type=int, default=10**12)
    p.add_argument('--recordings-per-shard', type=int, default=8)
    p = sub.add_parser('check')
    p.add_argument('--dense-plan', required=True)
    p.add_argument('--clip-plan', required=True)
    p = sub.add_parser('materialize')
    for name in ('dense-plan', 'out', 'ref-source', 'ref-weights', 'processor'):
        p.add_argument('--' + name, required=True)
    p.add_argument('--dense-plan-sha256')
    p.add_argument('--a1-plan')
    p.add_argument('--ref-archive')
    for name, default in (('chunk', 0), ('chunks', 1), ('worker', 0), ('workers', 1)):
        p.add_argument('--' + name, type=int, default=default)
    p.add_argument('--deadline-seconds', type=float, default=3500)
    args = parser.parse_args(argv)
    if args.command == 'prepare':
        a1 = {'path': str(Path(args.a1_plan).resolve()), 'sha256': args.a1_plan_sha256}
        sources = clips.load_a1(a1)
        if args.a1_runtime_path:
            a1['path'] = args.a1_runtime_path
        plan = build_plan(sources, a1, steps=args.steps, full_budget=args.full_budget,
                          recordings_per_shard=args.recordings_per_shard)
        result = write_plans(plan, args.out)
        result['estimates'] = [estimates(plan, n) for n in CAPACITIES]
        print(json.dumps(result, sort_keys=True))
        return 0
    plan_pin = clips.pin(args.dense_plan)
    if args.command == 'check':
        plan = json.loads(clips.read_pin(plan_pin))
        with open(args.clip_plan) as stream:
            rows = (json.loads(line) for line in stream)
            def pinned_rows():
                layout = None
                for i, row in enumerate(rows):
                    if layout is None:
                        layout = row['layout']
                    if row['layout'] != layout:
                        raise ValueError('Clip file layout mismatch')
                    if row['i'] != i:
                        raise ValueError('Clip file row order mismatch')
                    if row['dense_plan_sha256'] != plan_pin['sha256']:
                        raise ValueError('Clip file plan hash mismatch')
                    yield row
            result = check_clips(plan, pinned_rows())
        if result['rows'] != len(plan['schedule']):
            raise ValueError('Clip file row count mismatch')
        print(json.dumps(result, sort_keys=True))
        return 0
    if args.dense_plan_sha256 and args.dense_plan_sha256 != plan_pin['sha256']:
        raise ValueError('Dense plan SHA-256 mismatch')
    a1 = None
    if args.a1_plan:
        a1 = clips.pin(args.a1_plan)
    report, receipt = materialize(plan_pin, args.out, args.ref_source, args.ref_weights, args.processor,
        chunk=args.chunk, chunks=args.chunks, worker=args.worker, workers=args.workers,
        deadline_seconds=args.deadline_seconds, a1_plan=a1, source_tar=args.ref_archive)
    print(json.dumps({'receipt': receipt, 'complete': report['complete']}, sort_keys=True))
    return 0 if report['complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
