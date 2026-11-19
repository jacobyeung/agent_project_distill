"""One-process native mode-q fixture, with explicit constructor/host boundaries."""
from pathlib import Path
from copy import deepcopy
from contextlib import ExitStack
from unittest.mock import patch
import json, os, sys, sqlite3, tarfile, traceback, gzip
L=Path(__file__).resolve().parents[2]; B=L/'work/build21'; O=B/'proofs/capacity'; T=L/'work/tree_r1'
O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(T),str(B),str(L/'work/build17'),str(L/'work/n1fix2')]
os.environ.update(R2_FIXTURES=str(L/'fixtures'),R2_PROOFS=str(O),LANE_TEST_OUTPUT=str(L/'work/tmp'),S1_CPU_REHEARSAL='1',
    R1_MOUNT=str(O),STUDENT_ORCHARD='1',STUDENT_MODEL_ROOT=str(O/'model'),STUDENT_FRAME_ROOT_MAP=json.dumps({'/data2':str(O/'data2root')}))
import tempfile
tempfile.tempdir=str(L/'work/tmp')
from capacity_tools import guard, population, pose_manifests
from monitor9 import Monitor
m=Monitor(T)
from student_pilot.p3_provenance import file_pin, load, pinned, digest, source_files, sha256
from tests.test_r2_build_n1 import write, configuration, sampling
from tests.test_r2_n1fix import sealed_functions
from tests.test_carrier_c1_run import RunnerTests
from native_assets21 import assets, PatchGridProcessor
from student_pilot import carrier_c1_run as C, carrier_c1_data as D, carrier_c1_routing as R
from student_pilot import r1_handover as H, r1_persisted as P, s1_pool
from student_pilot.carrier_c1 import CarrierC1
from launch_r1 import production_proof as Q, p_export_receipt as E, p_handover_receipt as HR
import torch
torch.set_num_threads(8)
torch.set_num_interop_threads(1)
import numpy as np
from PIL import Image,ImageDraw

class FixtureProcessor(PatchGridProcessor):
    def apply_chat_template(self,messages,**kwargs):
        prefix='<|im_start|>user\n<video>'+messages[0]['content'][1]['text']+'<|im_end|>\n<|im_start|>assistant\n<think>\n'
        return prefix if len(messages)==1 else prefix+messages[-1]['content'].removeprefix('<think>\n')+'<|im_end|>\n'

def processor(root):
    p=FixtureProcessor(root);p._student_pilot_student='qwen35';return p

def retain_open(path,mode='r',*a,**kw):
    return original_open(path,mode.replace('x','w') if path.is_relative_to(O) else mode,*a,**kw)
original_open=Path.open
original_mkdir=Path.mkdir
def retain_mkdir(path,mode=0o777,parents=False,exist_ok=False):
    return original_mkdir(path,mode,parents,True if path.is_relative_to(O) else exist_ok)

def manifest_for_rows(root,rows,stream,family=None):
    from tests.test_r2_data_path import manifest
    return file_pin(manifest(root,rows,stream,family))

