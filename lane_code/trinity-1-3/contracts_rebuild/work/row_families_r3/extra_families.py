"""Additional native production entry points; executed by render_arms.py."""
from student_pilot import carrier_c1_routing as C

for typ in ('camera_displacement','camera_movement_direction','camera_rotation'):
    for kind in ('landscape','nadir_positive'):
        for i in range(3):
            def camera(typ=typ,kind=kind,i=i):
                from derivgen.camera_rows import camera_rows
                from scipy.spatial.transform import Rotation
                contract,_=fixture(kind);poses=contract.camera_to_world.copy()
                # A clear translation and turn margin avoids admission-boundary fixtures.
                for k in range(32):
                    poses[k,:3,3]=[k*.02,k*.12,0.]
                    poses[k,:3,:3]=Rotation.from_euler('z',k*.8,degrees=True).as_matrix()@poses[k,:3,:3]
                E=np.linalg.inv(poses)@poses[0];p=np.zeros((32,9));p[:,:3]=E[:,:3,3];p[:,3:7]=Rotation.from_matrix(E[:,:3,:3]).as_quat();p[:,7:]=[.9,1.1]
                frames=[dict(path=str(W/f'rgb/frame{k}.png'),source_index=k,sha256=hashlib.sha256(f'fixture{k}'.encode()).hexdigest()) for k in range(32)]
                clip=dict(recording_id='synthetic-camera',dataset='scannet',scene='r6_fixture_00',frames=frames,total_num_frames=32,fps=1,gt_pose9=p.tolist(),gt_up=poses[0,2,:3].tolist())
                manifest=W/f'camera_manifest_{args.arm}_{kind}_{typ}_{i}.json'
                manifest.write_text(json.dumps(dict(frames=frames,fps=1,total_num_frames=32)))
                clip['rgb_manifest']=dict(path=str(manifest),sha256=hashlib.sha256(manifest.read_bytes()).hexdigest())
                q=dict(qid=f'camera/{typ}/{kind}/{i}',question_type=typ,question=f'What is the {typ} between frame 1 and frame {12+i*2} of 32?',options=['A. left','B. right','C. forward','D. backward'] if typ=='camera_movement_direction' else [])
                rows,refusals=camera_rows(clip,seed=17,per_type=1,distribution={},questions=[q])
                if not rows:raise ValueError(json.dumps(refusals))
                row=rows[0]
                # Manifest path is fixture transport, not row semantics. Use the common
                # immutable source pin so OFF/base includes identical provenance bytes.
                row['provenance']['rgb_manifest']['path']=str(W/'camera_manifest.json')
                return row
            capture('camera/'+typ,f'{kind}/{i}','derivgen.camera_rows.camera_rows',camera)

sys.path.insert(0,str(tree/'tests/headcall'))
for typ in ('distance','closest','direction','motion'):
    for i in range(3):
        def headcall(typ=typ,i=i):
            import rows_fixture as F
            from headcall.rows import prepare_row
            row=getattr(F,typ+'_row')(qid=f'headcall/{typ}/{i}')
            entry=dict(kind='headcall',head_calls=row['head_calls'])
            pd=dict(uv=[[[0.,0.] for _ in range(8)] for _ in range(16)],depth=[[0.]*8 for _ in range(16)],mask=[[False]*8 for _ in range(16)])
            return prepare_row(dict(row,_headcall=entry,_camera=dict(point_depth=pd)))
        capture('headcall/'+typ,f'fixture/{i}','headcall.rows.prepare_row + headcall.derive.render',headcall)

for typ in ('camera_displacement','camera_movement_direction'):
    for i in range(3):
        def hp(typ=typ,i=i):
            from student_pilot.head_programs import render_hp_target,format_move
            q=f'What is the camera motion between frame 2 and frame {8+i*2} of 32?'
            call=dict(name='move',**{'from':2,'to':8+i*2})
            response=format_move((.2,.1,1.+i*.1))
            target=render_hp_target(typ,q,['A. Forward','B. Backward','C. Left','D. Right'] if typ.endswith('direction') else [],[2,8+i*2],[str(k) for k in range(16)],call,response)
            return dict(target=target,events=[dict(call=json.dumps(call),response=response)])
        capture('control/head_program_'+typ,f'fixture/{i}','student_pilot.head_programs.render_hp_target',hp)

for mode in ('TR','AO'):
    for i in range(3):
        def trace_count(mode=mode,i=i):
            from student_pilot.trace_targets import render_count,lint_row
            row=dict(qid=f'timestamp-count/{i}',category='object_counting',answer=str(i+1),student_input=dict(options=[],frame_indices=list(range(32)),timestamps=list(range(32)),fps=1),primitives=dict(kind='object_counting',frame_count=32,name='chair',instances=[dict(frames=[2+k,6+k]) for k in range(i+1)]))
            row['target']=render_count(row,mode);row['lint']=lint_row(row,mode)
            return row
        capture('control/timestamp_count_'+mode,f'fixture/{i}','student_pilot.trace_targets.render_count',trace_count)

