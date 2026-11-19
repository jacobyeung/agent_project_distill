import sqlite3,json,hashlib,random,sys,os,re
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w'
db='/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite'
SEED=20261119
rem={}
lists={'s':'w17b/work/build17/inputs/s.json','u':'w18/work/build18/inputs/u.json','union':'w21/work/build21/inputs/u_union.json','n':'inputs/records/n.json','z':'inputs/records/z.json'}
for k,f in lists.items():
    b=open(os.path.join(W,f),'rb').read(); print(k,f,hashlib.sha256(b).hexdigest()[:16],file=sys.stderr)
    for line in b.decode().splitlines():
        if line.strip(): rem.setdefault(json.loads(line)['row_key'],[]).append(k)
nm=json.load(open(os.path.join(W,'w22/work/build22/inputs/naming_remove.json')))
for r in nm['rows']: rem.setdefault(r['qid'],[]).append('naming')
print('removal keys',len(rem),'naming rows',len(nm['rows']),file=sys.stderr)
c=sqlite3.connect('file:'+db+'?mode=ro&immutable=1',uri=True)
ids=[];cats={};removed=0
for i,row in c.execute('select i,row from rows'):
    r=json.loads(row); q=r.get('qid')
    if q in rem: removed+=1; continue
    ids.append(i); t=r.get('question_type') or r.get('category'); cats[t]=cats.get(t,0)+1
print('admitted_by_lists',len(ids),'removed',removed,file=sys.stderr)
json.dump(dict(admitted=len(ids),removed=removed,cats=cats),open('/scratch/jjyeung/orch_n30/n_review/vqa_counts.json','w'),indent=1)
rng=random.Random(SEED); pick=sorted(rng.sample(ids,40))
out=[]
for i in pick:
    row,target=c.execute('select row,target from rows where i=?',(i,)).fetchone(); r=json.loads(row)
    si=r.get('student_input',{})
    out.append(dict(i=i,qid=r.get('qid'),type=r.get('question_type') or r.get('category'),dataset=r.get('dataset'),scene=r.get('scene'),pool=r.get('pool'),head_program=r.get('head_program'),
        question=(si.get('question') or r.get('question')),answer=r.get('answer'),target=target))
json.dump(dict(seed=SEED,db_sha='210b2534',sample=out),open('/scratch/jjyeung/orch_n30/n_review/vqa_sample40.json','w'),indent=1)
print(json.dumps(dict(seed=SEED,ids=pick)))
