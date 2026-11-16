exec(open('load.py').read())
from collections import Counter
out=[]
def P(*a):
    s=' '.join(str(x) for x in a); print(s); out.append(s)
for qt in REL[:3]:
    ks=sorted(k for k in nat if nat[k]['question_type']==qt)
    c=Counter(); 
    for k in ks:
        r=nat[k]; th=thinktext(r); q=T[k]['question']
        qf=int(re.search(r'in frame (\d+) of',q).group(1))
        m=re.search(r'find the camera \(first seen in frame (\d+)\)',th)
        cf=int(m.group(1)) if m else None
        d=dict((a.strip(),float(b)) for a,b in re.findall(r'([A-Za-z][A-Za-z \-]*?) (\d+\.\d+) m',th.split('to each:')[-1]))
        zero=[o for o,v in d.items() if v==0.0]
        pred=opt(k,r['answer']); gt=opt(k,S[k]['ground_truth'])
        argmin=min(d,key=d.get) if d else None
        c['n']+=1
        c['camera_as_object_template']+= m is not None
        c['cam_frame==q_frame']+= cf==qf
        c['has_zero']+= bool(zero)
        c['zero_picked']+= bool(zero) and pred in zero
        c['pred==argmin_stated']+= argmin==pred
        c['gt_is_zero']+= gt in zero
        c['correct']+= r['score']
        c['correct|zero']+= bool(zero) and r['score']==1
        c['correct|nozero']+= (not zero) and r['score']==1
        c['zero_and_frame_match']+= bool(zero) and cf==qf
        c['correct|frame_match']+= cf==qf and r['score']==1
        c['frame_match_n']+= cf==qf
    P(qt,dict(c))
open('a2.txt','w').write('\n'.join(out))
