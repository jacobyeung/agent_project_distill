import json,sys,sqlite3,collections
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/review_treen1/work');sys.path[:0]=[str(W/'pkg/work/tree_r1')]
from student_pilot.r0_exclusion import reserve
R=reserve();c=sqlite3.connect('file:/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite?mode=ro',uri=True)
hits=collections.Counter();ex=[];n=0
rm=set(json.loads(l)['row_key'] for l in open(W/'tmp/list.jsonl'))
for i,row in c.execute('SELECT i,row FROM rows'):
    r=json.loads(row);n+=1
    try:R.check(r,'vqa')
    except ValueError as e:
        hits[(r.get('question_type'),r['qid'] in rm)]+=1
        if len(ex)<10:ex.append((r['qid'],r.get('dataset'),r.get('scene'),str(e)[:120]))
out=dict(rows=n,hits={str(k):v for k,v in hits.items()},total=sum(hits.values()),examples=ex)
print(json.dumps(out,indent=1));(W/'R0_V7.json').write_text(json.dumps(out,indent=1))
