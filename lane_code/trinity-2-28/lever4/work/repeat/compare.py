"""Compare two served-depth dumps (run 1, run 2) with each other and with T1.

Camera/scale deviations use the capture worker's definition (runtime/w.py
`compare`: max |actual-expected| per field over all anchors, against the T1
pass-0 geometry of every item of the capture; bounds are twice the maximum
T1 repeat deviation, as build_depth.reference derives them). Printed gaps are
recomputed with relift.py's own restore/fit_lift/gap_value/round_gap/printed_gap.
"""
import os
for _k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[_k]='1'
os.environ['CUDA_VISIBLE_DEVICES']=''
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import time
import numpy as np

HERE=Path(__file__).resolve().parent
FIELDS=('K','camera_to_world_metric','camera_to_world_unscaled','canvas_to_source','scale')
DATASETS=('scannet','scannetppv2','arkitscenes')


def load_relift(path):
    spec=importlib.util.spec_from_file_location('relift',str(path))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.dependencies()
    return mod


def w_compare(actual,expected):
    """runtime/w.py compare(), deviations only (bounds applied separately)."""
    return {k:float(np.max(np.abs(np.asarray(actual[k])-np.asarray(expected[k])))) for k in FIELDS}


def rotation_deg(Ra,Rb):
    # Geodesic angle, stable for small angles: |Ra-Rb|_F = 2*sqrt(2)*sin(theta/2).
    f=np.linalg.norm(Ra-Rb,axis=(-2,-1))
    return np.degrees(2*np.arcsin(np.clip(f/(2*np.sqrt(2)),0,1)))


def pose_terms(a,b):
    """Per-anchor camera translation (m, metric) and rotation (deg)."""
    A=np.asarray(a['camera_to_world_metric'],float);B=np.asarray(b['camera_to_world_metric'],float)
    t=np.linalg.norm(A[:,:3,3]-B[:,:3,3],axis=1);r=rotation_deg(A[:,:3,:3],B[:,:3,:3])
    Ka=np.asarray(a['K'],float);Kb=np.asarray(b['K'],float)
    return dict(translation_m_max=float(t.max()),translation_m_median=float(np.median(t)),
                rotation_deg_max=float(r.max()),rotation_deg_median=float(np.median(r)),
                K_abs_max=float(np.max(np.abs(Ka-Kb))),
                K_rel_max=float(np.max(np.abs(Ka-Kb)/np.maximum(np.abs(Kb),1e-12)*(np.abs(Kb)>1e-9))),
                scale_abs=float(abs(float(a['scale'])-float(b['scale']))),
                scale_rel=float(abs(float(a['scale'])-float(b['scale']))/abs(float(b['scale']))))


def read_run(R,depth,receipt_path,expected):
    receipt=json.loads(Path(receipt_path).read_text())
    if not receipt.get('verified',False):raise ValueError(f'{receipt_path}: depth upload not verified')
    reader=R.Records(depth,receipt);rows={}
    for row in reader:
        cap=row['metadata']['capture']
        if cap in rows:raise ValueError(f'{depth}: duplicate depth capture {cap}')
        rows[cap]=row
    if reader.report['salvaged'] or set(rows)!=expected:
        raise ValueError(f'{depth}: incomplete depth return (salvaged={reader.report["salvaged"]}, '
                         f'missing={sorted(expected-set(rows))[:5]}, extra={sorted(set(rows)-expected)[:5]})')
    return rows,receipt,reader.report


def t1_reference(R,t1,refs):
    """T1 pass-0 rows via relift.read_records, plus T1 repeats via the same Records reader."""
    rows=R.read_records(t1,refs);rep=[]
    for r in R.Records(t1,{'sha256':R.T1_SHA}):
        if r['pass_index']!=0:rep.append(r)
    repeat=[dict(item_id=r['item_id'],**w_compare(r['geometry'],rows[r['item_id']]['geometry'])) for r in rep]
    bounds={k:2*max(x[k] for x in repeat) for k in FIELDS}
    return rows,repeat,bounds


def gap_class(a,b):
    if a is None and b is None:return 'equal'
    if a is None or b is None:return 'missing'
    d=round(abs(a-b),2)
    return 'equal' if d==0 else '0.01' if d==0.01 else 'beyond'


