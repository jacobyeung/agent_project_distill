"""CPU preparation of pooled, full-recording pose-only rows.

Sampling uses integer raw frame numbers. A bounded pool conditions Table 14's
interval distribution on available paths; it never rounds a requested interval
to the nearest pooled frame. The audit records this restriction explicitly.
The trainer continues to use pose_samples' schema, targets and augmentation.
"""
import argparse
from bisect import bisect_left, bisect_right
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import hashlib
import io
from itertools import repeat
import json
import math
import multiprocessing
from pathlib import Path
import random
import re
import subprocess
import tarfile

import numpy as np

from . import pose_samples


PROBABILITIES = {'d1': (0.6, 0.6), 'd2': (0.8, 0.5), 'd3': (0.8, 0.5)}
NATIVE = {'d1': 'scannet', 'd2': 'scannetppv2', 'd3': 'arkitscenes'}
ALIASES = {**{v: k for k, v in NATIVE.items()}, 'scannetpp': 'd2', 'scannet++': 'd2',
           'scannetv2': 'd1', **{k: k for k in NATIVE}}
COORDINATES = 'source_world_meters_opencv_camera_to_world'
CONDITIONING = 'Table 14 mode probabilities; starts and intervals conditioned on exact feasible pool paths'
WINDOW_CONDITIONING = 'raw-frame windows; fps/30-scaled stride; random starts conditioned on the staged dense pool'
RANDOM32_CONDITIONING = 'one sorted uniform 32-frame subset per scene and epoch, conditioned on the staged pool'
SPARSE_CONDITIONING = 'posed frames only; nearest posed target within 30-100 raw frames and feasible remaining pool paths'
VARIANTS = {'window64_stride3': (64, False), 'window96_stride3': (96, False),
            'window64_jitter': (64, True), 'window96_jitter': (96, True)}


def sampling_settings(request):
    """Explicit variants retain the legacy policy when absent. Epochs select new frozen manifests."""
    variant = request.get('variant', 'table14')
    if variant not in (*VARIANTS, 'table14', 'random32_per_epoch', 'all_frames32'):
        raise ValueError('Unknown recording sampling variant')
    return {'variant': variant, 'pool_size': integer(request.get('pool_size', 512 if variant in VARIANTS else 96),
                                                   'Pool size', 32),
            'epoch': integer(request.get('epoch', 0), 'Epoch')}


def window_gaps(fps, jitter):
    if type(fps) not in (float, int) or not math.isfinite(fps) or fps <= 0:
        raise ValueError('Window sampling requires positive finite fps')
    stride = max(1, round(3 * fps / 30))
    return tuple(sorted({max(1, stride + delta) for delta in ((-1, 0, 1) if jitter else (0,))}))


def conditioning_for(sampling):
    variant = sampling['variant']
    if variant == 'all_frames32':
        return 'fresh sorted uniform 32 posed frames per row, conditioned on the staged pool; all 32 targets'
    return (CONDITIONING if variant == 'table14' else RANDOM32_CONDITIONING
            if variant == 'random32_per_epoch' else WINDOW_CONDITIONING)


class WindowSampler:
    """Draw exact raw-frame windows within a dense staged pool, without nearest-frame substitutions."""
    def __init__(self, pool, count, fps, jitter=False):
        self.pool = frame_numbers(pool)
        self.count, self.gaps = count, window_gaps(fps, jitter)
        if count not in (64, 96) or self.pool != list(range(self.pool[0], self.pool[-1] + 1)):
            raise ValueError('Windows require 64 or 96 frames and a dense raw-frame pool')
        if len(self.pool) < 1 + (count - 1) * max(self.gaps):
            raise ValueError('Pool is too small for the requested window and fps-scaled stride')
        self.jitter = jitter

    def draw(self, rng, dataset):
        gaps = [rng.choice(self.gaps) for _ in range(self.count - 1)] if self.jitter else [self.gaps[0]] * (self.count - 1)
        start = rng.randint(self.pool[0], self.pool[-1] - sum(gaps))
        order = [start]
        for gap in gaps:
            order.append(order[-1] + gap)
        return 'video', 'jitter' if self.jitter else 'fixed', order


class AllFrameSampler:
    def __init__(self, pool):
        self.pool = frame_numbers(pool)
        if len(self.pool) < 32:
            raise ValueError('All-frame sampling needs at least 32 posed frames')

    def draw(self, rng, dataset):
        return 'collection', None, sorted(rng.sample(self.pool, 32))


class Random32Sampler:
    """One fresh sorted 32-frame subset per scene and epoch; row augmentation remains independent."""
    def __init__(self, pool, seed, scene, epoch):
        self.pool = frame_numbers(pool)
        self.order = sorted(random.Random(f'{seed}:{scene}:epoch:{epoch}').sample(self.pool, 32))

    def draw(self, rng, dataset):
        return 'collection', None, list(self.order)


def sampler_for(source, sampling, seed):
    variant = sampling['variant']
    if variant == 'all_frames32':
        return AllFrameSampler(source['pool'])
    if sparse_frames(source) is not None:
        if variant != 'table14':
            raise ValueError('Sparse poses currently require table14 sampling')
        return SparsePoolSampler(source['pool'], source['sample_sizes'])
    if variant in VARIANTS:
        count, jitter = VARIANTS[variant]
        return WindowSampler(source['pool'], count, source['fps'], jitter)
    if variant == 'random32_per_epoch':
        return Random32Sampler(source['pool'], seed, source['dataset'] + '/' + source['scene'], sampling['epoch'])
    return PoolSampler(source['pool'], source['sample_sizes'])


