"""Frozen, ordered episode lists and nested, scene-balanced training subsets."""
import random
from collections import defaultdict, Counter
from .io import ordered_id_sha256, read_json, write_json
from .episodes import canonical_scene

def quotas(counts, n, at_least_one=False):
    if n > sum(counts.values()) or n < (len(counts) if at_least_one else 0):
        raise ValueError('Invalid sample size')
    q = {s: int(at_least_one) for s in counts}
    remaining = n - sum(q.values())
    capacities = {s: counts[s] - q[s] for s in counts}
    total = sum(capacities.values())
    ideals = {s: remaining * capacities[s] / total if total else 0 for s in counts}
    for s in counts:
        q[s] += int(ideals[s])
    order = sorted(counts, key=lambda s: (-(ideals[s] % 1), s))
    for s in order[:n-sum(q.values())]:
        q[s] += 1
    return q

def _groups(episodes, seed):
    groups = defaultdict(list)
    for e in sorted(episodes, key=lambda e: int(e.episode_id)):
        groups[e.scene].append(e)
    rng = random.Random(seed)
    for s in sorted(groups):
        rng.shuffle(groups[s])
    return dict(groups)

def interleave(groups):
    n = sum(map(len, groups.values()))
    used = Counter()
    out = []
    for k in range(n):
        s = min((s for s in groups if used[s] < len(groups[s])),
                key=lambda s: (-(len(groups[s])*(k+1)/n-used[s]), s))
        out.append(groups[s][used[s]])
        used[s] += 1
    return out

def balanced(episodes, n, seed=0):
    groups = _groups(episodes, seed)
    q = quotas({s: len(v) for s, v in groups.items()}, n)
    return interleave({s: groups[s][:q[s]] for s in groups})

def subsets(episodes, seed=0, small=108, large=1082):
    groups = _groups(episodes, seed)
    counts = {s: len(v) for s, v in groups.items()}
    lo = quotas(counts, small, True)
    # Allocate the larger set from remaining capacities so nesting is guaranteed.
    extra = quotas({s: counts[s]-lo[s] for s in counts}, large-small)
    return (interleave({s: groups[s][:lo[s]] for s in groups}),
            interleave({s: groups[s][:lo[s]+extra[s]] for s in groups}))

def manifest(name, episodes, **metadata):
    ids = [e.episode_id for e in episodes]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate ids')
    return dict(name=name, ids=ids, ordered_id_sha256=ordered_id_sha256(ids),
                hash_encoding='UTF-8 ids with trailing LF',
                records=[dict(position=i, episode_id=e.episode_id, scene=e.scene,
                              trajectory_id=e.trajectory_id) for i, e in enumerate(episodes)],
                scene_counts=dict(Counter(e.scene for e in episodes)), **metadata)

def verify_manifest(data, episodes):
    by_id = {e.episode_id: e for e in episodes}
    ids = [str(x) for x in data['ids']]
    if len(set(ids)) != len(ids) or ordered_id_sha256(ids) != data['ordered_id_sha256']:
        raise ValueError('Invalid list hash or duplicate ids')
    if len(data['records']) != len(ids):
        raise ValueError('Missing list records')
    for i, (key, row) in enumerate(zip(ids, data['records'])):
        e = by_id[key]
        if (row['position'], str(row['episode_id']), canonical_scene(row['scene']), str(row['trajectory_id'])) != (
                i, key, canonical_scene(e.scene), e.trajectory_id):
            raise ValueError('List position, scene or trajectory mismatch')
    return [by_id[k] for k in ids]

def load_rand100(path, episodes):
    """An external id file must supply position, scene and trajectory for every id."""
    if path is None:
        raise FileNotFoundError('BLOCKED_IDS_MISSING: MIP OpenNav-100 id list')
    data = read_json(path)
    if isinstance(data, list):
        data = dict(records=data, ids=[str(r['episode_id']) for r in data])
        data['ordered_id_sha256'] = ordered_id_sha256(data['ids'])
    out = verify_manifest(data, episodes)
    if len(out) != 100:
        raise ValueError('OpenNav-100 must have exactly 100 episodes')
    return out

def select_pairs(pairs, n=300, seed=0):
    ids = sorted(pairs, key=int)
    random.Random(seed).shuffle(ids)
    return [pairs[k] for k in ids[:n]]
