"""Print compact item views. usage: show_items.py <step> <id> [<id> ...]   (searches direct sets, facing, vsti; routed with planner python)"""
import sys; sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
step = int(sys.argv[1]); ids = set(sys.argv[2:]); run = 'R1' if step in (100, 200, 400) else 'S1'
rows = []
for s in ('dev-S1', 'R0-dev'):
    try: rows += K.direct(run, step, s)
    except Exception as e: pass
for tw in ('away', 'forward'):
    try: rows += K.facing(run, step, tw)
    except Exception as e: pass
try: rows += K.vsti(run, step)
except Exception as e: pass
if any(i not in {r['id'] for r in rows} for i in ids):
    try:
        for part in ('A', 'B'): rows += K.routed(step if step != 100 else 200, part=part)
    except Exception as e: print('routed unavailable:', repr(e)[:100])
for r in rows:
    if r['id'] in ids:
        tx = r['text'] or ''
        print('== %s | %s %s %s | gt=%s pred=%s score=%s forced=%s' % (r['id'], r['set'], r['type'], r.get('subtype'), r['gt'], r.get('pred', r.get('answer')), r['score'], r.get('forced_close')))
        print('Q:', r['question'][:260].replace('\n', ' '), '|', ' ; '.join(r['options'])[:200])
        print('T:', tx[:700].replace('\n', ' / ') + (' ...[%d chars]' % len(tx) if len(tx) > 700 else ''))
