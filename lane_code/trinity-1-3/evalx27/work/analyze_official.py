"""Summarize the returned official six-task read from report/B*.json only (reviewer R1)."""
import json, sys
from collections import defaultdict
from pathlib import Path

P = Path(sys.argv[1])  # extracted packet dir
F17 = {'object_counting': 67.3, 'object_size_estimation': 71.5, 'object_rel_distance': 58.3,
       'object_rel_direction': 74.7, 'route_planning': 57.7, 'obj_appearance_order': 64.1}
NAMES = {'object_counting': 'Counting', 'object_size_estimation': 'Object size', 'object_rel_distance': 'Relative distance',
         'object_rel_direction': 'Relative direction', 'route_planning': 'Route planning', 'obj_appearance_order': 'Appearance order'}
DIR = ('object_rel_direction_easy', 'object_rel_direction_medium', 'object_rel_direction_hard')
SHARED = ('arkitscenes', '41159525')


def grouped(rows, drop=None):
    by = defaultdict(list)
    for r in rows:
        if drop and (r['dataset'], r['scene_name']) == drop:
            continue
        by[r['question_type']].append(r['score'])
    t = {k: sum(v) / len(v) for k, v in by.items()}
    g = {k: t[k] for k in F17 if k != 'object_rel_direction'}
    g['object_rel_direction'] = sum(t[k] for k in DIR) / 3
    return g, sum(g.values()) / 6


out = {}
for arm in ('B2048', 'ON16k', 'B4096'):
    d = json.loads((P / 'report' / f'{arm}.json').read_text())
    out[arm] = d
b = out['B2048']
print(f"B2048 items={b['items']} scenes={b['scenes']} mode={b.get('mode')} synthetic={b.get('generation_synthetic')}")
print('| Task | n | B2048 | 95% CI | errors | capped src/cont | unparsed | f17 | ON16k | B4096 |')
for k in F17:
    g = b['groups'][k]
    lo, hi = g['percentile_95']
    print(f"| {NAMES[k]} | {g['items']} | {100*g['score']:.2f} | [{100*lo:.1f}, {100*hi:.1f}] | {len(g['errors'])} | "
          f"{g['source_capped']}/{g['continuation_capped']} | {g['unparsed']} | {F17[k]} | "
          f"{100*out['ON16k']['groups'][k]['score']:.2f} | {100*out['B4096']['groups'][k]['score']:.2f} |")
m = b['six_task_mean']
print(f"| Six-task mean | {b['items']} | {100*m['score']:.2f} | [{100*m['percentile_95'][0]:.1f}, {100*m['percentile_95'][1]:.1f}] | | | | "
      f"{sum(F17.values())/6:.2f} | {100*out['ON16k']['six_task_mean']['score']:.2f} | {100*out['B4096']['six_task_mean']['score']:.2f} |")
print('per subtype (B2048):', {k: round(100 * v['score'], 2) for k, v in b['per_type'].items()})
print('excluded:', b['excluded'])
rows = b['rows']
shared = [r for r in rows if (r['dataset'], r['scene_name']) == SHARED]
g_all, m_all = grouped(rows)
g_cut, m_cut = grouped(rows, SHARED)
print(f"shared-venue video {SHARED}: {len(shared)} items {sorted({r['question_type'] for r in shared})}; "
      f"six-task mean all {100*m_all:.2f} (recomputed), without them {100*m_cut:.2f}")
