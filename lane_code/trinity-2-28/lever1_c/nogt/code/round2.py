"""Raw-only reproduction and gated builds. All paths remain on local scratch."""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import ctypes
ctypes.CDLL(None).prctl(41, 1, 0, 0, 0)
import hashlib, json, struct, sys, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'code'))
sys.path.insert(0, str(ROOT/'code/builder_cr'))
from raw_functions import load_mesh, build_memberships, membership_boxes
from build_t1_cr import build as build_t1
from build_arkit_cr import build as build_arkit
from preflight import TARGETS, sha

REFROOT = Path('/scratch/jjyeung/orch_n30/cont_ops24_c/gt')
REFS = {'scannet':'scene0166_00', 'scannetppv2':'17c5e6a336', 'arkitscenes':'41069053'}
OUT = ROOT/'out'

def read(p):
    return json.loads(Path(p).read_text())

def write(p, x):
    Path(p).write_text(json.dumps(x, indent=2, allow_nan=False)+'\n')

def relpath(dataset, cid):
    return Path('arkit_gt/gt')/(cid+'.npz') if dataset == 'arkitscenes' else Path('t1_gt/gt')/(dataset+'__'+cid+'.npz')

def source(dataset, cid):
    bases = {'scannet':'data3/shared/datasets/scannet/scans',
             'scannetppv2':'data2/jjyeung/raw_datasets/scannetpp/data',
             'arkitscenes':'data3/shared/datasets/arkitscenes/3dod/Training'}
    return ROOT/'raw'/bases[dataset]/cid

def sens_anchors(path, indices):
    """Seek over compressed payloads and non-anchor poses; decode no RGB/depth."""
    wanted = set(indices); poses = {}; records = {}
    with path.open('rb') as f:
        def unpack(fmt):
            return struct.unpack('<'+fmt, f.read(struct.calcsize('<'+fmt)))
        assert unpack('I')[0] == 4
        n = unpack('Q')[0]; name = f.read(n).decode()
        mats = [np.array(unpack('16f')).reshape(4,4) for _ in range(4)]
        color, depth, cw, ch, dw, dh, shift, count = unpack('2i4IfQ')
        assert max(indices) < count
        assert np.array_equal(mats[1],np.eye(4)) and np.array_equal(mats[3],np.eye(4))
        for i in range(max(indices)+1):
            if i in wanted: poses[i] = np.array(unpack('16f'),np.float32).reshape(4,4)
            else: f.seek(64, 1)
            tc, td, nc, nd = unpack('4Q')
            if i in wanted: records[i] = dict(timestamp_color_us=tc,timestamp_depth_us=td,color_offset=f.tell(),color_bytes=nc,depth_bytes=nd)
            f.seek(nc+nd, 1)
    return np.stack([poses[i] for i in indices]), mats[0][:3,:3], (ch,cw), dict(sensor=name,frame_count=count,decoded_poses=len(poses),decoded_images=0,records=records)

def colmap_check(src, cameras):
    errors=[]
    for line in (src/'iphone/colmap/images.txt').read_text().splitlines():
        x=line.split()
        if len(x)!=10 or line.startswith('#') or not x[-1].endswith('.jpg'): continue
        key=Path(x[-1]).stem
        if key not in cameras: continue
        qw,qx,qy,qz,tx,ty,tz=map(float,x[1:8])
        R=Rotation.from_quat([qx,qy,qz,qw]).as_matrix()
        center=-R.T@np.array([tx,ty,tz])
        errors.append(float(np.linalg.norm(center-np.array(cameras[key]['aligned_pose'])[:3,3])))
    return dict(matched=len(errors),median_m=float(np.median(errors)) if errors else None,
                max_m=max(errors) if errors else None,passed=bool(errors and np.median(errors)<.05))

def prepare_t1(dataset, cid, indices):
    src=source(dataset,cid); asset=OUT/'prepared'/cid; asset.mkdir(parents=True,exist_ok=True)
    if dataset=='scannet':
        vertices,faces=load_mesh(src/(cid+'_vh_clean_2.ply'))
        groups,fi,_,diagnostics=membership_boxes(vertices,faces,read(src/(cid+'_vh_clean_2.0.010000.segs.json')),read(src/(cid+'.aggregation.json')),cid)
        meta=dict(segGroups=groups,provider_axesLengths='half_extents')
        mesh=dict(vertices_world=vertices,faces=faces,face_instance_ids=fi)
        poses,K,source_hw,sens=sens_anchors(src/(cid+'.sens'),indices)
        K=(np.diag([640/source_hw[1],480/source_hw[0],1])@K).astype(np.float32)
        intrinsics=np.repeat(K[None],32,axis=0)
        evidence=dict(box_convention='full extents from raw membership AABB; 2 x provider half extents',sens=sens,axisAlignment_applied=False,instances=diagnostics)
    else:
        vertices,faces=load_mesh(src/'scans/mesh_aligned_0.05.ply')
        groups=read(src/'scans/segments_anno.json')['segGroups']
        seg=np.array(read(src/'scans/segments.json')['segIndices'],np.int64)
        assert len(faces)!=len(vertices)
        assert len(seg) in (len(faces),len(vertices))
        membership=build_memberships(faces,seg,groups,len(seg)==len(faces))
        mesh=dict(vertices_world=vertices,faces=faces,**membership)
        ratios=[]; prepared=[]
        for g in groups:
            iid=int(g.get('objectId',g['id'])); slot=np.flatnonzero(membership['membership_instance_ids']==iid)[0]
            a,b=membership['membership_face_offsets'][slot:slot+2]
            pts=vertices[np.unique(faces[membership['membership_face_indices'][a:b]])].astype(float)
            obb=g['obb']; A=np.array(obb['normalizedAxes']).reshape(3,3); C=np.array(obb['centroid']); L=np.array(obb['axesLengths'])
            if len(pts): ratios.append(dict(id=iid,axis_ratio=(np.max(np.abs((pts-C)@A.T),axis=0)/L).tolist()))
            prepared.append(dict(id=iid,objectId=iid,label=g['label'],obb=dict(obb,axesLengths=(L*.5).tolist())))
        # Raw mesh reaches half the source length; r1313 converts full to half.
        assert max(max(r['axis_ratio']) for r in ratios) < .525
        meta=dict(segGroups=prepared)
        cameras=read(src/'iphone/pose_intrinsic_imu.json')
        selected=[cameras[f'frame_{i:06d}'] for i in indices]
        poses=np.array([c['aligned_pose'] for c in selected],np.float32)
        intrinsics=np.array([np.diag([1/3,1/3,1])@np.array(c['intrinsic']) for c in selected],np.float32)
        evidence=dict(box_convention='v1 stores 0.5 x raw full annotation lengths; double obb_lengths for geometry',mesh_axis_ratios=ratios,colmap=colmap_check(src,cameras))
    np.savez_compressed(asset/'instance_mesh.npz',**mesh)
    np.savez_compressed(asset/'official_cameras.npz',camera_poses=poses,intrinsics=intrinsics,indices=np.array(indices,np.int64),raster_hw=np.array([480,640]))
    write(asset/'instances.json',meta)
    write(asset/'PREPARATION.json',evidence)
    return asset,evidence

