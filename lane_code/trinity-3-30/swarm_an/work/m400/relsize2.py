import sys,re; sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
from collections import Counter,defaultdict
T=['relative_size_object']
def form(t):
    t=t.split('</think>')[0]
    if re.search(r'nearest|farthest|closest|from the camera',t): return 'distance-order'
    if re.search(r'\d+(\.\d+)?\s*(cm|m)\b',t): return 'measured'
    if re.search(r'order them',t): return 'size-order'
    if re.search(r'(shorter|longer|larger|smaller|bigger) than',t): return 'bare-compare'
    return 'other'
S={}
for run,st in (('S1',544),('R1',100),('R1',200),('R1',400)):
    S[st]={r['id']:r for r in K.direct(run,st,'dev-S1',types=T)}
for st in (544,100,200,400):
    c=defaultdict(lambda:[0,0])
    for r in S[st].values(): f=form(r['text'] or ''); c[f][0]+=1; c[f][1]+=int((r['score'] or 0)<0.5)
    print(st,{k:'n%d wr%d'%tuple(v) for k,v in sorted(c.items())})
for a,b in ((544,400),(200,400)):
    fl=Counter()
    for i in S[400]:
        ra=(S[a][i]['score'] or 0)>0.5; rb=(S[b][i]['score'] or 0)>0.5
        if ra!=rb: fl[('R->W' if ra else 'W->R', form(S[b][i]['text'] or ''))]+=1
    print('flips %d->%d'%(a,b),dict(fl))
# measured: does the stated number order match the answer? and object size regression between steps
for a,b in ((200,400),(544,400)):
    for lab in ('R->W','W->R'):
        L=[]
        for i in S[400]:
            ra=(S[a][i]['score'] or 0)>0.5; rb=(S[b][i]['score'] or 0)>0.5
            if ra!=rb and (('R->W' if ra else 'W->R')==lab): L.append('%s(%s)'%(i[-6:],form(S[b][i]['text'] or '')[:4]))
        print(a,b,lab,len(L),' '.join(L))
# accuracy of measured traces: does answer follow stated numbers?