# True failed-ground rows use native status execution and the native event renderer.
for status in ('not_seen','different_name_retry','open_vocabulary','normalized_phrase'):
    for i in range(3):
        def recovery(status=status,i=i):
            clip=clip_for('landscape',i)
            names=['missing chair'] if status=='not_seen' else ['missing chair','table'] if status=='different_name_retry' else ['ornate ceramic planter'] if status=='open_vocabulary' else ['chairs']
            if status=='open_vocabulary':
                clip.geo.labels[0]=names[0]
            session=D.make_session(backend,clip,[],B.FusedBoxProvider(),multi_instance=True)
            events=[dict(kind='ground_trace_start',trace_revision='3.14'),dict(kind='canonical_text',text='<think>\n')]
            for j,name in enumerate(names):
                call=f'<ground obj="{name}" mode="box">';body=session.execute(call)
                if j:events.append(dict(kind='canonical_text',text='\n'))
                events.extend([dict(kind='ground_call',call_id=str(j),token=call+'\n'),dict(kind='ground_response',call_id=str(j),text=G.wrap(body))])
            events.append(dict(kind='canonical_text',text='\nI answer from the visible scene.\n</think>\n<answer>1</answer>'))
            from student_pilot.ground_rows import render_ground
            target,spans,segments=render_ground(events,'1')
            return dict(target=target,events=events,source_events=session.events,spans=spans,segments=segments,question='Locate '+', '.join(names)+'.',candidate_phrases=names)
        capture('recovery/'+status,f'fixture/{i}','derivgen.ground_v313.Session.execute + student_pilot.ground_rows.render_ground',recovery)

for kind in ('gt_instance_mask','gt_absent'):
    for i in range(3):
        def pointing(kind=kind,i=i):
            from student_pilot.carrier_c1_data import mask_target
            mask=np.zeros((24,32),bool)
            if kind=='gt_instance_mask':mask[4+i:13+i,6:18]=True
            path=W/f'pointing_{kind}_{i}.npz'
            if not path.exists():np.savez(path,mask=mask)
            target,audit=mask_target(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()),kind=kind)
            return dict(target=target,audit=audit)
        capture('pointing/'+kind,f'raster/{i}','student_pilot.carrier_c1_data.mask_target',pointing)

for kind in ('landscape','nadir_positive'):
    for i in range(3):
        def live(kind=kind,i=i):
            from fixtures_contracts import session as live_session, response
            from student_pilot.e2e_routing_rows import adapt_generated
            s=live_session(fixture(kind)[1](),W/f'live_{args.arm}_{kind}_{i}',policy=True)
            calls=['<ground obj="chair" mode="box">','<ground obj="table" mode="box">','<gap a="chair" b="table" rule="box_grid_5cm">']
            events=[]
            for call in calls:
                body=response(s,call)
                events.append(dict(call=call,response=body if body.startswith('<tool_response>') else G.wrap(body)))
            suffix='<think>\n'+'\n'.join(e['call']+'\n'+e['response'] for e in events)+'\nI use the measured distance.\n</think>\n<answer>0.66</answer>'
            source=dict(qid=f'live/{kind}/{i}',type='object_abs_distance',question='How far is the chair from the table?',options=[],answer='0.66',spec_version='3.14',suffix=suffix,events=events)
            row=adapt_generated(source,dict(question=source['question'],options=[]),dataset='synthetic',scene='fixture')
            row['source_events']=s.events
            return row
        capture('runtime/mdg_distance',f'{kind}/{i}','student_pilot.carrier_c1_decode.respond_state + student_pilot.e2e_routing_rows.adapt_generated',live)

