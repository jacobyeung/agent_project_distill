import json, sqlite3, sys, collections
from pathlib import Path
sys.path.insert(0, '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w18/work/tree_r1')
from student_pilot.r1_rooms import Rooms
from student_pilot.row_removals import row_keys
W = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w')
cfg = json.load(open(W/'w18/work/build18/inputs/config.json'))
R = Rooms(json.load(open(W/'w17b/work/build17/proofs/rooms/RESULT.json'))['audit']['authority'])
tm = json.load(open('/scratch/jjyeung/orch_n30/sb_alias2/out/TIERED_ALIAS_MAP.json'))['aliases']
files = {}
for f in cfg['remove_files']:
    s = set(); reasons = collections.Counter()
    for line in open(f['path']):
        if line.strip(): d = json.loads(line); s.add(d['row_key']); reasons[d.get('reason', d.get('defect'))] += 1
    files[Path(f['path']).name + ':' + f['sha256'][:8]] = (s, reasons)
c = collections.Counter()
con = sqlite3.connect('file:/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite?mode=ro&immutable=1', uri=True)
for (raw,) in con.execute('select row from rows'):
    r = json.loads(raw)
    if R.room(tm[r['dataset'] + '/' + r['scene']]['canonical']) not in R.k1 or R.status(r)[0] == 'k1_heldout': continue
    k = row_keys(r); hit = tuple(n for n, (s, _) in files.items() if k & s)
    c[hit] += 1
for k, v in c.most_common(): print(v, k)
for n, (s, rs) in files.items(): print(n, len(s), dict(rs.most_common(3)))
