"""Offline resolver and node-local execution for the unsubmitted proof kit."""
from pathlib import Path, PurePosixPath
import base64, hashlib, io, json, os, shutil, subprocess, sys, tarfile

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()

def load(path):
    v=json.loads(Path(path).read_text())
    if isinstance(v,dict) and v.get('encoding') in ('base64','base64-json'):
        raw=base64.b64decode(v['payload'],validate=True)
        if hashlib.sha256(raw).hexdigest()!=v['sha256']:raise ValueError('E01')
        return json.loads(raw)
    return v

def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
    return dict(path=str(path),sha256=sha(path))

def checked(path,expected,size=None):
    path=Path(path)
    if not path.is_file() or size is not None and path.stat().st_size!=size or sha(path)!=expected:
        raise ValueError('E10:'+str(path))
    return path

def inside(root,name):
    p=Path(name)
    if p.is_absolute() or '..' in p.parts:raise ValueError('E11')
    out=(Path(root)/p).resolve()
    if not out.is_relative_to(Path(root).resolve()):raise ValueError('E11')
    return out

def pool_file(pool,path):
    p=Path(path).resolve()
    if not p.is_relative_to(Path(pool).resolve()):raise ValueError('E12:'+str(p))
    return p

def seal(kit):
    kit=Path(kit)
    expected={n:h for h,n in (line.split('  ',1) for line in (kit/'SHA256SUMS.txt').read_text().splitlines())}
    actual={str(p.relative_to(kit)):sha(p) for p in kit.rglob('*') if p.is_file() and p.name not in ('SHA256SUMS.txt','BUILD.json')}
    if actual!=expected:raise ValueError('E13')
    return sha(kit/'SHA256SUMS.txt')

def small_archive(path):
    values={};metadata={}
    with tarfile.open(path,'r:*') as t:
        members=t.getmembers()
        if len({m.name for m in members})!=len(members):raise ValueError('E14')
        manifest=json.load(t.extractfile('MANIFEST.json'))
        if manifest['schema']!='r7-handover-small-files-v1' or manifest['run']!='6ed2c7aa' or manifest['step']!=400:
            raise ValueError('E15')
        expected={'MANIFEST.json'}
        for item in manifest['files']:
            name='files'+item['path'];expected.add(name)
            m=t.getmember(name)
            if not m.isfile() or '..' in PurePosixPath(name).parts or m.size!=item['bytes'] or item.get('match') is not True:
                raise ValueError('E16')
            raw=t.extractfile(m).read()
            h=hashlib.sha256(raw).hexdigest()
            if h!=item['sha256'] or item.get('pin') not in (None,h):raise ValueError('E17')
            values[h]=dict(member=name,original=item['path'],bytes=len(raw),sha256=h)
            if item['path'].endswith('.json'):metadata[h]=json.loads(raw)
        if {m.name for m in members if m.isfile()}!=expected:raise ValueError('E18')
    return values,metadata

