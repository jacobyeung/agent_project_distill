import sys, json
sys.path.insert(0, '/scratch/jjyeung/orch_n30/sb_ktfix2/code')
from common import *
from exclusions import population, decision_rows
from evaluate_v2 import gains_once, arm
pop = population(); allowed = sorted(pop['allowed_row_ids']); withheld = sorted(set(pop['row_rooms']) - set(allowed))
i = allowed[0]; room = pop['row_rooms'][i]; out = {}
for name, row in [('unpinned_id', dict(row_id='ground-planted', room=room, split='train')),
                  ('wrong_room', dict(row_id=i, room='scannet/scene0000', split='train')),
                  ('heldout_split', dict(row_id=i, room=room, split='heldout')),
                  ('withheld_row', dict(row_id=withheld[0], room=pop['row_rooms'][withheld[0]], split='train'))]:
    try: out[name] = 'kept' if decision_rows([row]) else 'dropped'
    except ValueError as e: out[name] = 'rejected: ' + str(e)[:60]
base = [dict(row_id=r, room=pop['row_rooms'][r], split='train', arm=arm(32, 32, 'today'), score=0.) for r in pop['row_rooms']]
treat = [dict(row_id=r, room=pop['row_rooms'][r], split='train', arm=arm(64, 64, 'today'), score=-1.) for r in pop['row_rooms']]
out['clean_gain'] = gains_once(base + treat)['gains']['added_frame_gain']['point']
out['extra_unpinned_row'] = gains_once(base + treat + [dict(row_id='ground-planted', room=room, split='train', arm=arm(64, 64, 'today'), score=1e6)])['status']
dup = [dict(t, score=+5.) for t in treat if t['row_id'] in set(allowed)]
g = gains_once(base + treat + dup)
out['duplicate_rows_appended'] = dict(status=g['status'], point=g['gains']['added_frame_gain']['point'] if g['status'] == 'OK' else None)
print(json.dumps(out, indent=1)); open('/scratch/jjyeung/orch_n30/sb_ktchk/work/rows_probe.json', 'w').write(json.dumps(out, indent=1))
