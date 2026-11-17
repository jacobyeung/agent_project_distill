import contextlib,copy,json,sys,tempfile
from pathlib import Path
H=Path(__file__).resolve().parents[1];sys.path[:0]=[str(H/'tools'),str(H/'tests')]
import selection_check as sc
from fix7_fixtures import pool_fixture
out=Path(tempfile.mkdtemp(prefix='selection_',dir=H/'evidence/fix7_selection'))
with (out/'fixture.log').open('x') as log,contextlib.redirect_stdout(log):raw,_,_=pool_fixture(out)
baseline=sc.project(raw);assert baseline['selected_rows']==1
catalog={}
manifest=sc.load(raw['manifest']['path'])
# Resolver uses an explicit per-pin fixture mapping, with native hash checks.
from student_pilot.p3_provenance import pinned
class Local:
 def __init__(self):self.verified={}
 def __call__(self,pin):
  p=pinned(pin);self.verified[pin['sha256']]=dict(path=str(p),bytes=p.stat().st_size);return p
code=sc.load(H/'payload/7.json');code['tree']=str(H/'build/tree')
a=out/'equal';a.mkdir();assert sc.regenerate(raw,baseline,Local(),a,code)==0
assert sc.load(a/'q.json')['status']=='EQUAL'
changed=copy.deepcopy(baseline);changed['sources']['T0_room']['counts']['seen']+=1
b=out/'changed';b.mkdir();assert sc.regenerate(raw,changed,Local(),b,code)==1
assert '$.sources.T0_room.counts.seen' in sc.load(b/'q.json')['differences']
# All nested keys, list order, missing keys and JSON number types are significant.
for x,y in [({'a':[1,2]},{'a':[2,1]}),({'a':1},{'a':True}),({'a':[]},{}),({'blockers':[]},{'blockers':['x']})]:assert sc.differences(x,y)
# The production attempt must fail, never fabricate a candidate from a stale hash map.
p=sc.load(H/'evidence/fix7_selection/production_attempt/q.json')
assert p['status']=='BLOCKED' and not p['regenerated']
assert not (H/'evidence/fix7_selection/production_attempt/r.json').exists()
(out/'results.json').write_text(json.dumps(dict(status='PASS',equal=True,changed_content_refused=True,production_missing_refused=True),indent=2)+'\n')
(H/'evidence/fix7_selection/selection_tests.json').write_text(json.dumps(dict(status='PASS',path=str(out),tool_sha256=sc.sha(H/'tools/selection_check.py'),equal=True,changed_content_refused=True,production_missing_refused=True),indent=2)+'\n')
print(out)
