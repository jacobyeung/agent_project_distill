"""GT-grid annotations and one scale-free camera alignment per capture."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from gpkg.capture_io import Records
from gpkg.runtime.c import rle
from gpkg.score_ceiling import name_key


def bind(name,ids,labels):
    matches=[int(i) for i,label in zip(ids,labels) if name_key(label)==name_key(name)]
    return dict(status='bound' if len(matches)==1 else 'U',instance_id=matches[0] if len(matches)==1 else None,
                candidates=matches,reason=None if len(matches)==1 else 'ambiguous label' if matches else 'missing label',
                rule='stage1.name_key: strip and lowercase; no fuzzy matching')


def alignment(reader,gt):
    a,b=np.asarray(reader,float),np.asarray(gt,float)
    if a.shape!=b.shape or a.ndim!=3 or a.shape[1:]!=(4,4) or len(a)<3:
        raise ValueError('paired 4x4 camera arrays required')
    for poses in (a,b):
        if (not np.isfinite(poses).all() or not np.allclose(poses[:,3,:],[0,0,0,1],atol=1e-6)
            or not np.allclose(poses[:,:3,:3]@poses[:,:3,:3].transpose(0,2,1),np.eye(3),atol=1e-5)
            or not np.allclose(np.linalg.det(poses[:,:3,:3]),1,atol=1e-5)):
            raise ValueError('camera poses must be finite rigid SE(3)')
    x,y=a[:,:3,3],b[:,:3,3];xc,yc=x-x.mean(0),y-y.mean(0)
    u,s,vt=np.linalg.svd(xc.T@yc)
    correction=np.diag([1.,1.,np.linalg.det(vt.T@u.T)])
    R=vt.T@correction@u.T;t=y.mean(0)-R@x.mean(0)
    errors=np.linalg.norm(x@R.T+t-y,axis=1)
    rotations=(R@a[:,:3,:3])@b[:,:3,:3].transpose(0,2,1)
    angles=np.degrees(np.arccos(np.clip((np.trace(rotations,axis1=1,axis2=2)-1)/2,-1,1)))
    rms=float(np.sqrt(np.mean(errors**2)));rot_rms=float(np.sqrt(np.mean(angles**2)))
    T=np.eye(4);T[:3,:3]=R;T[:3,3]=t
    rank=int(np.linalg.matrix_rank(xc,tol=1e-8))
    # A line or stationary center sequence cannot determine the rigid rotation.
    accepted=rank>=2 and rms<=.10 and float(angles.max())<=5.
    return dict(performed=True,fit_scale=False,translation_rms_m=rms,translation_residual_m=errors.tolist(),
                rotation_rms_deg=rot_rms,rotation_max_deg=float(angles.max()),rotation_residual_deg=angles.tolist(),
                center_rank=rank,accepted=accepted,reader_world_to_gt_world=T.tolist(),
                rotation_check='every anchor <=5 degrees',reason=None if accepted else 'degenerate centers or alignment residual exceeds ruling')


def full_box(z,index,dataset):
    lengths=np.asarray(z['obb_lengths'][index],float)
    axes=np.asarray(z['obb_axes'][index],float).reshape(3,3)
    center=np.asarray(z['obb_centroid'][index],float)
    if not np.isfinite(np.r_[lengths,axes.ravel(),center]).all() or np.any(lengths<=0):
        return None,'invalid extent',None
    if not np.allclose(axes@axes.T,np.eye(3),atol=1e-6):return None,'invalid axes',None
    factor=2 if dataset=='scannetppv2' else 1
    box=dict(center=center.tolist(),axes=axes.tolist(),full_lengths=(factor*lengths).tolist())
    rule='half extents doubled' if factor==2 else 'both full and half readings' if dataset=='scannet' else 'full extents'
    alt=dict(box,full_lengths=(2*lengths).tolist()) if dataset=='scannet' else None
    return box,rule,alt


def convert_file(path,refs,captured=()):
    scene=refs[0]['capture'];dataset=scene.split('/')[0]
    with np.load(path,allow_pickle=False) as z:
        arrays={k:z[k] for k in ('inst','ids','labels','frame_indices','valid','c2w','K_frames','obb_centroid','obb_lengths','obb_axes')}
    z=arrays;inst=z['inst'];sources=z['frame_indices'].tolist()
    if inst.shape not in ((32,240,320),(32,320,240)) or not np.issubdtype(inst.dtype,np.integer):
        raise ValueError('unsupported GT raster')
    if any(ref['source_indices']!=sources for ref in refs):raise ValueError('exact anchors differ')
    if len(set(z['ids'].tolist()))!=len(z['ids']):raise ValueError('duplicate instance ids')
    portrait=inst.shape[1:]==(320,240)
    orientation=dict(status='U' if portrait else 'identity',transform=None if portrait else 'identity',
                     reason='reader binder opens RGB and routed_features resizes masks; neither establishes portrait GT rotation' if portrait else None)
    visible={str(int(i)):[int(np.count_nonzero(frame==i)) for frame in inst] for i in z['ids']}
    align=dict(performed=False,accepted=False,fit_scale=False,reason='no captured cameras')
    if captured:
        reader=[];truth=[]
        for row in captured:
            if row['source_indices']!=sources:raise ValueError('captured camera anchors differ')
            g=row.get('geometry')
            if not g:continue
            if g['source_indices']!=sources:raise ValueError('geometry source binding differs')
            reader.extend(g['camera_to_world_metric']);truth.extend(z['c2w'])
        if reader:align=alignment(reader,truth)
    inventory=[]
    for i,iid in enumerate(z['ids']):
        box,rule,alt=full_box(z,i,dataset)
        inventory.append(dict(instance_id=int(iid),label=str(z['labels'][i]),visible_pixels=visible[str(int(iid))],
                              stored_lengths=z['obb_lengths'][i].tolist(),full_obb=box,half_extent_obb=alt,extent_rule=rule))
    by_id={v['instance_id']:v for v in inventory};targets={};bindings=[]
    for ref in refs:
        from gt.adapter import names
        for name in names(ref)[0]:
            binding=bind(name,z['ids'],z['labels']);iid=binding['instance_id'];key=ref['item_id']+':'+name
            bindings.append(dict(key=key,**binding))
            target=dict(binding_reviewed=iid is not None,binding=binding,instance_id=iid,
                        annotation_complete=iid is not None and not portrait and bool(z['valid'].all()),
                        world_alignment_reviewed=align['accepted'])
            if iid is not None:
                info=by_id[iid];target.update({k:info[k] for k in ('full_obb','half_extent_obb','extent_rule','visible_pixels')})
                if not info['full_obb']:target['world_alignment_reviewed']=False
                if not portrait:
                    target['masks']={str(s):{'240x320':rle(inst[f]==iid)} for f,s in enumerate(sources)}
            if align.get('reader_world_to_gt_world'):
                target['reader_world_to_gt_world']=align['reader_world_to_gt_world']
            targets[key]=target
    value=dict(schema='gt-adapter-v2',capture=scene,dataset=dataset,source_indices=sources,targets=targets,
               grid=[240,320],orientation=orientation,alignment=align,
               c2w=z['c2w'].tolist(),intrinsics=z['K_frames'].tolist(),valid=z['valid'].tolist(),
               conventions=dict(camera_axes='OpenCV x right, y down, z forward',world='GT metric world',
                                obb_axes='rows; normalizedAxes reshape(3,3)',pixel_centres='edge origin, half'),
               instances=inventory)
    report=dict(capture=scene,path=str(path),raster_shape=list(inst.shape),orientation=orientation,alignment=align,
                instances=inventory,bindings=bindings,valid_frames=int(z['valid'].sum()),
                prediction_grid_rule='routed_features.resize(prediction, (240,320)); GT unchanged')
    return value,report


def convert(staged,manifest,capture=None,receipt=None):
    refs=json.loads(Path(manifest).read_text())['items'];groups=defaultdict(list)
    for ref in refs:groups[ref['capture']].append(ref)
    captured=defaultdict(list);read_report=None
    if bool(capture)!=bool(receipt):raise ValueError('capture requires raw-byte receipt')
    if capture:
        records=Records(capture,receipt);seen=set();ids={r['item_id']:r for r in refs}
        for row in records:
            if row['pass_index']!=0:continue
            if row['item_id'] not in ids or row['item_id'] in seen:raise ValueError('capture membership/duplicate')
            if row['capture']!=ids[row['item_id']]['capture']:raise ValueError('capture binding differs')
            seen.add(row['item_id'])
            captured[row['capture']].append({k:row[k] for k in ('item_id','capture','source_indices','geometry')})
        read_report=records.report
    source=json.loads((ROOT/'kit2/kit/rerun2/gt_staging.json').read_text())['files']
    out={};reports=[];missing=[]
    for entry in source:
        scene=entry['capture'];path=Path(staged)/entry['relative_path']
        if not path.is_file():missing.append(scene);continue
        value,report=convert_file(path,groups[scene],captured[scene]);out[scene]=value;reports.append(report)
    bindings=[b for r in reports for b in r['bindings']]
    return out,dict(schema='gt-adapter-audit-v2',available_captures=len(reports),missing_captures=missing,
                    portrait_unknown=sum(r['orientation']['status']=='U' for r in reports),
                    unique_bindings=sum(b['status']=='bound' for b in bindings),bindings=bindings,files=reports,
                    capture_read=read_report,alignment_fit_scale=False,
                    rulings=dict(grid='predictions resized to GT; GT never upsampled',
                                 extents='ScanNet++ half; ScanNet both; ARKit full',
                                 alignment='one center-only rigid Kabsch per capture; RMS <=0.10m and all rotation residuals <=5deg',
                                 binding='strip/lowercase only; ambiguous stays U'))


def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--staged',default=ROOT.parent/'gt')
    p.add_argument('--manifest',default=ROOT/'kit2/kit/rerun2/items544.json')
    p.add_argument('--capture');p.add_argument('--receipt');p.add_argument('--out',required=True);p.add_argument('--audit',required=True)
    a=p.parse_args(argv);values,report=convert(a.staged,a.manifest,a.capture,a.receipt)
    for path,value in ((a.out,values),(a.audit,report)):
        with Path(path).open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:report[k] for k in ('available_captures','portrait_unknown','unique_bindings','capture_read')}))
