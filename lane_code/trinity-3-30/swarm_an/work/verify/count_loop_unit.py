"""What repeats in counting runaways, and do the removed list rows teach same-frame repeats?"""
import sys,re,json,sqlite3,random; sys.path.insert(0,'/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
from collections import Counter
for s,t in (('dev-S1','object_counting'),('R0-dev','object_counting'),('dev-S1','relative_count')):
    rows=[r for r in K.direct('R1',200,s,types=[t]) if r['forced_close']]
    same=0;inc=0;other=0;first_same=0
    for r in rows:
        ents=[e.strip() for e in re.split(r';',r['text'][:6000])]
        tail=ents[-40:-1]
        c=Counter(tail)
        if c and c.most_common(1)[0][1]>=30: same+=1
        elif len(set(tail))>30: inc+=1
        else: other+=1
        fr=re.findall(r'frame (\d+(?:\.\d+)?)',r['text'][:400])
        first_same+= len(fr)>=2 and fr[0]==fr[1]
    print(s,t,'runaways',len(rows),'| loop of one identical entry',same,'| ever-changing entries',inc,'| other',other,'| first two listed frames identical',first_same)
# non-runaway traces: share whose list repeats a frame
for s in ('dev-S1','R0-dev'):
    rows=[r for r in K.direct('R1',200,s,types=['object_counting']) if not r['forced_close']]
    rep=[r for r in rows if (lambda f: len(f)!=len(set(f)))(re.findall(r'frame (\d+(?:\.\d+)?)',r['text'].split('</think>')[0]))]
    print(s,'non-runaway',len(rows),'with a repeated frame in the list',len(rep),'acc with repeat %.1f vs without %.1f'%(100*sum(r['score'] for r in rep)/max(1,len(rep)),100*sum(r['score'] for r in rows if r not in rep)/max(1,len(rows)-len(rep))))
# removed list rows: sample by primary key from the counting family, keep those in z.json
Z=set(json.loads(l)['row_key'] for l in open('/scratch/jjyeung/orch_n30/r1_ops6/cp/out/records/z.json') if l.strip())
fr=json.load(open('/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json'))['families']['object_counting']
ids=[i for a,b in fr for i in range(a,b+1)]; random.seed(7); pick=sorted(random.sample(ids,1200))
c=sqlite3.connect('file:/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro',uri=True)
n=0;rep=0;maxrun=Counter();lens=Counter();pools=Counter()
for k in range(0,len(pick),200):
    for i,row in c.execute('select i,row from rows where i in (%s)'%','.join(map(str,pick[k:k+200]))):
        r=json.loads(row)
        if r['qid'] not in Z: continue
        th=r['target'].split('</think>')[0]; f=re.findall(r'frame (\d+)',th)
        if len(f)<1: continue
        n+=1; pools[r.get('pool')]+=1
        run=1;best=1
        for a,b in zip(f,f[1:]):
            run=run+1 if a==b else 1; best=max(best,run)
        rep+= best>=2; maxrun[min(best,6)]+=1; lens[min(len(f),10)]+=1
print('removed counting rows sampled',n,dict(pools),'| rows with the same frame listed consecutively',rep,'| longest same-frame run histogram',sorted(maxrun.items()),'| list length histogram',sorted(lens.items()))
