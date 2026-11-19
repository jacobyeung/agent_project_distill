from pathlib import Path
from copy import deepcopy
import sys,json,sqlite3
L=Path(__file__).resolve().parents[2];B=L/'work/build17';T=L/'work/tree_r1';O=B/'proofs/room_fixture';O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(T),str(L/'work/n1fix2')]
from monitor9 import Monitor
m=Monitor(T)
from student_pilot import r1_rooms as R
from student_pilot.p3_provenance import load,write,file_pin
cfg=deepcopy(load(B/'inputs/config.json'));rooms=R.Rooms(cfg['r1_training']['room_authority'])
reserve=next(x for x in sorted(rooms.r0) if x.startswith('scannet/'))
rows=[dict(qid='a',dataset='d1',scene='fixture',canonical='scannet/scene9997_00'),
      dict(qid='b',dataset='d1',scene='fixture',canonical='arkitscenes/41069175'),
      dict(qid='c',dataset='d1',scene='fixture',canonical=reserve+'_00'),
      dict(qid='d',dataset='d1',scene='unknown')]
sources={}
for kind in ('recovery','units','absolute_distance'):
    p=O/(kind+'.jsonl');p.write_text(''.join(json.dumps(r)+'\n' for r in rows));sources[kind]={'source':file_pin(p)}
write(O/'sources.json',sources);cfg['r1_training']['row_sources']=file_pin(O/'sources.json')
database=O/'tiny.sqlite';con=sqlite3.connect(database)
con.execute('CREATE TABLE IF NOT EXISTS rows (i INTEGER PRIMARY KEY,row TEXT)')
con.executemany('INSERT OR REPLACE INTO rows VALUES (?,?)',[(i,json.dumps(r)) for i,r in enumerate(rows)])
con.commit();con.close()
write(O/'store.json',dict(database=file_pin(database)));cfg['streams']['vqa']=file_pin(O/'store.json')
audit,hits=R.census(cfg)
assert audit['complete'] is False and audit['unknown_overlap']==3
assert len(hits)==6 and audit['store']['unresolved']==1
for cell in audit['slices'].values():
    assert cell['rows']==4 and cell['k1_heldout']==1 and cell['r0']==1 and cell['unresolved']==1
write(O/'RESULT.json',dict(status='PASS',scope='Synthetic data-admission census only; not a frame host or production-mode fixture.',audit=audit,hits=hits))
m.save(O)
print('Synthetic room census passed')
