import sqlite3,json,re,random,sys
from collections import Counter,defaultdict
sys.path.insert(0,'.'); from dircls import opening, rel, lab
c=sqlite3.connect('file:/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro',uri=True)
AW=re.compile(r'away from|opposite direction|back to|turned away|back toward')
T=defaultdict(Counter); samp=defaultdict(list); n=0
for i,row in c.execute('select i,row from rows'):
    if 'object_rel_direction' not in row: continue
    d=json.loads(row)
    if not str(d.get('category','')).startswith('object_rel_direction'): continue
    n+=1
    q=d['student_input']['question']; ty=d['category'].split('_')[-1]; away=bool(AW.search(q))
    tg=d['target']; th=tg.split('</think>')[0].replace('<think>','').strip()
    L=[l for l in th.split('\n') if l.strip()]
    opts={o[0]:o[3:].strip() for o in d['student_input']['options']}; ans=opts.get(d['answer'])
    tl=[l for l in L if l.startswith('The question has me')]; tl=tl[0] if tl else ''
    turn='turn' if ('half turn' in tl or 'swap' in tl) else ('keep' if ('keep' in tl or 'no turn' in tl) else 'none')
    rl=L[1] if len(L)>1 else ''
    fb,lr=rel(rl)
    k=(ty,'away' if away else 'toward',d['pool'])
    T[k]['n']+=1; T[k]['open '+opening(th)]+=1; T[k]['turn '+turn]+=1; T[k]['ans '+str(ans)]+=1; T[k]['prerel_fb '+str(fb)]+=1
    T[k]['form '+('ifstood' if 'If I stood' in th or 'would be' in th else 'standing' if 'Standing at' in th else 'stand' if 'I stand at' in th else 'facing-from' if 'from the' in rl and 'facing' in rl else 'other')]+=1
    samp[(ty,'away' if away else 'toward')].append(dict(i=i,qid=d['qid'],pool=d['pool'],q=q.split('\n')[0],opts=d['student_input']['options'],ans=ans,trace=th))
json.dump({'|'.join(k):dict(v) for k,v in T.items()},open('v7dir_tally.json','w'),indent=0)
random.seed(20261119)
out={}
for k,v in samp.items(): out['|'.join(k)]=random.sample(v,min(30,len(v)))
json.dump(out,open('v7dir_sample.json','w'))
print('direction rows',n)
for k in sorted(T): 
    v=T[k]; print(k, v['n'], {a:b for a,b in sorted(v.items()) if a!='n'})
