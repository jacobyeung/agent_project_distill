from pathlib import Path
import json,shutil,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24g'
sys.path.insert(0,str(L/'work/build24'));import joblib as J
base=J.load(L/'out/UPLOADS_MINIMAL.json')
baseline={v['name']:v for doc in base['kits'].values() for v in doc['files']}
for filename in ('UPLOADS_24B.json','UPLOADS_24C.json','UPLOADS_24D.json','UPLOADS_24E.json','UPLOADS_24F.json'):
 for v in J.load(L/'out'/filename)['files']:baseline[v['name']]=v
needed={};current={};kits={}
for name in ('q','n'):
 k=L/'work/build24/kits'/name
 files=[v for v in J.load(L/'work/build24e'/('UPLOADS_'+name+'.json'))['files'] if v['opaque_name'].startswith('u/')]
 files += [dict(local_path=str(p),opaque_name=name+'/'+str(p.relative_to(k)),sha256=J.sha(p),bytes=p.stat().st_size,needed_minimal=True) for p in k.rglob('*') if p.is_file()]
 J.write(D/('UPLOADS_'+name+'.json'),dict(files=files,total_bytes=sum(v['bytes'] for v in files)))
 kits[name]=dict(step=400,GO=False,kit_seal=J.seal(k),tree_seal=J.load(k/'k/a.json')['source']['tree_sha256'])
 for v in files:
  label=v['opaque_name'];old=baseline.get(label);current[label]=v
  if old and old['sha256']==v['sha256'] and old['bytes']==v['bytes']:continue
  needed[label]=dict(name=label,bytes=v['bytes'],sha256=v['sha256'],local_path=v['local_path'],action='replace' if old else 'add')
root=D/'upload';root.mkdir(exist_ok=True)
for name,v in needed.items():
 p=root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(v['local_path'],p);v['local_path']=str(p)
assert not set(baseline)-set(current)
merged={**baseline,**needed};assert all(merged[n]['sha256']==v['sha256'] and merged[n]['bytes']==v['bytes'] for n,v in current.items())
value=dict(schema='build24g-upload-diff-v1',GO=False,baseline=[dict(path=str(L/'out'/n),sha256=J.sha(L/'out'/n)) for n in ('UPLOADS_MINIMAL.json','UPLOADS_24B.json','UPLOADS_24C.json','UPLOADS_24D.json','UPLOADS_24E.json','UPLOADS_24F.json')],files=[needed[n] for n in sorted(needed)],total_files=len(needed),total_bytes=sum(v['bytes'] for v in needed.values()),stream_root=str(root),kits=kits,overlay_reconstructs_exact_final_upload_set=True)
J.write(L/'out/UPLOADS_24G.json',value);(L/'out/UPLOADS_24G.list').write_text(''.join(n+'\n' for n in sorted(needed)));J.write(D/'KIT.json',kits)
go=L/'out/kit_n_go';k=L/'work/build24/kits/n';diff=[]
for p in sorted(go.rglob('*')):
 if p.is_file() and J.sha(p)!=J.sha(k/p.relative_to(go)):
  diff.append(dict(name='n/'+str(p.relative_to(go)),bytes=p.stat().st_size,sha256=J.sha(p),local_path=str(p),action='replace'))
assert [v['name'] for v in diff]==['n/BUILD.json','n/SHA256SUMS.txt','n/k/a.json']
J.write(L/'out/UPLOADS_24G_GO.json',dict(schema='build24g-go-diff-v1',armed_variant=True,upload_authorized=False,requires='Orchestrator launch GO',base_kit_seal=J.seal(k),kit_seal=J.seal(go),files=diff,total_bytes=sum(v['bytes'] for v in diff),total_files=len(diff)))
print(len(needed),'files',value['total_bytes'],'bytes; GO delta',len(diff),'files',flush=True)
