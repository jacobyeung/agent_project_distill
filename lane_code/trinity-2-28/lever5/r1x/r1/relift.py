"""CPU relift of authenticated T1 masks through the deployed geometry and gap code.

Lane copy (lever5) under the gate amendment of ORCH RULING 2026-11-21T18:48Z, made before any cell was read:
the gate is (i) every depth-free gap check matches; (ii) cell (a) is relifted from the same dump and the same
code path as cells b-g, so every comparison is paired inside one dump; (iii) camera/scale parity and the printed-gap
parity of a(dump) against T1 are reported per dataset and do not gate.

Rank 5 extension (lever5, ORCH ANSWER 2026-11-21T19:02Z): the cell population adds the 21 NOGT captures that pass rank 5's
checks (GT NPZs built from raw scans; 41254810 excluded, it fails binding). For those captures FUNNEL_T1 holds no binding
(binding null, gt_available false), so the operand binding comes from the NPZ alone; every other check is unchanged."""
import os
for _k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[_k]='1'
os.environ['CUDA_VISIBLE_DEVICES']=''
import argparse
from collections import Counter,defaultdict
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'runtime'))
import j as wire_json
wire_json.install()
import numpy as np
HERE=Path(__file__).resolve().parent
BASE=Path('/scratch/jjyeung/orch_n30/cont_ops24_c')
GB=BASE/'gbuild'
KIT=Path('/scratch/jjyeung/orch_n30/grd_funnel1/kit/rerun2')
T1_SHA='fe9f10b875283b02e3c376b69c3601a4086312ac56ba77fbebedce4eb21e51b7'
NOGT_DIRS=[Path('/scratch/jjyeung/orch_n30/lever5/r1x/gt21/t1'),Path('/scratch/jjyeung/orch_n30/lever5/r1x/gt21/ark')]
NOGT_CAPTURES={(p.stem.replace('__','/') if '__' in p.stem else 'arkitscenes/'+p.stem) for d in NOGT_DIRS for p in d.glob('*.npz')}
EXPECTED_GT=38+21
assert len(NOGT_CAPTURES)==21 and 'arkitscenes/41254810' not in NOGT_CAPTURES


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def dependencies():
    sys.path[:0]=[str(HERE),str(GB),str(GB/'work/payload/b'),str(GB/'work/payload/tree'),str(HERE.parent/'r3')]
    global grounding,geometry,boxes,Records,unrle,resize,bind,full_box,names,official_mra,unit_factor,Bootstrap,pose,fmt
    from e2e_reader import grounding,geometry
    from trace_format import box_v313 as boxes
    from gpkg.capture_io import Records
    from gpkg.runtime.c import unrle
    from gpkg.grid import resize
    from gt.v2 import bind,full_box
    from gt.adapter import names
    from gpkg.score_ceiling import official_mra,unit_factor
    from round7_common import Bootstrap
    import devpose as pose
    pose.dependencies(GB)
    import depth_format as fmt
    # Grounding fixtures are the source authority supplied for this build.
    pins=json.loads((KIT/'SOURCE_PINS.json').read_text())
    assert sha(Path(grounding.__file__))==pins['fixtures/grounding.py.txt']


def masks_array(masks):
    out=np.zeros((32,240,320),bool)
    for f,m in masks.items():
        a=unrle(m) if isinstance(m,dict) else np.asarray(m,bool)
        if a.shape!=(240,320):raise ValueError('selected mask grid differs')
        out[int(f)-1]=a
    return out


def restore(row,half_only=False):
    d,uv=fmt.decode(row,half_only=half_only);m=row['metadata']['geometry']
    # Construct with scale one because both saved depth and saved cameras are
    # already metric. Retain the real applied scale separately in metadata.
    g=geometry.from_arrays(K=m['K'],canvas_to_source=m['canvas_to_source'],
        camera_to_world=m['camera_to_world_metric'],scale=1.,depth_grid=d,grid_uv=uv,
        anchor_frame_indices=m['source_indices'])
    assert np.array_equal(g.depth_grid,d) and np.array_equal(g.C,np.asarray(m['camera_to_world_metric']))
    return g


