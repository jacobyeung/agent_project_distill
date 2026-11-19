"""Room populations from explicit manifest membership, never item-name heuristics."""
from bootstrap import bootstrap
from measurements import summarize

ROOM = 'room_size_estimation'
POPULATIONS = ('dev-S1', 'R0-dev')


def tag_items(manifest):
    items = {i['id']: dict(i) for i in manifest['items']}
    memberships = {}
    for population in POPULATIONS:
        ids = manifest.get('sets', {}).get(population, [])
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate population membership: ' + population)
        for key in ids:
            if key not in items:
                raise ValueError('Population member absent from manifest: ' + key)
            if key in memberships:
                raise ValueError('Conflicting population membership: ' + key)
            memberships[key] = population
    for key, item in items.items():
        if item['question_type'] != ROOM:
            continue
        labels = {item[field] for field in ('population', 'r0_split', 'split')
                  if item.get(field) in POPULATIONS}
        if key in memberships:
            labels.add(memberships[key])
        if len(labels) > 1:
            raise ValueError('Conflicting population tags: ' + key)
        item['_population'] = next(iter(labels), None)
    return items


def inherit_tags(items, catalog, check_pair_items):
    """Join only exact item identities; a dataset or ID prefix is not a split."""
    shared = {k for k in items.keys() & catalog.keys() if items[k]['question_type'] == ROOM}
    check_pair_items({k:items[k] for k in shared}, {k:catalog[k] for k in shared})
    for key in shared:
        left, right = items[key].get('_population'), catalog[key].get('_population')
        if left and right and left != right:
            raise ValueError('Paired population differs: ' + key)
        if right:
            items[key]['_population'] = right


def room_mra(per_item, items):
    if not any(i['question_type'] == ROOM for side in items.values() for i in side.values()):
        return {}
    result = {}
    labels = ['all', *POPULATIONS]
    if any(i['question_type'] == ROOM and not i.get('_population')
           for side in items.values() for i in side.values()):
        labels.append('MISSING')
    for label in labels:
        selected, row = {}, {}
        for side in ('a', 'b'):
            ids = {k for k, i in items[side].items() if i['question_type'] == ROOM
                   and (label == 'all' or (i.get('_population') or 'MISSING') == label)}
            selected[side] = {k:v for k,v in per_item[side].items() if k in ids}
            summary = summarize(list(selected[side].values()), ids)
            row[side] = {k:summary[k] for k in ('n', 'expected', 'missing_ids', 'status')}
            row[side].update(mra_answer=summary['score'], mra_answer_status=summary['score_status'])
        a, b = selected['a'], selected['b']
        shared = sorted(a.keys() & b.keys())
        pairs = [(a[k]['room'], 100*(a[k]['score']-b[k]['score'])) for k in shared
                 if a[k]['score'] is not None and b[k]['score'] is not None]
        row['paired'] = {**bootstrap(pairs), 'status':'OK' if pairs else 'MISSING',
                         'a_only_ids':sorted(a.keys()-b.keys()), 'b_only_ids':sorted(b.keys()-a.keys())}
        result[label] = row
    return result
