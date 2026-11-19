"""CPU-only, train-only scale pricing with frozen folds and output refusal."""
import os
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='8'
os.environ['CUDA_VISIBLE_DEVICES']=''
import sys
sys.dont_write_bytecode=True
import ast, importlib.util, json, hashlib, time, re, gzip
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'out'
BASE=Path('/scratch/jjyeung/orch_n30/sb_scale1')
TREE=Path('/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872')
sys.path.insert(0,str(TREE))
from student_pilot import ground_lifting, camera_targets
from student_pilot.ground_profiles import load_geometry
from student_pilot.scene_state import FrameMap
from trace_format.ground_v313 import Session
if 'torch' in sys.modules: sys.modules['torch'].set_num_threads(8)
spec=importlib.util.spec_from_file_location('scale1',BASE/'code/scale_analysis.py')
s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
sha,read,dump,digest=s.sha,s.read,s.dump,s.digest
TIMINGS=defaultdict(float)
for name in ('geometry_npz','distance','attempt','norm','gravities'):
    nodes=[n for n in ast.parse(s.HARNESS.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(s.HARNESS),'exec'),globals())
COMMAND='env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B code/scale_drift.py score'
SCORE_FILES=('ITEMS12.json','ITEMS12.md','SCALE_DRIFT.json','SCALE_DRIFT_REPORT.md','CAPTURE_SCORES.json','DISTANCE_ROWS.json')
def refuse(directory=OUT):
    for name in SCORE_FILES:
        if (directory/name).exists(): raise RuntimeError('Refuse scoring/freeze: score file exists: '+name)
def codepins():
    paths={Path(__file__),ROOT/'code/test_scale_drift.py',BASE/'code/scale_analysis.py',s.HARNESS,s.CAMERA,s.RULE_CODE,s.RULE}
    for module in list(sys.modules.values()):
        p=getattr(module,'__file__',None)
        if p and Path(p).is_relative_to(TREE) and Path(p).suffix=='.py': paths.add(Path(p))
    return {str(p):sha(p) for p in sorted(paths)}
def freeze():
    refuse()
    if (OUT/'BARS_FROZEN.json').exists(): raise RuntimeError('Bars already frozen')
    b=read(BASE/'out/BARS_FROZEN.json')
    pins=codepins()
    for p in [BASE/'out'/x for x in ('BARS_FROZEN.json','SCALE_REPORT.md','NEEDS.md','NEEDS_INPUTS.json')]+[s.MANIFEST,ROOT/'prompts/sb_scale2.md',OUT/'SOURCE_SEARCH.txt']:
        pins[str(p)]=sha(p)
    source_paths=[Path(p) for p in (OUT/'SOURCE_SEARCH.txt').read_text().splitlines() if '/sb_records/out/kit/inputs/' in p]
    for p in source_paths: pins[str(p)]=sha(p)
    bars=dict(schema='sb-scale2-bars-v1',frozen_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),input_sha256=pins,
      code_sha256=sha(__file__),folds=b['folds'],room_halves=b['room_halves'],captures=b['captures'],source_paths=list(map(str,source_paths)),
      metrics=dict(displacement=b['metric'],pairs=b['pairs'],thresholds=b['thresholds'],
       distance='Exact E3 GT-mask distance(row,geometry,gt,predicted) with inferred G1 gravity; G3T depth and poses each scaled once; deployed box_grid_5cm and two-decimal response. Refusals score zero; finite predictions only in ratios. Equal-room primary; item mean also reported.',
       bias='Pooled item median predicted/GT and p10/p50/p90 of per-capture median ratios. Depth: matched grid cells, finite GT and own in (0.1,10), finite positive G3T, confidence strictly above clip median, valid GT frame. Also depth-implied scale from E3 frozen mask (without own restriction).',
       depth_pose='GT-depth-implied scale median(GT_depth/G3T_depth) on frozen GT-depth mask divided by per-capture LS GT pose-length scale. This is a consistency diagnostic through G3T, not proof of dataset label bias.'),
      fit=b['fit'],dataset_fit='Same room-balanced log fit as global, restricted to that dataset AND fit-half rooms. No fallback for absent dataset.',
      calibration_transfer='Fit factors on displacement only; apply identical factors to distance geometry and relift. No distance-target tuning.',
      arms=dict(A='step544 own scale; also frozen donor544',G='global c times A; also calibrated donor544',D='dataset c times A; also calibrated donor544',
       donor400='MISSING pending exact step400 own forward',freeze_training='MISSING; equals N init step400 only with head, private features and FoV conditioning frozen',
       reweight_source='MISSING unless local target rows identify bias; any causal price needs retraining',learned='REJECT unless new paired number supports it; no substitution from external evaluation'),
      bootstrap=b['bootstrap'],decisions=dict(calibration='Adopt only if paired improvement over A has lower CI > 0 in both folds and combined; prefer dataset over global only if D-G passes the same rule. Routed distance must not have CI-supported harm (upper CI < 0). Otherwise keep A.',
       donor544='Exactly A: zero paired difference, known level; no claim vs missing step400.',donor400='MISSING until forward and paired comparison.',freeze_training='MISSING until step400 forward plus output-invariance check.',reweight_source='Require receipt-backed source identity and targets; causal gain remains MISSING without a controlled retrain.',learned='Reject given user-supplied -9.3 points unless local paired evidence reverses it.'),
      source_search=dict(command="find /scratch/jjyeung -maxdepth 6 \\( -name '*8957d119*' -o -name '*a2v3*' -o -name '*a3v2*' \\) -print > out/SOURCE_SEARCH.txt",scope='Filename metadata only; irrelevant quarantine match not opened'),
      scope='Filter manifest to k1_split=train before capture payload access; no heldout/R0-dev/dev-S1/BENCH/withheld evaluation inputs.',
      missing_policy='No guessed mappings or imputed predictions. Missing GT capture excluded and listed; program refusal retained at zero MRA.')
    dump(OUT/'BARS_FROZEN.json',bars)
    (ROOT/'STATUS.md').write_text('The scoring bars are frozen. They copy sb_scale1 room folds exactly, pin code and inputs, and define room-balanced fitting, paired bootstrap decisions, and distance transfer without distance-target fitting. The source search found metadata-only scene lists and receipts; no source identity is inferred. CPU scoring is next.\n')
    print('FROZEN',flush=True)