def host():
    base=assets(O/'model')
    mp=write(O/'model.json',dict(kind='base',base_identity='fixture',rehearsal=True,
        root=str(O/'model'),files={p.name:sha256(p) for p in (O/'model').iterdir() if p.is_file()}))
    im=Image.new('RGB',(32,32),'white');draw=ImageDraw.Draw(im)
    draw.rectangle((2,10,10,20),fill='red');draw.rectangle((20,10,28,20),fill='blue');im.save(O/'f.png')
    (O/'data2root').mkdir(exist_ok=True);im.save(O/'data2root/f.png')
    fp=dict(file_pin(O/'data2root/f.png'),path='/data2/f.png')
    row=dict(qid='v0',dataset='d1',scene='scene9997_00',canonical='scannet/scene9997_00',
        question_type='object_rel_direction_easy',answer='A',
        target='<think>\nLocate: the red square is seen in frame 1.\nLocate: the blue square is seen in frame 2.\nRelate: the red square is left of the blue square.\n</think>\n\nA',
        student_input=dict(question='Is the red square left or right of the blue square?',options=['A. left','B. right'],
            frames=[fp]*32,frame_indices=list(range(32)),timestamps=[i/10 for i in range(32)],fps=10,total_num_frames=32))
    division=write(O/'division.json',dict(schema='diagnostic-whole-scene-division-v1',training_only=True,
        train_scenes=['d1/scene9997_00'],heldout_scenes=['d1/scene9998_00']))
    camera=dict(embed_dim=16,num_heads=2,trunk_depth=1,refine_iterations=1,weight_gravity=.05,
        weight_scale=.04,weight_focal=2.,supervision=division)
    depth=dict(weight=.05,d_proj=16,mlp_hidden=16,num_heads=2,context_depth=1,vit_layers=[1,2,3],num_points_per_frame=1)
    camera['point_depth']=depth
    model=CarrierC1(base,camera,depth,2,D.C1_A,'final',True,frame_layout='duplicate',depth_fov_source='pose_head')
    model.trace_program_version='3.13'
    cfg=configuration()
    from trace_format.contracts import HEADING_PLANE_MIN_DEFAULT
    cfg['heading_plane_min']=HEADING_PLANE_MIN_DEFAULT
    for key in ('depth_init','checkpoint_disk_guard','admission','milestone_gate','align','pose_exclusions','report_exclusions','exclude_qids','r2_build2'):
        cfg.pop(key,None)
    cfg.update(base_identity='fixture',trace_program_version='3.13',depth_fov_source='pose_head',routing_opener_init='keep',
        ground_target_filter=True,scene_division=division,output=str(O/'train'),
        preparation_output=str(O/'prepare'),min_pixels=16,max_pixels=16)
    cfg.pop('tool_mode_flag',None)
    prior=load(B/'inputs/config.json')
    for key in ('dev_scene_exclusions','benchmark_scene_exclusions','exclusions','remove_files','r2_identity','r2_all_stream_exclusions','r2_scene_rebuild','scene_coverage'):
        if key in prior:cfg[key]=prior[key]
    cfg['r1_training'].update(room_authority=prior['r1_training']['room_authority'],registry=prior['r1_training']['registry'],component_rows=prior['r1_training']['component_rows'])
    cfg['recipe']=C.recipe_for(cfg)
    streams={}
    for stream in ('vqa','pointing'):
        r=deepcopy(row);r['qid']=stream+'0'
        if stream=='pointing':
            mask=np.zeros((32,32),dtype=bool);mask[10:21,2:11]=True
            np.savez(O/'mask.npz',mask=mask)
            r['student_input'].update(question='Point to the red square in frame 1.',options=[])
            r['pointing']=dict(kind='gt_instance_mask',frame=1,rgb_sha256=fp['sha256'],instance_id='red',mask=file_pin(O/'mask.npz'))
        src=O/(stream+'.jsonl');population(src,r,stream,guard)
        directory=O/stream
        if not (directory/'receipt.json').exists():
            if (directory/'rows.sqlite').exists():(directory/'rows.sqlite').write_bytes(b'')
            guard(stream+' producer');D.build_stream(file_pin(src),division,directory,stream,training_mode='final',remove_files=cfg['remove_files'],ground_target_filter=stream=='pointing')
        streams[stream]=file_pin(directory/'receipt.json')
    # Real native materializer, using synthetic RGB and metric labels at the frame-host boundary.
    from student_pilot.pose_samples import AUGMENT,SCHEMA,encode_sample
    from student_pilot.r2_materialize import materialize
    poses=np.tile(np.eye(4),(32,1,1));poses[:,0,3]=np.arange(32)*.01
    intr=np.tile([[32.,0,16.],[0,32.,16.],[0,0,1.]],(32,1,1))
    cam,mask,scale,gravity=encode_sample(poses,intr,(32,32),range(32),max_groups=32,all_frames=True)
    pose=deepcopy(row);pose.update(qid='p0',category='camera_pose_only',answer='',target='<think>\n\n</think>\n\n')
    target=dict(camera=cam.tolist(),camera_mask=mask.tolist(),trajectory_scale=scale,gravity=gravity.tolist(),gravity_mask=True,
        point_depth=dict(uv=[[[500.,500.]]]*32,depth=[[2.]]*32,mask=[[True]]*32))
    pose.update(target_record=target,pose_sample=dict(schema=SCHEMA,recording=dict(sampling=dict(variant='all_frames32')),
        frames=32,positions=list(range(32)),temporal_grouping='fused_pairs_all_frames',anchors=list(range(1,33)),
        augment={**AUGMENT,'seed':17,**dict.fromkeys(('brightness','contrast','saturation','hue','blur_p','grayscale_p'),0)},
        metric=True,**{k:target[k] for k in ('camera','camera_mask','trajectory_scale','gravity','gravity_mask')}))
    pose_inputs=pose_manifests(O,pose,manifest_for_rows)
    pose_children=[]
    for group in range(2):
        directory=O/('pose_store'+str(group))
        if not (directory/'receipt.json').exists():
            guard('pose producer '+str(group));materialize([p['path'] for p in pose_inputs[group*4:(group+1)*4]],directory,dense=False,
                limits={'pose':190_000_000,'membership':20_000_000})
        native=load(directory/'receipt.json')['streams']['pose']
        pose_children.append(write(O/('pose'+str(group)+'.json'),dict(schema='decoupled-v-preparation-v1',rehearsal=True,model=mp,
            inputs=dict(division=division),database=native['database'],count=native['count'],settings=dict(camera=camera,
            anchors=list(range(1,33)),temporal_grouping='fused_pairs_all_frames'))))
    streams['pose']=write(O/'pose.json',dict(schema='c1-pose-mix-v1',division=division,
        sources=[dict(kind='rows',receipt=pin,frame_prefix=None) for pin in pose_children]))
    events=[dict(kind='plan',text='Call: measure camera displacement between frame 1 and frame 25.'),
        dict(kind='tool_call',token='<move from=1 to=25>',call_id='move'),
        dict(kind='tool_response',name='move',text='dx = -0.24 m, dy = +0.00 m, dz = +0.00 m, distance = 0.24 m',call_id='move',
             values={'move.delta':{'value':[-.24,0.,0.]},'move.distance':{'value':.24}}),
        dict(kind='canonical_text',text='\nStep: the printed distance is 0.24 m.')]
    answer='<answer>0.24</answer>';text,spans=R.render(events,answer)
    rr=deepcopy(row);rr.update(qid='r0',schema='derivgen-row-v2',form='spec-v3.8-calculator-v2',head_layout='per_frame',infrastructure_only=False,
        events=events,tool_output_spans=spans,answer=answer,gt_answer='0.24',target=text,question_type='camera_displacement',
        question='How far in meters did the camera move from frame 1 to frame 25?',
        provenance=dict(canonical=row['canonical'],alias='d1/scene9997_00',source_row_sha256=digest(row),frame_indices=list(range(32))))
    rgb=write(O/'rgb.json',dict(frames=[dict(fp,source_index=i) for i in range(32)],fps=10,total_num_frames=32))
    rr['provenance']['rgb_manifest']=rgb
    population(O/'routing.jsonl',rr,'routing',guard)
    index=write(O/'rgb_index.json',dict(manifests={rgb['sha256']:rgb['path']}))
    if not (O/'routing19/receipt.json').exists():
        guard('routing producer');R.build_routing_stream(file_pin(O/'routing.jsonl'),index,division,O/'routing19',str(O/'model'),exclusions=cfg['exclusions'])
    streams['routing']=file_pin(O/'routing19/receipt.json');cfg['streams']=streams
    from student_pilot.s1_routing import legacy_replay
    with sqlite3.connect(O/'routing19/rows.sqlite') as db:
        for (encoded,) in db.execute('SELECT row FROM rows LIMIT 2000'):legacy_replay(json.loads(encoded))
    ex={}
    for name in ('dev_s1','eval_rooms','room_release_gate'):
        path=O/(name+'.tsv');path.write_text('');pin=file_pin(path);ex[name]=dict(list=pin['path'],list_sha256=pin['sha256'],rows=0)
    for name,key,pin in [('dev_s1','withhold',cfg['dev_scene_exclusions']),('eval_rooms','v2',cfg['benchmark_scene_exclusions'])]:
        ex[name].update({key:pin['path'],key+'_sha256':pin['sha256']})
    with (L/'work/build16/proofs/traces/units.jsonl').open() as source:packed=json.loads(next(source))['native_row']
    from student_pilot.ground_rows import pack
    packed=pack(dict(packed['ground_record'],suffix=packed['target']),packed['provenance'])
    from student_pilot.s1_routing import frame_request
    needed=frame_request(packed);native_scene=needed['d']+'/'+needed['s']
    div=load(division['path']);div['train_scenes'].append(native_scene);division=write(O/'division.json',div)
    cfg['scene_division']=division
    # Fixture metadata rebinds the division to the host's complete synthetic scene set.
    for name,pin in streams.items():
        value=load(pin['path'])
        if name=='pose':
            value['division']=division
            for source in value['sources']:
                child=load(source['receipt']['path']);child['inputs']['division']=division
                source['receipt']=write(Path(source['receipt']['path']),child)
        else:value['division']=division
        streams[name]=write(Path(pin['path']),value)
    with gzip.open(O/'pool.gz','wt') as f:f.write(json.dumps(packed)+'\n')
    pool=write(O/'pool.json',dict(schema='dose-pool-s1-manifest-v2',sets=[dict(name='source',status='final',
        rows_per_type={packed['question_type']:1},files=dict(packed=dict(file_pin(O/'pool.gz'),rows=1,bytes=(O/'pool.gz').stat().st_size)))],exclusions=ex))
    s1_pool.prepare(pool,O/'selected',cfg['remove_files'])
    from student_pilot.r2_scene_bindings import rebuild,SOURCES
    scene_sources={name:(load(streams['pose']['path'])['sources'][0 if name=='pose_a2v3' else 1]['receipt'] if stream=='pose' else streams[stream]) for name,stream in SOURCES.items()}
    scene_spec=dict(pool_manifest=pool,remove_files=cfg['remove_files'],sources={
        name:dict(receipt=pin,rows=load(pin['path'])['database'],count=load(pin['path'])['count'])
        for name,pin in scene_sources.items()})
    scene=rebuild(scene_spec,cfg,O/'scene')
    cfg.update(r2_scene_rebuild=file_pin(O/'scene/2.json'),scene_coverage=scene['scene_coverage'])
    with gzip.open(O/'frames.gz','wt') as f:
        for i in range(32):f.write(json.dumps(dict(d='d1',s='scene9997_00',i=i,sha256=fp['sha256'],path='/data2/k6tk/'+fp['sha256'][:2]+'/'+fp['sha256']+'.png'))+'\n')
        for i in needed['i']:f.write(json.dumps(dict(d=needed['d'],s=needed['s'],i=i,sha256=fp['sha256'],path='/data2/k6tk/'+fp['sha256'][:2]+'/'+fp['sha256']+'.png'))+'\n')
    image_path=O/'data2root/k6tk'/fp['sha256'][:2]/(fp['sha256']+'.png');image_path.parent.mkdir(parents=True,exist_ok=True);im.save(image_path)
    with gzip.open(O/'plan.gz','wt') as f:json.dump(dict(v={'scene9997_00':dict(g='d1',raw_n=32),needed['s']:dict(g=needed['d'],raw_n=max(needed['i'])+1)}),f)
    cfg['s1_routing']=dict(schema='s1-routing-inputs-v1',selection=file_pin(O/'selected/receipt.json'),catalog={},
        frame_map=file_pin(O/'frames.gz'),frame_plan=file_pin(O/'plan.gz'))
    cfg['s1_route_policy']=None
    cfg['route_table']={'camera_displacement':'route','object_abs_distance':'route'}
    sources={};manifests={};catalog={}
    for kind in ('recovery','absolute_distance','units'):
        pin=manifest_for_rows(O/kind,[],'routing',kind);value=load(pin['path'])
        sources[kind]=dict(source=value['rows']);manifests[kind]=pin;catalog[kind]=dict(source=value['rows'],qids=[])
    cfg['r1_training'].update(row_sources=write(O/'row_sources.json',sources),routing_inputs=manifests,
        source_membership=write(O/'catalog.json',dict(schema='r1-source-catalog-v1',sources=catalog)))
    binding,_=sampling(O/'sampler');card=load(binding['card']['path']);card.update(counting_admission='procedure_only_v1',weight_scale=.04,vehicle='N',leg='R1')
    card['cells'][2]['type']='camera_displacement'
    cfg['r1_training']['mix']=write(O/'card.json',card);cfg['r2_sampling']=binding
    from student_pilot.source_seal import inventory,archive,create
    files=inventory(T);archive(T,O/'source.tar',files,compress=True)
    closure={str(p.relative_to(T)):sha256(p) for p in source_files([Path(C.__file__)])}
    cfg['code']=write(O/'code.json',create(T,O/'source.tar',closure,{}))
    cfg['recipe']=C.recipe_for(cfg)
    from student_pilot.r1_rooms import census
    audit,_=census(cfg);room=write(O/'room.json',audit)
    return cfg,model,mp,camera,depth,room

