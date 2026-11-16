import ast
import json
from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(L/'work/tree_r1'))
from launch_r2.build import verify,scan
from launch_r2.staging import read,validate_plan
from student_pilot.p3_provenance import load
records=[]
for arm in ('a0','a2'):
    root=L/'work/build4/kits'/arm
    launch=read(root/'k/launch.json');cfg=read(root/launch['config']['file']);zero=read(root/'k/0.json')
    plan=read(root/zero['staging']['path'])
    names=validate_plan(cfg,plan['entries'])
    auth=read(root/'k/4.json')
    assert auth['production_go_granted'] is False and auth['config_sha256']==launch['config']['sha256']
    syntax=[]
    for name in ('s.py','l.py','a.py','v.py','gcsput.py'):
        ast.parse((root/'b'/name).read_text(),feature_version=(3,6));syntax.append(name)
    records.append(dict(arm=arm,seal=verify(root),scan=scan(root),relative_paths=names,
        planned=len(names),entries={p:{k:v for k,v in plan['entries'][p].items() if k!='payload'} for p in names},
        python36_syntax=syntax,actual_python36_runtime=False,actual_pinned_environment=False,
        routing_vocabulary=cfg.get('routing_vocabulary'),dev=cfg['dev_scene_exclusions'],
        authorization=auth,checkpoint_disk_guard=cfg['checkpoint_disk_guard']))
(L/'work/build4/KIT_CHECKS.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps([dict(arm=r['arm'],planned=r['planned'],scan=r['scan']) for r in records]))
