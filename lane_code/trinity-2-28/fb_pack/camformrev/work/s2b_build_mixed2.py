"""Mixed base without the extract (fits the 200 MB local composition limit): non-camera rows + camera_B camera rows."""
from pathlib import Path
import json, sqlite3, hashlib, sys
W = Path(__file__).resolve().parent; RO = W.parents[1]/'ro/orch_n30'
sha = lambda b: hashlib.sha256(b).hexdigest()
sys.path.insert(0, str(W/'tree_C'))
from student_pilot.carrier_c1_routing import ROUTING_SCHEMA
items, seen = [], set()
for p, limit in ((RO/'fb_pack/relcnt/out/relative_count.jsonl', None),
                 (RO/'fb_pack/route/out/rows/absolute_distance_retained.jsonl', 2000),
                 (RO/'fb_pack/route/out/rows/camera_B_retained.jsonl', None)):
    n = 0
    with p.open() as f:
        for line in f:
            r = json.loads(line)
            if r['qid'] in seen: continue
            seen.add(r['qid']); items.append(json.dumps(r)); n += 1
            if limit and n >= limit: break
    print(p.name, n, sha(p.read_bytes()))
db = sqlite3.connect(':memory:'); db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
for i, r in enumerate(items): db.execute('INSERT INTO rows VALUES(?,?,?)', (i, r, '{}'))
db.commit(); path = W/'compose/mixed2.sqlite'; path.write_bytes(db.serialize()); db.close()
base = dict(schema=ROUTING_SCHEMA, scene_role='train', heldout_overlap=0, database=dict(path=str(path), sha256=sha(path.read_bytes())), division=None)
(W/'compose/mixed2_base.json').write_text(json.dumps(base)); print(len(items), path.stat().st_size)
