"""K1-X factorial in the served reader, CPU-only and local scratch inputs."""
import os
for _n in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_n]='1'
os.environ['CUDA_VISIBLE_DEVICES']=''
import argparse, ast, hashlib, io, itertools, json, math, re, sys, time, types
from collections import Counter
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
SEED=20261120
DRAWS=10000


def clean(x):
    if isinstance(x,np.ndarray):return clean(x.tolist())
    if isinstance(x,np.generic):return clean(x.item())
    if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)):return [clean(v) for v in x]
    if isinstance(x,float) and not math.isfinite(x):return None
    return x


def write(path,x):
    path=Path(path)
    assert path.resolve().is_relative_to(ROOT)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(clean(x),indent=2,allow_nan=False)+'\n')


def declarations(path,names,bindings):
    nodes=[n for n in ast.parse(Path(path).read_text()).body
           if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
    assert len(nodes)==len(names),(path,names)
    ns=dict(bindings)
    exec(compile(ast.Module(nodes,[]),str(path),'exec'),ns)
    return types.SimpleNamespace(**{n:ns[n] for n in names})

mra=declarations(ROOT/'vendor/gd_harness.py',['mra'],dict(np=np,math=math)).mra


class Inputs:
    def __init__(self):self.hashes={};self.bytes=0
    def read(self,path):
        p=Path(path).resolve()
        assert p.is_relative_to('/scratch'),p
        b=p.read_bytes();self.bytes+=len(b)
        self.hashes[str(p)]=dict(sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
        return b
    def json(self,path):return json.loads(self.read(path))
    def npz(self,path):
        with np.load(io.BytesIO(self.read(path)),allow_pickle=False) as z:
            return {k:z[k] for k in z.files}
    def rows(self,path,arms):
        # Hash the complete receipt and parse only requested arms.
        data=self.read(path)
        return [r for l in data.splitlines() if any(('"arm": "'+a+'"').encode() in l for a in arms)
                for r in [json.loads(l)] if r['arm'] in arms]


def options(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['run','test','summarize','inventory','prepare'],nargs='?',default='run')
    defaults=dict(labels='/scratch/jjyeung/n30_mirror/gt_audit/gt_audit/work/k1audit/K1_LABELS_CORRECTED.jsonl',
        boxes='/scratch/jjyeung/n30_mirror/gt_audit/gt_audit/work/k1audit/K1_BOX_AUDIT.json',
        rowsets='/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS',
        train1012='/scratch/jjyeung/orch_n30/sb_k1012/out/K1_TRAIN_1012.txt',
        manifest='/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json',
        gd='/scratch/jjyeung/orch_n30/k1_ops3/work/e3gd',
        ladder='/scratch/jjyeung/orch_n30/sb_kbox4',
        tree='/scratch/jjyeung/orch_n30/b04host3/tree_rebuild/work/base/tree_b01ce449',
        selector='/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/heads/selector/work/run_iso',
        convert='/scratch/jjyeung/k1/run_convert_2',tower='/scratch/jjyeung/k1/run_tower_sam_2',
        own='/scratch/jjyeung/k1/own_170235/native/probe',
        towers='/scratch/jjyeung/orch_n30/geo_k1/geom',out=str(ROOT/'out'))
    for n,v in defaults.items():p.add_argument('--'+n,type=Path,default=Path(v))
    p.add_argument('--heavy-io-approved',action='store_true',help='Set only after explicit approval in the session')
    p.add_argument('--phase',choices=['parity','factorial','all'],default='all')
    p.add_argument('--capture',action='append')
    p.add_argument('--workers',type=int,default=1,choices=range(1,9))
    return p.parse_args(argv)


def dependencies(args):
    sel=args.selector.parents[1]
    sys.path[:0]=[str(args.ladder/'reader_src'),str(sel/'sl118'),str(sel),str(args.tree)]
    import torch
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    from scipy import ndimage
    from e2e_reader import grounding as G, geometry as geometry
    from e2e_reader.stage1 import StageOne,median_ratio
    from student_pilot import routed_features as F,tower_scale_rule
    from selector_head import load_head
    mathv=declarations(ROOT/'vendor/ladder_math_v2.py',['fusion_box'],dict(np=np,Counter=Counter))
    pricing=declarations(ROOT/'vendor/ladder_pricing.py',['lift_frames','session_distance'],
                         dict(np=np,re=re,fusion_box=mathv.fusion_box))
    detect=declarations(ROOT/'vendor/ladder_predicted.py',['cache_detect'],dict(np=np)).cache_detect
    objects=declarations(ROOT/'vendor/ladder_train_pricing.py',['empty','majority','Objects'],
        dict(np=np,Counter=Counter,ndimage=ndimage,torch=torch,G=G,F=F,StageOne=StageOne,cache_detect=detect))
    oracle=declarations(ROOT/'vendor/e3_harness.py',['oracle_scale'],dict(np=np,tower_scale_rule=tower_scale_rule)).oracle_scale
    return types.SimpleNamespace(**locals())


def metadata(args,inputs):
    labels={r['id']:r for r in map(json.loads,inputs.read(args.labels).splitlines())}
    assert inputs.hashes[str(args.labels)]['sha256'].startswith('d781ac7b')
    sets={s:set(inputs.read(args.rowsets/f'K1_{f}.txt').decode().splitlines())
          for s,f in [('heldout','HELDOUT_216'),('train','TRAIN_1037')]}
    sets['train1012']=set(inputs.read(args.train1012).decode().splitlines())
    assert len(sets['heldout'])==216 and len(sets['train'])==1037 and len(sets['train1012'])==1012
    assert sets['train1012']<=sets['train'] and not sets['train']&sets['heldout']
    manifest=inputs.json(args.manifest)
    ids=sets['train']|sets['heldout']
    captures=[]
    for c0 in manifest['captures']:
        rows=[r for r in c0['rows'] if r['id'] in ids]
        if rows:
            c=dict(c0,rows=rows);captures.append(c)
    assert len(captures)==259
    refs=inputs.rows(args.ladder/'out/box_ladder/PER_ITEM.jsonl',{'A0_deployed','A2_gt_masks'})
    refs={(r['arm'],r['row_id']):r for r in refs}
    gd=inputs.rows(args.gd/'out/PER_ITEM.jsonl',{'GT','GD_reviewed'})
    gd={(r['arm'],r['row_id']):r for r in gd if r['type']=='object_abs_distance' and r['row_id'] in ids}
    boxes=inputs.json(args.boxes)
    boxes={(r['canonical'],r['box']['instance_id']):r for r in boxes.values()}
    freeze=inputs.json(args.ladder/'out/box_ladder/FREEZE.json')['fused_frozen']['rule']
    return types.SimpleNamespace(**locals())


def key(c):return hashlib.sha256(json.dumps(c['canonical'],sort_keys=True,allow_nan=False).encode()).hexdigest()[:16]


def load_capture(c,args,I,D):
    k=key(c);t=I.npz(args.tower/k/'tower.npz');rec=I.json(args.tower/k/'PHASE_COMPLETE.json')
    own=I.npz(args.own/k/'own.npz')
    ownrec=args.own/k/'PHASE_COMPLETE.json'
    if ownrec.exists():
        receipt=I.json(ownrec)
        assert I.hashes[str(args.own/k/'own.npz')]['sha256']==receipt['files']['own.npz']
        assert receipt['capture_sha256']==rec['capture_sha256']
    assert np.array_equal(t['frame_indices'][t['anchor_slots']],c['anchor_indices'])
    scale=D.median_ratio(t['depth_grid'],t['depth_conf_grid'],own['depth'])
    served=float(D.torch.tensor(float(np.log(scale)),dtype=D.torch.float32).exp())
    geo=D.geometry.from_tower(t['raw_pose'],t['anchor_slots'],t['frame_indices'],t['depth_grid'],t['grid_uv'],own['gravity'],served,rec['source_hw'])
    path=args.convert/k/'geometry.npz'
    fallback=not path.exists()
    if path.exists():
        z=I.npz(path)
        stored=D.geometry.from_arrays(**{n:z[n] for n in ['K','canvas_to_source','camera_to_world','depth_grid','grid_uv','anchor_frame_indices']},scale=served)
        assert np.array_equal(stored.C,geo.C) and np.array_equal(stored.depth_grid,geo.depth_grid)
    gt=I.npz(c['gt']['path'])
    assert I.hashes[c['gt']['path']]['sha256']==c['gt']['sha256']
    assert np.array_equal(gt['frame_indices'],c['anchor_indices'])
    gt['inst']=gt.get('inst',gt.get('instances'))
    cache=I.json(args.convert/k/'candidates.json')
    so,so_diag=D.oracle(t,gt,'specified')
    provenance=dict(served_scale=served,unrounded_own_scale=scale,oracle_scale=so,
        gt_to_own_metric=served/so,oracle_diagnostic=so_diag,convert_missing=fallback,
        source_tower=str(args.tower/k/'tower.npz'),source_own=str(args.own/k/'own.npz'),
        own_receipt_available=ownrec.exists(),source_candidates=str(args.convert/k/'candidates.json'))
    return geo,t,own,gt,cache,provenance


def selected_masks(c,names,geo,cache,gt,head,D):
    # Objects.load is copied unchanged; no oracle labels enter A0.
    objects=D.objects.Objects(c,cache,geo,head,gt,dict(rows=[],same_geometry=False))
    masks={};choices={}
    for n in names:
        d=objects.load(n);choice=d['A0']
        shape=tuple(D.F.OUTPUT_SHAPE)
        mask=np.zeros((32,)+shape,bool)
        members=[]
        if choice>=0:
            for p in d['tracks'][choice].proposals:
                m=d['raw'][p.frame-1][p.index]['mask'][::2,::2]
                assert m.shape==shape
                mask[p.frame-1]=m;members.append([p.frame,p.index])
        masks[n]=mask
        choices[n]=dict(candidate_id=d['accepted'][choice]['candidate_id'] if choice>=0 else None,members=members)
    return masks,choices


def gt_masks(c,names,gt):
    return {n:(gt['inst']==c['gt_name_ids'][n][0])&gt['valid'].astype(bool)[:,None,None] for n in names}


def sample_gt(gt,axis):
    h,w=gt['depth'].shape[1:]
    x=np.clip(np.floor(axis/1000*w).astype(int),0,w-1)
    y=np.clip(np.floor(axis/1000*h).astype(int),0,h-1)
    d=gt['depth'][:,y[:,None],x[None,:]].astype(float)
    d[~gt['valid'].astype(bool)]=np.nan
    return d


def gt_camera_poses(gt):
    """Repair only small rotation serialization errors; keep the reader guard."""
    C=np.array(gt['c2w'],float,copy=True)
    valid=gt['valid'].astype(bool)
    R=C[valid,:3,:3]
    orth=np.max(abs(R@R.transpose(0,2,1)-np.eye(3)),axis=(1,2))
    det=np.linalg.det(R)
    if np.any(orth>1e-5) or np.any(abs(det-1)>1e-5):
        raise ValueError('GT rotations exceed bounded serialization-error repair')
    repaired=[]
    for i in np.flatnonzero(valid):
        r=C[i,:3,:3]
        if np.allclose(r@r.T,np.eye(3),atol=1e-6) and np.allclose(np.linalg.det(r),1.,atol=1e-6):continue
        u,_,vt=np.linalg.svd(r)
        q=u@vt
        assert np.linalg.det(q)>0
        repaired.append(dict(anchor_slot=int(i),max_element_adjustment=float(abs(q-r).max())))
        C[i,:3,:3]=q
    return C,dict(repaired_anchors=repaired,max_raw_orthogonality_error=float(orth.max()),
                  max_raw_determinant_error=float(abs(det-1).max()),repair_bound=1e-5)


def swapped(geo,t,own,gt,meta,depth,pose,scale,D):
    s=meta['served_scale'] if scale=='own' else meta['oracle_scale']
    q=s/meta['oracle_scale']
    # All cells retain the reader's intrinsics and 51x51 endpoint depth grid.
    d=t['depth_grid']*s if depth=='G3T' else sample_gt(gt,t['grid_uv'])*q
    if depth=='own':d=np.asarray(own['depth'],float)
    C=np.array(geo.C,copy=True)
    C[:,:3,3]*=s/meta['served_scale']
    if pose=='GT':
        C=gt_camera_poses(gt)[0]
        C[:,:3,3]*=q
    valid=gt['valid'].astype(bool) if depth=='GT' or pose=='GT' else np.ones(32,bool)
    if pose=='GT':
        # Invalid GT anchors never answer. Finite placeholders only satisfy the
        # reader's array validator; has() excludes them from the program.
        C[~valid]=np.eye(4)
    result=D.geometry.from_arrays(K=geo.K,canvas_to_source=geo.A,camera_to_world=C,scale=1.,
        depth_grid=d,grid_uv=t['grid_uv'],anchor_frame_indices=c_anchors(geo))
    if not valid.all():
        result.has=lambda frame:type(frame) is int and 1<=frame<=32 and bool(valid[frame-1])
    return result


def c_anchors(geo):return np.array(geo.frame_map.source_indices)


def lifted(masks,geo,D):
    return {n:dict(D.pricing.lift_frames(n,m,geo,D.G),boxes={}) for n,m in masks.items()}


def predict(row,geo,objects,D,rule='best1'):
    try:
        p,ref,raw,printed=D.pricing.session_distance(row,geo,objects,D.G,rule)
        return dict(prediction=p,refusal=ref,printed=printed)
    except (ValueError,KeyError,IndexError) as e:
        return dict(prediction=None,refusal=type(e).__name__+':'+str(e),printed={})


def cell_name(m,d,p,s):return '/'.join((m,d,p,s))
CELLS=[cell_name(*x) for x in itertools.product(['GT','deployed'],['G3T','GT'],['G3T','GT'],['own','GT'])]
EXTRAS=[m+'/'+d for m in ['GT','deployed'] for d in ['own_depth','Pi3X','DA3','oracle_extent','oracle_centre','voted_GT']]
BASE='GT/G3T/G3T/own'
DBASE='deployed/G3T/G3T/own'
END='GT/GT/GT/GT'
DEND='deployed/GT/GT/GT'


def extent_objects(c,objects,gt,geo,boxes,kind):
    # Register GT annotations through camera 1, preserving the served box axes.
    if not gt['valid'][0]:raise ValueError('oracle_box_registration_anchor_1_invalid')
    transform=geo.C[0,:3,:3]@gt['c2w'][0,:3,:3].T
    origin=geo.C[0,:3,3]-transform@gt['c2w'][0,:3,3]
    result={}
    for n,obj in objects.items():
        new=dict(obj,boxes=dict(obj['boxes']))
        if obj['seen'] and 'best1' in obj['boxes']:
            record=boxes[(c['canonical'],c['gt_name_ids'][n][0])]
            if record['status'] not in ('full','half'):raise ValueError('unresolved_extent_convention')
            b=record['box'];raw=dict(obj['boxes']['best1'])
            if kind=='oracle_centre':raw['centroid']=transform@np.array(b['centroid'])+origin
            else:
                axes=np.array(b['normalizedAxes']).reshape(3,3)@transform.T
                lengths=np.array(b['axesLengths'])*(2 if record['status']=='half' else 1)
                # Extent along each retained served axis of the oriented GT box.
                raw['axesLengths']=np.abs(np.asarray(raw['normalizedAxes'])@axes.T)@lengths
            new['boxes']['best1']=raw
        result[n]=new
    return result


def diagnostics(c,gmasks,geo,own_geo,gt,objects,D):
    depth={}
    for n,masks in gmasks.items():
        values={k:[] for k in ['truth','G3T','own']}
        for f,mask in enumerate(masks,1):
            uv=D.G.mask_pixels(mask)
            if not len(uv):continue
            h,w=gt['depth'].shape[1:]
            x=np.clip((uv[:,0]*w/1000).astype(int),0,w-1);y=np.clip((uv[:,1]*h/1000).astype(int),0,h-1)
            truth=gt['depth'][f-1,y,x]
            values['truth'].append(truth)
            values['G3T'].append(geo.depth(f,uv));values['own'].append(own_geo.depth(f,uv))
        out={}
        if values['truth']:
            truth=np.concatenate(values['truth'])
            for k in ['G3T','own']:
                d=np.concatenate(values[k]);ok=np.isfinite(truth)&(truth>0)&np.isfinite(d)&(d>0)
                if ok.any():
                    ratio=float(np.median(truth[ok]/d[ok]))
                    out[k]=dict(n=int(ok.sum()),eligible=int(np.count_nonzero(np.isfinite(truth)&(truth>0))),
                        metric=float(np.mean(abs(d[ok]-truth[ok])/truth[ok])),
                        fitted=float(np.mean(abs(d[ok]*ratio-truth[ok])/truth[ok])),fit=ratio)
        depth[n]=out
    result={}
    for r in c['rows']:
        a,b=r['operands'];obs=objects['GT']
        frames=[obs[n].get('best') for n in (a,b)]
        pose={}
        if None not in frames and all(gt['valid'][f-1] for f in frames):
            i,j=[f-1 for f in frames]
            Rp=geo.C[i,:3,:3].T@geo.C[j,:3,:3]
            Rt=gt['c2w'][i,:3,:3].T@gt['c2w'][j,:3,:3]
            tp=geo.C[i,:3,:3].T@(geo.C[j,:3,3]-geo.C[i,:3,3])
            tt=gt['c2w'][i,:3,:3].T@(gt['c2w'][j,:3,3]-gt['c2w'][i,:3,3])
            pose=dict(rotation_deg=float(np.degrees(np.arccos(np.clip((np.trace(Rp.T@Rt)-1)/2,-1,1)))),
                translation_m=float(np.linalg.norm(tp-tt)),same_frame=i==j,frames=frames)
        dep=[objects['deployed'][n].get('best') for n in (a,b)]
        result[r['id']]=dict(depth={n:depth[n] for n in (a,b)},pose=pose,
            deployed_same_frame=None if None in dep else dep[0]==dep[1],deployed_frames=dep)
    return result


def run_capture(c,args,I,D,M,head,phase):
    start=time.monotonic()
    geo,t,own,gt,cache,meta=load_capture(c,args,I,D)
    names=sorted({n for r in c['rows'] for n in r['operands']})
    gm=gt_masks(c,names,gt)
    dm,choices=selected_masks(c,names,geo,cache,gt,head,D)
    masks={'GT':gm,'deployed':dm}
    objects={m:lifted(ms,geo,D) for m,ms in masks.items()}
    per={r['id']:dict(row_id=r['id'],capture=c['canonical'],room=c['room'],dataset=c['canonical'].split('/')[0],
          split=c['k1_split'],label=M.labels[r['id']]['corrected'],cells={}) for r in c['rows']}
    parity=[]
    for m,arm in [('GT','A2_gt_masks'),('deployed','A0_deployed')]:
        for r in c['rows']:
            value=predict(r,geo,objects[m],D)
            per[r['id']]['cells'][cell_name(m,'G3T','G3T','own')]=value
            if c['k1_split']=='train':
                ref=M.refs[(arm,r['id'])]
                equal=value['prediction']==ref['prediction'] and clean(value['printed'])==ref['box']
                parity.append(dict(row_id=r['id'],arm=arm,passed=equal,prediction_equal=value['prediction']==ref['prediction'],
                    got=value['prediction'],expected=ref['prediction'],boxes_equal=clean(value['printed'])==ref['box']))
    if phase=='parity':
        return dict(capture=c['canonical'],phase=phase,rows=list(per.values()),parity=parity,geometry=meta,choices=choices,
                    seconds=time.monotonic()-start,input_sha256=I.hashes)
    assert all(x['passed'] for x in parity),'per-item served parity failed'
    meta['gt_pose_precision']=gt_camera_poses(gt)[1]
    for d,p,s in itertools.product(['G3T','GT'],['G3T','GT'],['own','GT']):
        if (d,p,s)==('G3T','G3T','own'):continue
        g=swapped(geo,t,own,gt,meta,d,p,s,D)
        for m,ms in masks.items():
            obs=lifted(ms,g,D)
            for r in c['rows']:per[r['id']]['cells'][cell_name(m,d,p,s)]=predict(r,g,obs,D)
            if (d,p,s)==('GT','GT','GT'):
                for r in c['rows']:per[r['id']]['cells'][m+'/voted_GT']=predict(r,g,obs,D,M.freeze)
    og=swapped(geo,t,own,gt,meta,'own','G3T','own',D)
    for m,ms in masks.items():
        obs=lifted(ms,og,D)
        for r in c['rows']:per[r['id']]['cells'][m+'/own_depth']=predict(r,og,obs,D)
        for kind in ['oracle_extent','oracle_centre']:
            try:
                obs=extent_objects(c,objects[m],gt,geo,M.boxes,kind)
                for r in c['rows']:per[r['id']]['cells'][m+'/'+kind]=predict(r,geo,obs,D)
            except (KeyError,ValueError) as e:
                for r in c['rows']:per[r['id']]['cells'][m+'/'+kind]=dict(prediction=None,refusal=str(e),printed={})
    tower_info={}
    for label,folder in [('Pi3X','pi3x_native'),('DA3','da3_native')]:
        path=args.towers/folder/(c['canonical'].replace('/','__')+'.npz')
        if path.exists():
            z=I.npz(path);assert np.array_equal(z['anchor_frame_indices'],c['anchor_indices'])
            d=np.asarray(z['depth_grid'],float)
            assert d.shape==own['depth'].shape and np.array_equal(z['grid_uv'],t['grid_uv'])
            # Remove the tower's arbitrary depth scale; own depth supplies the metric scale.
            s=D.median_ratio(d,t['depth_conf_grid'],own['depth'])
            g=D.geometry.from_arrays(K=geo.K,canvas_to_source=geo.A,camera_to_world=geo.C,scale=1.,
                depth_grid=d*s,grid_uv=t['grid_uv'],anchor_frame_indices=c['anchor_indices'])
            tower_info[label]=dict(path=str(path),own_scale=s,status='OK')
            for m,ms in masks.items():
                obs=lifted(ms,g,D)
                for r in c['rows']:per[r['id']]['cells'][m+'/'+label]=predict(r,g,obs,D)
        else:
            tower_info[label]=dict(path=str(path),status='MISSING')
            for r in c['rows']:
                for m in masks:per[r['id']]['cells'][m+'/'+label]=dict(prediction=None,refusal='missing_tower_export',printed={})
    diag=diagnostics(c,gm,geo,og,gt,objects,D)
    for rid,row in per.items():row['diagnostics']=diag[rid]
    return dict(capture=c['canonical'],phase=phase,rows=list(per.values()),parity=parity,geometry=meta,choices=choices,
        towers=tower_info,seconds=time.monotonic()-start,input_sha256=I.hashes)

_BOOT={}
def bootstrap(rows,values):
    """Paired, item-weighted room bootstrap; values may be a matrix of cells."""
    values=np.asarray(values,float)
    if values.ndim==1:values=values[:,None]
    rooms=tuple(sorted({r['room'] for r in rows}))
    if not rooms:return []
    if rooms not in _BOOT:
        rng=np.random.default_rng(SEED)
        ids=rng.integers(len(rooms),size=(DRAWS,len(rooms)))
        weights=np.zeros((DRAWS,len(rooms)),np.int16)
        for i,d in enumerate(ids):weights[i]=np.bincount(d,minlength=len(rooms))
        _BOOT[rooms]=weights
    weights=_BOOT[rooms];index={r:i for i,r in enumerate(rooms)}
    counts=np.zeros(len(rooms));sums=np.zeros((len(rooms),values.shape[1]))
    for r,v in zip(rows,values):
        k=index[r['room']];counts[k]+=1;sums[k]+=v
    draws=(weights@sums)/(weights@counts)[:,None]
    lo,hi=np.percentile(draws,[2.5,97.5],axis=0)
    return [dict(n=len(rows),rooms=len(rooms),mean=float(v),ci95=[float(a),float(b)])
            for v,a,b in zip(values.mean(0),lo,hi)]

BUCKETS={'all':lambda r:True,'arkitscenes':lambda r:r['dataset']=='arkitscenes',
         'scannet_scannetpp':lambda r:r['dataset'] in ('scannet','scannetpp'),
         'scannet':lambda r:r['dataset']=='scannet','scannetpp':lambda r:r['dataset']=='scannetpp'}
CONTRAST_PAIRS={'C1':(DEND,DBASE),'C3_depth':('GT/GT/G3T/own',BASE),
 'C3_pose':('GT/G3T/GT/own',BASE),'C3_joint':('GT/GT/GT/own',BASE),
 'C3_full_gap':(END,BASE),'C3_scale':('GT/G3T/G3T/GT',BASE),
 'C5':('GT/own_depth',BASE),'C5_deployed':('deployed/own_depth',DBASE),
 'C6':('deployed/oracle_extent',DBASE),'centre':('deployed/oracle_centre',DBASE),
 'Pi3X':('GT/Pi3X',BASE),'DA3':('GT/DA3',BASE),
 'Pi3X_deployed':('deployed/Pi3X',DBASE),'DA3_deployed':('deployed/DA3',DBASE),
 'fusion':('GT/voted_GT',END),'fusion_deployed':('deployed/voted_GT',DEND)}


def verdicts(stats):
    def point(k):return stats[k]['mean']
    def lower(k):return stats[k]['ci95'][0]
    out={}
    out['C1']='geometry pays now' if point('C1')>=4 and lower('C1')>0 else ('geometry waits for masks' if point('C1')<2 else 'undecided')
    out['C3_pose']='pose binds; no depth trains' if point('C3_pose')>=10 and point('C3_depth')<=4 else 'pose-only gate fails'
    out['C3_depth']='opens arm B' if point('C3_depth')>=5 and lower('C3_depth')>0 else 'depth-only gate fails'
    interact=point('C3_depth')<=point('C3_full_gap')/3 and point('C3_pose')<=point('C3_full_gap')/3
    out['C3_interaction']='they interact; fusion row decides' if interact else 'interaction criterion fails'
    out['C5']='serve own depth' if point('C5')>=-1 and lower('C5')>=-3 else ('own depth cannot carry distance' if point('C5')<=-5 else 'undecided')
    out['C6']='opens arm C' if point('C6')>=5 and lower('C6')>0 else 'arm C gate fails'
    for k in ['Pi3X','DA3']:out[k]='proposes a new pin' if point(k)>=3 and lower(k)>0 else 'G3T stays'
    conditions=dict(depth_gain=point('C3_depth')>=5,C1=point('C1')>=2,
        no_tower_recovers_half=all(point(k)<.5*point('C3_depth') for k in ['Pi3X','DA3']),
        own_depth_gap=-point('C5')>=3)
    out['arm_B_full_gate']=dict(conditions=conditions,passed=all(conditions.values()),
        verdict='PASS' if all(conditions.values()) else 'FAIL',
        half_recovery_definition='half of GT-depth-alone gain over served G3T at GT masks')
    return out


def parity_summary(rows,checks):
    train=[r for r in rows if r['split']=='train']
    result=[]
    for k,target in [(DBASE,56.77),(BASE,73.97)]:
        value=100*math.fsum(mra(r['cells'][k]['prediction'],r['label']) for r in train)/len(train)
        arm='A0_deployed' if k==DBASE else 'A2_gt_masks'
        c=[x for x in checks if x['arm']==arm]
        result.append(dict(cell=k,n=len(train),target=target,observed=value,delta=value-target,
            tolerance=.2,score_pass=abs(value-target)<=.2,exact_prints=sum(x['passed'] for x in c),
            print_count=len(c),passed=abs(value-target)<=.2 and len(c)==1037 and all(x['passed'] for x in c)))
    return result


def aggregate(args,M,I,records):
    rows=sorted([r for x in records for r in x['rows']],key=lambda r:r['row_id'])
    assert {r['row_id'] for r in rows}==M.sets['train']|M.sets['heldout']
    checks=[x for rec in records for x in rec['parity']]
    parity=parity_summary(rows,checks)
    full=all(set(CELLS+EXTRAS)<=r['cells'].keys() for r in rows)
    result=dict(status='COMPLETE' if full and all(p['passed'] for p in parity) else 'PARITY_STOP',
        parity=parity,rows=rows,parity_checks=checks,geometry={r['capture']:r['geometry'] for r in records},
        choices={r['capture']:r['choices'] for r in records},towers={r['capture']:r.get('towers',{}) for r in records},
        input_sha256=dict(I.hashes),statistics=dict(draws=DRAWS,seed=SEED,unit='physical room',paired=True),
        registered_cells=CELLS,extra_cells=EXTRAS,contract=CONTRACT)
    for rec in records:result['input_sha256'].update(rec['input_sha256'])
    cells=CELLS+EXTRAS if full else [BASE,DBASE]
    tables={};contrasts={};cross={};diags={}
    pairs=CONTRAST_PAIRS if full and all(p['passed'] for p in parity) else {}
    for split,ids in M.sets.items():
        tables[split]={};contrasts[split]={};cross[split]={};diags[split]={}
        for ds,keep in BUCKETS.items():
            rs=[r for r in rows if r['row_id'] in ids and keep(r)]
            score=np.array([[100*mra(r['cells'][k]['prediction'],r['label']) for k in cells] for r in rs])
            stats=bootstrap(rs,score)
            tables[split][ds]={k:dict(s,answered=sum(r['cells'][k]['prediction'] is not None for r in rs)) for k,s in zip(cells,stats)}
            if pairs:
                vals=np.array([[100*(mra(r['cells'][a]['prediction'],r['label'])-mra(r['cells'][b]['prediction'],r['label']))
                    for a,b in pairs.values()] for r in rs])
                contrasts[split][ds]=dict(zip(pairs,bootstrap(rs,vals)))
                vs=verdicts(contrasts[split][ds])
                contrasts[split][ds]['verdicts']=vs
            for served,other in [(BASE,'GD_reviewed'),(END,'GT')]:
                if served not in cells:continue
                paired=[r for r in rs if (other,r['row_id']) in M.gd]
                values=[[100*mra(r['cells'][served]['prediction'],r['label']),
                         100*mra(M.gd[(other,r['row_id'])]['pred'],r['label'])] for r in paired]
                values=np.asarray(values)
                stats=bootstrap(paired,np.column_stack((values,values[:,0]-values[:,1])))
                cross[split].setdefault(ds,{})[served]=dict(zip(['served','GD_program','paired_difference'],stats))
            if full:
                diag={}
                for model in ['G3T','own']:
                    for metric in ['metric','fitted']:
                        pairs2=[]
                        for r in rs:
                            ds2=r['diagnostics']['depth']
                            vals=[v[model] for v in ds2.values() if model in v]
                            if vals:
                                val=sum(v[metric]*v['n'] for v in vals)/sum(v['n'] for v in vals)
                                pairs2.append((r,val))
                        diag[model+'_'+metric]=bootstrap([r for r,v in pairs2],[v for r,v in pairs2])[0] if pairs2 else None
                for metric in ['rotation_deg','translation_m','same_frame']:
                    pairs2=[(r,r['diagnostics']['pose'][metric]) for r in rs if metric in r['diagnostics']['pose']]
                    diag[metric]=bootstrap([r for r,v in pairs2],[v for r,v in pairs2])[0] if pairs2 else None
                pairs2=[(r,r['diagnostics']['deployed_same_frame']) for r in rs if r['diagnostics']['deployed_same_frame'] is not None]
                diag['deployed_same_frame']=bootstrap([r for r,v in pairs2],[v for r,v in pairs2])[0] if pairs2 else None
                diags[split][ds]=diag
    result.update(tables=tables,contrasts=contrasts,cross_program=cross,readouts=diags)
    return result

CONTRACT=dict(program='sb_kbox4 served reader: lift_bestspread, reader guard, box_grid_5cm, run_iso candidates_argmax',
    masks='Selector runs once on served geometry. Each chosen raw mask and frame stays fixed across swaps.',
    scale='s=served own scale or E3 specified oracle SO. q=s/SO. G3T depth and translations multiply s; GT depth and translations multiply q.',
    depth='GT dose_pool optical-axis depth sampled by floor(endpoint_canvas*size/1000) onto the served 51x51 grid; reader bilinear interpolation and 5x5 spread stencil remain unchanged.',
    pose='GT c2w at anchors in GT world coordinates. Rotations failing the sealed 1e-6 orthogonality check are projected to SO(3) only when raw orthogonality and determinant errors are <=1e-5; translations are unchanged and repairs are recorded. No GT gravity is applied to cells with G3T pose.',
    intrinsics='Served K and canvas_to_source retained in every cell; GT intrinsics are not a fifth factor.',
    own='Stored own_170235 depth is already metric; served G3T poses and intrinsics remain fixed.',
    towers='Pi3X/DA3 depth only, scaled by median(own/tower depth) on finite positive points above median G3T confidence. G3T poses/intrinsics retained.',
    oracle_boxes='Corrected full GT annotation extents or centres, registered by anchor 1 into served world. Extents project onto retained served axes; centres preserve served lengths and axes.',
    voted='Ladder frozen vote_10_3_best on GT depth/pose/oracle scale; same spread cut and program.',
    readouts='Depth AbsRel at all GT-mask pixels, per-operand median scale fit, pixel-weighted within each row then item mean. Pose errors use the GT-mask best frames; same-frame share also reported for deployed masks.',
    train='1037 is parity; 1012 is decision cross-check. Deployed-mask train cells are in-sample.',
    cross_program='E3/GD_reviewed GT masks are saved comparisons only; neither endpoint sets a stop for this served program.')


def fmt(x,ci=True):
    if not x:return 'n/a'
    return f"{x['mean']:.2f}"+(f" [{x['ci95'][0]:.2f}, {x['ci95'][1]:.2f}]" if ci else '')


def report(result):
    lines=[f"K1-X served-reader factorial: {result['status']}. Scores are MRA ×100.",
      'Held-out decides (216 rows / 48 rooms); train 1,012 cross-checks; train 1,037 establishes parity. Train deployed-mask scores are in-sample.',
      'Intervals use 10,000 paired physical-room bootstrap draws, seed 20261120. All cell intervals and separate ScanNet/ScanNet++ tables are in K1X.json.','',
      '| Train parity | Target | Replay | Exact per-row predictions and boxes | Gate |','|---|---:|---:|---:|---|']
    for p in result['parity']:lines.append(f"| {p['cell']} | {p['target']:.2f} | {p['observed']:.4f} | {p['exact_prints']}/{p['print_count']} | {'PASS' if p['passed'] else 'FAIL'} |")
    lines+=['','| Cell (masks/depth/pose/scale) | HO all | HO ARKit | HO SN/SN++ | T1012 all | T1012 ARKit | T1012 SN/SN++ | T1037 all |','|---|---:|---:|---:|---:|---:|---:|---:|']
    cells=list(result['tables']['heldout']['all'])
    for k in cells:
        vals=[fmt(result['tables'][s][d][k],False) for s,d in [('heldout','all'),('heldout','arkitscenes'),('heldout','scannet_scannetpp'),('train1012','all'),('train1012','arkitscenes'),('train1012','scannet_scannetpp'),('train','all')]]
        lines.append('| '+k+' | '+' | '.join(vals)+' |')
    if result['status']=='COMPLETE':
        lines+=['','| Contrast | Held-out delta [95% CI] | Train1012 delta | Held-out registered verdict |','|---|---:|---:|---|']
        ho=result['contrasts']['heldout']['all'];tr=result['contrasts']['train1012']['all'];vs=ho['verdicts']
        for k in ['C1','C3_depth','C3_pose','C3_joint','C3_scale','C5','C6','Pi3X','DA3','centre','fusion']:
            lines.append(f"| {k} | {fmt(ho[k])} | {fmt(tr[k],False)} | {vs.get(k,'diagnostic')} |")
        lines+=[f"C3 interaction: {vs['C3_interaction']}. Arm B full gate: {vs['arm_B_full_gate']['verdict']}; {vs['arm_B_full_gate']['conditions']}.",
          'Arm B tests whether either tower recovers half of the GT-depth-alone gain; own-depth gap is G3T minus own depth at GT masks.','',
          '| GT-mask endpoint, held-out | Served program | GD/E3 program | Paired served minus GD/E3 | Published target |','|---|---:|---:|---:|---:|']
        for k,target in [(BASE,75.05),(END,91.99)]:
            r=result['cross_program']['heldout']['all'][k]
            lines.append(f"| {k} | {fmt(r['served'])} | {fmt(r['GD_program'])} | {fmt(r['paired_difference'])} | {target:.2f} |")
        lines+=['','| Readout | HO all / ARKit / SN+SN++ | T1012 all / ARKit / SN+SN++ | T1037 all |','|---|---:|---:|---:|']
        for metric in ['G3T_metric','G3T_fitted','own_metric','own_fitted','rotation_deg','translation_m','same_frame','deployed_same_frame']:
            vals=[' / '.join(fmt(result['readouts'][s][d].get(metric),False) for d in ['all','arkitscenes','scannet_scannetpp']) for s in ['heldout','train1012']]
            vals.append(fmt(result['readouts']['train']['all'].get(metric),False));lines.append('| '+metric+' | '+' | '.join(vals)+' |')
    lines+=['',
      'GT depth uses dose_pool rasters at the anchors, sampled to the served 51×51 endpoint grid. All cells retain served intrinsics, bilinear depth interpolation, the spread cut, and the distance program.',
      'Scale matching: s is own or E3 oracle scale; q=s/SO. G3T depth/translation multiply s; GT depth/translation multiply q. GT pose uses anchor c2w directly.',
      'GT rotation precision: matrices failing the sealed proper-rotation check are projected to SO(3) only within a 1e-5 input-error bound. Translations and the reader guard remain unchanged; per-anchor adjustments are recorded in K1X.json.',
      'The reader reconstructs both refused captures from run_tower_sam_2/{45511ef70c22b11e,9baa923934276385}/tower.npz and own_170235/native/probe/<key>/own.npz; their convert candidates.json files supply masks.',
      'Those captures lack convert geometry and own PHASE_COMPLETE receipts. Every input read is hashed; per-row replay parity checks their reconstruction against the ladder.',
      'Pi3X/DA3 substitute depth shape only, normalized to own depth with the same confidence eligibility. Oracle boxes use corrected GT annotations registered through anchor 1; voted boxes use the ladder frozen vote_10_3_best.',
      'Depth readouts average GT-mask pixels within each row, then rows; scale fits use each operand’s valid pixels. Pose errors use the two GT-mask best frames. Same-frame values are fractions.',
      'Limitations: fixed served intrinsics and 51×51 GT resampling distinguish this ceiling from GD/E3; anchor-1 registration can mix pose error into oracle-centre effects; train selector scores are in-sample.',
      'Coverage, refusal reasons, dataset verdicts, all intervals and exact per-row prints are recorded in K1X.json. No GD/E3 prediction is substituted into a factorial cell.',
      'Run: nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B k1x.py run --heavy-io-approved. Tests: same prefix with k1x.py test.',
      'Borderline no-archaeology sentences retained: none. Files: k1x.py, tests/test_k1x.py, vendor/LADDER_COPIES.json, out/K1X.json, out/REPORT_R2.md, out/SHA256SUMS.']
    assert len(lines)<=100,len(lines)
    return '\n'.join(lines)+'\n'


def checksums(args):
    paths=[ROOT/'k1x.py',ROOT/'tests/test_k1x.py',*sorted((ROOT/'vendor').glob('*.py')),*sorted((ROOT/'vendor').glob('*.json'))]
    paths += [args.out/n for n in ['K1X.json','REPORT_R2.md','TESTS.json','PARITY.json','INVENTORY.json']]
    (args.out/'SHA256SUMS').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT)}\n' for p in paths if p.exists()))


