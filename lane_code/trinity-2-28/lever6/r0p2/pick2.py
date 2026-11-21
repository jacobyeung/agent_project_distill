import json,numpy as np
win={'69e56cf0f8':'f2405ef4_DSC05860.JPG','4f144c7489':'e7c619ce_DSC02206.JPG'}
for s,wf in win.items():
    d=json.load(open(f'tf_{s}.json'));fr=[f for f in d['frames'] if not f.get('is_bad')]
    P={f['file_path']:np.array(f['transform_matrix']) for f in fr}
    up=np.mean([M[:3,1] for M in P.values()],0);up/=np.linalg.norm(up)
    def hz(v):v=v-(v@up)*up;return v/np.linalg.norm(v)
    w=hz(-P[wf][:3,2]);c=np.mean([M[:3,3] for M in P.values()],0)
    rows=[]
    for k,M in P.items():
        v=-M[:3,2];v/=np.linalg.norm(v)
        rows.append((k,float(hz(v)@w),float(v@up),float((M[:3,3]-c)@w)))
    print(s,'up',np.round(up,2),'|mean up| before norm ok')
    door=sorted([r for r in rows if abs(r[2])<.2],key=lambda r:(r[1]-0.5*r[3]))[:3]
    winf=sorted([r for r in rows if r[1]>.85 and .3<r[2]<.6],key=lambda r:-r[3])[:3]
    ceil=sorted(rows,key=lambda r:-r[2])[:3]
    for name,L in [('door',door),('winframe',winf),('ceiling',ceil)]:
        print(' ',name,[(r[0],round(r[1],2),round(r[2],2),round(r[3],2)) for r in L])
    print('  door2',[(r[0],round(r[1],2),round(r[2],2),round(r[3],2)) for r in sorted([r for r in rows if r[1]<-.8 and r[2]>-.1],key=lambda r:-r[3])[:3]])
    print('  winf2',[(r[0],round(r[1],2),round(r[2],2),round(r[3],2)) for r in sorted([r for r in rows if r[1]>.8],key=lambda r:-r[2])[:3]])