def produce(cfg,model,mp,camera,depth,step):
    root=O/str(step);root.mkdir(exist_ok=True)
    n=deepcopy(cfg);p=deepcopy(cfg)
    for key in ('r1_training','r2_sampling','preparation','geometry_connector'):p.pop(key,None)
    p['camera_overrides']={'weight_focal':2.0}
    p['h1']={**p.get('h1',{}),'stop_after_step':600}
    p['output']=str(root/'6ed2c7aa')
    p['init_artifact']=dict(load(L/'work/build17/inputs/config.json')['init_artifact'])
    p['init_artifact']['artifact']=file_pin(L/'work/n1fix2/inputs/init_artifact.json')
    p['recipe']=C.recipe_for(p)
    ident=H.export_identity(p)
    p['preparation_output']=str(root/'p_prepare')
    guard('P native preparation '+str(step))
    C.prepare(p)
    prep=file_pin(root/'p_prepare/receipt.json')
    ident=H.export_identity(p)
    p['preparation']=prep
    ppin=write(root/'config.json',p)
    commit=load(prep['path'])['trainer_commit']
    bound=dict(config_sha256=ident,preparation=prep,world_size=4,trainer_commit=commit)
    functions=sealed_functions();write(root/'binding.json',bound)
    with RunnerTests().local_collectives(),patch('student_pilot.fsdp_training.publication_state',return_value=model.state_dict()):
        if step==600:complete=functions['checkpoint'](root/'checkpoint',model,torch.optim.AdamW(C.parameter_groups(model)),bound,step)
        functions['export'](root/'export',model,model,p,step)
    ap=file_pin(root/'export/artifact.json')
    run=dict(config=ppin,preparation=prep,binding=file_pin(root/'binding.json'))
    if step==600:run['checkpoint']=complete
    hp=(HR if step==600 else E).produce(run,ap,root/'h.json',job_id='6ed2c7aa',trainer_commit=commit)
    receipt=load(hp['path']);paths={}
    # Metadata is persisted; checkpoint state shards stay solely at the producer.
    weight_names={}
    with tarfile.open(root/'weights.tar','w:gz') as archive:
        for label,pin in receipt['pins'].items():
            if label.startswith('export/') or label in ('heads','full_weights'):
                name='e/'+label.removeprefix('export/') if label.startswith('export/') else ('e/full_weights.json' if label=='full_weights' else 'heads.pt')
                weight_names[name]=pin['sha256'];archive.add(pin['path'],arcname=name,recursive=False)
    with tarfile.open(root/'weights.tar','r:gz') as archive:
        for member in archive:
            path=root/'persisted'/member.name;path.parent.mkdir(parents=True,exist_ok=True)
            with archive.extractfile(member) as source,path.open('wb') as target:
                for block in iter(lambda:source.read(1<<20),b''):target.write(block)
            paths[weight_names[member.name]]=str(path)
    for label,pin in receipt['pins'].items():
        if pin['sha256'] in paths:continue
        if label.startswith('checkpoint/') and not label.startswith('checkpoint/rng'):
            paths[pin['sha256']]=str(root/'absent'/pin['sha256']);continue
        path=root/'persisted'/pin['sha256'];path.parent.mkdir(exist_ok=True)
        path.write_bytes(Path(pin['path']).read_bytes());paths[pin['sha256']]=str(path)
    n['init_artifact']=dict(artifact=ap,lm='full',heads=['pose','depth','frame_embeddings'])
    n['r1_training'].update(p_run=run,handover_receipt=hp,persisted_files=paths,proof_mode='q',donor_config_sha256=ident)
    return n

