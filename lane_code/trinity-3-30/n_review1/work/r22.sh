cd /scratch/jjyeung/orch_n30/n_review
cat > twins.py <<'PYEOF'
import sqlite3,json,os,hashlib,collections
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w'; U=W+'/w24/work/build22/upload/u/'
rem={}
for k,f in {'s':'w17b/work/build17/inputs/s.json','u':'w18/work/build18/inputs/u.json','union':'w21/work/build21/inputs/u_union.json','n':'inputs/records/n.json','z':'inputs/records/z.json'}.items():
    for line in open(os.path.join(W,f)):
        if line.strip(): rem.setdefault(json.loads(line)['row_key'],set()).add(k)
for r in json.load(open(W+'/w22/work/build22/inputs/naming_remove.json'))['rows']: rem.setdefault(r['qid'],set()).add('naming')
c=sqlite3.connect('file:/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite?mode=ro&immutable=1',uri=True)
qids=set(json.loads(r)['qid'] for (r,) in c.execute('select row from rows'))
bind=[json.loads(l) for l in open(U+'d8c3837019d29e9c8b7916a7e8b3c3d595890b6cad32c7dc72ba5f871a0a5108') if l.strip()]
rows=[json.loads(l) for l in open(U+'7b3d696d580386f9e8af3240fa142e2ad50eebb277a8718c97e2db497dcc925e') if l.strip()]
st=collections.Counter()
for b in bind:
    st['bind']+=1; st['src_in_v7']+=b['source_key'] in qids
    if b['source_key'] in rem: st['src_removed:'+'+'.join(sorted(rem[b['source_key']]))]+=1
tw=collections.Counter(); ex=[]
import re
for r in rows:
    tw['rows']+=1; tg=r.get('target',''); m=re.search(r'<think>(.*?)</think>',tg,re.S)
    if not m or not m.group(1).strip(): tw['answer_only']+=1
    if re.search(r'\d+\.\d+|\b\d+\s*(m|meters?|cm|degrees?)\b',m.group(1) if m else ''): tw['measure']+=1
    if r.get('qid') in rem: tw['twin_qid_removed']+=1
    tw['type:'+str(r.get('question_type'))]+=1
import random
pick=random.Random(20261119).sample(range(len(rows)),40)
for i in sorted(pick)[:40]:
    r=rows[i]; ex.append(dict(idx=i,qid=r.get('qid'),type=r.get('question_type'),q=r['student_input'].get('question','')[:200],t=r.get('target','')))
json.dump(dict(binding=dict(st),twins=dict(tw),sample=ex),open('/scratch/jjyeung/orch_n30/n_review/twins_check.json','w'),indent=1)
print(dict(st)); print(dict(tw))
for e in ex[:40]: print(e['idx'],e['qid'],e['type'],'|',e['t'].replace('\n',' / ')[:420])
PYEOF
OMP_NUM_THREADS=2 nice -n 10 timeout 900 python3 twins.py; sha256sum twins_check.json
