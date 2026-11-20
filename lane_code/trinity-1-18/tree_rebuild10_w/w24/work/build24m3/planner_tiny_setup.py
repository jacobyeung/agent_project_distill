from common import *
s=(D/'planner_scene_test.py').read_text()
s=s.replace("F=D/'planner_scene'","F=D/'planner_scene_tiny'")
needle="cfg=J.load(D/'removal_receipts/cfg.json')"
s=s.replace(needle,needle+'''
import sqlite3,copy
def tiny_receipt(pin,label):
 receipt=J.load(pin['path']);source=Path(receipt['database']['path']);dest=F/(label+'.sqlite')
 with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(dest) as db:
  db.execute('create table rows(i integer primary key,row text,target text)')
  _,row,target=src.execute('select i,row,target from rows order by i limit 1').fetchone()
  db.execute('insert into rows values(0,?,?)',(row,target))
 receipt['database']=file_pin(dest);receipt['count']=1
 return J.write(F/(label+'.json'),receipt)
pose=J.load(cfg['streams']['pose']['path'])
for index,source in enumerate(pose['sources']):
 source['receipt']=tiny_receipt(source['receipt'],'pose'+str(index))
 if 'count' in source:source['count']=1
cfg['streams']['pose']=J.write(F/'pose.json',pose)
cfg['streams']['pointing']=tiny_receipt(cfg['streams']['pointing'],'pointing')
cfg['streams']['routing']=file_pin(D/'tiny_routing/legacy.json')
''')
s=s.replace("collect(cfg)","collect(cfg['streams']);collect(cfg)")
s=s.replace("fixture='Synthetic retained native24 stores and twin authority constants;", "fixture='One native pose row from each mix source, one native pointing/routing row, retained native VQA/twin fixture and authority constants;")
(D/'planner_scene_tiny.py').write_text(s)
