from pathlib import Path
import json,os,sqlite3,sys
from collections import Counter
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';P=L/'work/merge11/proofs/n1/half_refusals';P.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
from monitor9 import Monitor
monitor=Monitor(L/'work/tree_r1')
os.environ.update(R2_FIXTURES=str(L/'fixtures'),R2_PROOFS=str(P))
from student_pilot.r2_adapters import normalize
from student_pilot.r2_intake import intake
from student_pilot.p3_provenance import file_pin,load
from student_pilot.carrier_c1_run import Rows
from tests.test_r2_build9_recovery import envelope
pin=file_pin(B/'inputs/extents.json');audits={}
with Path('/scratch/jjyeung/orch_n30/rows_r1/out/extent_audit/ROW_AUDIT.jsonl').open() as f:
    for line in f:
        a=json.loads(line)
        if a['family'].startswith('build9_'):audits[a['qid']]=a
results={}
for name in ('a0_recovery','a0_units','a0_pool_abs_distance_reworded'):
    folder=P/name;folder.mkdir(exist_ok=True);counts=Counter();examples=[]
    reader=Rows(dict(streams={},extent_receipt=pin),None);c=sqlite3.connect(':memory:');reader.connections['routing']=c
    c.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
    with (L/'work/rows_slices/slices_final'/(name+'.jsonl')).open() as f:
        for line in f:
            raw=json.loads(line);a=audits[raw['qid']]
            if 'half' not in a['box_statuses']:continue
            indices=raw.get('frame_indices') or raw.get('provenance',{})['frame_indices']
            frame_map={raw['qid']:dict(fps=24.,total_num_frames=indices[-1]+1,frames=[dict(path='/unavailable-rgb/'+str(i),sha256='a'*64,source_index=i) for i in indices])}
            row=normalize(raw,frame_map);row.update(answer_form='routed',response_heads=['pose','depth'])
            c.execute('INSERT OR REPLACE INTO rows VALUES(0,?,?)',(json.dumps(row),'{}'))
            try:reader.row('routing',0)
            except ValueError as error:assert str(error).startswith('EXTENT_');counts['reader_refused']+=1
            else:raise AssertionError('Half box admitted')
            mp=envelope(folder,[row],'routing',name);m=load(mp);m['extent_receipt']=pin;mp.write_text(json.dumps(m))
            admitted,rep=intake(mp);assert not admitted and rep['refusals'][0]['reason'].startswith('EXTENT_');counts['intake_refused']+=1
            examples.append(dict(qid=row['qid'],box_statuses=a['box_statuses']))
            if len(examples)==5:break
    reader.close();results[name]=dict(counts=counts,examples=examples)
(P/'RESULT.json').write_text(json.dumps(results,indent=2)+'\n');monitor.save(P);print(json.dumps(results))
