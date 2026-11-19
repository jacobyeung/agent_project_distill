from common import *
track(__file__);cfg=config();kit=P.load(track(KIT,'2ad4032d5927800d0eafb6c96d33b1d268b9bd4e2c1c9d719a70c99f56363aee'))
rows=[]
def visit(v,where):
 if isinstance(v,dict):
  if 'path' in v and 'sha256' in v:
   item=dict(field=where,**v,expected_mirror_path=str(mapped(v['path'])))
   try:item.update(status='PASS',resolved=str(resolve(v)))
   except (FileNotFoundError,ValueError) as e:item.update(status='MISSING' if isinstance(e,FileNotFoundError) else 'MISMATCH',error=str(e))
   rows.append(item)
  else:
   for k,x in v.items():visit(x,where+'.'+k)
 elif isinstance(v,list):
  for i,x in enumerate(v):visit(x,where+'.'+str(i))
visit(cfg,'launch')
def content(v):
 if isinstance(v,dict):return {k:content(x) for k,x in v.items() if k!='path' and k!='persisted_files'}
 if isinstance(v,list):return [content(x) for x in v]
 return v
mismatches=[k for k in cfg if k not in kit or content(cfg[k])!=content(kit[k])]
pop=P.load(resolve(cfg['r2_sampling']['population']));ind=P.load(resolve(cfg['r2_sampling']['indices']))
r={'status':'PASS' if not mismatches else 'MISMATCH','launch_kit_differing_fields_ignoring_paths':mismatches,'pins':rows,'population':pop,'indices_cell_counts':{k:len(v) for k,v in ind['cells'].items()},'production_population_status':'MISSING' if not pop['complete'] or not pop['after_all_filters'] else 'AVAILABLE'}
write('out/INPUT_AUDIT.json',r)
for v in rows:
 if v['status']!='PASS':print(v['field'],v['status'],v['path'])
print('launch/kit differences',mismatches)
for k in ['vqa','routing','pose','pointing']:
 try:
  r=P.load(resolve(cfg['streams'][k]));print('stream',k,{x:r[x] for x in ('database','count','source_count','schema') if x in r})
 except Exception as e:print('stream',k,str(e))