def resolve(kit,pool,listing,output):
    kit=Path(kit);pool=Path(pool).resolve();output=Path(output).resolve();seal(kit)
    spec=load(kit/'k/p.json');root=pool_file(pool,pool/spec['p_root']);milestone=pool_file(pool,pool/spec['milestone'])
    if output.is_relative_to(root) or output.is_relative_to(milestone):raise ValueError('E19')
    for path in (milestone/'DONE.json',milestone/'e.json',milestone/'r.json',milestone/'s.tar',root/'o/gcs_6ed2c7aa_m400.done'):
        pool_file(pool,path)
    done=load(milestone/'DONE.json')
    if done.get('step')!=400 or done.get('ok')!=1 or done.get('checkpoint_overlap')!='no':raise ValueError('E20')
    receipt=load(milestone/'e.json');run=load(milestone/'r.json')
    if receipt.get('schema')!='p-export-only-v1' or receipt.get('step')!=400 or set(run)!={'config','binding','preparation'}:
        raise ValueError('E21')
    for key,pin in run.items():
        if receipt['pins'].get(key)!=pin:raise ValueError('E22')
    values,metadata=small_archive(milestone/'s.tar')
    pins=receipt['pins'];artifact=metadata[pins['artifact']['sha256']]
    if artifact.get('step')!=400 or artifact.get('config_sha256')!=spec['p_identity']:raise ValueError('E23')
    if any(pins[k]['sha256'] not in values for k in ('artifact','config','binding','preparation','full_weights')):raise ValueError('E24')
    if metadata[pins['config']['sha256']]['preparation']!=run['preparation']:raise ValueError('E25')
    tokens=(root/'o/gcs_6ed2c7aa_m400.done').read_text().split()
    if len(tokens)!=3 or '6ed2c7aa_m400' not in tokens[0]:raise ValueError('E26')
    listing_value=load(listing);parts=listing_value['objects'];expected=[f'q8/8865619b/6ed2c7aa_m400.tar.part{i:02d}-of-04' for i in range(4)]
    if [x['name'] for x in parts]!=expected:raise ValueError('E27')
    combined=hashlib.sha256();total=0;verified=[]
    for entry in parts:
        path=pool_file(pool,entry['pool_path']);h=hashlib.sha256();n=0
        with path.open('rb') as f:
            for block in iter(lambda:f.read(8<<20),b''):combined.update(block);h.update(block);n+=len(block)
        if n!=entry['bytes'] or entry.get('sha256',h.hexdigest())!=h.hexdigest():raise ValueError('E28')
        total+=n;verified.append(dict(path=str(path),sha256=h.hexdigest(),bytes=n,name=entry['name']))
    if total!=int(tokens[1]) or combined.hexdigest()!=tokens[2]:raise ValueError('E29')
    cfg=load(kit/'k/n.json');runtime=metadata[pins['config']['sha256']]
    ns=spec['namespace'];paths={h:ns+'/u/'+h for h in values}
    cfg['streams']=runtime['streams'];cfg['s1_routing']=runtime['s1_routing']
    cfg['init_artifact']['artifact']=pins['artifact'];cfg['routing_opener_init']='keep'
    cfg['r1_training'].update(p_run=run,handover_receipt=dict(path=ns+'/e.json',sha256=sha(milestone/'e.json')),
        persisted_files={p['sha256']:paths.get(p['sha256'],ns+'/u/'+p['sha256']) for p in pins.values()},
        proof_mode='q',donor_config_sha256=spec['p_identity'])
    cfg.update(output=ns+'/r',preparation_output=ns+'/p0',code=dict(path=ns+'/c.json',sha256=spec['code_sha256']))
    uploads=spec['uploads'];paths.update({x['sha256']:ns+'/u/'+x['sha256'] for x in uploads})
    request=load(kit/'k/r.json')
    request.update(config=None,staged_pins=[dict(path=v,sha256=h) for h,v in paths.items()],
        room_audit=dict(path=paths[spec['room_sha256']],sha256=spec['room_sha256']),
        frame_roots=spec['frame_roots'],milestone=400,device='cuda:0',memory_gib=180)
    result=dict(schema='q20-resolved-v1',kit_sha256=seal(kit),request=request,config=cfg,paths=paths,
        archive=dict(path=str(milestone/'s.tar'),sha256=sha(milestone/'s.tar'),bytes=(milestone/'s.tar').stat().st_size),
        receipt=dict(path=str(milestone/'e.json'),sha256=sha(milestone/'e.json'),bytes=(milestone/'e.json').stat().st_size),
        small_files=values,parts=verified,tar_sha256=combined.hexdigest(),tar_bytes=total,
        model_manifest=metadata[pins['preparation']['sha256']]['model'],
        placeholders_resolved=['artifact','e.json','r.json','s.tar','model_manifest','tokenizer_config','gcs_parts'])
    result['receipt_inventory']={}
    for name in ('h.json','RP.json','e.json','r.json'):
        path=pool_file(pool,milestone/name)
        result['receipt_inventory'][name]=(dict(path=str(path),sha256=sha(path),bytes=path.stat().st_size,
            used_for_admission=name in ('e.json','r.json')) if path.is_file() else dict(present=False,used_for_admission=False))
    if result['model_manifest']['sha256'] not in metadata:raise ValueError('E30')
    model=metadata[result['model_manifest']['sha256']]
    result['model_files']=model['files'];result['model_root']=model['root']
    if 'config.json' not in model['files']:raise ValueError('E31')
    supplied={entry['sha256']:entry for entry in listing_value.get('metadata',[])}
    result['external_metadata']=[]
    for name,h in model['files'].items():
        if name.endswith(('.json','.txt','.jinja','.model')) and h not in values:
            if h not in supplied:raise ValueError('E41:'+name+':'+h)
            entry=supplied[h];path=pool_file(pool,entry['pool_path']);checked(path,h,entry['bytes'])
            result['external_metadata'].append(dict(path=str(path),sha256=h,bytes=entry['bytes']))
            paths[h]=ns+'/u/'+h
            request['staged_pins'].append(dict(path=paths[h],sha256=h))
    write(output,result)
    return result

