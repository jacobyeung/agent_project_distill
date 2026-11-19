import collections as C
import hashlib, io, json, os, pathlib, sys
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
B = pathlib.Path('/scratch/jjyeung/orch_n30')
K = B / 'sb_kbox4'
F = B / 'sb_maskfail'
PINS = {}

def read(p):
    p = pathlib.Path(p)
    assert str(p).startswith('/scratch/'), str(p)
    data = p.read_bytes()
    PINS[str(p)] = hashlib.sha256(data).hexdigest()
    return data

def js(p): return json.loads(read(p))
def lines(p): return set(read(p).decode().splitlines())
def digest(s): return hashlib.sha256(json.dumps(s, sort_keys=True, allow_nan=False).encode()).hexdigest()[:16]
def save(name, d):
    PINS[str(pathlib.Path(__file__).resolve())] = hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()
    d['input_sha256'] = dict(PINS)
    (HERE / name).write_text(json.dumps(d, indent=2) + '\n')
def mra(r):
    if r['prediction'] is None: return 0.
    return float(np.mean([abs(r['prediction']-r['label'])/abs(r['label']) < 1-t for t in np.arange(.5,.96,.05)])) * 100

def numbers():
    for p in sorted((HERE/'in').glob('*.md')): read(p)
    read(F/'RULES.md'); read(K/'math_v2.py')
    records = js(F/'out/MASKFAIL.json')['records']
    attrib = js(F/'out/ATTRIBUTION.json')
    splits = js(F/'out/SPLITS.json')
    items = [json.loads(x) for x in read(K/'out/box_ladder/PER_ITEM.jsonl').splitlines()]
    arms = C.defaultdict(dict)
    for r in items: arms[r['arm']][r['row_id']] = r
    base, gt = arms['A0_deployed'], arms['A2_gt_masks']
    objs = C.defaultdict(list)
    for r in records: objs[(r['row'], r['object'])].append(r)
    cats, recalls = {}, {}
    for key, rr in objs.items():
        price = next((r for r in rr if r['frame']==r['pricing_best_frame']), None)
        if rr[0]['selected_candidate_id'] is None: cat = 'refused'
        elif price and (price['iou'] or 0)>=.5: cat = 'good'
        elif max(r['iou'] or 0 for r in rr)<.1 and max(r['precision'] for r in rr)<.2: cat='wrong'
        elif max(r['iou'] or 0 for r in rr)>=.5: cat='poor_frame'
        else: cat='weak'
        cats[key] = cat
        recalls[key] = any(r['valid'] and r['visible'] and r['deployed_best_iou']>=.5 for r in rr)
    priority = {'good':0, 'poor_frame':1, 'weak':2, 'wrong':3, 'refused':4}
    groups = C.defaultdict(list)
    rowkeys = C.defaultdict(list)
    for key in objs: rowkeys[key[0]].append(key)
    for rid, keys in rowkeys.items(): groups[max((cats[k] for k in keys), key=priority.get)].append(rid)
    def summary(ids):
        return dict(rows=len(ids), A0=sum(mra(base[i]) for i in ids)/len(ids), A2=sum(mra(gt[i]) for i in ids)/len(ids), contribution=sum(mra(gt[i])-mra(base[i]) for i in ids)/len(base))
    wr = groups['wrong'] + groups['refused']
    no_pool = [rid for rid in wr if any(not recalls[k] for k in rowkeys[rid] if cats[k] in ('wrong','refused'))]
    has_pool = [rid for rid in wr if rid not in set(no_pool)]
    ds = C.defaultdict(list)
    for rid, r in base.items(): ds[r['dataset']].append(rid)
    visible = [r for r in records if r['valid'] and r['visible']]
    large = [r for r in visible if r['share']>.01]
    def fr(rr): return dict(n=len(rr), served=sum((r['iou'] or 0)>=.5 for r in rr)/len(rr), pool=sum(r['deployed_best_iou']>=.5 for r in rr)/len(rr))
    first = {'served':0,'pool':0,'denominator':len(objs)}
    for rr in objs.values():
        vis=[r['frame'] for r in rr if r['visible'] and r['valid']]
        if not vis: continue
        for name,field in [('served','iou'),('pool','deployed_best_iou')]:
            hit=[r['frame'] for r in rr if r['visible'] and r['valid'] and (r[field] or 0)>=.3]
            first[name]+=bool(hit and min(hit)==min(vis))
    wrongframes=[r for k,rr in objs.items() if cats[k]=='wrong' for r in rr]
    pricedwrong=[r for r in wrongframes if r['frame']==r['pricing_best_frame']]
    heater=[rid for rid,kk in rowkeys.items() if any(k[1]=='heater' and cats[k] in ('wrong','refused') for k in kk)]
    result=dict(all=summary(list(base)), groups={k:summary(v) for k,v in groups.items()}, operand_categories=dict(C.Counter(cats.values())), proposal_partition={'no_pool':summary(no_pool),'has_pool':summary(has_pool)}, datasets={k:summary(v) for k,v in ds.items()}, heater_wrong=summary(heater), pool_recall=sum(recalls.values()), visible=fr(visible), above_one_percent=fr(large), first=first, wrong_omitted=sum(r['failure_kind']=='omitted_selection' for r in wrongframes), wrong_priced_kinds=dict(C.Counter(r['failure_kind'] for r in pricedwrong)), false_presence=sum(r['valid'] and not r['visible'] and r['served_area']>0 for r in records), attribution={k:v for k,v in attrib.items() if k!='input_sha256'}, category_definition='refused > wrong (max IoU < .1 and max precision < .2) > weak (max IoU < .5) > poor priced frame > good')
    save('NUMBERS.json', result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('input_sha256','attribution')},indent=2))

