from common import *
for name in ('q','n','n_go','qd'):
 k=kit(name);s=(k/'b/pl.py').read_text()
 s=s.replace("    cfg=deepcopy(resolved['config'])", """    cfg=deepcopy(resolved['config'])
    base=deepcopy(load(kit/'k/r.json')['routing_base'])
    if selected:
        value=load(selected[1])
        chosen=value.get('inputs_pinned',{}).get('routing_base')
        if chosen is not None:
            if not isinstance(chosen,dict) or set(chosen)!={'path','sha256'}:
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
""")
 s=s.replace("if key in child:closure(child[key],field+'.'+key)","""if key in child:
                                    if key=='database' and output and h==base['sha256']:
                                        continue
                                    closure(child[key],field+'.'+key)""")
 s=s.replace("    closure(cfg.get('streams',{}))", """    # Plan the same effective stream that stage_host substitutes, but retain the
    # original config pin so host.json records both sides of the substitution.
    streams=deepcopy(cfg.get('streams',{}));streams['routing']=base
    if selected:
        value=load(selected[1]);database=value.get('inputs_pinned',{}).get('routing_database')
        if database is not None:
            if base['sha256'] not in sources:need(base['sha256'],'request.routing_base')
            expected=load(sources[base['sha256']])['database']
            if database.get('sha256')!=expected['sha256']:
                raise ValueError('R1_ROUTING_SELECTION_DATABASE_DIFFERS')
            if load(kit/'k/a.json').get('discovery'):
                local=root.parent/'dr/p/q/base/rows.sqlite'
                if local.is_symlink():raise ValueError('R1_STAGED_PIN_SYMLINK')
                remember(local,expected['sha256'])
    closure(streams)
""")
 s=s.replace("    request['routing_base']=localize(load(kit/'k/r.json')['routing_base'])","    request['routing_base']=localize(base)")
 s=s.replace("        stage.context=scope(final_paths)","""        if output:final_paths[output]=str(q/'base/rows.sqlite')
        stage.context=scope(final_paths)""")
 s=s.replace("        stage.context.__enter__()","""        stage.context.__enter__()
        if output:
            from rb import reconstruct
            generated=reconstruct(cfg,q)
            if str(generated)!=final_paths[output]:raise ValueError('R1_ROUTING_OUTPUT_PATH_DIFFERS')""")
 replace(k/'b/pl.py',s)
 replace(k/'b/rb.py',(D/'rb.py').read_bytes())
 s=(k/'b/rg.py').read_text().replace("s1_routing=cfg['s1_routing'],division=point['division'],base_model=model_pin(cfg))", "s1_routing=cfg['s1_routing'],division=point['division'],base_model=model_pin(cfg),\n        routing_database=load(pinned(cfg['streams']['routing']))['database'])")
 replace(k/'b/rg.py',s)
 # Preserve every superseded seal, including hardlinked base upload files.
 for part in ('BUILD.json','SHA256SUMS.txt'):replace(k/part,(k/part).read_bytes())
 print(name,reseal(k))
