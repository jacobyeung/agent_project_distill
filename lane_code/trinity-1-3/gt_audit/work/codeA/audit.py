"""CPU-only extent audit; all writes stay in the three authorized directories."""
import os
os.environ.update(PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', CUDA_VISIBLE_DEVICES='')
import ast, collections, datetime, glob, hashlib, itertools, json, math, pathlib, resource, sys, time
import numpy as np
from scipy.spatial import cKDTree

L=pathlib.Path('/scratch/jjyeung/orch_n30/rows_r1')
OUT=L/'out/extent_audit'; CLEAN=L/'out/recovery_v2x'; CODE=L/'work/codeD'
GEOM=pathlib.Path('/scratch/jjyeung/orch_n30/rows_a2/vsti/code/geometry.py')
LABEL=pathlib.Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/tree_r1/trace_format/box_v313.py')
ROOTS=['/scratch/jjyeung/orch_n30/rows_a2/work/rroot_v3','/scratch/jjyeung/orch_n30/b12_cntapp/work/rasters']
BUILD9=pathlib.Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/rows_slices/slices_final')
FILES={'recovery_v2':L/'out/recovery_v2/rows.jsonl','unit_slice':L/'out/units_p_slice/rows.jsonl',
       'build9_recovery':BUILD9/'a0_recovery.jsonl','build9_units':BUILD9/'a0_units.jsonl',
       'build9_pool_abs_distance_reworded':BUILD9/'a0_pool_abs_distance_reworded.jsonl',
       'unit_slice_v2':L/'out/units_p_slice_v2/rows.jsonl'}

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def dump(path,obj):
    with open(path,'w') as f:json.dump(obj,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')

def extract(path,names):
    tree=ast.parse(path.read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert len(nodes)==len(names)
    env={'np':np};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),env)
    return env

G=extract(GEOM,{'backproject','verify_source'})
S=extract(LABEL,{'box','grid_points','box_grid_5cm'})

def boxkey(can,b):
    return hashlib.sha256(json.dumps([can,b],sort_keys=True,separators=(',',':')).encode()).hexdigest()[:24]

def num(x):
    try:
        f=float(x);return f if math.isfinite(f) else None
    except (ValueError,TypeError):return None

def inventory():
    aliases=json.load(open('/scratch/jjyeung/orch_n30/rows_a2/work/alias_map.json'))
    rows=[]; boxes={}; inputs={}
    for family,path in FILES.items():
        if not path.exists():inputs[family]={'path':str(path),'exists':False};continue
        h=hashlib.sha256(); n=0
        with open(path,'rb') as f:
            for line,raw in enumerate(f,1):
                if not raw.endswith(b'\n'):raise RuntimeError('Input is still being written: '+str(path))
                r=json.loads(raw);h.update(raw);n+=1;g=r.get('ground_record',r);a=g.get('program_audit',{})
                can=g.get('canonical') or r.get('provenance',{}).get('canonical') or g.get('room') or aliases.get(str(r.get('dataset'))+'/'+str(r.get('scene')))
                bs=a.get('independent_ordered_boxes',[]); keys=[]
                for b in bs:
                    k=boxkey(can,b);boxes[k]={'canonical':can,'box':b};keys.append(k)
                ds=can.split('/')[0] if can else str(r.get('dataset','unknown'))
                source=num(g.get('source_gt_answer',g.get('source_join',{}).get('gt_answer')))
                metric=num(g.get('native_independent_label',a.get('independent_target')))
                rows.append(dict(family=family,line=line,qid=r.get('qid'),canonical=can,dataset=ds,
                    box_keys=keys,source_m=source,stored_m=metric,stored_gt=num(r.get('gt_answer',g.get('gt_answer'))),
                    unit=g.get('unit','meters'),roles=g.get('roles',{}),rule=a.get('target_distance_rule'),
                    line_sha256=hashlib.sha256(raw).hexdigest()))
        inputs[family]={'path':str(path),'exists':True,'rows':n,'bytes':path.stat().st_size,'sha256':h.hexdigest()}
    dump(CODE/'inventory.json',{'rows':rows,'boxes':boxes,'inputs':inputs})
    print('inventory',len(rows),'rows',len(boxes),'unique boxes',flush=True)
    return rows,boxes,inputs

def raster_index():
    ix=collections.defaultdict(list)
    for root in ROOTS:
        for f in sorted(glob.glob(root+'/**/*.npz',recursive=True)):
            # Canonical ScanNet++ aliases share raster keys. Bare numeric files are ARKitScenes.
            name=pathlib.Path(f).stem
            if name.isdigit():name='arkitscenes__'+name
            if f not in ix[name]:ix[name].append(f)
    return ix

def metrics(P,b,trans=False):
    lengths=np.asarray(b['axesLengths'],float);axes=np.asarray(b['normalizedAxes'],float).reshape(3,3)
    if trans:axes=axes.T
    if not len(P) or not np.isfinite(lengths).all() or np.min(lengths)<=0 or not np.allclose(axes@axes.T,np.eye(3),atol=.02):return None
    q=np.abs((P-np.asarray(b['centroid']))@axes.T)
    stable=lengths>=.12
    ratio=np.max(q[:,stable]/lengths[stable],axis=1) if stable.any() else np.max(q/lengths,axis=1)
    return {'points':len(P),'x1_inside_6cm':float(np.mean((q<=lengths*.5+.06).all(1))),
            'x2_inside_6cm':float(np.mean((q<=lengths+.06).all(1))),
            'x1_inside_exact':float(np.mean((q<=lengths*.5).all(1))),
            'x2_inside_exact':float(np.mean((q<=lengths).all(1))),
            'p98_max_relative_extent':float(np.quantile(ratio,.98)),
            'stable_axes':int(stable.sum()),'p98_axis_relative_extent':np.quantile(q/lengths,.98,axis=0).tolist()}

def classify(m,frames):
    if not m or m['points']<100 or frames<2 or not m['stable_axes']:return 'unknown'
    r=m['p98_max_relative_extent'];s1=m['x1_inside_6cm'];s2=m['x2_inside_6cm']
    if s1>=.95 and .35<=r<=.60:return 'full'
    if s2>=.90 and .70<=r<=1.15 and (s2-s1)>=.15:return 'half'
    return 'unknown'

def measure_rasters(boxes):
    cachepath=CODE/'box_measurements.json'; scenepath=CODE/'raster_checks.json'
    cache=json.load(open(cachepath)) if cachepath.exists() else {}
    checks=json.load(open(scenepath)) if scenepath.exists() else {}
    ix=raster_index(); byscene=collections.defaultdict(list)
    for k,b in boxes.items():
        if k not in cache:byscene[b['canonical']].append(k)
    for si,(can,keys) in enumerate(sorted(byscene.items(),key=lambda x:str(x[0]))):
        rk=can.replace('scannetpp/','scannetppv2/').replace('/','__') if can else ''
        paths=ix.get(rk,[])
        if not paths:
            for k in keys:cache[k]={'status':'unknown','method':'no_raster','reason':'No matching raster in the two authorized roots.'}
            continue
        candidates=collections.defaultdict(list)
        for path in paths:
            with np.load(path,allow_pickle=False) as z:
                # Only the arrays used by verify_source and instance backprojection enter memory.
                data={k:z[k] for k in ['depth','inst','c2w','K','ids','labels','obb_centroid','obb_lengths','obb_axes']}
                for name in ['K_frames','valid']:
                    if name in z.files:data[name]=z[name]
            if path not in checks:
                try:verify=G['verify_source'](data)
                except Exception as e:verify={'passed':False,'reason':type(e).__name__+': '+str(e)}
                # Floor/gravity is irrelevant to extent. Accept its box/pose check separately.
                depth=data['depth'];valid=data.get('valid',np.ones(len(depth),bool))&(depth>0).any(axis=(1,2))
                poses=data['c2w'].astype(float); rot=poses[valid,:3,:3]
                rotation_ok=bool(len(rot) and np.allclose(rot.transpose(0,2,1)@rot,np.eye(3),atol=.02) and np.allclose(np.linalg.det(rot),1,atol=.02))
                K=data.get('K_frames',np.repeat(data['K'][None],len(depth),axis=0))
                pp=[];ii=[]
                for f in np.flatnonzero(valid):
                    p=G['backproject'](depth[f],K[f],poses[f],6); good=(depth[f,::6,::6]>0)&np.isfinite(p).all(-1)
                    pp.append(p[good]);ii.append(data['inst'][f,::6,::6][good])
                P=np.concatenate(pp) if pp else np.empty((0,3));ids=np.concatenate(ii) if ii else np.empty(0)
                scores={};support={}
                for transpose in [False,True]:
                    allmetrics=[]
                    for j,iid in enumerate(data['ids']):
                        ps=P[ids==iid]
                        if len(ps)<10:continue
                        b={'axesLengths':data['obb_lengths'][j],'normalizedAxes':data['obb_axes'][j],'centroid':data['obb_centroid'][j]}
                        m=metrics(ps,b,transpose)
                        if m:allmetrics.append(m)
                    for scale in [1,2]:
                        eligible=[m for m in allmetrics if (.25<m['p98_max_relative_extent']<.70 if scale==1 else .65<m['p98_max_relative_extent']<1.2)]
                        score=sum(m[f'x{scale}_inside_6cm']*m['points'] for m in eligible)/max(1,sum(m['points'] for m in eligible))
                        key=('columns' if transpose else 'rows')+':x'+str(scale)
                        scores[key]=score;support[key]={'instances':len(eligible),'points':sum(m['points'] for m in eligible)}
                good=[k for k,v in scores.items() if v>=.88 and support[k]['instances']>=2 and support[k]['points']>=100]
                checks[path]={'sha256':sha(path),'vsti_verify_source':verify,'rotation_ok':rotation_ok,'pose_verified':rotation_ok and bool(good),
                              'pose':'c2w; OpenCV +z forward; pixel centers +0.5','raster_box_scores':scores,'raster_box_support':support,'passing_conventions':good}
            check=checks[path]
            wanted={int(boxes[k]['box']['instance_id']) for k in keys};points={i:[] for i in wanted};frames=collections.Counter();pixels=collections.Counter()
            d=data['depth'];K=data.get('K_frames',np.repeat(data['K'][None],len(d),axis=0));poses=data['c2w'];valid=data.get('valid',np.ones(len(d),bool))
            # Deterministic evenly spaced instance-pixel sample, at most 2,000 per frame.
            for f in np.flatnonzero(valid):
                for iid in wanted:
                    v,u=np.nonzero((data['inst'][f]==iid)&np.isfinite(d[f])&(d[f]>0))
                    pixels[iid]+=len(v)
                    if not len(v):continue
                    frames[iid]+=1
                    if len(v)>2000:
                        take=np.linspace(0,len(v)-1,2000,dtype=int);v=v[take];u=u[take]
                    rays=np.stack([u+.5,v+.5,np.ones(len(u))],1)@np.linalg.inv(K[f]).T
                    p=(rays*d[f,v,u,None])@poses[f,:3,:3].T+poses[f,:3,3]
                    points[iid].append(p)
            for k in keys:
                b=boxes[k]['box'];iid=int(b['instance_id']);P=np.concatenate(points[iid]) if points[iid] else np.empty((0,3))
                m=metrics(P,b); mt=metrics(P,b,True)
                status=classify(m,frames[iid]) if check['pose_verified'] else 'unknown'
                # Native label code uses row axes. A contradictory column interpretation is not accepted.
                candidates[k].append({'status':status,'method':'raster_containment','raster':path,'pose_verified':check['pose_verified'],
                    'instance_frames':frames[iid],'instance_pixels':pixels[iid],'rows_axes':m,'columns_axes_diagnostic':mt})
            del data,points
        for k,vals in candidates.items():
            decisive={x['status'] for x in vals if x['status']!='unknown'}
            status=next(iter(decisive)) if len(decisive)==1 else 'unknown'
            cache[k]={'status':status,'method':'raster_containment','reason':'Concordant decisive raster evidence.' if len(decisive)==1 else ('Raster disagreement.' if len(decisive)>1 else 'Insufficient or ambiguous containment evidence.'),'observations':vals}
        if si%10==0:
            dump(cachepath,cache);dump(scenepath,checks)
            print('raster scenes',si+1,'/',len(byscene),'boxes',len(cache),'RSS_MB',round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024),flush=True)
    dump(cachepath,cache);dump(scenepath,checks)
    return cache,checks

