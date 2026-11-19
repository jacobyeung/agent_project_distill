"""CPU training pricing on frozen rowsets; never loads held-out or GT geometry."""
import gzip,json,re,resource,sys,time
from pathlib import Path
from collections import Counter
import numpy as np
import torch
from scipy import ndimage
import serving_reference as R
from serving_reference import ROOT,OUT,PINS,read,write,clean,F,G,StageOne,cache_detect
import math_v2 as M
import pricing
pricing.fusion_box=M.fusion_box

def setup():
    torch.set_num_threads(8)
    gate=json.loads(read(OUT/'REFERENCE_REBUILD.json'));assert gate['status']=='PASS'
    manifest=json.loads(read(ROOT/'pinned_train.json'));PINS.update(manifest['input_sha256'])
    labels=json.loads(read(ROOT/'train_labels.json'));PINS.update(labels['input_sha256'])
    labels={r['id']:r for r in labels['rows']}
    rowids=set(read(R.ROWSETS/'K1_TRAIN_1037.txt').decode().splitlines())
    tableids=set(read(R.ROWSETS/'K1_TRAIN_TABLES_883.txt').decode().splitlines())
    assert PINS[str(R.ROWSETS/'K1_TRAIN_1037.txt')]=='e7646798c8a1e12ca6291723c5f686473b9954a78d068dcfa65c314be35a98ac'
    assert PINS[str(R.ROWSETS/'K1_TRAIN_TABLES_883.txt')]=='778354e77f117e1d44033e5630c4cd55ba6788e6c4f4a25133a224d34f467191'
    assert all(r['convention'] in ('full','half') for rid,r in labels.items() if rid in rowids)
    caps=[c for c in manifest['captures'] if any(r['id'] in rowids for r in c['rows'])]
    assert len(caps)==209 and all(c['k1_split']=='train' for c in caps)
    folds=M.folds(c['room'] for c in caps);assert len(folds)==192
    boxes=json.loads(read(ROOT/'train_boxes.json'));PINS.update(boxes['input_sha256'])
    audit={}
    for line in read('/scratch/jjyeung/n30_mirror/gt_audit/gt_audit/work/k1audit/K1_ROW_AUDIT.jsonl').decode().splitlines():
        match=re.search(r'"id"\s*:\s*"([^"\\]+)"',line)
        if match and match[1] in rowids:audit[match[1]]=json.loads(line)
    truth={}
    for c in caps:
        for row in c['rows']:
            if row['id'] not in rowids:continue
            for n,bk in zip(row['operands'],audit[row['id']]['box_keys'],strict=True):
                box=boxes['boxes'][bk];assert box['canonical']==c['canonical']
                assert box['box']['instance_id']==row['gt_instances'][n]
                full=max(box['box']['axesLengths'])*(2 if labels[row['id']]['convention']=='half' else 1)
                key=(c['canonical'],row['gt_instances'][n]);assert key not in truth or truth[key]==full
                truth[key]=float(full)
    headpath=R.SEL/'work/run_iso'
    fits=json.loads(read('/scratch/jjyeung/orch_n30/k1_ops3/work/e3gd/out/FITS.json'))
    scales=json.loads(read(R.SEL/'sl118/SCALES_S4.json'))
    assert fits['S4_coefficients']==scales['coefficients']
    assert PINS['/scratch/jjyeung/orch_n30/k1_ops3/work/e3gd/out/FITS.json']=='592c20480643fc8b3d45ba1a8e71cbee2998e7e02b63296f23c82c8393da9834'
    for ext in ['json','safetensors']:read(headpath/f'selector_head.{ext}')
    head,meta=R.load_head(headpath);R.code_pins()
    return caps,labels,rowids,tableids,folds,truth,head

def empty(name):return dict(name=name,seen=False,frames=[],visible=[],areas={},points={},boxes={})

def lifted(name,masks,geo):
    obj=pricing.lift_frames(name,masks,geo,G);obj['boxes']={};return obj

