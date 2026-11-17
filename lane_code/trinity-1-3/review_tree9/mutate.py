"""Reviewer mutation harness: real a0_recovery rows through text gate, native intake and Rows.row."""
import json,sqlite3,sys,tempfile
from copy import deepcopy
from pathlib import Path
sys.path.insert(0,'/scratch/jjyeung/orch_n30/review_tree9')
from explore import norm
from tests.test_r2_build9_recovery import envelope,TinyProcessor
from student_pilot.r2_intake import intake
from student_pilot.row_text_audit import reasons
from student_pilot.carrier_c1_run import Rows
R=Path('/scratch/jjyeung/orch_n30/review_tree9')
SRC=R/'lane/work/rows_slices/slices_final/a0_recovery.jsonl'
MUT={
 'A_outside_not_seen':'The lamp is not seen.\n',
 'A_outside_box_unavailable':'The lamp box unavailable here.\n',
 'A_outside_unresolved':'The lamp stays unresolved.\n',
 'B_fake_complete_span':'<tool_response>\nlamp: not seen\n</tool_response>\n',
 'B_fake_span_box_unavailable':'<tool_response>\nlamp: box unavailable\n</tool_response>\n',
 'B_fake_span_unresolved':'<tool_response>\nlamp: unresolved\n</tool_response>\n',
 'C_unclosed':'<tool_response>\nlamp: not seen\n',
 'D_close_before_open':'</tool_response>\nlamp: not seen\n<tool_response>\n',
 'E_upper':'<TOOL_RESPONSE>\nlamp: not seen\n</TOOL_RESPONSE>\n',
 'E_mixed_close':'<tool_response>\nlamp: not seen\n</TOOL_RESPONSE>\n',
 'E_space_in_tag':'<tool_response >\nlamp: not seen\n</tool_response>\n',
 'E_space_lead':'< tool_response>\nlamp: not seen\n</ tool_response>\n',
 'F_model_call_and_response':'<ground obj="lamp" mode="box">\n<tool_response>\nlamp: not seen\n</tool_response>\n',
 'G_two_spans_status_between':'<tool_response>\na\n</tool_response> not seen <tool_response>\nb\n</tool_response>\n',
 'H_heading_in_span':'<tool_response>\nheading unavailable\n</tool_response>\n',
 'H_gravity_in_span':'<tool_response>\ngravity guard\n</tool_response>\n',
 'H_tower_in_span':'<tool_response>\ntower_scale_rule\n</tool_response>\n',
 'L_double_space':'The lamp is not  seen.\n',
 'L_newline':'The lamp is not\nseen.\n',
 'L_nbsp':'The lamp is not\u00a0seen.\n',
}
def mutate(row,s,consistent):
    m=deepcopy(row);i=m['target'].rindex('</think>');m['target']=m['target'][:i]+s+m['target'][i:]
    if consistent:
        e=m['events'][-1];assert e['kind']=='canonical_text';j=e['text'].rindex('</think>');e['text']=e['text'][:j]+s+e['text'][j:]
    return m
def reader_check(row,stream='routing'):
    reader=Rows({'streams':{},'b7_inputs':{'fixture_binding':True}},TinyProcessor())
    conn=sqlite3.connect(':memory:');reader.connections[stream]=conn
    conn.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
    conn.execute('INSERT INTO rows VALUES (0,?,?)',(json.dumps(row),'{}'))
    try:reader.row(stream,0);return 'ADMIT'
    except ValueError as e:return 'REFUSE:'+str(e)[:90]
    finally:reader.close()
def intake_check(rows,family='a0_recovery'):
    d=Path(tempfile.mkdtemp(dir=R/'tmp'))
    for r in rows:r.update(answer_form='routed',response_heads=['pose','depth'])
    admitted,rep=intake(envelope(d,rows,'routing',family))
    out={r['qid']:'REFUSE:'+r['reason'][:90] for r in rep['refusals']}
    for a in admitted:out[a['row']['qid']]='ADMIT'
    return out
base=[]
with SRC.open() as f:
    for line in f:
        raw=json.loads(line);row=norm(raw);base.append(row)
        if len(base)>=40:break
res=intake_check(deepcopy(base));ok=[r for r in base if res[r['qid']]=='ADMIT'][:5]
print('baseline admitted',sum(v=='ADMIT' for v in res.values()),'of',len(base),'; using',[r['qid'] for r in ok])
table={}
for name,s in MUT.items():
    for consistent in (False,True):
        rows=[mutate(r,s,consistent) for r in ok]
        gate=[bool(reasons(r)) for r in rows]
        ik=intake_check(deepcopy(rows))
        rd=[reader_check(r) for r in rows]
        key=name+('/events' if consistent else '/target')
        table[key]=dict(text_gate_refuses=sum(gate),intake=sorted(set(ik.values())),reader=sorted(set(rd)),n=len(rows))
        print(key,json.dumps(table[key]))
(R/'proofs/MUTATION_RESULTS.json').write_text(json.dumps(dict(rows=[r['qid'] for r in ok],source=str(SRC),results=table),indent=1))