def native(b,factor=1):
    return {'centre':b['centroid'],'lengths':np.asarray(b['axesLengths'])*factor,'axes':np.asarray(b['normalizedAxes']).reshape(3,3)}

def pair_distance(bs,factors):
    # Every input carries exactly the two independent ordered boxes; no other instances are invented.
    if len(bs)!=2:raise ValueError('Expected two independent ordered boxes')
    for b,f in zip(bs,factors):
        n=np.prod(np.ceil(np.array(b['axesLengths'])*f/.05))
        if n>1500000:raise ValueError('Grid exceeds conservative 1.5 million point memory bound')
    return S['box_grid_5cm'](native(bs[0],factors[0]),native(bs[1],factors[1]))

def distances(rows,boxes,cache):
    path=CODE/'distance_cache.json';dc=json.load(open(path)) if path.exists() else {}
    evidence=collections.defaultdict(list)
    for i,r in enumerate(rows):
        ks=r['box_keys'];bs=[boxes[k]['box'] for k in ks]
        key=hashlib.sha256(json.dumps(ks).encode()).hexdigest()[:24]
        if key not in dc:
            values={};errors={}
            for factors in [(1,1),(2,2)]:
                try:values[''.join(map(str,factors))]=pair_distance(bs,factors)
                except Exception as e:errors[''.join(map(str,factors))]=type(e).__name__+': '+str(e)
            dc[key]={'values':values,'errors':errors}
        d=dc[key];r['distance_key']=key
        missing=[j for j,k in enumerate(ks) if cache[k]['method']=='no_raster']
        if missing and len(ks)==2 and r['source_m'] is not None:
            # Mixed hypotheses prevent a pair-level answer from silently certifying both boxes.
            for factors in [(1,2),(2,1)]:
                fk=''.join(map(str,factors))
                if fk not in d['values'] and fk not in d['errors']:
                    try:d['values'][fk]=pair_distance(bs,factors)
                    except Exception as e:d['errors'][fk]=type(e).__name__+': '+str(e)
            matches=[f for f,v in d['values'].items() if abs(v-r['source_m'])<=.03]
            for j in missing:
                factors={f[j] for f in matches}
                opposite=[abs(v-r['source_m']) for f,v in d['values'].items() if len(factors)==1 and f[j] not in factors]
                status='unknown'
                if len(d['values'])==4 and len(factors)==1 and opposite and min(opposite)>=.08:
                    status='full' if next(iter(factors))=='1' else 'half'
                evidence[ks[j]].append({'status':status,'source_m':r['source_m'],'matching_hypotheses':matches,'family':r['family'],'qid':r['qid'],'distance_key':key})
        if i%250==0:
            dump(path,dc);print('distances',i+1,'/',len(rows),'unique pairs',len(dc),flush=True)
    for k,ev in evidence.items():
        s={e['status'] for e in ev if e['status']!='unknown'}
        cache[k]={'status':next(iter(s)) if len(s)==1 else 'unknown','method':'source_distance_fallback','reason':'Unique per-box scale across all matching pair hypotheses; contradictions veto classification.','evidence':ev}
    # Mixed rows receive a selective correction in addition to the requested uniform x2 diagnostic.
    for r in rows:
        states=[cache[k]['status'] for k in r['box_keys']];d=dc[r['distance_key']]
        if len(states)==2 and 'unknown' not in states:
            factors=tuple(2 if s=='half' else 1 for s in states);fk=''.join(map(str,factors))
            if fk not in d['values'] and fk not in d['errors']:
                try:d['values'][fk]=pair_distance([boxes[k]['box'] for k in r['box_keys']],factors)
                except Exception as e:d['errors'][fk]=str(e)
            r['corrected_m']=d['values'].get(fk)
        else:r['corrected_m']=None
    dump(path,dc)
    return dc

