"""Plan authenticated bytes before the native host creates its namespace."""
from pathlib import Path
from copy import deepcopy
import base64
import hashlib
import json
import os
import shutil
import tarfile
from z import load, checked, sha, write, seal, name_guard, selected400


def raw_json(value):
    return (json.dumps(value, sort_keys=True, indent=2)+'\n').encode()


def selection_pin(kit, local=None):
    if local is not None:
        source=Path(local)
        if source.is_symlink() or not source.is_file():raise ValueError('R1_ROUTING_SELECTION_PIN_MISSING')
        pin=dict(path='u/'+sha(source),sha256=sha(source))
        value=load(checked(source,pin['sha256']))
        h=value.get('regenerated_sha256')
        if not isinstance(h,str) or len(h)!=64 or any(c not in '0123456789abcdef' for c in h):
            raise ValueError('R1_ROUTING_SELECTION_PIN_INVALID')
        return pin,source
    pin = load(Path(kit)/'k/h.json').get('routing_selection')
    if not isinstance(pin, dict) or set(pin) != {'path', 'sha256'}:
        raise ValueError('R1_ROUTING_SELECTION_PIN_MISSING')
    if pin['path'] != 'u/'+pin['sha256']:
        raise ValueError('R1_ROUTING_SELECTION_PIN_INVALID')
    spec = load(Path(kit)/'k/p.json')
    source = checked(Path(spec['n_root'])/pin['path'], pin['sha256'])
    value = load(source)
    h = value.get('regenerated_sha256')
    if not isinstance(h, str) or len(h) != 64 or any(c not in '0123456789abcdef' for c in h):
        raise ValueError('R1_ROUTING_SELECTION_PIN_INVALID')
    return pin, source


