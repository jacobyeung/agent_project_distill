"""AWS manifest closure and official-5130 adapter; no media/model reads."""
from collections import defaultdict
import json
from pathlib import Path
import random
from .items import pinned, read_rows, index_rows
from .official import VSI_PRIMARY_GROUPS, build_prompt_context

OFFICIAL_SHA = 'd69dfb86'  # Full digest is bound by the binder from the supplied file.
GEN_SHA = '7167390bec007be66c4b2a55eecf08838394221fcddfaf4cefe70b86999ee947'
SCO_SHA = '1c35feb7dc597379c0983e922dcc46975d3dbf99dd246188cdf19e48e33d75d2'


def map_path(path, roots):
    for old, new in sorted(roots.get('path_map', {}).items(), key=lambda v: -len(v[0])):
        if path == old or path.startswith(old.rstrip('/') + '/'):
            return new.rstrip('/') + path[len(old):]
    if path.startswith('/data2/') and roots.get('data2_root'):
        return roots['data2_root'].rstrip('/') + path[len('/data2'):]
    return path


def child_pin(value, parent, roots):
    path = map_path(value['path'], roots)
    if not Path(path).is_absolute():
        path = str(Path(parent['path']).parent / path)
    return dict(path=path, sha256=value['sha256'])


def resolve_spec(spec, roots):
    if not spec.get('generation_manifest'):
        return spec
    gen, sco = spec['generation_manifest'], spec['scoring_manifest']
    if gen['sha256'] != GEN_SHA or sco['sha256'] != SCO_SHA:
        raise ValueError('Require the exact v3 release manifests')
    generation = json.loads(pinned(gen).read_text())
    scoring = json.loads(pinned(sco).read_text())
    if (generation['schema'] != 'student-generation-manifest-v1' or
            scoring['schema'] != 'student-scoring-manifest-v1' or
            scoring['generation']['sha256'] != gen['sha256'] or
            generation['expected_count'] != 450 or scoring['expected_count'] != 450 or
            generation['ordered_ids'] != scoring['ordered_ids']):
        raise ValueError('Prepared release closure differs')
    rows = child_pin(generation['inputs'], gen, roots)
    labels = child_pin(scoring['labels'], sco, roots)
    if set(index_rows(read_rows(rows))) != set(map(str, generation['ordered_ids'])):
        raise ValueError('Prepared release membership differs')
    if spec.get('rows') and spec['rows'] != rows:
        raise ValueError('Explicit inputs differ from manifest')
    if spec.get('labels') and spec['labels'] != labels:
        raise ValueError('Explicit labels differ from manifest')
    return {**spec, 'rows': rows, 'labels': labels}


def stratified(rows, count, seed=17):
    if count is None:
        return rows
    if type(count) is not int or not 1 <= count <= len(rows):
        raise ValueError('Invalid official sample size')
    groups = defaultdict(list)
    for row in rows:
        found = [g for g, types in VSI_PRIMARY_GROUPS.items() if row['question_type'] in types]
        if len(found) != 1:
            raise ValueError('Unknown official task group')
        groups[found[0]].append(row)
    if set(groups) != set(VSI_PRIMARY_GROUPS):
        raise ValueError('Official task groups incomplete')
    # Proportional largest-remainder allocation; deterministic ties and draws.
    minimum = int(count >= len(groups))
    remaining = count-minimum*len(groups)
    capacity = {g: len(v)-minimum for g,v in groups.items()}
    total = sum(capacity.values())
    quotas = {g: minimum + remaining*capacity[g]//total for g in groups}
    order = sorted(groups, key=lambda g: (-(remaining*capacity[g] % total), g))
    for g in order[:count-sum(quotas.values())]:
        quotas[g] += 1
    rng = random.Random(seed)
    sampled = []
    for group in sorted(groups):
        candidates = sorted(groups[group], key=lambda r: str(r['id']))
        sampled.extend(rng.sample(candidates, quotas[group]))
    return sorted(sampled, key=lambda r: str(r['id']))


def dev_rows(spec, roots):
    rows = read_rows(spec['rows'])
    if len(index_rows(rows)) != len(rows):
        raise ValueError('Dev rows must be distinct')
    result = []
    for row in sorted(rows, key=lambda r: str(r['id'])):
        task = {**row, 'example_id': str(row['id']), 'benchmark': 'devrows', 'options': row.get('options') or []}
        task['video_path'] = str(Path(roots['video_root']) / row['dataset'] / (row['scene_name'] + '.mp4'))
        build_prompt_context(task, 'ours')
        result.append(task)
    return result


def official_rows(spec, roots):
    rows = read_rows(spec['rows'])
    if len(rows) != 5130 or len(index_rows(rows)) != 5130:
        raise ValueError('Official metadata must contain exactly 5130 distinct items')
    result = []
    for row in stratified(rows, spec.get('slice'), spec.get('seed', 17)):
        task = {**row, 'example_id': str(row['id']), 'benchmark': 'official5130',
                'options': row.get('options') or []}
        task['video_path'] = str(Path(roots['video_root']) / row['dataset'] / (row['scene_name'] + '.mp4'))
        build_prompt_context(task, 'ours')
        result.append(task)
    return result
