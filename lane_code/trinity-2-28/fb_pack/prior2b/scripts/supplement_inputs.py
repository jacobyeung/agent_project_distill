from common import *
track(__file__);audit=P.load(track(W/'out/INPUT_AUDIT.json'))
manifest=RO/'orch_n30/tree_rebuild10_w/ext/m400real/MANIFEST.json';m=P.load(track(manifest));found={};checks=[]
for item in m['files']:
 h=item.get('sha256');p=manifest.parent/'files'/item['path'].lstrip('/')
 if h and p.is_file():found[h]=p
cfg=config()
for h,path in cfg.get('r1_training',{}).get('persisted_files',{}).items():
 item=dict(field='launch.r1_training.persisted_files.'+h,path=path,sha256=h,expected_mirror_path=str(mapped(path)))
 try:item.update(status='PASS',resolved=str(resolve(dict(path=path,sha256=h))))
 except (FileNotFoundError,ValueError) as error:item.update(status='MISSING' if isinstance(error,FileNotFoundError) else 'MISMATCH',error=str(error))
 audit['pins'].append(item)
for item in audit['pins']:
 value=dict(item)
 if item['status']!='PASS' and item['sha256'] in found:
  path=track(found[item['sha256']],item['sha256']);value.update(status='PASS',resolved=str(path),recovered_from_manifest=P.file_pin(manifest));value.pop('error',None)
 checks.append(value)
write('out/INPUT_AUDIT_FINAL.json',dict(pins=checks,launch_kit_differing_fields_ignoring_paths=audit['launch_kit_differing_fields_ignoring_paths'],population=audit['population'],indices_cell_counts=audit['indices_cell_counts'],production_population_status=audit['production_population_status']))
print('pass',sum(v['status']=='PASS' for v in checks),'missing',sum(v['status']=='MISSING' for v in checks))
for v in checks:
 if v['status']!='PASS':print(v['field'],v['status'],v['path'])