def distribution(values):
    v=np.asarray([x for x in values if x is not None and math.isfinite(x)],float)
    if not len(v):return {'n':0}
    return dict(n=len(v),min=float(v.min()),p05=float(np.quantile(v,.05)),p25=float(np.quantile(v,.25)),median=float(np.median(v)),p75=float(np.quantile(v,.75)),p95=float(np.quantile(v,.95)),max=float(v.max()),mean=float(v.mean()))

def stats(rows,dc):
    ans={'rows':len(rows),'exclusive_row_status':dict(collections.Counter(r['status'] for r in rows)),
         'rows_with_box_status':{s:sum(s in r['box_statuses'] for r in rows) for s in ['full','half','unknown']},
         'box_occurrences':dict(collections.Counter(s for r in rows for s in r['box_statuses']))}
    half=[r for r in rows if 'half' in r['box_statuses']]
    comparisons={}
    for label,field in [('uniform_x2','x2_m'),('selective_correction','corrected_m')]:
        eligible=[r for r in half if r.get(field) is not None]
        vsstored=[r for r in eligible if r['stored_m'] is not None]
        vssource=[r for r in eligible if r['source_m'] is not None]
        comparisons[label]={'rows':len(eligible),'ratio_to_stored':distribution([r[field]/r['stored_m'] for r in vsstored if r['stored_m']>0]),
            'zero_stored_denominators':sum(r['stored_m']==0 for r in vsstored),
            'delta_to_stored_m':distribution([r[field]-r['stored_m'] for r in vsstored]),
            'absolute_error_to_source_m':distribution([abs(r[field]-r['source_m']) for r in vssource]),
            'source_within_3cm':sum(abs(r[field]-r['source_m'])<=.03 for r in vssource),'source_compared':len(vssource),
            'closer_to_source_than_stored':sum(r['stored_m'] is not None and abs(r[field]-r['source_m'])<abs(r['stored_m']-r['source_m']) for r in vssource)}
    ans['half_row_comparisons']=comparisons
    full=[r for r in rows if r['status']=='full' and r['x1_m'] is not None and r['stored_m'] is not None]
    ans['full_row_sampler_validation']={'compared':len(full),'within_1e_8_m':sum(abs(r['x1_m']-r['stored_m'])<1e-8 for r in full),
        'absolute_error_m':distribution([abs(r['x1_m']-r['stored_m']) for r in full])}
    return ans

