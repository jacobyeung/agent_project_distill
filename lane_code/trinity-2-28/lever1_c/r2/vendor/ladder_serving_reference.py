"""Rebuild training-only labels with the table producer on R1 serving geometry."""
import ast, collections, gzip, hashlib, io, itertools, json, resource, sys, time
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
import torch
from scipy import ndimage
from adapters import ROOT, TREE, READER
from dryrun import read, write, PINS, clean
from predicted import cache_detect

PACK=Path('/scratch/jjyeung/n30_mirror/sb_headacc2/pack')
ROWSETS=PACK.parent/'K1_ROWSETS'
SEL=READER/'heads/selector'
K1=Path('/scratch/jjyeung/k1')
OUT=ROOT/'out/box_ladder'
TABLES=OUT/'serving_tables'
sys.path[:0]=[str(ROOT/'reader_src'),str(SEL/'sl118'),str(SEL),str(TREE)]
from e2e_reader.stage1 import StageOne, median_ratio
from e2e_reader.geometry import from_tower, from_arrays
from e2e_reader import grounding as G
from student_pilot import routed_features as F
from selector_head import load_head
import selector_inputs as SI

def digest(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,allow_nan=False).encode()).hexdigest()

def npz(path):
    with np.load(io.BytesIO(read(path)),allow_pickle=False) as z:
        return {k:z[k] for k in z.files}

