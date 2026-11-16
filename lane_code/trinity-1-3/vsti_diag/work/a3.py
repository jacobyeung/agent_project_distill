exec(open('load.py').read())
from collections import Counter,defaultdict
out=[]
def P(*a):
    s=' '.join(str(x) for x in a); print(s); out.append(s)
def cls(th):
    th=th.strip()
    if 'standing at' in th and 'facing' in th: return 'facing_bearing(VSI direction)'
    if 'level horizon' in th: return 'frame_bearing_horizon'
    if 'first seen in frame' in th and 'in front of' in th: return 'firstseen+front_order'
    if 'first seen in frame' in th: return 'firstseen_other'
    if re.search(r'\b(above|below|higher|lower)\b',th): return 'vertical_words'
    return 'other'
for qt in REL[3:]:
    ks=sorted(k for k in nat if nat[k]['question_type']==qt)
    g=defaultdict(list)
    for k in ks: g[cls(thinktext(nat[k]))].append(nat[k]['score'])
    P(qt,{c:(len(v),round(100*sum(v)/len(v))) for c,v in g.items()})
    # step-2 skeleton shapes
    sk=Counter()
    for k in ks:
        th=thinktext(nat[k]); s=re.sub(r'\d+','N',th)
        for o in re.findall(r"\(([^)]*)\)",'') : pass
        lines=[l for l in s.split('\n') if l.strip()]
        sk[lines[0][:60]]+=1
    P(' first lines',sk.most_common(5))
open('a3.txt','w').write('\n'.join(out))
