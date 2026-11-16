"""Fixed subset lists for one LIBERO suite, with make_libero_subset.py's selection rule (env lane, 2026-10-29):
group episodes by instruction, sort tasks by instruction string, and draw random.Random(seed).sample(pool, min(K, len(pool)))
per task from the pool sorted by episode_index. Writes a build_subset.py spec.
usage: make_spec.py episodes.jsonl K SEED OUT [SOURCE]   (SOURCE = <repo>@<revision>, recorded in the spec)"""
import collections, json, random, sys
eps = [json.loads(l) for l in open(sys.argv[1])]
k, seed, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
source = sys.argv[5] if len(sys.argv) > 5 else "IPEC-COMMUNITY/libero_spatial_no_noops_1.0.0_lerobot@bf14d6258218d12c2e3c1a3b9922e163cdf6455d"
by_task = collections.defaultdict(list)
for e in eps:
    by_task[e['tasks'][0]].append(e)
assert len(by_task) == 10, len(by_task)
rng = random.Random(seed); chosen = []; per_task = {}
for t in sorted(by_task):
    pool = sorted(by_task[t], key=lambda e: e['episode_index'])
    pick = rng.sample(pool, min(k, len(pool)))
    chosen += pick; per_task[t] = sorted(e['episode_index'] for e in pick)
spec = {"demos_per_task": k, "seed": seed, "episodes": sorted(e['episode_index'] for e in chosen),
        "frames": sum(e['length'] for e in chosen), "per_task": per_task, "source": source}
json.dump(spec, open(out, 'w'), indent=1)
print(out, len(spec['episodes']), 'episodes', spec['frames'], 'frames', 'tasks', {t[:40]: len(v) for t, v in per_task.items()})
