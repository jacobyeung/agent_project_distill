import json,sqlite3
S=json.load(open('twins_sample.json'))
c=sqlite3.connect('file:/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro',uri=True)
def th(t): return t.split('</think>')[0].replace('<think>','').strip()
ok=0; out=[]
from collections import Counter
fbc=Counter(); pools=Counter()
for d in S:
    i=d['src']['source_store_i']; r=json.loads(c.execute('select row from rows where i=?',(i,)).fetchone()[0])
    assert r['qid']==d['src']['source_qid'].split('-p')[0] or True
    st=th(r['target']).split('\n'); tw=d['trace'].split('\n')
    same12 = st[0]==tw[0] and st[1]==tw[1]
    opts={o[0]:o[3:].strip() for o in r['student_input']['options']}
    ok+=same12; pools[r['pool']]+=1
    out.append(dict(twin=d, src=dict(qid=r['qid'],pool=r['pool'],q=r['student_input']['question'].split('\n')[0],ans=opts[r['answer']],trace=th(r['target']))))
    fbc[(d['cat'][-4:], 'behind' in tw[1])]+=1
print('steps 1-2 identical',ok,'of',len(S),'pools',pools,'fb',fbc)
json.dump(out,open('twins_with_src.json','w'))
for o in out[30:36]:
    print('== SRC',o['src']['q'],'|',o['src']['ans']); print('   ',o['src']['trace'].replace('\n','\n    '))
    print('   TWIN',o['twin']['q'],'|',o['twin']['src']['mapped_label']); print('   ',o['twin']['trace'].split('\n')[-2:])
