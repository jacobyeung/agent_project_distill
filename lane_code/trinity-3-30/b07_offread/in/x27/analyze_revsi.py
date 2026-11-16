"""Summarize the returned ReVSI five-category direct read. Numbers from report/B*.json only (review_rv R1); R5 distributions from the items journal."""
import collections, glob, json, sys
from pathlib import Path
P = Path(sys.argv[1])
PARENT = {'route_planning': 42.86, 'object_size_estimation': 63.41, 'object_rel_direction': 48.43}
CATS = ('object_counting', 'object_rel_direction', 'object_rel_distance', 'object_size_estimation', 'route_planning')
out = {a: json.loads((P / 'report' / f'{a}.json').read_text()) for a in ('B2048', 'ON16k', 'B4096')}
b = out['B2048']
print(f"B2048 items={b['items']} scenes={b['scenes']} mode={b['mode']} synthetic={b['generation_synthetic']}")
print('| Category | n | B2048 | 95% CI (scenes) | errors | capped src/cont | unparsed | parent CP1 m200 B2048 (unpaired) | ON16k | B4096 |')
for k in CATS:
    g = b['groups'][k]; lo, hi = g['percentile_95']
    print(f"| {k} | {g['items']} | {100*g['score']:.2f} | [{100*lo:.1f}, {100*hi:.1f}] | {g.get('error_count', len(g['errors']))} | "
          f"{g['source_capped']}/{g['continuation_capped']} | {g['unparsed']} | {PARENT.get(k, 'not recovered')} | "
          f"{100*out['ON16k']['groups'][k]['score']:.2f} | {100*out['B4096']['groups'][k]['score']:.2f} |")
m = b['five_category_mean']
print(f"| Five-category mean | {b['items']} | {100*m['score']:.2f} | [{100*m['percentile_95'][0]:.1f}, {100*m['percentile_95'][1]:.1f}] | | | | n/a (58.63 is 7-category) | "
      f"{100*out['ON16k']['five_category_mean']['score']:.2f} | {100*out['B4096']['five_category_mean']['score']:.2f} |")
print('per subtype B2048:', {k: (v['items'], round(100*v['score'], 2)) for k, v in b['per_type'].items()})
print('direction toward/away (diagnostic):', {k: (v['items'], round(100*v['score'], 2), [round(100*x, 1) for x in v['percentile_95']]) for k, v in b['direction_by_question_text'].items()})
print('excluded:', b['excluded'])
sizes = collections.Counter(); vt = collections.Counter(); think = []; n = 0
for f in sorted(glob.glob(str(P / 'a0' / 'results' / '*' / 'items_*.jsonl'))):
    for line in open(f):
        r = json.loads(line); n += 1
        sizes[str(r.get('processed_height_width'))] += 1; vt[str(r.get('visual_tokens_per_frame'))] += 1
for f in sorted(glob.glob(str(P / 'a0' / 'results' / '*' / 'budget_2048.meta.jsonl'))):
    for line in open(f):
        r = json.loads(line); think.append(r['think_tokens'])
print('R5 items', n, 'processed_height_width', dict(sizes), 'visual_tokens_per_frame', dict(vt))
if think:
    think.sort(); print('think tokens median', think[len(think)//2], 'p90', think[int(.9*len(think))], 'max', think[-1], 'at budget', sum(t >= 2048 for t in think))