def plan_payload(kit, resolved, root, *, regeneration=False):
    from student_pilot.r1_persisted import scope
    from student_pilot.p3_provenance import pinned
    from i import refresh
    kit, root = Path(kit), Path(root)
    q = root/'q'
    if q.exists():
        raise ValueError('R1_HOST_JOB_TMP_NOT_FRESH')
    spec = load(kit/'k/p.json')
    if resolved['kit_sha256'] != seal(kit):
        raise ValueError('E32')
    selected = None if regeneration else selection_pin(kit, root.parent/'routing_selection.json')
    scratch = root/'i'; scratch.mkdir(mode=0o700)
    metadata = scratch/'m'; metadata.mkdir(mode=0o700)
    sources = {}
    def remember(path, h=None, size=None):
        p = Path(path); h = h or sha(p)
        checked(p, h, size)
        sources[h] = str(p)
        return h
    record = resolved['archive']
    archive = tarfile.open(checked(record['path'], record['sha256'], record['bytes'])) if record else None
    try:
        for h, item in resolved['small_files'].items():
            if spec.get('step',400)==400:
                selected400(item.get('original',item.get('member','')))
                selected400(item.get('member',''))
            if archive:
                raw = archive.extractfile(item['member']).read()
                if len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=h:
                    raise ValueError('E33')
                p=metadata/h; p.write_bytes(raw); remember(p,h)
            else:
                remember(item['path'],h,item['bytes'])
    finally:
        if archive: archive.close()
    receipt=resolved['receipt']; remember(receipt['path'],receipt['sha256'],receipt['bytes'])
    for item in spec['uploads']:
        remember(Path(spec['n_root'])/'u'/item['sha256'],item['sha256'],item['bytes'])
    for item in resolved.get('external_metadata',[]):
        remember(item['path'],item['sha256'],item['bytes'])
    from px import resolver
    need=resolver(kit,root,sources)
    cfg=deepcopy(resolved['config'])
    # Native stream readers follow pinned child receipts and databases. Preserve
    # their bytes while adding their authenticated closure to the copy plan.
    seen=set()
    def closure(value, field='config.streams'):
        if isinstance(value,dict):
            if set(value)=={'path','sha256'}:
                h=value['sha256']
                if h in seen:return
                seen.add(h)
                if h not in sources:need(h,field)
                p=Path(sources[h])
                if p.stat().st_size<=50_000_000:
                    with p.open('rb') as f:head=f.read(1)
                    if head in (b'{',b'['):
                        try:child=load(p)
                        except (ValueError,UnicodeError):return
                        # Follow the native stream-reader closure, not historical
                        # provenance that the readers deliberately leave unopened.
                        if isinstance(child,dict):
                            for key in ('database','model','division','dense_indices'):
                                if key in child:closure(child[key],field+'.'+key)
                            for i,source in enumerate(child.get('sources',[])):
                                if not isinstance(source,dict):continue
                                for key in ('receipt','model','dense_plan','teacher','clips_plan'):
                                    if key in source:closure(source[key],field+'.sources.'+str(i)+'.'+key)
                return
            for key,v in value.items():closure(v,field+'.'+str(key))
        elif isinstance(value,list):
            for i,v in enumerate(value):closure(v,field+'.'+str(i))
    closure(cfg.get('streams',{}))
    # P's regeneration recipe additionally consumes its materialization receipt.
    # Authenticate that recipe and its inputs before the native hook copies bytes.
    if regeneration and cfg.get('streams',{}).get('routing',{}).get('sha256')=='ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984':
        closure(cfg['r1_training']['p_run']['config'],'config.r1_training.p_run.config')
        with scope(sources):
            p_config=load(pinned(cfg['r1_training']['p_run']['config']))
            p_receipt=load(pinned(p_config['streams']['routing']))
            closure(p_receipt['materialization'],'P.routing.materialization')
            recipe=load(sources[p_receipt['materialization']['sha256']])
        for field in ('remove_files','dev_scene_exclusions','benchmark_scene_exclusions'):
            closure(p_config[field],'P.config.'+field)
        for field in ('inputs','legacy','division','base_model'):closure(recipe[field],'P.materialization.'+field)
        for h,p in recipe['inputs'].get('catalog',{}).items():
            if h not in sources:need(h,'P.materialization.inputs.catalog.'+h)
    # Catalog keys authenticate the producer's row, removal and tokenizer inputs.
    for h,p in cfg.get('s1_routing',{}).get('catalog',{}).items():
        if h not in sources:need(h,'config.s1_routing.catalog.'+h)
    code=base64.b64decode(json.loads((kit/'k/c0.json').read_text())['payload'])
    if hashlib.sha256(code).hexdigest()!=spec['code_sha256']:raise ValueError('E34')
    codepath=metadata/'source_code.json'; codepath.write_bytes(code); remember(codepath,spec['code_sha256'])
    cfg['code']=dict(path=str(codepath),sha256=spec['code_sha256'])
    # Bind manifest sibling names during planning, before either native reader runs.
    handover=load(receipt['path']); mp=handover['pins']['full_weights']
    manifest=load(sources[mp['sha256']])
    names={'full_weights.json':mp['sha256'],manifest['index']['name']:manifest['index']['sha256']}
    names.update({v['name']:v['sha256'] for v in manifest['files']})
    paths={h:str(q/'u'/h) for h in set(resolved['paths'])|set(sources)}
    for name,h in names.items():
        name_guard(kit)(name)
        if Path(name).name!=name or name in ('.','..'):raise ValueError('E43')
        paths[h]=str(q/'w'/name)
    cfg['r1_training']['persisted_files']={h:paths.get(h,str(q/'u'/h)) for h in cfg['r1_training']['persisted_files']}
    request=deepcopy(resolved['request'])
    cfgpin=write(scratch/'pre.json',cfg)
    refresh_request=dict(request,config=cfgpin,staged_pins=[cfgpin])
    with scope(sources):
        refreshed=refresh(refresh_request,scratch/'pool')
        cfg=load(pinned(refreshed['config']))
    for p in (scratch/'pool').rglob('*'):
        if p.is_file():remember(p)
    extras={}
    def localize(value):
        if isinstance(value,dict):
            if 'path' in value and 'sha256' in value:
                h=value['sha256']; p=value['path']
                if h not in sources and h not in paths:need(h,'config.pin')
                return {k:(paths.get(h,str(q/'u'/h)) if k=='path' else localize(v)) for k,v in value.items()}
            return {k:localize(v) for k,v in value.items()}
        if isinstance(value,list):return [localize(v) for v in value]
        if isinstance(value,str):
            if value.startswith('u/'):return str(q/value)
            if value.startswith(str(q)+'/'):return value
            if value.startswith(spec['namespace']+'/'):
                return str(q/value[len(spec['namespace'])+1:])
            if Path(value).is_absolute():
                # Every direct path is planned explicitly; no external symlink enters q.
                p=Path(value)
                dest='f/'+hashlib.sha256(value.encode()).hexdigest()
                extras[dest]=p
                return str(q/dest)
        return value
    # Output locations are future destinations, never inputs to be copied.
    cfg['output']=str(q/'r'); cfg['preparation_output']=str(q/'p0')
    # Catalog values name authenticated sources, not extra host-path inputs.
    cfg.get('s1_routing',{}).update(catalog={h:paths.get(h,str(q/'u'/h)) for h in cfg.get('s1_routing',{}).get('catalog',{})})
    cfg=localize(cfg)
    cfg['code']=dict(path=str(q/'source_code.json'),sha256=spec['code_sha256'])
    cfg['output']=str(q/'r'); cfg['preparation_output']=str(q/'p0')
    cfg.get('s1_routing',{}).update(catalog={h:paths.get(h,str(q/'u'/h)) for h in cfg.get('s1_routing',{}).get('catalog',{})})
    cfgraw=raw_json(cfg); cfgpath=metadata/'n.json';cfgpath.write_bytes(cfgraw);cfgh=remember(cfgpath)
    request=localize(request)
    request.update(config=dict(path=str(q/'n.json'),sha256=cfgh),job_tmp=str(q),binaries=load(kit/'k/h.json')['binaries'])
    request['routing_base']=localize(load(kit/'k/r.json')['routing_base'])
    request['staged_pins']=[dict(path=str(q/'u'/h),sha256=h) for h in sources]+[request['config']]
    if selected:
        pin,source=selected;remember(source,pin['sha256']);request['routing_selection']=dict(path=str(q/pin['path']),sha256=pin['sha256'])
    else:request['routing_selection']={'required_parameter':'R1_ROUTING_SELECTION_PIN_MISSING'}
    entries={}
    copies={}
    def copy_entry(name,p,h=None):
        p=Path(p);h=h or sha(p)
        entries[name]=dict(sha256=h,parts=[str(q/name)],bytes=p.stat().st_size)
        copies[name]=str(p)
    for h,p in sources.items():copy_entry('u/'+h,p,h)
    copy_entry('source_code.json',codepath,spec['code_sha256']);copy_entry('n.json',cfgpath,cfgh)
    entries['e']=dict(archive=dict(sha256=resolved['tar_sha256'],bytes=resolved['tar_bytes'],
        parts=[dict(sha256=p['sha256'],bytes=p['bytes']) for p in resolved['parts']]),
        inventory={label:pin['sha256'] for label,pin in handover['pins'].items()})
    # Payload members stay in their authenticated archive until the staging hook.
    for dest,p in extras.items():
        if p.is_dir():
            for f in sorted(p.rglob('*')):
                if f.is_symlink():raise ValueError('R1_STAGING_SYMLINK')
                if f.is_file():copy_entry(dest+'/'+str(f.relative_to(p)),f)
        elif p.is_file():copy_entry(dest,p)
        else:raise ValueError('R1_STAGING_PATH_MISSING:'+str(p))
    manifest_path=scratch/'staging.json';manifest_pin=write(manifest_path,dict(entries=entries))
    request['staging']=dict(path=str(q/'u'/manifest_pin['sha256']),sha256=manifest_pin['sha256'])
    sources[manifest_pin['sha256']]=str(manifest_path)
    from launch_r1.entry import temporary_paths
    temporary_paths(cfg,q);temporary_paths(request,q);temporary_paths(load(manifest_path),q)
    final=deepcopy(resolved);final['config']=cfg;final['paths']=paths
    final['_namespace']=str(q)
    def stage(received,directory):
        from z import copy_resolved_payload
        if Path(directory)!=q or received!=entries:raise ValueError('R1_STAGING_PLAN_DIFFERS')
        copy_resolved_payload(kit,final,q)
        for name,p in copies.items():
            target=q/name;target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            checked(p,entries[name]['sha256'],entries[name]['bytes'])
            if target.exists():checked(target,entries[name]['sha256'],entries[name]['bytes'])
            else:
                with Path(p).open('rb') as a,target.open('xb') as b:shutil.copyfileobj(a,b,8<<20)
        shutil.copyfile(manifest_path,q/'u'/manifest_pin['sha256'])
        for p in [q,*[p for p in q.rglob('*') if p.is_dir()]]:p.chmod(0o700)
        if (q/'n.json').read_bytes()!=cfgraw:raise ValueError('R1_STAGING_CONFIG_DIFFERS')
        final_paths={h:str(q/'u'/h) for h in sources}
        final_paths.update(paths)
        final_paths[cfgh]=str(q/'n.json')
        final_paths[spec['code_sha256']]=str(q/'source_code.json')
        # Keep native reads on the authenticated staged bytes after preflight.
        stage.context=scope(final_paths)
        stage.context.__enter__()
    def close():
        if stage.context is not None:
            stage.context.__exit__(None,None,None)
            stage.context=None
    stage.context=None
    stage.close=close
    # The map only resolves authenticated bootstrap metadata before q exists.
    sources[cfgh]=str(cfgpath)
    write(root/'plan.json',dict(request=request,config=cfg,entries=entries))
    return request,sources,stage
