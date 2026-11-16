import numpy as np,json,sqlite3,collections,re,sys,math
from multiprocessing import Pool
DB='file:/scratch/jjyeung/orch_n30/rows_a2/vsti/out/vsti_rel_v3/rows.sqlite?mode=ro'
def load_rows():
    db=sqlite3.connect(DB,uri=True)
    return [json.loads(t) for (t,) in db.execute('select row from rows order by i')]
def lift(z,f,conv):
    d=z['depth'][f].astype(float);H,W=d.shape
    v,u=np.mgrid[0:H,0:W]
    K=z['K_frames'][f] if 'K_frames' in z else z['K']
    x=(u+.5-K[0,2])/K[0,0];y=(v+.5-K[1,2])/K[1,1]
    if conv=='cv': cam=np.stack([x*d,y*d,d],-1)
    else: cam=np.stack([x*d,-y*d,-d],-1)  # OpenGL-style alternative (y up, -z forward)
    M=z['c2w'][f].astype(float)
    return cam@M[:3,:3].T+M[:3,3], d>0
def rot(z,j,layout):
    A=z['obb_axes'][j].reshape(3,3).astype(float)
    return A if layout=='rows' else A.T
def boxdist(p,c,R,h):
    l=R@(p-c); return float(np.linalg.norm(np.maximum(np.abs(l)-h,0)))
