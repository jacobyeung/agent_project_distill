"""Build the extract and mixed base databases plus fixture base pins (independent of the patch's harness)."""
from pathlib import Path
import gzip, json, sqlite3, hashlib, sys
W = Path(__file__).resolve().parent
FB = W.parents[1]
RO = FB/'ro/orch_n30'
EXTRACT = RO/'sb_rowA/out/CAMERA_SOURCES.jsonl.gz'
sha = lambda b: hashlib.sha256(b).hexdigest()
assert sha(EXTRACT.read_bytes()) == '6d9abc4257735f41d34eb1a22499b584027815f1d2a8fe379c00c343fbde952c'
D = W/'compose'; D.mkdir(exist_ok=True)

def write_db(path, items):
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
    for i, (row, target) in enumerate(items):
        db.execute('INSERT INTO rows VALUES(?,?,?)', (i, row, target))
    db.commit(); path.write_bytes(db.serialize()); db.close()
    pin = dict(path=str(path.resolve()), sha256=sha(path.read_bytes()))
    base = dict(schema='c1-routing-v1', scene_role='train', heldout_overlap=0, database=pin, division=None)
    return base

extract = []
with gzip.open(EXTRACT, 'rt') as f:
    for line in f:
        e = json.loads(line); extract.append((e['row'], e['target']))
assert len(extract) == 6000
mixed = list(extract)
seen = {json.loads(r)['qid'] for r, _ in extract}
extra = [(RO/'fb_pack/relcnt/out/relative_count.jsonl', None),
         (RO/'fb_pack/route/out/rows/absolute_distance_retained.jsonl', 2000),
         (RO/'fb_pack/route/out/rows/camera_B_retained.jsonl', None)]
for p, limit in extra:
    n = 0
    with p.open() as f:
        for line in f:
            r = json.loads(line)
            if r['qid'] in seen: continue
            seen.add(r['qid']); mixed.append((json.dumps(r), '{}')); n += 1
            if limit and n >= limit: break
    print(p.name, n)
sys.path.insert(0, str(W/'tree_C'))
from student_pilot.carrier_c1_routing import ROUTING_SCHEMA
for name, items in (('extract', extract), ('mixed', mixed)):
    base = write_db(D/(name+'.sqlite'), items)
    base['schema'] = ROUTING_SCHEMA
    p = D/(name+'_base.json'); p.write_text(json.dumps(base))
    print(name, len(items), sha(p.read_bytes()))
pol = W/'tree_C/configs/r1_camera_trace_form_v1.json'
print('policy', sha(pol.read_bytes()))
