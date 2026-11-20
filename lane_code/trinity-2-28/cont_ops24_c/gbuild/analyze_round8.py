"""CPU-only, held-out camera audit. Never emit question text or wording groups."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[k]='1'
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['PYTHONDONTWRITEBYTECODE']='1'
import sys, time, json, gzip, hashlib, zipfile, io, re, resource
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
from analyze_round5 import angles, sha, FRAMES, DENSE
from gt.v2 import alignment
from project_round6 import pair_errors
from round7_common import Bootstrap, table
from gpkg.capture_io import Records
ROOT=Path(__file__).resolve().parent
CAP=ROOT.parent/'cap'; CAM=Path('/scratch/jjyeung/orch_n30/cont_ops25_c/cam')
OUT=CAP/'score_cam'
sys.path.insert(0,str(ROOT/'work/payload/tree'))
from student_pilot.camera_targets import encode_cameras, to_gravity_reference_frame
from student_pilot.carrier_c1_routing import OwnGeometry
TYPES=['displacement','rotation','direction']
CLASSES=['pass','moderate','gross','unclassified-GT','no-GT']
START=time.monotonic(); inputs={}
def read(p):
    p=Path(p);inputs[str(p)]=sha(p);return json.loads(p.read_text())
def write(p,v):
    # These R8 paths were created in this session; no earlier delivery is writable here.
    with Path(p).open('w') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def textfile(p,s):
    with Path(p).open('x') as f:f.write(s)
def category(f):return 'pass' if f['accepted'] else 'gross' if f['rotation_max_deg']>60 else 'moderate'
def angle_vec(a,b):
    a,b=np.asarray(a),np.asarray(b);n=np.linalg.norm(a,axis=-1)*np.linalg.norm(b,axis=-1)
    return np.degrees(np.arccos(np.clip(np.sum(a*b,axis=-1)/np.maximum(n,1e-15),-1,1)))
def metric_poses(p,up):
    R,t,_=to_gravity_reference_frame(p,up);C=np.tile(np.eye(4),(len(p),1,1));C[:,:3,:3]=R;C[:,:3,3]=t;return C

def pair(a,b,i,j):
    ar,br=a[:,:3,:3],b[:,:3,:3];ra=ar[i].T@ar[j];rb=br[i].T@br[j]
    ta=ar[i].T@(a[j,:3,3]-a[i,:3,3]);tb=br[i].T@(b[j,:3,3]-b[i,:3,3])
    na,nb=np.linalg.norm(ta),np.linalg.norm(tb)
    return dict(relative_rotation_error_deg=float(angles(ra@rb.T)),
        translation_direction_error_deg=float(angle_vec(ta,tb)) if min(na,nb)>1e-8 else None,
        distance_ratio=float(na/nb) if nb>1e-8 else None,gt_distance_m=float(nb),
        rotation_angle_gap_deg=float(abs(angles(ra)-angles(rb))))

def numeric_response(s):return np.array([float(x) for x in re.findall(r'=\s*([+-]?\d+(?:\.\d+)?)',s)])
def load_camera():
    expected={name:h for h,name in (line.split() for line in (CAM/'reads/reads.sha').read_text().splitlines())}
    inputs[str(CAM/'reads/reads.sha')]=sha(CAM/'reads/reads.sha')
    rows=[];seen=set();scorechecks=0
    for name,h in expected.items():
        p=CAM/'reads'/name;assert sha(p)==h;inputs[str(p)]=h
        for line in gzip.open(p,'rt'):
            r=json.loads(line);x=r['raw']['input'];raw=r['raw']['arms']['tower'];o=raw['output'];step=int(r['export']['step'])
            key=(step,r['item_id']);assert key not in seen;seen.add(key)
            score=r['arms']['tower']['score'];assert score==r['arms']['tower']['scores']['answer']==o['scores']['answer'];assert 0<=score<=1;scorechecks+=1
            qt={'camera_displacement':'displacement','camera_rotation':'rotation','camera_movement_direction':'direction'}[r['question_type']]
            # Copy only approved fields; no question, response prose, stratum, or source partition.
            rows.append(dict(item_key=hashlib.sha256(r['item_id'].encode()).hexdigest(),step=step,capture=x['scene'],dataset=x['dataset'],
                room=raw['room_key'],type=qt,score=score,asked_frames=x['display_frame_pair'],source_indices=x['source_frame_indices'],
                dense_count=r['raw']['mapping']['dense_count'],fps=x['fps'],scale=o['scale'],pose9=o['heads']['pose9'],gravity=o['heads']['gravity'],
                provenance=x['label_provenance'],calls=[{k:c[k] for k in ('name','i','j','response') if k in c} for c in o['calls']['records'] if c.get('served') and c.get('name') in ('move','turn')]))
    assert Counter(r['step'] for r in rows)=={544:900,400:900}
    assert len({r['capture'] for r in rows})==52
    assert {r['item_key'] for r in rows if r['step']==544}=={r['item_key'] for r in rows if r['step']==400}
    return rows,scorechecks

def gt_load(rows):
    need=read(CAM/'reads/need.json');receipt=CAM/'gt/c25_gt34.sha';inputs[str(receipt)]=sha(receipt)
    registered={Path(n).name:h for h,n in (line.split() for line in receipt.read_text().splitlines())}
    gt={};pins=[]
    for cap in sorted(need):
        p=CAM/'gt/t1_gt/gt'/(cap.replace('/','__')+'.npz')
        if not p.exists():continue
        assert len(need[cap])==1;n=need[cap][0];assert registered[p.name]==n['gt_sha256']
        with zipfile.ZipFile(p) as z:
            blobs={k:z.read(k+'.npy') for k in ('c2w','frame_indices','valid')}
        h=hashlib.sha256(blobs['c2w']).hexdigest();assert h==n['c2w_sha256']
        data={k:np.load(io.BytesIO(v),allow_pickle=False) for k,v in blobs.items()};assert data['valid'].all()
        for r in (r for r in rows if r['capture']==cap):
            assert r['provenance']['gt_sha256']==n['gt_sha256'] and r['provenance']['gt_members']['c2w']['sha256']==h
            assert np.array_equal(data['frame_indices'],r['source_indices'])
        gt[cap]=data
        pins.append(dict(capture=cap,path=str(p),file_sha256=n['gt_sha256'],file_sha256_authority='supplied c25_gt34.sha; not rehashed',
            c2w_member_sha256=h,c2w_member_rehashed=True,frame_indices_sha256=hashlib.sha256(blobs['frame_indices']).hexdigest()))
    assert len(gt)==34
    return gt,pins

def audit_rows(rows,gt,dist):
    replay=Counter();examples=[];recovered={};groups=defaultdict(list);poses={};codes={}
    for cap,g in dist.items():
        if not g:continue
        p,_,_=encode_cameras(np.array(g['camera_to_world_unscaled']),np.tile(np.eye(3),(32,1,1)),(480,640),all_frames=True)
        codes[cap]=p
    for r in rows:
        cap,step=r['capture'],r['step'];groups[(step,cap)].append(r)
        own=OwnGeometry(r['pose9'],r['gravity'],None)
        scaled=np.array(r['pose9']);scaled[:,:3]*=r['scale'] or 1
        wrongscale=OwnGeometry(scaled,r['gravity'],None)
        for c in r['calls']:
            for mode,geom in [('logged_own',own),('logged_own_times_scale',wrongscale)]:
                s=getattr(geom,c['name']+'_text')(c['i'],c['j']);replay[(step,mode,c['name'],'total')]+=1
                replay[(step,mode,c['name'],'exact')]+=int(s==c['response'])
        r['class']='no-GT' if cap not in gt else 'unclassified-GT'
        r['classification_authority']='unavailable';r['pair_error']=None
        r['served_asked_pair_error']=None
        if cap in gt:
            b=gt[cap]['c2w'];gp,_,_=encode_cameras(b,np.tile(np.eye(3),(32,1,1)),(480,640),all_frames=True)
            gu=b[0,:3,:3].T@np.array([0.,0.,1.]);gg=OwnGeometry(gp,gu,None)
            asked=[c for c in r['calls'] if [c['i'],c['j']]==r['asked_frames']]
            if asked:
                c=asked[0];v=numeric_response(c['response']);truth=numeric_response(getattr(gg,c['name']+'_text')(c['i'],c['j']))
                if c['name']=='move':
                    r['served_asked_pair_error']=dict(tool='move',distance_ratio=float(v[3]/truth[3]) if truth[3]>0 else None,
                        level_translation_direction_error_deg=float(angle_vec(v[:3],truth[:3])) if min(np.linalg.norm(v[:3]),np.linalg.norm(truth[:3]))>0 else None)
                else:
                    r['served_asked_pair_error']=dict(tool='turn',yaw_error_deg=float(abs((v[0]-truth[0]+180)%360-180)))
        if cap not in codes or r['scale'] is None:continue
        assert r['source_indices']==dist[cap]['source_indices']
        p=codes[cap].copy();p[:,:3]*=r['scale'];geom=OwnGeometry(p,r['gravity'],None)
        errors=[]
        for c in r['calls']:
            s=getattr(geom,c['name']+'_text')(c['i'],c['j']);err=float(np.max(np.abs(numeric_response(s)-numeric_response(c['response']))))
            errors.append(err);replay[(step,'distance_reconstruction',c['name'],'total')]+=1
            replay[(step,'distance_reconstruction',c['name'],'exact')]+=int(s==c['response'])
            replay[(step,'distance_reconstruction',c['name'],'within_one_print_unit')]+=int(err<=.0100001 if c['name']=='move' else err==0)
            if s!=c['response']:examples.append(dict(step=step,capture=cap,tool=c['name'],max_printed_difference=err))
        assert all(e<=.0100001 for e in errors)
        C=metric_poses(p,r['gravity']);poses[(step,r['item_key'])]=C
        if cap in gt:
            fit=alignment(C,gt[cap]['c2w']);r['class']=category(fit);r['classification_authority']='distance_tower_reconstruction_approximate'
            r['pair_error']=pair(C,gt[cap]['c2w'],*(i-1 for i in r['asked_frames']))
    caps=[]
    for (step,cap),rr in sorted(groups.items()):
        known=[r for r in rr if r['classification_authority'].startswith('distance')]
        assigned=0
        if known and len({r['class'] for r in known})==1:
            for r in rr:
                if r['class']=='unclassified-GT':
                    r['class']=known[0]['class'];r['classification_authority']='capture_class_from_reconstructed_called_items';assigned+=1
                    r['pair_error']=pair(metric_poses(codes[cap],r['gravity']),gt[cap]['c2w'],*(i-1 for i in r['asked_frames']))
                    r['pair_error']['distance_ratio']=None
        scal=[r['scale'] for r in rr if r['scale'] is not None]
        info=dict(step=step,capture=cap,dataset=rr[0]['dataset'],items=len(rr),rooms=sorted({r['room'] for r in rr}),
            class_counts=dict(Counter(r['class'] for r in rr)),scale_range=[min(scal),max(scal)] if scal else None,
            gravity_origin_error_deg=None,rigid_fit=None,relative_errors=None,no_scale_items_assigned_capture_class=assigned)
        if cap in gt:
            u=gt[cap]['c2w'][0,:3,:3].T@np.array([0.,0.,1.]);errs=[float(angle_vec(r['gravity'],u)) for r in rr]
            info['gravity_origin_error_deg']=dict(mean=float(np.mean(errs)),max=max(errs))
        if known:
            r=known[0];C=poses[(step,r['item_key'])];fits=[alignment(poses[(step,q['item_key'])],gt[cap]['c2w']) for q in known]
            info.update(rigid_fit=fits[0],relative_errors=pair_errors(C,gt[cap]['c2w']),
                class_range=sorted({category(f) for f in fits}),reconstructed_items=len(known),
                max_pose_difference_within_capture=float(max(np.max(np.abs(poses[(step,q['item_key'])]-C)) for q in known)))
        caps.append(info)
    rep=[dict(step=s,source=src,tool=t,**{kind:n for (ss,src2,tt,kind),n in replay.items() if (ss,src2,tt)==(s,src,t)}) for s,src,t in sorted({k[:3] for k in replay})]
    return caps,rep,examples,poses

def served_bins(rows):
    boot=Bootstrap({str(i):{'task':{'room':r['room']}} for i,r in enumerate(rows)})
    result=[]
    specs=[('displacement','distance_ratio',[0,.5,.8,1.2,2,float('inf')]),
           ('direction','level_translation_direction_error_deg',[0,5,15,30,60,181]),
           ('rotation','yaw_error_deg',[0,5,15,30,60,181])]
    for step in (544,400):
      for ds in ('all','scannet','scannetppv2'):
       for typ,field,edges in specs:
        for lo,hi in zip(edges[:-1],edges[1:]):
            rr=[r for r in rows if r['step']==step and r['type']==typ and (ds=='all' or r['dataset']==ds)
                and r['served_asked_pair_error'] and r['served_asked_pair_error'].get(field) is not None
                and lo<=r['served_asked_pair_error'][field]<hi]
            result.append(dict(step=step,dataset=ds,type=typ,error=field,bin=f'[{lo:g},{hi:g})',items=len(rr),accuracy=boot.metric(rr,'score')))
    return result

def score_tables(rows):
    refs={str(i):{'task':{'room':r['room']}} for i,r in enumerate(rows)};boot=Bootstrap(refs);tables=[];loss=[]
    for step in (544,400):
      for ds in ('all','scannet','scannetppv2'):
       for typ in ('all',*TYPES):
        base=[r for r in rows if r['step']==step and (ds=='all' or r['dataset']==ds) and (typ=='all' or r['type']==typ)]
        for cls in (*CLASSES,'all'):
            rr=[r for r in base if cls=='all' or r['class']==cls]
            tables.append(dict(step=step,dataset=ds,type=typ,capture_class=cls,items=len(rr),captures=len({r['capture'] for r in rr}),rooms=len({r['room'] for r in rr}),accuracy=boot.metric(rr,'score')))
        total=sum(1-r['score'] for r in base);gross=sum(1-r['score'] for r in base if r['class']=='gross');unknown=sum(1-r['score'] for r in base if r['class'] in ('unclassified-GT','no-GT'))
        loss.append(dict(step=step,dataset=ds,type=typ,total_loss=total,reconstructed_gross_loss=gross,unknown_class_loss=unknown,
            observed_gross_share=gross/total if total else None,possible_gross_share_range=[gross/total,(gross+unknown)/total] if total else None,
            authority='conditional on approximate overlap classes; full gross share unidentified'))
    bins=[]
    specs=[('relative_rotation_error_deg',[0,5,15,30,60,181]),('translation_direction_error_deg',[0,5,15,30,60,181]),('distance_ratio',[0,.5,.8,1.2,2,float('inf')])]
    for step in (544,400):
      for ds in ('all','scannet','scannetppv2'):
       for field,edges in specs:
        for lo,hi in zip(edges[:-1],edges[1:]):
         for typ in TYPES:
            rr=[r for r in rows if r['step']==step and r['type']==typ and (ds=='all' or r['dataset']==ds) and r['pair_error'] and r['pair_error'][field] is not None and lo<=r['pair_error'][field]<hi]
            bins.append(dict(step=step,dataset=ds,error=field,bin=f'[{lo:g},{hi:g})',type=typ,items=len(rr),accuracy=boot.metric(rr,'score')))
    return tables,loss,bins,boot.rooms

def features(gt,caps,rows,dist,split,meta,dense,poses):
    dg=read(ROOT/'out2/GT.json');lookup={r['capture']:r for r in split['captures']};out=[]
    camera_caps=set(gt);allcaps=set(dg)|camera_caps
    for cap in sorted(allcaps):
        b=np.array(gt[cap]['c2w'] if cap in gt else dg[cap]['c2w']);m=meta[cap];indices=m['anchor_indices'];native=m['native'];d=dense[native]
        di=[f['index'] for f in d['frames']];assert [di[s] for s in d['anchor_slots']]==indices
        fps=m['fps'];h,w=m['hw'];rot=b[:,:3,:3];up=rot.transpose(0,2,1)@np.array([0.,0.,1.])
        # Tilt convention: left tilt puts world up toward image right; right tilt toward image left.
        ori=[]
        for x,y,z in up:
            ori.append(('upright' if y<0 else 'upside_down') if abs(y)>=abs(x) else ('sideways_left' if x>0 else 'sideways_right'))
        angle=angles(rot[:-1].transpose(0,2,1)@rot[1:]);trans=np.linalg.norm(np.diff(b[:,:3,3],axis=0),axis=1)
        distmat=np.linalg.norm(b[:,None,:3,3]-b[None,:,:3,3],axis=-1)
        vals=dict(native_height=h,native_width=w,native_aspect_h_over_w=h/w,native_portrait=float(h>w),tower_frames=len(di),
            time_span_s=(di[-1]-di[0])/fps,mean_tower_gap_s=float(np.diff(di).mean()/fps),mean_anchor_gap_s=float(np.diff(indices).mean()/fps),
            consecutive_anchor_rotation_mean_deg=float(angle.mean()),consecutive_anchor_rotation_max_deg=float(angle.max()),
            consecutive_anchor_translation_mean_m=float(trans.mean()),consecutive_anchor_translation_max_m=float(trans.max()),
            overlap_proxy_rot_gt30=float(np.mean(angle>30)),overlap_proxy_trans_gt1=float(np.mean(trans>1)),
            overlap_proxy_either=float(np.mean((angle>30)|(trans>1))),trajectory_diameter_m=float(distmat.max()),
            trajectory_bbox_diagonal_m=float(np.linalg.norm(np.ptp(b[:,:3,3],axis=0))))
        vals.update({f'orientation_{k}_share':ori.count(k)/len(ori) for k in ('upright','upside_down','sideways_left','sideways_right')})
        for name in ('rotation_mean_deg','rotation_max_deg','translation_mean_m','translation_max_m'):
            vals['consecutive_tower_'+name]=vals['consecutive_anchor_'+name] if len(di)==32 else None
        vals['orientation_non_upright_share']=1-vals['orientation_upright_share']
        vals.update({f'dataset_{ds}':float(cap.startswith(ds+'/')) for ds in ('arkitscenes','scannet','scannetppv2')})
        peranchor=None;distanceclass=None
        if cap in lookup:
            a=np.array(dist[cap]['camera_to_world_metric']);pup=a[:,:3,:3].transpose(0,2,1)@np.array([0.,0.,1.]);ga=angle_vec(pup,up)
            peranchor=ga.tolist();vals.update(gravity_mean_deg=float(ga.mean()),gravity_max_deg=float(ga.max()))
            distanceclass=category(lookup[cap]['rigid_fit'])
        else:vals.update(gravity_mean_deg=None,gravity_max_deg=None)
        states=[c for c in caps if c['capture']==cap]
        camera_gravity=[]
        for step in (544,400):
            rr=[r for r in rows if r['capture']==cap and r['step']==step and (step,r['item_key']) in poses]
            if rr:
                C=poses[(step,rr[0]['item_key'])];pred=C[:,:3,:3].transpose(0,2,1)@np.array([0.,0.,1.]);ga=angle_vec(pred,up)
                camera_gravity.append(dict(step=step,per_anchor_deg=ga.tolist(),mean=float(ga.mean()),max=float(ga.max()),authority='approximate distance-tower reconstruction'))
        out.append(dict(capture=cap,dataset=cap.split('/')[0],in_distance_GT=cap in dg,in_camera_GT=cap in camera_caps,
            distance_class=distanceclass,camera_classes=[dict(step=c['step'],counts=c['class_counts']) for c in states],
            native_rgb_hw=[h,w],native_orientation='portrait' if h>w else 'landscape',source_frame_indices=indices,
            tower_source_frame_indices=di,fps=fps,fps_nominal=cap.startswith('arkitscenes/'),
            native_size_authority='pinned decoded FRAMES.json; upstream sensor size unavailable',
            GT_anchor_orientation=ori,GT_up_in_camera=up.tolist(),gravity_per_anchor_deg=peranchor,
            camera_gravity_origin_error=[dict(step=c['step'],error=c['gravity_origin_error_deg']) for c in states],
            camera_gravity_reconstructed=camera_gravity,
            consecutive_tower_GT_available=len(di)==32,motion_authority='consecutive GT anchors; intermediate tower poses unavailable for 64-frame inputs',features=vals))
    auc=[]
    for dataset in ('all','arkitscenes','scannet','scannetppv2'):
      for comparison,classes in [('gross_vs_pass',('gross',)),('fail_vs_pass',('gross','moderate'))]:
       for name in out[0]['features']:
        pos=[r['features'][name] for r in out if r['distance_class'] in classes and (dataset=='all' or r['dataset']==dataset) and r['features'][name] is not None]
        neg=[r['features'][name] for r in out if r['distance_class']=='pass' and (dataset=='all' or r['dataset']==dataset) and r['features'][name] is not None]
        value=float(np.mean((np.array(pos)[:,None]>np.array(neg)[None,:])+.5*(np.array(pos)[:,None]==np.array(neg)[None,:]))) if pos and neg else None
        auc.append(dict(dataset=dataset,comparison=comparison,feature=name,n_positive=len(pos),n_pass=len(neg),auc=value,
            positive_median=float(np.median(pos)) if pos else None,pass_median=float(np.median(neg)) if neg else None))
    return out,auc

def main():
    OUT.mkdir(exist_ok=True);(CAM/'out').mkdir(exist_ok=True)
    rows,checks=load_camera();gt,pins=gt_load(rows)
    meta={r['scene']:r for r in read(FRAMES)['captures']};dense=read(DENSE)['captures']
    r5=read(CAP/'score_t2/CAMERAS_T2_R5.json')['captures'];dist={k:next((r['geometry'] for r in v if r['geometry']),None) for k,v in r5.items()}
    split=read(CAP/'score_t1/CAMERA_SPLIT.json')
    # Validate every primary distance camera against the supplied frozen geometry and R7 fit.
    rec=Records(CAP/'t1.gz',CAP/'t1ret/CAPTURE.json');n=0
    distance_gt_caps={r['capture'] for r in split['captures']}
    for r in rec:
        if r['pass_index']!=0 or not r['geometry']:continue
        if r['capture'] not in distance_gt_caps:continue
        assert np.allclose(r['geometry']['camera_to_world_metric'],dist[r['capture']]['camera_to_world_metric'],atol=1e-5,rtol=0);n+=1
    assert not rec.report['salvaged'];inputs[str(CAP/'t1.gz')]=rec.report['raw_sha256'];inputs[str(CAP/'t1ret/CAPTURE.json')]=sha(CAP/'t1ret/CAPTURE.json')
    caps,replay,examples,poses=audit_rows(rows,gt,dist)
    tables,loss,bins,rooms=score_tables(rows)
    for r in rows:
        m=meta[r['capture']];d=dense[m['native']]
        assert r['dense_count']==len(d['frames']) and r['fps']==m['fps']
        assert r['source_indices']==m['anchor_indices']
        assert [d['frames'][s]['sha256'] for s in d['anchor_slots']]==[f['sha256'] for f in m['frames']]
    feature_rows,auc=features(gt,caps,rows,dist,split,meta,dense,poses)
    missing=[dict(capture=cap,items_per_step={str(s):sum(r['capture']==cap and r['step']==s for r in rows) for s in (544,400)}) for cap in sorted({r['capture'] for r in rows}-set(gt))]
    comparisons=[];sc={r['capture']:r for r in split['captures']}
    for cap in sorted({r['capture'] for r in rows}):
        c=[r for r in caps if r['capture']==cap];classes={str(r['step']):r.get('class_range') for r in c}
        comparisons.append(dict(capture=cap,camera_reconstruction_classes=classes,distance_class=category(sc[cap]['rigid_fit']) if cap in sc else None,
            same_400_544=classes['400']==classes['544'] if all(classes.values()) else None,
            same_camera_distance={s:cl==[category(sc[cap]['rigid_fit'])] for s,cl in classes.items() if cl and cap in sc}))
    sanitized=[{k:r[k] for k in ('item_key','step','capture','dataset','room','type','score','asked_frames','scale','class','classification_authority','pair_error','served_asked_pair_error')} for r in rows]
    # Preserve selected heads separately as replay evidence, explicitly labelled own-head output.
    write(CAM/'out/REPLAY_EVIDENCE_R8.json',dict(description='Logged own heads are not served tower poses. No question text.',
        rows=[{k:r[k] for k in ('item_key','step','capture','pose9','gravity','calls')} for r in rows]))
    result=dict(schema='camera-items-r8',status='partial: full served tower poses absent',score_field='arms.tower.score',
        equal_fields=['arms.tower.scores.answer','raw.arms.tower.output.scores.answer'],score_agreements=checks,
        bootstrap=dict(seed=20261120,draws=10000,room_key='raw.arms.tower.room_key',rooms=rooms,item_weighted=True),
        classification='Approximate reconstruction from frozen distance tower geometry only; no labels inferred from logged own poses.',
        tables=tables,loss=loss,asked_pair_bins=bins,served_asked_pair_bins=served_bins(rows),captures=caps,items=sanitized,no_GT=missing,comparisons=comparisons,
        replay=replay,reconstruction_rounding_differences=examples,GT_provenance=pins,distance_validation=rec.report,distance_geometry_matches=n)
    feat=dict(schema='capture-features-r8',captures=feature_rows,AUC=auc,
        auc_definition='P(feature(failure)>feature(pass)) + 0.5 ties; signed direction retained; no threshold selection.',
        cohort='Unique captures; AUC uses the 38 distance GT captures only. Additional camera GT captures lack served tower classes.',
        caveat='Motion on 32 GT anchors is not motion on consecutive 64 tower inputs; image orientation describes projected world up, not an inferred EXIF rotation.')
    write(OUT/'CAMERA_ITEMS_R8.json',result);write(OUT/'CAPTURE_FEATURES_R8.json',feat)
    paths=[ROOT/'analyze_round8.py',ROOT/'analyze_round5.py',ROOT/'camera_split_round7.py',ROOT/'project_round6.py',ROOT/'round7_common.py',ROOT/'gt/v2.py',ROOT/'gpkg/capture_io.py']
    for directory in ['work/payload/tree/student_pilot','work/payload/b/e2e_reader']:
        names=['camera_targets.py','carrier_c1_routing.py','tower_read.py','_tower_native.py','carrier_c1_data.py','pose_samples.py'] if 'student_pilot' in directory else ['real.py','generate.py','geometry.py','parity.py','servers.py','core.py']
        paths += [ROOT/directory/n for n in names]
    paths += [ROOT/'work/payload/tree/student_pilot/g3t_vendor/vggt/utils/load_fn.py']
    for p in paths:inputs[str(p)]=sha(p)
    write(CAM/'out/INPUTS_R8.json',dict(files=inputs,GT_members=pins,runtime_seconds=time.monotonic()-START,max_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    print(json.dumps(dict(camera_class_counts=[{k:r[k] for k in ('step','capture_class','items','captures')} for r in tables if r['dataset']=='all' and r['type']=='all'],replay=replay,unique_features=len(feature_rows),distance_checked=n,runtime_seconds=time.monotonic()-START)))
if __name__=='__main__':main()
