"""Read-only, local CPU re-review; write evidence only beside this file."""
import ast
import collections as C
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
B = Path('/scratch/jjyeung/orch_n30')
OLD = B/'sb_mdrev'
SRC = Path('/scratch/jjyeung/b01ec87a6f29b/d/s')
PINS = {}

def read(p):
    p = Path(p).resolve()
    assert str(p).startswith('/scratch/'), p
    raw = p.read_bytes()
    PINS[str(p)] = hashlib.sha256(raw).hexdigest()
    return raw

def js(p): return json.loads(read(p))

def pin(p):
    p = Path(p).resolve()
    assert str(p).startswith('/scratch/'), p
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024), b''): h.update(chunk)
    PINS[str(p)] = h.hexdigest()
    return h.hexdigest()

def save(name, data):
    pin(__file__)
    data['input_sha256'] = dict(PINS)
    data['command'] = 'bash run_review_v2.sh '+sys.argv[1]
    (HERE/name).write_text(json.dumps(data, indent=2)+'\n')

def evidence():
    old = {n:js(OLD/(n+'.json')) for n in ['NUMBERS','DATA_AUDIT','CACHE_AUDIT','DETAILS','ALIAS_AUDIT']}
    for n in ['REVIEW_VERDICT.md','audit.py','run_review.sh']: read(OLD/n)
    specs = {p.name:read(p).decode() for p in sorted((HERE/'in').glob('*.md'))}
    pins = ['bdb5d402','969cdb56','3119aa4a','634820b4','4d4736cf','sb_auditfix2','planted-row']
    checks = {n:{s:s in v for s in pins} for n,v in specs.items() if n.startswith('KIT_SPEC')}
    receipt = js('/scratch/jjyeung/b01ec87a6f29b/d/k/SAM3_RECEIPT.json')
    checkpoint = '/scratch/jjyeung/b01ec87a6f29b/d/k/sam3.pt'
    source_checks = {n:pin(SRC/n)==h for n,h in receipt['source_files'].items()}
    source_list = ['sam3/model/sam3_tracking_predictor.py','sam3/train/loss/sam3_loss.py','sam3/train/loss/loss_fns.py','sam3/train/matcher.py']
    symbols = {}
    for n in source_list:
        tree = ast.parse(read(SRC/n))
        symbols[n] = [x.name for x in tree.body if isinstance(x,(ast.ClassDef,ast.FunctionDef))]
    for p in [B/'sb_kbox4/train_pricing.py',B/'sb_kbox4/summarize_train.py',B/'sb_kbox4/eligibility_report.py',B/'sb_kbox4/reader_src/e2e_reader/stage1.py',B/'b04host3/tree_rebuild/work/base/tree_b01ce449/student_pilot/routed_features.py',B/'b04host3/tree_rebuild/work/base/tree_b01ce449/student_pilot/routed_candidates.py']: read(p)
    result = dict(reused={n:{k:v for k,v in d.items() if k not in ('input_sha256','attribution')} for n,d in old.items()},spec_exclusion_tokens=checks,checkpoint_sha256=pin(checkpoint),checkpoint_matches=None,receipt_source_hash_matches=source_checks,source_symbols=symbols)
    result['checkpoint_matches'] = result['checkpoint_sha256']==receipt['checkpoint_sha256']
    save('EVIDENCE_V2.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('reused','input_sha256')},indent=2))

def numbers():
    records = js(B/'sb_maskfail/out/MASKFAIL.json')['records']
    objs = C.defaultdict(list)
    for r in records: objs[r['row'],r['object']].append(r)
    first = {'n':0,'served':0,'pool':0}
    for rr in objs.values():
        vis=[r['frame'] for r in rr if r['valid'] and r['visible'] and r['share']>=.001]
        if not vis: continue
        first['n']+=1
        for name,field in [('served','iou'),('pool','deployed_best_iou')]:
            hit=[r['frame'] for r in rr if r['valid'] and r['visible'] and (r[field] or 0)>=.3]
            first[name]+=bool(hit and min(hit)==min(vis))
    manifest=js(B/'sb_kbox4/pinned_train.json')
    ids=set(read('/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS/K1_TRAIN_1037.txt').decode().splitlines())
    rewrite=[r['id'] for c in manifest['captures'] for r in c['rows'] if r['id'] in ids and set(r['operands']) & {'heater','coat hanger'}]
    counts=C.Counter();names=set();spacing=C.defaultdict(list);spacing_all=C.defaultdict(list)
    for c in manifest['captures']:
        for r in c['rows']:
            if r['id'] in ids:
                counts.update((c['canonical'],n) for n in r['operands']); names.update(r['operands'])
        anchors=c.get('anchor_indices',[])
        spacing_all[c['canonical'].split('/')[0]].extend(b-a for a,b in zip(anchors,anchors[1:]))
        if any(r['id'] in ids for r in c['rows']):
            spacing[c['canonical'].split('/')[0]].extend(b-a for a,b in zip(anchors,anchors[1:]))
    import numpy as np
    result=dict(first_share_point001=first,rewrite_rows=len(set(rewrite)),distinct_objects=len(counts),operand_names=len(names),anchor_spacing_priced={k:float(np.median(v)) if v else None for k,v in spacing.items()},anchor_spacing_all={k:float(np.median(v)) if v else None for k,v in spacing_all.items()},teacher_gpu_seconds_per_prompt_frame=77*60*2/(4546*32))
    save('NEW_NUMBERS.json',result);print(json.dumps(result,default=str)[:2000])

def legality():
    path=B/'sb_auditfix2/store_room_audit.py';read(path)
    spec=importlib.util.spec_from_file_location('fixed_audit',path)
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    ledger=audit.Inputs()
    rooms,mint,sets,checks,aliases,quarantine=audit.prepare(B/'sb_auditfix2/inputs/tree_r1',B/'sb_auditfix2/inputs/lists',ledger)
    p=js(B/'sb_kbox4/pinned_train.json')
    mismatches=[];hits={n:[] for n in sets};resolved=[]
    ids=set(read('/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS/K1_TRAIN_1037.txt').decode().splitlines())
    for c in p['captures']:
        ds,scene=c['canonical'].split('/',1)
        _,canonical,room,_,error=audit.resolve(dict(dataset=ds,scene=scene,canonical=c['canonical']),rooms,mint,aliases,quarantine)
        if error or room!=c['room']:mismatches.append([c['canonical'],room,c['room'],error])
        resolved.append(room)
        for n,s in sets.items():
            if room in s:hits[n].append(c['canonical'])
    # The explicit planted-row test uses an authoritative R0 room, not a new mapping.
    r0=next(s for s in sorted(sets['R0']) if s.startswith('scannet/'))
    planted=dict(dataset='scannet',scene=r0.split('/')[1]+'_99')
    _,canonical,room,_,error=audit.resolve(planted,rooms,mint,aliases,quarantine)
    PINS.update({k:v['sha256'] for k,v in ledger.pins.items()})
    overlap=set(hits['withheld-80'])
    affected=[dict(capture=c['canonical'],room=c['room'],priced_row_ids=[r['id'] for r in c['rows'] if r['id'] in ids]) for c in p['captures'] if c['canonical'] in overlap]
    result=dict(captures=len(p['captures']),rooms=len(set(resolved)),mismatches=mismatches,real_hits=hits,withheld_affected=affected,withheld_unique_rooms=len({c['room'] for c in affected}),withheld_priced_captures=sum(bool(c['priced_row_ids']) for c in affected),withheld_priced_rows=sum(len(c['priced_row_ids']) for c in affected),planted_row=planted,planted_resolved_room=room,planted_error=error,planted_hits={n:int(room in s) for n,s in sets.items()},list_checks=checks,scope='Fixed checker prepare/resolve on exact pinned capture identities; no benchmark questions or answers opened.')
    save('LEGALITY_V2.json',result);print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},indent=2))

