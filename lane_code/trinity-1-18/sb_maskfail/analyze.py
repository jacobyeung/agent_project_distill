"""Training-only mask audit; use bash run.sh analyze.py measure|price|report."""
import collections, gzip, hashlib, io, json, pickle, sys, time
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
BOX=Path('/scratch/jjyeung/orch_n30/sb_kbox4')
sys.path.insert(0,str(BOX))
import train_pricing as T
from box_math import paired_bootstrap
from summarize_train import contrast as ladder_contrast
T.torch.set_num_threads(8)
OUT=HERE/'out'; WORK=HERE/'tmp'; PROV=OUT/'provenance'
for p in [OUT,WORK,PROV]:p.mkdir(exist_ok=True)
MAN=Path('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json')
IDS=Path('/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS/K1_TRAIN_1037.txt')
LAB=Path('/scratch/jjyeung/n30_mirror/gt_audit/gt_audit/work/k1audit/K1_LABELS_CORRECTED.jsonl')
TAR=Path('/scratch/jjyeung/n30_mirror/b05_owngrd/B05_K1_TEACHER_LABELS.tar')
KINDS=['no_proposal','omitted_selection','wrong_instance','wrong_class','partial_mask','merged_instances','other_mask_error','correct']
THRESH=[.3,.5,.7]

def paired_bootstrap(left,right):
    result=ladder_contrast(left,right)
    return dict(result,n=result['rows'],status='OK')

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def write(p,d):p.write_text(json.dumps(T.clean(d),separators=(',',':'),allow_nan=False)+'\n')
def readj(p):return json.loads(T.read(p))
def status(s):(HERE/'STATUS.md').write_text(s+'\n')
def stub(c):return c['canonical'].replace('/','__')

def setup():
    ids=set(T.read(IDS).decode().splitlines());assert len(ids)==1037
    manifest=readj(MAN)
    pin=readj(BOX/'pinned_train.json')
    caps=[c for c in pin['captures'] if any(r['id'] in ids for r in c['rows'])]
    original={c['canonical']:c for c in manifest['captures']}
    for c in caps:
        assert c['k1_split']=='train'
        assert c['anchor_indices']==original[c['canonical']]['anchor_indices']
        for row in c['rows']:
            if row['id'] in ids:
                src=next(r for r in original[c['canonical']]['rows'] if r['id']==row['id'])
                assert src['operands']==row['operands'] and src['gt_instances']==row['gt_instances']
    labels={r['id']:r for line in T.read(LAB).decode().splitlines() if (r:=json.loads(line))['id'] in ids}
    assert set(labels)==ids and all(r['split']=='train' for r in labels.values())
    # Stream the published rows, retaining only A0/A2 training records.
    old={}
    per=BOX/'out/box_ladder/PER_ITEM.jsonl';T.PINS[str(per)]=sha(per)
    with per.open() as f:
        for line in f:
            r=json.loads(line)
            if r['row_id'] in ids and r['arm'] in ['A0_deployed','A2_gt_masks']:
                old[(r['arm'],r['row_id'])]=r
    assert len(old)==2074
    T.PINS[str(TAR)]=sha(TAR)
    for p in [HERE/'RULES.md',HERE/'run.sh',HERE/'analyze.py',BOX/'run.sh']:
        T.read(p)
    return caps,ids,labels,old

def codepins():
    for m in list(sys.modules.values()):
        p=getattr(m,'__file__',None)
        if p and p.endswith('.py') and p.startswith('/scratch/jjyeung/') and '/envs/' not in p:
            if str(p) not in T.PINS:T.read(p)

def decode(r):
    return np.repeat(np.arange(len(r['counts']))%2==1,r['counts']).reshape(r['size'],order='F')

def metrics(m,target):
    area=int(m.sum());inter=int(np.count_nonzero(m&target));union=area+int(target.sum())-inter
    return (inter/union if union else None),inter,area

def classify(r,t):
    if not r['valid']:return 'MISSING'
    if not r['visible'] and not r['served_area']:return 'absent_both'
    if r['visible'] and r['iou']>=t:return 'correct'
    if r['visible'] and r['deployed_best_iou']==0:return 'no_proposal'
    if r['visible'] and not r['served_area']:return 'omitted_selection'
    if r['merged']:return 'merged_instances'
    if r['dominant_fraction']>=.5 and r['dominant_id']!=r['instance']:
        if r['dominant_class'] is not None and r['class'] is not None:
            return 'wrong_instance' if r['dominant_class']==r['class'] else 'wrong_class'
    if r['visible'] and r['precision']>=.8:return 'partial_mask'
    return 'other_mask_error'

