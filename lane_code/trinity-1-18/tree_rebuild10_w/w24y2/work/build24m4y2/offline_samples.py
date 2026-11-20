from pathlib import Path
import hashlib, json, sqlite3, sys
from unittest.mock import patch
L=Path.cwd();D=L/'work/build24m4y2';R=L.parent/'work/d173817/173817'
sys.path[:0]=[str(L/'out/rcj'),str(L/'work/tree_r1c')]
import nd
F=D/'offline';F.mkdir();q=F/'q';(q/'u').mkdir(parents=True)
(F/'s').symlink_to(L/'work/tree_r1c',target_is_directory=True)
source=L/'work/build24m4x2/native/q'
(q/'n.json').write_bytes((source/'n.json').read_bytes())
for p in (source/'u').iterdir():
    (q/'u'/p.name).symlink_to(p.resolve())
counts={}
for name,filename in [('base','p_sample.json'),('selection','n_sample.json')]:
    rows=nd.load(R/filename)['rows'];counts[name]=len(rows)
    (q/name).mkdir()
    with sqlite3.connect(q/name/'rows.sqlite') as c:
        c.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
        c.executemany('INSERT INTO rows VALUES(?,?,?)',[(r['i'],r['row'],r['target']) for r in rows])
(F/'scratch').mkdir()
pdb=q/'base/rows.sqlite';ndb=q/'selection/rows.sqlite'
rules=nd.native_rules(ndb)
try:
    nd.publish(pdb,ndb,F/'missing',F/'rd0',F/'strict',F/'scratch')
except ValueError as e:
    assert str(e)=='E96:gate'
else:raise AssertionError('Sample accepted as full P store')
with patch.object(nd,'GATE',hashlib.sha256(pdb.read_bytes()).hexdigest()):
    result=nd.publish(pdb,ndb,F/'missing',F/'rd0',F/'out',F/'scratch')
value=nd.load(F/'out/nd.json')
assert value['criteria']['a']['status']=='PASS',value['criteria']['a']
assert value['criteria']['b']['status']=='PASS',value['criteria']['b']
assert value['criteria']['c']['status']=='FAIL'  # No sample chain is passed off as the full chain.
assert value['criteria']['d']['status']=='DEFERRED_TO_DISCOVERY'
report=dict(status='PASS',sample_counts=counts,criteria=value['criteria'],native_rules='PASS',
    strict_P_gate='E96:gate',sample_only_P_hash_substitution=True,
    scope='Exact SQL text from 173817 published samples. Chain unavailable for these sample stores; full decision uses REPLAY173817.json.',
    files=result['files'])
(D/'OFFLINE_SAMPLES.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status='PASS',sample_counts=counts,matched=value['matched_rows'],a=value['criteria']['a']['status'],b=value['criteria']['b']['status'],c=value['criteria']['c']['status'])))
