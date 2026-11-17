"""Local package integrity and namespace-source rehearsal; no remote reads or processes."""
from pathlib import Path
import hashlib,json,tarfile,sys
W=Path.cwd();sys.path.insert(0,str(W/'work/p'))
from orchard_h10.common import read_config,submit_argv,sha
from orchard_h10.job import check_inputs,verify_config
from orchard_h10.runner import worker_args
for token in ('c4d7e0a91b28f','d8a2f6c09e137'):
 pkg=W/'out'/token;cfg=read_config(pkg);verify_config(cfg)
 dest=W/'work/rehearsal_delivery'/token
 if dest.exists():raise ValueError('Rehearsal requires empty root')
 dest.mkdir(parents=True)
 with tarfile.open(pkg/'0.tgz') as archive:
  for e in archive:
   if not e.isfile() or Path(e.name).is_absolute() or '..' in Path(e.name).parts:raise ValueError('Unsafe package')
   p=dest/'p'/e.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(archive.extractfile(e).read())
 for name,pin in cfg['payload_pins'].items():assert sha(dest/'p'/name)==pin['sha256'],name
 # Mirror the package job's own bind-source preparation, without invoking bwrap.
 for name in ('sj','fsw','m/ap'):(dest/name).mkdir(parents=True,exist_ok=True)
 inputs=json.loads((W/'in/pkg/a/1.json').read_text().replace('b01ec87a6f29b',token))
 inputs['types']=['object_abs_distance'];inputs.pop('optional',None);inputs['resume']=None
 private=pkg/'a';private.mkdir(mode=0o700,exist_ok=True);private.chmod(0o700)
 (private/'1.json').write_text(json.dumps(inputs,indent=2)+'\n');check_inputs(inputs,cfg)
 runtime=dict(package=str(dest/'p'),output=str(dest/'r'),export=cfg['logical']+'/d/e',binding=cfg['logical']+'/d/binding.json',
              settings=cfg['logical']+'/d/settings.json',device='cpu',modes=cfg['modes'])
 (dest/'r/metadata/a').mkdir(parents=True)
 from orchard_h10.common import ORDER
 args=worker_args(dict(config=runtime,type=ORDER.index('object_abs_distance'),index=0,cards=1,stop_at=0,finish_by=0))
 assert args[args.index('--modes')+1]=='none'
 assert args[args.index('--types')+1]=='object_abs_distance'
 items=json.loads((dest/'p/items/devs1_routed.json').read_text())['items']
 assert sum(i['question_type']=='object_abs_distance' for i in items)==150
 print(json.dumps(dict(token=token,rule=cfg['stage1_select_rule'],payload_sha256=cfg['payload_sha256'],plan=cfg['plan_sha256'],
       pins_checked=len(cfg['payload_pins']),empty_root=True,bind_sources_created=['sj','fsw','m/ap'],reads=150,
       worker_argv=args,submit_argv=submit_argv(token,1,'01:45:00'),
       full_restore='NOT RUN: model, SAM, environment and RGB archives are referenced on Orchard and not staged here')))
