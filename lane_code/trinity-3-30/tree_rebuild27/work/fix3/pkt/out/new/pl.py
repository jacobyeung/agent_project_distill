"""Plan authenticated bytes before the native host creates its namespace."""
from pathlib import Path
from copy import deepcopy
import base64
import hashlib
import json
import os
import shutil
import tarfile
from z import load, checked, sha, write, seal, name_guard, selected400, inside


def raw_json(value):
    return (json.dumps(value, sort_keys=True, indent=2)+'\n').encode()


def selection_pin(kit):
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


def named_folder(folder, pool, named, link=True):
    """Place each named file's pool bytes under its own name in one folder; return {sha256: path}."""
    folder = Path(folder); folder.mkdir(mode=0o700, exist_ok=True)
    placed = {}
    for name, h in named.items():
        source = checked(pool(h), h); target = inside(folder, name)
        if target.exists():checked(target, h)
        elif link:os.link(source, target)
        else:
            shutil.copyfile(source, target); checked(target, h)
        placed[h] = str(target)
    return placed


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
    selected = None if regeneration else selection_pin(kit)
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
    # The opener witness takes the processor folder from where the model manifest's config.json pin
    # resolves. In mode q that manifest's non-weight files therefore also get one folder, q/y, under
    # their manifest names (hard links to q/u), and their pins resolve there once staging is done.
    named={}
    if not regeneration:
        for name,h in resolved['model_files'].items():
            if name.endswith(('.json','.txt','.jinja','.model')):
                name_guard(kit)(name)
                if Path(name).name!=name or name in ('.','..'):raise ValueError('E43')
                if h not in sources:need(h,'model_manifest.files.'+name)
                named[name]=h
        if 'config.json' not in named:raise ValueError('E31')
    cfg=deepcopy(resolved['config'])
    base=deepcopy(resolved['request'].get('routing_base') or load(kit/'k/r.json')['routing_base'])
    if selected:
        value=load(selected[1])
        chosen=value.get('inputs_pinned',{}).get('routing_base')
        if chosen is not None:
            if (not isinstance(chosen,dict) or set(chosen)!={'path','sha256'} or not isinstance(chosen['sha256'],str) or len(chosen['sha256'])!=64 or any(c not in '0123456789abcdef' for c in chosen['sha256'])):
                raise ValueError('R1_ROUTING_SELECTION_BASE_INVALID')
            base=deepcopy(chosen)
    # Only P's authenticated database is reconstructed. All producer inputs,
    # including the legacy routing database, remain required staged inputs.
    output=None
    if regeneration and base['sha256']=='ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984':
        if base['sha256'] not in sources:need(base['sha256'],'request.routing_base')
        output=load(sources[base['sha256']])['database']['sha256']
        if output!='4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84':
            raise ValueError('P_TRAINED_ROUTING_DATABASE_DIFFERS')

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
                                if key in child:
                                    if key=='database' and output and h==base['sha256']:
                                        continue
                                    closure(child[key],field+'.'+key)
                            for i,source in enumerate(child.get('sources',[])):
                                if not isinstance(source,dict):continue
                                for key in ('receipt','model','dense_plan','teacher','clips_plan'):
                                    if key in source:closure(source[key],field+'.sources.'+str(i)+'.'+key)
                return
            for key,v in value.items():closure(v,field+'.'+str(key))
        elif isinstance(value,list):
            for i,v in enumerate(value):closure(v,field+'.'+str(i))
    # Plan the same effective stream that stage_host substitutes, but retain the
    # original config pin so host.json records both sides of the substitution.
    streams=deepcopy(cfg.get('streams',{}));streams['routing']=base
    if selected:
        value=load(selected[1]);database=value.get('inputs_pinned',{}).get('routing_database')
        if database is not None:
            if base['sha256'] not in sources:need(base['sha256'],'request.routing_base')
            expected=load(sources[base['sha256']])['database']
            if not isinstance(database,dict) or set(database)!={'path','sha256'} or database.get('sha256')!=expected['sha256']:
                raise ValueError('R1_ROUTING_SELECTION_DATABASE_DIFFERS')
            if load(kit/'k/a.json').get('discovery') and expected['sha256'] not in sources:
                local=root.parent/'dr/p/q/base/rows.sqlite'
                if local.is_symlink() or not local.resolve().is_relative_to(root.parent.resolve()):raise ValueError('R1_STAGED_PIN_SYMLINK')
                if local.is_file():remember(local,expected['sha256'])
    closure(streams)

    # P's regeneration recipe additionally consumes its materialization receipt.
    # Authenticate that recipe and its inputs before the native hook copies bytes.
    if output:
        closure(cfg['r1_training']['p_run']['config'],'config.r1_training.p_run.config')
        with scope(sources):
            p_config=load(pinned(cfg['r1_training']['p_run']['config']))
            p_receipt=load(pinned(p_config['streams']['routing']))
            closure(p_receipt['materialization'],'P.routing.materialization')
            recipe=load(sources[p_receipt['materialization']['sha256']])
        closure(p_config['code'],'P.config.code')
        closure(p_config.get('s1_route_policy',{}),'P.config.s1_route_policy')
        for field in ('remove_files','dev_scene_exclusions','benchmark_scene_exclusions'):
            closure(p_config[field],'P.config.'+field)
        for field in ('inputs','legacy','division','base_model'):closure(recipe[field],'P.materialization.'+field)
        model=load(sources[recipe['base_model']['sha256']])
        for name,h in model['files'].items():
            if name.endswith(('.json','.txt','.jinja','.model')) and h not in sources:
                need(h,'P.materialization.base_model.files.'+name)
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
    # Scene readers need the authenticated base before computing their census.
    early_base=None
    if output and cfg.get('r2_all_stream_exclusions'):
        from rb import reconstruct
        with scope(sources):
            early_base=reconstruct(cfg,scratch)
        remember(early_base,output)
    request=deepcopy(resolved['request'])
    scene_pool_inputs=None
    if cfg.get('r2_all_stream_exclusions'):
        with scope(sources):
            pool_before=load(pinned(cfg['s1_routing']['selection']))
            scene_pool_inputs={key:pool_before.get(key) for key in ('manifest','tokenizer')}
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
    scene=None;source_record=None
    if cfg.get('r2_all_stream_exclusions'):
        from student_pilot.r1_rooms import census,verify_audit
        from cs import sources as census_sources,discovery
        from sc import bind
        effective=deepcopy(cfg);effective['streams']['routing']=localize(base)
        with scope(sources):
            audit,_=census(effective)
            audit_pin=write(scratch/'ra.json',audit)
            remember(audit_pin['path'],audit_pin['sha256'])
            staged_audit=dict(path=str(q/'u'/audit_pin['sha256']),sha256=audit_pin['sha256'])
            cfg['r1_training']['room_audit']=staged_audit
            effective['r1_training']['room_audit']=staged_audit
            request['room_audit']=staged_audit
        with scope(sources):
            verify_audit(effective,staged_audit)
        scene=bind(cfg,sources,scratch,q,kit,routing_base=localize(base),pool_inputs=scene_pool_inputs)
        for p in scene.rglob('*'):
            if p.is_file():remember(p)
        from rv import location,put
        if regeneration:
            live=root.parent/'live'
            if any(p.is_symlink() for p in (live,*live.parents)):
                raise ValueError('R1_REVIEW_FILE_UNUSABLE')
            live.mkdir(mode=0o700,exist_ok=True)
        else:
            live,_=location(kit,root.parent,os.environ['SLURM_JOB_ID'])
        put(live/'s0.json',(scene/'2.json').read_bytes())
        put(live/'s1.json',(scene/'0.json').read_bytes())
        effective.update(r2_scene_rebuild=cfg['r2_scene_rebuild'],scene_coverage=cfg['scene_coverage'],s1_routing=cfg['s1_routing'])
        with scope(sources):
            source_record=census_sources(effective)
    cfgraw=raw_json(cfg); cfgpath=metadata/'n.json';cfgpath.write_bytes(cfgraw);cfgh=remember(cfgpath)
    request=localize(request)
    request.update(config=dict(path=str(q/'n.json'),sha256=cfgh),job_tmp=str(q),binaries=load(kit/'k/h.json')['binaries'])
    request['routing_base']=localize(base)
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
    if early_base is not None:
        for name in ('base','base_tree','base_input.json','base_mounts.json','base_imports.json'):
            p=scratch/name
            if p.is_dir():
                for f in p.rglob('*'):
                    if f.is_file():copy_entry(name+'/'+str(f.relative_to(p)),f)
            elif p.is_file():copy_entry(name,p)
    copy_entry('source_code.json',codepath,spec['code_sha256']);copy_entry('n.json',cfgpath,cfgh)
    if scene is not None:
        for p in scene.rglob('*'):
            if p.is_file():copy_entry('sc/'+str(p.relative_to(scene)),p)
    if source_record is not None:
        source_path=scratch/'ss.json';write(source_path,source_record)
        copy_entry('ss.json',source_path)
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
        linked=named_folder(q/'y',lambda h:q/'u'/h,named) if named else {}
        for p in [q,*[p for p in q.rglob('*') if p.is_dir()]]:p.chmod(0o700)
        if (q/'n.json').read_bytes()!=cfgraw:raise ValueError('R1_STAGING_CONFIG_DIFFERS')
        final_paths={h:str(q/'u'/h) for h in sources}
        final_paths.update(paths)
        final_paths.update(linked)
        final_paths[cfgh]=str(q/'n.json')
        final_paths[spec['code_sha256']]=str(q/'source_code.json')
        # Keep native reads on the authenticated staged bytes after preflight.
        if output:final_paths[output]=str(q/'base/rows.sqlite')
        stage.context=scope(final_paths)
        stage.context.__enter__()
        if named:
            from pf import check
            check(cfg,resolved['model_manifest'])
        if output and early_base is None:
            from rb import reconstruct
            generated=reconstruct(cfg,q)
            if str(generated)!=final_paths[output]:raise ValueError('R1_ROUTING_OUTPUT_PATH_DIFFERS')
    def close():
        if stage.context is not None:
            stage.context.__exit__(None,None,None)
            stage.context=None
    stage.context=None
    stage.close=close
    if named:
        # Fail before the long steps: rehearse both processor folders on the planned bytes.
        from pf import check
        with scope({**sources,**named_folder(scratch/'y',lambda h:sources[h],named,link=False)}):
            check(cfg,resolved['model_manifest'])
    # The map only resolves authenticated bootstrap metadata before q exists.
    sources[cfgh]=str(cfgpath)
    write(root/'plan.json',dict(request=request,config=cfg,entries=entries,generated={output:str(q/'base/rows.sqlite')} if output else {}))
    return request,sources,stage