def work(args):
    path,rs=args
    z=dict(np.load(path)); out=dict(path=path,rows=[],src={})
    ids=list(map(int,z['ids']));labels=[str(x) for x in z['labels']]
    n=len(z['inst']); valid=z['valid'].astype(bool)&(z['depth']>0).any(axis=(1,2))
    # source convention: sample 8 valid frames
    fr=np.flatnonzero(valid)[::4][:8]
    stats={}
    for conv in ['cv','gl']:
        P=[];I=[]
        for f in fr:
            w,ok=lift(z,f,conv);P.append(w[ok][::5]);I.append(z['inst'][f][ok][::5])
        P=np.concatenate(P);I=np.concatenate(I)
        for layout in ['rows','cols']:
            for fac in [.5,1.]:
                ins=[];rat=[]
                for j,i in enumerate(ids):
                    q=P[I==i]
                    if len(q)<20:continue
                    R=rot(z,j,layout);l=np.abs((q-z['obb_centroid'][j])@R.T)
                    ins.append(float(np.mean((l<=z['obb_lengths'][j]*fac+.05).all(1))))
                    rat.append(float(np.median(np.quantile(l/np.maximum(z['obb_lengths'][j],.02),.98,axis=0).max())))
                stats[f'{conv}:{layout}:{fac}']=(float(np.mean(ins)) if ins else None, float(np.median(rat)) if rat else None)
        if conv=='cv':
            # floor plane: floor-labelled points
            fl=[i for i,l in zip(ids,labels) if l.strip().lower()=='floor']
            F=P[np.isin(I,fl)]
            if len(F)>200:
                _,_,vh=np.linalg.svd(F-F.mean(0),full_matrices=False);nrm=vh[-1]
                camz=np.median(z['c2w'][valid,2,3]); out['src']['floor_normal_z']=float(abs(nrm[2])); out['src']['cam_above_floor_z']=float(camz-np.median(F[:,2]))
            hz=P[:,2]; base=np.percentile(hz,1); out['src']['cam_minus_p1_z']=float(np.median(z['c2w'][valid,2,3])-base)
            out['src']['camy_dot_z']=float(np.median(z['c2w'][valid,2,1]))
    out['src']['conv']=stats
    best=max([k for k in stats if k.startswith('cv') and stats[k][0] is not None],key=lambda k:(stats[k][0]>=.9, -float(k.split(':')[2]) if stats[k][0]>=.9 else 0, stats[k][0]),default=None)
    # independent factor: smallest factor with containment>=.9 among cv; layout by higher containment at that factor
    fac=None;layout=None
    for fc in [.5,1.]:
        cand=[(stats[f'cv:{lay}:{fc}'][0] or 0,lay) for lay in ['rows','cols']]
        sc,lay=max(cand)
        if sc>=.9: fac,layout=fc,lay;break
    out['src']['my_factor']=fac;out['src']['my_layout']=layout
    for r in rs:
        p=r['provenance'];t=r['question_type'];f=p['camera_frame'];o=dict(qid=r['qid'],t=t,ds=r['dataset'],errors=[])
        if list(z['frame_indices'])!=r['student_input']['frame_indices']:o['errors'].append('frame_indices')
        if p['geometry_audit']['box_half_factor']!=fac or p['geometry_audit']['axes_layout']!=('rows' if layout=='rows' else 'columns'):o['errors'].append(f'convention gen={p["geometry_audit"]["box_half_factor"]},{p["geometry_audit"]["axes_layout"]} mine={fac},{layout}')
        M=z['c2w'][f-1].astype(float);cam=M[:3,3]
        objs=[]
        for ins in p['instances']:
            j=ids.index(ins['id']);lab=labels[j]
            sh=(z['inst']==ins['id']).reshape(n,-1).mean(1)
            vis=np.flatnonzero(sh>=.002)
            fs=int(vis[0])+1 if len(vis) else None
            R=rot(z,j,layout or 'rows');h=z['obb_lengths'][j]*(fac or .5);c=z['obb_centroid'][j]
            pc=np.linalg.inv(M)@np.r_[c,1]
            objs.append(dict(label=lab,fs=fs,cited=ins['frame'],share_f=float(sh[f-1]),share_cited=float(sh[ins['frame']-1]),d=boxdist(cam,c,R,h),dc=float(np.linalg.norm(cam-c)),zc=float(c[2]),x=pc[0],zz=pc[2],
                             inimg=bool(pc[2]>0 and 0<=z['K'][0,0]*pc[0]/pc[2]+z['K'][0,2]<z['inst'].shape[2] and 0<=z['K'][1,1]*pc[1]/pc[2]+z['K'][1,2]<z['inst'].shape[1])))
        for ob in objs:
            if ob['fs']!=ob['cited']:o['errors'].append(f'first_seen {ob["label"]} cited {ob["cited"]} mine {ob["fs"]}')
            if f'locate the {ob["label"]}, first seen in frame {ob["fs"]}.' not in r['target']:o['errors'].append('locate line missing')
        ch=[s[3:] for s in r['student_input']['options']];ans=ch[ord(r['answer'])-65]
        if t.startswith('camera_'):
            m=min(objs,key=lambda q:q['d']);mine=m['label']
            o['center_answer']=min(objs,key=lambda q:q['dc'])['label']
            ds=sorted(q['d'] for q in objs);o['min_gap']=ds[1]-ds[0]
        else:
            a,b=objs
            if t.endswith('nf'):mine='Near' if a['d']<b['d'] else 'Far';o['center_answer']='Near' if a['dc']<b['dc'] else 'Far'
            elif t.endswith('ud'):mine='Up' if a['zc']>b['zc'] else 'Down';o['center_answer']=mine
            else:
                mine='Left' if math.atan2(a['x'],a['zz'])<math.atan2(b['x'],b['zz']) else 'Right'
                o['center_answer']='Left' if a['x']/a['zz']<b['x']/b['zz'] else 'Right'
        o['mine']=mine;o['ans']=ans
        if mine!=ans:o['errors'].append(f'answer gen={ans} mine={mine}')
        o['vis_f']=[q['share_f']>=.002 for q in objs];o['inimg']=[q['inimg'] for q in objs]
        o['fs_lt_f']=[q['fs']<=f for q in objs if q['fs']]
        o['labels']=[q['label'] for q in objs]
        out['rows'].append(o)
    return out
if __name__=='__main__':
    rows=load_rows();g=collections.defaultdict(list)
    for r in rows:g[r['provenance']['raster']].append(r)
    items=sorted(g.items())
    if len(sys.argv)>1: items=items[::int(sys.argv[1])]
    res=[]
    with Pool(8) as pool:
        for k,x in enumerate(pool.imap_unordered(work,items,chunksize=2)):
            res.append(x)
            if k%100==0:print(k,flush=True)
    json.dump(res,open('rv_out.json','w'))