def recompute_gaps(R,depths,t1rows,refs,half_only):
    out={}
    for iid,ref in refs.items():
        row=t1rows[iid];depth=depths[ref['capture']]
        if depth['metadata']['frame_binding_sha256']!=ref['mapping']['frame_binding_sha256']:raise ValueError('RGB binding differs')
        g=R.restore(depth,half_only=half_only);nn=R.names(ref)[0]
        objects={o['name'].strip().lower():o for o in row['objects']};values=[]
        for name in nn:
            obj=objects.get(name.strip().lower())
            value,_=R.fit_lift(name,R.masks_array(obj['selected_masks']) if obj else np.zeros((32,240,320),bool),g)
            values.append(value)
        out[iid]=dict(gap=R.round_gap(R.gap_value(values)),raw=R.gap_value(values),printed=R.printed_gap(row),names=list(nn),boxes=values)
    return out


def leaves(x):
    if isinstance(x,dict):
        for k in sorted(x):yield from leaves(x[k])
    elif isinstance(x,(list,tuple,np.ndarray)):
        for v in (x.tolist() if isinstance(x,np.ndarray) else x):yield from leaves(v)
    elif isinstance(x,(int,float,np.floating,np.integer)) and not isinstance(x,bool):yield float(x)


def box_diff(a,b):
    if a is None or b is None:return None if a is None and b is None else float('inf')
    la,lb=list(leaves(a)),list(leaves(b))
    if len(la)!=len(lb):return float('inf')
    return float(np.max(np.abs(np.subtract(la,lb)))) if la else 0.


def tally(pairs,refs,names):
    """Item and object counts by class; objects inherit their item's class (relift rule)."""
    items={k:0 for k in ('equal','0.01','beyond','missing')};objects=dict(items)
    for iid,c in pairs.items():
        items[c]+=1;objects[c]+=len(names[iid])
    off=sorted(iid for iid,c in pairs.items() if c!='equal')
    return dict(items=items,objects=objects,n_items=len(pairs),n_objects=sum(len(names[i]) for i in pairs),not_equal=off)


def summarize(per_capture,keys,worst=3):
    out={}
    for ds in DATASETS+('all',):
        caps=[c for c in per_capture if ds=='all' or c.split('/')[0]==ds]
        if not caps:continue
        d=dict(captures=len(caps))
        for k in keys:
            v=np.array([per_capture[c][k] for c in caps],float)
            order=sorted(caps,key=lambda c:-per_capture[c][k])[:worst]
            d[k]=dict(max=float(v.max()),median=float(np.median(v)),worst=[[c,per_capture[c][k]] for c in order])
        out[ds]=d
    return out


def fmt(x):
    if x is None:return '-'
    if x==0:return '0'
    return f'{x:.3g}' if abs(x)>=1e-3 else f'{x:.2e}'