def combine(name,base,gt,frames):
    d=T.empty(name);d['boxes']={}
    for f in range(1,33):
        src=gt if f in frames else base;k=str(f)
        if f in src['visible']:d['visible'].append(f);d['areas'][k]=src['areas'][k]
        if f in src['frames']:d['frames'].append(f);d['points'][k]=src['points'][k]
    if d['frames']:d.update(seen=True,best=min(d['frames'],key=lambda f:(-d['areas'][str(f)],f)))
    return d

def price_rows(c,rows,geo,objects,labels,arm):
    result=[]
    for row in rows:
        try:pred,refusal,_,_=T.pricing.session_distance(row,geo,objects,T.G,'best1')
        except (ValueError,KeyError,IndexError) as exc:pred=None;refusal=type(exc).__name__+':'+str(exc)
        result.append(dict(arm=arm,row_id=row['id'],room=c['room'],capture=c['canonical'],dataset=c['canonical'].split('/')[0],prediction=pred,label=labels[row['id']]['corrected'],refusal_code=refusal))
    return result

def measure(limit=None):
    caps,ids,labels,old=setup();headpath=T.R.SEL/'work/run_iso'
    for ext in ['json','safetensors']:T.read(headpath/f'selector_head.{ext}')
    head,_=T.R.load_head(headpath);codepins();common=dict(T.PINS)
    for ci,c in enumerate(caps[:limit]):
        dest=WORK/(stub(c)+'.pkl');rp=WORK/(stub(c)+'.json.gz')
        if dest.exists() and rp.exists():continue
        started=time.monotonic();T.PINS.clear();T.PINS.update(common)
        rows=[r for r in c['rows'] if r['id'] in ids]
        geo,cache,meta,tower,receipt=T.R.geometry(c)
        gt,rawgt=T.R.gt_arrays(c);inst=gt['instances'];raster=rawgt.get('inst',rawgt.get('instances'))
        classes={int(i):str(n) for i,n in zip(rawgt['ids'],rawgt['labels'])}
        valid=rawgt['valid'].astype(bool)
        ref=readj_gz(T.R.TABLES/(stub(c)+'.json.gz'))
        teacherpath=HERE/'teacher/teacher_k1_full/teacher_k1'/stub(c)/'teacher.json.gz'
        teacher=readj_gz(teacherpath) if teacherpath.exists() else None
        if teacher is not None:
            assert teacher['frame_indices']==c['anchor_indices']
            assert teacher['frame_sha256']==[f['sha256'] for f in c['model_row']['student_input']['frames']]
        objects=T.Objects(c,cache,geo,head,gt,ref)
        records=[];bases={};gts={};framekinds={};selection={}
        names=sorted({n for row in rows for n in row['operands']})
        for name in names:
            iid=c['gt_name_ids'][name];assert len(iid)==1;iid=int(iid[0])
            data=objects.load(name);choice=data['A0']
            selected={} if choice<0 else {p.frame:p for p in data['tracks'][choice].proposals}
            served=np.zeros((32,240,320),bool)
            for f,p in selected.items():served[f-1]=data['raw'][f-1][p.index]['mask'][::2,::2]
            bases[name]=T.lifted(name,served,geo)
            gts[name]=T.lifted(name,(raster==iid)&valid[:,None,None],geo)
            selection[name]=None if choice<0 else data['accepted'][choice]['candidate_id']
            objrecords=[]
            for f in range(32):
                target=inst[f]==iid;m=served[f];iou,inter,area=metrics(m,target)
                vis=bool(target.any());share=float(np.mean(raster[f]==iid))
                deployed=[metrics(p['mask'][::2,::2],target) for p in data['raw'][f]]
                teach=[]
                if teacher is not None:
                    for p in teacher['frames'][str(f)]['phrases'].get(name,{}).get('instances',[]):
                        tm=T.F.resize(decode(p['mask']),T.F.SHAPE)[::2,::2]
                        teach.append(metrics(tm,target))
                allids,counts=np.unique(inst[f][m],return_counts=True)
                annotated=[(int(k),int(n)) for k,n in zip(allids,counts) if int(k) in classes]
                dominant=max(annotated,key=lambda v:(v[1],-v[0])) if annotated else (None,0)
                covered=[k for k,n in annotated if area and n/area>=.1 and n/int(np.count_nonzero(inst[f]==k))>=.1]
                r=dict(capture=c['canonical'],dataset=c['canonical'].split('/')[0],object=name,instance=iid,
                    frame=f+1,source_frame=c['anchor_indices'][f],**{'class':classes.get(iid)},share=share,
                    share_bin=('<0.5%' if share<.005 else '0.5-1%' if share<.01 else '1-5%' if share<.05 else '5-20%' if share<=.2 else '>20%'),
                    iou=iou if valid[f] else None,valid=bool(valid[f]),visible=vis,served_area=area,
                    precision=inter/area if area else 0.,merged=len(covered)>=2,merged_ids=covered,
                    dominant_id=dominant[0],dominant_class=classes.get(dominant[0]),dominant_fraction=dominant[1]/area if area else 0.,
                    any_overlap=any(v[1]>0 for v in deployed+teach),deployed_candidate_count=len(deployed),teacher_candidate_count=len(teach),
                    deployed_best_iou=max((v[0] or 0. for v in deployed),default=0.),
                    teacher_best_iou=max((v[0] or 0. for v in teach),default=0.) if teacher is not None else None,
                    teacher_status='OK' if teacher is not None else 'MISSING: '+str(teacherpath),selected_candidate_id=selection[name],
                    selected_proposal_index=int(selected[f+1].index) if f+1 in selected else None)
                r['failure_kinds']={str(t):classify(r,t) for t in THRESH};r['failure_kind']=r['failure_kinds']['0.5']
                objrecords.append(r)
            framekinds[name]={str(t):[r['failure_kinds'][str(t)] for r in objrecords] for t in THRESH}
            for row in rows:
                if name in row['operands']:
                    assert row['gt_instances'][name]==iid
                    records.extend(dict(r,row=row['id']) for r in objrecords)
            # Retained masks can dominate RAM on captures with many phrases.
            objects.data.pop(name);objects.stage.raw.pop(name)
        # The unchanged pricing path must reproduce both endpoints for every row.
        parity=[]
        for arm,values in [('A0_deployed',bases),('A2_gt_masks',gts)]:
            priced=price_rows(c,rows,geo,values,labels,arm)
            for r in priced:
                expected=old[(arm,r['row_id'])]
                assert r['prediction']==expected['prediction'],(c['canonical'],arm,r['row_id'],r['prediction'],expected['prediction'])
                assert r['label']==expected['label']
                parity.append(r)
        codepins();pmap=dict(T.PINS)
        pp=PROV/(stub(c)+'.json');write(pp,dict(capture=c['canonical'],input_sha256=pmap,teacher_contract=teacher['contract'] if teacher else 'MISSING'))
        for r in records:r['input_sha256']={str(pp):sha(pp)}
        with gzip.open(rp,'wt') as f:json.dump(dict(records=records,input_sha256=pmap),f,separators=(',',':'))
        contract=geo.contract
        arrays=dict(K=contract.K,canvas_to_source=contract.canvas_to_source,camera_to_world=contract.camera_to_world,
            scale=contract.scale,depth_grid=tower['depth_grid'],grid_uv=tower['grid_uv'],anchor_frame_indices=c['anchor_indices'])
        with dest.open('wb') as f:pickle.dump(dict(capture=c,rows=rows,labels=labels,geometry=arrays,base=bases,gt=gts,kinds=framekinds,parity=parity,input_sha256=pmap),f,protocol=5)
        print(json.dumps(dict(stage='measure',done=ci+1,total=len(caps),capture=c['canonical'],records=len(records),seconds=round(time.monotonic()-started,1))),flush=True)
        status(f'Mask comparison: {ci+1}/{len(caps)} training captures completed; A0 and A2 predictions match published rows exactly for completed captures. Rules are fixed in RULES.md. Attribution is pending.')
    if limit is None:aggregate(caps)

