"""Deterministic clip planning, local materialization, and authenticated packaging."""
import argparse
import bisect
from collections import Counter, defaultdict
import copy
import hashlib
import io
import json
import math
import os
from pathlib import Path
import random
import re
import sqlite3
import tarfile
import time
import uuid

import numpy as np

from . import recording_pose as recording
from . import pose_samples
from . import c1r_ref
from .c1r_targets import encode_target

CURRICULUM = {'hold_fraction': 0.4, 'initial': [0.5, 0.3, 0.2], 'final': [0.15, 0.25, 0.6]}
PROBABILITIES = {'video': {'d1': 0.6, 'd2': 0.8, 'd3': 0.8}, 'dense': 0.5, 'fixed': 0.5}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def pin(path):
    return recording.pin(path)


def read_pin(value):
    return recording.read_pin(value)


def atomic(path, writer):
    """Publish a new file after a complete temporary write; retain interrupted files."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.part')
    with temporary.open('xb') as stream:
        writer(stream)
        stream.flush()
        os.fsync(stream.fileno())
    os.rename(temporary, path)


def write_json(path, value):
    atomic(path, lambda stream: stream.write(canonical(value) + b'\n'))


def posed_ordinals(source):
    numbers = source.get('frame_numbers')
    if numbers is None:
        if source['pose_count'] != source['total_num_frames']:
            raise ValueError('Missing sparse posed ordinals')
        return list(range(source['total_num_frames']))
    numbers = recording.frame_numbers(numbers)
    if len(numbers) != source['pose_count'] or numbers[-1] >= source['total_num_frames']:
        raise ValueError('Invalid posed ordinal census')
    return numbers


def fingerprint(source):
    return sha256(canonical([source['dataset'], source['scene'], source['fps'], source['total_num_frames'],
                             source['pose_count'], posed_ordinals(source)]))


def load_a1(value):
    data = json.loads(read_pin(value))
    if data.get('schema') != 'recording-pose-plan-v1' or not data.get('scenes'):
        raise ValueError('Expected admitted recording plan')
    sources, seen = [], set()
    for source in data['scenes']:
        key = source['dataset'], source['scene']
        if (source['dataset'] not in ('d1', 'd2', 'd3') or key in seen
                or not re.fullmatch(r'[a-zA-Z0-9_-]+', source['scene'])
                or not math.isfinite(source['fps']) or source['fps'] <= 0):
            raise ValueError('Invalid or duplicate recording identity')
        posed_ordinals(source)
        sources.append(source)
        seen.add(key)
    return sources


def probabilities(step, steps, curriculum):
    f = (step + 1) / steps
    hold = curriculum['hold_fraction']
    t = max(0.0, (f - hold) / (1 - hold))
    return [(1 - t) * a + t * b for a, b in zip(curriculum['initial'], curriculum['final'])]


def tier_at(seed, step, micro, steps, curriculum):
    p = probabilities(step, steps, curriculum)
    draw = random.Random(f'c1r-tier:{seed}:{step}:{micro}').random()
    return 'hi' if draw < p[0] else '64' if draw < p[0] + p[1] else '32'


def uniform_ordinals(numbers, n, rng):
    spacing = (len(numbers) - 1) / (n - 1)
    positions, previous = [], -1
    for k in range(n):
        j = round(k * spacing + rng.uniform(-0.5, 0.5) * spacing)
        j = max(previous + 1, min(j, len(numbers) - n + k))
        positions.append(j)
        previous = j
    return [numbers[j] for j in positions]


def nearest(numbers, value, minimum=0):
    j = bisect.bisect_left(numbers, value, lo=minimum)
    candidates = [k for k in (j - 1, j) if minimum <= k < len(numbers)]
    if not candidates:
        raise ValueError('No distinct posed ordinal remains')
    return min(candidates, key=lambda k: (abs(numbers[k] - value), numbers[k]))


def sample_clip(source, numbers, n, rng, modes):
    """Sample only posed ordinals; retain the requested mode when a fallback occurs."""
    result = {'mode': None, 'requested_mode': None, 'cut3r_kind': None, 'stride': None,
              'gap_seconds': [], 'fallback': False}
    if rng.random() >= modes['video'][source['dataset']]:
        result.update(mode='collection', requested_mode='collection', ordinals=sorted(rng.sample(numbers, n)))
        return result
    mode = 'dense' if rng.random() < modes['dense'] else 'cut3r'
    result.update(mode=mode, requested_mode=mode)
    if mode == 'dense':
        grid_step = max(1, round(source['fps'] / 10))
        # Sparse recordings already define their own temporal grid.
        every_frame = len(numbers) == source['total_num_frames']
        grid = numbers[::grid_step] if every_frame and source['dataset'] != 'd3' else numbers
        feasible = [k for k in (1, 2, 3) if (n - 1) * k < len(grid)]
        if feasible:
            stride = rng.choice(feasible)
            start = rng.randrange(len(grid) - stride * (n - 1))
            result.update(stride=stride, ordinals=[grid[start + stride * k] for k in range(n)])
            return result
    else:
        kind = 'fixed' if rng.random() < modes['fixed'] else 'variable'
        gaps = [rng.uniform(1.0, 3.33)] * (n - 1) if kind == 'fixed' else [rng.uniform(1.0, 3.33) for _ in range(n - 1)]
        result.update(cut3r_kind=kind, gap_seconds=gaps)
        length = sum(gaps) * source['fps']
        latest = numbers[-1] - length
        starts = bisect.bisect_right(numbers, latest)
        if starts:
            start = rng.randrange(starts)
            selected = [start]
            target = float(numbers[start])
            try:
                for gap in gaps:
                    target += gap * source['fps']
                    selected.append(nearest(numbers, target, selected[-1] + 1))
                result['ordinals'] = [numbers[j] for j in selected]
                return result
            except ValueError:
                pass
    result.update(mode='uniform', fallback=True, ordinals=uniform_ordinals(numbers, n, rng))
    return result


def summarize(rows, sources, steps):
    by_tier, by_dataset, by_mode = Counter(), Counter(), Counter()
    mode_tier, mode_dataset, deciles = defaultdict(Counter), defaultdict(Counter), defaultdict(Counter)
    spans, covered = defaultdict(list), defaultdict(set)
    replacements = Counter()
    frames, pending, fallbacks = Counter(), 0, 0
    for row in rows:
        by_tier[row['tier']] += 1
        deciles[str(min(9, row['step'] * 10 // steps))][row['tier']] += 1
        if row['pending']:
            pending += 1
            continue
        by_dataset[row['dataset']] += 1
        by_mode[row['mode']] += 1
        mode_tier[row['tier']][row['mode']] += 1
        mode_dataset[row['dataset']][row['mode']] += 1
        spans[row['mode']].append((row['ordinals'][-1] - row['ordinals'][0]) / row['fps'])
        covered[row['recording_fingerprint']].update(row['ordinals'])
        frames[row['tier']] += row['N']
        fallbacks += row['fallback']
        if row['recording_fallback']:
            replacements[row['tier']] += 1
    coverage = {}
    for source in sources:
        key = source['recording_fingerprint']
        count = len(covered[key])
        coverage[source['scene']] = {'posed': source['pose_count'], 'selected_unique': count,
                                     'fraction': count / source['pose_count']}
    span_hist = {}
    for mode, values in spans.items():
        bins = Counter()
        for x in values:
            label = next((str(b) for b in (1, 3.33, 10, 30, 60, 120, 300, 600) if x <= b), 'above_600')
            bins[label] += 1
        span_hist[mode] = {'count': len(values), 'min': min(values), 'mean': sum(values) / len(values),
                           'max': max(values), 'upper_bound_seconds': dict(bins)}
    return {'counts': {'rows': len(rows), 'ready': len(rows) - pending, 'pending': pending,
                        'tiers': dict(by_tier), 'datasets': dict(by_dataset), 'modes': dict(by_mode),
                        'frames_per_tier': dict(frames), 'sampling_fallbacks': fallbacks,
                        'recording_fallbacks': dict(replacements)},
            'histograms': {'tier_step_decile': dict(deciles), 'mode_per_tier': dict(mode_tier),
                           'mode_per_dataset': dict(mode_dataset), 'span_seconds_per_mode': span_hist,
                           'ordinal_coverage': coverage}}


def _plan_v1(request):
    """Create a path-free row plan; a hi fill preserves all previously ready rows."""
    seed, steps = request.get('seed', 17), request.get('steps', 800)
    ranks, micros = request.get('ranks', 8), request.get('microsteps', 4)
    if any(type(x) is not int or x < 1 for x in (steps, ranks, micros)) or (ranks, micros) != (8, 4):
        raise ValueError('Expected positive steps and the 8-rank, 4-microstep layout')
    tiers = request.get('tiers', {'hi': None, '64': 64, '32': 32})
    if (set(tiers) != {'hi', '64', '32'} or tiers['64'] != 64 or tiers['32'] != 32
            or tiers['hi'] is not None and (type(tiers['hi']) is not int or not 64 <= tiers['hi'] <= 256 or tiers['hi'] % 16)):
        raise ValueError('Invalid frame tiers')
    curriculum = copy.deepcopy(request.get('curriculum', CURRICULUM))
    modes = copy.deepcopy(request.get('mode_probabilities', PROBABILITIES))
    if (set(curriculum) != set(CURRICULUM) or not 0 <= curriculum['hold_fraction'] < 1
            or any(len(curriculum[k]) != 3 or any(not 0 <= x <= 1 for x in curriculum[k])
                   or not math.isclose(sum(curriculum[k]), 1) for k in ('initial', 'final'))
            or set(modes) != set(PROBABILITIES) or set(modes['video']) != {'d1', 'd2', 'd3'}
            or any(not 0 <= x <= 1 for x in [*modes['video'].values(), modes['dense'], modes['fixed']])):
        raise ValueError('Invalid sampling probabilities')
    sources = load_a1(request['a1_plan'])
    numbers = [posed_ordinals(s) for s in sources]
    ids = [fingerprint(s) for s in sources]
    census = [{'dataset': s['dataset'], 'scene': s['scene'], 'fps': s['fps'],
               'total_num_frames': s['total_num_frames'], 'pose_count': s['pose_count'],
               'recording_fingerprint': ids[j]} for j, s in enumerate(sources)]
    rows, order, fallback_orders, cursors = [], [], {}, Counter()
    for tier, n in tiers.items():
        if n is not None:
            eligible = [j for j, s in enumerate(sources) if s['pose_count'] >= n]
            if not eligible:
                raise ValueError('No eligible recording for tier ' + tier)
            random.Random(f'c1r-fallback:{seed}:{tier}').shuffle(eligible)
            fallback_orders[tier] = eligible
    for i in range(steps * ranks * micros):
        epoch, offset = divmod(i, len(sources))
        if offset == 0:
            order = list(range(len(sources)))
            random.Random(f'c1r-record:{seed}:{epoch}').shuffle(order)
        step, micro = i // 32, (i % 32) // 8
        tier = tier_at(seed, step, micro, steps, curriculum)
        n, base = tiers[tier], order[offset]
        row = {'i': i, 'qid': sha256(f'c1r-qid:{seed}:{i}'.encode())[:24], 'step': step,
               'micro': micro, 'rank': i % 8, 'tier': tier, 'N': n, 'pending': n is None,
               'base_recording': {'dataset': sources[base]['dataset'], 'scene': sources[base]['scene'],
                                  'recording_fingerprint': ids[base]}}
        if n is not None:
            selected = base
            replacement = None
            if len(numbers[base]) < n:
                queue = fallback_orders[tier]
                selected = queue[cursors[tier] % len(queue)]
                cursors[tier] += 1
                replacement = {'reason': 'too_few_poses', 'posed': len(numbers[base]),
                               'cursor': cursors[tier] - 1}
            source = sources[selected]
            row.update(dataset=source['dataset'], scene=source['scene'], recording_fingerprint=ids[selected],
                       fps=source['fps'], total_num_frames=source['total_num_frames'],
                       recording_fallback=replacement,
                       augment_seed=int(sha256(f'c1r-aug:{seed}:{i}'.encode())[:8], 16))
            row.update(sample_clip(source, numbers[selected], n, random.Random(f'c1r-clip:{seed}:{i}'), modes))
            row['effective_gap_seconds'] = [(b - a) / source['fps'] for a, b in zip(row['ordinals'], row['ordinals'][1:])]
        rows.append(row)
    result = {'schema': 'c1r-clip-plan-v1', 'seed': seed, 'steps': steps, 'ranks': ranks, 'microsteps': micros,
              'tiers': tiers, 'curriculum': curriculum, 'mode_probabilities': modes, 'a1_plan': request['a1_plan'],
              'recording_order': 'independent_epochs_with_per_tier_fallback_v1',
              'recordings_sha256': sha256(canonical(ids)), 'recordings': census, 'rows': rows}
    result.update(summarize(rows, census, steps))
    if request.get('previous_plan'):
        previous = json.loads(read_pin(request['previous_plan']))
        keys = ('schema', 'seed', 'steps', 'ranks', 'microsteps', 'curriculum', 'mode_probabilities',
                'a1_plan', 'recording_order', 'recordings_sha256', 'recordings')
        if any(previous[k] != result[k] for k in keys) or len(previous['rows']) != len(rows):
            raise ValueError('Hi fill changed the planning identity')
        if previous['tiers']['hi'] is not None or tiers['hi'] is None:
            raise ValueError('Hi fill needs a pending source and a resolved hi tier')
        for old, new in zip(previous['rows'], rows):
            if not old['pending'] and canonical(old) != canonical(new):
                raise ValueError('Hi fill changed an existing row')
    return result


def _validate_plan_v1(data):
    if (data.get('schema') != 'c1r-clip-plan-v1' or data.get('ranks') != 8 or data.get('microsteps') != 4
            or len(data['rows']) != data['steps'] * 32):
        raise ValueError('Invalid clip plan layout')
    for i, row in enumerate(data['rows']):
        if (row['i'] != i or row['step'] != i // 32 or row['micro'] != (i % 32) // 8 or row['rank'] != i % 8
                or row['qid'] != sha256(f"c1r-qid:{data['seed']}:{i}".encode())[:24]
                or row['tier'] != tier_at(data['seed'], row['step'], row['micro'], data['steps'], data['curriculum'])
                or row['N'] != data['tiers'][row['tier']] or row['pending'] != (row['N'] is None)):
            raise ValueError('Clip row identity mismatch')
        if not row['pending']:
            values = recording.frame_numbers(row['ordinals'])
            if len(values) != row['N'] or values[-1] >= row['total_num_frames']:
                raise ValueError('Clip ordinal shape mismatch')
    return data


def layout_frames(viewpoints, numbers, fps, layout, gap):
    """Reserve a posed partner after every anchor, with deterministic nearest snapping."""
    viewpoints = list(viewpoints)
    adjusted = 0
    if layout == 'paired':
        if len(numbers) < 64:
            raise ValueError('Paired layout requires 64 posed frames')
        previous, projected = -2, []
        for j, value in enumerate(viewpoints):
            position = bisect.bisect_left(numbers, value)
            position = max(previous + 2, min(position, len(numbers) - 2 * (32 - j)))
            projected.append(numbers[position])
            previous = position
        adjusted = sum(a != b for a, b in zip(viewpoints, projected))
        viewpoints = projected
    slots, actual, fallback = [], [], 0
    for j, value in enumerate(viewpoints):
        slots.append(value)
        if layout == 'duplicate':
            slots.append(value)
            actual.append(0.0)
        elif layout == 'paired':
            lo = bisect.bisect_right(numbers, value)
            hi = bisect.bisect_left(numbers, viewpoints[j + 1]) if j < 31 else len(numbers)
            target = value + gap * fps
            preferred = nearest(numbers, target)
            position = max(lo, min(preferred, hi - 1))
            partner = numbers[position]
            slots.append(partner)
            actual.append((partner - value) / fps)
            fallback += position != preferred
    distinct = list(dict.fromkeys(slots))
    lookup = {value: i for i, value in enumerate(distinct)}
    return dict(viewpoints=viewpoints, slots=slots, ordinals=distinct,
                slot_map=[lookup[value] for value in slots],
                anchor_slots=list(range(32)) if layout == 'spread' else list(range(0, 64, 2)),
                pair_actual_gap_seconds=actual, pair_fallback_count=fallback,
                viewpoint_fallback_count=adjusted)


def summarize_v2(rows, sources, steps):
    counts = {'rows': len(rows), 'ready': len(rows), 'pending': 0,
              'datasets': dict(Counter(r['dataset'] for r in rows)),
              'modes': dict(Counter(r['mode'] for r in rows)),
              'layouts': dict(Counter(r['layout'] for r in rows)),
              'slots': sum(len(r['slots']) for r in rows),
              'distinct_frames': sum(len(r['ordinals']) for r in rows),
              'sampling_fallbacks': sum(r['fallback'] for r in rows),
              'recording_fallbacks': sum(bool(r['recording_fallback']) for r in rows),
              'pair_fallbacks': sum(r['pair_fallback_count'] for r in rows),
              'viewpoint_adjustments': sum(r['viewpoint_fallback_count'] for r in rows)}
    return {'counts': counts, 'histograms': {'mode_per_dataset': {
        d: dict(Counter(r['mode'] for r in rows if r['dataset'] == d)) for d in ('d1', 'd2', 'd3')}}}


def plan(request):
    """Default to the fixed-viewpoint contract; explicit legacy tier requests remain stable."""
    if 'frames' not in request and ('tiers' in request or 'curriculum' in request):
        return _plan_v1(request)
    if any(k in request for k in ('tiers', 'curriculum', 'previous_plan')):
        raise ValueError('Fixed viewpoint plans have no tiers or curriculum')
    seed, steps = request.get('seed', 17), request.get('steps', 800)
    ranks, micros = request.get('ranks', 8), request.get('microsteps', 4)
    frames = dict(request.get('frames', {}))
    if set(frames) - {'layout', 'pair_gap_seconds', 'pixels_per_frame'}:
        raise ValueError('Unknown frame settings')
    layout, gap = frames.get('layout', 'spread'), frames.get('pair_gap_seconds', 0.5)
    if (layout not in ('spread', 'paired', 'duplicate') or type(gap) not in (int, float)
            or not math.isfinite(gap) or gap <= 0):
        raise ValueError('Invalid frame layout or pair gap')
    if frames.get('pixels_per_frame', list(pose_samples.DEFAULT_PIXELS)) != list(pose_samples.DEFAULT_PIXELS):
        raise ValueError('Fixed native pixel budget required')
    frames = {'layout': layout, 'pair_gap_seconds': gap, 'pixels_per_frame': list(pose_samples.DEFAULT_PIXELS)}
    if (type(seed) is not int or type(steps) is not int or steps < 1 or (ranks, micros) != (8, 4)):
        raise ValueError('Expected integer seed, positive steps, 8 ranks and 4 microsteps')
    modes = copy.deepcopy(request.get('mode_probabilities', PROBABILITIES))
    if (set(modes) != set(PROBABILITIES) or set(modes['video']) != {'d1', 'd2', 'd3'}
            or any(type(x) not in (int, float) or not math.isfinite(x) or not 0 <= x <= 1
                   for x in [*modes['video'].values(), modes['dense'], modes['fixed']])):
        raise ValueError('Invalid sampling probabilities')
    sources = load_a1(request['a1_plan'])
    numbers = [posed_ordinals(s) for s in sources]
    ids = [fingerprint(s) for s in sources]
    required = 64 if layout == 'paired' else 32
    eligible = [j for j, values in enumerate(numbers) if len(values) >= required]
    if not eligible:
        raise ValueError('No eligible recording for layout')
    random.Random(f'c1r-fallback:{seed}:32').shuffle(eligible)
    rows, order, cursor = [], [], 0
    for i in range(steps * 32):
        epoch, offset = divmod(i, len(sources))
        if offset == 0:
            order = list(range(len(sources)))
            random.Random(f'c1r-record:{seed}:{epoch}').shuffle(order)
        base = selected = order[offset]
        replacement = None
        if len(numbers[base]) < required:
            selected = eligible[cursor % len(eligible)]
            replacement = {'reason': 'too_few_poses', 'posed': len(numbers[base]), 'cursor': cursor}
            cursor += 1
        source = sources[selected]
        sample = sample_clip(source, numbers[selected], 32, random.Random(f'c1r-clip:{seed}:{i}'), modes)
        mapping = layout_frames(sample.pop('ordinals'), numbers[selected], source['fps'], layout, gap)
        row = dict(schema='c1r-clip-row-v2', i=i, qid=sha256(f'c1r-qid:{seed}:{i}'.encode())[:24],
                   step=i // 32, micro=(i % 32) // 8, rank=i % 8, layout=layout, pair_gap_seconds=gap,
                   dataset=source['dataset'], scene=source['scene'], recording_fingerprint=ids[selected],
                   fps=source['fps'], total_num_frames=source['total_num_frames'],
                   base_recording={'dataset': sources[base]['dataset'], 'scene': sources[base]['scene'],
                                   'recording_fingerprint': ids[base]}, recording_fallback=replacement,
                   pending=False, **sample, **mapping)
        row['N'] = len(row['ordinals'])
        row['frames'] = len(row['slots'])
        row['effective_gap_seconds'] = [(b-a)/row['fps'] for a, b in zip(row['viewpoints'], row['viewpoints'][1:])]
        row['augment_seed'] = int(sha256(f'c1r-aug:{seed}:{i}'.encode())[:8], 16)
        row['augment_seeds'] = [int(sha256(f'c1r-aug:{seed}:{i}:{v}'.encode())[:8], 16) for v in row['ordinals']]
        rows.append(row)
    census = [{k: s[k] for k in ('dataset', 'scene', 'fps', 'total_num_frames', 'pose_count')} |
              {'recording_fingerprint': ids[j]} for j, s in enumerate(sources)]
    result = dict(schema='c1r-clip-plan-v2', seed=seed, steps=steps, ranks=8, microsteps=4,
                  frames=frames, mode_probabilities=modes, a1_plan=request['a1_plan'],
                  recording_order='independent_epochs_with_fixed_viewpoint_fallback_v2',
                  recordings_sha256=sha256(canonical(ids)), recordings=census, rows=rows)
    result.update(summarize_v2(rows, census, steps))
    return result


def validate_row_v2(row):
    """Check slot identities independently of any media or teacher backend."""
    layout = row.get('layout')
    values = recording.frame_numbers(row['ordinals'])
    viewpoints = recording.frame_numbers(row['viewpoints'])
    slots, mapping, anchors = row['slots'], row['slot_map'], row['anchor_slots']
    expected_slots = 32 if layout == 'spread' else 64
    if (row.get('schema') != 'c1r-clip-row-v2' or layout not in ('spread', 'paired', 'duplicate')
            or len(viewpoints) != 32 or len(slots) != expected_slots or len(mapping) != expected_slots
            or row['N'] != len(values) or row['frames'] != len(slots) or row['pending'] is not False
            or values[-1] >= row['total_num_frames'] or list(dict.fromkeys(slots)) != values
            or any(type(v) is not int or not 0 <= v < len(values) for v in mapping)
            or [values[k] for k in mapping] != slots
            or anchors != (list(range(32)) if layout == 'spread' else list(range(0, 64, 2)))
            or [slots[k] for k in anchors] != viewpoints
            or type(row['total_num_frames']) is not int or row['total_num_frames'] < 1
            or type(row['augment_seed']) is not int or not 0 <= row['augment_seed'] < 2**32
            or len(row['augment_seeds']) != len(values)
            or any(type(v) is not int or not 0 <= v < 2**32 for v in row['augment_seeds'])
            or type(row['fps']) not in (int, float) or not math.isfinite(row['fps']) or row['fps'] <= 0
            or type(row['pair_gap_seconds']) not in (int, float) or not math.isfinite(row['pair_gap_seconds'])
            or row['pair_gap_seconds'] <= 0):
        raise ValueError('Clip slot identity mismatch')
    if (layout == 'duplicate' and slots[::2] != slots[1::2]
            or layout == 'paired' and any(a >= b for a, b in zip(slots, slots[1:]))
            or row['pair_actual_gap_seconds'] != ([] if layout == 'spread' else
                [(b-a)/row['fps'] for a, b in zip(slots[::2], slots[1::2])])
            or type(row['pair_fallback_count']) is not int or not 0 <= row['pair_fallback_count'] <= 32):
        raise ValueError('Clip pair gaps differ')
    if (row['effective_gap_seconds'] != [(b-a)/row['fps'] for a, b in zip(viewpoints, viewpoints[1:])]
            or type(row['viewpoint_fallback_count']) is not int or not 0 <= row['viewpoint_fallback_count'] <= 32
            or layout != 'paired' and (row['pair_fallback_count'] or row['viewpoint_fallback_count'])
            or row['dataset'] not in ('d1', 'd2', 'd3')
            or not re.fullmatch(r'[a-zA-Z0-9_-]+', row['scene'])
            or not re.fullmatch(r'[0-9a-f]{64}', row['recording_fingerprint'])
            or row['mode'] not in ('collection', 'dense', 'cut3r', 'uniform')
            or row['requested_mode'] not in ('collection', 'dense', 'cut3r')
            or type(row['fallback']) is not bool
            or row['fallback'] != (row['mode'] == 'uniform')):
        raise ValueError('Clip sampling identity mismatch')
    return row


def validate_plan(data):
    if data.get('schema') == 'c1r-clip-plan-v1':
        return _validate_plan_v1(data)
    if (data.get('schema') != 'c1r-clip-plan-v2' or data.get('ranks') != 8 or data.get('microsteps') != 4
            or type(data.get('steps')) is not int or data['steps'] < 1 or len(data['rows']) != data['steps'] * 32):
        raise ValueError('Invalid clip plan layout')
    if (type(data.get('seed')) is not int or set(data['frames']) != {'layout', 'pair_gap_seconds', 'pixels_per_frame'}
            or data['frames']['pixels_per_frame'] != list(pose_samples.DEFAULT_PIXELS)):
        raise ValueError('Invalid fixed frame settings')
    for i, row in enumerate(data['rows']):
        validate_row_v2(row)
        if (row['i'] != i or row['step'] != i // 32 or row['micro'] != (i % 32) // 8 or row['rank'] != i % 8
                or row['qid'] != sha256(f"c1r-qid:{data['seed']}:{i}".encode())[:24]
                or row['layout'] != data['frames']['layout'] or row['pair_gap_seconds'] != data['frames']['pair_gap_seconds']
                or row['augment_seed'] != int(sha256(f"c1r-aug:{data['seed']}:{i}".encode())[:8], 16)
                or row['augment_seeds'] != [int(sha256(f"c1r-aug:{data['seed']}:{i}:{v}".encode())[:8], 16)
                                             for v in row['ordinals']]):
            raise ValueError('Clip row identity mismatch')
    return data


def bind_sources(data, a1_pin):
    sources = load_a1(a1_pin)
    ids = [fingerprint(s) for s in sources]
    if sha256(canonical(ids)) != data['recordings_sha256']:
        raise ValueError('Recording census fingerprint mismatch')
    lookup = {key: source for key, source in zip(ids, sources)}
    posed = {key: posed_ordinals(source) for key, source in lookup.items()}
    sets = {key: set(values) for key, values in posed.items()}
    for row in data['rows']:
        if row['pending']:
            continue
        source = lookup.get(row['recording_fingerprint'])
        if (source is None or source['scene'] != row['scene'] or source['dataset'] != row['dataset']
                or source['fps'] != row['fps'] or source['total_num_frames'] != row['total_num_frames']
                or not set(row['ordinals']) <= sets[row['recording_fingerprint']]):
            raise ValueError('Clip recording fingerprint mismatch')
        if row.get('schema') == 'c1r-clip-row-v2':
            expected = layout_frames(row['viewpoints'], posed[row['recording_fingerprint']], source['fps'],
                                     row['layout'], row['pair_gap_seconds'])
            if any(row[k] != expected[k] for k in ('viewpoints', 'slots', 'ordinals', 'slot_map',
                                                  'anchor_slots', 'pair_actual_gap_seconds', 'pair_fallback_count')):
                raise ValueError('Clip posed partner mismatch')
    return lookup


def recording_chunks(data, chunks):
    """Contiguous recording groups, cut nearest cumulative clip-count quantiles."""
    if type(chunks) is not int or chunks < 1:
        raise ValueError('Expected positive chunk count')
    groups = defaultdict(list)
    for row in data['rows']:
        if not row['pending']:
            groups[row['recording_fingerprint']].append(row)
    keys = sorted(groups, key=lambda key: (groups[key][0]['step'], groups[key][0]['i'], key))
    cumulative = [0]
    for key in keys:
        cumulative.append(cumulative[-1] + len(groups[key]))
    boundaries = [0]
    for k in range(1, chunks):
        target = cumulative[-1] * k / chunks
        j = bisect.bisect_left(cumulative, target)
        boundary = min((max(0, j - 1), min(j, len(keys))), key=lambda x: (abs(cumulative[x] - target), x))
        boundaries.append(max(boundaries[-1], boundary))
    boundaries.append(len(keys))
    return [[(key, groups[key]) for key in keys[a:b]] for a, b in zip(boundaries, boundaries[1:])]


def teacher_identity(source_dir, weights_dir, source_tar=None):
    root, weights = Path(source_dir).resolve(), Path(weights_dir).resolve()
    archive = Path(source_tar) if source_tar else root.with_suffix('.tar')
    source_files = {}
    with tarfile.open(archive, 'r:') as tar:
        for member in tar:
            if (not member.isfile() or not member.name.startswith('vggt/') or '..' in Path(member.name).parts
                    or member.name in source_files):
                raise ValueError('Invalid teacher source archive member')
            digest = sha256(tar.extractfile(member).read())
            deployed = root / member.name
            if recording.file_sha(deployed) != digest:
                raise ValueError('Teacher source differs from archive')
            source_files[member.name] = digest
    if not source_files or {p.relative_to(root).as_posix() for p in root.rglob('*.py')} != set(source_files):
        raise ValueError('Teacher source inventory differs from archive')
    weights_pin, archive_pin = pin(weights / 'model.safetensors'), pin(archive)
    return {'repository': c1r_ref.REPOSITORY, 'revision': c1r_ref.REVISION, 'layer': 23, 'input': c1r_ref.INPUT,
            'weights': weights_pin, 'config': pin(weights / 'config.json'),
            'source_tar': archive_pin, 'source_files': source_files,
            'weights_sha256': weights_pin['sha256'], 'source_tar_sha256': archive_pin['sha256']}


def decode_selected(source, needed, threads=4):
    """decode_pyav_pool's checks without its PNG staging: selected raw ordinals -> RGB arrays in memory.

    Every frame is decoded once and counted (the count must equal total_num_frames); no other frame is retained.
    """
    import av
    video = source['video']
    if recording.file_sha(video['path']) != video['sha256']:
        raise ValueError('Video source SHA-256 mismatch')
    selected = set(recording.frame_numbers(needed))
    numbers = recording.sparse_frames(source)
    if numbers is not None and not selected <= set(numbers):
        raise ValueError('Sparse pool includes an unposed raw frame')
    if numbers is None and source['total_num_frames'] != source['pose_count']:
        raise ValueError('Decoded frame count does not equal full-recording pose count')
    frames, count = {}, 0
    with av.open(video['path']) as container:
        if not container.streams.video:
            raise ValueError('Recording has no video stream')
        stream = container.streams.video[0]
        stream.thread_count = threads
        for number, frame in enumerate(container.decode(stream)):
            count = number + 1
            if number in selected:
                frames[number] = frame.to_ndarray(format='rgb24')
    if count != source['total_num_frames'] or len(frames) != len(selected):
        raise ValueError('Decoded frame count or selected pool does not match the recording')
    return {'decoded_frame_count': count, 'frames': frames}


def write_frames(path, row, frames):
    """Write deterministic native-raster JPEGs in an uncompressed clip archive (frames: ordinal -> RGB array)."""
    from PIL import Image
    entries, payloads = [], []
    for k, ordinal in enumerate(row['ordinals']):
        image = Image.fromarray(frames[ordinal], mode='RGB')
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=95)
        raw = output.getvalue()
        entries.append({'name': f'{k:06d}.jpg', 'sha256': sha256(raw), 'raster_hw': [image.height, image.width]})
        payloads.append(raw)
    manifest = {'schema': 'c1r-frames-v1', 'qid': row['qid'], 'ordinals': row['ordinals'], 'members': entries,
                'recording_fingerprint': row['recording_fingerprint']}
    if row.get('schema') == 'c1r-clip-row-v2':
        manifest.update(schema='c1r-frames-v2', slots=row['slots'], slot_map=row['slot_map'],
                        anchor_slots=row['anchor_slots'], viewpoints=row['viewpoints'], layout=row['layout'],
                        row_sha256=sha256(canonical(row)))
    def writer(stream):
        with tarfile.open(fileobj=stream, mode='w:', format=tarfile.USTAR_FORMAT) as tar:
            for name, raw in [*((entry['name'], raw) for entry, raw in zip(entries, payloads)),
                              ('frames.json', canonical(manifest) + b'\n')]:
                info = tarfile.TarInfo(name)
                info.size, info.mode, info.mtime = len(raw), 0o644, 0
                tar.addfile(info, io.BytesIO(raw))
    atomic(path, writer)
    return pin(path)


def verify_frames(value, row, raster_hw=None):
    from PIL import Image
    if recording.file_sha(value['path']) != value['sha256']:
        raise ValueError('Frame archive SHA-256 mismatch')
    payloads = []
    with tarfile.open(value['path'], 'r:') as tar:
        members = tar.getmembers()
        names = [f'{k:06d}.jpg' for k in range(row['N'])] + ['frames.json']
        if [m.name for m in members] != names or not all(m.isfile() for m in members):
            raise ValueError('Frame archive layout mismatch')
        manifest = json.loads(tar.extractfile('frames.json').read())
        if (manifest.get('schema') != ('c1r-frames-v2' if row.get('schema') == 'c1r-clip-row-v2' else 'c1r-frames-v1') or manifest['qid'] != row['qid']
                or manifest['ordinals'] != row['ordinals'] or len(manifest['members']) != row['N']
                or manifest['recording_fingerprint'] != row['recording_fingerprint']):
            raise ValueError('Frame archive clip binding mismatch')
        if row.get('schema') == 'c1r-clip-row-v2' and (
                any(manifest.get(k) != row[k] for k in ('slots', 'slot_map', 'anchor_slots', 'viewpoints', 'layout'))
                or manifest.get('row_sha256') != sha256(canonical(row))):
            raise ValueError('Frame archive slot binding mismatch')
        for member, entry in zip(members[:-1], manifest['members']):
            raw = tar.extractfile(member).read()
            if entry['name'] != member.name or sha256(raw) != entry['sha256']:
                raise ValueError('JPEG member SHA-256 mismatch')
            with Image.open(io.BytesIO(raw)) as image:
                image.load()
                if image.format != 'JPEG' or image.mode != 'RGB' or [image.height, image.width] != entry['raster_hw']:
                    raise ValueError('JPEG raster mismatch')
                if raster_hw is not None and list(raster_hw) != entry['raster_hw']:
                    raise ValueError('GT raster differs from native decoded raster')
            payloads.append(raw)
    return payloads


def verify_clip(entry, row, raster_hw=None):
    payloads = verify_frames(entry['frames_tar'], row, raster_hw)
    if recording.file_sha(entry['g3t']['path']) != entry['g3t']['sha256']:
        raise ValueError('Teacher cache SHA-256 mismatch')
    c1r_ref.verify_npz(entry['g3t']['path'], row, entry['frames_tar']['sha256'])
    return payloads


def close_pose_cache(cache):
    for key, value in cache.items():
        if isinstance(key, tuple) and key[0] == 'archive':
            value.close()


def processor_identity(directory):
    """Pin only the local processor assets; model tensors are not needed for CPU encoding."""
    root = Path(directory).resolve()
    names = ('config.json', 'processor_config.json', 'preprocessor_config.json', 'video_preprocessor_config.json',
             'tokenizer_config.json', 'tokenizer.json', 'special_tokens_map.json', 'chat_template.jinja',
             'chat_template.json', 'added_tokens.json', 'vocab.json', 'merges.txt')
    files = {name: recording.file_sha(root / name) for name in names if (root / name).is_file()}
    if not files or 'tokenizer_config.json' not in files:
        raise ValueError('Missing local processor assets')
    return {'schema': 'c1r-processor-v1', 'files': files, 'pixels': list(pose_samples.DEFAULT_PIXELS),
            'prompt': pose_samples.PROMPT, 'target': pose_samples.TARGET, 'spatial_merge': 2, 'temporal_patch': 2}


def processor_grid(processor, row, payloads):
    """Run the real native encoder over slot RGBs with their original timestamps."""
    from PIL import Image
    from transformers.video_utils import VideoMetadata
    distinct = []
    for raw in payloads:
        with Image.open(io.BytesIO(raw)) as image:
            distinct.append(np.asarray(image.convert('RGB')).copy())
    arrays = np.stack([distinct[k] for k in row['slot_map']])
    metadata = VideoMetadata(total_num_frames=row['total_num_frames'], fps=row['fps'],
                             frames_indices=row['slots'], width=arrays.shape[2], height=arrays.shape[1])
    if processor.video_processor.merge_size != 2 or processor.video_processor.temporal_patch_size != 2:
        raise ValueError('Processor merge geometry changed')
    batch, audit = pose_samples.encode_frames(processor, pose_samples.PROMPT, [], arrays, metadata,
                                             pose_samples.TARGET, pixels=pose_samples.DEFAULT_PIXELS)
    grid = np.asarray(audit['video_grid_thw'], dtype=np.int64).reshape(3)
    del batch
    return grid


def materialize(plan_path, plan_sha256, a1_plan, chunk, chunks, worker, workers, out,
                g3t_source, g3t_weights, deadline_seconds, *, source_tar=None, teacher_factory=None,
                processor=None, processor_factory=None):
    """Process each assigned recording once; receipts retain all errors and output pins."""
    started = time.monotonic()
    if not math.isfinite(deadline_seconds) or deadline_seconds < 0:
        raise ValueError('Expected a finite nonnegative deadline')
    deadline = started + deadline_seconds
    plan_pin = {'path': str(Path(plan_path).resolve()), 'sha256': plan_sha256}
    data = validate_plan(json.loads(read_pin(plan_pin)))
    sources = bind_sources(data, a1_plan)
    is_v2 = data['schema'] == 'c1r-clip-plan-v2'
    processor_identity_, processor_instance = None, None
    if is_v2:
        if processor is None:
            raise ValueError('Fixed-layout materialization requires --processor DIR')
        processor_identity_ = processor_identity(processor)
    if not 0 <= chunk < chunks or not 0 <= worker < workers:
        raise ValueError('Invalid worker or chunk index')
    assignments = recording_chunks(data, chunks)[chunk][worker::workers]
    root = Path(out).resolve()
    root.mkdir(parents=True, exist_ok=True)
    receipt = {'schema': 'c1r-worker-v1', 'plan': plan_pin, 'a1_plan': a1_plan,
               'chunk': chunk, 'chunks': chunks, 'worker': worker, 'workers': workers,
               'clips': [], 'failures': [], 'decode': [], 'g3t_seconds_per_n': {},
               'peak_gpu_memory_bytes': 0, 'teacher': None, 'stopped_for_deadline': False}
    if is_v2:
        receipt.update(schema='c1r-worker-v2', processor=processor_identity_, frames=data['frames'])
    receipt['stopped_for_teacher_error'] = False
    cache, teacher, timings = {}, None, defaultdict(list)
    recording.pyav_preflight()
    identity = teacher_identity(g3t_source, g3t_weights, source_tar)
    receipt['teacher'] = identity
    binding_path = root / 'binding.json'
    binding = {'schema': 'c1r-cache-binding-v1', 'teacher': identity,
               'recordings_sha256': data['recordings_sha256']}
    if is_v2:
        binding.update(schema='c1r-cache-binding-v2', plan_sha256=plan_sha256, processor=processor_identity_)
    import fcntl
    with (root / 'binding.lock').open('ab') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if binding_path.exists():
            if json.loads(binding_path.read_bytes()) != binding:
                raise ValueError('Existing cache teacher or recording binding mismatch')
        else:
            write_json(binding_path, binding)
    last_decode, last_inference = 0.0, 0.0
    try:
        for key, rows in assignments:
            if time.monotonic() + max(2, last_decode + last_inference) >= deadline:
                receipt['stopped_for_deadline'] = True
                break
            source = sources[key]
            try:
                poses = recording.load_poses(source, cache)
                todo = []
                for row in rows:
                    target = encode_target(poses, row.get('viewpoints', row['ordinals']), source)
                    del target
                    fpath = root / 'f' / row['qid'][:2] / (row['qid'] + '.tar')
                    gpath = root / 'g' / row['qid'][:2] / (row['qid'] + '.npz')
                    entry = {'i': row['i'], 'qid': row['qid'], 'recording_fingerprint': key, 'frames': row['N']}
                    if fpath.exists() and gpath.exists():
                        entry.update(frames_tar=pin(fpath), g3t=pin(gpath))
                        verify_clip(entry, row, poses['raster_hw'])
                        if is_v2:
                            with np.load(gpath, allow_pickle=False) as saved:
                                if str(saved['processor_sha256'].item()) != sha256(canonical(processor_identity_)):
                                    raise ValueError('Cache processor binding mismatch')
                        entry['reused'] = True
                        receipt['clips'].append(entry)
                    else:
                        todo.append((row, fpath, gpath, entry))
                if not todo:
                    continue
                if time.monotonic() + max(2, last_decode + last_inference) >= deadline:
                    receipt['stopped_for_deadline'] = True
                    break
                needed = sorted({ordinal for row, f, g, e in todo if not f.exists() for ordinal in row['ordinals']})
                frames = {}
                if needed:
                    t = time.monotonic()
                    staged = decode_selected(source, needed)
                    last_decode = time.monotonic() - t
                    receipt['decode'].append({'scene': source['scene'], 'recording_fingerprint': key,
                                               'seconds': last_decode, 'frames': len(needed),
                                               'decoded_frame_count': staged['decoded_frame_count']})
                    frames = staged['frames']
                for row, fpath, gpath, entry in todo:
                    if time.monotonic() + max(2, last_inference) >= deadline:
                        receipt['stopped_for_deadline'] = True
                        break
                    running_teacher = False
                    try:
                        entry['frames_tar'] = pin(fpath) if fpath.exists() else write_frames(fpath, row, frames)
                        payloads = verify_frames(entry['frames_tar'], row, poses['raster_hw'])
                        if not gpath.exists():
                            running_teacher = True
                            if teacher is None:
                                teacher = (teacher_factory or c1r_ref.Teacher)(g3t_source, g3t_weights, 'cuda')
                            t = time.monotonic()
                            if is_v2:
                                if processor_instance is None:
                                    if processor_factory is None:
                                        from .decoupled_v_run import processor_for
                                        processor_instance = processor_for(processor)
                                    else:
                                        processor_instance = processor_factory(processor)
                                grid = processor_grid(processor_instance, row, payloads)
                                arrays = teacher.extract([io.BytesIO(raw) for raw in payloads],
                                                         video_grid_thw=grid, slot_map=row['slot_map'])
                            else:
                                arrays = teacher.extract([io.BytesIO(raw) for raw in payloads])
                            last_inference = time.monotonic() - t
                            c1r_ref.validate_arrays(arrays, row['N'])
                            timings[str(row['N'])].append(last_inference)
                            arrays.update(frames_tar_sha256=np.asarray(entry['frames_tar']['sha256']),
                                          ordinals=np.asarray(row['ordinals'], dtype=np.int64), qid=np.asarray(row['qid']))
                            if is_v2:
                                target = encode_target(poses, row['viewpoints'], source)
                                arrays.update({k: np.asarray(target[k], dtype=np.bool_ if k.endswith('mask') else np.float64)
                                               for k in ('camera', 'camera_mask', 'trajectory_scale', 'gravity', 'gravity_mask')})
                                arrays.update(video_grid_thw=np.asarray(grid, dtype=np.int64),
                                              layout=np.asarray(row['layout']), row_sha256=np.asarray(sha256(canonical(row))),
                                              processor_sha256=np.asarray(sha256(canonical(processor_identity_))))
                                arrays.update({k: np.asarray(row[k], dtype=np.int64)
                                               for k in ('viewpoints', 'slots', 'slot_map', 'anchor_slots')})
                                c1r_ref.validate_cache_v2(arrays, row)
                            running_teacher = False
                            atomic(gpath, lambda stream: np.savez(stream, **arrays))
                        entry['g3t'] = pin(gpath)
                        verify_clip(entry, row, poses['raster_hw'])
                        entry.update(reused=False, g3t_seconds=last_inference)
                        receipt['clips'].append(entry)
                    except Exception as error:
                        receipt['failures'].append({'i': row['i'], 'qid': row['qid'], 'error': str(error)})
                        if running_teacher:
                            receipt['stopped_for_teacher_error'] = True
                            break
                if receipt['stopped_for_deadline'] or receipt['stopped_for_teacher_error']:
                    break
            except Exception as error:
                receipt['failures'].append({'scene': source['scene'], 'recording_fingerprint': key,
                                           'rows': [row['i'] for row in rows], 'error': str(error)})
    finally:
        close_pose_cache(cache)
    if teacher_factory is None:
        import torch
        if torch.cuda.is_initialized():
            receipt['peak_gpu_memory_bytes'] = int(torch.cuda.max_memory_allocated())
            receipt['peak_gpu_reserved_bytes'] = int(torch.cuda.max_memory_reserved())
    receipt['g3t_seconds_per_n'] = {n: {'count': len(v), 'total': sum(v), 'mean': sum(v) / len(v)} for n, v in timings.items()}
    receipt['seconds'] = time.monotonic() - started
    receipt['assigned_clips'] = sum(len(rows) for key, rows in assignments)
    receipt['complete'] = len(receipt['clips']) == receipt['assigned_clips'] and not receipt['failures']
    destination = root / 'r' / f'{chunk:04d}_{worker:04d}_{uuid.uuid4().hex}.json'
    write_json(destination, receipt)
    return pin(destination)


def worker_entries(data, plan_pin, a1_plan, worker_receipts):
    entries, failures, teachers, verified, processors = {}, [], [], set(), []
    for receipt_pin in worker_receipts:
        report = json.loads(read_pin(receipt_pin))
        if report.get('schema') != ('c1r-worker-v2' if data['schema'] == 'c1r-clip-plan-v2' else 'c1r-worker-v1') or report['plan'] != plan_pin or report['a1_plan'] != a1_plan:
            raise ValueError('Worker receipt input binding mismatch')
        if data['schema'] == 'c1r-clip-plan-v2':
            if report.get('frames') != data['frames'] or not report.get('processor'):
                raise ValueError('Worker layout or processor binding mismatch')
            if processors and processors[0] != report['processor']:
                raise ValueError('Worker processor identities differ')
            processors.append(report['processor'])
        teacher = report['teacher']
        if (teacher.get('repository') != c1r_ref.REPOSITORY or teacher.get('revision') != c1r_ref.REVISION
                or teacher.get('layer') != 23 or teacher.get('input') != c1r_ref.INPUT
                or teacher.get('weights_sha256') != teacher['weights']['sha256']
                or teacher.get('source_tar_sha256') != teacher['source_tar']['sha256']):
            raise ValueError('Worker teacher contract mismatch')
        for field in ('weights', 'config', 'source_tar'):
            key = teacher[field]['path'], teacher[field]['sha256']
            if key not in verified:
                if recording.file_sha(key[0]) != key[1]:
                    raise ValueError('Teacher input SHA-256 mismatch')
                verified.add(key)
        if teachers and teacher != teachers[0]:
            raise ValueError('Worker teacher identities differ')
        teachers.append(teacher)
        failures.extend({'worker_receipt': receipt_pin, **failure} for failure in report['failures'])
        for entry in report['clips']:
            if type(entry['i']) is not int or not 0 <= entry['i'] < len(data['rows']):
                raise ValueError('Worker receipt row index mismatch')
            if entry['i'] in entries:
                old = entries[entry['i']]
                if any(old[k] != entry[k] for k in ('qid', 'recording_fingerprint', 'frames', 'frames_tar', 'g3t')):
                    raise ValueError('Conflicting clip receipt pins')
            row = data['rows'][entry['i']]
            if (entry['qid'] != row['qid'] or entry['recording_fingerprint'] != row['recording_fingerprint']
                    or entry['frames'] != row['N']):
                raise ValueError('Worker clip identity mismatch')
            entries[entry['i']] = entry
    return entries, failures, teachers, processors


def coverage(plan_path, plan_sha256, worker_receipts, a1_plan):
    """Report the largest verified complete step prefix without building a package."""
    plan_pin = {'path': str(Path(plan_path).resolve()), 'sha256': plan_sha256}
    data = validate_plan(json.loads(read_pin(plan_pin)))
    bind_sources(data, a1_plan)
    entries, worker_failures, teachers, processors = worker_entries(data, plan_pin, a1_plan, worker_receipts)
    accepted, rejected = set(), []
    for i, entry in sorted(entries.items()):
        try:
            row = data['rows'][i]
            verify_clip(entry, row)
            if processors:
                with np.load(entry['g3t']['path'], allow_pickle=False) as saved:
                    if str(saved['processor_sha256'].item()) != sha256(canonical(processors[0])):
                        raise ValueError('Cache processor binding mismatch')
            accepted.add(i)
        except Exception as error:
            rejected.append({'i': i, 'qid': data['rows'][i]['qid'], 'error': str(error)})
    k = 0
    while k < data['steps'] and all(i in accepted for i in range(k * 32, (k + 1) * 32)):
        k += 1
    return {'schema': 'c1r-coverage-v2' if data['schema'].endswith('v2') else 'c1r-coverage-v1',
            'plan': plan_pin, 'steps_available': k, 'count': len(accepted), 'steps': data['steps'],
            'complete': k == data['steps'], 'missing': [i for i in range(len(data['rows'])) if i not in entries],
            'rejected': rejected, 'worker_failures': worker_failures}


def package(plan_path, plan_sha256, worker_receipts, a1_plan, out, prefix_steps=None):
    """Build immutable databases; report every absent or rejected row explicitly."""
    plan_pin = {'path': str(Path(plan_path).resolve()), 'sha256': plan_sha256}
    data = validate_plan(json.loads(read_pin(plan_pin)))
    sources = bind_sources(data, a1_plan)
    limit = data['steps'] if prefix_steps is None else prefix_steps
    if type(limit) is not int or not 1 <= limit <= data['steps']:
        raise ValueError('Invalid step prefix')
    root = Path(out).resolve()
    root.mkdir(parents=True, exist_ok=False)
    entries, failures, teachers, processors = worker_entries(data, plan_pin, a1_plan, worker_receipts)
    rows_tmp = root / ('rows.' + uuid.uuid4().hex + '.part')
    g3t_tmp = root / ('ref.' + uuid.uuid4().hex + '.part')
    db, gdb = sqlite3.connect(rows_tmp), sqlite3.connect(g3t_tmp)
    db.execute('PRAGMA journal_mode=MEMORY')
    gdb.execute('PRAGMA journal_mode=MEMORY')
    db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY, row TEXT NOT NULL, target TEXT NOT NULL)')
    gdb.execute('CREATE TABLE g3t(i INTEGER PRIMARY KEY, path TEXT, sha256 TEXT, frames INTEGER)')
    cache, pose_key, poses, accepted = {}, None, None, []
    per_step = Counter()
    try:
        ordered_rows = sorted(data['rows'][:limit * 32], key=lambda row: (row.get('recording_fingerprint', ''), row['i']))
        for row in ordered_rows:
            try:
                if row['pending']:
                    raise ValueError('Frame tier is pending')
                entry = entries.get(row['i'])
                if entry is None:
                    raise ValueError('Missing worker clip receipt')
                if (entry['qid'] != row['qid'] or entry['recording_fingerprint'] != row['recording_fingerprint']
                        or entry['frames'] != row['N']):
                    raise ValueError('Worker clip identity mismatch')
                key = row['recording_fingerprint']
                source = sources[key]
                if key != pose_key:
                    poses = recording.load_poses(source, cache)
                    pose_key = key
                target = encode_target(poses, row.get('viewpoints', row['ordinals']), source)
                verify_clip(entry, row, poses['raster_hw'])
                if processors:
                    with np.load(entry['g3t']['path'], allow_pickle=False) as saved:
                        if str(saved['processor_sha256'].item()) != sha256(canonical(processors[0])):
                            raise ValueError('Cache processor binding mismatch')
                record = {'schema': 'c1r-clip-row-v1', 'qid': row['qid'], 'dataset': row['dataset'],
                          'scene': row['scene'], 'step': row['step'], 'micro': row['micro'], 'rank': row['rank'],
                          'tier': row.get('tier'), 'frames': row['N'], 'mode': row['mode'], 'stride': row['stride'],
                          'gaps': row['gap_seconds'], 'fallback': row['fallback'], 'ordinals': row['ordinals'],
                          'fps': row['fps'], 'total_num_frames': row['total_num_frames'],
                          'frames_tar': entry['frames_tar'], 'augment': dict(pose_samples.AUGMENT, seed=row['augment_seed']),
                          'question': pose_samples.PROMPT, 'target': pose_samples.TARGET}
                if data['schema'] == 'c1r-clip-plan-v2':
                    record = dict(row, frames_tar=entry['frames_tar'], g3t=entry['g3t'],
                                  augment=dict(pose_samples.AUGMENT, seed=row['augment_seed']),
                                  question=pose_samples.PROMPT, options=[], target_text=pose_samples.TARGET,
                                  members=[f'{k:06d}.jpg' for k in range(row['N'])],
                                  plan_row_sha256=sha256(canonical(row)))
                db.execute('INSERT INTO rows VALUES (?, ?, ?)', (row['i'], canonical(record).decode(), canonical(target).decode()))
                gdb.execute('INSERT INTO g3t VALUES (?, ?, ?, ?)',
                            (row['i'], entry['g3t']['path'], entry['g3t']['sha256'], row['N']))
                accepted.append(row)
                per_step[row['step']] += 1
            except Exception as error:
                failures.append({'i': row['i'], 'qid': row['qid'], 'error': str(error)})
        db.commit()
        gdb.commit()
    finally:
        db.close()
        gdb.close()
        close_pose_cache(cache)
    os.rename(rows_tmp, root / 'rows.sqlite')
    os.rename(g3t_tmp, root / 'ref.sqlite')
    available = 0
    while available < limit and per_step[available] == 32:
        available += 1
    teacher = teachers[0] if teachers else None
    receipt = {'schema': 'c1r-clips-v1', 'count': len(accepted), 'steps': data['steps'], 'prefix_steps': prefix_steps,
               'steps_available': available, 'complete': prefix_steps is None and available == data['steps'] and not failures,
               'tiers': data.get('tiers'), 'curriculum': data.get('curriculum'), 'seed': data['seed'],
               'mode_probabilities': data['mode_probabilities'],
               'rows': pin(root / 'rows.sqlite'), 'g3t': pin(root / 'ref.sqlite'), 'teacher': teacher,
               'failures': failures, 'input_pins': {'plan': plan_pin, 'a1_plan': a1_plan, 'worker_receipts': worker_receipts},
               'planned_counts': data['counts'], 'planned_histograms': data['histograms']}
    if data['schema'] == 'c1r-clip-plan-v2':
        receipt.update(schema='c1r-clips-v2', frames=data['frames'], processor=processors[0] if processors else None)
        receipt.pop('tiers')
        receipt.pop('curriculum')
    receipt['skipped_recordings'] = [
        {'i': row['i'], 'base_recording': row['base_recording'], 'reason': row['recording_fallback'],
         'selected_scene': row['scene'], 'selected_fingerprint': row['recording_fingerprint']}
        for row in data['rows'][:limit * 32] if not row['pending'] and row['recording_fallback']]
    receipt.update((summarize_v2 if data['schema'] == 'c1r-clip-plan-v2' else summarize)(
        sorted(accepted, key=lambda row: row['i']), data['recordings'], data['steps']))
    write_json(root / 'receipt.json', receipt)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('plan')
    p.add_argument('--request', required=True)
    p.add_argument('--output', required=True)
    for name in ('materialize', 'package', 'coverage'):
        p = sub.add_parser(name)
        p.add_argument('--plan', required=True)
        p.add_argument('--plan-sha256', required=True)
        p.add_argument('--a1-plan', required=True)
        p.add_argument('--a1-plan-sha256', required=True)
        p.add_argument('--out', required=True)
        if name == 'materialize':
            for name_, default in (('chunk', 0), ('chunks', 1), ('worker', 0), ('workers', 1)):
                p.add_argument('--' + name_, type=int, default=default)
            p.add_argument('--processor', help='Local base processor directory; required for v2')
            p.add_argument('--ref-source', required=True)
            p.add_argument('--ref-weights', required=True)
            p.add_argument('--ref-source-tar')
            p.add_argument('--deadline-seconds', type=float, default=3300)
        else:
            p.add_argument('--worker-receipts', required=True, help='JSON list of receipt pins')
            p.add_argument('--prefix-steps', type=int)
    args = parser.parse_args(argv)
    if args.command == 'plan':
        result = plan(json.loads(Path(args.request).read_bytes()))
        write_json(args.output, result)
        print(json.dumps({'plan': pin(args.output), 'counts': result['counts']}, sort_keys=True))
        return 0
    a1 = {'path': str(Path(args.a1_plan).resolve()), 'sha256': args.a1_plan_sha256}
    if args.command == 'materialize':
        result = materialize(args.plan, args.plan_sha256, a1, args.chunk, args.chunks, args.worker, args.workers,
                             args.out, args.ref_source, args.ref_weights, args.deadline_seconds,
                             source_tar=args.ref_source_tar, processor=args.processor)
        print(json.dumps(result, sort_keys=True))
        return int(bool(json.loads(read_pin(result))['failures']))
    if args.command == 'coverage':
        result = coverage(args.plan, args.plan_sha256, json.loads(Path(args.worker_receipts).read_bytes()), a1)
        write_json(Path(args.out) / ('coverage_' + uuid.uuid4().hex + '.json'), result)
        print(json.dumps(result, sort_keys=True))
        return 0
    result = package(args.plan, args.plan_sha256, json.loads(Path(args.worker_receipts).read_bytes()),
                     a1, args.out, args.prefix_steps)
    print(json.dumps({'receipt': pin(Path(args.out) / 'receipt.json'), 'count': result['count'],
                      'steps_available': result['steps_available'], 'complete': result['complete'],
                      'failures': len(result['failures'])}, sort_keys=True))
    return int(bool(result['failures']))


if __name__ == '__main__':
    raise SystemExit(main())