def write_md(path,res):
    L=[f"# Repeat comparison\n",f"run1 `{res['inputs']['run1']}`  \nrun2 `{res['inputs']['run2']}`  \nT1 `{res['inputs']['t1']}`\n"]
    keys=('translation_m_max','rotation_deg_max','K_abs_max','scale_abs','depth_abs_max')
    head='| dataset | n | translation m | rotation deg | K abs | scale abs | depth m |\n|---|---|---|---|---|---|---|'
    for title,block,kk in (('run2 vs run1 (max / median over captures)',res['camera']['run2_vs_run1']['summary'],keys),
                           ('run1 vs T1',res['camera']['run1_vs_t1']['summary'],keys[:4]),
                           ('run2 vs T1',res['camera']['run2_vs_t1']['summary'],keys[:4])):
        L.append(f'\n## {title}\n');L.append(head if len(kk)==5 else head.replace(' depth m |','').replace('|---|---|---|---|---|---|---|','|---|---|---|---|---|---|'))
        for ds,d in block.items():
            L.append(f"| {ds} | {d['captures']} | "+' | '.join(f"{fmt(d[k]['max'])} / {fmt(d[k]['median'])}" for k in kk)+' |')
        worst='; '.join(f"{ds} {k.split('_')[0]}: "+', '.join(f"{c} ({fmt(v)})" for c,v in d[k]['worst'][:2] if v>0)
                        for ds,d in block.items() if ds!='all' for k in kk if d[k]['max']>0 and k!='K_abs_max')
        L.append('\nWorst captures: '+(worst or 'none (all zero)'))
        a=block['all']
        L.append('\nw.py fields, max over all captures: '+', '.join(f"{k} {fmt(a[k]['max'])}" for k in FIELDS))
    ag=res['agreement_within_t1_bounds']
    L.append(f"\n## run2 vs run1 within T1 bounds (twice max T1 repeat deviation): **{ag['all_within']}**\n")
    L.append('| field | bound | run2-run1 max | worst capture | captures over bound |\n|---|---|---|---|---|')
    for k,v in ag['fields'].items():L.append(f"| {k} | {fmt(v['bound'])} | {fmt(v['max'])} | {v['worst'] if v['max']>0 else '-'} | {v['over_bound']} |")
    if 'gaps' in res:
        L.append('\n## Printed gaps (items / objects; objects inherit item class)\n')
        L.append('| comparison | dataset | equal 0.00 | 0.01 | beyond | missing |\n|---|---|---|---|---|---|')
        for name,t in res['gaps']['tables'].items():
            for ds,x in t.items():
                L.append(f"| {name} | {ds} | "+' | '.join(f"{x['items'][c]} / {x['objects'][c]}" for c in ('equal','0.01','beyond','missing'))+' |')
        L.append(f"\nObject boxes run2 vs run1: {res['gaps']['object_boxes_run2_vs_run1']['identical']} identical of {res['gaps']['object_boxes_run2_vs_run1']['n']}, max leaf diff {fmt(res['gaps']['object_boxes_run2_vs_run1']['max_abs'])}.")
    L.append('\nChecks: '+', '.join(f'{k}={v}' for k,v in res['checks'].items()))
    Path(path).write_text('\n'.join(L)+'\n')


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run1',type=Path,required=True);p.add_argument('--receipt1',type=Path,required=True)
    p.add_argument('--run2',type=Path,required=True);p.add_argument('--receipt2',type=Path,required=True)
    p.add_argument('--parity1',type=Path,help="run1 parity receipt (default: 5.json beside --run1, if present)")
    p.add_argument('--parity2',type=Path,help="run2 parity receipt (default: 5.json beside --run2, if present)")
    p.add_argument('--relift',type=Path,default=HERE/'kit/r1/relift.py')
    p.add_argument('--t1',type=Path,help='T1 capture (default: relift BASE/cap/t1.gz)')
    p.add_argument('--out',type=Path,required=True);p.add_argument('--md',type=Path,required=True)
    p.add_argument('--skip-gaps',action='store_true');p.add_argument('--half-only',action='store_true')
    a=p.parse_args(argv);t0=time.time()
    R=load_relift(a.relift)
    refs={r['item_id']:r for r in json.loads((R.KIT/'items544.json').read_text())['items']}
    expected={r['capture'] for r in refs.values()}
    t1=a.t1 or R.BASE/'cap/t1.gz'
    t1rows,repeat,bounds=t1_reference(R,t1,refs)
    runs={};checks={}
    for tag,dp,rp,pp in (('run1',a.run1,a.receipt1,a.parity1),('run2',a.run2,a.receipt2,a.parity2)):
        rows,receipt,report=read_run(R,dp,rp,expected)
        pp=pp or (dp.parent/'5.json' if (dp.parent/'5.json').is_file() else None)
        parity=json.loads(pp.read_text()) if pp else None
        runs[tag]=dict(rows=rows,receipt=receipt,report=report,parity=parity,parity_path=str(pp) if pp else None)
    # Alignment: same captures, anchors and RGB binding as the manifest.
    for cap in sorted(expected):
        ref=next(r for r in refs.values() if r['capture']==cap)
        for tag in runs:
            m=runs[tag]['rows'][cap]['metadata']
            if m['geometry']['source_indices']!=ref['source_indices']:raise ValueError(f'{tag} {cap}: anchors differ from manifest')
            if m['frame_binding_sha256']!=ref['mapping']['frame_binding_sha256']:raise ValueError(f'{tag} {cap}: RGB binding differs')
    checks['captures_aligned']=len(expected)
    # Camera/scale: run vs T1 (per item, w.py definition) and run2 vs run1 (per capture).
    cam={}
    for tag in runs:
        per_item={};per_cap={}
        for iid,ref in refs.items():
            if not t1rows[iid]['geometry']:continue  # build_depth.reference keeps only T1 items with geometry
            g=runs[tag]['rows'][ref['capture']]['metadata']['geometry'];e=t1rows[iid]['geometry']
            per_item[iid]=dict(capture=ref['capture'],**w_compare(g,e),**pose_terms(g,e))
        checks['t1_items_with_geometry']=len(per_item)
        for cap in expected:
            its=[v for v in per_item.values() if v['capture']==cap]
            if not its:raise ValueError(f'{cap}: no T1 item with geometry')
            per_cap[cap]={k:max(v[k] for v in its) for k in its[0] if k!='capture'}
            per_cap[cap]['items']=len(its)
        # Reproduce the run's own embedded and receipt-level deviations.
        if all('parity' in r for r in runs[tag]['rows'].values()):
            emb={x['item_id']:x['max_deviations'] for r in runs[tag]['rows'].values() for x in r['parity']['items']}
            checks[f'{tag}_vs_t1_equals_embedded_row_parity']=set(emb)==set(per_item) and all(
                emb[i][k]==per_item[i][k] for i in emb for k in FIELDS)
        else:checks[f'{tag}_vs_t1_equals_embedded_row_parity']='rows carry no parity'
        par=runs[tag]['parity']
        if par:
            pe={x['item_id']:x['max_deviations'] for c in par['captures'] for x in c['items']}
            checks[f'{tag}_vs_t1_equals_parity_receipt_items']=set(pe)==set(per_item) and all(pe[i][k]==per_item[i][k] for i in pe for k in FIELDS)
            checks[f'{tag}_vs_t1_equals_parity_receipt_maxima']=all(par['max_deviations'][k]==max(v[k] for v in per_item.values()) for k in FIELDS)
            checks[f'{tag}_parity_bounds_equal_t1_repeat_bounds']=all(par['bounds'][k]==bounds[k] for k in FIELDS)
        cam[f'{tag}_vs_t1']=dict(summary=summarize(per_cap,FIELDS+('translation_m_max','rotation_deg_max','K_abs_max','scale_abs')),
            trusted_by_receipt=par['trusted'] if par else None,
            captures_untrusted=sorted(c for c,r in runs[tag]['rows'].items() if not r.get('parity',{}).get('trusted',True)),
            captures_over_bounds=sorted(c for c in per_cap if any(per_cap[c][k]>bounds[k] for k in FIELDS)),
            per_capture=per_cap,per_item=per_item)
    rr={}
    for cap in sorted(expected):
        g1=runs['run1']['rows'][cap];g2=runs['run2']['rows'][cap]
        d1,_=R.fmt.decode(g1,half_only=a.half_only);d2,_=R.fmt.decode(g2,half_only=a.half_only)
        dd=np.abs(d1-d2)
        rr[cap]=dict(**w_compare(g2['metadata']['geometry'],g1['metadata']['geometry']),
                     **pose_terms(g2['metadata']['geometry'],g1['metadata']['geometry']),
                     depth_abs_max=float(dd.max()),depth_abs_median=float(np.median(dd)),
                     depth_rel_max=float(np.max(dd/np.maximum(np.abs(d1),1e-6))),
                     depth_identical=bool(g1['depth_sha256']==g2['depth_sha256']))
    cam['run2_vs_run1']=dict(summary=summarize(rr,FIELDS+('translation_m_max','rotation_deg_max','K_abs_max','scale_abs','depth_abs_max')),
                             per_capture=rr)
    agree={}
    for k in FIELDS:
        worst=max(rr,key=lambda c:rr[c][k])
        agree[k]=dict(bound=bounds[k],max=rr[worst][k],worst=worst,over_bound=sum(rr[c][k]>bounds[k] for c in rr),
                      within=all(rr[c][k]<=bounds[k] for c in rr))
    res=dict(inputs=dict(run1=str(a.run1),receipt1=str(a.receipt1),run2=str(a.run2),receipt2=str(a.receipt2),
                         parity1=runs['run1']['parity_path'],parity2=runs['run2']['parity_path'],t1=str(t1),relift=str(a.relift),
                         run1_sha256=runs['run1']['report']['raw_sha256'],run2_sha256=runs['run2']['report']['raw_sha256'],
                         depth_precision='float16 only' if a.half_only else 'float16 plus exact residual'),
             definitions=dict(fields='max |a-b| over all anchors and matrix entries (runtime/w.py compare); vs T1 per item against T1 pass-0 geometry, per capture = max over its items',
                              translation_m='Euclidean distance of metric camera centres, per anchor; *_max/_median over 32 anchors',
                              rotation_deg='geodesic angle between camera rotations, per anchor',
                              bounds='twice the maximum |T1 repeat - T1 pass 0| over the 10 T1 repeats (build_depth.reference)',
                              gap_classes='|round2(a)-round2(b)|: equal (0.00 m), 0.01, beyond (>=0.02), missing (one side None)'),
             t1_bounds=bounds,t1_repeat_deviations=repeat,camera=cam,
             agreement_within_t1_bounds=dict(all_within=all(v['within'] for v in agree.values()),fields=agree),checks=checks)
    if not a.skip_gaps:
        gaps={tag:recompute_gaps(R,runs[tag]['rows'],t1rows,refs,a.half_only) for tag in runs}
        names={i:v['names'] for i,v in gaps['run1'].items()}
        tables={}
        for name,f in (('run1_vs_printed',lambda i:gap_class(gaps['run1'][i]['gap'],gaps['run1'][i]['printed'])),
                       ('run2_vs_printed',lambda i:gap_class(gaps['run2'][i]['gap'],gaps['run2'][i]['printed'])),
                       ('run2_vs_run1',lambda i:gap_class(gaps['run2'][i]['gap'],gaps['run1'][i]['gap']))):
            cls={i:f(i) for i in refs}
            tables[name]={ds:tally({i:c for i,c in cls.items() if ds=='all' or refs[i]['capture'].split('/')[0]==ds},refs,names)
                          for ds in DATASETS+('all',)}
        bd=[box_diff(b2,b1) for i in refs for b1,b2 in zip(gaps['run1'][i]['boxes'],gaps['run2'][i]['boxes'])]
        bd_f=[x for x in bd if x is not None]
        per_item=[dict(item_id=i,capture=refs[i]['capture'],printed_m=gaps['run1'][i]['printed'],run1_m=gaps['run1'][i]['gap'],
                       run2_m=gaps['run2'][i]['gap'],run1_raw=gaps['run1'][i]['raw'],run2_raw=gaps['run2'][i]['raw'],
                       object_box_diff_run2_vs_run1=[box_diff(b2,b1) for b1,b2 in zip(gaps['run1'][i]['boxes'],gaps['run2'][i]['boxes'])])
                  for i in refs]
        res['gaps']=dict(tables=tables,items=per_item,
            object_boxes_run2_vs_run1=dict(n=len(bd),identical=sum(x==0 or x is None for x in bd),
                                           max_abs=max(bd_f) if bd_f else None,
                                           worst=sorted(((x,o['item_id']) for o in per_item for x in o['object_box_diff_run2_vs_run1'] if x),reverse=True)[:5]))
        dfp=R.depth_free_parity(t1rows,refs)
        checks['depth_free_gap_checks_all_match']=all(x['match'] for x in dfp);checks['depth_free_gap_checks']=len(dfp)
    res['seconds']=time.time()-t0
    R.dump(a.out,res);write_md(a.md,res)
    print(json.dumps(dict(checks=checks,agreement=res['agreement_within_t1_bounds']['all_within'],
                          gaps={k:v['all']['items'] for k,v in res.get('gaps',{}).get('tables',{}).items()},seconds=round(res['seconds'],1))))
    return 0


if __name__=='__main__':raise SystemExit(main())
