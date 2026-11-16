"""Metadata-first allocation under sealed stream quotas; no answer statistics."""
from fractions import Fraction
import random
from .p3_provenance import digest, load, pinned
from .r2_exclusions import SEALED
from .r2_withheld import SHA256 as WITHHELD_SHA256
from .r2_portable import bound

# The plan's section 4 weights. D0 places the final direct cell in VQA.
VQA = [('direction', '29.3'), ('facing_pairs', '29.4'), ('relative_distance', '24.6'),
       ('object_size', '11.7'), ('counting', '9.6'), ('totals', '1.5'),
       ('appearance_order', '15.6'), ('box_3d', '4.8'), ('room_size', '1.5'), ('route_planning', '10.5')]
ROUTING = [('camera_displacement', '14.5'), ('camera_movement_direction', '12.7'),
           ('camera_rotation', '9.5'), ('absolute_distance', '12.4'), ('recovery', '2.0'), ('units', '2.4')]
STEPS = 1000


def table(fallback=False):
    cells = []
    for stream, weights, quota in [('vqa', VQA, 128), ('routing', ROUTING, 64),
                                  ('pose', [('pose', '64')], 60 if fallback else 64),
                                  ('pointing', [('pointing','32')], 36 if fallback else 32)]:
        total = sum(Fraction(w) for _, w in weights)
        for kind, weight in weights:
            share = Fraction(weight)*quota/total
            cells.append(dict(type=kind, stream=stream, rows_per_step=float(share),
                numerator=share.numerator, denominator=share.denominator, plan_rows_per_step=float(weight),
                plan_stream='routing' if kind == 'route_planning' else stream,
                form='simulated-miss recovery' if kind == 'recovery' else 'program with GT response' if stream == 'routing'
                     else 'direct qualitative' if stream == 'vqa' else 'perception'))
    return dict(schema='r2-mix-v1', steps=STEPS, world=4, rows_per_rank=72, global_batch=288,
                quotas=dict(vqa=128, routing=64, pose=60 if fallback else 64, pointing=36 if fallback else 32),
                fallback=fallback, cells=cells, route_planning_stream='vqa', mdg=False)


def validate_table(value):
    if value != table(value.get('fallback', False)):
        raise ValueError('Mix differs from the bound allocation')
    return value


