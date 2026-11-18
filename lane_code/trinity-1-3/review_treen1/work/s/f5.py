import copy,json,os,sys,sqlite3,collections,tempfile,hashlib
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/review_treen1/work');K=W/'pkg'
os.environ.update(R2_FIXTURES=str(K/'fixtures'),R2_PROOFS=str(W/'tmp'))
sys.path[:0]=[str(K/'work/tree_r1')]
from student_pilot.r2_adapters import normalize
from student_pilot.carrier_c1_run import Rows
from student_pilot.r2_intake import intake
from tests.test_r2_build9_recovery import envelope,TinyProcessor
from student_pilot.p3_provenance import file_pin,digest
EX=K/'work/build9fix/inputs/extents.json';PIN=file_pin(EX);REC=json.loads(EX.read_text())
out={'extents_sha256':PIN['sha256'],'receipt_rows':len(REC['rows'])}
R=Path('/scratch/jjyeung/orch_n30/rows_r1/out')
for name,p,sha,n in (('recovery_v3',R/'recovery_v3/rows.jsonl','58389a67f9a5b51abbc06e5953937b35541ef5effc4e70e6a35092d14f288473',994),('pool_repaired',R/'vehN_pool_abs_distance/repaired/rows.jsonl','1b6bc0cee9831da378234f5cfb9e35352d5b30cf7cb5325f9fb7d6a135b53220',1579),('units_repaired',R/'vehN_units/repaired/rows_slice.jsonl','aa1432cde2aa3612e0d0e287c94aaa0aeb37dc175485a3ad044bca71f3e5ce9c',8577)):
    b=p.read_bytes();out[name]=dict(sha_ok=hashlib.sha256(b).hexdigest()==sha,rows=b.count(b'\n'),expected=n)
def norm(raw):
    p=raw.get('provenance',{});si=raw.get('student_input',{})
    ind=si.get('frame_indices') or raw.get('frame_indices') or p['frame_indices']
    fr={raw['qid']:dict(fps=si.get('fps') or p.get('fps_source',{}).get('value') or 24.,total_num_frames=ind[-1]+1,frames=[dict(path='/u/'+str(i),sha256='a'*64,source_index=i) for i in ind])}
    r=normalize(raw,fr);r.update(answer_form='routed',response_heads=['pose','depth']);return r
def reader(row,pin):
    r=Rows({'streams':{},'extent_receipt':pin,'r1_training':{'schema':'r1-training-v1'}},TinyProcessor());c=sqlite3.connect(':memory:')
    r.connections['routing']=c;c.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)');c.execute('INSERT INTO rows VALUES(0,?,?)',(json.dumps(row),'{}'))
    try:r.row('routing',0);return 'ADMIT'
    except ValueError as e:return str(e)[:60]
def ink(row,pin,fam='absolute_distance'):
    d=Path(tempfile.mkdtemp(dir=W/'tmp'));p=envelope(d,[row],'routing',fam);m=json.loads(p.read_text())
    if pin:m['extent_receipt']=pin
    p.write_text(json.dumps(m));a,rep=intake(p);return 'ADMIT' if a else rep['refusals'][0]['reason'][:60]
def both(row,pin):return dict(intake=ink(copy.deepcopy(row),pin),reader=reader(copy.deepcopy(row),pin))
# build-9 half-box rows (scannetpp/ v1) from the bound slices
S=K/'work/rows_slices/slices_final';half={}
for fam in ('a0_pool_abs_distance_reworded','a0_units','a0_recovery'):
    c=collections.Counter()
    for l in open(S/(fam+'.jsonl')):
        raw=json.loads(l);r=norm(raw);g=r.get('ground_record',r)
        if (g.get('canonical') or r['provenance'].get('canonical','')).startswith('scannetpp/'):
            v=reader(r,PIN);c[v[:30]]+=1
            if fam not in half:half[fam]=dict(qid=r['qid'],**both(r,PIN))
    half[fam+'_scannetpp_v1_reader_census']=dict(c)
out['half_box']=half
# repaired row: admits with receipt; variants
rows=[norm(json.loads(l)) for l in open(R/'vehN_pool_abs_distance/repaired/rows.jsonl')]
rep=next(r for r in rows if r.get('provenance',{}).get('repair'));full=next(r for r in rows if not r.get('provenance',{}).get('repair'))
def variant_receipt(edit,tag):
    v=copy.deepcopy(REC);edit(v);p=W/'tmp'/(tag+'.json');p.write_text(json.dumps(v));return file_pin(p)
t={}
t['repaired_with_receipt']=both(rep,PIN)
t['repaired_no_receipt']=both(rep,None)
x=copy.deepcopy(rep);x['provenance'].pop('repair');t['repaired_row_repair_dropped']=both(x,PIN)
x=copy.deepcopy(rep);g=x.get('ground_record',x);b=g['program_audit']['independent_ordered_boxes'][0];b['axesLengths']=[v/2 for v in b['axesLengths']];t['repaired_row_box_halved_back']=both(x,PIN)
t['unknown_box_status']=both(rep,variant_receipt(lambda v:v['rows'][rep['qid']].__setitem__('box_statuses',['full','unknown']),'unk'))
t['half_box_status']=both(full,variant_receipt(lambda v:v['rows'][full['qid']].__setitem__('box_statuses',['half','full']),'half'))
t['repair_sha_altered']=both(rep,variant_receipt(lambda v:v['rows'][rep['qid']].__setitem__('repair_sha256','0'*64),'rsha'))
t['row_absent_from_receipt']=both(full,variant_receipt(lambda v:v['rows'].pop(full['qid']),'absent'))
x=copy.deepcopy(full);x['answer']=str(x.get('answer'))+'0';t['full_row_answer_changed']=both(x,PIN)
t['wrong_schema_receipt']=None
try:both(full,variant_receipt(lambda v:v.__setitem__('schema','x'),'schema'))
except ValueError as e:t['wrong_schema_receipt']=str(e)
x=copy.deepcopy(full);g=x.get('ground_record',x);g['program_audit']['independent_ordered_boxes']=[];t['boxes_removed']=both(x,PIN)
out['repaired_variants']=t;out['rep_qid']=rep['qid'];out['full_qid']=full['qid']
print(json.dumps(out,indent=1));(W/'F5.json').write_text(json.dumps(out,indent=1))