def readj_gz(p):return json.loads(gzip.decompress(T.read(p)))

def dist(values):
    x=np.asarray([v for v in values if v is not None],float)
    return dict(n=len(x),mean=float(x.mean()) if len(x) else None,quantiles=dict(zip(['min','p10','p25','p50','p75','p90','max'],np.quantile(x,[0,.1,.25,.5,.75,.9,1]).tolist())) if len(x) else {},rates={str(t):float(np.mean(x>=t)) if len(x) else None for t in THRESH})

def stats(records):
    rows=[r for r in records if r['valid'] and r['visible']]
    best={}
    for r in rows:
        key=(r['capture'],r['row'],r['object']);best[key]=max(best.get(key,0),r['iou'])
    unique={}
    for r in rows:
        key=(r['capture'],r['instance'],r['frame']);unique[key]=r['iou']
    ubest={}
    for (c,i,f),v in unique.items():ubest[(c,i)]=max(ubest.get((c,i),0),v)
    pricingbest={key:0. for key in best}
    for r in records:
        key=(r['capture'],r['row'],r['object'])
        if key in pricingbest and r['frame']==r.get('pricing_best_frame'):
            pricingbest[key]=r['iou'] if r['valid'] else None
    failure={str(t):dict(collections.Counter(r['failure_kinds'][str(t)] for r in rows)) for t in THRESH}
    availability={}
    for t in THRESH:
        wrong=[r for r in rows if r['iou']<t]
        availability[str(t)]=dict(wrong=len(wrong),deployed_correct=sum(r['deployed_best_iou']>=t for r in wrong),teacher_correct=sum((r['teacher_best_iou'] or 0)>=t for r in wrong),
            teacher_only_correct=sum(r['deployed_best_iou']<t and (r['teacher_best_iou'] or 0)>=t for r in wrong),neither_correct=sum(r['deployed_best_iou']<t and r['teacher_best_iou'] is not None and r['teacher_best_iou']<t for r in wrong),teacher_missing=sum(r['teacher_best_iou'] is None for r in wrong),unknown_teacher_without_deployed=sum(r['deployed_best_iou']<t and r['teacher_best_iou'] is None for r in wrong))
    return dict(total_records=len(records),visible_valid=len(rows),absent=sum(r['valid'] and not r['visible'] for r in records),invalid=sum(not r['valid'] for r in records),
        object_frame=dist(r['iou'] for r in rows),all_evaluable_object_frame=dist(r['iou'] for r in records if r['valid']),object_best_frame=dist(best.values()),pricing_best_frame_iou=dist(pricingbest.values()),unique_object_frame=dist(unique.values()),unique_object_best_frame=dist(ubest.values()),failure=failure,availability=availability,
        all_frame_failure={str(t):dict(collections.Counter(r['failure_kinds'][str(t)] for r in records)) for t in THRESH})

