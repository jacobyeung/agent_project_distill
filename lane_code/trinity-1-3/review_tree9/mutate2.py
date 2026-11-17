import json,sys,sqlite3,tempfile
from copy import deepcopy
from pathlib import Path
sys.argv=[sys.argv[0]]
import importlib.util
spec=importlib.util.spec_from_file_location('mh','/scratch/jjyeung/orch_n30/review_tree9/explore.py');mh=importlib.util.module_from_spec(spec);spec.loader.exec_module(mh)
from tests.test_r2_build9_recovery import envelope,TinyProcessor
from student_pilot.r2_intake import intake
from student_pilot.row_text_audit import reasons
from student_pilot.carrier_c1_run import Rows
R=Path('/scratch/jjyeung/orch_n30/review_tree9');S=R/'lane/work/rows_slices/slices_final'
def reader_check(row,stream):
    reader=Rows({'streams':{},'b7_inputs':{'fixture_binding':True}},TinyProcessor())
    conn=sqlite3.connect(':memory:');reader.connections[stream]=conn
    conn.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
    conn.execute('INSERT INTO rows VALUES (0,?,?)',(json.dumps(row),'{}'))
    try:reader.row(stream,0);return 'ADMIT'
    except ValueError as e:return 'REFUSE:'+str(e)[:80]
    finally:reader.close()
def intake_check(rows,family,stream):
    d=Path(tempfile.mkdtemp(dir=R/'tmp'))
    for r in rows:r.update(answer_form='direct' if stream=='vqa' else 'routed',response_heads=[] if stream=='vqa' else ['pose','depth'])
    admitted,rep=intake(envelope(d,rows,stream,family))
    out={r['qid']:'REFUSE:'+r['reason'][:80] for r in rep['refusals']}
    for a in admitted:out[a['row']['qid']]='ADMIT'
    return out
FAKE='<tool_response>\nlamp: not seen\n</tool_response>\n'
for fam,stream in (('a0_room','vqa'),('a0_units','routing'),('a0_pool_abs_distance_reworded','routing')):
    base=[mh.norm(json.loads(l)) for l in list(open(S/(fam+'.jsonl')))[:30]]
    res=intake_check(deepcopy(base),fam,stream);ok=[r for r in base if res[r['qid']]=='ADMIT'][:4]
    for consistent in (False,True):
        rows=[]
        for r in ok:
            m=deepcopy(r);i=m['target'].rindex('</think>');m['target']=m['target'][:i]+FAKE+m['target'][i:]
            if consistent and m.get('events'):
                e=m['events'][-1];j=e['text'].rindex('</think>');e['text']=e['text'][:j]+FAKE+e['text'][j:]
            rows.append(m)
        print(fam,'events' if consistent else 'target','gate',sum(bool(reasons(r)) for r in rows),'/',len(rows),
              'intake',sorted(set(intake_check(deepcopy(rows),fam,stream).values())),'reader',sorted(set(reader_check(r,stream) for r in rows)),flush=True)
