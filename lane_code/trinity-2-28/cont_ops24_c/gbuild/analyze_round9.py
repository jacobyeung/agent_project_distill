"""Bounded CPU image-content and identity audit; creates round-9 files only."""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['PYTHONDONTWRITEBYTECODE']='1'
import resource
resource.setrlimit(resource.RLIMIT_AS,(15*1024**3,15*1024**3))
import hashlib, json, time, zipfile
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np
from gpkg.capture_io import Records
from gpkg.grid import resize
from gpkg.runtime.c import unrle
from round7_common import Bootstrap, read, write, sha, table, fmt
from analyze_round5 import FRAMES, DENSE

ROOT=Path(__file__).resolve().parent
CAP=ROOT.parent/'cap'
OUT=CAP/'score_bind'
LUT=np.array([int(i).bit_count() for i in range(256)],dtype=np.uint8)
MODES=['same','shift_-2','shift_-1','shift_+1','shift_+2','rot180','flip_h','flip_v']
SOURCES={}

def load(path):
    SOURCES[str(path)]=sha(path)
    return read(path)

def median(v):
    return float(np.median(v)) if len(v) else None

def packed(mask):
    return np.packbits(mask.reshape(-1)),int(mask.sum())

def iou(a,aa,b,ba):
    inter=int(LUT[np.bitwise_and(a,b)].sum())
    union=aa+ba-inter
    return inter/union if union else 0.

def variants(mask):
    out={'same':mask,'rot180':np.rot90(mask,2),'flip_h':np.fliplr(mask),'flip_v':np.flipud(mask)}
    if mask.shape==(320,240):
        out.update(rot90_ccw=np.rot90(mask,1),rot90_cw=np.rot90(mask,-1))
    return out

def summary(frames,modes):
    result={}
    for mode in modes:
        rows=[r for r in frames if r['gt_visible'] and r['best_iou'][mode] is not None]
        vals=[r['best_iou'][mode] for r in rows]
        base=[r['best_iou']['same'] for r in rows]
        active=[r for r in rows if r['proposal_count']>0]
        own_visible=[r for r in frames if r['gt_pixels_by_mode'][mode] and r['best_iou'][mode] is not None]
        result[mode]=dict(n=len(rows),median=median(vals),paired_same_median=median(base),
            median_gain=(median(vals)-median(base)) if vals else None,
            n_with_proposals=len(active),median_with_proposals=median([r['best_iou'][mode] for r in active]),
            all_anchor_median=median([r['best_iou'][mode] for r in frames if r['best_iou'][mode] is not None]),
            own_visible_n=len(own_visible),own_visible_median=median([r['best_iou'][mode] for r in own_visible]),
            fraction_gt_05=sum(v>.5 for v in vals)/len(vals) if vals else None)
    alternatives=[m for m in modes if m!='same' and result[m]['median'] is not None]
    best=max(alternatives,key=lambda m:result[m]['median']) if alternatives else None
    gain=max(alternatives,key=lambda m:result[m]['median_gain']) if alternatives else None
    same=result['same']['median']
    return dict(modes=result,same_median=same,best_alternative=best,
                best_alternative_median=result[best]['median'] if best else None,
                best_mode=max([m for m in modes if result[m]['median'] is not None],key=lambda m:result[m]['median']) if same is not None else None,
                gain_mode=gain,max_paired_median_gain=result[gain]['median_gain'] if gain else None,
                changed=bool(gain and result[gain]['median_gain']>.2),
                changed_vs_full_same=bool(best and same is not None and result[best]['median']-same>.2))

def analyze_object(obj,key,iid,raster,sources,arm):
    modes=MODES+(['rot90_ccw','rot90_cw'] if raster.shape[1:]==(320,240) else [])
    masks=[variants(frame==iid) for frame in raster]
    truth=[{m:packed(a) for m,a in row.items()} for row in masks]
    proposals=defaultdict(list)
    if arm=='points_selected':
        for f,m in obj['selected_masks'].items(): proposals[int(f)-1].append(dict(mask=m))
    else:
        for p in obj['proposals']:
            k=int(p['frame'])-1
            assert 0<=k<32
            if 'source_index' in p: assert p['source_index']==sources[k]
            proposals[k].append(p)
    frames=[]
    for k in range(32):
        prepared=[]
        for p in proposals[k]:
            raw=unrle(p['mask'])
            shapes={a.shape for a in masks[k].values()}
            prepared.append({shape:packed(resize(raw,shape)) for shape in shapes})
        values={};areas={};winners={};gt_slots={}
        for mode in modes:
            shift=int(mode.split('_')[1]) if mode.startswith('shift_') else 0
            j=k+shift; transform='same' if shift else mode
            gt_slots[mode]=j if 0<=j<32 else None
            if not 0<=j<32:
                values[mode]=None;areas[mode]=None;winners[mode]=None;continue
            target,area=truth[j][transform];shape=masks[j][transform].shape
            vals=[iou(target,area,*p[shape]) for p in prepared]
            values[mode]=max(vals,default=0.);areas[mode]=area
            winners[mode]=int(np.argmax(vals)) if vals else None
        frames.append(dict(anchor_slot=k,reader_frame=k+1,source_index=sources[k],gt_visible=areas['same']>0,
                           proposal_count=len(prepared),best_iou=values,gt_pixels_by_mode=areas,
                           gt_slot_by_mode=gt_slots,best_proposal_index_in_frame=winners))
    return dict(key=key,arm=arm,instance_id=iid,frames=frames,summary=summary(frames,modes))

