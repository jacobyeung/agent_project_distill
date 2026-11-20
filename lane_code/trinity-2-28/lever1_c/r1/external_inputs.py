"""Remove inputs unused by the geometry writer before admission or extraction."""
import json

REMOVED = ('sam_checkpoint','sam_receipt','selector_weights','selector_config')


def reshape(nf, pf, B):
    inputs=json.loads(nf['a/1.json'])
    for key in REMOVED:inputs['files'].pop(key)
    inputs.pop('sam_source')
    # Mixed archives also contain these unused components. Read authenticated
    # archives once, but never materialize or open their excluded members.
    inputs['retain_roots']=['m544','g','b','o','f','v','q']
    rows=json.loads(pf['g/0.json'])['items']
    ref=json.loads(pf['g/8.json'])
    dense=json.loads(next(v for n,v in pf.items() if n.startswith('b/') and n.endswith('/DENSE_MANIFEST.json')))['captures']
    if isinstance(dense,list):dense={c['native']:c for c in dense}
    captures={}
    for row in rows:
        members=[]
        for frame in dense[row['task']['native']]['frames']:
            path=frame['path']
            if path.startswith('/scratch/jjyeung/devs1_frames/'):
                path=path[len('/scratch/jjyeung/devs1_frames/'):]
            members.append(dict(path='f/'+path,sha256=frame['sha256']))
        captures[row['capture']]=members
    first=next(r['capture'] for r in rows if r['item_id']==ref['representatives'][0])
    pf['g/2.json']=B.jd(dict(captures=captures,first=first))
    nf['a/1.json']=B.jd(inputs)
    nf['INPUTS.example.json']=B.jd(inputs)
    job=pf['orchard_h10/job.py'].decode()
    job=B.once(job,"'g3t_config','sam_checkpoint',\n            'sam_receipt','selector_weights','selector_config','base_config'", "'g3t_config','base_config'")
    start=job.index("    expected={'sam_checkpoint'")
    end=job.index("    for key in ('frames_root','sam_source'):",start)
    job=job[:start]+"    for name,prefix in [('g3t_weights','d460957b'),('g3t_config','5aeb2acd')]:\n        if not inputs['files'][name]['sha256'].startswith(prefix):raise ValueError('E51')\n"+job[end:]
    job=job.replace("('frames_root','sam_source')", "('frames_root',)")
    job=job.replace("    root=Path(root); receipts={}", "    from pathlib import Path\n    root=Path(root); receipts={}")
    job=B.once(job,"    # Exact template parts", "    from orchard_h10.s import preflight, extract, materialize\n    package=J.physical(root,cfg['logical']+'/p')\n    preflight(package)\n    captures=json.loads((package/'g/2.json').read_text())\n    index={}\n    # Exact template parts")
    job=job.replace("if sha(J.physical(root,cfg['logical']+'/p/'+rel))!=pin['sha256']", "if S.sha(J.physical(root,cfg['logical']+'/p/'+rel))!=pin['sha256']")
    job=job.replace("a['expanded_bytes'],links=True)","a['expanded_bytes'],links=True,retain_roots=inputs['retain_roots'])")
    job=B.once(job,"S.extract_stream(stream,root/a['destination'],None,a['expanded_bytes'],links=True,retain_roots=inputs['retain_roots'])",
        "extract(S,stream,root/a['destination'],a['expanded_bytes'],inputs['retain_roots'],dest,index)")
    job=B.once(job,"    for name,f in inputs['files'].items():\n        path=J.physical", "    materialize(index,captures['captures'][captures['first']],J.physical(root,cfg['logical']+'/d'))\n    write(J.physical(root,cfg['logical']+'/d/9.json'),dict(index=index,**captures))\n    for name,f in inputs['files'].items():\n        path=J.physical")
    job=B.once(job,"        if path.stat().st_size!=f['bytes'] or S.sha(path)!=f['sha256']:raise ValueError('Input differs: '+name)",
        "        if path.suffix=='.json':\n            import hashlib\n            raw=_a0['raw'](path.read_bytes())\n            valid=len(raw)==f['bytes'] and hashlib.sha256(raw).hexdigest()==f['sha256']\n        else:valid=path.stat().st_size==f['bytes'] and S.sha(path)==f['sha256']\n        if not valid:raise ValueError('E52')")
    pf['orchard_h10/job.py']=job.encode()
    stage=pf['orchard_h10/vendor/orchard_stage.py'].decode()
    stage=B.once(stage,'strip=0, overlay=False):','strip=0, overlay=False, retain_roots=None, frame_offsets=None):')
    stage=B.once(stage,"mode='r|*'", "mode='r:' if frame_offsets is not None else 'r|*'")
    stage=B.once(stage,"            target = destination/str(path)","            if retain_roots is not None and path.parts[0] not in retain_roots:\n                continue\n            target = destination/str(path)")
    stage=B.once(stage,"            target = destination/str(path)", "            if frame_offsets is not None and path.parts[0]=='f':\n                if item.isfile():frame_offsets[str(path)]=dict(offset=item.offset_data,bytes=item.size)\n                elif not item.isdir():raise ValueError('E58')\n                continue\n            target = destination/str(path)")
    stage=B.once(stage,"            target.chmod(item.mode & 0o777)",
        "            if retain_roots is not None and path.parts[0]!='v' and target.suffix=='.json':\n                target.write_bytes(_a0['pack'](target.read_bytes()))\n            target.chmod(item.mode & 0o777)")
    pf['orchard_h10/vendor/orchard_stage.py']=stage.encode()
    prep=pf['orchard_h10/prepare.py'].decode()
    prep=B.once(prep,"    from parity_kit.stage_restore import stage", "    from student_pilot.g3t_online import VENDOR, vendor_digest\n    from student_pilot.tower_read import SOURCE_SHA256\n    from student_pilot.c1r_ref import source_import\n    if vendor_digest()!=SOURCE_SHA256:raise ValueError('E53')\n    source_import(VENDOR)\n    from parity_kit.stage_restore import stage")
    prep=B.once(prep,"config=str(d/pins['preparation']['config']['path']),frames_root=inputs['frames_root'],", "config=str(d/pins['preparation']['config']['path']),frames_root=inputs['frames_root'],\n        capture_index=str(d/'9.json'),")
    prep=prep.replace("with dest.open('xb') as stream:stream.write(src.read_bytes())", "with dest.open('xb') as stream:\n                import j\n                stream.write(j.pack(src.read_bytes()))")
    start=prep.index('    sam=dict(');end=prep.index("    write(d/'manifest.json'",start)
    prep=prep[:start]+"    code=dict(reader=b/'e2e_reader',heads=b/'heads',tree=p/'tree',evaluator=p/'h1eval',runner=b/'parity_kit')\n    manifest=build(Path(config['logical']),export,path('g3t_weights').parent,code_roots=code)\n"+prep[end:]
    prep=prep.replace("        selector_head=str(path('selector_config').parent),sam3=sam,\n",'')
    pf['orchard_h10/prepare.py']=prep.encode()
    return dict(removed=list(REMOVED),retain_roots=inputs['retain_roots'])
