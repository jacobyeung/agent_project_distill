import sqlite3,json,collections
c=sqlite3.connect('file:/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite?mode=ro',uri=True)
print([r[1] for r in c.execute('PRAGMA table_info(rows)')])
for name,(a,b) in (('box_3d',(52529,56341)),):
    cnt=collections.Counter();ex=None
    for i,row,t in c.execute('SELECT i,row,target FROM rows WHERE i BETWEEN ? AND ?',(a,b)):
        r=json.loads(row);can=(r.get('provenance') or {}).get('canonical') or r.get('dataset','?')
        cnt[(r.get('question_type'),str(r.get('dataset')),str(can).split('/')[0])]+=1
        if ex is None and 'scannetpp/' in json.dumps(r): ex=r
    print(name,dict(cnt))
    if ex: print(json.dumps(ex)[:2500])