class Joined:
    def __init__(self,parts):self.parts=iter(parts);self.stream=None;self.digest=hashlib.sha256();self.n=0
    def read(self,n=-1):
        if n<0:n=8<<20
        out=bytearray()
        while len(out)<n:
            if self.stream is None:
                try:self.stream=Path(next(self.parts)['path']).open('rb')
                except StopIteration:break
            b=self.stream.read(n-len(out))
            if not b:self.stream.close();self.stream=None;continue
            out.extend(b);self.digest.update(b);self.n+=len(b)
        return bytes(out)

def stage_payload(kit,resolved,root):
    kit=Path(kit);root=Path(root);spec=load(kit/'k/p.json')
    if resolved['kit_sha256']!=seal(kit):raise ValueError('E32')
    root.mkdir(parents=True,exist_ok=True);u=root/'u';u.mkdir(exist_ok=True)
    record=resolved['archive'];path=checked(record['path'],record['sha256'],record['bytes'])
    with tarfile.open(path) as t:
        for h,item in resolved['small_files'].items():
            raw=t.extractfile(item['member']).read()
            if len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=h:raise ValueError('E33')
            (u/h).write_bytes(raw)
    receipt=resolved['receipt'];(root/'e.json').write_bytes(checked(receipt['path'],receipt['sha256'],receipt['bytes']).read_bytes())
    for entry in spec['uploads']:
        source=Path(spec['n_root'])/'u'/entry['sha256']
        checked(source,entry['sha256'],entry['bytes'])
        with source.open('rb') as a,(u/entry['sha256']).open('wb') as b:shutil.copyfileobj(a,b,8<<20)
    for entry in resolved.get('external_metadata',[]):
        source=checked(entry['path'],entry['sha256'],entry['bytes'])
        with source.open('rb') as a,(u/entry['sha256']).open('wb') as b:shutil.copyfileobj(a,b,8<<20)
    source=load(kit/'k/a.json')['source'];shutil.copyfile(kit/source['path'],root/'t.tar')
    (root/'c.json').write_bytes(base64.b64decode(load_raw(kit/'k/c0.json')['payload']))
    if sha(root/'c.json')!=spec['code_sha256']:raise ValueError('E34')
    for part in resolved['parts']:checked(part['path'],part['sha256'],part['bytes'])
    stream=Joined(resolved['parts']);export=root/'e';export.mkdir(exist_ok=True)
    with tarfile.open(fileobj=stream,mode='r|*') as t:
        for member in t:
            if not member.isfile() or member.issym() or member.islnk():
                if member.isdir():continue
                raise ValueError('E35')
            path=inside(export,member.name);path.parent.mkdir(parents=True,exist_ok=True)
            with t.extractfile(member) as a,path.open('wb') as b:shutil.copyfileobj(a,b,8<<20)
    while stream.read(8<<20):pass
    if stream.n!=resolved['tar_bytes'] or stream.digest.hexdigest()!=resolved['tar_sha256']:raise ValueError('E36')
    byhash={sha(p):p for p in export.rglob('*') if p.is_file()}
    receipt=load(root/'e.json')
    for label,pin in receipt['pins'].items():
        h=pin['sha256']
        if h not in resolved['small_files']:
            if h not in byhash:raise ValueError('E37:'+label)
            os.link(byhash[h],u/h) if not (u/h).exists() else checked(u/h,h)
    ns=spec['namespace']
    # The native reader opens the manifest and its siblings by their export names.
    mp=receipt['pins']['full_weights'];manifest=load(checked(u/mp['sha256'],mp['sha256']))
    native=root/'w';native.mkdir(exist_ok=True)
    names={'full_weights.json':mp['sha256'],manifest['index']['name']:manifest['index']['sha256']}
    names.update({item['name']:item['sha256'] for item in manifest['files']})
    for name,h in names.items():
        if PurePosixPath(name).name!=name or name in ('.','..'):raise ValueError('E43')
        source=checked(u/h,h);target=inside(native,name)
        if target.exists():checked(target,h)
        else:os.link(source,target)
        resolved['paths'][h]=ns+'/w/'+name
        resolved['config']['r1_training']['persisted_files'][h]=ns+'/w/'+name
    cfgpin=write(root/'n.json',resolved['config'])
    request=resolved['request'];request['config']=dict(cfgpin,path=ns+'/n.json')
    request['staged_pins'].append(request['config']);request['_paths']=resolved['paths']
    request['_paths'].update(resolved['config']['r1_training']['persisted_files'])
    write(root/'r.json',request)
    return request