def build_raw(dataset,cid,indices,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    if dataset=='arkitscenes':
        listing=read(ROOT/('ref_arkit_listing.json' if cid==REFS[dataset] else 'arkit_listing.json'))[cid]
        result=build_arkit(cid,str(source(dataset,cid)),indices,str(path),depth_names=listing['depth_names'])
        return dict(sha256=result[0],missing_slots=result[1],rotation=result[2],box_convention='annotation full extents; assignment margin 0.03 m',depth_listing_sha256=sha(ROOT/('ref_arkit_listing.json' if cid==REFS[dataset] else 'arkit_listing.json')))
    asset,evidence=prepare_t1(dataset,cid,indices)
    evidence['sha256']=build_t1(str(asset),str(path))
    return evidence

def compare_arrays(actual,reference,dataset):
    result={}
    with np.load(actual) as a,np.load(reference) as b:
        for k in sorted(set(a.files)|set(b.files)):
            if k not in a.files or k not in b.files:
                result[k]=dict(passed=False,reason='key missing');continue
            x,y=a[k],b[k]
            row=dict(actual_dtype=str(x.dtype),reference_dtype=str(y.dtype),actual_shape=list(x.shape),reference_shape=list(y.shape))
            if x.shape!=y.shape:
                row.update(passed=False,reason='shape mismatch');result[k]=row;continue
            equal=x==y
            row.update(exact_equal=bool(equal.all()),different_elements=int((~equal).sum()),elements=x.size)
            valid=x.dtype==y.dtype
            if x.dtype.kind in 'fiu':
                d=np.abs(x.astype(float)-y.astype(float))
                finite=np.isfinite(x).all() and np.isfinite(y).all()
                row.update(max_abs=float(d.max(initial=0)),rmse=float(np.sqrt(np.mean(d*d))))
                tolerant=k=='c2w' or (k=='depth' and dataset!='arkitscenes')
                bound=8*np.finfo(np.float32).eps*np.maximum(1,np.abs(y.astype(float))) if tolerant else np.zeros(y.shape)
                within=d<=bound
                row['outside_tolerance']=int((~within).sum())
                valid=valid and finite and within.all()
                if k=='depth':
                    row['support_mismatch']=int(np.count_nonzero((x>0)!=(y>0)))
                    valid=valid and row['support_mismatch']==0
            else: valid=valid and equal.all()
            row['passed']=bool(valid);result[k]=row
    return dict(passed=all(r['passed'] for r in result.values()),arrays=result)

def reproduce():
    assert 'PIPE_RC 0 0 0 0' in (ROOT/'ref_stage.log').read_text()
    tolerance=OUT/'REPRO_TOLERANCE.md';assert tolerance.is_file()
    missing=[s for s in (ROOT/'ref_list.txt').read_text().splitlines() if not (ROOT/'raw'/s).is_file()]
    assert not missing,missing
    grids={x['canonical']:x['grid'] for x in read(ROOT/'code/PILOT300_INPUTS.json')}
    grids.update({x['scene']:x['anchor_indices'] for x in read(ROOT/'DEVS1_MANIFEST.json')['captures']})
    result={}
    for dataset,cid in REFS.items():
        start=time.monotonic();path=OUT/'reproduction'/relpath(dataset,cid)
        print('BUILD REFERENCE',dataset,cid,flush=True)
        evidence=build_raw(dataset,cid,grids[dataset+'/'+cid],path)
        comparison=compare_arrays(path,REFROOT/relpath(dataset,cid),dataset)
        comparison.update(dataset=dataset,capture=cid,evidence=evidence,actual=str(path),reference=str(REFROOT/relpath(dataset,cid)),seconds=time.monotonic()-start,compared_utc=datetime.now(timezone.utc).isoformat(),tolerance_sha256=sha(tolerance))
        result[dataset]=comparison;write(OUT/'REPRODUCTION.json',result)
        print('REFERENCE RESULT',dataset,comparison['passed'],[(k,v.get('different_elements'),v.get('max_abs')) for k,v in comparison['arrays'].items() if not v['passed']],flush=True)
    return result

if __name__=='__main__':
    reproduce()
