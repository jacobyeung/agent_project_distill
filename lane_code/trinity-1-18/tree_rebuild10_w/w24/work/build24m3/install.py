from common import *
for name in ('q','n','n_go','qd'):
 k=kit(name)
 for part in ('sc.py','cs.py'):replace(k/'b'/part,(D/part).read_bytes())
 s=(k/'b/pl.py').read_text()
 needle="    cfgraw=raw_json(cfg);"
 assert needle in s
 block="""    scene=None;source_record=None
    if not regeneration and cfg.get('r2_all_stream_exclusions'):
        from student_pilot.r1_rooms import census,verify_audit
        from cs import sources as census_sources,preflight
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
        scene=bind(cfg,sources,scratch,q,kit,routing_base=localize(base))
        for p in scene.rglob('*'):
            if p.is_file():remember(p)
        from rv import location,put
        live,_=location(kit,root.parent,os.environ['SLURM_JOB_ID'])
        put(live/'s0.json',(scene/'2.json').read_bytes())
        put(live/'s1.json',(scene/'0.json').read_bytes())
        effective.update(r2_scene_rebuild=cfg['r2_scene_rebuild'],scene_coverage=cfg['scene_coverage'])
        with scope(sources):
            source_record=census_sources(effective)
            preflight(kit,root.parent,effective,source_record,os.environ['SLURM_JOB_ID'])
    cfgraw=raw_json(cfg);"""
 s=s.replace(needle,block)
 needle="    entries['e']=dict("
 block="""    if scene is not None:
        for p in scene.rglob('*'):
            if p.is_file():copy_entry('sc/'+str(p.relative_to(scene)),p)
    if source_record is not None:
        source_path=scratch/'ss.json';write(source_path,source_record)
        copy_entry('ss.json',source_path)
    entries['e']=dict("""
 s=s.replace(needle,block)
 replace(k/'b/pl.py',s)
 s=(k/'b/i.py').read_text()
 s=s.replace("if original['implementation']==implementation():return request","if original['implementation']==implementation() and normalized(original['remove_files'])==normalized(cfg['remove_files']):return request")
 s=s.replace("after=prepare(before['manifest'],root/'s',before['remove_files'],before['tokenizer'],before['room_sets'])","changed=normalized(before['remove_files'])!=normalized(cfg['remove_files'])\n    after=prepare(before['manifest'],root/'s',cfg['remove_files'],before['tokenizer'],before['room_sets'])")
 s=s.replace("        if key=='implementation':continue","        if key=='implementation' or changed:continue")
 s=s.replace("same_selection=True","same_selection=not changed,removals_regenerated=changed")
 replace(k/'b/i.py',s)
 # Final census uses the source descriptor staged before native preparation.
 s=(k/'b/a.py').read_text().replace('from sv import publish','from cs import publish')
 replace(k/'b/a.py',s)
 s=(k/'b/h.py').read_text()
 needle="# Host evidence is pinned before the prepared config is published."
 assert needle in s
 s=s.replace(needle,"""# The census binding cannot enter identity(), which would create a cycle.
# Its authenticated pin enters the identity-exempt host receipt instead.
if any(p.get('role')=='protected_rooms' for p in cfg.get('remove_files',[])):
 from cs import verify as verify_census
 host['protected_census']=verify_census(k,r.parent,cfg)
"""+needle)
 replace(k/'b/h.py',s)
 # A discovery-only review records protected-room failures and keeps preparing.
 s=(k/'b/rv.py').read_text()
 s=s.replace('        evidence(cfg, root / "rooms.json", live)',"""        try:
            evidence(cfg, root / "rooms.json", live)
        except ValueError as error:
            from cs import discovery
            if not discovery(kit) or not str(error).startswith(('R1_PROTECTED_ROOM','R1_SCENE_PROTECTED')):
                raise
            put(live/'d5.json',encoded(dict(status='WOULD_REFUSE',refusal=str(error),config_identity=value)))
        if any(p.get('role')=='protected_rooms' for p in cfg.get('remove_files',[])):
            from cs import verify as verify_census
            pin=verify_census(kit,root,cfg)
            if load(cfg['r1_training']['host_receipt']['path']).get('protected_census')!=pin:
                raise ValueError('R1_CENSUS_RECEIPT_PIN_DIFFERS')""")
 replace(k/'b/rv.py',s)
 # Preserve old census publication for the existing standalone diagnostics.
 for part in ('BUILD.json','SHA256SUMS.txt'):replace(k/part,(k/part).read_bytes())
 print(name,reseal(k))
