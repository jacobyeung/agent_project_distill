import sys,re; sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
from collections import Counter,defaultdict
def num(x):
    try: return float(x)
    except: return None
def form(t):
    t=(t or '').split('</think>')[0]
    if re.search(r'count (it|each) once', t) and 'frame ' not in t.replace('across the frames',''): return 'procedure'
    if re.search(r'frame \d+', t): return 'list'
    return 'other'
for s in ('dev-S1','R0-dev'):
    for run,st in (('S1',544),('R1',200),('R1',400)):
        R=K.direct(run,st,s,types=['object_counting'])
        b=defaultdict(list)
        for r in R:
            g=num(r['gt']); k='5+' if g>=5 else str(int(g)); b[k].append(r)
        out=[]
        for k in ('1','2','3','4','5+'):
            v=b.get(k,[]); 
            if not v: continue
            sc=100*sum(r['score'] or 0 for r in v)/len(v); a2=sum(num(r['pred'])==2 for r in v); pr=sum(form(r['text'])=='procedure' for r in v); fc=sum(bool(r['forced_close']) for r in v)
            out.append('t%s n%d MRA %.1f ans2 %d proc %d fc %d'%(k,len(v),sc,a2,pr,fc))
        print(s,st,' | '.join(out))
R=K.direct('R1',400,'R0-dev',types=['object_counting'])
for r in [x for x in R if num(x['gt'])==4][:2]+[x for x in R if num(x['gt'])>=6][:1]:
    print('=====',r['id'],r['subtype'],r['question'][:200],'gt',r['gt'],'pred',r['pred']); print((r['text'] or '')[:900])