def majority(members,inst):
    count=Counter()
    for p in members:
        mask=ndimage.zoom(p.mask,(inst.shape[1]/p.mask.shape[0],inst.shape[2]/p.mask.shape[1]),order=0,prefilter=False)
        ids,counts=np.unique(inst[p.frame-1][mask],return_counts=True)
        count.update({int(i):int(n) for i,n in zip(ids,counts) if i>=0})
    return min(count,key=lambda i:(-count[i],i)) if count else None

class Objects:
    def __init__(self,c,cache,geo,head,gt,ref,nonull=None):
        self.c,self.geo,self.gt,self.ref=c,geo,gt,ref
        self.stage=StageOne(cache_detect(cache),head,geo,rule='candidates_argmax')
        self.data={};self.nonull=nonull or {}
    def load(self,name):
        if name in self.data:return self.data[name]
        accepted,x=self.stage.features(name)
        raw=self.stage.raw[name]
        props,_=F.candidates.lift(F.cache_for(name,raw),name,self.geo,floor=.3,grids=self.stage.grids,phrase=name)
        byid={p.id:p for p in F.candidates.link(props,name)}
        tracks=[byid[a['candidate_id']] for a in accepted]
        a0=self.stage.select(dict(x=torch.tensor(x,dtype=torch.float64),name=name)) if x else -1
        lab={r['candidate_id']:r for r in self.ref['rows'] if r['name']==name}
        # The reference was built on these exact serving candidates.
        if self.ref.get('same_geometry',True):assert set(lab)=={a['candidate_id'] for a in accepted}
        positive=[i for i,a in enumerate(accepted) if lab.get(a['candidate_id'],{}).get('y')==1] if self.ref.get('same_geometry',True) else []
        oracle=min(positive,key=lambda i:(-len(tracks[i].proposals),i)) if positive else a0
        nid=self.nonull.get(self.c['canonical']+'::'+name)
        a8=next((i for i,a in enumerate(accepted) if a['candidate_id']==nid),-1)
        d=dict(accepted=accepted,tracks=tracks,raw=raw,A0=a0,A1=oracle,A8=a8,merges={},points={},objects={},got={})
        self.data[name]=d;return d
    def get(self,name,kind='A0',tau=None):
        d=self.load(name);choice=d[kind]
        if (kind,tau) in d['got']:return d['got'][(kind,tau)]
        if choice<0:return empty(name),dict(added=0,correct=0,frames_before=[],frames_after=[],n_all=0,n_conf=0,n_operand=0)
        tracks=d['tracks'];seed=tracks[choice].proposals
        if tau is None:
            members=seed;objs=[dict(members={p.frame:p for p in t.proposals}) for t in tracks]
        else:
            if tau not in d['merges']:d['merges'][tau]=M.merge(tracks,tau)
            objs=d['merges'][tau];members=list(next(o for o in objs if choice in o['ids'])['members'].values())
        key=tuple(sorted((p.frame,p.index) for p in members))
        if key not in d['objects']:
            obj=empty(name)
            for p in members:
                pk=(p.frame,p.index)
                if pk not in d['points']:
                    mask=d['raw'][p.frame-1][p.index]['mask'][::2,::2]
                    uv=G.mask_pixels(mask);P,Pc,sp=(np.asarray(v,np.float64) for v in self.geo.lift(p.frame,uv,mode='center'))
                    valid=np.isfinite(P).all(1)&np.isfinite(Pc).all(1)&(Pc[:,2]>0)
                    P,sp=P[valid],sp[valid]
                    d['points'][pk]=(P[sp<=np.median(sp)] if len(P) else P,float(mask.mean()))
                points,area=d['points'][pk];f=p.frame
                obj['visible'].append(f);obj['areas'][str(f)]=area
                if len(points):obj['frames'].append(f);obj['points'][str(f)]=points
            obj['frames'].sort()
            if obj['frames']:obj.update(seen=True,best=min(obj['frames'],key=lambda f:(-obj['areas'][str(f)],f)))
            d['objects'][key]=obj
        sid=majority(seed,self.gt['instances']);before={(p.frame,p.index) for p in seed}
        added=[p for p in members if (p.frame,p.index) not in before]
        iid=self.c['gt_name_ids'][name]
        assert len(iid)==1
        diag=dict(added=len(added),correct=sum(sid is not None and majority([p],self.gt['instances'])==sid for p in added),
            seed_majority=sid,frames_before=sorted(p.frame for p in seed),frames_after=sorted(p.frame for p in members),
            n_all=len(objs),n_conf=sum(any(p.score>=.5 for p in o['members'].values()) for o in objs),
            n_operand=sum(majority(o['members'].values(),self.gt['instances'])==iid[0] for o in objs))
        d['got'][(kind,tau)]=(d['objects'][key],diag)
        return d['got'][(kind,tau)]

