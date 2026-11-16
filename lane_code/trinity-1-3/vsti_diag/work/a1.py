exec(open('load.py').read())
from collections import Counter
out=[]
def P(*a): 
    s=' '.join(str(x) for x in a); print(s); out.append(s)
for qt in REL:
    ks=sorted(k for k in nat if nat[k]['question_type']==qt)
    P('\n##',qt,len(ks))
    for arm in ('native','f17','p1m200'):
        if arm=='native': ans={k:nat[k]['answer'] for k in ks}; sc={k:nat[k]['score'] for k in ks}
        else: ans={k:cmp[arm][k]['official_fuzzy_pred'] for k in ks}; sc={k:cmp[arm][k]['official_fuzzy_score'] for k in ks}
        acc=100*sum(sc.values())/len(ks)
        if qt.startswith('obj_obj'):
            dist=Counter(opt(k,ans[k]) for k in ks); gt=Counter(opt(k,S[k]['ground_truth']) for k in ks)
            conf=Counter((opt(k,S[k]['ground_truth']),opt(k,ans[k])) for k in ks)
            P(arm,'acc',acc,'pred',dict(dist),'| gt',dict(gt),'| conf(gt,pred)',dict(conf))
        else:
            dist=Counter(ans[k] for k in ks); pos=Counter(S[k]['ground_truth'] for k in ks)
            P(arm,'acc',acc,'pred letters',dict(sorted(dist.items())),'| gt letters',dict(sorted(pos.items())))
    # agreement
    a=sum(1 for k in ks if nat[k]['score']==0 and cmp['f17'][k]['official_fuzzy_score']==1 and cmp['p1m200'][k]['official_fuzzy_score']==1)
    P('native wrong & both comparators right',a, '| native right & both wrong', sum(1 for k in ks if nat[k]['score']==1 and cmp['f17'][k]['official_fuzzy_score']==0 and cmp['p1m200'][k]['official_fuzzy_score']==0))
    L=[nat[k]['decode']['generated_tokens'] for k in ks]; P('native gen tokens mean',sum(L)/len(L),'min',min(L),'max',max(L), 'finish',dict(Counter(nat[k]['finish'] for k in ks)))
open('a1.txt','w').write('\n'.join(out))
