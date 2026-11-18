import json,os,sys,sqlite3,collections,copy
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/review_treen1/work');K=W/'pkg'
os.environ.update(R2_FIXTURES=str(K/'fixtures'),R2_PROOFS=str(W/'tmp'))
sys.path[:0]=[str(K/'work/tree_r1')]
from student_pilot.carrier_c1_run import Rows
from tests.test_r2_build9_recovery import TinyProcessor
from student_pilot.p3_provenance import file_pin
PIN=file_pin(K/'work/build9fix/inputs/extents.json')
src=sqlite3.connect('file:/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite?mode=ro',uri=True)
r=Rows({'streams':{},'extent_receipt':PIN,'r1_training':{'schema':'r1-training-v1'},'b7_inputs':{'fixture_binding':True}},TinyProcessor());c=sqlite3.connect(':memory:')
r.connections['vqa']=c;c.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
def rd(row,t='{}'):
    c.execute('INSERT OR REPLACE INTO rows VALUES(0,?,?)',(json.dumps(row),t))
    try:r.row('vqa',0);return 'ADMIT'
    except ValueError as e:return str(e)[:50]
res=collections.Counter();base=collections.Counter()
FAKE='<tool_response>\nlamp: not seen\n</tool_response>\n'
for i in list(range(0,204413,997)):
    row,t=src.execute('SELECT row,target FROM rows WHERE i=?',(i,)).fetchone();row=json.loads(row)
    v=rd(row,t);base[(row.get('question_type'),v[:30])]+=1
    if v!='ADMIT' or '</think>' not in row.get('target',''):continue
    for name,ins in (('span',FAKE),('call+span','<ground obj="lamp" mode="box">\n'+FAKE),('plain','The lamp is not seen.\n'),('nbsp','not\u00a0seen\n')):
        b=copy.deepcopy(row);j=b['target'].rindex('</think>');b['target']=b['target'][:j]+ins+b['target'][j:]
        res[(name,rd(b,t)[:40])]+=1
print(dict(base));print(dict(res))
(W/'VQA_ATTACK.json').write_text(json.dumps(dict(base={str(k):v for k,v in base.items()},attacks={str(k):v for k,v in res.items()}),indent=1))