def evaluate(c,rows,geo,objects,arm,rule,labels,folds,truth,gt,diags=None,geometry_meta=None):
    out=[]
    for row in rows:
        try:
            cache=gt.setdefault('_distance_cache',{})
            refs=[geo]+[objects[n] for n in row['operands']]
            key=(row['id'],rule,tuple(id(v) for v in refs))
            if key not in cache:
                # Keep references alive so object IDs cannot be reused within this capture.
                cache[key]=(refs,pricing.session_distance(row,geo,objects,G,rule))
            pred,refusal,_,printed=cache[key][1]
        except (ValueError,KeyError,IndexError) as exc:pred=None;refusal=type(exc).__name__+':'+str(exc);printed={}
        diagnostics={}
        for name in row['operands']:
            iid=row['gt_instances'][name];obj=objects[name]
            frames=obj['frames'];firsts=gt.setdefault('_first',{})
            if iid not in firsts:
                mask=(gt['raster']==iid)&gt['valid'][:,None,None]
                eligible=np.flatnonzero(mask.mean(axis=(1,2))>=.002)+1
                firsts[iid]=int(eligible[0]) if len(eligible) else None
            first=firsts[iid]
            box=printed.get(name);longest=float(max(box['lengths'])) if box else None
            full=truth[(c['canonical'],iid)]
            diagnostics[name]=dict(instance=iid,object_id=c['canonical']+'::'+str(iid),gt_longest=full,printed_longest=longest,
                size_ratio=longest/full if longest is not None else None,size_mra=M.mra(longest,full),
                first_gt=first,first_printed=min(frames) if frames else None,frames=frames,
                **((diags or {}).get(name,{})))
        out.append(dict(arm=arm,row_id=row['id'],room=c['room'],capture=c['canonical'],dataset=c['canonical'].split('/')[0],split='train',fold=folds[c['room']],
            prediction=pred,label=labels[row['id']]['corrected'],refusal_code=refusal,member_frames={n:objects[n]['frames'] for n in row['operands']},
            box=printed,diagnostics=diagnostics,reviewed_guard_refused=bool((geometry_meta or {}).get('reviewed_guard_refused'))))
    return out

