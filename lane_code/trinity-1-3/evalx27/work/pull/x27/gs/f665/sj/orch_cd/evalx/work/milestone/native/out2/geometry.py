"""Frozen raw G3T caches and checkpoint-specific scale/gravity for native reads."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from routed import trainer_row,source_pins

def captures():return load(VENDOR/'r3/FRAMES.json')['captures']

def validate_dense(c,e):
    import numpy as np
    frames=e['frames'];slots=e['anchor_slots'];indices=[p['index'] for p in frames]
    n=int(c['group'][3:])
    if len(frames)!=n or len(slots)!=32 or slots[0]!=0 or slots[-1]>=n or min(slots)<0:
        raise ValueError('Dense frame count/anchor slots differ')
    if any(type(i) is not int for i in indices+slots) or any(np.diff(indices)<=0) or any(np.diff(slots)<=0):
        raise ValueError('Dense indices/slots must increase')
    if [indices[i] for i in slots]!=c['anchor_indices']:raise ValueError('Dense/LM anchor mismatch')
    return indices,slots

def convert(state,own_depth,gravity,source_hw,output):
    """Use the tree's frozen estimator and camera conversion, exactly one scale."""
    import numpy as np
    install_tree()
    from student_pilot.tower_scale import estimate_scale
    from student_pilot.camera_targets import to_gravity_reference_frame
    from student_pilot.ground_profiles import load_geometry
    from student_pilot.scene_state import FrameMap
    own_depth=np.asarray(own_depth)
    if own_depth.shape!=(32,51,51) or not np.isfinite(own_depth).all() or np.any(own_depth<=0):
        raise ValueError('Own depth must be finite positive 32x51x51')
    H,W=map(int,source_hw)
    if min(H,W)<=0:raise ValueError('Invalid native raster')
    scale,_,_=estimate_scale(state.depth_grid,state.depth_conf_grid,own_depth)
    raw=state.raw_pose9[state.anchor_slots]
    R,t,fov=to_gravity_reference_frame(raw,gravity)
    C=np.repeat(np.eye(4)[None],32,axis=0);C[:,:3,:3]=R;C[:,:3,3]=t
    K=np.zeros((32,3,3));K[:,0,0]=W/(2*np.tan(fov[:,1]/2));K[:,1,1]=H/(2*np.tan(fov[:,0]/2))
    K[:,0,2]=W/2;K[:,1,2]=H/2;K[:,2,2]=1
    A=np.repeat(np.diag([W/1000,H/1000,1.])[None],32,axis=0)
    anchors=state.frame_indices[state.anchor_slots]
    output=local(output)
    if output.exists():raise ValueError('Geometry destination exists')
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('wb') as f:
        np.savez(f,profile='scaled_g3t_depth',depth_unit='unscaled',pose_unit='unscaled',
            reference_source_frame=anchors[0],K=K,canvas_to_source=A,camera_to_world=C,
            scale=scale,depth_scale_count=0,pose_scale_count=0,anchor_frame_indices=anchors,
            depth_grid=state.depth_grid,grid_uv=state.grid_uv)
    geometry=load_geometry(output,FrameMap(tuple(anchors.tolist())),'tower_scaled')
    if geometry.depth_scale_count!=1:raise ValueError('Geometry scaled more than once')
    return dict(scale=float(scale),geometry_identity=geometry.identity,depth_scale_count=geometry.depth_scale_count)

def validate_manifest(m,artifact):
    if m.get('schema')!='s1-predicted-geometry-v1' or m.get('checkpoint')!=artifact:
        raise ValueError('Geometry must bind the exact LEG checkpoint; older parent-conditioned exports are refused')
    if m.get('producer')!='legs1-own-scale-gravity-v1' or m.get('producer_sha256')!=sha(__file__):
        raise ValueError('Unverified geometry producer')
    if not m.get('videos'):raise ValueError('Empty geometry manifest')
    return m

def tower(args):
    if not args.device.startswith('cuda:'):raise ValueError('Full frozen tower requires an assigned card')
    import numpy as np
    from PIL import Image
    install_tree()
    from student_pilot.tower_read import FrozenG3TTower,WEIGHTS_SHA256,CONFIG_SHA256,REVISION
    if sha(args.weights)!=WEIGHTS_SHA256 or sha(args.config)!=CONFIG_SHA256:raise ValueError('Frozen G3T weights/config differ')
    dense=load(args.dense_manifest)
    if dense.get('schema')!='legs1-dense-frames-v1':raise ValueError('Dense frame manifest schema differs')
    cs=captures()
    if set(dense['captures'])!={c['native'] for c in cs}:raise ValueError('Dense capture membership differs')
    for c in cs:validate_dense(c,dense['captures'][c['native']])
    dest=local(args.dest);dest.mkdir(parents=True,exist_ok=False);entries={}
    model=None
    for c in sorted(cs,key=lambda c:c['group']):
        e=dense['captures'][c['native']];indices,slots=validate_dense(c,e)
        images=[Image.open(checked(p)).convert('RGB') for p in e['frames']]
        if model is None or model.dense_frames!=len(images):
            model=None
            model=FrozenG3TTower(dict(weights_path=str(local(args.weights)),config_path=str(local(args.config)),
                device=args.device,dense_frames=len(images),depth_chunk_size=8,dtype='bf16'))
        s=model.run(dict(tower_native_frames=images,tower_frame_indices=indices,tower_anchor_slots=slots,frame_indices=c['anchor_indices']))
        p=dest/(digest(c['native'])+'.npz')
        with p.open('wb') as f:np.savez(f,raw_pose=s.raw_pose9,depth_grid=s.depth_grid,depth_conf_grid=s.depth_conf_grid,
            frame_indices=s.frame_indices,anchor_slots=s.anchor_slots,grid_uv=s.grid_uv,source_hw=[images[0].height,images[0].width])
        entries[c['native']]=pin(p)
        del images,s
    dump(dest/'RAW_G3T.json',dict(schema='legs1-raw-g3t-cache-v1',captures=entries,
        weights_sha256=WEIGHTS_SHA256,config_sha256=CONFIG_SHA256,revision=REVISION,dense_manifest=pin(args.dense_manifest)))