def quant(a):
    return [float(x) for x in np.quantile(a,[.1,.5,.9])] if len(a) else None
def metric(records):
    by=defaultdict(list); ratios=[]; cm=[]; n=0; refusals=0
    for r in records:
        p=np.asarray(r['p'],float); g=np.asarray(r['gt'],float)
        scores=s.pair_scores(p,g); by[r['room']].extend(scores.tolist()); n+=len(g)
        v=np.isfinite(p); refusals+=int((~v).sum())
        if v.any():
            rr=p[v]/g[v]; ratios.extend(rr.tolist()); cm.append(float(np.median(rr)))
    rooms={k:float(np.mean(v)) for k,v in sorted(by.items())}
    vals=list(rooms.values())
    if not vals: return dict(status='MISSING'),{}
    return dict(status='OK',mra=float(np.mean(vals)),ci95=s.interval(vals),rooms=len(rooms),items=n,
      item_weighted_mra=float(np.mean([x for v in by.values() for x in v])),refusals=refusals,
      pooled_median_ratio=float(np.median(ratios)) if ratios else None,
      capture_median_ratio_p10_p50_p90=quant(cm),captures_with_ratio=len(cm)),rooms
def compare(records):
    arms={}; room={}
    for a in ('A','G','D'):
        arms[a],room[a]=metric([dict(r,p=r['pred'][a]) for r in records])
    diffs={}
    for name,a,b in [('G-A','G','A'),('D-A','D','A'),('D-G','D','G')]:
        keys=sorted(set(room[a])&set(room[b])); v=[room[a][k]-room[b][k] for k in keys]
        diffs[name]=dict(points=float(np.mean(v)),ci95=s.interval(v),rooms=len(keys)) if v else dict(status='MISSING')
    return dict(arms=arms,paired_differences=diffs)
def bydataset(records):
    return {ds:compare(records if ds=='all' else [r for r in records if r['dataset']==ds]) for ds in ('all','arkitscenes','scannet','scannetpp')}