def aliases():
    import io
    import numpy as np
    from scipy.ndimage import zoom
    records=js(B/'sb_maskfail/out/MASKFAIL.json')['records']
    manifest=js(B/'sb_kbox4/pinned_train.json')
    ids=set(read('/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS/K1_TRAIN_1037.txt').decode().splitlines())
    bycap=C.defaultdict(dict)
    for r in records:bycap[r['capture']][r['object'],r['frame']]=r
    result={};summary=C.Counter();recover=C.Counter();row_hits={}
    for c in manifest['captures']:
        cap=c['canonical']
        if cap not in bycap:continue
        key=hashlib.sha256(json.dumps(cap,sort_keys=True,allow_nan=False).encode()).hexdigest()[:16]
        cache=js(Path('/scratch/jjyeung/k1/run_convert_2')/key/'candidates.json')
        with np.load(io.BytesIO(read(c['gt']['path'])),allow_pickle=False) as z:
            raster=z['inst'] if 'inst' in z else z['instances'];valid=z['valid']
        if raster.shape[1:]!=(240,320):raster=np.stack([zoom(x,(240/x.shape[0],320/x.shape[1]),order=0,prefilter=False) for x in raster])
        names=sorted({n for row in c['rows'] if row['id'] in ids for n in row['operands']})
        hits={}
        for name in names:
            hit=set();iid=c['gt_name_ids'][name][0]
            for slot in range(32):
                if not valid[slot] or not np.any(raster[slot]==iid):continue
                rec=cache['frames'][str(slot)]['phrases'].get(name)
                if not rec:continue
                target=raster[slot]==iid;pres=float(rec['presence'])
                entries=sorted([e for e in rec['instances'] if float(e['score'])>=.3 and float(e['score'])*float(e.get('source_presence',pres))>=.05],key=lambda e:-float(e['score']))
                ranks=C.Counter()
                for pooled_rank,e in enumerate(entries):
                    prompt=e.get('source_prompt',name);ranks[prompt]+=1
                    if prompt in hit or ranks[prompt]>30:continue
                    rle=e['mask'];h,w=rle['size'];cs=np.asarray(rle['counts'],np.int64)
                    mask=np.repeat(np.arange(len(cs))%2==1,cs).reshape((h,w),order='F')
                    if mask.shape!=(480,640):mask=zoom(mask,(480/h,640/w),order=0,prefilter=False)
                    mask=mask[::2,::2];union=np.count_nonzero(mask|target)
                    if union and np.count_nonzero(mask&target)/union>=.5:hit.add(prompt)
            hits[name]=hit
            result[cap+'::'+name]=sorted(hit)
        for row in c['rows']:
            if row['id'] not in ids:continue
            row_hits[row['id']]={}
            for name in row['operands']:
                selected={'heater':'radiator','coat hanger':'coat rack'}.get(name,name)
                hit=hits[name];row_hits[row['id']][name]=dict(raw=name in hit,single=selected in hit,pool=bool(hit))
                summary.update(operands=1,raw=int(name in hit),single=int(selected in hit),pool=int(bool(hit)))
                if selected in hit and name not in hit:recover[name]+=1
        if len(result)%100<5:print('objects',len(result),flush=True)
    items=[json.loads(x) for x in read(B/'sb_kbox4/out/box_ladder/PER_ITEM.jsonl').splitlines()]
    arms=C.defaultdict(dict)
    for r in items:arms[r['arm']][r['row_id']]=r
    # Reuse the original review's exact categories and score convention.
    code=read(OLD/'audit.py').decode();ns={'__file__':str(OLD/'audit.py'),'__name__':'reused_audit'};exec(compile(code,str(OLD/'audit.py'),'exec'),ns)
    mra=ns['mra'];objs=C.defaultdict(list)
    for r in records:objs[r['row'],r['object']].append(r)
    missed=C.defaultdict(list)
    for (rid,name),rr in objs.items():
        if rr[0]['selected_candidate_id'] is None or (max(r['iou'] or 0 for r in rr)<.1 and max(r['precision'] for r in rr)<.2):missed[rid].append(name)
    groups=C.defaultdict(list)
    for rid,names in missed.items():
        if not all(any(r['valid'] and r['visible'] and r['deployed_best_iou']>=.5 for r in objs[rid,n]) for n in names):continue
        groups['above' if all(row_hits[rid][n]['raw'] for n in names) else 'below'].append(rid)
    partition={k:dict(rows=len(v),contribution=sum(mra(arms['A2_gt_masks'][i])-mra(arms['A0_deployed'][i]) for i in v)/1037) for k,v in groups.items()}
    output=dict(counts=dict(summary),single_recovers=dict(recover),lifting_partition=partition,object_prompt_hits=result,method='Each source prompt: joint >= .05, conditional >= .3, cap 30; valid visible raster IoU >= .5; row-operand weights. Pooled recall uses union; the original cap audit found no cap-dependent recalls.')
    save('ALIASES_V2.json',output);print(json.dumps({k:v for k,v in output.items() if k not in ('object_prompt_hits','input_sha256')},indent=2))

