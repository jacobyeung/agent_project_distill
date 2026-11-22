"""NF-A item rule, fixed before any run (rule tag nfa-v1).

Source: the 636 dev-S1 routed items of package b9ef552934627 (payload items/devs1_routed.json)
and the executed order of job 171253 read 0 (return c82cb20f, journals in STEPS order).
Rule:
 1. Types: camera_displacement, camera_rotation, camera_movement_direction, object_abs_distance.
 2. 150 items to types in proportion to their counts, largest remainder; equal remainders go to the
    smaller sha256("nfa-v1|type|"+type).
 3. Within a type, items to datasets in proportion, largest remainder; equal remainders go to the
    smaller sha256("nfa-v1|"+type+"|"+dataset).
 4. Within a (type, dataset) stratum, the items with the smallest sha256("nfa-v1|"+item_id).
 5. Production order = job 171253 read 0's executed order restricted to the chosen items;
    reverse = that list reversed.
"""
import argparse
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

TAG = 'nfa-v1'
TYPES = ('camera_displacement', 'camera_rotation', 'camera_movement_direction', 'object_abs_distance')
TOTAL = 150
ITEMS_SHA = '2849206e3eb66f40b3e2fba49cfe84abe3c0465a318f85aaeaeca6ff6f26fe21'  # payload items/devs1_routed.json of b9ef552934627
ORDER = ('camera_displacement', 'camera_rotation', 'camera_movement_direction',
         'object_abs_distance', 'room_size_estimation')


def h(text):
    return hashlib.sha256(text.encode()).hexdigest()


def largest_remainder(counts, total, tie):
    """counts: {key: n}. Returns {key: allocation}; ties broken by tie(key) ascending."""
    whole = sum(counts.values())
    quotas = {k: Fraction(n * total, whole) for k, n in counts.items()}
    alloc = {k: int(q) for k, q in quotas.items()}
    left = total - sum(alloc.values())
    ranked = sorted(counts, key=lambda k: (-(quotas[k] - alloc[k]), tie(k)))
    for k in ranked[:left]:
        alloc[k] += 1
    return alloc


def choose(items):
    pool = [r for r in items if r['question_type'] in TYPES]
    by_type = Counter(r['question_type'] for r in pool)
    per_type = largest_remainder(dict(by_type), TOTAL, lambda t: h(f'{TAG}|type|{t}'))
    chosen, strata = [], []
    for t in TYPES:
        rows = [r for r in pool if r['question_type'] == t]
        ds = Counter(r['dataset'] for r in rows)
        per_ds = largest_remainder(dict(ds), per_type[t], lambda d, t=t: h(f'{TAG}|{t}|{d}'))
        for d in sorted(per_ds):
            stratum = sorted((r for r in rows if r['dataset'] == d), key=lambda r: h(f"{TAG}|{r['id']}"))
            picked = stratum[:per_ds[d]]
            chosen.extend(picked)
            strata.append(dict(type=t, dataset=d, available=ds[d], chosen=len(picked)))
    return chosen, per_type, strata


def production_order(journal_root):
    """Executed order of read 0: worker STEPS type sequence, then each type journal's line order."""
    root = Path(journal_root)
    # The worker's --types order is recorded in the read's 30.json (config['types']).
    worker = json.loads((root.parent / 'a' / '30.json').read_text())
    kinds = worker['config']['types']
    order = []
    for kind in kinds:
        t = ORDER.index(kind)
        with (root / str(t) / '0' / 'items.jsonl').open() as f:
            order.extend(json.loads(line)['id'] for line in f)
    return kinds, order


def build(items_path, journal_root):
    raw = Path(items_path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != ITEMS_SHA:
        raise ValueError('item source differs from the pinned b9ef552934627 manifest')
    manifest = json.loads(raw)
    items = manifest['items']
    chosen, per_type, strata = choose(items)
    ids = {r['id'] for r in chosen}
    kinds, executed = production_order(journal_root)
    forward = [i for i in executed if i in ids]
    if len(forward) != TOTAL or set(forward) != ids:
        raise ValueError('production order does not cover the chosen items')
    reverse = forward[::-1]
    index = {r['id']: n for n, r in enumerate(items)}
    by_id = {r['id']: r for r in items}
    counts = Counter((by_id[i]['question_type'], by_id[i]['dataset']) for i in forward)
    return dict(
        schema='nfa-items-v1', rule=TAG, total=TOTAL, types=list(TYPES),
        source=dict(items_sha256=hashlib.sha256(raw).hexdigest(), item_set_sha256=manifest['item_set_sha256'],
                    count=manifest['count'], job=171253, read=0, executed_type_sequence=kinds),
        per_type=per_type, strata=strata,
        per_type_dataset={f'{t}|{d}': n for (t, d), n in sorted(counts.items())},
        forward_ids=forward, reverse_ids=reverse,
        forward_indices=[index[i] for i in forward],
        forward_types=[by_id[i]['question_type'] for i in forward],
        forward_datasets=[by_id[i]['dataset'] for i in forward],
        forward_rooms=[by_id[i]['room_key'] for i in forward],
        forward_ids_sha256=h(json.dumps(forward)), reverse_ids_sha256=h(json.dumps(reverse)),
        forward_type_sequence=[t for t in kinds if t in TYPES],
        reverse_type_sequence=[t for t in kinds if t in TYPES][::-1])


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--items', required=True)
    p.add_argument('--journals', required=True, help='return metadata/reads/0/metadata/journals')
    p.add_argument('--out', required=True)
    a = p.parse_args()
    value = build(a.items, a.journals)
    Path(a.out).write_text(json.dumps(value, indent=1, sort_keys=True) + '\n')
    print(json.dumps(dict(per_type=value['per_type'], per_type_dataset=value['per_type_dataset'],
                          forward_ids_sha256=value['forward_ids_sha256'])))
