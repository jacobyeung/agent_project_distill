"""Pointing-store rows on K1 training rooms, minus K1-heldout, R0 (all r0_split values) and dev rooms.

Run: bash work/run.sh k1_overlap   (writes work/k1_overlap.json)
Room rule as r1_rooms.Rooms.room (scannet capture -> sceneNNNN; scannetpp capture = room).
dev-S1 and benchmark lists are not local; the R0 proofs name them (absent_from), and admission applies
cfg dev_scene_exclusions / benchmark_scene_exclusions (s1_admission.py:187) before any row trains.
"""
import hashlib
import json
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

PACK = Path('/scratch/jjyeung/orch_n30/fb_pack')
SPLIT = PACK/'ro/orch_n30/tree_rebuild10_w/ext/b12/work/auth/K1SPLIT_R0.json'
SOURCE = PACK/'in/pointing/rows_c09bb5ca.sqlite'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def room(canonical):
    ds, capture = canonical.split('/', 1)
    if ds == 'scannet':
        return 'scannet/' + re.match(r'(scene\d+)', capture).group(1)
    if ds in ('scannetpp', 'scannetppv2'):
        return 'scannetpp/' + capture
    return None


split = json.loads(SPLIT.read_text())
k1 = split['teacher_k1']['captures']
k1_train = {c['room'] for c in k1 if c['k1_split'] == 'train'}
k1_held = {c['room'] for c in k1 if c['k1_split'] == 'heldout'}
r0 = split['r0_scenes']
r0_rooms = {c['room'] for c in r0['captures'].values()} | set(r0['rooms'])
dev_rooms = set(r0['dev_room_list'])
dev_list = r0['dev_room_list']
assert len(dev_rooms) == r0['dev_rooms']
blocked = k1_held | r0_rooms | dev_rooms
eligible = k1_train - blocked
rows, rooms, kinds = Counter(), defaultdict(Counter), Counter()
c = sqlite3.connect(f'file:{SOURCE}?mode=ro', uri=True)
for (raw,) in c.execute('SELECT row FROM rows ORDER BY i'):
    row = json.loads(raw)
    r = room(row['provenance']['canonical_scene'])
    status = ('k1_train_eligible' if r in eligible else 'k1_heldout' if r in k1_held else 'r0' if r in r0_rooms
              else 'dev' if r in dev_rooms else 'k1_train_blocked' if r in k1_train else 'not_k1')
    rows[status] += 1
    if status == 'k1_train_eligible':
        rooms[r][row['pointing']['kind']] += 1
        kinds[row['pointing']['kind']] += 1
c.close()
out = dict(inputs={str(SPLIT): sha(SPLIT), str(SOURCE): sha(SOURCE)},
           k1_captures=Counter(x['k1_split'] for x in k1), k1_train_rooms=len(k1_train), k1_heldout_rooms=len(k1_held),
           r0_rooms=len(r0_rooms), r0_split_counts=Counter(x['r0_split'] for x in r0['captures'].values()),
           dev_rooms=len(dev_rooms), dev_room_list_type=type(dev_list).__name__,
           k1_train_rooms_blocked=len(k1_train & blocked), eligible_rooms=len(eligible),
           store_rows_by_status=rows, eligible_rooms_with_rows=len(rooms), eligible_rows_by_kind=kinds,
           rows_per_eligible_room=sorted(sum(v.values()) for v in rooms.values()))
(Path(__file__).with_name('k1_overlap.json')).write_text(json.dumps(out, indent=1, default=dict) + '\n')
print(json.dumps({k: v for k, v in out.items() if k != 'rows_per_eligible_room'}, indent=1, default=dict))
print('rows_per_eligible_room', out['rows_per_eligible_room'])
