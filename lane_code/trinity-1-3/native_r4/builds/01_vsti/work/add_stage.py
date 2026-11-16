from pathlib import Path
p=Path('code/venue.py');s=p.read_text()
pos=s.index('\ndef namespace(')
s=s[:pos]+'''
def stage_local(root,assets,budget=8000000000):
    """Stage local archives using the inherited bounded archive reader."""
    import paths
    sys.path.extend([str(paths.CORE),str(paths.CORE/'orchard_native')])
    import orchard_stage as S
    import native_stage as N
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    used=0;receipts={};result=dict(assets)
    for role in ('metadata','runtime','fla'):
        source=assets.get(role+'_archive')
        if source is None:raise ValueError('missing local archive descriptor: '+role)
        archive=checked(source)
        if archive.stat().st_size>budget-used:raise ValueError('archive cannot fit the stage budget')
        destination=root/role
        if destination.exists():raise ValueError('staging phase already exists: '+role)
        if role=='metadata':
            used+=extract(archive,destination,budget-used,include=lambda name:name.startswith(('fsw/','m/')))
            result['base_bindings']=list(result.get('base_bindings',[]))+[(str(destination/'fsw'),FSW)]
        else:
            destination.mkdir()
            saved=S.RUNTIME_ABSOLUTE_LINKS
            try:
                if role=='runtime':S.RUNTIME_ABSOLUTE_LINKS=N.runtime_links(archive)
                with archive.open('rb') as stream:
                    inventory=S.extract_stream(stream,destination,None,budget-used,links=role=='runtime')
            finally:S.RUNTIME_ABSOLUTE_LINKS=saved
            used+=sum(r['bytes'] for r in inventory.values())
            relative=assets[role+'_relative_root'];candidate=destination/relative
            if not candidate.is_dir():raise ValueError('archive layout differs: '+role)
            result['runtime_root' if role=='runtime' else 'fla_root']=str(candidate)
        receipts[role]=dict(source=source,owned_bytes=used)
        dump(root/'STAGING.json',receipts)
    # The original export is a read-only child mount over the staged metadata namespace.
    result['base_bindings']=[v for v in result['base_bindings'] if v[1]!=assets['export_logical']]+[(assets['export_root'],assets['export_logical'])]
    dump(root/'ASSETS.json',result);return result
''' +s[pos:]
s=s.replace("    for name in ('plan','run'):","    q=sub.add_parser('stage')\n    for k in ('root','assets'):q.add_argument('--'+k,required=True)\n    q.add_argument('--budget',type=int,default=8000000000)\n    for name in ('plan','run'):")
s=s.replace("    if a.command=='packet':return packet", "    if a.command=='stage':return stage_local(a.root,load(a.assets),a.budget)\n    if a.command=='packet':return packet")
p.write_text(s)