def twins(request,cfg,mp,root):
    records={}
    def invoke(name,n,extra=None):
        r=deepcopy(request);r['config']=write(root/(name+'.json'),n);r['staged_pins'][0]=r['config']
        if extra:extra(r)
        prior=root/'twins'/name/'p'
        if prior.exists():prior.rename(prior.parent/('retained_'+str(len(list(prior.parent.glob('retained_*'))))))
        records[name]=Q.run(r,root/'twins'/name)
    n=deepcopy(cfg);n['r1_training']['handover_receipt']['sha256']='0'*64;invoke('wrong_h_pin',n)
    n=deepcopy(cfg);card=load(n['r1_training']['mix']['path']);card['leg']='other'
    n['r1_training']['mix']=write(root/'other_card.json',card);invoke('non_R1',n)
    n=deepcopy(cfg);card=load(n['r1_training']['mix']['path']);card['vehicle']='other'
    n['r1_training']['mix']=write(root/'other_vehicle.json',card);invoke('non_N',n)
    invoke('missing_model_manifest',deepcopy(cfg),lambda r:r['staged_pins'].__setitem__(2,dict(mp,path=str(root/'missing_manifest.json'))))
    n=deepcopy(cfg);n['remove_files']=n['remove_files'][:-1];invoke('without_z',n)
    n=deepcopy(cfg);sources=load(n['r1_training']['row_sources']['path'])
    sources['units']['source']=write(root/'heldout_slice.json',dict(qid='heldout',canonical='arkitscenes/41069175'))
    n['r1_training']['row_sources']=write(root/'heldout_sources.json',sources);invoke('k1_slice',n)
    receipt=load(cfg['r1_training']['handover_receipt']['path'])
    label=next(k for k in receipt['pins'] if k.startswith('export/') and k.endswith('.safetensors'))
    path=Path(cfg['r1_training']['persisted_files'][receipt['pins'][label]['sha256']]);original=path.read_bytes()
    path.write_bytes(original[:-1]+bytes([original[-1]^1]))
    try:invoke('altered_shard',deepcopy(cfg))
    finally:path.write_bytes(original)
    if receipt['step']==400:
        n=deepcopy(cfg);n['r1_training']['proof_mode']='train';invoke('export_in_training_config',n)
    else:
        n=deepcopy(cfg);receipt.update(schema=E.SCHEMA,stop_step=600,checkpoint_status=E.NO_CHECKPOINT)
        receipt['pins']={k:v for k,v in receipt['pins'].items() if not k.startswith('checkpoint')}
        n['r1_training']['p_run'].pop('checkpoint');n['r1_training']['persisted_files']={}
        n['r1_training']['handover_receipt']=write(root/'export_at_stop_receipt.json',receipt)
        invoke('export_at_stop',n)
    write(root/'TWINS.json',records)
    return records

