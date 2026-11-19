"""Non-training qualification of a staged population and a donor export."""
from copy import deepcopy
from pathlib import Path
import os,resource
from student_pilot.p3_provenance import digest,file_pin,load,pinned,write


def direct_pins(value):
    if isinstance(value,dict):
        if 'path' in value and 'sha256' in value:
            yield {k:value[k] for k in ('path','sha256')}
        for item in value.values():
            yield from direct_pins(item)
    elif isinstance(value,list):
        for item in value:
            yield from direct_pins(item)


def verify_staged(config_pin, request):
    """Authenticate every declared staged byte before native preparation imports."""
    inventory=load(pinned(request['inventory']))
    if inventory.get('schema')!='r1-proof-inventory-v1' or not inventory.get('files'):
        raise ValueError('R1_PROOF_INVENTORY_REQUIRED')
    seen={}
    for item in inventory['files']:
        pin={k:item[k] for k in ('path','sha256')}
        path=pinned(pin)
        if path.stat().st_size!=item['bytes'] or pin['path'] in seen:
            raise ValueError('R1_PROOF_INVENTORY_DIFFERS')
        seen[pin['path']]=pin['sha256']
    # Follow declared metadata pins, never reinterpret databases or weight shards.
    pending=[config_pin,*direct_pins({k:v for k,v in request.items() if k!='inventory'})]
    checked=set()
    while pending:
        pin=pending.pop();key=(pin['path'],pin['sha256'])
        if key in checked:continue
        if seen.get(pin['path'])!=pin['sha256']:
            raise ValueError('R1_PROOF_PIN_NOT_STAGED:'+pin['path'])
        checked.add(key);path=pinned(pin)
        if path.suffix=='.json':
            try:value=load(path)
            except ValueError:continue  # Pinned JSONL remove records use .json too.
            pending.extend(direct_pins(value))
    return dict(files=len(seen),closure_pins=len(checked),inventory=request['inventory'])


def room_gate(cfg, pin):
    """Require a complete independently pinned scene audit, never a partial census."""
    report=load(pinned(pin))
    expected={k:v['source']['sha256'] for k,v in load(pinned(cfg['r1_training']['row_sources'])).items()
              if k in ('recovery','absolute_distance','units')}
    if (report.get('schema')!='r1-room-audit-v1' or report.get('complete') is not True
            or report.get('sources')!=expected or report.get('division')!=cfg['scene_division']
            or report.get('remove_files')!=cfg['remove_files'] or report.get('unknown_rows')!=0
            or report.get('remaining_hits')!={'k1':0,'r0':0,'outside_train':0}):
        raise ValueError('R1_PROOF_ROOM_AUDIT_INCOMPLETE')
    authorities=report.get('authorities',{})
    expected_hashes={'k1':'4d4736cf64e496a184d36d74d710e76d1673429e28790613794867ac077048a9',
                    'r0':'bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3'}
    for key,sha in expected_hashes.items():
        if authorities.get(key,{}).get('sha256')!=sha:
            raise ValueError('R1_PROOF_ROOM_AUTHORITY_DIFFERS:'+key)
        pinned(authorities[key])
    return pin


def bind_handover(cfg, export, output):
    """Produce the explicit map and let N's unchanged reader decide the milestone."""
    from student_pilot import r1_handover as H,r1_training as R
    from student_pilot.carrier_c1_run import identity
    from student_pilot.source_seal import binding
    from launch_r1.p_opener_witness import produce
    required={'artifact','config','binding','preparation','checkpoint','handover_receipt'}
    if set(export)!=required:
        raise ValueError('R1_PROOF_EXPORT_FILES_REQUIRED')
    for pin in export.values():pinned(pin)
    artifact=load(pinned(export['artifact']))
    if type(artifact.get('step')) is not int or artifact['step'] not in (400,600):
        raise ValueError('R1_PROOF_EXPORT_STEP_REQUIRED')
    current=deepcopy(cfg)
    current['init_artifact']={**current['init_artifact'],'artifact':export['artifact'],'lm':'full'}
    current['routing_opener_init']='keep'
    value=current['r1_training']
    value.update(p_run={k:export[k] for k in ('config','binding','preparation','checkpoint')},
                 handover_receipt=export['handover_receipt'],donor_config_sha256=artifact['config_sha256'])
    current['routing_vocabulary']=produce(current,Path(output)/'v.json')
    source,_,actual,_=H.donor(current,artifact)
    target=R.target_identity(current)
    value.update(continuation_identity=target['config_identity'],store_hashes=target['stores'])
    expected=R.boundary(current,artifact['step'])
    write(Path(output)/'m.json',dict(schema='r1-handover-map-v1',artifact_sha256=export['artifact']['sha256'],
        step=artifact['step'],source=actual,target={k:expected[k] for k in actual}))
    value['handover_mapping']=file_pin(Path(output)/'m.json')
    step=R.start(current)
    # Only initialization/progress metadata changes; prepared streams and sampler
    # remain byte-bound to the native producer and the completed loader audit.
    receipt=load(pinned(cfg['preparation']))
    receipt.update(r1_training=value,config_sha256=identity(current),init_artifact=current['init_artifact'],
                   routing_vocabulary=current['routing_vocabulary'],routing_opener_init='keep')
    receipt['source_seal']=binding(load(pinned(current['code'])),receipt['config_sha256'])
    write(Path(output)/'p.json',receipt);current['preparation']=file_pin(Path(output)/'p.json')
    write(Path(output)/'c.json',current)
    return current,step


