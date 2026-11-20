"""REPORT6 geometry and REPORT9 content binding for independently rebuilt GT."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from round2 import *
from audit_functions import project_box, box_metrics, analyze_object, summary, MODES, Records
from preflight import FRAME_ROOTS
from collections import defaultdict
CAP=Path('/scratch/jjyeung/orch_n30/cont_ops24_c/cap')

def geometry_check(z,dataset):
    pose=z['c2w'].astype(float);rot=pose[:,:3,:3]
    ortho=float(np.max(np.abs(rot@rot.transpose(0,2,1)-np.eye(3))))
    det=float(np.max(np.abs(np.linalg.det(rot)-1)))
    bottom=float(np.max(np.abs(pose[:,3]-[0,0,0,1])))
    finite=all(np.isfinite(z[k]).all() for k in ['depth','c2w','K_frames','obb_axes','obb_lengths','obb_centroid'])
    invalid=int(np.count_nonzero((z['inst']>=0)&(z['depth']<=0)))
    unknown=set(np.unique(z['inst']).tolist())-set(z['ids'].tolist())-{-1}
    rows=[];total=inside=0
    H,W=z['depth'].shape[1:];yy,xx=np.indices((H,W))
    for f in range(32):
        K=z['K_frames'][f];R=pose[f,:3,:3]
        d=z['depth'][f].astype(float)
        cam=np.stack([(xx+.5-K[0,2])/K[0,0]*d,(yy+.5-K[1,2])/K[1,1]*d,d],-1)
        world=cam@R.T+pose[f,:3,3]
        for k,iid in enumerate(z['ids']):
            mask=z['inst'][f]==iid;ys,xs=np.nonzero(mask)
            if not len(xs):continue
            axes=z['obb_axes'][k].reshape(3,3);lengths=z['obb_lengths'][k]*(2 if dataset=='scannetppv2' else 1)
            box=dict(center=z['obb_centroid'][k],axes=axes,full_lengths=lengths)
            p=project_box(box,pose[f],K,z['inst'][f],iid)
            metrics=box_metrics(p['projected_bbox'],[xs.min(),ys.min(),xs.max()+1,ys.max()+1])
            local=np.abs((world[mask]-z['obb_centroid'][k])@axes.T)
            slack=1e-4
            if dataset=='arkitscenes':
                # PNG source is 4/5 the output raster. Bound the exact displacement
                # between output pixel center and the nearest sampled source center.
                sx=(np.floor(xs*.8)+.5)/.8;sy=(np.floor(ys*.8)+.5)/.8
                shift_cam=np.column_stack([(xs+.5-sx)/K[0,0]*d[mask],(ys+.5-sy)/K[1,1]*d[mask],np.zeros(len(xs))])
                slack=.030001+np.abs((shift_cam@R.T)@axes.T)
            contained=np.all(local<=lengths/2+slack,axis=1)
            total+=len(xs);inside+=int(contained.sum())
            rows.append(dict(slot=f,instance_id=int(iid),visible_pixels=len(xs),contained_pixels=int(contained.sum()),bbox_iou=metrics['bbox_iou'],mask_bbox_coverage=metrics['mask_bbox_coverage']))
    bbox=sum(r['bbox_iou']>.25 for r in rows)
    containment=inside/total if total else None
    passed=finite and max(ortho,det,bottom)<=1e-4 and invalid==0 and not unknown and np.all(z['depth']>=0) and len(rows)>0 and bbox/len(rows)>.5 and containment>=.95
    return dict(passed=bool(passed),pose_orthogonality_max=ortho,pose_det_error_max=det,pose_bottom_error_max=bottom,finite=bool(finite),labeled_nonpositive_depth=invalid,unknown_ids=sorted(unknown),visible_instance_frames=len(rows),bbox_iou_gt025_count=bbox,bbox_iou_gt025_share=bbox/len(rows) if rows else None,contained_pixels=inside,labeled_pixels=total,containment_share=containment,instance_frames=rows)

def run_checks(selected=None):
    builds=read(OUT/'BUILDS.json');manifest={m['scene']:m for m in read(ROOT/'DEVS1_MANIFEST.json')['captures']}
    previous=read(OUT/'CAPTURE_CHECKS.json') if selected is not None else None
    if selected is not None:
        builds={c:b for c,b in builds.items() if c in selected}
    data={};results={};objects=[]
    for canonical,build in builds.items():
        if not build['built']:continue
        with np.load(build['path']) as z:data[canonical]={k:z[k] for k in z.files}
        z=data[canonical];m=manifest[canonical]
        hashes=[]
        for f in m['frames']:
            p=next((root/f['path'] for root in FRAME_ROOTS if (root/f['path']).is_file()),None)
            hashes.append(dict(index=f['index'],path=str(p) if p else None,expected=f['sha256'],verified=p is not None and sha(p)==f['sha256']))
        identity=z['frame_indices'].tolist()==m['anchor_indices']==[f['index'] for f in m['frames']] and all(f['verified'] for f in hashes)
        results[canonical]=dict(geometry=geometry_check(z,canonical.split('/')[0]),identity_passed=identity,frames=hashes,arms={},binding_calls=[])
        print('GEOMETRY',canonical,results[canonical]['geometry']['passed'],results[canonical]['geometry']['bbox_iou_gt025_share'],results[canonical]['geometry']['containment_share'],flush=True)
    receipts={}
    for arm in ['t1','t2']:
        receipt=read(CAP/(arm+'ret/CAPTURE.json'));records=Records(CAP/(arm+'.gz'),receipt)
        for row in records:
            c=row['capture']
            if c not in data or row['pass_index']!=0 or (arm=='t2' and row.get('arm')!='points'):continue
            z=data[c];m=manifest[c]
            assert row['source_indices']==z['frame_indices'].tolist()
            if arm=='t2':
                hashes=[f['sha256'] for f in m['frames']];b=row['binding']
                assert b['frame_hashes_match'] and b['bound_anchor_sha256']==b['expected_anchor_sha256']==hashes
            for obj in row['objects']:
                matches=[int(i) for i,label in zip(z['ids'],z['labels']) if str(label).strip().lower()==obj['name'].strip().lower()]
                results[c]['binding_calls'].append(dict(arm=arm,item_id=row['item_id'],name=obj['name'],candidates=matches))
                if len(matches)!=1:continue
                r=analyze_object(obj,row['item_id']+':'+obj['name'],matches[0],z['inst'],row['source_indices'],arm)
                r.update(capture=c,arm=arm);objects.append(r)
        assert not records.report['salvaged']
        receipts[arm]=records.report
        print('BINDING ARM',arm,'objects',sum(o['arm']==arm for o in objects),flush=True)
    for c,r in results.items():
        modes=MODES+(['rot90_ccw','rot90_cw'] if data[c]['inst'].shape[1:]==(320,240) else [])
        for arm in ['t1','t2']:
            oo=[o for o in objects if o['capture']==c and o['arm']==arm]
            r['arms'][arm]=dict(objects=len(oo),**summary([f for o in oo for f in o['frames']],modes))
        r['binding_passed']=all(a['same_median'] is not None and a['same_median']>0 and not a['changed'] for a in r['arms'].values())
        r['colmap_passed']=builds[c].get('evidence',{}).get('colmap',{}).get('passed',True)
        r['passed']=r['identity_passed'] and r['geometry']['passed'] and r['binding_passed'] and r['colmap_passed']
        print('CAPTURE',c,r['passed'],[(arm,a['same_median'],a['best_alternative_median']) for arm,a in r['arms'].items()],flush=True)
    if previous is not None:
        results={**previous['captures'],**results}
        objects=[o for o in previous['objects'] if o['capture'] not in selected]+objects
    write(OUT/'CAPTURE_CHECKS.json',dict(captures=results,objects=objects,receipts=receipts,rules_sha256=sha(OUT/'CHECK_RULES.md')))

if __name__=='__main__':run_checks()
