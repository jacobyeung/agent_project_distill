"""Apply the scoped reader change and reseal an authenticated workspace."""
from pathlib import Path
import base64,hashlib,json,os,sys,resource,time

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):h.update(block)
    return h.hexdigest()

def load(path):
    value=json.loads(Path(path).read_bytes())
    if isinstance(value,dict) and value.get('encoding')=='base64-json':
        raw=base64.b64decode(value['payload'],validate=True)
        if hashlib.sha256(raw).hexdigest()!=value['sha256']:raise ValueError('Capsule differs')
        return json.loads(raw)
    return value

def apply(root):
    root=Path(root).resolve();tree=root/'work/tree_r1c'
    sys.path.insert(0,str(tree))
    from student_pilot.source_seal import inventory,archive,check_archive
    from student_pilot.p3_provenance import digest,file_pin
    from launch_r1.build import verify
    kits={n:root/p for n,p in DATA['kit_paths'].items()}
    # Every input and base seal is checked before the first mutation.
    if digest(inventory(tree))!=DATA['base_tree']:raise ValueError('Base tree differs')
    for name,k in kits.items():
        if verify(k)!=DATA['base_kits'][name]:raise ValueError('Base kit differs: '+name)
        if load(k/'k/a.json')['source']['tree_sha256']!=DATA['base_tree']:raise ValueError('Base kit tree differs')
        for rel in ('k/c.json','k/n.json'):
            if load(k/rel)['extent_receipt']['sha256']!=DATA['receipt']:raise ValueError('Receipt differs')
    for rel,record in DATA['files'].items():
        if sha(root/rel)!=record['before']:raise ValueError('Base file differs: '+rel)
    if sha(Path(__file__).with_name('TREE_CHANGE_24M4V.patch'))!=DATA['patch_sha256']:raise ValueError('Patch differs')
    target=root/'work/build24m4w_apply';target.mkdir()
    attic=root/'attic/build24m4w_apply'
    def replace(path,raw):
        path=Path(path);mode=path.stat().st_mode&511 if path.exists() else 0o644
        if path.exists():
            old=attic/path.relative_to(root);old.parent.mkdir(parents=True,exist_ok=True)
            if old.exists():old=old.with_name(old.name+'.'+str(time.time_ns()))
            path.rename(old)
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);path.chmod(mode)
    def cap(path,value):
        raw=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
        replace(path,(json.dumps(dict(encoding='base64-json',payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest()))+'\n').encode())
    for rel,record in DATA['files'].items():replace(root/rel,base64.b64decode(record['after']))
    files=inventory(tree);seal=digest(files)
    if seal!=DATA['tree']:raise ValueError('Result tree differs')
    packed=target/'t.tar';archive(tree,packed,files,compress=True);check_archive(file_pin(packed),files)
    seals={};code_files=[]
    for name,k in kits.items():
        for rel in ('k/7.json','k/c0.json'):
            value=load(k/rel);value.update(files=files,tree_sha256=seal,commit='sha256:'+seal)
            for field in ('sources','operation_sources'):value[field]={n:files[n] for n in value[field]}
            value['archive']['sha256']=sha(packed);cap(k/rel,value)
        value=load(k/'k/a.json');replace(k/value['source']['path'],packed.read_bytes())
        value['source'].update(sha256=sha(packed),tree_sha256=seal);value['GO']=name=='n_go';cap(k/'k/a.json',value)
        spec=load(k/'k/p.json');old=spec['code_sha256']
        raw=base64.b64decode(json.loads((k/'k/c0.json').read_bytes())['payload']);h=hashlib.sha256(raw).hexdigest();spec['code_sha256']=h
        for item in spec['uploads']:
            if item['sha256']==old:
                item.update(sha256=h,bytes=len(raw))
                for field in ('path','opaque_name','name'):
                    if field in item:item[field]=item[field].replace(old,h)
        spec['pin_paths']={v['sha256']:spec['namespace']+'/u/'+v['sha256'] for v in spec['uploads']};cap(k/'k/p.json',spec)
        for rel in ('k/c.json','k/n.json'):
            value=load(k/rel);value['r1_training']['extent_pool_sources']=DATA['sources']
            value['code']=dict(path='k/7.json',sha256=sha(k/'k/7.json')) if rel=='k/c.json' else dict(path='u/'+h,sha256=h)
            cap(k/rel,value)
        dest=target/'u'/h;dest.parent.mkdir(exist_ok=True)
        if not dest.exists():dest.write_bytes(raw)
        code_files.append(dict(name='u/'+h,path=str(dest),sha256=h,bytes=len(raw)))
        checks={str(p.relative_to(k)):sha(p) for p in k.rglob('*') if p.is_file() and p.name not in ('BUILD.json','SHA256SUMS.txt')}
        replace(k/'SHA256SUMS.txt',''.join(h+'  '+n+'\n' for n,h in sorted(checks.items())).encode())
        value=load(k/'BUILD.json');value.update(source_seal=seal,kit_sha256=sha(k/'SHA256SUMS.txt'),config_sha256=sha(k/'k/c.json'),GO=name=='n_go');cap(k/'BUILD.json',value)
        seals[name]=verify(k)
        if seals[name]!=DATA['kits'][name]:raise ValueError('Result kit differs: '+name)
    replace(root/'out/TREE_SEAL.json',(json.dumps(dict(tree_sha256=seal,files=len(files)),indent=2)+'\n').encode())
    replace(root/'out/TREE_FILES.sha256',''.join(h+'  '+n+'\n' for n,h in sorted(files.items())).encode())
    result=dict(status='PASS',tree_sha256=seal,kits=seals,code_files=code_files,
                preserved_helpers={n:sha(root/'out/rcj'/n) for n in ('x.py','nd.py','ps.py','pc.py')})
    reviewed=DATA['reviewed'];uploads=[];optional=[]
    def row(name,path,before=None):
        return dict(name=name,local_path=str(path),relative_path=str(path.relative_to(root)),
                    sha256=sha(path),bytes=path.stat().st_size,mode=format(path.stat().st_mode&511,'04o'),
                    baseline_sha256=before,action='replace' if before else 'add')
    for name,k in kits.items():
        for rel,before in reviewed['files'][name].items():
            path=k/rel
            if sha(path)!=before['sha256'] or path.stat().st_mode&511!=before['mode']:
                (optional if name=='n_go' else uploads).append(row(name+'/'+rel,path,before['sha256']))
    for name,before in reviewed['rcj'].items():
        path=root/'out/rcj'/name
        if sha(path)!=before:uploads.append(row('rcj/'+name,path,before))
    for record in {v['name']:v for v in code_files}.values():
        uploads.append(row(record['name'],Path(record['path'])))
    uploads.sort(key=lambda v:v['name']);optional.sort(key=lambda v:v['name'])
    for label,items in (('UPLOADS',uploads),('UPLOADS_GO',optional)):
        document=dict(schema='cpu-publication-delta-v1',files=items,total_files=len(items),
            total_bytes=sum(v['bytes'] for v in items),baseline_kit_seals=reviewed['kits'],
            baseline_rcj=reviewed['rcj'],kit_seals=seals,tree_sha256=seal,uploaded=False,launched=False,
            over_5MB=[dict(name=v['name'],bytes=v['bytes']) for v in items if v['bytes']>5000000])
        (target/(label+'.json')).write_text(json.dumps(document,sort_keys=True,indent=2)+'\n')
        (target/(label+'.list')).write_text(''.join(v['name']+'\n' for v in items))
    result['uploads']=str(target/'UPLOADS.json')
    (target/'RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True,indent=2))
    return result

if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_AS,(14*1024**3,14*1024**3))
    if os.getpriority(os.PRIO_PROCESS,0)<10:os.nice(10-os.getpriority(os.PRIO_PROCESS,0))
    if len(sys.argv)!=2:raise SystemExit('Usage: apply_24m4v.py WORKSPACE')
    apply(sys.argv[1])