def payload(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def pin(path):
    return {'path': str(Path(path).resolve()), 'sha256': file_sha(path)}


def read_pin(value):
    if not isinstance(value, dict) or set(value) != {'path', 'sha256'}:
        raise ValueError('Expected a path and SHA-256 pin')
    raw = Path(value['path']).read_bytes()
    if digest(raw) != value['sha256']:
        raise ValueError('Source SHA-256 mismatch: ' + value['path'])
    return raw


def write_new(path, data):
    with Path(path).open('xb') as stream:
        stream.write(data)


def store_png(path, raw, sha):
    """Publish complete bytes atomically; retain temporary hardlinks without deletion."""
    import os
    import uuid
    path = Path(path)
    if not path.exists():
        temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.part')
        write_new(temporary, raw)
        try:
            os.link(temporary, path)
        except FileExistsError:
            pass
    if file_sha(path) != sha:
        raise ValueError('Content-addressed frame is corrupt')


def integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(name + ' must be an integer >= ' + str(minimum))
    return value


def frame_numbers(values):
    values = list(values)
    if not values or any(type(v) is not int or v < 0 for v in values) or values != sorted(set(values)):
        raise ValueError('Frame numbers must be distinct increasing nonnegative integers')
    return values


def sparse_frames(source):
    """An explicit per-recording opt-in carries the posed raw ordinals."""
    flag = source.get('sparse_poses', False)
    if type(flag) is not bool:
        raise ValueError('sparse_poses must be a boolean')
    if not flag:
        return None
    numbers = frame_numbers(source['frame_numbers'])
    if (len(numbers) != source['pose_count'] or numbers[-1] >= source['total_num_frames']
            or source['pose_count'] > source['total_num_frames']):
        raise ValueError('Sparse pose ordinals disagree with recording counts')
    return numbers


def identity(dataset, scene):
    dataset = ALIASES[dataset.lower()]
    if not isinstance(scene, str) or not scene:
        raise ValueError('Scene must be a nonempty string')
    return dataset, scene


def token(dataset, scene):
    return 'v' + digest(('rung1 scene ' + NATIVE[dataset] + '/' + scene).encode())[:12]


def scene_keys(dataset, scene):
    """Native and rung-1 aliases, including ScanNet repeat-scan closure."""
    dataset, scene = identity(dataset, scene)
    keys = {(dataset, scene), (dataset, token(dataset, scene))}
    if dataset == 'd1' and re.fullmatch(r'scene\d{4}_\d{2}', scene):
        keys.add((dataset, scene[:9]))
    return keys


def exclusion_keys(dataset, scene):
    keys = scene_keys(dataset, scene)
    if dataset == 'd1' and re.fullmatch(r'scene\d{4}_\d{2}', scene):
        # The gate authority contains opaque tokens. Match every repeat-scan
        # suffix so a gate token cannot leak through a different recording.
        keys.update((dataset, token(dataset, scene[:10] + f'{suffix:02d}')) for suffix in range(100))
    return keys


def listed_scenes(value):
    """Explicit JSON scene lists or native dataset/scene identities."""
    if not isinstance(value, list):
        raise ValueError('Scene authority must contain a list')
    keys = set()
    for item in value:
        if isinstance(item, str):
            dataset, separator, scene = item.partition('/')
            if not separator:
                raise ValueError('Scene authority requires dataset/scene identities')
        elif isinstance(item, list) and len(item) == 2:
            dataset, scene = item
        else:
            raise ValueError('Invalid scene authority entry')
        keys.update(scene_keys(dataset, scene))
    return keys


def load_authorities(spec):
    """All authorities are mandatory, pinned and read before any sampling.

    admission_policy is the repo's auxiliary_targets allowed_groups/excluded_groups
    policy. Additional authorities must appear in its required_exclusion_lists,
    and must be supplied through extra_benchmarks with matching pins.
    """
    required = {'gate', 'vsi288', 'vsti', 'division', 'admission_policy', 'extra_benchmarks'}
    if set(spec) != required or not isinstance(spec['extra_benchmarks'], list):
        raise ValueError('Missing exclusion authority')
    records = {key: json.loads(read_pin(spec[key])) for key in ('gate', 'vsti', 'division', 'admission_policy')}
    gate = records['gate']
    if gate.get('schema') != 'gate_heldout_scenes_v1' or len(gate['scenes']) != 38:
        raise ValueError('Expected the 38-scene gate authority')
    if len({tuple(s) for s in gate['scenes']}) != 38:
        raise ValueError('Duplicate gate scene')
    vsi = []
    for line in read_pin(spec['vsi288']).decode().splitlines():
        fields = line.split('\t')
        if len(fields) != 2:
            raise ValueError('VSI scene authority must be a two-column TSV')
        vsi.append(fields)
    if len(vsi) != 288 or len({tuple(s) for s in vsi}) != 288:
        raise ValueError('Expected exactly 288 distinct benchmark scenes')
    policy = records['admission_policy']
    extras = spec['extra_benchmarks']
    if policy.get('required_exclusion_lists', []) != extras:
        raise ValueError('Admission policy requires different additional scene authorities')
    blocked = {'gate': listed_scenes(gate['scenes']), 'vsi288': listed_scenes(vsi),
               'vsti': listed_scenes(records['vsti']['scenes']),
               'admission_policy': listed_scenes(policy['excluded_groups'])}
    if not blocked['vsti']:
        raise ValueError('VSTI authority is empty')
    for i, source in enumerate(extras):
        blocked[f'extra_{i}'] = listed_scenes(json.loads(read_pin(source))['scenes'])
    division = records['division']
    allowed = listed_scenes(division['train_scenes']) & listed_scenes(policy['allowed_groups'])
    heldout = listed_scenes(division.get('heldout_scenes', []))
    heldout |= listed_scenes(division.get('heldout_group_ids', []))
    blocked['division_heldout'] = heldout
    if not allowed:
        raise ValueError('Frozen training division and admission policy have no common scenes')
    return allowed, blocked


class PoolSampler:
    """Precompute feasible fixed runs and variable-interval reachability once per pool."""
    def __init__(self, pool, sizes=pose_samples.SAMPLE_SIZES):
        self.pool = frame_numbers(pool)
        self.sizes = tuple(sizes)
        if not self.sizes or any(n not in pose_samples.SAMPLE_SIZES for n in self.sizes):
            raise ValueError('Unsupported sample sizes')
        available = set(pool)
        self.fixed = {}
        for n in pose_samples.SAMPLE_SIZES:
            self.fixed[n] = {gap: [f for f in pool if all(f + k * gap in available for k in range(n))]
                             for gap in range(30, 101)}
            self.fixed[n] = {gap: starts for gap, starts in self.fixed[n].items() if starts}
        self.next = {f: [g for g in pool if 30 <= g - f <= 100] for f in pool}
        self.reach = {1: set(pool)}
        for n in range(2, 33):
            self.reach[n] = {f for f in pool if any(g in self.reach[n - 1] for g in self.next[f])}

    def ready(self):
        return all(self.fixed[n] and self.reach[n] for n in self.sizes)

    def draw(self, rng, dataset):
        n = rng.choice(self.sizes)
        p_video, p_fix = PROBABILITIES[dataset]
        if rng.random() >= p_video:
            return 'collection', None, rng.sample(self.pool, n)
        fixed = rng.random() < p_fix
        if fixed:
            if not self.fixed[n]:
                raise ValueError('No exact fixed-interval pool path for N=' + str(n))
            gap = rng.choice(list(self.fixed[n]))
            start = rng.choice(self.fixed[n][gap])
            return 'video', 'fixed', [start + k * gap for k in range(n)]
        if not self.reach[n]:
            raise ValueError('No variable-interval pool path for N=' + str(n))
        order = [rng.choice(sorted(self.reach[n]))]
        for remaining in range(n - 1, 0, -1):
            order.append(rng.choice([f for f in self.next[order[-1]] if f in self.reach[remaining]]))
        return 'video', 'variable', order


class SparsePoolSampler:
    """Choose nearest posed targets while retaining raw gap bounds and reachability."""
    def __init__(self, pool, sizes=None):
        self.pool = frame_numbers(pool)
        self.next = {f: self.pool[bisect_left(self.pool, f + 30):bisect_right(self.pool, f + 100)]
                     for f in self.pool}
        self.depth = {}
        for f in reversed(self.pool):
            self.depth[f] = 1 + max((self.depth[g] for g in self.next[f]), default=0)
        self.feasible_sizes = tuple(n for n in pose_samples.SAMPLE_SIZES if max(self.depth.values()) >= n)
        self.sizes = self.feasible_sizes if sizes is None else tuple(sizes)
        if not self.sizes or any(n not in self.feasible_sizes for n in self.sizes):
            raise ValueError('Sparse posed frames cannot support the requested video sizes')

    def ready(self):
        return all(n in self.feasible_sizes for n in self.sizes)

    def video(self, rng, n, fixed):
        start = rng.choice([f for f in self.pool if self.depth[f] >= n])
        gap = rng.randint(30, min(100, (self.pool[-1] - start) // (n - 1))) if fixed else None
        order, targets = [start], [start]
        for step in range(1, n):
            target = start + step * gap if fixed else order[-1] + rng.randint(30, 100)
            candidates = [f for f in self.next[order[-1]] if self.depth[f] >= n - step]
            order.append(min(candidates, key=lambda f: (abs(f - target), f)))
            targets.append(target)
        self.target_frame_numbers = targets
        return order

    def draw(self, rng, dataset):
        n = rng.choice(self.sizes)
        p_video, p_fix = PROBABILITIES[dataset]
        if rng.random() >= p_video:
            self.target_frame_numbers = None
            return 'collection', None, rng.sample(self.pool, n)
        fixed = rng.random() < p_fix
        return 'video', 'fixed' if fixed else 'variable', self.video(rng, n, fixed)


def make_sparse_pool(numbers, rng, pool_size):
    sampler = SparsePoolSampler(numbers)
    largest = max(sampler.sizes)
    chosen = set(sampler.video(rng, largest, True) + sampler.video(rng, largest, False))
    for k in range(16):
        chosen.add(numbers[min(len(numbers) - 1, k * len(numbers) // 16)])
    if len(chosen) > pool_size:
        raise ValueError('Pool size cannot hold the required sparse video scaffolds')
    remaining = sorted(set(numbers) - chosen)
    chosen.update(rng.sample(remaining, min(pool_size, len(numbers)) - len(chosen)))
    return sorted(chosen), list(sampler.sizes)


def sizes_for(count):
    return tuple(n for n in pose_samples.SAMPLE_SIZES if 1 + (n - 1) * 30 <= count)


def make_pool(count, rng, pool_size=96):
    """Up to 96 frames: two video scaffolds, then stratified and random coverage.

    The scaffolds support every N that fits the recording without substituting
    pool-index strides for raw-frame intervals.
    """
    count = integer(count, 'Recording frame count', 1)
    sizes = sizes_for(count)
    if not sizes:
        raise ValueError('Recording is too short for N=8 at a 30-frame minimum interval')
    largest = max(sizes)
    gap = rng.randint(30, min(100, (count - 1) // (largest - 1)))
    start = rng.randrange(count - (largest - 1) * gap)
    chosen = {start + gap * k for k in range(largest)}
    gaps, budget = [], count - 1
    for remaining in range(largest - 1, 0, -1):
        gap = rng.randint(30, min(100, budget - 30 * (remaining - 1)))
        gaps.append(gap)
        budget -= gap
    current = rng.randrange(count - sum(gaps))
    chosen.add(current)
    for gap in gaps:
        current += gap
        chosen.add(current)
    for k in range(16):
        chosen.add(rng.randrange(k * count // 16, (k + 1) * count // 16))
    if pool_size < len(chosen):
        raise ValueError('Pool size cannot hold the required Table 14 scaffolds')
    while len(chosen) < min(pool_size, count):
        chosen.add(rng.randrange(count))
    return sorted(chosen)


def make_plan(request):
    if request.get('schema') != 'recording-pose-request-v1':
        raise ValueError('Unknown recording request schema')
    allowed, blocked = load_authorities(request['authorities'])
    index = json.loads(read_pin(request['recordings']))
    seed = integer(request.get('seed', 17), 'Seed')
    samples = integer(request.get('rows_per_scene', 80), 'Rows per scene', 1)
    sampling = sampling_settings(request)
    explicit_sampling = any(key in request for key in ('variant', 'pool_size', 'epoch'))
    authorities = request['authorities']
    reason_sources = {name: [authorities[name]] for name in ('gate', 'vsi288', 'vsti', 'admission_policy')}
    reason_sources['division_heldout'] = [authorities['division']]
    reason_sources['outside_frozen_training_division'] = [authorities['division'], authorities['admission_policy']]
    reason_sources.update({f'extra_{i}': [source] for i, source in enumerate(authorities['extra_benchmarks'])})
    scenes, excluded, deferred, seen = [], [], [], set()
    for source in index['recordings']:
        dataset, native_scene = identity(source['dataset'], source['scene'])
        key = dataset, native_scene
        if key in seen:
            raise ValueError('Duplicate recording identity')
        seen.add(key)
        keys = scene_keys(*key)
        reasons = [name for name, values in blocked.items() if exclusion_keys(*key) & values]
        if not keys & allowed:
            reasons.append('outside_frozen_training_division')
        if reasons:
            excluded.append({'dataset': dataset, 'scene': native_scene, 'reasons': reasons,
                             'sources': {reason: reason_sources[reason] for reason in reasons}})
            continue
        # Source payloads are never opened for excluded recordings.
        count = integer(source['total_num_frames'], 'total_num_frames', 1)
        pose_count = integer(source['pose_count'], 'pose_count', 1)
        numbers = sparse_frames(source)
        if pose_count != count and numbers is None:
            deferred.append({'dataset': dataset, 'scene': native_scene, 'reason': 'sparse_pose_count',
                             'pose_count': pose_count, 'total_num_frames': count})
            continue
        try:
            rng = random.Random(f'{seed}:{dataset}:{native_scene}:pool')
            variant = sampling['variant']
            if variant == 'all_frames32':
                available = numbers if numbers is not None else range(count)
                pool = sorted(rng.sample(available, min(len(available), sampling['pool_size'])))
                AllFrameSampler(pool)
                sizes = [32]
            elif numbers is not None:
                if variant != 'table14':
                    raise ValueError('Sparse poses currently require table14 sampling')
                pool, sizes = make_sparse_pool(numbers, rng, sampling['pool_size'])
            elif variant in VARIANTS:
                size = min(count, sampling['pool_size'])
                start = rng.randrange(count - size + 1)
                pool = list(range(start, start + size))
                n, jitter = VARIANTS[variant]
                WindowSampler(pool, n, source['fps'], jitter)
                sizes = [n]
            elif variant == 'random32_per_epoch':
                pool = sorted(rng.sample(range(count), min(count, sampling['pool_size'])))
                if len(pool) < 32:
                    raise ValueError('Recording is too short for a random 32-frame subset')
                sizes = [32]
            else:
                pool = make_pool(count, rng, sampling['pool_size'])
                sizes = list(sizes_for(count))
        except ValueError as error:
            deferred.append({'dataset': dataset, 'scene': native_scene, 'reason': str(error)})
            continue
        if source['coordinate_frame'] != COORDINATES:
            raise ValueError('Unsupported pose coordinate convention')
        fps = source['fps']
        if isinstance(fps, bool) or not isinstance(fps, (float, int)) or not math.isfinite(fps) or fps <= 0:
            raise ValueError('Recording requires positive finite fps metadata')
        scenes.append({**source, 'dataset': dataset, 'scene': token(dataset, native_scene),
                       'native_scene': native_scene, 'pool': pool, 'sample_sizes': sizes})
    plan = {'schema': 'recording-pose-plan-v1', 'seed': seed, 'rows_per_scene': samples,
            'conditioning': CONDITIONING, 'authorities': request['authorities'],
            'recordings': request['recordings'], 'scenes': scenes, 'excluded': excluded, 'deferred': deferred,
            'probabilities': PROBABILITIES, 'sample_sizes': list(pose_samples.SAMPLE_SIZES)}
    if explicit_sampling:
        plan['sampling'] = sampling
        plan['conditioning'] = conditioning_for(sampling)
        if sampling['variant'] != 'table14':
            plan['probabilities'] = {}
        plan['sample_sizes'] = ([VARIANTS[sampling['variant']][0]] if sampling['variant'] in VARIANTS
                                else [32] if sampling['variant'] in ('random32_per_epoch', 'all_frames32') else list(pose_samples.SAMPLE_SIZES))
    return plan


def validate_plan(plan):
    """Recheck authority bytes and admission before decoding or drawing rows."""
    sampling = sampling_settings(plan.get('sampling', {}))
    conditioning = conditioning_for(sampling)
    if plan.get('schema') != 'recording-pose-plan-v1' or plan['conditioning'] != conditioning:
        raise ValueError('Unknown plan schema or sampling policy')
    allowed, blocked = load_authorities(plan['authorities'])
    seen = set()
    for source in plan['scenes']:
        dataset, native = identity(source['dataset'], source['native_scene'])
        keys = scene_keys(dataset, native)
        if not keys & allowed or any(exclusion_keys(dataset, native) & values for values in blocked.values()):
            raise ValueError('Plan includes an excluded scene')
        if source['scene'] != token(dataset, native) or (dataset, native) in seen:
            raise ValueError('Plan recording identity mismatch')
        seen.add((dataset, native))
        pool = frame_numbers(source['pool'])
        if len(pool) > sampling['pool_size'] or pool[-1] >= source['total_num_frames']:
            raise ValueError('Plan pool exceeds its recording or frame budget')
        numbers = sparse_frames(source)
        if numbers is not None and not set(pool) <= set(numbers):
            raise ValueError('Sparse pool includes an unposed raw frame')
        expected_sizes = ([32] if sampling['variant'] == 'all_frames32' else
                          list(SparsePoolSampler(numbers).sizes) if numbers is not None else
                          [VARIANTS[sampling['variant']][0]] if sampling['variant'] in VARIANTS
                          else [32] if sampling['variant'] in ('random32_per_epoch', 'all_frames32') else list(sizes_for(source['total_num_frames'])))
        sampler = sampler_for(source, sampling, plan['seed'])
        if (source['sample_sizes'] != expected_sizes
                or numbers is None and source['pose_count'] != source['total_num_frames']
                or isinstance(sampler, PoolSampler) and not sampler.ready()):
            raise ValueError('Plan cannot support every requested video branch and size')


def load_poses(source, cache):
    """Read a pinned NPZ or an explicitly indexed tar member, without extraction."""
    spec = source['poses']
    path = spec['path']
    if (path, spec['sha256']) not in cache:
        if file_sha(path) != spec['sha256']:
            raise ValueError('Pose source SHA-256 mismatch')
        cache[path, spec['sha256']] = True
    if 'member' in spec:
        if ('archive', path) not in cache:
            cache['archive', path] = tarfile.open(path, 'r:')
        archive = cache['archive', path]
        member = archive.getmember(spec['member'])
        if not member.isfile():
            raise ValueError('Pose member must be a regular file')
        raw = archive.extractfile(member).read()
        if digest(raw) != spec['member_sha256']:
            raise ValueError('Pose member SHA-256 mismatch')
        handle = io.BytesIO(raw)
    else:
        handle = path
    with np.load(handle, allow_pickle=False) as data:
        c2w = data['c2w'] if 'c2w' in data else data['camera_poses']
        indices = data['frame_numbers'] if 'frame_numbers' in data else data['indices']
        indices = frame_numbers(indices.tolist())
        count = source['pose_count']
        numbers = sparse_frames(source)
        if indices != (numbers if numbers is not None else list(range(source['total_num_frames']))) or len(c2w) != count:
            raise ValueError('Full poses must cover every raw frame exactly once')
        intrinsics = np.asarray(data['intrinsics'], dtype=np.float64)
        if intrinsics.shape == (3, 3):
            intrinsics = np.broadcast_to(intrinsics, (count, 3, 3))
        raster = data['raster_hw'].tolist()
        if len(raster) != 2 or any(type(v) is not int or v < 1 for v in raster):
            raise ValueError('Expected a positive integer RGB raster')
        up = np.asarray(data['world_up'] if 'world_up' in data else source['world_up'], dtype=np.float64)
        if up.shape != (3,) or not np.isfinite(up).all() or np.linalg.norm(up) < 1e-6:
            raise ValueError('World up must be a finite nonzero vector')
        if c2w.shape != (count, 4, 4) or intrinsics.shape != (count, 3, 3):
            raise ValueError('Pose or intrinsic array shape mismatch')
        result = {'c2w': c2w, 'intrinsics': intrinsics, 'raster_hw': raster, 'world_up': up}
        if numbers is not None:
            result['frame_numbers'] = numbers
        return result


def decode_pool(source, frame_root):
    """Count decoded frames, then materialize only selected RGB PNGs with ffmpeg.

    Codecs may decode dependency frames internally. No other RGB frames are saved.
    No frame rate conversion, resizing, or timestamp-based seeking is allowed.
    """
    from PIL import Image
    if sparse_frames(source) is not None:
        return decode_sparse_pool(source, frame_root)
    video = source['video']
    if file_sha(video['path']) != video['sha256']:
        raise ValueError('Video source SHA-256 mismatch')
    probe = subprocess.run(['ffprobe', '-v', 'error', '-threads', '1', '-select_streams', 'v:0', '-count_frames',
                            '-show_entries', 'stream=nb_read_frames', '-of', 'json', video['path']],
                           check=True, capture_output=True)
    count = int(json.loads(probe.stdout)['streams'][0]['nb_read_frames'])
    numbers = sparse_frames(source)
    if count != source['total_num_frames'] or numbers is None and count != source['pose_count']:
        raise ValueError('Decoded frame count does not equal full-recording pose count')
    selected = set(frame_numbers(source['pool']))
    if numbers is not None and not selected <= set(numbers):
        raise ValueError('Sparse pool includes an unposed raw frame')
    if max(selected) >= count:
        raise ValueError('Pool frame exceeds decoded recording')
    expression = '+'.join(f'eq(n\\,{n})' for n in sorted(selected))
    # A bounded image2pipe stream avoids buffering 96 full-size images at once.
    command = ['ffmpeg', '-v', 'error', '-nostdin', '-threads', '1', '-hwaccel', 'none', '-noautorotate',
               '-i', video['path'], '-map', '0:v:0', '-vf', 'select=' + expression, '-vsync', '0',
               '-f', 'image2pipe', '-pix_fmt', 'rgb24', '-vcodec', 'ppm', '-']
    frames = []
    with subprocess.Popen(command, stdout=subprocess.PIPE) as process:
        for number in sorted(selected):
            if process.stdout.readline() != b'P6\n':
                raise ValueError('Missing decoded pooled RGB frame')
            dimensions = process.stdout.readline().split()
            width, height = map(int, dimensions)
            if process.stdout.readline() != b'255\n':
                raise ValueError('Unsupported decoded RGB raster')
            length = width * height * 3
            rgb = process.stdout.read(length)
            if len(rgb) != length:
                raise ValueError('Incomplete decoded pooled RGB frame')
            image = Image.frombytes('RGB', (width, height), rgb)
            output = io.BytesIO()
            image.save(output, format='PNG')
            raw = output.getvalue()
            sha = digest(raw)
            path = Path(frame_root).resolve() / sha[:2] / (sha + '.png')
            path.parent.mkdir(parents=True, exist_ok=True)
            store_png(path, raw, sha)
            frames.append({'frame_number': number, 'path': str(path), 'sha256': sha,
                           'raster_hw': [height, width]})
        if process.stdout.read(1):
            raise ValueError('Decoder produced extra frames')
        if process.wait() != 0:
            raise ValueError('Frame decoder failed')
    return {'dataset': source['dataset'], 'scene': source['scene'], 'decoded_frame_count': count,
            'pose_count': source['pose_count'], 'video': source['video'], 'frames': frames}


def decode_sparse_pool(source, frame_root):
    """Retain the sparse-recording entry point for existing callers."""
    return decode_pyav_pool(source, frame_root)


def pyav_preflight():
    """Load the in-process CPU decoder and its bundled codec libraries."""
    try:
        import av
        from PIL import Image
        import numpy
        for name in ('h264', 'hevc'):
            av.CodecContext.create(name, 'r')
    except (ImportError, OSError, ValueError) as error:
        raise ValueError('CPU decoder unavailable') from error
    return {'backend': 'pyav', 'version': av.__version__,
            'libraries': {name: list(version) for name, version in av.library_versions.items()}}


def decode_pyav_pool(source, frame_root):
    """Decode dense or sparse recordings by raw ordinal, without external tools.

    Count every decoded frame and save only selected RGB frames. PyAV does not
    apply display rotation, frame-rate conversion, resizing or timestamp seeks.
    """
    import av
    from PIL import Image
    video = source['video']
    if file_sha(video['path']) != video['sha256']:
        raise ValueError('Video source SHA-256 mismatch')
    selected = set(frame_numbers(source['pool']))
    numbers = sparse_frames(source)
    if numbers is not None and not selected <= set(numbers):
        raise ValueError('Sparse pool includes an unposed raw frame')
    if numbers is None and source['total_num_frames'] != source['pose_count']:
        raise ValueError('Decoded frame count does not equal full-recording pose count')
    frames, count = [], 0
    with av.open(video['path']) as container:
        if not container.streams.video:
            raise ValueError('Recording has no video stream')
        stream = container.streams.video[0]
        stream.thread_count = 1
        for number, frame in enumerate(container.decode(stream)):
            count = number + 1
            if number not in selected:
                continue
            image = Image.fromarray(frame.to_ndarray(format='rgb24'))
            output = io.BytesIO()
            image.save(output, format='PNG')
            raw = output.getvalue()
            sha = digest(raw)
            path = Path(frame_root).resolve() / sha[:2] / (sha + '.png')
            path.parent.mkdir(parents=True, exist_ok=True)
            store_png(path, raw, sha)
            frames.append({'frame_number': number, 'path': str(path), 'sha256': sha,
                           'raster_hw': [image.height, image.width]})
    if count != source['total_num_frames'] or len(frames) != len(selected):
        raise ValueError('Decoded frame count or selected pool does not match the recording')
    return {'dataset': source['dataset'], 'scene': source['scene'], 'decoded_frame_count': count,
            'pose_count': source['pose_count'], 'video': source['video'], 'frames': frames}


def stage(plan, plan_pin, frame_root, shard, shards, *, use_pyav=False, workers=1):
    validate_plan(plan)
    integer(shards, 'Shards', 1)
    integer(shard, 'Shard')
    if shard >= shards:
        raise ValueError('Shard index exceeds shard count')
    integer(workers, 'Workers', 1)
    decoder = decode_pyav_pool if use_pyav else decode_pool
    sources = [s for i, s in enumerate(plan['scenes']) if i % shards == shard]
    if workers == 1 or not sources:
        scenes = [decoder(s, frame_root) for s in sources]
    else:
        # Spawn keeps codec state out of children; map preserves the plan order.
        # Materialize every result before returning a complete staging receipt.
        with ProcessPoolExecutor(max_workers=min(workers, len(sources)),
                                 mp_context=multiprocessing.get_context('spawn')) as pool:
            scenes = list(pool.map(decoder, sources, repeat(frame_root)))
    return {'schema': 'recording-pose-staged-v1', 'plan': plan_pin, 'shard': shard, 'shards': shards, 'scenes': scenes}


def build_row(source, poses, staged, sampler, index, seed, sampling=None):
    rng = random.Random(f"{seed}:{source['dataset']}:{source['scene']}:{index}")
    if sampling is not None and sampling['variant'] != 'table14':
        rng = random.Random(f"{seed}:{source['dataset']}:{source['scene']}:{index}:{sampling['variant']}:{sampling['epoch']}")
    mode, interval_mode, order = sampler.draw(rng, source['dataset'])
    pose_order = order
    if sparse_frames(source) is not None:
        lookup = {f: i for i, f in enumerate(poses['frame_numbers'])}
        pose_order = [lookup[f] for f in order]
    all_frames = sampling is not None and sampling['variant'] == 'all_frames32'
    capacity = 32 if all_frames else max(16, len(order) // 2)
    camera, mask, scale, gravity = pose_samples.encode_sample(
        poses['c2w'], poses['intrinsics'], poses['raster_hw'], pose_order, poses['world_up'], max_groups=capacity, all_frames=all_frames)
    if not mask[:len(order) if all_frames else len(order) // 2].all():
        raise ValueError('Selected pose anchors must all have calibrated rigid targets')
    positions = [source['pool'].index(f) for f in order]
    frames = {f['frame_number']: f for f in staged['frames']}
    sample = {'schema': pose_samples.SCHEMA, 'mode': mode, 'frames': len(order), 'positions': positions,
              'stride': order[1] - order[0] if interval_mode == 'fixed' else None, 'reversed': False,
              'augment': {**pose_samples.AUGMENT, 'seed': rng.randrange(2**31)},
              'camera': camera.tolist(), 'camera_mask': mask.tolist(), 'trajectory_scale': scale,
              'gravity': gravity.tolist(), 'gravity_mask': True, 'metric': True}
    if all_frames:
        sample.update(anchors=list(range(1, 33)), temporal_grouping='fused_pairs_all_frames')
    # Timing fields preserve the original raw frame ordinals. Window strides alone scale with fps.
    inputs = {'question': pose_samples.PROMPT, 'options': [],
              'frames': [{k: frames[f][k] for k in ('path', 'sha256')} for f in order],
              'frame_indices': order, 'timestamps': [f / source['fps'] for f in order],
              'fps': source['fps'], 'total_num_frames': source['total_num_frames']}
    sample['recording'] = {'schema': 'recording-pose-sampling-v1', 'raw_frame_numbers': order,
                           'pool_positions': positions, 'interval_mode': interval_mode,
                           'effective_intervals': [b - a for a, b in zip(order, order[1:])],
                           'conditioning': CONDITIONING}
    if sampling is not None:
        sample['recording']['sampling'] = sampling
        sample['recording']['conditioning'] = conditioning_for(sampling)
    if sparse_frames(source) is not None and not all_frames:
        sample['recording']['conditioning'] = SPARSE_CONDITIONING
        sample['recording']['target_frame_numbers'] = sampler.target_frame_numbers
        sample['stride'] = None
    row = {'qid': pose_samples.sample_qid(source['dataset'] + '/' + source['scene'], index, seed),
           'dataset': source['dataset'], 'scene': source['scene'], 'category': pose_samples.CATEGORY,
           'answer': '', 'target': pose_samples.TARGET, 'student_input': inputs, 'pose_sample': sample}
    if sampling is not None and sampling['variant'] != 'table14':
        row['qid'] = pose_samples.sample_qid(source['dataset'] + '/' + source['scene'], index,
                                           f"{seed}:{sampling['variant']}:{sampling['epoch']}")
    pose_samples.check_sample(row, max_groups=capacity)
    return row


def build(plan, plan_pin, staged_pins, output):
    """Stream rows and compute AUDIT.json; authenticate every staged pooled frame."""
    from PIL import Image
    validate_plan(plan)
    staged, shards, total_shards = {}, set(), None
    for source_pin in staged_pins:
        receipt = json.loads(read_pin(source_pin))
        if receipt['schema'] != 'recording-pose-staged-v1' or receipt['plan'] != plan_pin:
            raise ValueError('Staging receipt belongs to another plan')
        if total_shards is not None and total_shards != receipt['shards']:
            raise ValueError('Staging receipts disagree on shard count')
        total_shards = receipt['shards']
        if receipt['shard'] in shards:
            raise ValueError('Duplicate staging shard')
        shards.add(receipt['shard'])
        for scene in receipt['scenes']:
            key = scene['dataset'], scene['scene']
            if key in staged:
                raise ValueError('Duplicate staged recording')
            staged[key] = scene
    if total_shards is None or shards != set(range(total_shards)):
        raise ValueError('Missing staging shard')
    if set(staged) != {(s['dataset'], s['scene']) for s in plan['scenes']}:
        raise ValueError('Staged scene identities differ from plan')
    audit = {'schema': 'recording-pose-audit-v1', 'plan': plan_pin, 'authorities': plan['authorities'],
             'staging': staged_pins, 'conditioning': plan['conditioning'], 'rows_per_scene': plan['rows_per_scene'],
             'probabilities': plan['probabilities'], 'seed': plan['seed'], 'depth_labels_built': False,
             'excluded': plan['excluded'], 'deferred': plan['deferred'],
             'excluded_scenes': len(plan['excluded']), 'deferred_scenes': len(plan['deferred']),
             'exclusion_counts': dict(Counter(reason for s in plan['excluded'] for reason in s['reasons'])),
             'exclusion_counts_by_dataset': {d: dict(Counter(reason for s in plan['excluded']
                 if s['dataset'] == d for reason in s['reasons'])) for d in PROBABILITIES},
             'deferred_counts': dict(Counter(s['reason'] for s in plan['deferred'])),
             'datasets': {d: {'scenes': 0, 'rows': 0, 'modes': Counter()} for d in PROBABILITIES},
             'N_histogram': Counter(), 'interval_histograms': {}, 'pool_coverage': [],
             'target_sanity': {'max_quaternion_norm_error': 0., 'max_gravity_norm_error': 0.,
                               'max_abs_translation': 0., 'finite_translation': True}}
    cache, rows = {}, 0
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    with (output / 'pose_rows.jsonl').open('xb') as stream:
        for source in plan['scenes']:
            scene = staged[source['dataset'], source['scene']]
            if (scene['decoded_frame_count'] != source['total_num_frames'] or scene['pose_count'] != source['pose_count']
                    or scene['video'] != source['video']):
                raise ValueError('Staging count or video identity mismatch')
            if [f['frame_number'] for f in scene['frames']] != source['pool']:
                raise ValueError('Staged raw frame numbers differ from pool')
            poses = load_poses(source, cache)
            for frame in scene['frames']:
                if frame['raster_hw'] != poses['raster_hw'] or file_sha(frame['path']) != frame['sha256']:
                    raise ValueError('Staged RGB hash or calibrated raster mismatch')
                with Image.open(frame['path']) as image:
                    if image.mode != 'RGB' or [image.height, image.width] != poses['raster_hw']:
                        raise ValueError('Staged image is not the calibrated RGB raster')
                    image.verify()
            sampler, used = sampler_for(source, sampling_settings(plan.get('sampling', {})), plan['seed']), set()
            dataset = audit['datasets'].setdefault(source['dataset'], {'scenes': 0, 'rows': 0, 'modes': Counter()})
            dataset['scenes'] += 1
            for index in range(plan['rows_per_scene']):
                row = build_row(source, poses, scene, sampler, index, plan['seed'], plan.get('sampling'))
                stream.write((pose_samples.manifest_line(row) + '\n').encode())
                rows += 1
                dataset['rows'] += 1
                sample = row['pose_sample']
                details = sample['recording']
                dataset['modes'][details['interval_mode'] or 'collection'] += 1
                audit['N_histogram'][str(sample['frames'])] += 1
                audit['interval_histograms'].setdefault(details['interval_mode'] or 'collection', Counter()).update(
                    map(str, details['effective_intervals']))
                used.update(details['raw_frame_numbers'])
                targets = np.asarray(sample['camera'])[np.asarray(sample['camera_mask'])]
                sanity = audit['target_sanity']
                sanity['max_quaternion_norm_error'] = max(sanity['max_quaternion_norm_error'],
                    float(np.max(np.abs(np.linalg.norm(targets[:, 3:7], axis=1) - 1))))
                sanity['max_gravity_norm_error'] = max(sanity['max_gravity_norm_error'],
                    abs(float(np.linalg.norm(sample['gravity'])) - 1))
                sanity['max_abs_translation'] = max(sanity['max_abs_translation'], float(np.abs(targets[:, :3]).max()))
            pool = source['pool']
            audit['pool_coverage'].append({'dataset': source['dataset'], 'scene': source['scene'],
                'recording_frames': source['total_num_frames'], 'pool_frames': len(pool), 'used_frames': len(used),
                'sample_sizes': source['sample_sizes'],
                'pool_fraction': len(pool) / source['total_num_frames'], 'used_pool_fraction': len(used) / len(pool),
                'min_frame_number': pool[0], 'max_frame_number': pool[-1],
                'span_fraction': (pool[-1] - pool[0] + 1) / source['total_num_frames'],
                'occupied_sixteenths': len({min(15, f * 16 // source['total_num_frames']) for f in pool})})
    audit.update(rows=rows, scenes=len(plan['scenes']), pose_rows=pin(output / 'pose_rows.jsonl'))
    if 'sampling' in plan:
        audit['sampling'] = plan['sampling']
    for key, value in cache.items():
        if key[0] == 'archive':
            value.close()
    write_new(output / 'AUDIT.json', payload(audit))
    return audit


def job_files(plan_pin, frame_root, receipt_root, deployment, shards=4):
    """Return an opaque Slurm array spec and script; never submit a job."""
    integer(shards, 'Shards', 1)
    name = 'a15_cot_ap' + digest(payload(plan_pin))[:12]
    spec = {'job_name': name, 'partition': 'cpu', 'qos': 'cpu-normal', 'time': '01:30:00',
            'array': f'0-{shards - 1}%4', 'cpus_per_task': 2, 'mem': '8G', 'gpus': 0}
    import shlex
    quote = shlex.quote
    script = '\n'.join(['#!/bin/bash', f'#SBATCH --job-name={name}', '#SBATCH --partition=cpu',
        '#SBATCH --qos=cpu-normal', '#SBATCH --time=01:30:00', f'#SBATCH --array={spec["array"]}',
        '#SBATCH --cpus-per-task=2', '#SBATCH --mem=8G',
        '#SBATCH --output=' + str(receipt_root).rstrip('/') + '/' + name + '_%A_%a.out', 'set -euo pipefail',
        'export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1',
        'cd ' + quote(str(deployment)),
        '"${PYTHON:?}" -B -m student_pilot.recording_pose stage --plan ' + quote(plan_pin['path']) +
        ' --plan-sha256 ' + quote(plan_pin['sha256']) + ' --frame-root ' + quote(str(frame_root)) +
        ' --shards ' + str(shards) + ' --shard "$SLURM_ARRAY_TASK_ID" --output ' +
        quote(str(receipt_root).rstrip('/')) + '/"$SLURM_ARRAY_TASK_ID".json', ''])
    return spec, script


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prepare = commands.add_parser('plan')
    prepare.add_argument('--request', type=Path, required=True)
    prepare.add_argument('--output', type=Path, required=True)
    for command in ('stage', 'build', 'jobs'):
        sub = commands.add_parser(command)
        sub.add_argument('--plan', type=Path, required=True)
        sub.add_argument('--plan-sha256', required=True)
        sub.add_argument('--output', type=Path, required=True)
        if command in ('stage', 'jobs'):
            sub.add_argument('--frame-root', type=Path, required=True)
            sub.add_argument('--shards', type=int, help='Default: one shard per 16 recordings; at most four run together')
        if command == 'stage':
            sub.add_argument('--shard', type=int, required=True)
        if command == 'jobs':
            sub.add_argument('--receipt-root', type=Path, required=True)
            sub.add_argument('--deployment', type=Path, required=True)
        if command == 'build':
            sub.add_argument('--staged-pins', type=Path, required=True, help='JSON list of staged receipt pins')
    args = parser.parse_args(argv)
    if args.command == 'plan':
        request = json.loads(args.request.read_bytes())
        result = make_plan(request)
        result['request'] = pin(args.request)
        write_new(args.output, payload(result))
        return
    plan_pin = {'path': str(args.plan.resolve()), 'sha256': args.plan_sha256}
    plan = json.loads(read_pin(plan_pin))
    if plan.get('schema') != 'recording-pose-plan-v1':
        raise ValueError('Unknown plan schema')
    if args.command in ('stage', 'jobs') and args.shards is None:
        args.shards = max(1, math.ceil(len(plan['scenes']) / 16))
    if args.command == 'stage':
        if args.output.exists():
            raise FileExistsError(args.output)
        result = stage(plan, plan_pin, args.frame_root, args.shard, args.shards)
        write_new(args.output, payload(result))
    elif args.command == 'build':
        build(plan, plan_pin, json.loads(args.staged_pins.read_bytes()), args.output)
    else:
        spec, script = job_files(plan_pin, args.frame_root, args.receipt_root, args.deployment, args.shards)
        args.output.mkdir(parents=True, exist_ok=False)
        write_new(args.output / (spec['job_name'] + '.json'), payload(spec))
        write_new(args.output / (spec['job_name'] + '.sh'), script.encode())


if __name__ == '__main__':
    main()
