import json, sqlite3, sys
from pathlib import Path
W = Path('/scratch/jjyeung/orch_n30/tr21_revT/w'); D = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24v/work/build24m4v')
tree = sys.argv[1]
sys.path[:0] = [str(W/tree), '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24v/out/rcj']
import ch
from student_pilot.p3_provenance import file_pin
names = json.loads((D/'SOURCES.json').read_text())['names']
cfg = dict(extent_receipt=file_pin(D/'c072905b.json'), r1_training=dict(extent_pool_sources=names))
rows = [json.loads(x['row']) for x in json.loads((D/'published/p_sample.json').read_text())['rows']]
out = {}
if tree == 'patched':
    out['scope_tests'] = ch.scope_tests(cfg, rows)
F = W/('real_'+tree); F.mkdir(exist_ok=True)
for label, sel in (('all100', rows), ('non_a0_80', [r for r in rows if not r['qid'].startswith('a0_')])):
    db = F/(label+'.sqlite')
    if not db.exists():
        with sqlite3.connect(db) as c:
            c.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
            for i, r in enumerate(sel): c.execute('INSERT INTO rows VALUES(?,?,?)', (i, json.dumps(r), '{}'))
    res = ch.scan(cfg, 'routing', [dict(database=file_pin(db))])
    out[label] = {k: res.get(k) for k in ('status', 'rows_checked', 'refused_rows', 'counts', 'extent_exempted_rows', 'extent_still_checked_rows', 'extent_required_rows', 'reason')}
    out[label]['first'] = [(x['row_key'][3], x['check'], x['exception'][:60]) for x in res.get('first_ten_refusals', [])[:3]]
(W/('REAL_CONTROLS_'+tree+'.json')).write_text(json.dumps(out, indent=1, default=str)); print(json.dumps(out, indent=1, default=str))