def fit_lift(name,masks,g,*,gt_cameras=None):
    obj=grounding.lift_bestspread(name,masks,g)
    if not obj['seen']:return None,obj
    if gt_cameras is not None:
        # Change relative pose only. Recover each operand's camera-local points,
        # use its own GT anchor, then one common first-anchor world transform.
        b=obj['best']-1;S=g.C[b];G=np.asarray(gt_cameras)[b]
        pts=np.asarray(obj['points'][str(b+1)],float)
        camera=(pts-S[:3,3])@S[:3,:3]
        gt_world=camera@G[:3,:3].T+G[:3,3]
        transported=pose.transport(gt_world,np.asarray(gt_cameras)[0],g.C[0])
        obj=dict(obj,points={str(b+1):transported.tolist()})
    try:return grounding.MinAreaBoxProvider()(name,obj,g,obj['best']),obj
    except ValueError as e:
        if str(e) not in ('box_needs_four_points','degenerate_floor_footprint','degenerate_box'):raise
        return None,dict(obj,box_failure=str(e))


def voted_box(name,masks,g):
    """Reader 5 cm / two-frame vote plus best view, with deployed lift and fit.

    Each view receives its own deployed median-spread filter. The imported
    voting primitive changes point support only; no legacy erosion/depth-cut,
    random point cap, fitted-quantile box or best-view gap override is added.
    """
    base=grounding.lift_bestspread(name,masks,g)
    if not base['seen']:return None
    parts=[]
    for frame in base['frames']:
        single=np.zeros_like(masks);single[frame-1]=masks[frame-1]
        lifted=grounding.lift_bestspread(name,single,g)
        parts.append(np.asarray(lifted['points'][str(frame)],float).reshape(-1,3))
    voted=boxes.vote_points(parts,vox=.05,min_frames=2)
    best=base['best'];points=np.concatenate([voted,np.asarray(base['points'][str(best)],float)])
    obj=dict(base,frames=[best],points={str(best):points.tolist()})
    try:return grounding.MinAreaBoxProvider()(name,obj,g,best)
    except ValueError as e:
        if str(e) not in ('box_needs_four_points','degenerate_floor_footprint','degenerate_box'):raise
        return None


def gap_value(values):
    if not all(x is not None for x in values):return None
    return pose.gap(*values)


def printed_gap(row):
    vv=[]
    for c in row['calls']:
        if c.get('served') and c['call'].startswith('<gap '):
            m=re.fullmatch(r'distance ([\d.]+) m',c.get('response') or '')
            if m:vv.append(float(m[1]))
    return vv[-1] if vv else None


def round_gap(value):return float(boxes.number(value,2)) if value is not None else None


def depth_free_parity(rows,refs,limit=None):
    checks=[]
    for row in rows.values():
        nn=names(refs[row['item_id']])[0];oo={o['name'].strip().lower():o for o in row['objects']}
        fitted=[oo.get(n.strip().lower(),{}).get('fitted_box') for n in nn]
        target=printed_gap(row)
        if target is None or not all(fitted):continue
        value=gap_value([f['f1'] for f in fitted])
        checks.append(dict(item_id=row['item_id'],printed_m=target,recomputed_m=value,match=round_gap(value)==target))
        if limit and len(checks)>=limit:break
    return checks


def read_records(path,refs):
    rr=Records(path,{'sha256':T1_SHA});rows={}
    for row in rr:
        if row['pass_index']!=0:continue
        iid=row['item_id'];ref=refs[iid]
        if iid in rows or row['capture']!=ref['capture'] or row['source_indices']!=ref['source_indices']:raise ValueError('T1 binding')
        rows[iid]=row
    if rr.report['salvaged'] or set(rows)!=set(refs):raise ValueError('incomplete T1 capture')
    return rows


def identity(masks,truth):
    inter=np.count_nonzero(masks&truth);union=np.count_nonzero(masks|truth)
    return inter/union if union else 0.


def oracle(pool,truth):
    if not pool:return np.zeros_like(truth),None
    ranked=[(identity(m,truth),i,m,-j) for j,(i,m) in enumerate(pool)]
    best=max(ranked,key=lambda x:(x[0],x[3]))
    return (best[2],dict(id=best[1],volume_iou=best[0])) if best[0]>0 else (np.zeros_like(truth),None)


def relaxed_pool(obj,g,grids):
    # The score gate tests score, not score*presence. Reuse every downstream
    # deployed producer, including early lift filters and candidate acceptance.
    from student_pilot import routed_features as F
    raw=[[] for _ in range(32)]
    for p in obj['proposals']:
        raw[p['frame']-1].append(dict(mask=unrle(p['mask']),score=p['score'],presence=p['presence']))
    proposals,rejected=F.candidates.lift(F.cache_for(obj['name'],raw),obj['name'],g,floor=0.,grids=grids,phrase=obj['name'])
    pools={obj['name']:F.candidates.link(proposals,obj['name'])}
    F.candidates.scene_candidates(pools,g)
    accepted=F.accept_features(pools[obj['name']],raw,F.Geometry(g))
    return [('relaxed:'+c['candidate_id'],masks_array(c['masks'])) for c in accepted],dict(raw_below_score_gate=sum(p['score']<.3 for p in obj['proposals']),accepted=len(accepted),rejected=len(rejected))


