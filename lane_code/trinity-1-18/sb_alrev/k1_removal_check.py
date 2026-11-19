"""Which K1 rows of v7 does N's pinned removal already drop? (u.json = v7 K1 list; all remove_files = N side)."""
import json, sqlite3, sys, collections
from pathlib import Path
sys.path.insert(0, '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w18/work/tree_r1')
from student_pilot.r1_rooms import Rooms
from student_pilot.row_removals import row_keys
W = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w')
cfg = json.load(open(W/'w18/work/build18/inputs/config.json'))
R = Rooms(json.load(open(W/'w17b/work/build17/proofs/rooms/RESULT.json'))['audit']['authority'])
tm = json.load(open('/scratch/jjyeung/orch_n30/sb_alias2/out/TIERED_ALIAS_MAP.json'))['aliases']
def keys(p):
    s = set()
    for line in open(p):
        if line.strip(): s.add(json.loads(line)['row_key'])
    return s
u = keys(W/'w18/work/build18/inputs/u.json')
allrm = set()
for f in cfg['remove_files']:
    if f['path'].endswith('.jsonl') or f['path'].endswith('u.json') or f['path'].endswith('n.json') or True:
        try: allrm |= keys(f['path'])
        except Exception as e: print('skip', f['path'], type(e).__name__)
c = collections.Counter()
con = sqlite3.connect('file:/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite?mode=ro&immutable=1', uri=True)
for (raw,) in con.execute('select row from rows'):
    r = json.loads(raw); t = r['dataset'] + '/' + r['scene']
    if R.room(tm[t]['canonical']) not in R.k1: continue
    base = R.status(r)[0] == 'k1_heldout'; k = row_keys(r)
    c[('baseline' if base else 'new', 'in_u' if k & u else 'not_u', 'in_any_remove' if k & allrm else 'not_removed')] += 1
print('u.json keys', len(u), 'all remove keys', len(allrm))
for k, v in sorted(c.items()): print(k, v)