def clean_slice(rows):
    decisions={r['line']:r for r in rows if r['family']=='recovery_v2'}
    counts={k:collections.Counter() for k in ['dataset_rows','missed_name_rows','all_operand_name_rows','missed_operand_positions','misses_per_row','status_rows','status_operands','membership_flag_counts']}
    cross=collections.Counter(); n=0; kept=[]
    with open(FILES['recovery_v2'],'rb') as src,open(CLEAN/'rows.jsonl','wb') as dst:
        for line,raw in enumerate(src,1):
            a=decisions[line];assert hashlib.sha256(raw).hexdigest()==a['line_sha256']
            if a['status']!='full':continue
            dst.write(raw);kept.append({'source_line':line,'qid':a['qid'],'sha256':a['line_sha256']});n+=1
            r=json.loads(raw);g=r['ground_record'];ds=a['dataset'].replace('scannetppv2','scannetpp')
            misses=g['simulated_misses'];names=[b['name'] for b in g['program_audit']['independent_ordered_boxes']]
            status=r['provenance']['details']['status'];nm=len(misses)
            counts['dataset_rows'][ds]+=1;counts['missed_name_rows'].update(set(misses));counts['all_operand_name_rows'].update(set(names))
            counts['misses_per_row'][str(nm)]+=1;counts['status_rows'][status]+=1;counts['status_operands'][status]+=nm
            for j,name in enumerate(names):
                if name in misses:counts['missed_operand_positions']['ab'[j]]+=1
            for name in set(misses):cross[(ds,status,nm,name)]+=1
            for field in ['training_admitted','diagnostic_only','gt_accepted','not_seen']:
                counts['membership_flag_counts'][field+'='+str(g.get(field)).lower()]+=1
    result={k:dict(v) for k,v in counts.items()};result.update(rows=n,source_rows=len(decisions),removed_rows=len(decisions)-n,
        selection='Keep exactly rows whose every independent ordered box is full. Preserve original bytes and order.',
        cross_status_misses_dataset_name=[dict(dataset=k[0],status=k[1],misses_per_row=k[2],name=k[3],rows=v) for k,v in sorted(cross.items())],
        source_sha256=sha(FILES['recovery_v2']),rows_sha256=sha(CLEAN/'rows.jsonl'))
    dump(CLEAN/'COUNTS.json',result);dump(CLEAN/'KEPT_LINES.json',kept)
    original=json.load(open(L/'out/recovery_v2/COUNTS.json'));real=original['real'];v1=original['v1'];v2=original['v2']
    text=['# Recovery v2x distribution','',f'The slice retains {n:,} of {len(decisions):,} recovery v2 rows. Every retained box is classified as full. Lines retain their exact source bytes and order. Counts describe this filter; the original selection quotas no longer apply.','',
          '## Dataset comparison','','| Dataset | v1 rows | v2 rows | v2x rows | Real failed pairs / all pairs |','|---|---:|---:|---:|---:|']
    for ds in ['scannetpp','scannet','arkitscenes']:text.append(f"| {ds} | {v1['dataset_rows'].get(ds,0)} | {v2['dataset_rows'].get(ds,0)} | {result['dataset_rows'].get(ds,0)} | {real['dataset_failed_pairs'][ds]} / {real['dataset_pairs'][ds]} |")
    text+=['','## Misses and statuses','','| Measure | v1 | v2 | v2x | Real evidence |','|---|---:|---:|---:|---|']
    for m,label in [('1','One miss'),('2','Two misses')]:text.append(f"| {label} | {v1['misses_per_row'].get(m,0)} | {v2['misses_per_row'].get(m,0)} | {result['misses_per_row'].get(m,0)} | {real['misses_per_failed_item'].get(m,0)} items |")
    for status in ['not seen','box unavailable']:text.append(f"| {status} | {v1['status_rows'].get(status,0)} rows | {v2['status_rows'].get(status,0)} rows | {result['status_rows'].get(status,0)} rows / {result['status_operands'].get(status,0)} operands | {real['printed_status_pairs'].get(status,0)} pairs |")
    text+=['','## Name comparison','','Counts refer to missed operands. Literal names remain distinct; the real comparison maps mouse to computer mouse.','','| Name | v1 rows | v2 rows | v2x rows | Real failures / pairs |','|---|---:|---:|---:|---:|---:|']
    for name in sorted(set(v1['missed_name_rows'])|set(v2['missed_name_rows'])|set(real['name_pairs'])):
        rn='computer mouse' if name=='mouse' else name
        text.append(f"| {name} | {v1['missed_name_rows'].get(name,0)} | {v2['missed_name_rows'].get(name,0)} | {result['missed_name_rows'].get(name,0)} | {real['missed_name_pairs'].get(rn,0)} / {real['name_pairs'].get(rn,0)} |")
    text+=['','## Real two-miss call sequences','','These supplied reference counts are unchanged; this audit did not replay the reader.']
    text += [f'- {v} items: `{k}`.' for k,v in real['two_miss_calls']['patterns'].items()]
    text+=['','## Membership flags','']+[f'- {k}: {v} rows.' for k,v in result['membership_flag_counts'].items()]
    text+=['','## Checks','','| Check | Result | Cases |','|---|---|---:|',f'| All retained boxes classified full | PASS | {n} |',f'| Retained line hashes match source | PASS | {n} |',f'| Source order preserved | PASS | {n} |','',
           'The audit does not rerun the original schema, tokenizer, admission, or Locate checks. The source membership flags remain unchanged. See ../extent_audit/REPORT.md for the measurement thresholds and unresolved cases.','']
    (CLEAN/'DISTRIBUTION.md').write_text('\n'.join(text))
    return result