def data():
    p=js(K/'pinned_train.json'); manifest=js(B/'k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json')
    root=pathlib.Path('/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS')
    train=lines(root/'K1_CAPTURES_TRAIN_239.txt'); held=lines(root/'K1_CAPTURES_HELDOUT_57.txt'); ids=lines(root/'K1_TRAIN_1037.txt')
    heldids=lines(root/'K1_HELDOUT_216.txt'); caps={c['canonical']:c for c in p['captures']}
    mc={c['canonical']:c for c in manifest['captures']}
    room_split=js(F/'teacher/auth/ROOM_SPLIT.json')
    result=dict(captures=len(caps),datasets=dict(C.Counter(n.split('/')[0] for n in caps)),train_list_equal=set(caps)==train,held_capture_overlap=sorted(set(caps)&held),held_row_overlap=sorted(ids&heldids),held_room_overlap=sorted({c['room'] for c in caps.values()} & {mc[n]['room'] for n in held}),nontrain=[n for n,c in caps.items() if c['k1_split']!='train' or mc[n]['k1_split']!='train'],raster_missing=[],frame_missing=[],anchor_mismatch=[],structural={'tested':0,'passes':0,'failures':[]},samples=[],split_metadata_overlaps={k:sorted(set(caps)&set(v)) for k,v in room_split.items() if isinstance(v,list)},R0_dev_capture_list='MISSING: no authoritative R0-dev capture list is supplied in in/, K1_ROWSETS, or named split evidence')
    seen=set()
    for n,c in caps.items():
        for f in c['dense_frames']:
            if not pathlib.Path(f['path']).is_file():result['frame_missing'].append(f['path'])
        if any(c['dense_frames'][slot]['sha256']!=c['model_row']['student_input']['frames'][i]['sha256'] for i,slot in enumerate(c['anchor_slots'])):result['anchor_mismatch'].append(n)
        path=pathlib.Path(c['gt']['path'])
        if not path.is_file(): result['raster_missing'].append(str(path));continue
        raw=read(path)
        with np.load(io.BytesIO(raw), allow_pickle=False) as z:
            labels=[str(x) for x in z['labels']]; inst=[int(x) for x in z['ids']]
        byid=dict(zip(inst,labels)); counts=C.Counter(labels)
        for row in c['rows']:
            if row['id'] not in ids:continue
            for name in row['operands']:
                iid=row['gt_instances'][name]; result['structural']['tested']+=1
                ok=byid.get(iid)==name and counts[name]==1 and c['gt_name_ids'][name]==[iid]
                result['structural']['passes']+=ok
                if not ok:result['structural']['failures'].append([n,name,iid,byid.get(iid),counts[name]])
        ds=n.split('/')[0]
        if ds not in seen:
            seen.add(ds);f=c['dense_frames'][0];content=read(f['path'])
            result['samples'].append(dict(capture=n,raster=str(path),raster_hash_matches=PINS[str(path)]==c['gt']['sha256'],frame=f['path'],frame_hash_matches=hashlib.sha256(content).hexdigest()==f['sha256']))
    result['dense_frames']=sum(len(c['dense_frames']) for c in caps.values())
    result['anchors']=sum(len(c['anchor_slots']) for c in caps.values())
    save('DATA_AUDIT.json',result); print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},indent=2))