def declarations(path,names,bindings):
    nodes=[n for n in ast.parse(read(path).decode()).body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert len(nodes)==len(names)
    exec(compile(ast.Module(nodes,[]),str(path),'exec'),bindings)
    return NS(**{n:bindings[n] for n in names})

def code_pins():
    for p in list(ROOT.glob('*.py'))+list((ROOT/'reader_src/e2e_reader').glob('*.py'))+[ROOT/'run.sh']+list((ROOT/'inputs').glob('*.md')):
        read(p)
    for m in list(sys.modules.values()):
        p=getattr(m,'__file__',None)
        if p and p.endswith('.py') and p.startswith((str(TREE),str(READER))):read(p)

def geometry(c):
    key=digest(c['canonical'])[:16]
    folder=K1/'run_tower_sam_2'/key
    tower=npz(folder/'tower.npz'); receipt=json.loads(read(folder/'PHASE_COMPLETE.json'))
    ownpath=K1/'own_170235/native/probe'/key
    own=npz(ownpath/'own.npz'); ownrec=json.loads(read(ownpath/'PHASE_COMPLETE.json'))
    assert PINS[str(ownpath/'own.npz')]==ownrec['files']['own.npz']
    assert ownrec['capture_sha256']==receipt['capture_sha256']
    assert np.array_equal(tower['frame_indices'][tower['anchor_slots']],c['anchor_indices'])
    scale=median_ratio(tower['depth_grid'],tower['depth_conf_grid'],own['depth'])
    served=float(torch.tensor(float(np.log(scale)),dtype=torch.float32).exp())
    geo=from_tower(tower['raw_pose'],tower['anchor_slots'],tower['frame_indices'],tower['depth_grid'],tower['grid_uv'],own['gravity'],served,receipt['source_hw'])
    path=K1/'run_convert_2'/key
    arrays=npz(path/('geometry.npz' if (path/'geometry.npz').exists() else 'REFUSED_GEOMETRY.npz'))
    stored=from_arrays(**{k:arrays[k] for k in ['K','canvas_to_source','camera_to_world','depth_grid','grid_uv','anchor_frame_indices']},scale=served)
    assert np.array_equal(geo.C,stored.C)
    cache=json.loads(read(path/'candidates.json'))
    meta=json.loads(read(path/'CACHE_COMPLETE.json'))
    return geo,cache,dict(capture=c['canonical'],scale=scale,served_scale=served,gravity=own['gravity'],
        reviewed_guard_refused=not (path/'geometry.npz').exists(),convert_refusal=meta.get('geometry_refusal'),
        checkpoint=ownrec['checkpoint'],arrays_match=True),tower,receipt

def gt_arrays(c):
    gt=npz(c['gt']['path']);assert PINS[c['gt']['path']]==c['gt']['sha256']
    assert np.array_equal(gt['frame_indices'],c['anchor_indices'])
    inst=gt.get('inst',gt.get('instances')); shape=F.OUTPUT_SHAPE
    if inst.shape[1:]!=shape:
        inst=np.stack([ndimage.zoom(f,(shape[0]/f.shape[0],shape[1]/f.shape[1]),order=0,prefilter=False) for f in inst])
    return dict(instances=inst,frame_indices=gt['frame_indices']),gt

def producers(train):
    base=Path('/scratch/jjyeung/orch_n30/k1_ops3/kc')
    old=declarations(base/'grd_selector/work/setsel/build.py',['iou','set_features'],dict(np=np))
    def decode(rle):
        return np.repeat(np.arange(len(rle['counts']))%2==1,rle['counts']).reshape(rle['size'],order='F')
    bindings=dict(collections=collections,itertools=itertools,np=np,
        gate=NS(eligible=lambda ds,cap:ds+'/'+cap in train),original_build=lambda:old,
        B=NS(kitlib=NS(normalize_phrase=lambda n:n,decode=decode)))
    return declarations(base/'k1_build/work/kit_k1a/work/refit/build_tables.py',['extract','label','build_capture'],bindings)

def rebuild(c,producer,head,sample_names):
    started=time.monotonic();geo,cache,meta,_,_=geometry(c)
    gt,_=gt_arrays(c);detect=cache_detect(cache)
    # The producer's extract/label bodies run unchanged, on the reader's raw-name retention.
    retained={n:detect(n) for n in cache['phrases']}
    caches={n:F.cache_for(n,fs) for n,fs in retained.items()}
    raw=dict(phrases=list(retained),frames={str(k):dict(phrases={n:rc['frames'][str(k)]['phrases'][n] for n,rc in caches.items()}) for k in range(32)})
    features,exact=producer.extract(c,raw,geo)
    rows,pairs=producer.label(c,features,exact,gt)
    # Recompute isolated vectors with the producer functions, independently of StageOne.
    inputs=[];isolated={};tracks={};grids=F.candidates.lift_grid(geo)
    for name,frames in retained.items():
        proposals,_=F.candidates.lift(F.cache_for(name,frames),name,geo,floor=.3,grids=grids,phrase=name)
        pool={name:F.candidates.link(proposals,name)};F.candidates.scene_candidates(pool,geo)
        accepted=F.accept_features(pool[name],frames,F.Geometry(geo))
        vectors=SI.candidate_vectors(pool[name],frames,F.Geometry(geo),accepted) if accepted else []
        isolated[name]=(accepted,vectors)
        tracks[name]={p.id:p for p in pool[name]}
        inputs.extend(dict(object_id=c['canonical']+'::'+name,candidate_id=a['candidate_id'],name=name,x=x) for a,x in zip(accepted,vectors))
    # Relabel the isolated pool, so no identity survives a change of geometry or pool.
    rows,pairs=producer.label(c,{n:a for n,(a,x) in isolated.items()},exact,gt)
    checks=[];stage=StageOne(detect,head,geo,rule='null_argmax')
    for name in sample_names:
        expected,x=isolated[name];got,y=stage.features(name)
        with torch.no_grad():
            k=int(torch.argmax(head.with_null(torch.tensor(x,dtype=torch.float64),None,name))) if x else -1
        k=-1 if k==len(x) else k
        j=stage.select(dict(x=torch.tensor(y,dtype=torch.float64),name=name)) if y else -1
        eid=None if k<0 else expected[k]['candidate_id'];gid=None if j<0 else got[j]['candidate_id']
        members_equal=all(set(a['masks'])==set(b['masks']) and all(np.array_equal(a['masks'][f],b['masks'][f]) for f in a['masks']) for a,b in zip(expected,got)) if len(expected)==len(got) else False
        sets_equal=[a['candidate_id'] for a in expected]==[a['candidate_id'] for a in got]
        error=float(np.max(np.abs(np.asarray(x)-np.asarray(y)))) if x and sets_equal else (0. if not x and not y else None)
        checks.append(dict(capture=c['canonical'],dataset=c['canonical'].split('/')[0],name=name,expected=eid,got=gid,passed=eid==gid and members_equal,
            exact_features=error==0.,max_feature_error=error,candidate_sets_equal=sets_equal,members_equal=members_equal))
    rec=dict(capture=c['canonical'],split='train',room=c['room'],rows=rows,pairs=pairs,inputs=inputs,geometry=meta,
        reference='unchanged table producer extract/label; isolated producer vectors; fresh GT labels',input_sha256=dict(PINS))
    dest=TABLES/(c['canonical'].replace('/','__')+'.json.gz')
    with gzip.open(dest,'wt') as f:json.dump(clean(rec),f,allow_nan=False)
    return checks,dict(capture=c['canonical'],candidates=len(rows),objects=len(isolated),geometry=meta,seconds=time.monotonic()-started,path=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest())

def main():
    torch.set_num_threads(8);start=time.monotonic();TABLES.mkdir(parents=True,exist_ok=True)
    manifest=json.loads(read(ROOT/'train_manifest.json'));PINS.update(manifest['input_sha256'])
    caps=manifest['captures'];train={c['canonical'] for c in caps};producer=producers(train)
    reg=json.loads(read('/scratch/jjyeung/orch_n30/k1_ops3/work/gt_sets/GT_SET_PRIMARY_296.json'))
    trainids=set(read(ROWSETS/'K1_TRAIN_TABLES_883.txt').decode().splitlines())
    read(ROWSETS/'K1_TRAIN_1037.txt')
    headpath=SEL/'work/run_iso'
    for ext in ['json','safetensors']:read(headpath/f'selector_head.{ext}')
    head,_=load_head(headpath);code_pins();common=dict(PINS)
    sample={}
    for ds in ['arkitscenes','scannet','scannetpp']:
        eligible=sorted([c for c in caps if c['canonical'].startswith(ds+'/') and any(r['id'] in trainids for r in c['rows'])],key=lambda c:c['canonical'])[:15]
        for c in eligible:
            old=json.loads(gzip.decompress(read(SEL/'data/caps_iso'/(c['canonical'].replace('/','__')+'.json.gz'))))
            sample[c['canonical']]=sorted({n for r in c['rows'] if r['id'] in trainids for n in r['operands']} & {i['name'] for i in old['inputs']})
    write(OUT/'REPLAY_SAMPLE.json',dict(captures=sample,policy='First 15 canonical-sorted registered table training captures per dataset; original table used only for fixed sample names'))
    checks=[];records=[];missing=[]
    for c in sorted(caps,key=lambda c:c['canonical']):
        PINS.clear();PINS.update(common)
        if c['canonical'] not in reg:
            missing.append(dict(capture=c['canonical'],status='MISSING',expected='GT_SET_PRIMARY_296.json entry and GT raster; excluded by registered rowsets'));continue
        c['gt']=reg[c['canonical']]
        dest=TABLES/(c['canonical'].replace('/','__')+'.json.gz')
        done=dest.with_suffix('.receipt.json')
        if done.exists():
            saved=json.loads(read(done));assert hashlib.sha256(dest.read_bytes()).hexdigest()==saved['record']['sha256']
            checks+=saved['checks'];records.append(saved['record']);continue
        rows,record=rebuild(c,producer,head,sample.get(c['canonical'],[]));checks+=rows;records.append(record)
        write(done,dict(checks=rows,record=record))
        print(json.dumps(clean(record)),flush=True)
    PINS.clear();PINS.update(common)
    for r in records:PINS[r['path']]=r['sha256']
    summary={}
    for ds in ['all','arkitscenes','scannet','scannetpp']:
        rows=[r for r in checks if ds=='all' or r['dataset']==ds]
        n=len(rows);matched=sum(r['passed'] for r in rows)
        summary[ds]=dict(matched=matched,total=n,rate=matched/n if n else 0,captures=len({r['capture'] for r in rows}),exact_features=sum(r['exact_features'] for r in rows))
    s=summary['all'];passed=s['rate']>=.95 and s['total']>=149 and s['captures']>=45
    write(OUT/'REFERENCE_REBUILD.json',dict(status='PASS' if passed else 'BLOCKED',summary=summary,checks=checks,captures=records,missing=missing,
        seconds=time.monotonic()-start,peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024))
    write(ROOT/'out/DRYRUN.json',dict(status='REPLAY_PASS' if passed else 'BLOCKED',passed=passed,stage1_replay=summary,
        full_train_started=False,heldout_evaluated=False,A6_status='DEFERRED by order 0654Z'))
    (ROOT/'STATUS.md').write_text(f'Serving reference rebuild: {len(records)} training captures; replay {s["matched"]}/{s["total"]} across {s["captures"]} captures. Gate {"PASS" if passed else "FAIL"}. Fresh labels use GT rasters on R1 serving geometry. Held-out and A6 remain deferred.\n')
    print(json.dumps(summary),flush=True)

if __name__=='__main__':main()
