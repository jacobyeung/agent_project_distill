from pathlib import Path
from collections import Counter,defaultdict
import sys,json,sqlite3,datetime
L=Path(__file__).resolve().parents[2];D=L/'work/build22'
sys.path[:0]=[str(L/'work/tree_r1'),str(L/'work/build21')]
import joblib as J
from student_pilot.r1_population import family
from student_pilot.r1_routing import Filters
from student_pilot.row_removals import Removals
from student_pilot.p3_provenance import load,pinned
cfg=load(D/'inputs/config.json');old=load(L/'work/build21/inputs/config.json')
before=Filters(old,old['scene_division']);after=Filters(cfg,cfg['scene_division'])
receipt=load(pinned(cfg['streams']['vqa']));db=pinned(receipt['database'])
counts=defaultdict(Counter);found=set();wanted=after.removals.keys[-1]
connection=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True)
for raw, in connection.execute('SELECT row FROM rows ORDER BY i'):
 row=json.loads(raw);cell=family(row,'vqa');c=counts[cell];c['rows']+=1
 a=before.reason(row,'vqa');b=after.reason(row,'vqa')
 c['before']+=a is None;c['after']+=b is None
 if row['qid'] in wanted:found.add(row['qid']);c['named']+=1;c['newly_removed']+=a is None
connection.close()
assert found==wanted
J.write(D/'REMOVAL_CENSUS.json',dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),database=receipt['database'],families=dict(counts),matched=len(found),scope='Native preparation filters; reader legality is checked in the complete census',per_list=after.removals.report()))
print(json.dumps(dict(families=dict(counts),matched=len(found)),indent=2))