def merged_identity(pool,truth,fallback):
    selected=[]
    for name,m in pool:
        active=m.reshape(32,-1).any(1)
        inter=(m&truth).reshape(32,-1).sum(1);union=(m|truth).reshape(32,-1).sum(1)
        iou=np.divide(inter,union,out=np.zeros(32),where=union>0)
        if active.any() and 2*np.count_nonzero((iou>.25)&active)>=np.count_nonzero(active):selected.append((name,m))
    out=fallback.copy()
    for _,m in selected:out|=m
    return out,[i for i,_ in selected]


def registered(gain,candidate):
    if gain['mean'] is None:return 'undecided until rank 5'
    lo,hi=gain['ci95'];g=gain['mean']
    if g>=8 and lo>0:
        return 'grounding binds; arm A opens' if candidate['mean']>=6 and candidate['ci95'][0]>0 else 'grounding binds; completeness binds'
    if g<=4 and hi<8:return 'grounding does not limit this half'
    return 'undecided until rank 5'


def stats(rows,refs):
    boot=Bootstrap(refs);out=[]
    for dataset in ('all','ARKit','ScanNet/ScanNet++'):
        rr=[r for r in rows if dataset=='all' or r['dataset']==dataset]
        cells={k:boot.metric(rr,k) for k in 'abcdefg'}
        diffs={k:boot.metric([dict(r,delta=r[k]-r['a']) for r in rr],'delta') for k in cells if k!='a'}
        out.append(dict(dataset=dataset,n=len(rr),rooms=len({r['room'] for r in rr}),cells=cells,versus_a=diffs,
                        reading=registered(diffs['e'],diffs['b'])))
    return out


def _ds(cap):
    return {'arkitscenes':'ARKit','scannet':'ScanNet','scannetpp':'ScanNet++','scannetppv2':'ScanNet++'}[cap.split('/')[0]]


def camera_report(depths):
    """Non-gating: per dataset, captures/items within T1's bound and max deviation per field (from each row's parity)."""
    out={}
    for cap,row in depths.items():
        d=out.setdefault(_ds(cap),dict(captures=0,captures_trusted=0,items=0,items_trusted=0,max_deviations={}))
        d['captures']+=1;d['captures_trusted']+=bool(row['parity']['trusted'])
        for it in row['parity']['items']:
            d['items']+=1;d['items_trusted']+=bool(it['trusted'])
            for k,v in it['max_deviations'].items():d['max_deviations'][k]=max(d['max_deviations'].get(k,0.0),float(v))
    return out


def gap_report(checks,refs):
    """Non-gating: per dataset, items whose a(dump) gap equals the printed T1 gap, differs by 0.01 m, or more."""
    out={}
    for c in checks:
        d=out.setdefault(_ds(refs[c['item_id']]['capture']),{'0.00':0,'0.01':0,'beyond':0,'missing':0})
        a,t=c['relift_m'],c['printed_m']
        if a is None or t is None:d['0.00' if a is None and t is None else 'missing']+=1
        else:
            e=round(abs(a-t),2);d['0.00' if e==0 else '0.01' if e<=0.01 else 'beyond']+=1
    return out