def cache():
    records=js(F/'out/MASKFAIL.json')['records'];read(K/'predicted.py')
    selected=[r for r in records if r['visible'] and r['valid'] and r['deployed_candidate_count']==0]
    bycap=C.defaultdict(list)
    for r in selected:bycap[r['capture']].append(r)
    counts=C.Counter(); examples=[]; unique=C.Counter(); seen=set()
    for cap,rr in sorted(bycap.items()):
        path=pathlib.Path('/scratch/jjyeung/k1/run_convert_2')/digest(cap)/'candidates.json'; d=js(path)
        for r in rr:
            rec=d['frames'][str(r['frame']-1)]['phrases'].get(r['object'])
            if rec is None:counts['record_missing']+=1;continue
            pres=float(rec['presence']); scores=rec['all_instance_scores']; hi=max(scores,default=0)
            raw=[e for e in rec['instances'] if e.get('source_prompt',r['object'])==r['object']]
            kept=[e for e in raw if float(e['score'])*float(e.get('source_presence',pres))>=.05]
            flags={'n':True,'conditional_ge_half':hi>=.5,'conditional_ge_half_presence_lt_point2':hi>=.5 and pres<.2,'presence_lt_point05':pres<.05,'conditional_ge_half_joint_veto':any(s>=.5 and s*pres<.05 for s in scores),'max_conditional_joint_veto':hi>=.5 and hi*pres<.05,'raw_kept_mismatch':bool(kept)}
            for k,v in flags.items():counts[k]+=v
            key=(cap,r['object'],r['frame'])
            if key not in seen:
                seen.add(key)
                for k,v in flags.items():unique[k]+=v
            if len(examples)<3:examples.append(dict(capture=cap,name=r['object'],frame=r['frame'],presence=pres,max_conditional=hi,cache=str(path)))
    result=dict(row_weighted=dict(counts),unique_frames=dict(unique),examples=examples,meaning='Vetoed query masks are absent; conditional confidence does not establish target overlap.')
    save('CACHE_AUDIT.json',result); print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},indent=2))