def one(c,labels,rowids,tableids,folds,truth,head,phase,decision=None,choices=None):
    start=time.monotonic();rows=[r for r in c['rows'] if r['id'] in rowids];trows=[r for r in rows if r['id'] in tableids]
    geo,cache,meta,tower,receipt=R.geometry(c);gt,gt_raw=R.gt_arrays(c)
    gt['raster']=gt_raw.get('inst',gt_raw.get('instances'));gt['valid']=gt_raw['valid'].astype(bool)
    ref=json.loads(gzip.decompress(read(R.TABLES/(c['canonical'].replace('/','__')+'.json.gz'))))
    PINS.update(ref['input_sha256'])
    names=sorted({n for r in rows for n in r['operands']});objects=Objects(c,cache,geo,head,gt,ref,choices)
    results=[];checks=[]
    def pred(arm,kind='A0',tau=None,rule='best1',rowset=rows,geo=geo,objects=objects):
        values={n:objects.get(n,kind,tau) for n in names}
        results.extend(evaluate(c,rowset,geo,{n:v[0] for n,v in values.items()},arm,rule,labels,folds,truth,gt,{n:v[1] for n,v in values.items()},meta))
    if phase in ('base','dry'):
        pred('A0_deployed');pred('A1_oracle_select','A1',rowset=trows)
        for tau in M.TAUS:
            for rule in M.RULES:pred(f'A4_obj_{tau:.2f}_{rule}',tau=tau,rule=rule)
        gtobjects={n:lifted(n,(gt['raster']==c['gt_name_ids'][n][0])&gt['valid'][:,None,None],geo) for n in names}
        for rule in M.RULES:
            results.extend(evaluate(c,rows,geo,gtobjects,'A2_gt_masks' if rule=='best1' else 'A3_gt_fused_'+rule,rule,labels,folds,truth,gt,geometry_meta=meta))
        # Direct copied-reader socket parity and no-merge identity on the dry captures.
        if phase=='dry':
            from e2e_reader.grounding import StageOneSocket,ground_session
            stage=StageOne(cache_detect(cache),head,geo,rule='candidates_argmax')
            s=ground_session(geo,StageOneSocket(stage.propose,stage.select,F.OUTPUT_SHAPE,32))
            base={r['row_id']:r for r in results if r['arm']=='A0_deployed'}
            for row in rows:
                for name in row['operands']:s.execute(f'<ground obj="{name}" mode="box">')
                a,b=row['operands'];response=s.execute(f'<gap a="{a}" b="{b}" rule="box_grid_5cm">')
                m=re.fullmatch(r'distance ([0-9]+\.[0-9]{2}) m',response);p=float(m[1]) if m else None
                checks.append(dict(check='reader_socket',row_id=row['id'],passed=p==base[row['id']]['prediction'],reader=p,kit=base[row['id']]['prediction']))
            pred('no_merge',tau=1.01)
            for r in [r for r in results if r['arm']=='no_merge']:
                checks.append(dict(check='tau_1.01',row_id=r['row_id'],passed=r['prediction']==base[r['row_id']]['prediction'] and r['box']==base[r['row_id']]['box']))
            for n,obj in gtobjects.items():
                for f,p in obj['points'].items():
                    if len(p)<4:continue
                    boxes=[M.fusion_box({int(f):p},int(f),rule,G.min_area_box) for rule in M.RULES]
                    checks.append(dict(check='single_frame',name=n,passed=all(all(np.array_equal(v,b[k]) for k,v in boxes[0].items()) for b in boxes)))
                    break
    if phase=='extras':
        frozen=decision['frozen_variant'];tau,rule=(frozen['tau'],frozen['rule']) if frozen else (None,'best1')
        pred('A8_nonull_best1','A8',rowset=trows)
        if frozen:
            pred('A5_obj_oracle_seed','A1',tau,rule,trows)
            pred('A8_nonull_obj','A8',tau,rule,trows)
        # Report the entire registered rowset, including explicit missing/refused geometry as zero.
        from adapters import reviewed_loader
        from student_pilot.scene_state import FrameMap
        loader,guard,_=reviewed_loader()
        for name in ('da3','pi3x'):
            path=Path('/scratch/jjyeung/orch_n30/geo_k1/geom')/(name+'_native')/(c['canonical'].replace('/','__')+'.npz')
            try:
                read(path)
                with guard.capture('training_challenger',c['canonical']):other=loader(path,FrameMap(tuple(c['anchor_indices'])),'tower_scaled')
                gtobjects={n:lifted(n,(gt['raster']==c['gt_name_ids'][n][0])&gt['valid'][:,None,None],other) for n in names}
                for tag,rr in ([('best1','best1'),('frozen',rule)] if frozen else [('best1','best1')]):results.extend(evaluate(c,rows,other,gtobjects,f'A7_{name}_{tag}',rr,labels,folds,truth,gt))
            except (FileNotFoundError,ValueError) as exc:
                for tag in (['best1','frozen'] if frozen else ['best1']):
                    rr=evaluate(c,rows,geo,{n:empty(n) for n in names},f'A7_{name}_{tag}','best1',labels,folds,truth,gt)
                    for r in rr:r['refusal_code']=('MISSING: ' if isinstance(exc,FileNotFoundError) else 'REFUSED: ')+str(path)+': '+str(exc)
                    results+=rr
    # S4/G1 is a separate treatment. Its candidate labels never seed an oracle arm.
    if phase=='extras' and not decision['frozen_variant']:
        return dict(capture=c['canonical'],phase=phase,items=results,checks=checks,geometry=meta,seconds=time.monotonic()-start,
            peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
            skipped='A5, A8 object, A7 frozen, A9 object: no eligible frozen object variant')
    scales=json.loads(read(R.SEL/'sl118/SCALES_S4.json'))
    scale=scales['captures'][c['canonical']]['S4']
    if scale is not None:
        raw=tower['raw_pose'][tower['anchor_slots']]
        from student_pilot import camera_targets
        rots=np.array([camera_targets.rotation_from_xyzw(p[3:7]).T for p in raw]);gravity=np.mean(-rots[:,:,1],axis=0);gravity/=np.linalg.norm(gravity)
        sgeo=R.from_tower(tower['raw_pose'],tower['anchor_slots'],tower['frame_indices'],tower['depth_grid'],tower['grid_uv'],gravity,scale,receipt['source_hw'])
        sobjs=Objects(c,cache,sgeo,head,gt,dict(rows=[],same_geometry=False))
        if phase in ('base','dry'):pred('A9_s4_today',geo=sgeo,objects=sobjs)
        else:pred('A9_s4_obj',tau=tau,rule=rule,geo=sgeo,objects=sobjs)
    else:
        arm='A9_s4_today' if phase in ('base','dry') else 'A9_s4_obj'
        rr=evaluate(c,rows,geo,{n:empty(n) for n in names},arm,'best1',labels,folds,truth,gt)
        for r in rr:r['refusal_code']='REFUSED: stored S4/G1 scale; '+str(scales['captures'][c['canonical']]['refused'])
        results+=rr
    return dict(capture=c['canonical'],phase=phase,items=results,checks=checks,geometry=meta,seconds=time.monotonic()-start,
        peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)

