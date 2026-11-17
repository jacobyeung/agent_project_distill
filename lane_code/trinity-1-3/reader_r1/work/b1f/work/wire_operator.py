from pathlib import Path
O=Path.cwd()/'out'
p=O/'tower_sequence.py';s=p.read_text()
s=s.replace("types=[0,1,2,3,4] if i==0 else [3],expected=636 if i==0 else 150)","perception_memo='verify' if i==0 else 'on',\n              perception_memo_verify_reads=30 if i==0 else None,perception_memo_max_bytes=64*1024**3,\n              types=[0,1,2,3,4] if i==0 else [3],expected=636 if i==0 else 150)")
s=s.replace(" specs=descriptors();identity=", " from e2e_reader.perception_memo import settings as memo_settings\n memo_settings(settings,required=True)\n if settings['stage1_select_rule'] not in RULES:raise ValueError('unknown_stage1_select_rule')\n specs=descriptors();identity=")
s=s.replace("chosen={**settings,'stage1_select_rule':spec['stage1_select_rule'],'save_own_depth':False}","chosen={**settings,'stage1_select_rule':spec['stage1_select_rule'],'save_own_depth':False,\n          **{k:spec[k] for k in ('perception_memo','perception_memo_verify_reads','perception_memo_max_bytes')}}")
s=s.replace("  for t in spec['types']:\n   configs", "  for t in spec['types']:\n   segment=dict(chosen)\n   if (i,t)!=(0,3):segment.update(perception_memo='on',perception_memo_verify_reads=None)\n   segment_path=root/str(t)/'metadata/0.json';sealed_write(segment_path,segment)\n   configs")
s=s.replace("'settings':str(path)","'settings':str(segment_path)")
s=s.replace("'stop_margin':1800,'return_margin':1200}","'stop_margin':1800,'return_margin':1200,**memo_settings(segment)}")
s=s.replace("  result.append(dict(read=i,type=t,args=args,expected=COUNTS[t]))", "  chosen=json.loads(Path(args[args.index('--settings')+1]).read_text())\n  assert chosen['perception_memo']==('verify' if (i,t)==(0,3) else 'on')\n  result.append(dict(read=i,type=t,args=args,settings=chosen,expected=COUNTS[t]))")
p.write_text(s)
p=O/'build_operator.py';s=p.read_text().replace("rules=['null_argmax','candidates_argmax'],save_own_depth=False", "rules=['null_argmax','candidates_argmax'],perception_memo='verify first 30 scheduled reads, then on',\n  memo_max_bytes=64*1024**3,memo_scope='one worker per segment',save_own_depth=False");p.write_text(s)
# Fixture inputs now explicitly declare off; test semantics and expected outputs stay intact.
files=list((O/'tests').glob('*.py'))+[Path('work/test_tower.py'),Path('work/test_sequence.py')]
for p in files:
 s=p.read_text()
 s=s.replace("dict(arm='own_depth',save_own_depth=False)","dict(arm='own_depth',save_own_depth=False,stage1_select_rule='null_argmax',perception_memo='off')")
 s=s.replace("artifact_manifest=str(binding),stage1_select_rule='null_argmax')","artifact_manifest=str(binding),stage1_select_rule='null_argmax',perception_memo='off')")
 p.write_text(s)