def first_batches(cfg, step, weights):
    """Every logical rank runs the first resumed plan, without an optimizer."""
    import torch
    from student_pilot import carrier_c1_run as C
    from student_pilot.r1_mix import plans
    artifact=load(pinned(cfg['init_artifact']['artifact']))
    expected=pinned(artifact['full_weights']).parent.resolve()
    if Path(weights).resolve()!=expected:
        raise ValueError('R1_PROOF_WEIGHTS_PATH_DIFFERS')
    receipt,manifest=C.prepared(cfg)
    processor=C.processor_for_receipt(manifest,receipt)
    model=C.load_model(manifest,receipt,processor).cpu().train()
    model.gradient_checkpointing_enable()
    reader=C.Rows(receipt,processor)
    losses=[]
    try:
        plan=next(plans(cfg['r2_sampling'],{s:reader.count(s) for s in ('pose','vqa','routing','pointing')},1000,start_step=step))
        for rank in range(cfg['recipe']['world_size']):
            totals={};numbers={}
            for (stream,_),fetched in zip(plan,C.fetch_plan(reader,model,plan,rank,device=torch.device('cpu'),distributed=False),strict=True):
                if fetched is None:raise ValueError('R1_PROOF_FIRST_BATCH_REFUSED')
                batch,target,audit=fetched
                with torch.no_grad():
                    result=model(batch,target,stream=stream)
                loss=result['loss']
                if not torch.isfinite(loss):raise ValueError('R1_PROOF_NONFINITE_LOSS')
                totals[stream]=totals.get(stream,0.)+float(loss.detach());numbers[stream]=numbers.get(stream,0)+1
            losses.append(dict(rank=rank,loss_per_stream={s:totals[s]/numbers[s] for s in totals},microbatches=numbers))
        return dict(status='PASS',absolute_step=step,ranks=losses,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                    device='cpu',optimizer_steps=0)
    finally:reader.close()


def run(config_pin, request_pin, output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    result=dict(status='REFUSE',GO=False,phases=[],absolute_resume_step=None,forward={'status':'NOT_REQUESTED'})
    try:
        request=load(pinned(request_pin))
        if os.environ.get('CUDA_VISIBLE_DEVICES','') or os.uname().nodename.startswith('trinity'):
            raise ValueError('R1_PROOF_FRAME_HOST_CPU_REQUIRED')
        result['staged']=verify_staged(config_pin,request);result['phases'].append('verify_staged')
        cfg=load(pinned(config_pin));room_gate(cfg,request['scene_audit'])
        from student_pilot.s1_admission import admit
        from student_pilot.r1_population import bind_prepared
        from student_pilot.r1_loader import production_audit
        # This sentinel permits data preparation only. It cannot validate as a
        # sampling binding and is replaced before audit, handover or forward.
        cfg['r2_sampling']={'schema':'r1-population-pending-v1'}
        write(output/'i.json',cfg);(output/'p').mkdir(exist_ok=True)
        prepared=admit(file_pin(output/'i.json'),output/'p',request['frame_roots'],threads=8,memory_gib=20,prepare_only=True)
        result['phases'].extend(['s1_routing.build','r1_routing.compose_native','carrier_c1_run.prepare'])
        produced=bind_prepared(load(pinned(prepared['config'])),output/'n')
        result['phases'].append('r1_population.bind_prepared');cfg=load(pinned(produced))
        result['loader']=production_audit(cfg,output/'a');result['phases'].append('r1_loader.production_audit')
        cfg,step=bind_handover(cfg,request['export'],output/'h')
        result['absolute_resume_step']=step;result['phases'].append('r1_handover.progress')
        result['config']=file_pin(output/'h/c.json')
        if request.get('weights'):
            result['forward']=first_batches(cfg,step,request['weights']);result['phases'].append('full_forward_loss')
        result['status']='ADMIT'
    except (ValueError,KeyError,TypeError,OSError,RuntimeError,MemoryError) as error:
        result['reason']=type(error).__name__+':'+str(error)
    write(output/'RESULT.json',result)
    return result
