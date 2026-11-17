import json,collections,re,numpy as np
R=[json.loads(l) for l in open('f3/r2/sj/h10sub3_b01ec87a6f29b00029ad2/items.jsonl')]
I={x['id']:x for x in json.load(open('f3/p446/items/devs1_routed.json'))['items']}
C=json.load(open('conv.json')); conv=set(C['conv']); rest=set(C['rest'])
base=[x for x in R if x['mode']=='none']
sc=lambda x:x['measurements']['M2']['task_accuracy']
def unit(q):
    q=q.lower()
    for u,k in (('centimet','cm'),('feet','ft'),('foot','ft'),('inch','in'),('meter','m'),('metre','m')):
        if u in q: return k
    return '?'
M=[x for x in base if unit(I[x['id']]['question'])=='m']
cl=[x for x in M if x['id'] not in conv and x['id'] not in rest]; cv=[x for x in M if x['id'] in conv]; rs=[x for x in M if x['id'] in rest]
print('metre items',len(M),'clean',len(cl),'conv',len(cv),'rest',len(rs),'MRA all',round(np.mean([sc(x) for x in M]),3),'clean',round(np.mean([sc(x) for x in cl]),3),'conv now',round(np.mean([sc(x) for x in cv]),3) if cv else None,'capped conv',sum(x['output']['finish']=='max_calls' for x in cv))
g=(len(cv)*np.mean([sc(x) for x in cl])-sum(sc(x) for x in cv))/len(M); print('metre-subset (a) gain task pts',round(100*g,1),'-> ReVSI pts if ReVSI not-seen rate equals dev-S1 metre rate',round(100*g*0.143,2))
# (c) alone: capped reads answer like answered not-seen reads
ans=[x for x in base if (x['id'] in conv or x['id'] in rest) and x['output']['finish']!='max_calls']
m_ans=np.mean([sc(x) for x in ans]); capped=[x for x in base if x['output']['finish']=='max_calls']
print('answered not-seen reads',len(ans),'MRA',round(m_ans,3),'capped',len(capped),'(c) gain all-units',round(100*len(capped)*m_ans/150,1))
ansm=[x for x in ans if unit(I[x['id']]['question'])=='m']; capm=[x for x in capped if unit(I[x['id']]['question'])=='m']
print('metre: answered ns',len(ansm),'MRA',round(np.mean([sc(x) for x in ansm]),3) if ansm else None,'capped',len(capm))
# per dataset read-level not-seen rate
D=collections.Counter((I[x['id']]['dataset'], x['id'] in conv or x['id'] in rest) for x in base)
for d in ('scannet','scannetppv2','arkitscenes'): print(d,'ns reads',D[(d,True)],'of',D[(d,True)]+D[(d,False)])
