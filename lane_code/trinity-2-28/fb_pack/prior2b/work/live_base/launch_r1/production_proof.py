"""Unsubmitted CPU preparation, persisted handover and full-forward proof."""
from collections import defaultdict
from contextlib import ExitStack
from pathlib import Path
import argparse
import resource
from student_pilot.p3_provenance import load, pinned, write, file_pin


def verify_staging(request):
    entries = request.get('staged_pins')
    if not entries:
        raise ValueError('R1_PROOF_STAGED_PINS_REQUIRED')
    return [file_pin(pinned(pin)) for pin in entries]


def forward(cfg, root, step, device='cpu'):
    from student_pilot.carrier_c1_run import first_batch_check
    records = first_batch_check(cfg, range(cfg['world_size']), root/'f.json',
                                steps=1, device=device, start_step=step)
    grouped = defaultdict(list)
    for row in records:
        if row.get('finite') is not True:
            raise ValueError('R1_PROOF_FORWARD_NONFINITE')
        grouped[row['stream']].append(row['loss'])
    return dict(records=file_pin(root/'f.json'), loss_by_stream={
        k:dict(mean=sum(v)/len(v),min=min(v),max=max(v),count=len(v)) for k,v in grouped.items()},
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        absolute_step=step, ranks=list(range(cfg['world_size'])), device=device)


def bind_handover(cfg, root):
    """Bind continuation to the final prepared stores and produced row plan."""
    from copy import deepcopy
    from student_pilot import r1_training as training, r1_handover as handover
    from student_pilot.carrier_c1_run import identity
    from student_pilot.source_seal import binding
    from student_pilot.p3_provenance import digest
    cfg = deepcopy(cfg)
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    value = cfg['r1_training']
    artifact = load(pinned(cfg['init_artifact']['artifact']))
    source, _, actual, _ = handover.donor(cfg, artifact)
    handover.compare_configs(source, cfg)
    target = training.target_identity(cfg)
    value.update(store_hashes=target['stores'], row_plan_sha256=digest(cfg['r2_sampling']))
    value['continuation_identity'] = training.target_identity(cfg)['config_identity']
    expected = training.boundary(cfg, artifact['step'])
    write(root/'mapping.json', dict(schema='r1-handover-map-v1',
        artifact_sha256=cfg['init_artifact']['artifact']['sha256'], step=artifact['step'],
        source=actual, target={key:expected[key] for key in actual}))
    value['handover_mapping'] = file_pin(root/'mapping.json')
    receipt = load(pinned(cfg['preparation']))
    receipt.update(r1_training=deepcopy(value), config_sha256=identity(cfg))
    sealed = binding(load(pinned(cfg['code'])), receipt['config_sha256'])
    if sealed is not None:
        receipt['source_seal'] = sealed
    write(root/'receipt.json', receipt)
    cfg['preparation'] = file_pin(root/'receipt.json')
    write(root/'config.json', cfg)
    return file_pin(root/'config.json')