def details():
    records=js(F/'out/MASKFAIL.json')['records']
    objs=C.defaultdict(list)
    for r in records:objs[(r['row'],r['object'])].append(r)
    first={}
    for share in [0,.002,.01]:
        out={'n':0,'served':0,'pool':0}
        for rr in objs.values():
            vis=[r['frame'] for r in rr if r['valid'] and r['visible'] and r['share']>=share]
            if not vis:continue
            out['n']+=1
            for name,field in [('served','iou'),('pool','deployed_best_iou')]:
                hit=[r['frame'] for r in rr if r['visible'] and r['valid'] and (r[field] or 0)>=.3]
                out[name]+=bool(hit and min(hit)==min(vis))
        first[str(share)]=out
    # Extract only the cache conversion function; do not import or execute the reader.
    import ast
    path=B/'b04host3/tree_rebuild/work/base/tree_b01ce449/student_pilot/routed_features.py'
    tree=ast.parse(read(path).decode()); node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='cache_for')
    ns={'rle':lambda m:m};exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),ns)
    probe=ns['cache_for']('chair',[[dict(mask='maskA',score=.9,presence=.1),dict(mask='maskB',score=.8,presence=.9)]])
    sourcepins=[K/'predicted.py',K/'train_pricing.py',K/'summarize_train.py',K/'serving_reference.py',K/'inputs/KIT_SPEC_box_ladder_k1_v2.md', B/'k1_ops3/kc/k1_build/work/kit_k1a/native_kit/vendor_sam/vendor/sam3_tower.py',B/'k1_ops3/kc/k1_build/work/kit_k1a/native_kit/vendor_sam/variantlib.py']
    for path in sourcepins:read(path)
    checks={}
    for s in ['/scratch/jjyeung/n13_outage/sam3_ckpt','/scratch/jjyeung/qwen_port_1110/sam3_ckpt']:
        p=pathlib.Path(s);checks[s]=dict(exists=p.exists(),entries=sorted(q.name for q in p.iterdir()) if p.is_dir() else None)
    checks['optional_track']={'path':str(B/'sb_kobj4/out/object_route/K1_TRACK.json'),'exists':(B/'sb_kobj4/out/object_route/K1_TRACK.json').is_file()}
    heaterwrong=[]
    items=[json.loads(x) for x in read(K/'out/box_ladder/PER_ITEM.jsonl').splitlines()]
    aa={r['row_id']:r for r in items if r['arm']=='A0_deployed'};gg={r['row_id']:r for r in items if r['arm']=='A2_gt_masks'}
    for (rid,name),rr in objs.items():
        if name=='heater' and rr[0]['selected_candidate_id'] is not None and max(r['iou'] or 0 for r in rr)<.1 and max(r['precision'] for r in rr)<.2:heaterwrong.append(rid)
    h=dict(rows=len(heaterwrong),A0=sum(mra(aa[i]) for i in heaterwrong)/len(heaterwrong),A2=sum(mra(gg[i]) for i in heaterwrong)/len(heaterwrong),contribution=sum(mra(gg[i])-mra(aa[i]) for i in heaterwrong)/len(aa))
    rates={k:dict(v,served_percent=100*v['served']/v['n'],pool_percent=100*v['pool']/v['n']) for k,v in first.items()}
    for p in sorted((HERE/'in').glob('*.md')):read(p)
    result=dict(first_seen_variants=rates,heater_wrong_only=h,mixed_presence_probe=probe,path_checks=checks,checks_scope='Path existence and direct directory entries; checkpoint bytes unavailable, no checkpoint content hash claimed.',ranking_half_transfer_ReVSI_per_GPUh={'retention':[1/14/.6,3/14/.6],'carry':[1/14/2,2.5/14/2],'finetune':[2/14/7,6/14/7]},ranking_scope='Arithmetic on declared scenarios and caps only; neither gains nor GPU throughput are measured in the supplied design/specs.')
    save('DETAILS.json',result);print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},indent=2))