def allocation(value):
    """Exact registered-run totals, with paired rows allocated as indivisible twins."""
    validate_table(value)
    result = {}
    for stream, quota in value['quotas'].items():
        cells = [c for c in value['cells'] if c['stream'] == stream]
        desired = {c['type']: Fraction(c['numerator'], c['denominator'])*value['steps'] for c in cells}
        totals = {k: int(v)//(2 if k == 'facing_pairs' else 1)*(2 if k == 'facing_pairs' else 1) for k,v in desired.items()}
        while sum(totals.values()) < quota*value['steps']:
            remaining = quota*value['steps']-sum(totals.values())
            key = max((k for k in totals if k != 'facing_pairs' or remaining >= 2), key=lambda k: (desired[k]-totals[k], k))
            totals[key] += 2 if key == 'facing_pairs' else 1
        result.update(totals)
    return result


def preflight(mix_pin, counts_pin, *, source_presence=None, root=None):
    mix = validate_table(load(bound(mix_pin, root)))
    counts = load(bound(counts_pin, root))
    if (counts.get('schema') != 'r2-filtered-counts-v1' or counts.get('after_filtering') is not True
            or counts.get('mix_sha256') != mix_pin['sha256'] or not counts.get('receipts')):
        raise ValueError('Mix needs complete post-filter metadata before materialization')
    reconciled = {}
    for pin in counts['receipts']:
        receipt = load(bound(pin, root))
        if (receipt.get('schema') != 'r2-filtered-population-v1' or receipt.get('complete') is not True
                or receipt.get('exclusions') != SEALED or receipt.get('withheld_sha256') != WITHHELD_SHA256
                or not receipt.get('cells')):
            raise ValueError('Population receipt lacks complete filtering evidence')
        for kind, count in receipt['cells'].items():
            if type(count) is not int or count < 0:
                raise ValueError('Invalid filtered population count')
            reconciled[kind] = reconciled.get(kind,0)+count
    if reconciled != counts.get('cells'):
        raise ValueError('Post-filter counts differ from their receipts')
    if mix['fallback']:
        presence = load(bound(source_presence, root)) if source_presence else {}
        if presence.get('schema') != 'r2-frame-host-presence-v1' or presence.get('second_pose_source') != 'absent':
            raise ValueError('Fallback requires the frame host to find the second source absent')
    totals = allocation(mix)
    if set(counts.get('cells', {})) != set(totals):
        raise ValueError('Mix has missing or foreign cells')
    repeats = {}
    for kind, draws in totals.items():
        population = counts['cells'][kind]
        if type(population) is not int or population <= 0:
            raise ValueError('Empty or invalid mix cell: '+kind)
        repeats[kind] = draws/population
        if repeats[kind] > 4:
            raise ValueError('Cell exceeds 4.0 repeats: '+kind)
    return dict(mix_sha256=mix_pin['sha256'], counts_sha256=counts_pin['sha256'], draws=totals, repeats=repeats)


def check_route_rows(rows, allowed_scenes):
    seen = set()
    for row in rows:
        if (row['qid'] in seen or row['dataset']+'/'+row['scene'] not in allowed_scenes
                or row.get('question_type') != 'route_planning' or row.get('events')
                or not row.get('student_input', {}).get('frames')):
            raise ValueError('Direct route rows require unique QIDs, VQA scenes and mapped frames')
        seen.add(row['qid'])
    return len(seen)


def check_actual(items, binding):
    from collections import Counter
    mix = validate_table(load(bound(binding['mix_pin'], binding.get('root'))))
    counts = Counter()
    streams = {c['type']:c['stream'] for c in mix['cells']}
    for item in items:
        cell = (item.get('mix_cell') or {}).get('type')
        if streams.get(cell) != item['stream']:
            raise ValueError('Missing or wrong final mix-cell membership')
        counts[cell] += 1
    for cell, draws in allocation(mix).items():
        if counts[cell] == 0:
            raise ValueError('Empty or invalid mix cell: '+cell)
        if draws/counts[cell] > 4:
            raise ValueError('Cell exceeds 4.0 repeats: '+cell)
    return dict(counts)


def reindex(items, binding, output):
    """Bind exact native-reader offsets after every row-level admission decision."""
    from collections import Counter
    from pathlib import Path
    from .p3_provenance import file_pin, write
    mix_pin = file_pin(bound(binding['mix_pin'], binding.get('root')))
    mix = validate_table(load(mix_pin['path']))
    streams = {c['type']: c['stream'] for c in mix['cells']}
    groups = {kind: [] for kind in streams}
    offsets, cells, pairs = Counter(), Counter(), {}
    for item in items:
        assignment = item.get('mix_cell') or {}
        kind, stream = assignment.get('type'), item['stream']
        if streams.get(kind) != stream:
            raise ValueError('Missing or wrong final mix-cell membership')
        index = offsets[stream]
        offsets[stream] += 1
        cells[kind] += 1
        if kind == 'facing_pairs':
            pair = assignment.get('pair')
            if not pair:
                raise ValueError('Missing final facing pair identity')
            pairs.setdefault(pair, []).append(index)
        else:
            groups[kind].append(index)
    if any(len(pair) != 2 for pair in pairs.values()):
        raise ValueError('Late refusal leaves an incomplete facing pair')
    groups['facing_pairs'] = list(pairs.values())
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    previous = load(bound(binding['counts_pin'], binding.get('root')))
    population = dict(schema='r2-filtered-population-v1', complete=True, exclusions=SEALED,
                      withheld_sha256=WITHHELD_SHA256, cells=dict(cells),
                      parent_counts_sha256=binding['counts_pin']['sha256'], after_frame_resolution=True)
    if 'merged_dev' in previous:
        population['merged_dev'] = previous['merged_dev']
    write(output/'p.json', population)
    counts = dict(schema='r2-filtered-counts-v1', after_filtering=True, mix_sha256=mix_pin['sha256'],
                  receipts=[file_pin(output/'p.json')], cells=dict(cells))
    if 'merged_dev' in previous:
        counts['merged_dev'] = previous['merged_dev']
    write(output/'c.json', counts)
    write(output/'i.json', dict(schema='r2-type-indices-v1', counts_sha256=file_pin(output/'c.json')['sha256'], cells=groups))
    result = dict(mix=mix_pin, counts=file_pin(output/'c.json'), indices=file_pin(output/'i.json'))
    if binding.get('source_presence'):
        result['source_presence'] = file_pin(bound(binding['source_presence'], binding.get('root')))
    preflight(result['mix'], result['counts'], source_presence=result.get('source_presence'))
    return result


def plans(binding, counts, steps, start_step=0, world=4):
    """Native microbatch plans from pinned final-reader indices; pairs share a step."""
    root = '.' if binding.get('portable') else None
    proof = preflight(binding['mix'], binding['counts'], source_presence=binding.get('source_presence'), root=root)
    mix = load(bound(binding['mix'], root))
    groups = load(bound(binding['indices'], root))
    populations = load(bound(binding['counts'], root))['cells']
    if (world != mix['world'] or steps > mix['steps'] or not 0 <= start_step <= steps
            or groups.get('schema') != 'r2-type-indices-v1' or groups.get('counts_sha256') != proof['counts_sha256']
            or set(groups.get('cells', {})) != set(populations)):
        raise ValueError('Native type index binding differs')
    pools, used = {}, {s:set() for s in mix['quotas']}
    for cell in mix['cells']:
        kind, stream = cell['type'], cell['stream']
        pool = groups['cells'][kind]
        flat = [i for pair in pool for i in pair] if kind == 'facing_pairs' else pool
        if (len(flat) != populations[kind] or len(set(flat)) != len(flat)
                or any(type(i) is not int or not 0 <= i < counts[stream] for i in flat)
                or used[stream] & set(flat) or kind == 'facing_pairs' and any(len(pair) != 2 for pair in pool)):
            raise ValueError('Type indices overlap, are empty or differ from counts')
        used[stream].update(flat)
        pools[kind] = list(pool)
        random.Random(17).shuffle(pools[kind])
    if any(len(used[s]) != counts[s] for s in used):
        raise ValueError('Type indices do not cover the native reader')
    consumed = {k:0 for k in pools}
    totals = proof['draws']
    for step in range(steps):
        plan=[]
        for stream,quota in mix['quotas'].items():
            names=[c['type'] for c in mix['cells'] if c['stream']==stream]
            selected=[]
            while len(selected) < quota:
                remaining=quota-len(selected)
                kind=max((k for k in names if k!='facing_pairs' or remaining>=2),
                         key=lambda k: (totals[k]*(step+1)-consumed[k]*mix['steps'], k))
                unit=2 if kind=='facing_pairs' else 1
                pool=pools[kind]
                index=(consumed[kind]//unit)%len(pool)
                selected.extend(pool[index] if unit==2 else [pool[index]])
                consumed[kind]+=unit
            plan.extend((stream,selected[i:i+world]) for i in range(0,quota,world))
        if step >= start_step:
            yield plan