def aggregate(caps):
    records=[];pins={}
    for c in caps:
        p=WORK/(stub(c)+'.json.gz');d=readj_gz(p);records.extend(d['records']);pins.update(d['input_sha256']);pins[str(p)]=sha(p)
    assert len(records)==1037*2*32
    write(OUT/'MASKFAIL.json',dict(schema='sb_maskfail_v1',input_sha256=pins,records=records))
    summary=dict(overall=stats(records),by_dataset={},by_share={},by_class={},input_sha256={str(OUT/'MASKFAIL.json'):sha(OUT/'MASKFAIL.json'),str(HERE/'analyze.py'):sha(HERE/'analyze.py')})
    for ds in sorted({r['dataset'] for r in records}):summary['by_dataset'][ds]=stats([r for r in records if r['dataset']==ds])
    for share in ['<0.5%','0.5-1%','1-5%','5-20%','>20%']:summary['by_share'][share]=stats([r for r in records if r['share_bin']==share])
    classes=collections.defaultdict(set)
    for r in records:classes[r['class']].add(r['row'])
    for cls in sorted(classes,key=lambda k:(-len(classes[k]),str(k)))[:30]:
        summary['by_class'][cls]=dict(rows=len(classes[cls]),**stats([r for r in records if r['class']==cls]))
    write(OUT/'SPLITS.json',summary)
    first_table(summary)
    status('Mask comparisons and failure splits are complete for all 1,037 training rows (66,368 operand-frame records). FIRST_TABLE.md is ready; all A0/A2 endpoint predictions reproduce exactly. Failure attribution is pending.')

def first_table(s,attrib=None):
    count=s['overall']['failure']['0.5'];n=s['overall']['visible_valid']
    lines=['| Failure kind | Visible operand-frames | % | All intervention frames | Independent gain (points) | Cumulative gain (points) |','|---|---:|---:|---:|---:|---:|']
    for k in KINDS:
        a=attrib['thresholds']['0.5']['independent'][k] if attrib else None
        b=attrib['thresholds']['0.5']['cumulative'][k] if attrib else None
        def fmt(x):return f"{x['estimate']:+.4f} [{x['ci95'][0]:+.4f}, {x['ci95'][1]:+.4f}]" if x else 'PENDING'
        alln=s['overall']['all_frame_failure']['0.5'].get(k,0)
        lines.append(f'| {k} | {count.get(k,0)} | {100*count.get(k,0)/n:.2f} | {alln} | {fmt(a)} | {fmt(b)} |')
    lines+=['',f'Primary IoU threshold: 0.5. Counts cover {n:,} visible, valid operand-frames; repeated row operands retain row weight. Rules: RULES.md. Independent effects overlap. Cumulative order follows table order; correct-mask replacement closes the residual to A2.']
    (OUT/'FIRST_TABLE.md').write_text('\n'.join(lines)+'\n')