def report(rows,boxes,inputs,cache,checks,dc):
    for r in rows:
        states=[cache[k]['status'] for k in r['box_keys']];r['box_statuses']=states
        r['status']='unknown' if not states or 'unknown' in states else ('half' if 'half' in states else 'full')
        # Presence counts separately expose rows that have both half and unknown boxes.
        r['x1_m']=dc[r['distance_key']]['values'].get('11');r['x2_m']=dc[r['distance_key']]['values'].get('22')
    summary={f:stats([r for r in rows if r['family']==f],dc) for f in inputs if inputs[f].get('exists')}
    grouped={f:{ds:stats([r for r in rows if r['family']==f and r['dataset']==ds],dc) for ds in sorted({r['dataset'] for r in rows if r['family']==f})} for f in summary}
    clean=clean_slice(rows)
    with open(OUT/'ROW_AUDIT.jsonl','w') as f:
        for r in rows:f.write(json.dumps(r,sort_keys=True,allow_nan=False)+'\n')
    dump(OUT/'BOX_AUDIT.json',{k:dict(boxes[k],**cache[k]) for k in boxes})
    dump(OUT/'RASTER_CHECKS.json',checks)
    validation=[r for r in rows if r['x1_m'] is not None and r['stored_m'] is not None]
    audit={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'inputs':inputs,'families':summary,'by_family_dataset':grouped,
        'unique_box_statuses':dict(collections.Counter(cache[k]['status'] for k in boxes)),
        'unique_box_methods':dict(collections.Counter(cache[k]['method'] for k in boxes)),
        'row_status_definition':'Exclusive: unknown if any unknown or no boxes; else half if any half; else full. Presence counts overlap.',
        'sampler_validation_all_rows':{'compared':len(validation),'within_1e_8_m':sum(abs(r['x1_m']-r['stored_m'])<1e-8 for r in validation),
            'absolute_error_m':distribution([abs(r['x1_m']-r['stored_m']) for r in validation])},
        'recovery_v2x':clean,'raster_files_read':len(checks),'raster_pose_verified':sum(c['pose_verified'] for c in checks.values()),
        'code_sha256':{'audit.py':sha(__file__),'geometry.py':sha(GEOM),'box_v313.py':sha(LABEL)},
        'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
        'distance_errors':{k:v['errors'] for k,v in dc.items() if v['errors']}}
    dump(OUT/'EXTENT_AUDIT.json',audit)
    t=['# Extent audit','',f"The clean recovery slice keeps {clean['rows']:,} of {clean['source_rows']:,} rows and excludes {clean['removed_rows']:,}. A row survives only when every native box is verified as full extents. Lines preserve source bytes and order.",'',
       '## Counts','','Exclusive row counts place any row with an unknown box in unknown, including rows that also contain a half box. Presence columns overlap. ScanNet++ and ScanNet++v2 remain separate here and combine in the recovery distribution.','',
       '| Family | Dataset | Rows | All full | Half, no unknown | Unknown present | Half present | Full present |','|---|---|---:|---:|---:|---:|---:|---:|']
    for family,sets in grouped.items():
        for ds,s in sets.items():
            e=s['exclusive_row_status'];p=s['rows_with_box_status'];t.append(f"| {family} | {ds} | {s['rows']} | {e.get('full',0)} | {e.get('half',0)} | {e.get('unknown',0)} | {p['half']} | {p['full']} |")
    t+=['','## Measurement method','',
        'Each box is keyed by its canonical scene and exact native geometry. No dataset-wide convention is assigned. The audit backprojects positive, finite instance depths with each raster’s K_frames (or K), c2w poses, and pixel centers at +0.5. It samples at most 2,000 evenly spaced labeled pixels per frame; all valid frames contribute. Both row and column axis layouts are recorded. The native distance implementation establishes row axes for the native boxes.',
        '',
        'The audit runs the supplied VSTI verify_source function and also checks the relevant pose/box portion independently: valid proper rotations, at least two raster instances and 100 sampled pixels, at least 88% containment, and relative extents consistent with the tested raster convention. Floor/gravity failures alone do not invalidate a distance audit. Raster checks and hashes are in RASTER_CHECKS.json.',
        '',
        'A native box needs at least 100 samples in two frames and at least one axis 0.12 m long. A full box needs at least 95% containment at x1 and a 98th-percentile maximum relative extent between 0.35 and 0.60. A half box needs at least 90% containment at x2, at least 15 percentage points of improvement over x1, and a relative extent between 0.70 and 1.15. Containment permits 6 cm, as in verify_source. The relative-extent statistic uses axes at least 0.12 m long to limit thin-axis noise. Conflicting decisive rasters veto a classification. Partial views, thin boxes, small instances, and failed pose checks can remain unknown.',
        '',
        'Only boxes without a matching raster use source-answer evidence. The audit tests all four two-box x1/x2 assignments, accepts source agreement within 0.03 m, and certifies a box only if all matching assignments give it the same scale and every opposite-scale assignment misses by at least 0.08 m. Contradictory decisive source rows veto the classification. This is conditional evidence from the source answer, not an independent geometric measurement.',
        '',
        'The distance implementation extracts the exact box, grid_points, and box_grid_5cm functions from the supplied formatter. Its linspace grid uses ceil(length/0.05) samples per axis, removes the inner half box, and takes the nearest grid-point distance with one CPU worker. The supplied independent audits contain two boxes per row; the audit measures that pair. It cannot establish whether unlisted instances would change the category-wide minimum. All comparisons use meters; unit-row feet answers remain untouched.',
        '',
        f"Sampler replay matches {audit['sampler_validation_all_rows']['within_1e_8_m']:,}/{len(validation):,} stored native labels within 1e-8 m. Per-family validation for rows classified full is in EXTENT_AUDIT.json.",
        '', '## Half-row answer changes','',
        'Uniform x2 doubles both boxes as requested. Selective correction doubles only boxes classified half and is available only when every box is known. Uniform x2 is a hypothesis, not a final correction, for mixed or unknown rows. Ratios below divide the uniform-x2 meter answer by the stored native meter answer; JSON includes quantiles, selective corrections, source errors, and row-level values.','',
        '| Family | Half present | x2/stored median | p05 | p95 | x2 within 3 cm of source | Source compared |','|---|---:|---:|---:|---:|---:|---:|']
    for family,s in summary.items():
        c=s['half_row_comparisons']['uniform_x2'];rat=c['ratio_to_stored']
        t.append(f"| {family} | {s['rows_with_box_status']['half']} | {rat.get('median','n/a')} | {rat.get('p05','n/a')} | {rat.get('p95','n/a')} | {c['source_within_3cm']} | {c['source_compared']} |")
    halfrec=[r for r in rows if r['family']=='recovery_v2' and 'half' in r['box_statuses']]
    fixable=[r for r in halfrec if 'unknown' not in r['box_statuses']]
    t+=['','## Price and method of a repair','',
        f"Filtering costs {clean['removed_rows']:,} recovery rows. Of {len(halfrec):,} recovery rows containing a half box, {len(fixable):,} have no unknown box and can receive a selective geometry correction under this audit. Unknown boxes require more geometric evidence before repair.",
        '',
        'A repair must double each confirmed half box’s lengths, recompute the 5 cm grid distances over the complete original instance sets, and regenerate the printed sizes from the corrected boxes in the response coordinate frame. It must update answers, unit conversion, distance responses, explanatory numbers, geometry audits, provenance, and response spans together. It must then rerun schema, trace, and label validation. Source answers are comparison evidence and should remain distinguishable from corrected labels. This audit does not rewrite or repair any row.',
        '', '## Open gaps','',
        '- The conservative thresholds leave ambiguous or weakly observed boxes unknown; excluded does not mean proven half.',
        '- Source-answer fallback is pair-based and depends on source correctness. Mixed hypotheses reduce but do not remove that limitation.',
        '- Two listed native boxes do not prove that all category instances are represented. Source disagreements can reflect this gap or other annotation differences.',
        '- The sampler is discretized; doubling boxes can move grid locations, so distances need not decrease strictly.',
        '- No GPU, network, SSH, Git, training, tree admission, or tokenizer validation ran.',
        f"- The unit_slice_v2 snapshot contains {inputs.get('unit_slice_v2',{}).get('rows',0):,} rows; the requested full build has 10,945 rows. Its exact audited snapshot hash is recorded even if the producing job later changes the file.",
        '', '## Artifacts and hashes','',f"- Clean rows SHA-256: `{clean['rows_sha256']}`.",f"- Recovery source SHA-256: `{clean['source_sha256']}`.",
        '- EXTENT_AUDIT.json contains aggregate counts and input/code hashes. ROW_AUDIT.jsonl and BOX_AUDIT.json connect every row and box to its evidence. KEPT_LINES.json records each retained source line and hash.',
        f"- Peak process RSS: {audit['peak_rss_mib']:.1f} MiB. Output size and byte-preservation checks appear in VALIDATION.json.",'']
    (OUT/'REPORT.md').write_text('\n'.join(t))
    return audit

