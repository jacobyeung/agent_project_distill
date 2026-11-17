"""Bounded real-row audit; never infer full-population eligibility from samples."""
from collections import defaultdict,Counter
import hashlib,itertools,json,sqlite3,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build_n1';T=L/'work/tree_r1'
sys.path.insert(0,str(T))
from student_pilot.p3_provenance import load,digest
from student_pilot.r1_loader import audit_rows
from student_pilot.carrier_c1_run import Rows
from student_pilot.r1_training import row_check
O=B/'proofs/loader_audit';O.mkdir(parents=True,exist_ok=True)
def write(name,value):
    (O/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
store=load(B/'inputs/store_parameter.json'); count=store['count']
con=sqlite3.connect('file:'+store['database']['path']+'?mode=ro&immutable=1',uri=True)
groups=defaultdict(list);hashes={};source_rows=[]
# Indexed point reads avoid a full database scan. This is a sample, not a census.
indices=sorted({i*(count-1)//1999 for i in range(2000)})
for index in indices:
    row,target=con.execute('SELECT row,target FROM rows WHERE i=?',(index,)).fetchone()
    raw=json.loads(row); family=raw.get('question_type','unknown')
    groups[family].append((raw,json.loads(target)));source_rows.append((index,hashlib.sha256(row.encode()).hexdigest()))
con.close()
write('SOURCE_SAMPLE.json',dict(receipt=store['receipt'],database=store['database'],declared_store_count=count,
      rows_read=len(indices),selection='2000 evenly spaced primary-key reads; no answer or benchmark statistic',rows=source_rows))
results={}
def inspect(family,pairs,stream,source):
    report=audit_rows((r for r,_ in pairs),stream,family)
    # Native Rows.row runs on the exact source bytes in an in-memory store.
    reader=Rows(dict(streams={},r1_training={'schema':'r1-training-v1'}),None)
    conn=sqlite3.connect(':memory:');conn.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
    reader.connections[stream]=conn
    counts=Counter();examples=[]
    try:
        for i,(row,target) in enumerate(pairs):
            conn.execute('INSERT INTO rows VALUES(?,?,?)',(i,json.dumps(row),json.dumps(target)))
        for i in range(len(pairs)):
            try:
                row,_=reader.row(stream,i);counts['reader_accepted']+=1
                if len(examples)<5:examples.append(dict(qid=row.get('qid'),row_sha256=digest(row),target=row.get('target',row.get('suffix'))))
            except (ValueError,KeyError,TypeError) as e:counts['reader_refused:'+str(e)]+=1
    finally:reader.close()
    report.update(source=source,native_reader=dict(counts),examples=examples,post_filter_eligible=None,
                  missing='Independent complete scene coverage and native frame-host preparation; sample is not full intake')
    results[family]=report
for family,pairs in groups.items():inspect(family,pairs,'vqa',store['database'])
R=Path('/scratch/jjyeung/orch_n30/rows_r1/out')
for family,path,stream in [('recovery_v2',R/'recovery_v2/rows.jsonl','routing'),
                         ('room_v2',R/'room_v2/rows.jsonl','vqa'),
                         ('room_programs_excluded',L/'work/rows_slices/slices_final/a0_room.jsonl','routing'),
                         ('units',L/'work/rows_slices/slices_final/a0_units.jsonl','routing'),
                         ('absolute_distance',L/'work/rows_slices/slices_final/a0_pool_abs_distance_reworded.jsonl','routing')]:
    pairs=[];h=hashlib.sha256()
    with path.open('rb') as f:
        for line in itertools.islice(f,2000):
            h.update(line);r=json.loads(line);pairs.append((r,{}))
    inspect(family,pairs,stream,dict(path=str(path),slice_sha256=h.hexdigest(),rows_read=len(pairs)))
for family,report in results.items():write(family+'.json',report)
card=load(B/'inputs/mix.json')
mix=[]
for cell in card['cells']:
    mix.append(dict(**cell,requested_draws=int(round(cell['rows_per_step']*1000)),
        eligible=None,ceiling=None,actual_draws=None,expected_repeats=None,
        status='EXCLUDED' if cell['rows_per_step']==0 else 'BLOCKED: full post-filter population missing'))
result=dict(status='BLOCKED',complete=False,families={k:{a:b for a,b in v.items() if a!='examples'} for k,v in results.items()},
    mix=mix,production_audit_entry='student_pilot/r1_loader.py:production_audit',
    stand_ins='No model, RGB, head, tower, or GPU execution. SQLite source slices are read through native Rows.row; no text or scene stand-ins.',
    missing=['Complete filtered populations and index maps for every stream','Independent alias/canonical coverage',
             'Real RGB and camera/pose/pointing preparation','Full sampler draws and per-unit/per-status/facing shares'],
    note='Rows.row acceptance is text/reader acceptance only. Unknown overlap never counts as admitted.')
write('RESULT.json',result)
with (B/'STATUS.md').open('a') as f:f.write('\nBounded source rows passed through the native reader. The loader audit is BLOCKED on complete filtered populations, independent scene coverage and frame-host preparation; work/build_n1/proofs/loader_audit/RESULT.json.\n')
print(json.dumps({k:v['native_reader'] for k,v in results.items()}))
