from pathlib import Path
import json,shutil,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24c'
sys.path.insert(0,str(L/'work/build24'));import joblib as J
base=J.load(L/'out/UPLOADS_MINIMAL.json')
baseline={v['name']:v for doc in base['kits'].values() for v in doc['files']}
for v in J.load(L/'out/UPLOADS_24B.json')['files']:baseline[v['name']]=v
needed={};all_current={}
for kit in ('q','n'):
 document=J.load(D/('UPLOADS_'+kit+'.json'));document['total_bytes']=sum(v['bytes'] for v in document['files']);J.write(D/('UPLOADS_'+kit+'.json'),document)
 for v in document['files']:
  name=v['opaque_name'];old=baseline.get(name);p=Path(v['local_path'])
  assert p.stat().st_size==v['bytes'] and J.sha(p)==v['sha256']
  all_current[name]=v
  if old and old['bytes']==v['bytes'] and old['sha256']==v['sha256']:continue
  needed[name]=dict(name=name,bytes=v['bytes'],sha256=v['sha256'],local_path=str(p),action='replace' if old else 'add')
root=D/'upload';root.mkdir(exist_ok=True)
for name,v in needed.items():
 p=root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(v['local_path'],p);v['local_path']=str(p)
assert not (set(baseline)-set(all_current)),sorted(set(baseline)-set(all_current))
merged={**baseline,**needed}
assert all(merged[n]['sha256']==v['sha256'] and merged[n]['bytes']==v['bytes'] for n,v in all_current.items())
value=dict(schema='build24c-upload-diff-v1',GO=False,baseline=[dict(path=str(L/'out'/n),sha256=J.sha(L/'out'/n)) for n in ('UPLOADS_MINIMAL.json','UPLOADS_24B.json')],files=[needed[n] for n in sorted(needed)],total_files=len(needed),total_bytes=sum(v['bytes'] for v in needed.values()),stream_root=str(root),kits=J.load(D/'KIT.json'),overlay_reconstructs_exact_final_upload_set=True)
J.write(L/'out/UPLOADS_24C.json',value);(L/'out/UPLOADS_24C.list').write_text(''.join(n+'\n' for n in sorted(needed)))
J.write(D/'UPLOAD_STREAM.json',dict(root=str(root),list=str(L/'out/UPLOADS_24C.list'),command='tar -C '+str(root)+' -cf - -T '+str(L/'out/UPLOADS_24C.list')))
print(value['total_files'],'files',value['total_bytes'],'bytes',flush=True)
