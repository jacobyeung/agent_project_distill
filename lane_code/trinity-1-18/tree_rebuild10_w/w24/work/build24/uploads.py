"""Compute the minimum transfer against the immutable Orchard kit-q inventory."""
from pathlib import Path
import json,sys,tarfile,shutil,os
L=Path(__file__).resolve().parents[2];D=L/'work/build24'
sys.path.insert(0,str(D));import joblib as J
base=J.load(L/'work/build21/UPLOADS.json')
with tarfile.open(L.parent/'w23/out/tree_rebuild_b23_40abf77b.tar') as t:
    delta=json.load(t.extractfile('out/UPLOADS_NEW.json'))
baseline={x['opaque_name']:dict(name=x['opaque_name'],bytes=x['bytes'],sha256=x['sha256']) for x in base['files']}
for x in delta:baseline[x['name']]={k:x[k] for k in ('name','bytes','sha256')}
assert baseline['q/SHA256SUMS.txt']['sha256'].startswith('bb04241c')
needed={};kits={}
for name in ('q','n'):
    rows=J.load(D/('UPLOADS_'+name+'.json'))['files'];out=[]
    for x in rows:
        n=x['opaque_name'];old=baseline.get(n)
        value=dict(name=n,bytes=x['bytes'],sha256=x['sha256'],local_path=x['local_path'],needed_minimal=True,
            action='reuse' if old and old['sha256']==x['sha256'] and old['bytes']==x['bytes'] else 'replace' if old else 'add')
        out.append(value);needed[n]=value
    kits[name]=dict(files=out,needed_files=len(out),needed_bytes=sum(x['bytes'] for x in out),
        transfer_files=sum(x['action']!='reuse' for x in out),transfer_bytes=sum(x['bytes'] for x in out if x['action']!='reuse'))
not_needed=[dict(x,needed_minimal=False,action='retain_at_Orchard_no_upload') for n,x in baseline.items() if n not in needed]
transfer=[x for x in needed.values() if x['action']!='reuse']
root=D/'upload_minimal';root.mkdir(exist_ok=True)
for x in transfer:
    source=Path(x['local_path']);assert J.sha(source)==x['sha256'] and source.stat().st_size==x['bytes']
    target=root/x['name'];target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        if J.sha(target)==x['sha256']:continue
        old=L/'attic/build24'/('upload_'+x['name'].replace('/','_')+'_'+J.sha(target)[:8]);target.rename(old)
    # Immutable blobs already present inside L can share their inode.
    if x['name'].startswith('u/') and source.is_relative_to(L):os.link(source,target)
    else:shutil.copyfile(source,target)
value=dict(schema='build24-minimal-upload-diff-v1',GO=False,baseline_kit_q='bb04241ca4a7ad1a1873991b722fa64e29b01af86373529f0dd074aa0749b200',
    baseline='build21g UPLOADS.json plus archived build23 out/UPLOADS_NEW.json',kits=kits,not_needed=not_needed,
    transfer=transfer,transfer_bytes=sum(x['bytes'] for x in transfer),transfer_files=len(transfer),
    camera_rows=dict(sha256='e3c72962e3fd774c7e15fa1e4aeae1b6642264bf4f3cf54b9e350b8d7bfb9707',needed_minimal=False,reason='Deferred; no active pin needs these rows.'),
    future_step600='Handover-owned files are pending. fill_m600.py emits the filled-kit upload inventory; diff its kit files before transfer.')
assert not any(x['sha256']==value['camera_rows']['sha256'] for x in needed.values())
J.write(L/'out/UPLOADS_MINIMAL.json',value)
(L/'out/UPLOADS_MINIMAL.list').write_text(''.join(x['name']+'\n' for x in sorted(transfer,key=lambda x:x['name'])))
J.write(D/'UPLOAD_STREAM.json',dict(root=str(root),file_list=str(L/'out/UPLOADS_MINIMAL.list'),files=len(transfer),bytes=value['transfer_bytes'],command='tar -C '+str(root)+' -cf - -T '+str(L/'out/UPLOADS_MINIMAL.list')))
print(json.dumps({k:{f:v[f] for f in ('needed_files','needed_bytes','transfer_files','transfer_bytes')} for k,v in kits.items()},indent=2))
