"""Build declaration-mode composition inputs (tree-independent bytes).

prod:  6,000 CAMERA_SOURCES extract rows as base + all delivered camera_wording (e8cbda99) rows as the bound slice.
mixed: real non-camera rows (relative_count, 2,000 absolute_distance) + camera_B_retained rows as base, empty slice batch.
"""
from pathlib import Path
import gzip, json, sqlite3, hashlib
W = Path(__file__).resolve().parent
RO = W.parents[1]/'ro/orch_n30'
CAM = RO/'fb_pack/cam/out'
D = W/'compose'; D.mkdir(exist_ok=True)
sha = lambda b: hashlib.sha256(b).hexdigest()
EXTRACT = RO/'sb_rowA/out/CAMERA_SOURCES.jsonl.gz'
SLICE = CAM/'rows/camera_wording.jsonl'
assert sha(EXTRACT.read_bytes()) == '6d9abc4257735f41d34eb1a22499b584027815f1d2a8fe379c00c343fbde952c'
assert sha(SLICE.read_bytes()) == 'e8cbda99f794540c9c0f716d1ae8ce451fd84e473598795c67237fe051acd2d0'
ROUTING_SCHEMA = 'c1-routing-stream-v1'

def write_db(name, items):
    path = D/(name+'.sqlite')
    db = sqlite3.connect(':memory:'); db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
    for i, (r, t) in enumerate(items): db.execute('INSERT INTO rows VALUES(?,?,?)', (i, r, t))
    db.commit(); path.write_bytes(db.serialize()); db.close()
    base = dict(schema=ROUTING_SCHEMA, scene_role='train', heldout_overlap=0,
                database=dict(path=str(path.resolve()), sha256=sha(path.read_bytes())), division=None)
    (D/(name+'_base.json')).write_text(json.dumps(base))
    return len(items)

info = {}
extract = []
with gzip.open(EXTRACT, 'rt') as f:
    for line in f:
        e = json.loads(line); extract.append((e['row'], e['target']))
info['prod_base_rows'] = write_db('prod', extract)
seen = {json.loads(r)['qid'] for r, _ in extract}
mixed = []
for p, limit in ((RO/'fb_pack/relcnt/out/relative_count.jsonl', None),
                 (RO/'fb_pack/route/out/rows/absolute_distance_retained.jsonl', 2000),
                 (RO/'fb_pack/route/out/rows/camera_B_retained.jsonl', None)):
    n = 0
    with p.open() as f:
        for line in f:
            r = json.loads(line)
            if r['qid'] in seen: continue
            seen.add(r['qid']); mixed.append((json.dumps(r), '{}')); n += 1
            if limit and n >= limit: break
    info[p.name] = dict(rows=n, sha256=sha(p.read_bytes()))
info['mixed_base_rows'] = write_db('mixed', mixed)
(D/'empty.jsonl').write_text('')
decl = dict(schema='r1-routing-slices-v1', bound=['camera_wording'],
            deferred={k: 'review fixture: not bound' for k in ('absolute_distance', 'units', 'coverage_distance', 'coverage_units', 'recovery')})
(D/'decl.json').write_text(json.dumps(decl)); (D/'intake.json').write_text(json.dumps(dict(note='review fixture intake')))
(D/'BUILD.json').write_text(json.dumps(info, indent=1)); print(json.dumps(info, indent=1))