def main():
    phase=sys.argv[1];assert phase in ('base','extras','dry')
    caps,labels,rowids,tableids,folds,truth,head=setup();common=dict(PINS)
    decision=json.loads(read(OUT/'FREEZE.json')) if phase=='extras' else None
    choices=json.loads(read(OUT/'nonull/TRAIN_OOF.json'))['oof_choices'] if phase=='extras' else None
    if phase!='dry':
        dry=json.loads(read(ROOT/'out/DRYRUN.json'));assert dry['passed'] and dry['status']=='PASS'
    common=dict(PINS)
    if phase=='dry':caps=[c for c in caps if c['canonical'] in ['arkitscenes/41048124','scannetpp/036bce3393']]
    else:
        shard=int(sys.argv[2]) if len(sys.argv)>2 else 0;n=int(sys.argv[3]) if len(sys.argv)>3 else 1
        caps=sorted(caps,key=lambda c:c['canonical'])[shard::n]
    folder=OUT/phase;folder.mkdir(parents=True,exist_ok=True)
    for c in caps:
        path=folder/(c['canonical'].replace('/','__')+'.json')
        if path.exists():
            previous=json.loads(path.read_text())
            deps=[ROOT/n for n in ['train_pricing.py','pricing.py','math_v2.py','serving_reference.py']]
            if all(previous['input_sha256'].get(str(p))==common.get(str(p)) for p in deps):continue
        PINS.clear();PINS.update(common)
        result=one(c,labels,rowids,tableids,folds,truth,head,phase,decision,choices)
        write(path,result)
        print(json.dumps({k:result[k] for k in ['capture','phase','seconds','peak_rss_mib']}),flush=True)
    (ROOT/'STATUS.md').write_text(f'CPU pricing stage {phase} completed its assigned training captures. Per-capture predictions, refusals, object diagnostics and input hashes are in out/box_ladder/{phase}. Held-out and GT-geometry arms were not evaluated.\n')

if __name__=='__main__':main()