def prepare(args):
    if not args.device.startswith('cuda:'):raise ValueError('Real checkpoint preparation requires an assigned card')
    import numpy as np
    import torch
    install_tree()
    from evalpath import runtime
    from student_pilot import carrier_c1_run as trainer
    from student_pilot.carrier_c1_decode import _prepare_decode
    from student_pilot.ground_context import closed_adapters
    from student_pilot.tower_read import TowerState,WEIGHTS_SHA256,CONFIG_SHA256,REVISION
    import read_runtime
    raw=load(args.raw_tower)
    if (raw.get('schema'),raw.get('weights_sha256'),raw.get('config_sha256'),raw.get('revision'))!=(
            'legs1-raw-g3t-cache-v1',WEIGHTS_SHA256,CONFIG_SHA256,REVISION):raise ValueError('Raw G3T provenance differs')
    cfg=load(args.config);artifact=dict(path=str(local(args.export)),sha256=args.sha256);checked(artifact)
    if load(args.export).get('step')!=args.step:raise ValueError('Export step differs')
    selected=dict(root=str(TREE),sources={n.removeprefix('student_pilot/'):h for n,h in source_pins().items() if n.startswith('student_pilot/')})
    model,processor,info=read_runtime.load_model(pin(args.config),artifact,pin(args.data_receipt),
        device=args.device,selected_trainer=selected)
    dest=local(args.dest);dest.mkdir(parents=True,exist_ok=False);videos={};records=[]
    tasks=rows(VENDOR/'r3/TASKS.jsonl');by_native={}
    for t in tasks:by_native.setdefault(t['native'],t)
    prefill=closed_adapters(torch.no_grad()(_prepare_decode))
    for c in captures():
        p=checked(raw['captures'][c['native']]);state=TowerState.from_npz(p)
        row=trainer_row(by_native[c['native']],c,args.frames_root,verify=True)
        batch=move_batch(runtime.prompt_batch(processor,row,cfg,'routed'),args.device)
        if state.frame_indices[state.anchor_slots].tolist()!=c['anchor_indices']:raise ValueError('Tower capture anchors differ')
        own=prefill(model,processor,batch,max_new_tokens=16384).heads
        if own.depth_map is None or own.gravity is None:raise ValueError('Checkpoint lacks own depth/gravity')
        axis=torch.as_tensor(state.grid_uv.copy(),device=own.depth_map.device)
        yy,xx=torch.meshgrid(axis,axis,indexing='ij');uv=torch.stack((xx,yy),-1).reshape(1,-1,2).expand(32,-1,-1)
        with torch.no_grad():depth=own.depth_head.query(own.depth_map,uv).double().cpu().numpy().reshape(32,51,51)
        clip=row['student_input']['video_identity']['video_sha256'];output=dest/(clip+'.npz')
        with np.load(p,allow_pickle=False) as z:hw=z['source_hw']
        record=convert(state,depth,own.gravity,hw,output);record.update(native=c['native'],raw=pin(p),
            conditioning_question_id=row['qid'],prefill_sha256=digest(batch['input_ids'].cpu().tolist()))
        records.append(record);videos[clip]=pin(output)
        del own,batch,depth
    dump(dest/'GEOMETRY_MANIFEST.json',dict(schema='s1-predicted-geometry-v1',videos=videos,checkpoint=artifact,
        producer='legs1-own-scale-gravity-v1',producer_sha256=sha(__file__),raw_tower=pin(args.raw_tower),
        config=pin(args.config),data_receipt=pin(args.data_receipt),records=records,load_receipt=info))

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('tower')
    for name in ('dense-manifest','weights','config','device','dest'):q.add_argument('--'+name,required=True)
    q=sub.add_parser('prepare')
    for name in ('raw-tower','config','export','sha256','frames-root','device','dest','data-receipt'):q.add_argument('--'+name,required=True)
    q.add_argument('--step',type=int,required=True)
    a=p.parse_args();{'tower':tower,'prepare':prepare}[a.command](a)
if __name__=='__main__':main()