def dump(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(wire_json.wire_dumps(value,indent=2,allow_nan=False,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item())+'\n')


def run(args):
    dependencies()
    refs={r['item_id']:r for r in json.loads((KIT/'items544.json').read_text())['items']}
    parity=json.loads((BASE/'cap/t1ret/PARITY.json').read_text())
    if not parity['trusted'] or parity['gap_atol_m']!=0:raise ValueError('registered T1 parity changed')
    result=dict(status='depth return missing',gap_atol_m=parity['gap_atol_m'],required_object_fraction=.95,
                manifest_items=len(refs),bootstrap=dict(draws=10000,seed=20261120,unit='physical room',weighting='item'),
                input_sha256={str(KIT/'items544.json'):sha(KIT/'items544.json')})
    if not args.depth.is_file():dump(args.out,result);print('depth return missing');return 0
    if not args.receipt or not args.receipt.is_file():raise ValueError('authenticated depth receipt required')
    receipt=json.loads(args.receipt.read_text())
    if not receipt.get('verified',False):raise ValueError('depth upload not verified')
    depth_reader=Records(args.depth,receipt);depths={}
    for row in depth_reader:
        cap=row['metadata']['capture']
        if cap in depths:raise ValueError('duplicate depth capture')
        depths[cap]=row
    expected={r['capture'] for r in refs.values()}
    if depth_reader.report['salvaged'] or set(depths)!=expected:raise ValueError('incomplete depth return')
    result['gate']='amended 2026-11-21T18:48Z: paired in-dump reading; T1 parity reported, not gating'
    result['camera_parity_vs_t1']=camera_report(depths)
    rows=read_records(args.capture,refs)
    result['depth_free_gap_checks']=depth_free_parity(rows,refs)
    if not all(x['match'] for x in result['depth_free_gap_checks']):raise ValueError('depth-free gap reproduction failed')
    computed={};checks=[];object_checks=[]
    for iid,ref in refs.items():
        row=rows[iid];depth=depths[ref['capture']]
        if depth['metadata']['frame_binding_sha256']!=ref['mapping']['frame_binding_sha256']:raise ValueError('RGB binding differs')
        g=restore(depth,half_only=args.half_only);nn=names(ref)[0]
        objects={o['name'].strip().lower():o for o in row['objects']};values=[];obj_result={}
        for name in nn:
            obj=objects.get(name.strip().lower());value,lift=fit_lift(name,masks_array(obj['selected_masks']) if obj else np.zeros((32,240,320),bool),g)
            values.append(value);obj_result[name]=(value,lift)
        actual=round_gap(gap_value(values));target=printed_gap(row)
        match=(actual is None and target is None) or (actual is not None and target is not None and abs(actual-target)<=parity['gap_atol_m'])
        check=dict(item_id=iid,printed_m=target,relift_m=actual,match=match)
        checks.append(check)
        for name in nn:object_checks.append(dict(key=iid+':'+name,match=match,rule='operand inherits its item printed-gap match'))
        computed[iid]=dict(gap=actual,objects=obj_result)
    fraction=sum(x['match'] for x in object_checks)/len(object_checks)
    result['parity']=dict(items=checks,objects=object_checks,object_fraction=fraction,passed=fraction>=.95,
                          gating=False,by_dataset=gap_report(checks,refs))
    # No intervention is evaluated before the all-150 parity gate above.
    funnel=json.loads(args.funnel.read_text());fobjects={o['key']:o for o in funnel['objects']['t1']}
    joins=[json.loads(x) for x in args.join.read_text().splitlines()]
    jk={r['key'] for r in joins};fk={o['key'] for o in fobjects.values()};item_level={k for k in jk if ':' not in k}
    # An item with no recorded object call joins at item level (vsi590k_045785); its funnel objects are exactly the remainder.
    if not (jk-item_level)<=fk or fk-jk!={k for k in fk if k.split(':')[0] in item_level} or any(r['key'] in item_level and r.get('stage')!='U' for r in joins):
        raise ValueError('join/funnel population mismatch')
    gt_paths={}
    for folder in args.gt_dirs:
        for path in folder.glob('*.npz'):
            cap=path.stem.replace('__','/') if '__' in path.stem else 'arkitscenes/'+path.stem
            if cap in expected:gt_paths[cap]=path
    if len(gt_paths)!=EXPECTED_GT:raise ValueError('expected %d GT captures'%EXPECTED_GT)
    output=[];exclusions=[dict(item_id=iid,reason='GT capture missing') for iid,r in refs.items() if r['capture'] not in gt_paths];details=[]
    portrait_keys={key for key,o in fobjects.items() if o.get('orientation') and o['orientation']['status']=='U'}
    if len(portrait_keys)!=20:raise ValueError('portrait census changed')
    from student_pilot import routed_features as F
    for cap,path in sorted(gt_paths.items()):
        result['input_sha256'][str(path)]=sha(path)
        with np.load(path,allow_pickle=False) as z:gt={k:z[k] for k in ('inst','ids','labels','frame_indices','valid','c2w')}
        g=restore(depths[cap],half_only=args.half_only);grids=None
        for iid,ref in refs.items():
            if ref['capture']!=cap:continue
            nn=names(ref)[0]
            bindings=[bind(n,gt['ids'],gt['labels']) for n in nn]
            if any(b['instance_id'] is None for b in bindings):exclusions.append(dict(item_id=iid,reason='unbound operand'));continue
            if gt['inst'].shape[1:]!=(240,320):
                exclusions.append(dict(item_id=iid,reason='portrait GT orientation censored'));continue
            if gt['frame_indices'].tolist()!=ref['source_indices'] or not gt['valid'].all():raise ValueError('GT anchor binding')
            row=rows[iid];objects={o['name'].strip().lower():o for o in row['objects']}
            pair={k:[] for k in 'abcdefg'}
            for name,binding in zip(nn,bindings):
                key=iid+':'+name;stage=fobjects[key]
                if cap in NOGT_CAPTURES:
                    if stage.get('binding') is not None or stage.get('gt_available'):raise ValueError('NOGT capture has a funnel binding: '+key)
                elif (stage.get('binding') or {}).get('instance_id')!=binding['instance_id']:raise ValueError('funnel binding differs')
                target=gt['inst']==binding['instance_id'];obj=objects.get(name.strip().lower())
                a=computed[iid]['objects'][name][0];pair['a'].append(a)
                pool=[(c['id'],masks_array(c['masks'])) for c in obj['candidates']] if obj else []
                bm,bi=oracle(pool,target)
                if obj:
                    if grids is None:grids=F.candidates.lift_grid(g)
                    extra,diag=relaxed_pool(obj,g,grids)
                else:extra,diag=[],{}
                cm,ci=oracle(pool+extra,target)
                dm,merged=merged_identity(pool+extra,target,cm)
                object_detail=dict(key=key,b=bi,c=ci,merged_ids=merged,proposal_gate=diag)
                for cell,mask in [('b',bm),('c',cm),('d',dm),('e',target),('g',target)]:
                    box,lift=fit_lift(name,mask,g,gt_cameras=gt['c2w'] if cell=='g' else None)
                    pair[cell].append(box)
                    object_detail[cell+'_best']=lift.get('best');object_detail[cell+'_frames']=lift['frames']
                pair['f'].append(voted_box(name,target,g))
                details.append(object_detail)
            truth=float(ref['task']['ground_truth']);factor=unit_factor(ref['task']['question'])
            entry=dict(item_id=iid,capture=cap,room=ref['task']['room'],dataset='ARKit' if cap.startswith('arkitscenes/') else 'ScanNet/ScanNet++',gaps={})
            for cell,values in pair.items():
                gap=round_gap(gap_value(values));entry['gaps'][cell]=gap
                entry[cell]=100*official_mra(None if gap is None else gap*factor,truth)
            output.append(entry)
    result.update(status='complete',rows=output,objects=details,
        exclusions=exclusions,counts=dict(eligible_items=len(output),eligible_captures=len({r['capture'] for r in output}),portrait_bound_objects=len(portrait_keys)),
        statistics=stats(output,refs),depth_precision='float16 plus exact residual' if not args.half_only else 'float16 only',
        definitions=dict(b='Best accepted linked candidate by global mask IoU with bound GT identity; stable input-order tie; zero overlap means null.',
          c='Union of existing candidates and the deployed lift/link/accept pipeline with score floor 0 instead of .3; detector retention stays unchanged.',
          d='Per-frame mask union of c and tracks with IoU >.25 in at least half of nonempty frames against the same bound identity.',
          e='Unresized landscape GT instance raster through deployed bestspread lift and min-area fit.',
          f='Imported 5 cm two-frame vote plus largest view, using per-view deployed bestspread and deployed min-area fit; no legacy depth-cut or random point cap.',
          g='Served camera-local points through own GT anchor, then rank-3 transport at anchor 1 into common served world. Depth unchanged.'))
    for p in (args.capture,args.depth,args.receipt,args.join,args.funnel,Path(grounding.__file__),Path(geometry.__file__),Path(boxes.__file__),Path(pose.__file__)):
        result['input_sha256'][str(p)]=sha(p)
    dump(args.out,result);print(result['status']);return 0


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture',type=Path,default=BASE/'cap/t1.gz')
    p.add_argument('--depth',type=Path,default=HERE/'returned/0.gz')
    p.add_argument('--receipt',type=Path)
    p.add_argument('--join',type=Path,default=BASE/'cap/score_t1/JOIN_T1.jsonl')
    p.add_argument('--funnel',type=Path,default=BASE/'cap/score_t1/FUNNEL_T1.json')
    p.add_argument('--gt-dirs',type=Path,nargs='+',default=[BASE/'gt/t1_gt/gt',BASE/'gt/arkit_gt/gt']+NOGT_DIRS)
    p.add_argument('--out',type=Path,default=HERE/'out/RELIFT.json')
    p.add_argument('--half-only',action='store_true')
    args=p.parse_args(argv);return run(args)


if __name__=='__main__':raise SystemExit(main())