def _run(request, output, *, stage=None):
    """Native admission performs build, composition and prepare in that order."""
    root = Path(output).resolve()
    result = dict(status='REFUSE',GO=False,steps=[],forward='not requested')
    environment = ExitStack()
    try:
        result['staged'] = verify_staging(request)
        cfg = load(pinned(request['config']))
        from student_pilot.r1_coverage import deferred
        deferred(cfg, request, read_pins=True)
        card = load(pinned(cfg['r1_training']['mix']))
        if card.get('counting_admission') != 'procedure_only_v1':
            raise ValueError('R1_PROOF_COUNTING_ADMISSION_REQUIRED')
        from student_pilot.r1_coverage import routing_request, validate_binding
        minimal = routing_request(cfg, request)
        if not cfg.get('s1_routing') or not minimal and not cfg['r1_training'].get('routing_inputs'):
            raise ValueError('R1_PROOF_NATIVE_ROUTING_REQUIRED')
        if minimal:
            validate_binding(cfg)
        from student_pilot.r1_rooms import verify_audit
        room = verify_audit(cfg,request['room_audit'])
        result['room_certification'] = dict(scope=room['certifies'],store=room['store'])
        import os
        if os.uname().nodename.startswith('trinity'):
            raise ValueError('R1_PROOF_FRAME_HOST_REQUIRED')
        from .entry import (begin_host, host_environment, check_host_runtime, stage_host,
                            check_host_scene, check_host_selection, finish_host)
        root, job_tmp, host = begin_host(cfg, root, request)
        environment.enter_context(host_environment(job_tmp))
        check_host_runtime(cfg, request, host)
        cfg = stage_host(cfg, root, request, job_tmp, stage=stage, result=host)
        check_host_scene(cfg, host)
        check_host_selection(cfg, root, request, host, record=True)
        if cfg['r1_training'].get('direction_twins'):
            from student_pilot.r1_direction_twins import augment
            from student_pilot.r1_rooms import census
            cfg=augment(cfg,root/'twins')
            audit,_=census(cfg)
            write(root/'twins/room_audit.json',audit)
            cfg['r1_training']['room_audit']=file_pin(root/'twins/room_audit.json')
            verify_audit(cfg,cfg['r1_training']['room_audit'])
            result['augmented_room_audit']=cfg['r1_training']['room_audit']
            result['steps'].append('direction_twins')
            check_host_scene(cfg, host)
        from student_pilot.r1_persisted import verify, scope, init_policy
        value=cfg['r1_training']
        closure=verify(value.get('handover_receipt'),value.get('p_run',{}),
                       cfg['init_artifact']['artifact'],value.get('persisted_files',{}),
                       weights=bool(request.get('weights')),proof_mode=value.get('proof_mode'),init_policy=init_policy(value))
        step = closure['receipt']['step']
        if step not in (400,600) or request.get('milestone',step)!=step:
            raise ValueError('R1_PROOF_EXPORT_STEP_REQUIRED')
        memory = request.get('memory_gib',192)
        if type(memory) is not int or not 8<=memory<=512:
            raise ValueError('R1_PROOF_MEMORY_REQUEST_INVALID')
        device = request.get('device','cpu')
        if device not in ('cpu','cuda:0'):
            raise ValueError('R1_PROOF_DEVICE_INVALID')
        # Refuse missing component evidence before writing capacity-sized stores.
        from student_pilot.r1_training import training_components
        with scope(closure['paths']):
            training_components(cfg['r1_training']['registry'], cfg)
        result['steps'].append('training_components')
        # Produce and bind the witness before native prepare validates the init boundary.
        from .p_opener_witness import produce as opener
        with scope(closure['paths']):
            cfg['routing_vocabulary'] = opener(cfg,root/'v.json')
            from student_pilot.r1_handover import bind_target
            cfg = bind_target(cfg,root/'m.json')
        write(root/'c.json',cfg)
        config_pin = file_pin(root/'c.json')
        result['steps'].append('p_opener_witness')
        from student_pilot.s1_admission import admit
        directory=root/'p';directory.mkdir(exist_ok=True)
        with scope(closure['paths']):
            visible = os.environ.get('CUDA_VISIBLE_DEVICES')
            os.environ['CUDA_VISIBLE_DEVICES'] = ''
            try:
                prepared = admit(config_pin,directory,request['frame_roots'],threads=8,
                                 memory_gib=memory,prepare_only=True)
            finally:
                if visible is None:
                    os.environ.pop('CUDA_VISIBLE_DEVICES',None)
                else:
                    os.environ['CUDA_VISIBLE_DEVICES'] = visible
        result['steps'].extend(['s1_routing.build',
            *([] if minimal else ['r1_routing.compose_native']), 's1_admission.prepare'])
        from student_pilot.r1_population import bind_prepared
        with scope(closure['paths']):
            produced = bind_prepared(load(pinned(prepared['config'])),root/'b')
        cfg = load(pinned(produced));result['config']=produced
        result['steps'].append('r1_population.bind_prepared')
        from student_pilot.r1_persisted import admission, scope
        with scope(closure['paths']):
            result['config'] = bind_handover(cfg,root/'h')
            cfg = load(pinned(result['config']))
            handover=admission(cfg,weights=bool(request.get('weights')))
        result['handover']={k:v for k,v in handover.items() if k!='paths'}
        result['absolute_resume_step']=handover['absolute_resume_step']
        result['init_milestone'] = handover['init_milestone']
        expected_start = 0 if init_policy(cfg['r1_training']) is not None else step
        if result['init_milestone'] not in (400,600) or result['absolute_resume_step'] != expected_start:
            raise ValueError('R1_PROOF_EXPORT_STEP_REQUIRED')
        result['steps'].append('persisted_handover')
        # The receipt and audit must name the config published by the final bind.
        from student_pilot.r1_loader import production_audit
        with scope(closure['paths']):
            result['audit']=production_audit(cfg,root/'a')
        result['steps'].append('r1_loader.production_audit')
        if request.get('weights'):
            with scope(handover['paths']):
                result['forward']=forward(cfg,root,result['absolute_resume_step'],device)
            result['steps'].append('all_rank_full_forward')
        finish_host(cfg, root, host, result['audit'], named_refusals=True)
        write(root/'host.json', host)
        result['host_receipt'] = file_pin(root/'host.json')
        result['status']='ADMIT'
    except (ValueError,KeyError,TypeError,OSError,RuntimeError,ImportError) as error:
        result['refusal']=type(error).__name__+':'+str(error)
    finally:
        environment.close()
    write(root/'RESULT.json',result)
    return result


def run(request, output, *, stage=None):
    """Run host checks around staging; a kit may supply its authenticated copier."""
    from student_pilot.r1_persisted import scope, proof_scope
    try:
        staging = verify_staging(request)
    except (ValueError,KeyError,TypeError,OSError):
        return _run(request,output,stage=stage)
    with proof_scope(), scope({p['sha256']:p['path'] for p in staging}):
        return _run(request,output,stage=stage)


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('request');parser.add_argument('output')
    args=parser.parse_args(argv)
    result=run(load(args.request),args.output)
    return 0 if result['status']=='ADMIT' else 1


if __name__=='__main__':
    raise SystemExit(main())
