from pathlib import Path
p=Path('code/o.py');s=p.read_text().replace("        original['logical_run']='/r';(root/'shm').mkdir()", "        S.physical(root,original['logical_run']).mkdir(parents=True,exist_ok=True);(root/'shm').mkdir()")
s=s.replace("S.namespace(root,dict(original,logical_run=str(runroot)))","S.namespace(root,original)")
s=s.replace("or '/g/raw/' in str(p) or p.name.endswith('.next')", "or ('/g/raw/' in str(p) and p.suffix=='.npz') or '/v/' in str(p.relative_to(runroot)) or p.name.endswith('.next')")
s=s.replace("        runtime=old['runtime_spec'];", "        for name in ('home','temp','cache'):(root/name).mkdir(exist_ok=True)\n        runtime=old['runtime_spec'];")
p.write_text(s)
p=Path('code/a.py');s=p.read_text().replace("    bound=validate_bound(root/'i/BOUND.json')",'''    else:
        fresh=prepare('/d/c.json','/d/d.json','/b/frames',root/'v')
        fresh=relocate_input(root/'v','/r/i')
        if fresh!=load(root/'i/BOUND.json'):raise ValueError('resumed frame/input pins differ')
        (root/'v/store').rename(root/'i/store')
    bound=validate_bound(root/'i/BOUND.json')''')
p.write_text(s)