def validate(inputs):
    kept=json.load(open(CLEAN/'KEPT_LINES.json'));expected={x['source_line']:x for x in kept};actual=[]
    with open(CLEAN/'rows.jsonl','rb') as f:
        for raw in f:actual.append(hashlib.sha256(raw).hexdigest())
    assert actual==[x['sha256'] for x in kept]
    assert [x['source_line'] for x in kept]==sorted(expected)
    assert sha(FILES['recovery_v2'])==inputs['recovery_v2']['sha256']
    files=[p for root in [OUT,CLEAN,CODE] for p in root.rglob('*') if p.is_file()]
    total=sum(p.stat().st_size for p in files);assert total<1000000000
    result={'retained_rows':len(kept),'byte_identical_line_hashes':True,'source_order':True,'recovery_input_unchanged':True,'total_artifact_bytes':total,
            'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
            'current_input_sha256':{f:sha(p) for f,p in FILES.items() if p.exists()},
            'audited_input_sha256':{f:v['sha256'] for f,v in inputs.items() if v.get('exists')}}
    dump(OUT/'VALIDATION.json',result)
    dump(OUT/'HASHES.json',{str(p.relative_to(L)):sha(p) for p in sorted(files) if p.name!='HASHES.json'})
    print(json.dumps(result),flush=True)

def main():
    OUT.mkdir(exist_ok=True);CLEAN.mkdir(exist_ok=True)
    rows,boxes,inputs=inventory();cache,checks=measure_rasters(boxes);dc=distances(rows,boxes,cache)
    report(rows,boxes,inputs,cache,checks,dc);validate(inputs)

if __name__=='__main__':main()