def main():
    summary=dict(status='INCOMPLETE',GO=False,stand_ins=['Synthetic RGB frame host and catalogs','Tiny native model dimensions',
        'PatchGridProcessor HF processor constructor','CPU local publication collectives'],milestones={})
    try:
        with ExitStack() as stack:
            stack.enter_context(patch.object(Path,'open',retain_open));stack.enter_context(patch.object(Path,'mkdir',retain_mkdir))
            stack.enter_context(patch.object(C,'processor_for',processor))
            stack.enter_context(patch('student_pilot.decoupled_v_run.processor_for',processor))
            real_uname=os.uname();host_uname=os.uname_result((real_uname.sysname,'fixture-host',real_uname.release,real_uname.version,real_uname.machine))
            stack.enter_context(patch.object(os,'uname',return_value=host_uname))
            stack.enter_context(patch.dict(os.environ,STUDENT_R2_FRAME_HOST='1'))
            guard('host');cfg,model,mp,camera,depth,room=host()
            for step in (400,600):
                guard('milestone '+str(step));n=produce(cfg,model,mp,camera,depth,step);root=O/str(step)
                config=write(root/'request_config.json',n)
                staged=[config,room,mp]+[file_pin(p) for p in (O/'model').iterdir() if p.is_file()]
                request=dict(config=config,staged_pins=staged,room_audit=room,frame_roots=[str(O)],weights=True,milestone=step,memory_gib=16)
                write(root/'request.json',request)
                prior=root/'q/p'
                if prior.exists():prior.rename(root/'q'/('retained_'+str(len(list((root/'q').glob('retained_*'))))))
                events=[]
                from student_pilot import s1_routing,r1_routing,s1_admission,r1_population,r1_loader
                from launch_r1 import p_opener_witness
                with ExitStack() as observed:
                    for module,name in [(Q,'verify_staging'),(D,'build_stream'),(s1_routing,'build'),(r1_routing,'compose_native'),
                            (s1_admission,'admit'),(r1_population,'bind_prepared'),(r1_loader,'production_audit'),
                            (P,'verify'),(P,'admission'),(p_opener_witness,'produce'),(C,'init_from_artifact'),(Q,'forward')]:
                        original=getattr(module,name);label=module.__name__+'.'+name
                        def wrapped(*args,_original=original,_label=label,**kwargs):
                            event=dict(function=_label,result='running');events.append(event)
                            if _label.endswith(('.build_stream','.build','.compose_native')):guard(_label)
                            print(json.dumps(dict(event='stage_start',function=_label)),flush=True)
                            try:value=_original(*args,**kwargs)
                            except Exception as error:event.update(result='REFUSE',error=type(error).__name__+':'+str(error));raise
                            event['result']='PASS';return value
                        observed.enter_context(patch.object(module,name,wrapped))
                    result=Q.run(request,root/'q')
                result['stage_events']=events;write(root/'q/RESULT.json',result)
                summary['milestones'][str(step)]=result
                if os.environ.get('CAPACITY_TWINS')=='1':summary.setdefault('twins',{})[str(step)]=twins(request,n,mp,root)
                print(step,result.get('status'),result.get('refusal'),flush=True)
    except Exception as error:
        summary.update(refusal=type(error).__name__+':'+str(error),traceback=traceback.format_exc())
        print(summary['traceback'],flush=True)
    summary['complete_native_fixture']=len(summary['milestones'])==2 and all(v['status']=='ADMIT' for v in summary['milestones'].values())
    summary['twins_all_refuse']=all(v.get('status')=='REFUSE' for rows in summary.get('twins',{}).values() for v in rows.values())
    summary['status']='ADMIT' if summary['complete_native_fixture'] and summary['twins_all_refuse'] else 'REFUSE'
    write(O/'RESULT.json',summary);m.save(O)
    raise SystemExit(0 if summary['status']=='ADMIT' else 1)

if __name__=='__main__':main()