def load_raw(path):return json.loads(Path(path).read_text())

def screen(line,words,hashes):
    import re
    def replace(match):
        token=match.group();lower=token.lower()
        digest=lambda text:hashlib.sha256(text.encode()).hexdigest()
        bad=any(word in lower for word in words)
        for part in re.findall(r'[a-z0-9_]+',lower):
            bad=bad or digest(part) in hashes['word']
            for width,values in hashes['substr'].items():
                n=int(width)
                bad=bad or any(digest(part[i:i+n]) in values for i in range(len(part)-n+1))
        return 'x_'+digest(token) if bad else token
    return re.sub(r'[^\s"\x27<>]+',replace,line)

def bootstrap(kit,resolved_path,node):
    kit=Path(kit).resolve();node=Path(node).resolve();spec=load(kit/'k/p.json');seal(kit)
    resolved=load(resolved_path);node.mkdir(parents=True,exist_ok=True)
    hx=node/'h';hx.mkdir(exist_ok=True)
    for name,h in spec['p_files'].items():
        src=Path(spec['pool'])/spec['p_root']/name
        target=inside(hx,name);target.parent.mkdir(parents=True,exist_ok=True)
        checked(src,h);shutil.copyfile(src,target)
    if 'ANON_OK.json' not in spec['p_files']:raise ValueError('E44')
    if spec.get('local_map'):
        value=load(kit/spec['local_map'])
        for item in spec['link_checks']:checked(item['path'],item['sha256'])
        write(hx/'k/0.json',value)
    code=base64.b64decode(load_raw(kit/'k/j.json')['payload'])
    if hashlib.sha256(code).hexdigest()!=load_raw(kit/'k/j.json')['sha256']:raise ValueError('E38')
    (node/'j.sh').write_bytes(code)
    stage_payload(kit,resolved,node)
    env={**os.environ,'Q_ROOT':str(node),'Q_KIT':str(kit),'Q_NS':spec['namespace'],'TK_KIT_HOME':str(hx),'TK_JOBDIR':str(node/'j')}
    return subprocess.run(['/bin/bash',str(node/'j.sh')],env=env).returncode

def snapshot(path,expected,root,revision):
    checked(path,expected);root=Path(root);root.mkdir(parents=True,exist_ok=True)
    marker='/snapshots/'+revision+'/';found=set()
    with tarfile.open(path,'r|*') as archive:
        for member in archive:
            if not member.isfile():
                if member.isdir():continue
                raise ValueError('E45')
            if marker not in member.name:continue
            name=member.name.partition(marker)[2]
            target=inside(root,name)
            if name in found:raise ValueError('E46')
            found.add(name);target.parent.mkdir(parents=True,exist_ok=True)
            with archive.extractfile(member) as a,target.open('wb') as b:shutil.copyfileobj(a,b,8<<20)
    if 'config.json' not in found:raise ValueError('E47')

def room_report(cfg,output):
    import sqlite3
    from collections import defaultdict
    from student_pilot.r1_rooms import Rooms
    from student_pilot.r2_withheld import Withheld
    from student_pilot.p3_provenance import pinned,load as read
    rooms=Rooms(cfg['r1_training']['room_authority']);withheld=Withheld()
    cells={}
    def consume(name,pin):
        receipt=read(pinned(pin))
        if receipt.get('schema')=='c1-pose-mix-v1':
            for source in receipt['sources']:
                if source['kind']!='rows':raise ValueError('E39')
                consume(name,source['receipt'])
            return
        database=pinned(receipt['database'])
        with sqlite3.connect(database.as_uri()+'?mode=ro',uri=True) as db:
            for (text,) in db.execute('SELECT row FROM rows ORDER BY i'):
                row=json.loads(text);family=row.get('question_type',row.get('category',name))
                status,canonical,_=rooms.status(row)
                held=withheld.touches(row,dict(names=[canonical] if canonical else []))
                key=name+'/'+family+'/'+status+('/withheld' if held else '/clear')
                cell=cells.setdefault(key,dict(rows=0,examples=[]));cell['rows']+=1
                if len(cell['examples'])<20:cell['examples'].append(row.get('qid',row.get('id')))
    for name,pin in cfg['streams'].items():consume(name,pin)
    return write(output,dict(report_only=True,admission_changed=False,cells=cells,
        authority=cfg['r1_training']['room_authority'],withheld_sha256=__import__('student_pilot.r2_withheld',fromlist=['SHA256']).SHA256))
