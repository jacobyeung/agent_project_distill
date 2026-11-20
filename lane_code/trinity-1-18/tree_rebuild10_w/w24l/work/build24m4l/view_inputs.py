from common import *
for name in NAMES:
 k=kit(name)
 print('KIT',name)
 for rel in ('k/a.json','k/7.json','k/c0.json','k/c.json','k/n.json','k/8.json','BUILD.json'):
  v=J.load(k/rel)
  if rel in ('k/c.json','k/n.json'):
   print(rel,{key:v.get(key) for key in ('code','run_id','output','preparation_output','source_seal')})
   print('R1', {key:val for key,val in v['r1_training'].items() if 'identity' in key or 'init' in key or 'proof' in key})
  elif rel in ('k/7.json','k/c0.json'):print(rel,{key:val if key not in ('files','sources','operation_sources') else len(val) for key,val in v.items()})
  else: print(rel,v)
 if name=='q':
  for rel in ('k/p.json','k/s.json'):
   v=J.load(k/rel)
   print(rel,'source refs',[(key,value) for key,value in v.items() if key not in ('entries','p_files','uploads','pin_paths','p_sources')])
   if rel=='k/s.json': print('staged code',[(key,val) for key,val in v['entries'].items() if '7.json' in key or 'c0.json' in key])
