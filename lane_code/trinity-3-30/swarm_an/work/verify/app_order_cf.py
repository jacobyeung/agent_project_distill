"""Appearance order counterfactuals on R0-dev at step 200: answer = the option best agreeing (pairwise) with the trace's own
stated first-seen frames, or with the trace's written order."""
import sys,re,itertools,json; sys.path.insert(0,'/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
rows=K.direct('R1',200,'R0-dev',types=['obj_appearance_order'])
def agree(order,rank):
    return sum((rank[a]<rank[b]) for a,b in itertools.combinations(order,2) if a in rank and b in rank)
n=0;act=0;byfr=0;byord=0;unm=0;unm_fix=0;ties=0
for r in rows:
    th=r['text'].split('</think>')[0]
    opts={o[0]:[x.strip() for x in o.split('. ',1)[1].split(',')] for o in r['options']}
    names=opts['A']
    fr={}
    m=re.search(r'first frame showing each object: ([^\n]*)',th)
    if m:
        for part in m.group(1).rstrip('.').split(';'):
            mm=re.match(r'\s*(.*?) frame (\d+(?:\.\d+)?)\s*$',part)
            if mm: fr[mm.group(1).strip()]=float(mm.group(2))
    mo=re.search(r'order them by first appearance: ([^\n]*)',th)
    worder=[x.strip() for x in mo.group(1).rstrip('.').split(',')] if mo else []
    if len(fr)<4: continue
    n+=1; act+=r['score']
    sc={k:agree(v,fr) for k,v in opts.items()}; best=max(sc.values()); bl=[k for k,v in sc.items() if v==best]
    ties+=len(bl)>1; byfr+= (r['gt'] in bl)/len(bl)
    wrank={x:i for i,x in enumerate(worder)}
    sc2={k:agree(v,wrank) for k,v in opts.items()}; b2=max(sc2.values()); bl2=[k for k,v in sc2.items() if v==b2]; byord+=(r['gt'] in bl2)/len(bl2)
    if worder not in opts.values():
        unm+=1; unm_fix+=(r['gt'] in bl2)/len(bl2)
print('parsed',n,'of',len(rows),'| actual %.1f | option nearest to stated frames %.1f (ties %d) | option nearest to written order %.1f | unmatched-order items %d, nearest-option correct on %.1f'%(100*act/n,100*byfr/n,ties,100*byord/n,unm,unm_fix))