def contracts():
    import math
    import types
    import typing
    pos=SRC/'sam3/model/position_encoding.py'
    tree=ast.parse(read(pos))
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PositionEmbeddingSine')
    ctor=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
    cls.body=[ctor]
    class Module:
        def __init__(self):pass
    calls=[]
    def zeros(shape,**kw):
        calls.append(dict(shape=shape,**kw))
        raise RuntimeError('CPU-only probe intercepted allocation: '+kw['device'])
    ns=dict(nn=types.SimpleNamespace(Module=Module),torch=types.SimpleNamespace(zeros=zeros),math=math,Optional=typing.Optional)
    exec(compile(ast.Module(body=[cls],type_ignores=[]),str(pos),'exec'),ns)
    errors={}
    for width in [64,256]:
        try:ns['PositionEmbeddingSine'](num_pos_feats=width,precompute_resolution=1008)
        except RuntimeError as e:errors[str(width)]=str(e)
    paths=['sam3/model_builder.py','sam3/model/sam3_tracking_predictor.py','sam3/train/loss/sam3_loss.py','sam3/train/loss/loss_fns.py','sam3/train/matcher.py','sam3/train/configs/odinw13/odinw_text_only_train.yaml','sam3/train/configs/roboflow_v100/roboflow_v100_full_ft_100_images.yaml']
    for name in paths:read(SRC/name)
    for p in sorted((HERE/'in').glob('*.md')):read(p)
    result=dict(cpu_constructor_probe=dict(calls=calls,errors=errors,no_cuda_calls_executed=True),tracker='build_tracker calls maskmem PositionEmbeddingSine(precompute_resolution=1008); default with_backbone=False and no checkpoint loader in this function.',detector='build_sam3_image_model calls _create_vision_backbone, which precomputes PositionEmbeddingSine at 1008 before moving the model to its requested device.',loss='The spec leaves the exact YAML unspecified. IABCEMdetr has no per-prediction ignore-region input; unmatched predictions get negative BCE (with whole-query nonexhaustive masking only). No dry-run gradient proof of the specified small-instance ignore exists in supplied inputs.')
    save('CONTRACTS_V2.json',result);print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},indent=2))

if __name__=='__main__': globals()[sys.argv[1]]()
