import json,sys,numpy as np
win={'69e56cf0f8':'f2405ef4_DSC05860.JPG','4f144c7489':'e7c619ce_DSC02206.JPG'}
for s,wf in win.items():
    d=json.load(open(f'tf_{s}.json'));fr=[f for f in d['frames'] if not f.get('is_bad')]
    P={f['file_path']:np.array(f['transform_matrix']) for f in fr}
    def dirn(M): v=-M[:3,2]; return v/np.linalg.norm(v)
    w=dirn(P[wf]);wh=w.copy();wh[2]=0;wh/=np.linalg.norm(wh)
    pos=np.array([M[:3,3] for M in P.values()]);c=pos.mean(0)
    rows=[]
    for k,M in P.items():
        v=dirn(M);vh=v.copy();vh[2]=0;n=np.linalg.norm(vh);vh=vh/n if n>1e-6 else vh
        rows.append((k,float(vh@wh),float(v[2]),float((M[:3,3]-c)@wh)))
    print(s,len(rows),'window dir',np.round(w,2))
    door=sorted([r for r in rows if abs(r[2])<.25],key=lambda r:(r[1]-0.5*r[3]))[:4]
    winf=sorted([r for r in rows if r[1]>.8 and .25<r[2]<.6],key=lambda r:-r[2])[:4]
    ceil=sorted(rows,key=lambda r:-r[2])[:4]
    for name,L in [('door',door),('winframe',winf),('ceiling',ceil)]:
        print(' ',name,[(r[0],round(r[1],2),round(r[2],2),round(r[3],2)) for r in L])