def source_audit(bars):
    sources={}; receipts={}; schemas={}; pins={}
    for name in bars['source_paths']:
        p=Path(name); pins[name]=sha(p)
        if p.name.endswith('receipt.json'):
            version='a2v3' if 'a2v3' in p.name else 'a3v2'; receipts[version]=read(p)
        if p.name.endswith('.gz'):
            fields=set(); counts=Counter()
            with gzip.open(p,'rt') as f:
                for line in f:
                    r=json.loads(line); fields.update(r); counts[r['dataset']]+=1
            schemas['a2v3' if 'a2v3' in p.name else 'a3v2']=dict(path=name,fields=sorted(fields),counts=dict(counts))
    for version,ds in [('a2v3','d1'),('a2v3','d2'),('a3v2','d1'),('a3v2','d3')]:
        receipt=receipts[version]
        sources[version+' '+ds]=dict(status='MISSING',dataset_mapping='MISSING: receipts name only opaque d1/d2/d3',
          target_depth_over_G3T_depth='MISSING',target_depth_implied_scale_over_GT_pose_length_scale='MISSING',
          reason='Local scene rows contain identifiers only; target depths, corresponding G3T and GT poses are absent.',
          expected_target_database=receipt['database'],receipt_label_counts=receipt['labels'][ds],local_scene_rows=schemas[version])
    return dict(search=bars['source_search'],search_results=(OUT/'SOURCE_SEARCH.txt').read_text().splitlines(),sources=sources,input_sha256=pins)
def decision(folds,combined,contrast):
    ci=[f['all']['paired_differences'][contrast]['ci95'] for f in folds]+[combined['all']['paired_differences'][contrast]['ci95']]
    return 'SUPPORTED' if all(x[0]>0 for x in ci) else ('HARM' if all(x[1]<0 for x in ci) else 'INCONCLUSIVE')
