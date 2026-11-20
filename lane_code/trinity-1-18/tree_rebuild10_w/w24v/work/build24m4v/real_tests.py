from pathlib import Path
import sys,json,sqlite3,copy,hashlib,gzip,re,collections,importlib.util,time
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4v'
sys.path[:0]=[str(L/'work/tree_r1c'),str(L/'out/rcj'),str(D),str(L/'out/kit_qd/b')]
import ch,z
from seal import write
from student_pilot.extent_receipt import Extents,required,content
from student_pilot.p3_provenance import file_pin,digest
from student_pilot.carrier_c1_run import Rows
names=z.load(D/'SOURCES.json')['names'];pin=file_pin(D/'c072905b.json')
cfg=dict(extent_receipt=pin,r1_training=dict(extent_pool_sources=names))
rows=[json.loads(x['row']) for x in z.load(D/'published/p_sample.json')['rows']]
pool=z.load(D/'pool_row.json');assert required(pool,'routing')
assert Extents(pin,names).check(pool,'routing') is None
assert digest(pool)==z.load(D/'BEFORE.json')['row_sha256']
checks=ch.scope_tests(cfg,rows);assert checks['status']=='PASS',checks
extra=[]
def refuses(row,stream='routing',sources=names,expected='EXTENT_ROW_UNAUDITED'):
 try:Extents(pin,sources).check(row,stream)
 except ValueError as e:assert str(e)==expected,(row['qid'],str(e));return str(e)
 raise AssertionError('Expected refusal')
for sources in (None,[]):extra.append(dict(case='default',sources=sources,error=refuses(pool,sources=sources)))
for name in ('slice','other'):
 row=z.load(D/('a0_units_row.json' if name=='slice' else 'a0_pool_abs_distance_reworded_row.json'))
 gate=Extents(pin,names);gate.receipt=dict(gate.receipt,rows={q:e for q,e in gate.receipt['rows'].items() if q!=row['qid']})
 try:gate.check(row,'routing')
 except ValueError as e:assert str(e)=='EXTENT_ROW_UNAUDITED';extra.append(dict(case=name,qid=row['qid'],error=str(e)))
 else:raise AssertionError(name)
for label,row,stream in [('unnamed',dict(pool,s1_source=dict(pool['s1_source'],name='unlisted')),'routing'),
 ('other_stream',dict(pool,answer_form='routed'),'vqa'),
 ('boundary',dict(pool,r1_source=dict(family='slice')),'routing')]:
 extra.append(dict(case=label,error=refuses(row,stream)))
# Prefix protection remains even if the original source field is present.
prefixed=next(r for r in rows if r['qid'].startswith('a0_'))
assert not Extents(pin,names).exempt(prefixed,'routing')
F=D/('real_rows_'+str(time.time_ns()));F.mkdir();db=F/'rows.sqlite'
with sqlite3.connect(db) as c:
 c.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
 for i,row in enumerate(rows):c.execute('INSERT INTO rows VALUES(?,?,?)',(i,json.dumps(row),'{}'))
dbpin=file_pin(db)
result=ch.scan(cfg,'routing',[dict(database=dbpin)])
write(D/'P_SAMPLE_CHAIN.json',result)
assert result['refused_rows']==20 and result['extent_exempted_rows']==14,result
sp=importlib.util.spec_from_file_location('student_pilot._extent_before',L/'attic/build24m4v/work/tree_r1c/student_pilot/extent_receipt.py')
old=importlib.util.module_from_spec(sp);sp.loader.exec_module(old)
before,after=old.Extents(pin),Extents(pin,names);differential=[]
for row in rows:
 def outcome(gate):
  try:gate.check(row,'routing');return 'PASS'
  except ValueError as e:return str(e)
 a,b=outcome(before),outcome(after)
 assert b=='PASS' if after.exempt(row,'routing') else a==b
 differential.append(dict(qid=row['qid'],before=a,after=b,exempt=after.exempt(row,'routing')))
write(D/'REAL_DIFFERENTIAL.json',dict(status='PASS',rows=differential))
# P's published unit variants differ from N's receipt. Keep their refusals above;
# run the zero-refusal chain on the 80 exact non-boundary published rows.
db=F/'non_boundary.sqlite';chain_rows=[r for r in rows if not r['qid'].startswith('a0_')]
with sqlite3.connect(db) as c:
 c.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
 for i,row in enumerate(chain_rows):c.execute('INSERT INTO rows VALUES(?,?,?)',(i,json.dumps(row),'{}'))
dbpin=file_pin(db);result=ch.scan(cfg,'routing',[dict(database=dbpin)])
write(D/'REAL_CHAIN.json',result)
assert result['status']=='PASS',result
assert (result['extent_exempted_rows'],result['extent_still_checked_rows'])==(14,66)
# A forged source field cannot pass an existing authenticated database pin.
with sqlite3.connect(db) as c:
 value=copy.deepcopy(prefixed);value['s1_source']['name']='unlisted'
 c.execute('UPDATE rows SET row=? WHERE i=0',(json.dumps(value),))
tamper=ch.scan(cfg,'routing',[dict(database=dbpin)])
assert tamper['status']=='UNAVAILABLE' and 'Missing or changed pinned input' in tamper['reason'],tamper
extra.append(dict(case='database_tamper',error=tamper['reason'],boundary='chain pinned() before Rows'))
write(D/'REAL_TESTS.json',dict(status='PASS',fail_before=z.load(D/'BEFORE.json'),after='PASS',
 scope_checks=checks,controls=extra,chain=result,scope='100 exact published P rows checked differentially; 80 non-boundary rows pass the chain. All 20 P unit variants retain their original refusal. No production full-DB replay claimed.'))
print(json.dumps(dict(status='PASS',rows=result['rows_checked'],exempted=result['extent_exempted_rows'],still_checked=result['extent_still_checked_rows'],refused=result['refused_rows'],tests=checks),indent=2))
