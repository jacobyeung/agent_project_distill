import sqlite3,json,hashlib,collections
c=sqlite3.connect('file:/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?immutable=1&mode=ro',uri=True)
out=open('all_rows_compact.jsonl','w')
cnt=collections.Counter()
for i,r,t in c.execute("select i,row,target from rows order by i"):
    d=json.loads(r)
    tg=d.get('target')
    rec=dict(i=i,qid=d.get('qid'),row_key=d.get('row_key'),pool=d.get('pool'),qt=d.get('question_type'),cat=d.get('category'),ds=d.get('dataset'),scene=d.get('scene'),
             retrace=(d.get('retrace') or {}).get('rule'),tcol=t[:200] if t!='{}' else None,
             keys=sorted(d.keys()),q=d.get('student_input',{}).get('question'),ans=d.get('answer'))
    if not isinstance(tg,str): rec['target_type']=type(tg).__name__; tg=json.dumps(tg)
    rec['target']=tg
    cnt[(rec['qt'],rec['cat'])]+=1
    out.write(json.dumps(rec)+'\n')
print(cnt)
