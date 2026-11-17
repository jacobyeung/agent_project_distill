from pathlib import Path
import json
W=Path(__file__).resolve().parents[1];O=W/'out';P=O/'src'
def edit(path,old,new):
 s=path.read_text();assert old in s,(path,old);path.write_text(s.replace(old,new))
# The private data root is unchanged; this archive has no f/ prefix.
f=P/'orchard_h10/job.py'
edit(f,"str(target)!=str(Path('sj')/Path(cfg['logical']).relative_to('/scratch/jjyeung')/'d')", "str(target) not in {str(Path('sj')/Path(cfg['logical']).relative_to('/scratch/jjyeung')/'d'), str(Path('sj')/Path(cfg['logical']).relative_to('/scratch/jjyeung')/'d/f')}")
# Preserve the reader; extend only the evaluation membership gate.
f=P/'h1eval/items.py'
edit(f,"if m['name'] not in ('r0dev','r0dev_f32') and found:","if m['name'] not in ('r0dev','r0dev_f32','room134') and found:")
edit(f,"    return m\n", "    if m['name']=='room134':\n        from .room134 import validate\n        validate(m)\n    return m\n")
edit(f,"def read_contract(manifest, arms, interventions, types=None):", "def read_contract(manifest, arms, interventions, types=None):\n    if manifest['name']=='room134':\n        if arms!=['tower'] or interventions!=[{'name':'none'}] or types!='room_size_estimation':\n            raise ValueError('Room read requires tower/none and room type only')")
f=P/'h1eval/h10/parity_adapter.py'
edit(f,"    if name=='r0dev_f32':", "    if name=='room134':\n        from h1eval.room134 import bind\n        return bind(items,settings)\n    if name=='r0dev_f32':")
# Types enter settings and the durable environment, in addition to worker args.
f=P/'h1eval/h10/launch.py'
edit(f,"                 shard=args.shard,ids=", "                 types=args.types.split(',') if args.types else None,\n                 shard=args.shard,ids=")
f=P/'orchard_h10/build.py'
edit(f,"budget_gpu_seconds=18000", "budget_gpu_seconds=9000,stage1_select_rule='null_argmax',perception_memo='on',perception_memo_verify_ids=[],save_own_depth=False")
f=P/'orchard_h10/prepare.py'
edit(f,"        perception_memo_verify_ids=config.get('perception_memo_verify_ids',[]))", "        perception_memo_verify_ids=config.get('perception_memo_verify_ids',[]),\n        types=inputs.get('types'))")
f=O/'node_check.py';edit(f,"settings['perception_memo']!='off'", "settings['perception_memo']!='on'")
edit(f,"or settings['perception_memo_modules']!=['g3t']", "or settings.get('types')!=['room_size_estimation'] or settings['perception_memo_modules']!=['g3t']")
f=O/'unpack_return.py';edit(f,"inside W5", "inside W6")
f=O/'tower_sequence.py';s=f.read_text();a=s.index('RULES=');b=s.index('\ndef sealed_write',a)
s=s[:a]+'''RULES=('null_argmax',)
COUNTS=(0,0,0,0,134)
SCHEDULE=((0,4),)

def descriptors(package):
 return [dict(arm='tower',modes=['none'],stage1_select_rule='null_argmax',save_own_depth=False,
              perception_memo='on',perception_memo_modules=['g3t'],perception_memo_verify_ids=[],
              types=[4],expected=134)]
''' +s[b:]
s=s.replace('Operator dispatch for two isolated reads within one allocation.','Operator dispatch for one room read within one allocation.')
s=s.replace("**{k:spec[k]", "'types':[ORDER[t] for t in spec['types']],**{k:spec[k]")
s=s.replace("configs[i]={**config,'output'", "configs[i]={**config,'items':str(Path(config['package'])/'items/room134.json'),'output'")
s=s.replace("('verify' if i==1 else 'on')", "'on'").replace('expected=636 if i==0 else 150','expected=134')
s=s.replace('for i in (1,0):','for i in (0,):').replace('for i,n in ((0,636),(1,150)):','for i,n in ((0,134),):').replace('expected=786','expected=134').replace('captures=(84,60)','captures=(0,)')
f.write_text(s)
f=O/'build_package.py';s=f.read_text();s=s.replace("names=set(json.loads((OUT/'baseline/9.json').read_text())['payload_pins'])-{'8.py'}", "names=set(json.loads((OUT/'BASE_INVENTORY.json').read_text()))-{'8.py','items/devs1_routed.json','items/r0dev.json'}\nnames.update({'items/room134.json','inputs/room_captures.json','h1eval/room134.py'})")
f.write_text(s)
f=O/'build_operator.py';s=f.read_text().replace('expected=[636,150]','expected=[134]').replace("walltime='05:00:00'", "walltime='02:30:00'")
s=s.replace("sequence=sequence.SCHEDULE", "plan_sha256=public['plan_sha256'],item_set_sha256=json.loads((O/'src/items/room134.json').read_text())['item_set_sha256'],\n  item_keys=(O/'ITEM_KEYS.txt').read_text().splitlines(),sequence=sequence.SCHEDULE")
s+="\n(O/'PACKAGE.json').write_bytes((P/'PACKAGE.json').read_bytes())\n"
f.write_text(s)
inputs=json.loads((O/'inputs_tower.json').read_text());inputs['types']=['room_size_estimation']
proof=json.loads((O/'FRAME_CHECK.json').read_text())
inputs['archives'].append(dict(destination='sj/b01ec87a6f29b/d/f',expanded_bytes=proof['expanded_bytes'],sha256=proof['sha256'],parts=[dict(path='/project/community/jjyeung/okh7/af83c921/d81f4a26.tar',bytes=proof['bytes'],sha256=proof['sha256'])]))
(O/'inputs_tower.json').write_text(json.dumps(inputs,indent=2,sort_keys=True)+'\n')