def aliases():
    from scipy.ndimage import zoom
    p=js(K/'pinned_train.json'); records=js(F/'out/MASKFAIL.json')['records'];rowids=lines('/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS/K1_TRAIN_1037.txt')
    bycap=C.defaultdict(dict)
    for r in records:bycap[r['capture']][(r['object'],r['frame'])]=r
    results={}; counts=C.Counter(); gained=C.Counter();lost=[]; aliasnames=set()
    for c in p['captures']:
        cap=c['canonical']
        if cap not in bycap:continue
        cache=js(pathlib.Path('/scratch/jjyeung/k1/run_convert_2')/digest(cap)/'candidates.json')
        with np.load(io.BytesIO(read(c['gt']['path'])),allow_pickle=False) as z:
            raster=z['inst'] if 'inst' in z else z['instances']; valid=z['valid']
        if raster.shape[1:]!=(240,320):raster=np.stack([zoom(x,(240/x.shape[0],320/x.shape[1]),order=0,prefilter=False) for x in raster])
        names=sorted({name for row in c['rows'] if row['id'] in rowids for name in row['operands']})
        for name in names:
            iid=c['gt_name_ids'][name][0];hit30=False;hitall=False;raw100=False
            rawhit=any(bycap[cap][(name,f)]['deployed_best_iou']>=.5 and bycap[cap][(name,f)]['visible'] and bycap[cap][(name,f)]['valid'] for f in range(1,33))
            for slot in range(32):
                rec=cache['frames'][str(slot)]['phrases'].get(name)
                if rec is None:continue
                pres=float(rec['presence']);hi=max(rec['all_instance_scores'],default=0)
                r=bycap[cap][(name,slot+1)]
                if r['valid'] and r['visible'] and r['deployed_candidate_count']==0:
                    # Count after row replication below.
                    pass
                entries=sorted([e for e in rec['instances'] if float(e['score'])*float(e.get('source_presence',pres))>=.05], key=lambda e:-float(e['score']))
                if any(e.get('source_prompt',name)!=name for e in entries):aliasnames.add(name)
                if not valid[slot] or not np.any(raster[slot]==iid):continue
                target=raster[slot]==iid
                rawrank=0
                for rank,e in enumerate(entries):
                    israw=e.get('source_prompt',name)==name
                    if israw:rawrank+=1
                    if hitall and (hit30 or rank>=30) and (raw100 or not israw or rawrank>100):continue
                    rle=e['mask'];h,w=rle['size'];cs=np.asarray(rle['counts'],np.int64)
                    mask=np.repeat(np.arange(len(cs))%2==1,cs).reshape((h,w),order='F')
                    if mask.shape!=(480,640):mask=zoom(mask,(480/h,640/w),order=0,prefilter=False)
                    mask=mask[::2,::2];union=np.count_nonzero(mask|target)
                    if union and np.count_nonzero(mask&target)/union>=.5:
                        hitall=True
                        if rank<30:hit30=True
                        if israw and rawrank<=100:raw100=True
            results[(cap,name)]=(rawhit,hit30,hitall,raw100)
        for row in c['rows']:
            if row['id'] not in rowids:continue
            for name in row['operands']:
                raw,alias30,aliasall,raw100=results[(cap,name)]
                counts.update({'operands':1,'raw30':int(raw),'alias30':int(alias30),'alias_all':int(aliasall),'raw100':int(raw100)})
                if alias30 and not raw:gained[name]+=1
                if raw and not alias30:lost.append([row['id'],name])
                for slot in range(32):
                    r=bycap[cap][(name,slot+1)]
                    if not(r['valid'] and r['visible'] and r['deployed_candidate_count']==0):continue
                    rec=cache['frames'][str(slot)]['phrases'].get(name)
                    if rec and float(rec['presence'])<.05 and max(rec['all_instance_scores'],default=0)>=.5:counts['conditional_half_and_presence_lt05']+=1
        print(cap,flush=True) if len(results)%100==0 else None
    result=dict(counts=dict(counts),gained_by_name=dict(gained),lost=lost,names_with_alias_instances=sorted(aliasnames),method='Exact cache retention; nearest-neighbor resize to 480x640 then stride 2; IoU >= .5 on valid visible anchors; row operands retain repeated weight.')
    save('ALIAS_AUDIT.json',result);print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},indent=2))

if __name__=='__main__':
    if sys.argv[1]=='all':
        for mode in ['numbers','data','cache','details','aliases']:
            PINS.clear();print('AUDIT '+mode,flush=True);globals()[mode]()
    else:globals()[sys.argv[1]]()