def score():
    refuse(); bars=read(OUT/'BARS_FROZEN.json')
    assert bars['code_sha256']==sha(__file__),'Code changed after freeze'
    for p,h in bars['input_sha256'].items(): assert sha(p)==h,'Changed input: '+p
    assert bars['folds']==read(BASE/'out/BARS_FROZEN.json')['folds']
    pins=dict(bars['input_sha256']); pins[str(OUT/'BARS_FROZEN.json')]=sha(OUT/'BARS_FROZEN.json')
    cs={c['canonical']:c for c in s.training()}
    baseline_bars=read(BASE/'out/BARS_FROZEN.json')
    records=[]; caprows=[]; missing=[]; depth=defaultdict(lambda:defaultdict(list))
    start=time.monotonic()
    for n,r in enumerate(bars['captures']):
        c=cs[r['canonical']]; assert c['k1_split']=='train' and digest(c)==r['capture_sha256']
        if not r['gt_present']:
            missing.append(dict(capture=c['canonical'],reason='GT archive MISSING',expected=c['gt'])); continue
        for arm in ('tower','own544'):
            q=r[arm]; assert sha(q['path'])==q['sha256']; pins[q['path']]=q['sha256']; pins[q['receipt']]=sha(q['receipt'])
            receipt=read(q['receipt']); assert receipt['capture_sha256']==digest(c) and not receipt['synthetic']
            assert receipt['checkpoint']['sha256']==baseline_bars['input_sha256'][str(s.ART544)]
        gt,tower,hw=s.load_capture(c,(Path(r['tower']['path']).parent,read(r['tower']['receipt'])),False)
        pins[c['gt']['path']]=c['gt']['sha256']
        _,centres,_=s.to_gravity_reference_frame(tower['raw_pose'][tower['anchor_slots']],[0.,-1.,0.])
        i,j=np.triu_indices(32,1)
        truth=np.linalg.norm(gt['c2w'][i,:3,3]-gt['c2w'][j,:3,3],axis=1)
        ok=gt['valid'][i].astype(bool)&gt['valid'][j].astype(bool)&np.isfinite(truth)&(truth>=.1)
        raw=np.linalg.norm(centres[i]-centres[j],axis=1)[ok]; truth=truth[ok]
        assert len(raw)>0 and np.isfinite(raw).all()
        pose_scale=float(np.dot(raw,truth)/np.dot(raw,raw))
        with np.load(r['own544']['path'],allow_pickle=False) as z: own=z['depth']
        scale,mask,threshold=s.estimate(tower['depth_grid'],tower['depth_conf_grid'],own)
        ds=c['canonical'].split('/')[0]
        rec=dict(capture=c['canonical'],room=c['room'],dataset=ds,gt=truth,pred=dict(A=raw*scale))
        records.append(rec)
        axis=tower['grid_uv']; H,W=gt['depth'].shape[1:]
        x=np.clip(np.floor(axis/1000*W).astype(int),0,W-1); y=np.clip(np.floor(axis/1000*H).astype(int),0,H-1)
        truth_depth=gt['depth'][:,y[:,None],x[None,:]].astype(float); truth_depth[~gt['valid'].astype(bool)]=np.nan
        depth_scale,depth_mask,_=s.estimate(tower['depth_grid'],tower['depth_conf_grid'],truth_depth)
        common=mask&depth_mask
        assert common.any()
        values=dict(own_over_GT=own[common]/truth_depth[common],pose_scaled_G3T_over_GT=tower['depth_grid'][common]*pose_scale/truth_depth[common])
        row=dict(capture=c['canonical'],room=c['room'],dataset=ds,scale_A=scale,scale_pose=pose_scale,scale_depth=depth_scale,
            depth_scale_over_pose_scale=depth_scale/pose_scale,matched_depth_pixels=int(common.sum()),depth_mask_pixels=int(depth_mask.sum()),
            displacement_median_ratio=float(np.median(rec['pred']['A']/truth)),depth_ratios={k:dict(median=float(np.median(v)),p10_p50_p90=quant(v)) for k,v in values.items()})
        for k,v in values.items(): depth[ds][k].append(v)
        caprows.append(row)
        if (n+1)%30==0: print('pose/depth',n+1,flush=True)
    folds=[]; outfold=[]; coeff={}; fit_audit=[]
    for f in bars['folds']:
        fitrooms=set(f['fit_rooms']); testrooms=set(f['test_rooms']); assert not fitrooms&testrooms
        cg=s.fit(records,fitrooms,'A'); cd={ds:s.fit([r for r in records if r['dataset']==ds],fitrooms,'A') for ds in depth}
        audit={ds:sorted({r['room'] for r in records if r['dataset']==ds and r['room'] in fitrooms}) for ds in depth}
        assert all(not set(v)&testrooms for v in audit.values())
        fit_audit.append(dict(name=f['name'],global_fit_rooms=sorted({r['room'] for r in records if r['room'] in fitrooms}),dataset_fit_rooms=audit))
        coeff[f['name']]=dict(global_factor=cg,dataset_factors=cd)
        test=[]
        for r in records:
            if r['room'] not in testrooms: continue
            rr=dict(r,pred=dict(A=r['pred']['A'],G=r['pred']['A']*cg,D=r['pred']['A']*cd[r['dataset']]))
            test.append(rr); outfold.append(rr)
        folds.append(dict(name=f['name'],**bydataset(test)))
    displacement=dict(folds=folds,combined=bydataset(outfold),coefficients=coeff,fit_audit=fit_audit)
    displacement['decisions']={k:decision(folds,displacement['combined'],k) for k in ('G-A','D-A','D-G')}
    depth_summary={}
    for ds in ('all','arkitscenes','scannet','scannetpp'):
        caps=[r for r in caprows if ds=='all' or r['dataset']==ds]
        entry=dict(captures=len(caps),depth_scale_over_pose_scale_p10_p50_p90=quant([r['depth_scale_over_pose_scale'] for r in caps]))
        for k in ('own_over_GT','pose_scaled_G3T_over_GT'):
            vals=np.concatenate([v for d in depth if ds=='all' or ds==d for v in depth[d][k]])
            meds=[r['depth_ratios'][k]['median'] for r in caps]
            byroom=defaultdict(list)
            for r in caps: byroom[r['room']].append(r['depth_ratios'][k]['median'])
            roommed=[float(np.median(v)) for v in byroom.values()]
            entry[k]=dict(pooled_median_ratio=float(np.median(vals)),pixels=len(vals),capture_median_p10_p50_p90=quant(meds),mean_room_median=float(np.mean(roommed)),mean_room_median_ci95=s.interval(roommed))
        byroom=defaultdict(list)
        for r in caps: byroom[r['room']].append(r['depth_scale_over_pose_scale'])
        vals=[float(np.median(v)) for v in byroom.values()]
        entry['depth_scale_over_pose_scale_mean_room_median']=float(np.mean(vals)); entry['depth_scale_over_pose_scale_mean_room_median_ci95']=s.interval(vals)
        depth_summary[ds]=entry
    del depth
    (ROOT/'STATUS.md').write_text('The CPU displacement and depth diagnostics are computed under the frozen bars. Both calibration fits use only their fit-half rooms, and the unchanged folds match sb_scale1. Exact GT-mask distance pricing is running for the same three scale rules before ITEMS12 is published.\n')
    distance_records=[]; distance_rows=[]
    bycap={r['capture']:r for r in caprows}
    for n,r in enumerate(bars['captures']):
        if r['canonical'] not in bycap: continue
        c=cs[r['canonical']]; rows=[v for v in c['rows'] if v['type']=='object_abs_distance']
        assert c['k1_split']=='train'
        if not rows: continue
        cr=bycap[c['canonical']]
        f=next(f for f in bars['folds'] if c['room'] in f['test_rooms']); co=coeff[f['name']]
        gt,tower,hw=s.load_capture(c,(Path(r['tower']['path']).parent,read(r['tower']['receipt'])),True)
        preds={}
        for a,factor in [('A',1.),('G',co['global_factor']),('D',co['dataset_factors'][cr['dataset']])]:
            try:
                gravity=gravities(tower,gt)['G1']
                geo=geometry_npz(c,tower,hw,gravity,cr['scale_A']*factor,a)
                geometry_error=None
            except (ValueError, FloatingPointError, np.linalg.LinAlgError) as exc:
                geo=None; geometry_error=type(exc).__name__+':'+str(exc)
            cache={}; values=[]
            for row in rows:
                p,error=(None,geometry_error) if geo is None else attempt(lambda: distance(row,geo,gt,'predicted',cache))
                values.append(np.nan if p is None else p)
                distance_rows.append(dict(capture=c['canonical'],room=c['room'],dataset=cr['dataset'],row_id=row['id'],arm=a,pred=p,gt=float(row['gt_value']),refusal=error))
            preds[a]=np.array(values)
        distance_records.append(dict(capture=c['canonical'],room=c['room'],dataset=cr['dataset'],gt=np.array([float(v['gt_value']) for v in rows]),pred=preds))
        if (n+1)%10==0: print('distance',n+1,flush=True)
    distance_folds=[dict(name=f['name'],**bydataset([r for r in distance_records if r['room'] in f['test_rooms']])) for f in bars['folds']]
    distance_result=dict(folds=distance_folds,combined=bydataset(distance_records),calibration='Factors fitted to displacement; exact relift at each scale')
    distance_result['decisions']={k:decision(distance_folds,distance_result['combined'],k) for k in ('G-A','D-A','D-G')}
    src=source_audit(bars)
    result=dict(schema='sb-scale2-items12-v1',input_sha256=pins,code_sha256=sha(__file__),command=COMMAND,
        captures=len(records),rooms=len({r['room'] for r in records}),pairs=sum(len(r['gt']) for r in records),missing=missing,
        displacement=displacement,distance=distance_result,depth=depth_summary,pose_stream=src,elapsed_seconds=time.monotonic()-start,
        interpretation='Depth/pose scale mismatch can reflect G3T shape or intrinsics as well as GT labels; it alone cannot identify a biased training source.')
    dump(OUT/'CAPTURE_SCORES.json',dict(input_sha256=pins,captures=caprows))
    dump(OUT/'DISTANCE_ROWS.json',dict(input_sha256=pins,rows=distance_rows))
    dump(OUT/'ITEMS12.json',result)
    write_items(result)
    (ROOT/'STATUS.md').write_text('ITEMS12.md and ITEMS12.json are complete. They report K1 training displacement, exact GT-mask routed distance, global-versus-dataset calibration, depth/pose consistency, and the four missing source-target comparisons. Final option pricing and validation are next.\n')
    print('ITEMS12 COMPLETE',flush=True)
