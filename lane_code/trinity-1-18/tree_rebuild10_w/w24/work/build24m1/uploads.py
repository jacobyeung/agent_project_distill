from pathlib import Path
import json,os,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24m1'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1')]
import joblib as J
from launch_r1.build import verify
baseline=J.load(D/'BASELINE.json')['kits'];root=D/'upload';root.mkdir(exist_ok=True)
needed=[];kits={}
for name in ('q','n','n_go'):
 k=L/('out/kit_n_go' if name=='n_go' else 'work/build24/kits/'+name)
 kits[name]=dict(kit_seal=verify(k),GO=J.load(k/'k/a.json')['GO'],tree_seal=J.load(k/'k/a.json')['source']['tree_sha256'])
 if name=='n_go':continue
 files=[v for v in J.load(L/'work/build24k'/('UPLOADS_'+name+'.json'))['files'] if v['opaque_name'].startswith('u/')]
 for p in sorted(k.rglob('*')):
  if not p.is_file():continue
  rel=str(p.relative_to(k));h=J.sha(p);mode=p.stat().st_mode&511
  v=dict(local_path=str(p),opaque_name=name+'/'+rel,sha256=h,bytes=p.stat().st_size,mode=format(mode,'04o'),needed_minimal=True);files.append(v)
  old=baseline[name].get(rel)
  if old and old['sha256']==h and old['mode']==mode:continue
  dest=root/name/rel;dest.parent.mkdir(parents=True,exist_ok=True)
  os.link(p,dest)
  needed.append(dict(name=name+'/'+rel,sha256=h,bytes=p.stat().st_size,mode=format(mode,'04o'),local_path=str(dest),action='replace' if old else 'add',mode_only=bool(old and old['sha256']==h)))
 J.write(D/('UPLOADS_'+name+'.json'),dict(files=files,total_bytes=sum(v['bytes'] for v in files)))
value=dict(schema='build24m1-upload-diff-v1',GO=False,baseline=dict(delivery='out/DELIVERY_24K.json',sha256=J.sha(L/'out/DELIVERY_24K.json')),kits=kits,files=needed,total_files=len(needed),total_bytes=sum(v['bytes'] for v in needed),stream_root=str(root),includes_permission_changes=True)
J.write(L/'out/UPLOADS_24M1.json',value);(L/'out/UPLOADS_24M1.list').write_text(''.join(v['name']+'\n' for v in needed))
go=L/'out/kit_n_go';n=L/'work/build24/kits/n';diff=[]
for p in sorted(go.rglob('*')):
 if p.is_file() and J.sha(p)!=J.sha(n/p.relative_to(go)):
  diff.append(dict(name='n/'+str(p.relative_to(go)),bytes=p.stat().st_size,sha256=J.sha(p),mode=format(p.stat().st_mode&511,'04o'),local_path=str(p),action='replace'))
assert [v['name'] for v in diff]==['n/BUILD.json','n/SHA256SUMS.txt','n/k/a.json']
J.write(L/'out/UPLOADS_24M1_GO.json',dict(schema='build24m1-go-diff-v1',upload_authorized=False,requires='Orchestrator launch GO',base_kit_seal=kits['n']['kit_seal'],kit_seal=kits['n_go']['kit_seal'],files=diff,total_files=len(diff),total_bytes=sum(v['bytes'] for v in diff)))
J.write(D/'KIT.json',kits)
print(len(needed),'files',value['total_bytes'],'bytes; includes',sum(v['mode_only'] for v in needed),'mode-only entries')
