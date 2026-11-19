"""Pinned R1 cell allocation and deterministic native-reader plans."""
from fractions import Fraction
from collections import Counter
import random
from .p3_provenance import digest, load, pinned
from .r1_training import STREAMS


def allocate(card, counts):
    if card.get('schema') != 'r1-card-v1' or card.get('steps') != 1000 or card.get('quotas') != STREAMS:
        raise ValueError('R1_CARD_INVALID')
    cells = [dict(c) for c in card['cells']]
    # SIZE-V is one parameter; its released slots remain in the direction cell.
    if 'size_rows_per_step' in card:
        size = next(c for c in cells if c['type']=='object_size')
        direction = next(c for c in cells if c['type']=='direction')
        desired = Fraction(str(card['size_rows_per_step']))
        direction['rows_per_step'] = str(Fraction(str(direction['rows_per_step'])) + Fraction(str(size['rows_per_step'])) - desired)
        size['rows_per_step'] = str(desired)
    if len({c['type'] for c in cells}) != len(cells) or set(counts) != {c['type'] for c in cells}:
        raise ValueError('R1_CELL_POPULATION_MISMATCH')
    if any(type(n) is not int or n < 0 for n in counts.values()):
        raise ValueError('R1_POPULATION_INVALID')
    requested = {c['type']: int(Fraction(str(c['rows_per_step']))*1000) for c in cells}
    if any(n < 0 for n in requested.values()):
        raise ValueError('R1_NEGATIVE_CELL')
    totals = {k: min(n, 4*counts[k]) for k, n in requested.items()}
    cuts = {k: dict(requested=requested[k], admitted=n, eligible=counts[k], ceiling=4*counts[k])
            for k, n in totals.items() if n < requested[k]}
    for stream, quota in STREAMS.items():
        names = [c['type'] for c in cells if c['stream'] == stream]
        if sum(requested[k] for k in names) != quota*1000:
            raise ValueError('R1_CARD_QUOTA_MISMATCH:'+stream)
        deficit = quota*1000 - sum(totals[k] for k in names)
        recipients = ['direction'] if stream == 'vqa' else (
            ['camera_displacement','camera_movement_direction','camera_rotation','absolute_distance']
            if stream == 'routing' else names)
        original = dict(totals)
        for _ in range(deficit):
            available = [k for k in recipients if totals[k] < 4*counts[k]]
            if not available:
                raise ValueError('R1_POST_FILTER_CAPACITY_SHORTFALL:'+stream)
            # Largest proportional deficit allocates only the released stream slots.
            key = max(available, key=lambda k: (Fraction(requested[k], max(1, sum(requested[j] for j in recipients)))
                                                *deficit - (totals[k]-original[k]), k))
            totals[key] += 1
    return dict(draws=totals, cuts=cuts, eligible=counts,
                repeats={k: totals[k]/counts[k] if counts[k] else 0 for k in totals})


def validate_binding(binding):
    card = load(pinned(binding['card']))
    population = load(pinned(binding['population']))
    indices = load(pinned(binding['indices']))
    if (population.get('schema') != 'r1-population-v1' or population.get('complete') is not True
            or population.get('after_all_filters') is not True or not population.get('evidence')
            or population.get('card_sha256') != binding['card']['sha256']
            or indices.get('population_sha256') != binding['population']['sha256']):
        raise ValueError('R1_COMPLETE_FILTERED_POPULATION_REQUIRED')
    for pin in population['evidence']:
        pinned(pin)
    proof = allocate(card, population['counts'])
    if set(indices.get('cells', {})) != set(proof['draws']):
        raise ValueError('R1_INDICES_DIFFER')
    return card, indices, proof


def plans(binding, counts, steps, start_step=0, world=4):
    card, indices, proof = validate_binding(binding)
    if world != 4 or not 0 <= start_step <= steps <= 1000:
        raise ValueError('R1_PLAN_POSITION_INVALID')
    pools, used = {}, {s:set() for s in STREAMS}
    for cell in card['cells']:
        kind, stream = cell['type'], cell['stream']
        values = indices['cells'][kind]
        if (len(values) != proof['eligible'][kind] or len(set(values)) != len(values)
                or any(type(i) is not int or not 0 <= i < counts[stream] for i in values)
                or used[stream] & set(values)):
            raise ValueError('R1_INDEX_OVERLAP_OR_COUNT')
        used[stream].update(values)
        pools[kind] = list(values)
        random.Random(card['seed']).shuffle(pools[kind])
    if any(len(used[s]) != counts[s] for s in STREAMS):
        raise ValueError('R1_INDEX_COVERAGE')
    schedules = {}
    if 'direction_prior' in binding:
        from .r1_direction_prior import schedules as prior_schedules
        schedules = prior_schedules(binding, card, indices, proof, pools)
    consumed = Counter()
    totals = proof['draws']
    for step in range(steps):
        plan = []
        for stream, quota in STREAMS.items():
            names = [c['type'] for c in card['cells'] if c['stream'] == stream and totals[c['type']] > 0]
            selected = []
            for _ in range(quota):
                available = [k for k in names if consumed[k] < totals[k]]
                kind = max(available, key=lambda k: (totals[k]*(step+1)-consumed[k]*1000, k))
                pool = pools[kind]
                selected.append(schedules[kind][consumed[kind]] if kind in schedules
                                else pool[consumed[kind] % len(pool)])
                consumed[kind] += 1
            plan.extend((stream, selected[i:i+world]) for i in range(0, quota, world))
        if step >= start_step:
            yield plan
