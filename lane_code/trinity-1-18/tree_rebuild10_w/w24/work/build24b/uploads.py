from pathlib import Path
import json,sys,shutil
L=Path(__file__).resolve().parents[2];D=L/'work/build24b';sys.path.insert(0,str(L/'work/build24'));import joblib as J
basefile=L/'out/UPLOADS_MINIMAL.json';base=J.load(basefile);baseline={v['name']:v for doc in base['kits'].values() for v in doc['files']}
needed={}
for name in ('q','n'):
 for x in J.load(D/('UPLOADS_'+name+'.json'))['files']:
  n=x['opaque_name'];old=baseline.get(n)
  if old and old['sha256']==x['sha256'] and old['bytes']==x['bytes']:continue
  p=Path(x['local_path']);assert p.is_file() and J.sha(p)==x['sha256'] and p.stat().st_size==x['bytes']
  needed[n]=dict(name=n,bytes=x['bytes'],sha256=x['sha256'],local_path=str(p),action='replace' if old else 'add')
root=D/'upload';root.mkdir(exist_ok=True)
for name,item in needed.items():
 p=root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(item['local_path'],p);item['local_path']=str(p)
value=dict(schema='build24b-upload-diff-v1',GO=False,baseline=dict(path=str(basefile),sha256=J.sha(basefile),set='Union of both kit file sets in UPLOADS_MINIMAL.json; its stream remains unchanged'),
 files=[needed[n] for n in sorted(needed)],total_files=len(needed),total_bytes=sum(x['bytes'] for x in needed.values()),stream_root=str(root),kits=J.load(D/'KIT.json'))
J.write(L/'out/UPLOADS_24B.json',value);(L/'out/UPLOADS_24B.list').write_text(''.join(n+'\n' for n in sorted(needed)))
J.write(D/'UPLOAD_STREAM.json',dict(root=str(root),list=str(L/'out/UPLOADS_24B.list'),command='tar -C '+str(root)+' -cf - -T '+str(L/'out/UPLOADS_24B.list')))
# Check the ongoing build24 stream from its own immutable staging root, not the superseded kit paths.
checked=[]
for v in base['transfer']:
 p=L/'work/build24/upload_minimal'/v['name'];assert p.stat().st_size==v['bytes'] and J.sha(p)==v['sha256'];checked.append(v['name'])
J.write(D/'BASELINE_UNCHANGED.json',dict(status='PASS',upload_manifest_sha256=J.sha(basefile),transfer_files_verified=len(checked),package_sha256=J.sha(L/'out/tree_rebuild_b24_90637cdf.tar')))
assert J.load(D/'BASELINE_UNCHANGED.json')['package_sha256']=='239a6d2b3ea00f1bce309a11d1082a0b186e465da43f4bb333ba0b3884435654'
print('Changed uploads:',value['total_files'],'files,',value['total_bytes'],'bytes; baseline unchanged')
