"""Reproduce a pinned selection with the current producer and identical rows."""
from pathlib import Path

def normalized(value):
    if isinstance(value,dict):
        return {k:normalized(v) for k,v in value.items() if not (k=='path' and 'sha256' in value)}
    if isinstance(value,list):return [normalized(v) for v in value]
    return value

def _refresh(request,root):
    from student_pilot.p3_provenance import load,pinned,file_pin,write
    from student_pilot.s1_pool import implementation,prepare
    from student_pilot.s1_pool_relocate import relocate
    from launch_r1.production_proof import verify_staging
    verify_staging(request)
    cfg=load(pinned(request['config']))
    spec=cfg.get('s1_routing')
    if not spec:return request
    from rb import routing_status
    original=load(pinned(spec['selection']))
    scene_files=dict(dev=cfg['dev_scene_exclusions'],benchmark=cfg['benchmark_scene_exclusions'])
    scenes_changed=normalized(original.get('scene_exclusions'))!=normalized(scene_files)
    if not scenes_changed and original['implementation']==implementation() and normalized(original['remove_files'])==normalized(cfg['remove_files']):
        routing_status(cfg)
        return request
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    moved=relocate(spec['selection'],spec.get('catalog',{}),root/'p')
    before=load(pinned(moved['relocated']))
    changed=normalized(before['remove_files'])!=normalized(cfg['remove_files'])
    if scenes_changed:
        from student_pilot.r2_scene_bindings import rebuild_pool
        selected=rebuild_pool(before['manifest'],scene_files['dev'],scene_files['benchmark'],root/'s',
            remove_files=cfg['remove_files'],tokenizer=before['tokenizer'],room_sets=before['room_sets'])
        after=load(pinned(selected))
    else:
        after=prepare(before['manifest'],root/'s',cfg['remove_files'],before['tokenizer'],before['room_sets'])
        selected=file_pin(root/'s/receipt.json')
    for key in set(before)|set(after):
        if key=='implementation' or changed or scenes_changed:continue
        if normalized(before.get(key))!=normalized(after.get(key)):raise ValueError('E86:'+key)
    spec['selection']=selected
    routing_status(cfg)
    write(root/'c.json',cfg)
    pin=file_pin(root/'c.json');result=dict(request,config=pin)
    result['staged_pins']=[*request['staged_pins'],pin,spec['selection']]
    write(root/'r.json',dict(status='PASS',source=original['implementation'],current=after['implementation'],same_selection=not (changed or scenes_changed),removals_regenerated=changed,scenes_regenerated=scenes_changed,config=pin))
    return result


def refresh(request,root):
    from z import write
    root=Path(root)
    try:
        result=_refresh(request,root)
    except BaseException as error:
        if not (root/'r.json').exists():
            write(root/'r.json',dict(status='REFUSE',refusal=str(error)))
        raise
    if not (root/'r.json').exists():
        write(root/'r.json',dict(status='PASS',prepared=False,config=result['config']))
    return result
