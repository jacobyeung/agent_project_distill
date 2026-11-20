from pathlib import Path
import sys,json,sqlite3,hashlib,os,resource,traceback,gzip
from unittest.mock import patch
L=Path.cwd();D=L/'work/build24m4y';R=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173754/173754')
resource.setrlimit(resource.RLIMIT_AS,(14*1024**3,14*1024**3))
label=sys.argv[1];F=D/('offline_'+label);F.mkdir();q=F/'q';(q/'selection').mkdir(parents=True);(q/'base').mkdir();(q/'u').mkdir()
T=L/'work/tree_r1c' if label=='new' else D/'base_tree';(F/'s').symlink_to(T,target_is_directory=True)
(q/'n.json').write_bytes((D/'native/q/n.json').read_bytes())
for p in (D/'native/q/u').iterdir():(q/'u'/p.name).symlink_to(p.resolve())
H=L/'out/rcj' if label=='new' else D/'offline_base_helpers'
if label=='base':
 H.mkdir()
 for name in ('nd.py','ps.py','f.json'):
  p=L/'attic/build24m4y/out/rcj'/name
  if not p.exists():p=L/'out/rcj'/name
  (H/name).write_bytes(p.read_bytes())
sys.path[:0]=[str(H),str(T)];import nd
P=json.loads((R/'p_sample.json').read_bytes());N=json.loads((R/'n_sample.json').read_bytes())
for name,source in [('base',P),('selection',N)]:
 with sqlite3.connect(q/name/'rows.sqlite') as c:
  c.execute('create table rows(i integer primary key,row text,target text)')
  c.executemany('insert into rows values(?,?,?)',[(v['i'],v['row'],v['target']) for v in source['rows']])
ndb=q/'selection/rows.sqlite';pdb=q/'base/rows.sqlite';rules=nd.native_rules(ndb)
(F/'scratch').mkdir()
record=dict(scope='Exact published SQL row/target text only; 10 P and 7 N rows. These are sample databases, not the production stores.',P_rows=len(P['rows']),N_rows=len(N['rows']),native_rules='PASS',tree=nd.TREE)
try:nd.publish(pdb,ndb,F/'missing_request',F/'rd0',F/'strict',F/'scratch')
except Exception as error:record['strict_publish_refusal']=traceback.format_exc();assert str(error)=='E96:gate'
else:raise AssertionError('sample unexpectedly matches production hash')
with patch.object(nd,'GATE',hashlib.sha256(pdb.read_bytes()).hexdigest()):
 record['sample_publish']=nd.publish(pdb,ndb,F/'missing_request',F/'rd0',F/'out',F/'scratch')
record['sample_publish_types']=nd.publish_types(ndb,F/'types/routing_types.json')
record['full_type_table']=nd.type_table(json.loads((R/'routing_types.json').read_bytes())['rows_by_type'],json.loads((R/'routing_types.json').read_bytes())['database_sha256'])
assert record['full_type_table']==json.loads((R/'routing_types.json').read_bytes())
record['production_status']=json.loads((R/'nd.json').read_bytes())['status'];record['unavailable']='Full P/N SQL stores, staged runtime, namespaces and processor assets for production replay. No production hash gate bypass is delivered.'
(F/'RESULT.json').write_text(json.dumps(record,indent=2)+'\n');print(label,'native rules, sample publish, sample types, and published full type-table replay PASS',flush=True)