def inventory(args,M,I):
    files=[]
    for c in M.captures:
        k=key(c)
        for p in [Path(c['gt']['path']),args.tower/k/'tower.npz',args.own/k/'own.npz',args.convert/k/'candidates.json']:
            files.append(dict(path=str(p),bytes=p.stat().st_size if p.exists() else None))
    result=dict(captures=len(M.captures),files=files,bytes=sum(r['bytes'] or 0 for r in files),missing=[r['path'] for r in files if r['bytes'] is None])
    write(args.out/'INVENTORY.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='files'}),flush=True)


def prepare(args,M,I):
    """Write an explicit pending report without reading raster arrays."""
    references=[]
    for arm,target in [('A0_deployed',56.77),('A2_gt_masks',73.97)]:
        rs=[r for (a,rid),r in M.refs.items() if a==arm]
        score=100*math.fsum(mra(r['prediction'],M.labels[r['row_id']]['corrected']) for r in rs)/len(rs)
        references.append(dict(arm=arm,n=len(rs),saved_score=score,target=target,replay_status='NOT_RUN'))
    result=dict(status='AWAITING_HEAVY_IO_APPROVAL',contract=CONTRACT,
        saved_ladder_references=references,
        registered_cells=[dict(cell=k,status='NOT_RUN') for k in CELLS],
        extra_cells=[dict(cell=k,status='NOT_RUN') for k in EXTRAS],
        contrasts={k:dict(status='NOT_RUN',verdict='UNAVAILABLE') for k in CONTRAST_PAIRS},
        input_sha256=I.hashes,approval_requirement='Trinity Agents rule: Ask before any heavy IO command; wait for the user answer.')
    write(args.out/'K1X.json',result)
    lines=['K1-X awaits explicit approval for the heavy raster/geometry pass.',
        'The served-reader factorial CLI is implemented but has not been validated on real captures.',
        'Round-1 outputs and code remain in out/round1/.', '',
        '| Train reference, 1,037 rows | Target | Saved ladder score | Fresh replay |',
        '|---|---:|---:|---|']
    for r in references:lines.append(f"| {r['arm']} | {r['target']:.2f} | {r['saved_score']:.4f} | NOT RUN |")
    lines+=['','Saved scores do not establish raw-geometry parity. The full run requires every per-row prediction and printed box to equal the ladder.',
        'Held-out cross-program differences, all 16 factorial cells, 12 extra rows, C1/C3/C5/C6, the arm-B gate, tower verdicts and readouts are NOT RUN.',
        'The inventory found all primary files for 259 captures (3,676,008,943 bytes). No heavy raster pass ran.',
        'Seven synthetic/source tests pass. Two checks await full parity and factorial outputs; out/TESTS.json records the test result.',
        'The two refused-capture fallbacks use run_tower_sam_2/<key>/tower.npz and own_170235/native/probe/<key>/own.npz, exactly as the ladder reconstruction. Their convert candidates.json files exist.',
        'The CLI freezes run_iso masks on served geometry, retains the reader lift and distance program, and matches GT metric inputs by own_scale/oracle_scale.',
        'The oracle-scale function is copied from E3. The GT endpoint retains served intrinsics and samples GT rasters onto the served 51×51 grid.',
        'Pi3X and DA3 depth exports exist for all 300 captures. The voted-box rule is the ladder frozen vote_10_3_best.',
        'Run after approval: nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B k1x.py run --heavy-io-approved.',
        'The run uses one CPU process and one numerical thread, local /scratch inputs, and outputs only under r2.',
        'Deviation: execution remains pending because the Trinity Agents rule requires an answer before heavy I/O; elapsed time does not grant approval.',
        'Borderline no-archaeology sentences retained: round-1 archive location, because the user explicitly requires its preservation.',
        'Files: k1x.py, tests/test_k1x.py, vendor/LADDER_COPIES.json, out/INVENTORY.json, out/K1X.json, out/REPORT_R2.md, out/SHA256SUMS.']
    (args.out/'REPORT_R2.md').write_text('\n'.join(lines)+'\n')
    checksums(args)


_RUN_CONTEXT=None


def execute_capture(job):
    args,D,M,head=_RUN_CONTEXT
    i,c,phase,fingerprint,total=job
    dest=args.out/phase/(c['canonical'].replace('/','__')+'.json')
    if dest.exists():
        rec=json.loads(dest.read_text())
        assert rec['fingerprint']==fingerprint,'completed capture belongs to different code or input metadata'
        return rec
    print(f"START {phase} {i+1}/{total} {c['canonical']}",flush=True)
    local=Inputs();rec=run_capture(c,args,local,D,M,head,phase)
    rec['fingerprint']=fingerprint;write(dest,rec)
    print(f"DONE {phase} {i+1}/{total} {c['canonical']} {rec['seconds']:.1f}s",flush=True)
    return rec


def main():
    global _RUN_CONTEXT
    args=options();assert args.out.resolve().is_relative_to(ROOT)
    args.out.mkdir(exist_ok=True,parents=True)
    if args.command=='test':
        import unittest
        sys.path.insert(0,str(ROOT));sys.modules['k1x']=sys.modules[__name__]
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        write(args.out/'TESTS.json',dict(tests=result.testsRun,passed=result.wasSuccessful(),failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped)))
        checksums(args);return 0 if result.wasSuccessful() else 1
    I=Inputs();M=metadata(args,I)
    if args.command=='inventory':inventory(args,M,I);return 0
    if args.command=='prepare':prepare(args,M,I);return 0
    captures=M.captures
    if args.capture:captures=[c for c in captures if c['canonical'] in args.capture]
    if args.command=='run':
        if not args.heavy_io_approved:raise PermissionError('Explicit user approval required before heavy raster I/O; use inventory or test while waiting.')
        D=dependencies(args)
        for ext in ['json','safetensors']:I.read(args.selector/f'selector_head.{ext}')
        head,_=D.load_head(args.selector)
        code=[ROOT/'k1x.py',*sorted((ROOT/'vendor').glob('*.py'))]
        for module in list(sys.modules.values()):
            path=getattr(module,'__file__',None)
            if path and path.endswith('.py') and any(Path(path).is_relative_to(p) for p in [args.tree,args.ladder,args.selector.parents[1]]):
                code.append(Path(path))
        for path in sorted(set(code)):I.read(path)
        fingerprint=hashlib.sha256(json.dumps(dict(inputs=I.hashes,contract=CONTRACT,
            paths={k:str(v) for k,v in vars(args).items() if isinstance(v,Path)}),sort_keys=True).encode()).hexdigest()
        _RUN_CONTEXT=(args,D,M,head)
        phases=['parity','factorial'] if args.phase=='all' else [args.phase]
        for phase in phases:
            if phase=='factorial' and not args.capture:
                p=json.loads((args.out/'PARITY.json').read_text())
                assert p['passed'],'full factorial requires complete exact train parity'
                assert p['fingerprint']==fingerprint,'parity belongs to different code or input metadata'
            records=[]
            cs=[c for c in captures if phase!='parity' or c['k1_split']=='train']
            jobs=[(i,c,phase,fingerprint,len(cs)) for i,c in enumerate(cs)]
            if args.workers==1:
                records=list(map(execute_capture,jobs))
            else:
                from concurrent.futures import ProcessPoolExecutor
                import multiprocessing
                with ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('fork')) as pool:
                    records=list(pool.map(execute_capture,jobs))
            if phase=='parity' and not args.capture:
                rows=[r for x in records for r in x['rows']];checks=[p for x in records for p in x['parity']]
                summary=parity_summary(rows,checks)
                p=dict(passed=all(v['passed'] for v in summary),parity=summary,checks=checks,fingerprint=fingerprint)
                write(args.out/'PARITY.json',p);print(json.dumps(p['parity']),flush=True)
                if not p['passed']:return 2
        if args.capture or args.phase=='parity':checksums(args);return 0
    records=[json.loads((args.out/'factorial'/(c['canonical'].replace('/','__')+'.json')).read_text()) for c in M.captures]
    result=aggregate(args,M,I,records)
    write(args.out/'K1X.json',result);(args.out/'REPORT_R2.md').write_text(report(result));checksums(args)
    print(json.dumps(dict(status=result['status'],parity=result['parity'])),flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