def main():
    start=time.monotonic();OUT.mkdir(exist_ok=True)
    gt=load(ROOT/'out2/GT.json');staging=load(ROOT/'kit2/kit/rerun2/gt_staging.json')
    refs={r['item_id']:r for r in load(ROOT/'kit2/kit/rerun2/items544.json')['items']}
    manifest={r['scene']:r for r in load(FRAMES)['captures']};dense=load(DENSE)['captures']
    funnel=load(CAP/'score_t1/FUNNEL_T1.json')
    camera_split={r['capture']:r for r in load(CAP/'score_t1/CAMERA_SPLIT.json')['captures']}
    joins={r['key']:r for r in map(json.loads,(CAP/'score_t1/JOIN_T1.jsonl').read_text().splitlines())}
    SOURCES[str(CAP/'score_t1/JOIN_T1.jsonl')]=sha(CAP/'score_t1/JOIN_T1.jsonl')
    receipts={a:load(CAP/f'{a}ret/CAPTURE.json') for a in ('t1','t2')}
    parity={a:load(CAP/f'{a}ret/PARITY.json') for a in ('t1','t2')}
    parity_bind={r['item_id']:r for r in parity['t2']['bindings']}
    rasters={};identity=[];member_pins=[];compressed_bytes=0
    for e in staging['files']:
        c=e['capture']
        if c not in gt:continue
        path=ROOT.parent/'gt'/e['relative_path'];m=manifest[c]
        with np.load(path,allow_pickle=False) as z:
            fields=z.files;rasters[c]=z['inst'];idx=z['frame_indices'].tolist();valid=z['valid'].tolist()
            assert all(valid) and idx==gt[c]['source_indices']==m['anchor_indices']==[f['index'] for f in m['frames']]
            assert np.array_equal(z['c2w'],np.array(gt[c]['c2w']))
            pins={}
            # Hash exact uncompressed NPY members; omit the large, unused depth member.
            for name in ('inst','frame_indices','valid','c2w','ids','labels'):
                with z.zip.open(name+'.npy') as f: pins[name+'.npy']=hashlib.file_digest(f,'sha256').hexdigest()
                compressed_bytes+=z.zip.getinfo(name+'.npy').compress_size
            member_pins.append(dict(path=str(path),bytes=path.stat().st_size,npy_member_sha256=pins))
        d=dense[m['native']]
        assert [d['frames'][s]['index'] for s in d['anchor_slots']]==idx
        assert [d['frames'][s]['sha256'] for s in d['anchor_slots']]==[f['sha256'] for f in m['frames']]
        identity.append(dict(capture=c,npz_path=str(path),npz_fields=fields,staging=e,
            native=m['native'],rgb_hw=m['hw'],gt_hw=list(rasters[c].shape[1:]),
            timestamp_rule=m.get('fps_rule'),fps=m['fps'],timestamps_synthetic=bool(np.allclose(m['timestamps'],np.array(idx)/m['fps'])),
            gt_native_rgb_id_timestamp_hash_fields=[],gt_rgb_hash_bindable=False,
            checks=dict(npz_gt_manifest_indices=True,dense_anchor_indices=True,dense_anchor_png_hashes=True),
            anchors=[dict(anchor_slot=k,gt_frame_index=i,reader_frame_index=f['index'],reader_png=f['path'],
                          reader_png_sha256=f['sha256'],reader_timestamp=m['timestamps'][k],gt_timestamp=None,
                          gt_rgb_filename=None,gt_rgb_sha256=None) for k,(i,f) in enumerate(zip(idx,m['frames']))]))
    assert len(rasters)==38
    objects=[];capture_reads={};record_identity=[];validation=dict(landscape_proposed_checks=0,bound_calls={},point_missing_t1_keys=[])
    for name,arm in [('t1','t1_raw'),('t2','points_raw')]:
        records=Records(CAP/f'{name}.gz',receipts[name]);seen=set();calls=0
        for row in records:
            if row['pass_index']!=0 or (name=='t2' and row.get('arm')!='points'):continue
            assert row['item_id'] not in seen;seen.add(row['item_id'])
            c=row['capture'];ref=refs[row['item_id']]
            assert c==ref['capture'] and row['source_indices']==ref['source_indices']
            if c not in gt:continue
            m=manifest[c];indices=row['source_indices']
            assert indices==gt[c]['source_indices']==ref['task']['source_frame_indices']
            if row.get('geometry'):assert row['geometry']['source_indices']==indices
            binding=row.get('binding');checks=dict(source_indices=True,geometry_source_indices=True)
            if name=='t2':
                hashes=[f['sha256'] for f in m['frames']]
                assert binding['frame_hashes_match'] and binding['bound_anchor_sha256']==binding['expected_anchor_sha256']==hashes
                assert parity_bind[row['item_id']]['bound_anchor_sha256']==hashes
                checks['reader_receipt_png_hashes']=True
            else: checks['reader_receipt_png_hashes']=None
            record_identity.append(dict(item_id=row['item_id'],capture=c,arm=name,checks=checks,
                                        native_rgb_gt_hash_binding=False))
            for obj in row['objects']:
                key=row['item_id']+':'+obj['name'];target=gt[c]['targets'].get(key,{})
                b=target.get('binding',{})
                if b.get('instance_id') is None:continue
                assert joins[key].get('binding')==b
                r=analyze_object(obj,key,b['instance_id'],rasters[c],indices,arm)
                r.update(capture=c,item_id=row['item_id'],name=obj['name']);objects.append(r);calls+=1
                if name=='t1' and rasters[c].shape[1:]==(240,320):
                    computed=any(f['best_iou']['same']>.5 for f in r['frames'])
                    assert computed==joins[key]['evidence']['proposed'],key
                    validation['landscape_proposed_checks']+=1
                if name=='t2':
                    r=analyze_object(obj,key,b['instance_id'],rasters[c],indices,'points_selected')
                    r.update(capture=c,item_id=row['item_id'],name=obj['name']);objects.append(r)
            if len(seen)%25==0:print(json.dumps(dict(arm=arm,items=len(seen),bound_calls=calls)),flush=True)
        assert len(seen)==150 and not records.report['salvaged']
        capture_reads[name]=records.report;SOURCES[str(CAP/f'{name}.gz')]=records.report['raw_sha256'];validation['bound_calls'][name]=calls
    t1keys={o['key'] for o in objects if o['arm']=='t1_raw'}
    assert t1keys=={o['key'] for o in objects if o['arm']=='points_raw'}
    captures=[]
    for c in gt:
        al=camera_split[c]['rigid_fit'];cl='pass' if al['accepted'] else 'gross' if al['rotation_max_deg']>60 else 'moderate'
        rr=dict(capture=c,dataset=c.split('/')[0],camera_class=cl,camera_pass=al['accepted'],
                portrait=rasters[c].shape[1:]==(320,240),arms={})
        for arm in ('t1_raw','points_raw','points_selected'):
            oo=[o for o in objects if o['capture']==c and o['arm']==arm]
            frames=[f for o in oo for f in o['frames']]
            modes=MODES+(['rot90_ccw','rot90_cw'] if rr['portrait'] else [])
            rr['arms'][arm]=dict(objects=len(oo),**summary(frames,modes))
        captures.append(rr)
    groups=[]
    for ds in ('arkitscenes','scannet','scannetppv2'):
        for split in ('all','pass','fail'):
            cc=[c for c in captures if c['dataset']==ds and (split=='all' or c['camera_pass']==(split=='pass'))]
            for arm in ('t1_raw','points_raw','points_selected'):
                aa=[c['arms'][arm] for c in cc];measured=[a for a in aa if a['same_median'] is not None]
                groups.append(dict(dataset=ds,camera_split=split,arm=arm,captures=len(cc),measured_captures=len(measured),
                    same_median=median([a['same_median'] for a in measured]),
                    best_alternative_median=median([a['best_alternative_median'] for a in measured]),
                    best_including_same_median=median([max(a['same_median'],a['best_alternative_median']) for a in measured]),
                    changed=sum(a['changed'] for a in aa),changed_vs_full_same=sum(a['changed_vs_full_same'] for a in aa),
                    best_alternative_counts=dict(Counter(a['best_alternative'] for a in measured))))
    boot=Bootstrap(refs);funnel_tables=[]
    for group in ('ScanNet + ScanNet++','ARKit (binding unresolved)'):
        isark=group.startswith('ARKit')
        ii=[i for i in funnel['items']['t1'] if i['capture'].startswith('arkitscenes/')==isark]
        oo=[o for o in funnel['objects']['t1'] if o['capture'].startswith('arkitscenes/')==isark]
        for stage in ('S0','S1','S2','S3','S4','S5','no-GT','censored'):
            selected=[i for i in ii if i['stage']==stage]
            funnel_tables.append(dict(group=group,reported_stage=stage if not isark or stage!='S1' else 'ARKit: unresolved S1 candidates',
                original_stage=stage,objects=sum(o['stage']==stage for o in oo),items=len(selected),score=boot.metric(selected,'score'),
                diagnostic_only=isark))
    assert sum(r['objects'] for r in funnel_tables)==300 and sum(r['items'] for r in funnel_tables)==150
    camera_tables=[]
    for group in ('ScanNet + ScanNet++','ARKit (binding unresolved)'):
        cc=[c for c in captures if c['dataset']=='arkitscenes'] if group.startswith('ARKit') else [c for c in captures if c['dataset']!='arkitscenes']
        camera_tables.append(dict(group=group,captures=len(cc),**{k:sum(c['camera_class']==k for c in cc) for k in ('pass','moderate','gross')}))
    # Preserve camera-question results separately from the 38 distance captures.
    cam=load(CAP/'score_cam/CAMERA_ITEMS_R8.json')
    camera_question_tables=[r for r in cam['tables'] if r['dataset']!='all' and r['type']=='all']
    dependencies=[ROOT/p for p in ('analyze_round9.py','round7_common.py','analyze_round5.py','gpkg/capture_io.py','gpkg/grid.py','gpkg/runtime/c.py','gpkg/source_pins.py','gt/v2.py','gt/adapter.py','gpkg/join_v2.py','kit2/kit/rerun2/join.py','work/payload/tree/student_pilot/routed_features.py','work/payload/tree/generator/derivgen_v7/derivgen/native.py')]
    for p in dependencies:SOURCES[str(p)]=sha(p)
    result=dict(schema='image-content-binding-r9',definitions=dict(
        units='Queried object-call occurrences, using exactly the T1 unique instance bindings; no cross-call pooling.',
        main_median='Within capture: median over object-call/anchor rows with nonempty same-frame GT. Missing proposals score zero. Dataset entries are medians of capture medians.',
        shifts='GT slot k+s versus reader slot k; no wraparound. Out-of-range slots are null. A shifted empty GT scores zero. Gain uses same-frame median on the identical eligible rows.',
        changed='Any alternative has a median IoU more than 0.2 above its paired same-frame median. Also record the literal alternative minus full same-frame classification.',
        portrait='No validated portrait mapping exists in the supplied adapter. Diagnostics use unchanged native 320x240 GT for identity/180/flips and exact np.rot90 GT for +/-90, giving 240x320. Proposals use the identical routed_features.resize function to each resulting GT grid. GT is never resized.',
        portrait_coordinates='For H=320,W=240: CCW maps (x,y) to (y,W-1-x); CW maps (x,y) to (H-1-y,x). Raw proposals are resized to that hypothesis grid; these are normalized-image-coordinate diagnostics, not an accepted source calibration.',
        raw_points='Both best raw point-arm proposals and the selected point-arm mask are evaluated; points arm only, no restricted-selector or noise arms.',
        no_gt_hash='Reader receipt PNG hashes establish reader inputs, but NPZ rows have no independent RGB hashes, native RGB filenames or timestamps.',
        hypothesis_scope='Each shift or image transform is tested separately; no combined shifts/transforms, continuous offset, arbitrary permutation, or camera fit.'),
        dataset_table=groups,captures=captures,objects=objects,identity=identity,record_identity=record_identity,
        funnel_tables=funnel_tables,camera_tables=camera_tables,camera_question_dataset_tables=camera_question_tables,
        validation=validation,capture_reads=capture_reads,input_sha256=SOURCES,npz_member_sha256=member_pins,
        runtime=dict(seconds=time.monotonic()-start,max_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                     numerical_threads=1,address_space_GiB=15,npz_compressed_member_bytes=compressed_bytes))
    write(OUT/'BINDING_R9.json',result)
    print(json.dumps(dict(runtime=result['runtime'],dataset_table=[g for g in groups if g['camera_split']=='all'])),flush=True)

if __name__=='__main__':main()
