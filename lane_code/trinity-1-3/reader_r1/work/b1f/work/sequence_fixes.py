from pathlib import Path
p=Path('out/tower_sequence.py');s=p.read_text();s=s.replace('# Distance under each rule precedes the remaining baseline types.\nSCHEDULE=((0,3),(1,3),(0,0),(0,1),(0,2),(0,4))','# Each read owns one worker; read 0 retains its memo across all five types.\nSCHEDULE=((0,3),(0,0),(0,1),(0,2),(0,4),(1,3))')
s=s.replace('def descriptors():','def descriptors(package):\n items=json.loads((Path(package)/\'items/devs1_routed.json\').read_text())[\'items\']\n verify_ids=[r[\'id\'] for r in items if r[\'question_type\']==\'object_abs_distance\'][:30]')
a=s.index('              perception_memo_verify_reads=');b=s.index('         for i,r in enumerate(RULES)]',a)
s=s[:a]+'''              perception_memo_verify_ids=verify_ids if i==0 else [],
              types=[3,0,1,2,4] if i==0 else [3],expected=636 if i==0 else 150)
'''+s[b:]
s=s.replace('specs=descriptors();','specs=descriptors(config[\'package\']);')
s=s.replace("root=base/str(i)","root=base/'metadata/reads'/str(i)")
s=s.replace("('perception_memo','perception_memo_verify_reads','perception_memo_max_bytes','perception_memo_verify_types')","('perception_memo','perception_memo_verify_ids')")
a=s.index("  sealed_write(root/'metadata/IDENTITY.json'");b=s.index('\n return configs',a)
s=s[:a]+'''  sealed_write(root/'metadata/READ_IDENTITY.json',dict(**identity,read=i,settings_sha256=canonical(chosen)))
  configs[i]={**config,'output':str(root),'settings':str(path),
      'cache_root':str(base/'cache'/str(i)), 'stop_file':str(base/'metadata/STOP'),
      'single_worker':True,'arms':['tower'],'modes':['none'],'types':[ORDER[t] for t in spec['types']],
      'stage1_select_rule':spec['stage1_select_rule'],
      'stop_margin':1800,'return_margin':1200,**memo_settings(chosen)}
'''+s[b:]
s=s.replace(' for (i,t),cfg in configs.items():',' for i,cfg in configs.items():\n  t=ORDER.index(cfg[\'types\'][0])')
s=s.replace("assert args[args.index('--types')+1]==ORDER[t]","assert args[args.index('--types')+1]==','.join(cfg['types'])\n  assert args[args.index('--stop-file')+1]==str(Path(config['output'])/'metadata/STOP')")
s=s.replace("  assert chosen['perception_memo_verify_types']==(['object_abs_distance'] if i==0 else None)\n  result.append(dict(read=i,type=t,args=args,settings=chosen,expected=COUNTS[t]))", "  assert chosen['perception_memo_verify_ids']==descriptors(config['package'])[i]['perception_memo_verify_ids']\n  result.append(dict(read=i,types=cfg['types'],args=args,settings=chosen,expected=636 if i==0 else 150))")
s=s.replace(' for i,t in SCHEDULE:',' for i in (0,1):').replace('  cfg=configs[i,t]','  cfg=configs[i]').replace('results.append(dict(read=i,type=t,**result))','results.append(dict(read=i,types=cfg[\'types\'],**result))')
p.write_text(s)
p=Path('out/build_operator.py');s=p.read_text();a=s.index("write(O/'READ_PLAN.json'");b=s.index('\nprint(',a)
s=s[:a]+'''sys.path.insert(0,str(O));import tower_sequence as sequence
write(O/'READ_PLAN.json',dict(token=public['token'],operator_sha256=sha(O/'tower_sequence.py'),
  sequence=sequence.SCHEDULE,expected=[636,150],arms=['tower'],modes=['none'],
  rules=sequence.RULES,read_settings=sequence.descriptors(O/'src'),memo_scope='one worker per read',
  save_own_depth=False,walltime='05:00:00',stop_margin=1800,return_margin=1200))
'''+s[b:];p.write_text(s)
p=Path('out/tower_pair.py');s=p.read_text();a=s.index('  if not paths:');b=s.index('  for path in paths:',a)
s=s[:a]+"  if not paths:raise ValueError('No item journals: '+str(path))\n  if path.is_dir():\n   for started in path.rglob('STARTED.json'):\n    if not (started.parent/'items.jsonl').is_file():raise ValueError('Started segment has no journal: '+str(started.parent))\n"+s[b:]
s=s.replace("'perception_memo_max_bytes','perception_memo_verify_reads','perception_memo_verify_types'","'perception_memo_verify_ids'")
p.write_text(s)
p=Path('out/unpack_return.py');s=p.read_text();a=s.index('\ndef main():');s=s[:a]+'''
def validate_journals(dest):
 root=Path(dest)
 # A read start proves a worker was launched, even if it failed before type setup.
 for steps in (root/'metadata/reads').glob('*/STEPS.jsonl'):
  if any(json.loads(line).get('event')=='start' for line in steps.read_text().splitlines()):
   if not list(steps.parent.glob('metadata/journals/*/*/items.jsonl')):
    raise ValueError('Started read has no journal: '+str(steps.parent))
 for started in (root/'metadata/reads').glob('*/metadata/journals/*/*/STARTED.json'):
  if not (started.parent/'items.jsonl').is_file():
   raise ValueError('Started segment has no journal: '+str(started.parent))
  if not (started.parent/'environment.json').is_file():
   raise ValueError('Started segment has no environment: '+str(started.parent))
 if not list((root/'metadata/reads').glob('*/metadata/journals/*/*/items.jsonl')):
  raise ValueError('Return has no journals')

'''+s[a:];s=s.replace("raise ValueError('Output must stay inside W2')","raise ValueError('Output must stay inside W4')");s=s.replace(' print(json.dumps(dict(output=', ' validate_journals(dest)\n print(json.dumps(dict(output=');p.write_text(s)