def fmt(v): return f"{v['mra']:.3f} [{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}]"
def delta(v): return f"{v['points']:+.3f} [{v['ci95'][0]:+.3f}, {v['ci95'][1]:+.3f}]"
def triple(v): return ' / '.join(f'{x:.4f}' for x in v) if v else 'MISSING'
def write_items(r):
    lines=['# K1 training scale bias and depth consistency','',
     'The two swapped test halves measure calibration at step 544. Step-400 predictions remain MISSING. Dataset-specific calibration must beat global calibration in both halves and combined before it is preferred.',
     '',f"The population contains {r['captures']} captures, {r['rooms']} rooms and {r['pairs']:,} displacement pairs. Three unavailable GT archives are listed in the JSON. No held-out payload or item was evaluated.",'',
     'MRA uses ten strict relative-error thresholds and averages within room, then across rooms. Intervals resample rooms 10,000 times with seed 17. Factors are fixed during bootstrap. Ratio distributions are descriptive: pooled item median and p10/p50/p90 across capture medians. Distance refusals score zero and do not enter ratio summaries.','']
    for kind in ('displacement','distance'):
        lines += [f'## {kind.title()}', '', '| Dataset | A MRA [95% CI] | Pooled predicted/GT | Capture medians p10 / p50 / p90 | Items / rooms |','|---|---:|---:|---:|---:|']
        for ds,v in r[kind]['combined'].items():
            a=v['arms']['A']; lines.append(f"| {ds} | {fmt(a)} | {a['pooled_median_ratio']:.4f} | {triple(a['capture_median_ratio_p10_p50_p90'])} | {a['items']} / {a['rooms']} |")
        lines += ['', '| Contrast | Fold 1 points [95% CI] | Fold 2 points [95% CI] | Combined points [95% CI] | Decision |','|---|---:|---:|---:|---|']
        for k in ('G-A','D-A','D-G'):
            vv=[f['all']['paired_differences'][k] for f in r[kind]['folds']]+[r[kind]['combined']['all']['paired_differences'][k]]
            lines.append('| '+k+' | '+' | '.join(delta(v) for v in vv)+' | '+r[kind]['decisions'][k]+' |')
        lines.append('')
    lines += ['G is global calibration; D is calibration per dataset. Both are fit to displacement in fit-half rooms only. The exact same factor scales G3T depth and translations for distance; E3 relifts the GT masks for every arm, retaining its bestspread-style box grid, 5 cm gap grid and two-decimal output. Distance is a GT-mask geometry diagnostic, not an end-to-end grounding score.','', '| Fit half | Global c | ARKitScenes c | ScanNet c | ScanNet++ c |','|---|---:|---:|---:|---:|']
    for f,v in r['displacement']['coefficients'].items(): lines.append(f"| {f} | {v['global_factor']:.6f} | "+' | '.join(f"{v['dataset_factors'][d]:.6f}" for d in ('arkitscenes','scannet','scannetpp'))+' |')
    lines += ['', '## Depth versus metric poses','', 'Depth comparisons sample the same 51×51 grid using E3 floor-and-clip coordinates. The matched mask requires finite GT and own depth in (0.1,10) m, positive G3T depth, valid GT frames, and G3T confidence above the clip median. GT-depth-implied scale uses the frozen GT-depth mask without the own-depth restriction. Pose scale fits all eligible pose lengths by zero-intercept least squares.','', '| Dataset | Own/GT pooled; capture p10/p50/p90 | Pose-scaled G3T/GT pooled; capture p10/p50/p90 | Depth-scale/pose-scale capture p10/p50/p90 |','|---|---:|---:|---:|']
    for ds,v in r['depth'].items():
        a=v['own_over_GT']; b=v['pose_scaled_G3T_over_GT']; lines.append(f"| {ds} | {a['pooled_median_ratio']:.4f}; {triple(a['capture_median_p10_p50_p90'])} | {b['pooled_median_ratio']:.4f}; {triple(b['capture_median_p10_p50_p90'])} | {triple(v['depth_scale_over_pose_scale_p10_p50_p90'])} |")
    lines += ['',r['interpretation'],'', '## Pose-stream sources','', 'The bounded filename search found receipts and identifier-only scene lists. Neither receipt states a real dataset-name mapping. No local target depths, corresponding G3T depth, or metric pose-length labels were found in these copies. All four comparisons and source-removal prices are MISSING.','', '| Source | Receipt depth rows | Missing target database | Dataset mapping |','|---|---:|---|---|']
    for name,v in r['pose_stream']['sources'].items(): lines.append(f"| {name} | {v['receipt_label_counts']['depth_rows']} | `{v['expected_target_database']['path']}` | MISSING |")
    lines += ['', 'The exact searched names were `*8957d119*`, `*a2v3*`, and `*a3v2*` under `/scratch/jjyeung` to depth 6. `SOURCE_SEARCH.txt` records all matches. Scene lists have only dataset code, row index, question identifier, scene, and optionally recording identifier. Counts do not supply metric targets.','', '## Commands and provenance','', 'All scored numbers and intervals in this report come from:', '', '```sh',COMMAND,'```','', 'The source search command is:', '', '```sh',r['pose_stream']['search']['command'],'```','', 'Each JSON pins its input files by SHA-256. BARS_FROZEN.json copies sb_scale1 folds exactly and freezes metrics, fitting and decisions before scoring. Existing score files cause a refusal. No code, data or outputs outside this workspace were changed.']
    (OUT/'ITEMS12.md').write_text('\n'.join(lines)+'\n')
if __name__=='__main__': {'freeze':freeze,'score':score}[sys.argv[1]]()