def price():
    caps,ids,labels,old=setup()
    codepins()
    allrows=[];pins=dict(T.PINS)
    for ci,c in enumerate(caps):
        dest=WORK/(stub(c)+'.prices.json')
        if dest.exists():
            d=readj(dest);allrows.extend(d['rows']);pins.update(d['input_sha256']);continue
        p=WORK/(stub(c)+'.pkl')
        with p.open('rb') as f:d=pickle.load(f)
        geo=T.R.from_arrays(**d['geometry']);result=[];object_cache={};row_cache={}
        for t in THRESH:
            for mode in ['independent','cumulative']:
                active=set()
                for kind in KINDS:
                    active=(active|{kind}) if mode=='cumulative' else {kind}
                    objs={}
                    for n in d['base']:
                        frames=tuple(f+1 for f,k in enumerate(d['kinds'][n][str(t)]) if k in active)
                        key=(n,frames)
                        if key not in object_cache:object_cache[key]=combine(n,d['base'][n],d['gt'][n],set(frames))
                        objs[n]=object_cache[key]
                    arm=f'{t}/{mode}/{kind}'
                    for row in d['rows']:
                        key=(row['id'],tuple(id(objs[n]) for n in row['operands']))
                        if key not in row_cache:row_cache[key]=price_rows(c,[row],geo,objs,labels,arm)[0]
                        result.append(dict(row_cache[key],arm=arm))
        for row in result:
            if row['arm'].endswith('/cumulative/correct'):
                assert row['prediction']==old[('A2_gt_masks',row['row_id'])]['prediction'],('closure',c['canonical'],row)
        cpins=dict(d['input_sha256']);cpins[str(p)]=sha(p);cpins[str(HERE/'analyze.py')]=sha(HERE/'analyze.py')
        write(dest,dict(rows=result,input_sha256=cpins));pins.update(cpins);allrows.extend(result)
        print(json.dumps(dict(stage='price',done=ci+1,total=len(caps),capture=c['canonical'])),flush=True)
        status(f'Attribution pricing: {ci+1}/{len(caps)} captures complete at IoU thresholds 0.3, 0.5, 0.7. All cumulative endpoints reproduce A2. FIRST_TABLE.md contains completed failure counts.')
    base=[old[('A0_deployed',i)] for i in sorted(ids)];gt=[old[('A2_gt_masks',i)] for i in sorted(ids)]
    output=dict(input_sha256=pins,baseline=100*float(np.mean([T.M.mra(r['prediction'],r['label']) for r in base])),raster=100*float(np.mean([T.M.mra(r['prediction'],r['label']) for r in gt])),gap=paired_bootstrap(gt,base),thresholds={})
    for t in THRESH:
        output['thresholds'][str(t)]={}
        for mode in ['independent','cumulative']:
            output['thresholds'][str(t)][mode]={};prev=base
            for kind in KINDS:
                arm=f'{t}/{mode}/{kind}';rows=[r for r in allrows if r['arm']==arm];assert len(rows)==1037
                b=paired_bootstrap(rows,base);b.update(refusals=sum(r['prediction'] is None for r in rows),mra=output['baseline']+b['estimate'],gap_fraction=b['estimate']/output['gap']['estimate'])
                if mode=='cumulative':b['increment']=paired_bootstrap(rows,prev)
                output['thresholds'][str(t)][mode][kind]=b;prev=rows
    write(OUT/'ATTRIBUTION.json',output)
    write(OUT/'COUNTERFACTUAL_ROWS.json',dict(rows=allrows,input_sha256=pins))
    first_table(readj(OUT/'SPLITS.json'),output)
    status('All counterfactuals are priced on 1,037 training rows at three thresholds. Cumulative endpoints reproduce A2 exactly. Paired room bootstrap intervals use 10,000 draws and seed 20261119. Final report and archive validation remain.')

if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='measure':measure(int(sys.argv[2]) if len(sys.argv)>2 else None)
    elif mode=='price':price()