# The camera pool wrapper needs its pinned exclusion authority. The production
# per-row renderer can still be exercised without bypassing that pool-level gate.
for typ in ('camera_displacement','camera_movement_direction','camera_rotation'):
    for kind in ('landscape','nadir_positive'):
        for i in range(3):
            def camera_leaf(typ=typ,kind=kind,i=i):
                from derivgen.camera_rows import _row,_Geometry
                from scipy.spatial.transform import Rotation
                contract,_=fixture(kind);poses=contract.camera_to_world.copy()
                for k in range(32):
                    poses[k,:3,3]=[k*.02,k*.12,0.]
                    poses[k,:3,:3]=Rotation.from_euler('z',k*.8,degrees=True).as_matrix()@poses[k,:3,:3]
                E=np.linalg.inv(poses)@poses[0];p=np.zeros((32,9));p[:,:3]=E[:,:3,3];p[:,3:7]=Rotation.from_matrix(E[:,:3,:3]).as_quat();p[:,7:]=[.9,1.1]
                clip=dict(recording_id='synthetic-camera',dataset='scannet',scene='r6_fixture_00',frames=[dict(source_index=k) for k in range(32)],gt_pose9=p.tolist(),gt_up=poses[0,2,:3].tolist(),rgb_manifest=dict(path='synthetic-rgb-manifest',sha256='a'*64))
                return _row(clip,typ,1,12+i*2,_Geometry(clip).pair(1,12+i*2))
            capture('camera_leaf/'+typ,f'{kind}/{i}','derivgen.camera_rows._row',camera_leaf)

for operation in ('surface_pair','extent_ends'):
    for kind in ('landscape','nadir_positive'):
        for i in range(3):
            def keypoints(operation=operation,kind=kind,i=i):
                clip=clip_for(kind,i)
                session=I.Session(backend,clip.geo,clip.masks,instances=I.GTInstances(clip),multi_instance=False,keypoint_calls=True)
                names=['chair','table'] if operation=='surface_pair' else ['chair']
                calls=[f'<ground obj="{n}">' for n in names]
                for call in calls:session.execute(call)
                def provider(op,names):
                    if op=='surface_pair':
                        clouds=[np.asarray(session.objects[n]['points']['4']) for n in names]
                        from scipy.spatial.distance import cdist
                        a,b=np.unravel_index(cdist(*clouds).argmin(),(len(clouds[0]),len(clouds[1])))
                        positions=[clouds[0][a],clouds[1][b]]
                    else:
                        cloud=np.asarray(session.objects[names[0]]['points']['4']);positions=[cloud[0],cloud[-1]]
                    return dict(status='ok',positions=[p.tolist() for p in positions],frames=[4,4],distance_m=float(np.linalg.norm(positions[1]-positions[0])),observed_surface_points=True)
                session.keypoint_provider=provider
                call='<surface_pair a="chair" b="table" mode="closest_visible">' if operation=='surface_pair' else '<extent_ends obj="chair" axis="longest_observed">'
                session.execute(call)
                source=dict(qid=f'{operation}/{kind}/{i}',type=operation,question='Measure the chair and table.',options=[],answer='observed',spec_version='3.13',events=session.events)
                source['suffix']='<think>\n'+'\n'.join(e['call']+'\n'+e['response'] for e in session.events)+'\nUse the observed points.\n</think>\n<answer>observed</answer>'
                from student_pilot.e2e_routing_rows import adapt_generated
                row=adapt_generated(source,dict(question=source['question'],options=[]),dataset='synthetic',scene='fixture')
                row['source_events']=session.events
                return row
            capture('keypoints/'+operation,f'{kind}/{i}','derivgen.ground_v313.Session.execute + student_pilot.e2e_routing_rows.adapt_generated',keypoints)

for typ in ('object_abs_distance','object_rel_distance'):
    for kind in ('landscape','nadir_positive'):
        for i in range(3):
            def legacy(typ=typ,kind=kind,i=i):
                clip=clip_for(kind,i)
                item=dict(qid=f'legacy/{typ}/{kind}/{i}',type=typ,question='Which of the table and plant is closest to the chair?',options=['A. table','B. plant'] if typ.endswith('rel_distance') else [],roles=dict(target='chair',cands=['table','plant']) if typ.endswith('rel_distance') else dict(a='chair',b='table'))
                return G.render(item,G.Session(backend,clip.geo,clip.masks),lambda s:len(s.split()))
            capture('legacy_surface/'+typ,f'{kind}/{i}','derivgen.ground_v312.render',legacy)

for i in range(3):
    def recording(i=i):
        from student_pilot.recording_pose import build_row
        contract,_=fixture('landscape')
        source=dict(dataset='scannet',scene='synthetic-recording',pool=list(range(32)),fps=1,total_num_frames=32,pose_count=32)
        poses=dict(c2w=contract.camera_to_world,intrinsics=contract.K,raster_hw=[480,640],world_up=[0,0,1])
        staged=dict(frames=[dict(frame_number=k,path=str(W/f'rgb/f{k}.png'),sha256=hashlib.sha256(str(k).encode()).hexdigest()) for k in range(32)])
        sampler=NS(draw=lambda rng,dataset:('fixed','fixed',list(range(2*i,2*i+16))))
        return build_row(source,poses,staged,sampler,i,17)
    capture('control/recording_pose',f'sensor/{i}','student_pilot.recording_pose.build_row',recording)
