"""Offline resolver and node-local execution for the unsubmitted proof kit."""
from pathlib import Path, PurePosixPath
import base64, hashlib, io, json, os, shutil, subprocess, sys, tarfile

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()

def load(path):
    try:v=json.loads(Path(path).read_text())
    except (ValueError,UnicodeError) as error:raise ValueError('E50:'+str(path)) from error
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

def small_archive(path,step=400):
    values={};metadata={}
    with tarfile.open(path,'r:*') as t:
        members=t.getmembers()
        if len({m.name for m in members})!=len(members):raise ValueError('E14')
        try:manifest=json.load(t.extractfile('MANIFEST.json'))
        except (ValueError,UnicodeError) as error:raise ValueError('E50:MANIFEST.json') from error
        if step not in (400,600) or manifest['schema']!='r7-handover-small-files-v1' or manifest['run']!='6ed2c7aa' or manifest['step']!=step:
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
            if item['path'].endswith('.json'):
                try:metadata[h]=json.loads(raw)
                except (ValueError,UnicodeError):pass
        if {m.name for m in members if m.isfile()}!=expected:raise ValueError('E18')
    return values,metadata

def metadata_at(values,metadata,pin):
    h=pin['sha256']
    if h not in metadata:raise ValueError('E50:'+values.get(h,{}).get('member',pin['path']))
    return metadata[h]

def metadata_closure(values,metadata,roots):
    seen=set()
    line_pins={('remove_files','*'),('removals','*','file'),('vqa_removals','*','file'),
        ('pointing_targets','removals','*','file'),('pointing_targets','settings','removals','*'),
        ('target_filter','removals','*','file'),('target_filter','settings','removals','*')}
    def visit(value,parts=()):
        if isinstance(value,dict):
            h=value.get('sha256');path=value.get('path')
            if (parts not in line_pins and isinstance(path,str) and path.endswith('.json')
                    and h in values and h not in seen):
                seen.add(h);visit(metadata_at(values,metadata,value))
            for key,item in value.items():
                visit(item,parts+(key,))
        elif isinstance(value,list):
            for item in value:visit(item,parts+('*',))
    for root in roots:visit(root)

def export_identity(value):
    value={k:v for k,v in value.items() if k not in ('preparation','admission','authorization','milestone_gate')}
    if 'readout' in value:value['readout']={k:v for k,v in value['readout'].items() if k!='contiguous_clips'}
    if value.get('frame_layout')=='spread':value.pop('frame_layout')
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def identities(spec,run,pins,values,metadata):
    artifact=metadata_at(values,metadata,pins['artifact'])
    runtime=metadata_at(values,metadata,pins['config'])
    bound=metadata_at(values,metadata,pins['binding'])
    prep=metadata_at(values,metadata,pins['preparation'])
    source=metadata_at(values,metadata,spec['p_kit_config'])
    if artifact.get('step')!=spec.get('step',400) or artifact.get('config_sha256')!=spec['p_runtime_identity']:raise ValueError('E23')
    if run!=spec['p_run'] or any(pins[k]!=v for k,v in spec['p_run'].items()):raise ValueError('E51')
    if export_identity(source)!=spec['p_kit_identity'] or export_identity(runtime)!=spec['p_runtime_identity']:
        raise ValueError('E52')
    if (runtime.get('preparation')!=run['preparation'] or bound.get('preparation')!=run['preparation']
            or bound.get('config_sha256')!=spec['p_runtime_identity']
            or prep.get('config_sha256')!=spec['p_runtime_identity']):raise ValueError('E25')
    projected=dict(runtime,streams=source['streams'],preparation_output=source['preparation_output'])
    if export_identity(projected)!=spec['p_kit_identity']:raise ValueError('E53')
    if set(prep['streams'])!=set(runtime['streams']) or any(prep['streams'][k]['receipt']!=v for k,v in runtime['streams'].items()):
        raise ValueError('E54')
    metadata_closure(values,metadata,[pins,source,runtime,prep,artifact])
    return runtime,prep

def resolve(kit,pool,listing,output):
    kit=Path(kit);pool=Path(pool).resolve();output=Path(output).resolve();seal(kit)
    selected=load(kit/'k/p.json').get('step',400)
    if selected==600:return resolve600(kit,pool,listing,output)
    if selected!=400:raise ValueError('E56:'+str(selected))
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
    pins=receipt['pins']
    runtime,preparation=identities(spec,run,pins,values,metadata)
    if any(pins[k]['sha256'] not in values for k in ('artifact','config','binding','preparation','full_weights')):raise ValueError('E24')
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
    cfg=load(kit/'k/n.json')
    metadata_closure(values,metadata,[cfg])
    ns=spec['namespace'];paths={h:ns+'/u/'+h for h in values}
    if cfg.get('r1_training',{}).get('routing_slices')=='deferred_first_boundary':
        if cfg['streams']['routing'].get('sha256')!=runtime['streams']['routing'].get('sha256'):
            raise ValueError('E55')
        cfg['streams']['routing']=runtime['streams']['routing']
    else:
        cfg['streams']=runtime['streams']
    cfg['s1_routing']=runtime['s1_routing']
    cfg['init_artifact']['artifact']=pins['artifact'];cfg['routing_opener_init']='keep'
    cfg['r1_training'].update(p_run=run,handover_receipt=dict(path=ns+'/e.json',sha256=sha(milestone/'e.json')),
        persisted_files={p['sha256']:paths.get(p['sha256'],ns+'/u/'+p['sha256']) for p in pins.values()},
        proof_mode='q',donor_config_sha256=spec['p_runtime_identity'])
    cfg.update(output=ns+'/r',preparation_output=ns+'/p0',code=dict(path=ns+'/c.json',sha256=spec['code_sha256']))
    uploads=spec['uploads'];expected_paths={x['sha256']:ns+'/u/'+x['sha256'] for x in uploads}
    if spec['pin_paths']!=expected_paths:raise ValueError('E49')
    paths.update(spec['pin_paths'])
    request=load(kit/'k/r.json')
    if cfg.get('r1_training',{}).get('routing_slices')=='deferred_first_boundary':
        request['routing_base']=cfg['streams']['routing']
    request.update(config=None,staged_pins=[dict(path=v,sha256=h) for h,v in paths.items()],
        room_audit=dict(path=paths[spec['room_sha256']],sha256=spec['room_sha256']),
        frame_roots=spec['frame_roots'],milestone=400,device='cuda:0',memory_gib=180)
    result=dict(schema='q20-resolved-v1',kit_sha256=seal(kit),request=request,config=cfg,paths=paths,
        archive=dict(path=str(milestone/'s.tar'),sha256=sha(milestone/'s.tar'),bytes=(milestone/'s.tar').stat().st_size),
        receipt=dict(path=str(milestone/'e.json'),sha256=sha(milestone/'e.json'),bytes=(milestone/'e.json').stat().st_size),
        small_files=values,parts=verified,tar_sha256=combined.hexdigest(),tar_bytes=total,
        model_manifest=preparation['model'],
        placeholders_resolved=['artifact','e.json','r.json','s.tar','model_manifest','tokenizer_config','gcs_parts'])
    result['receipt_inventory']={}
    for name in ('h.json','RP.json','e.json','r.json'):
        path=pool_file(pool,milestone/name)
        result['receipt_inventory'][name]=(dict(path=str(path),sha256=sha(path),bytes=path.stat().st_size,
            used_for_admission=name in ('e.json','r.json')) if path.is_file() else dict(present=False,used_for_admission=False))
    model=metadata_at(values,metadata,result['model_manifest'])
    result['model_files']=model['files'];result['model_root']=model['root']
    if 'config.json' not in model['files']:raise ValueError('E31')
    supplied={entry['sha256']:entry for entry in listing_value.get('metadata',[])}
    result['external_metadata']=[]
    for name,h in model['files'].items():
        if name.endswith('.json') and h in values:metadata_at(values,metadata,dict(path=name,sha256=h))
        if name.endswith(('.json','.txt','.jinja','.model')) and h not in values:
            if h not in supplied:raise ValueError('E41:'+name+':'+h)
            entry=supplied[h];path=pool_file(pool,entry['pool_path']);checked(path,h,entry['bytes'])
            if name.endswith('.json'):
                try:load(path)
                except (ValueError,UnicodeError) as error:raise ValueError('E50:'+name) from error
            result['external_metadata'].append(dict(path=str(path),sha256=h,bytes=entry['bytes']))
            paths[h]=ns+'/u/'+h
            request['staged_pins'].append(dict(path=paths[h],sha256=h))
    write(output,result)
    return result

def exact_path(path):
    p=Path(path)
    if not p.is_absolute() or str(p.resolve())!=str(p):raise ValueError('E57:'+str(p))
    return p

def receipt600(receipt,run):
    if type(receipt.get('step')) is not int or receipt.get('step')!=600:raise ValueError('E56:'+str(receipt.get('step')))
    if receipt.get('schema')!='p-handover-v1' or not receipt.get('job_id') or not receipt.get('trainer_commit'):
        raise ValueError('E58')
    if set(run)!={'config','binding','preparation','checkpoint'}:raise ValueError('E59')
    import re
    for key,pin in receipt.get('pins',{}).items():
        if not isinstance(pin,dict) or set(pin)!={'path','sha256'} or not re.fullmatch('[a-f0-9]{64}',pin.get('sha256','')):
            raise ValueError('E60:'+key)
        exact_path(pin['path'])
    for key,pin in run.items():
        if receipt['pins'].get(key)!=pin:raise ValueError('E22:'+key)
    cp=Path(run['checkpoint']['path'])
    if cp.name!='complete.json' or not (cp.parent.name=='checkpoint_000600' or cp.parent.name.startswith('checkpoint_000600_')):
        raise ValueError('E61')
    return receipt['pins']

def checkpoint600(receipt,run,values,metadata):
    pins=receipt600(receipt,run)
    complete=metadata_at(values,metadata,pins['checkpoint'])
    bound=metadata_at(values,metadata,pins['binding'])
    artifact=metadata_at(values,metadata,pins['artifact'])
    prep=metadata_at(values,metadata,pins['preparation'])
    if (complete.get('schema')!='c1-checkpoint-v1' or type(complete.get('step')) is not int or complete.get('step')!=600
            or complete.get('binding')!=bound or receipt['trainer_commit']!=bound.get('trainer_commit')):
        raise ValueError('E62')
    files=complete.get('files',{})
    if not files or not complete.get('layouts') or not any(n.startswith('rng') for n in files):raise ValueError('E63')
    expected={'artifact','heads','full_weights',*run}
    for name,pin in files.items():
        label='checkpoint/'+name;expected.add(label)
        p=PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts:raise ValueError('E64:'+label)
        target=str(exact_path(str(Path(run['checkpoint']['path']).parent/name)))
        if pins.get(label)!={'path':target,'sha256':pin.get('sha256')}:raise ValueError('E65:'+label)
    for name in ('heads','full_weights'):
        if pins.get(name)!=artifact.get(name):raise ValueError('E65:'+name)
    weights=metadata_at(values,metadata,pins['full_weights'])
    for item in [weights['index'],*weights['files']]:
        name=item['name'];label='export/'+name;expected.add(label)
        if PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts:raise ValueError('E64:'+label)
        target=str(exact_path(str(Path(pins['full_weights']['path']).parent/name)))
        if pins.get(label)!={'path':target,'sha256':item['sha256']}:raise ValueError('E65:'+label)
    for name,value in prep['streams'].items():
        for field,prefix in (('receipt','stream/'),('indices','indices/')):
            if value.get(field):
                label=prefix+name;expected.add(label)
                if pins.get(label)!=value[field]:raise ValueError('E65:'+label)
    if set(pins)!=expected:raise ValueError('E66')
    return complete

def local_metadata(spec,receipt,listing):
    """Read exact published metadata paths; large tensors stay at their source."""
    values={};metadata={};seen=set()
    candidates=[*receipt['pins'].values(),spec['p_kit_config'],*listing.get('metadata',[])]
    while candidates:
        pin=candidates.pop()
        if not isinstance(pin,dict):continue
        if 'path' not in pin or 'sha256' not in pin:continue
        h=pin['sha256'];p=exact_path(pin['path'])
        if h in seen or p.suffix not in ('.json','.txt','.jinja','.model') and not p.name.startswith('rng'):continue
        seen.add(h);checked(p,h)
        if p.stat().st_size>30_000_000:raise ValueError('E67:'+str(p))
        values[h]=dict(original=str(p),path=str(p),sha256=h,bytes=p.stat().st_size)
        if p.suffix=='.json':
            try:value=load(p)
            except ValueError:continue
            metadata[h]=value
            def collect(v):
                if isinstance(v,dict):
                    if 'path' in v and 'sha256' in v:candidates.append(v)
                    for item in v.values():collect(item)
                elif isinstance(v,list):
                    for item in v:collect(item)
            collect(value)
    return values,metadata

def resolve600(kit,pool,listing,output):
    spec=load(kit/'k/p.json');h=spec.get('handover')
    if not h:raise ValueError('E68')
    plan=h.get('plan')
    if plan not in ('A','B'):raise ValueError('E69')
    expected='h_6ed2c7aa/m600' if plan=='A' else 'pb_a5416871'
    if spec.get('milestone')!=expected:raise ValueError('E70')
    directory=pool_file(pool,pool/expected)
    if output.is_relative_to(directory) or output.is_relative_to(pool/spec['p_root']):raise ValueError('E19')
    def bound(name):
        pin=h['files'][name];p=exact_path(str(directory/name))
        if pin['path']!=str(p):raise ValueError('E57:'+name)
        return checked(p,pin['sha256'],pin.get('bytes'))
    rp=bound('RP.json');hp=bound('h.json');receipt=load(hp);run=load(rp);pins=receipt600(receipt,run)
    lv=load(checked(listing,h['l0']['sha256'],h['l0']['bytes']))
    if plan=='A':
        control=load(bound('DONE.json'))
        if control.get('step')!=600 or control.get('ok')!=1:raise ValueError('E20')
        archive=bound('s.tar');values,metadata=small_archive(archive,600)
        archive_record=dict(path=str(archive),sha256=sha(archive),bytes=archive.stat().st_size)
    else:
        control=load(bound('pb_report.json'))
        if control.get('step')!=600 or control.get('verdict')!='PASS' or control.get('run')!='6ed2c7aa':raise ValueError('E71')
        if control.get('files',{}).get('h.json')!=sha(hp) or control.get('files',{}).get('RP.json')!=sha(rp):raise ValueError('E72')
        values,metadata=local_metadata(spec,receipt,lv);archive_record=None
    runtime,preparation=identities(spec,run,pins,values,metadata)
    checkpoint600(receipt,run,values,metadata)
    parts=lv['objects'];verified=[];combined=hashlib.sha256();total=0
    if not parts or [x['name'] for x in parts]!=h['export']['names']:raise ValueError('E27')
    for item in parts:
        p=pool_file(pool,exact_path(item['pool_path']));checked(p,item['sha256'],item['bytes'])
        with p.open('rb') as f:
            for raw in iter(lambda:f.read(8<<20),b''):combined.update(raw);total+=len(raw)
        verified.append(dict(path=str(p),name=item['name'],sha256=item['sha256'],bytes=item['bytes']))
    if combined.hexdigest()!=h['export']['sha256'] or total!=h['export']['bytes']:raise ValueError('E29')
    cfg=load(kit/'k/n.json');metadata_closure(values,metadata,[cfg]);ns=spec['namespace']
    if cfg['streams']['routing']['sha256']!=runtime['streams']['routing']['sha256']:raise ValueError('E55')
    cfg['streams']['routing']=runtime['streams']['routing'];cfg['s1_routing']=runtime['s1_routing']
    cfg['init_artifact']['artifact']=pins['artifact'];cfg['routing_opener_init']='keep'
    paths={x:ns+'/u/'+x for x in values}
    expected_paths={x['sha256']:ns+'/u/'+x['sha256'] for x in spec['uploads']}
    if spec['pin_paths']!=expected_paths:raise ValueError('E49')
    paths.update(expected_paths)
    persisted={p['sha256']:ns+'/u/'+p['sha256'] for p in pins.values()}
    # Checkpoint tensors are provenance only. Native handover authenticates RNG.
    for label,pin in pins.items():
        if label.startswith('checkpoint/') and not label.startswith('checkpoint/rng'):
            persisted[pin['sha256']]=pin['path']
    cfg['r1_training'].update(p_run=run,handover_receipt=dict(path=ns+'/e.json',sha256=sha(hp)),
        persisted_files=persisted,proof_mode='q',donor_config_sha256=spec['p_runtime_identity'])
    cfg.update(output=ns+'/r',preparation_output=ns+'/p0',code=dict(path=ns+'/c.json',sha256=spec['code_sha256']))
    request=load(kit/'k/r.json');request.update(config=None,routing_base=cfg['streams']['routing'],
        staged_pins=[dict(path=p,sha256=x) for x,p in paths.items()],room_audit=dict(path=paths[spec['room_sha256']],sha256=spec['room_sha256']),
        frame_roots=spec['frame_roots'],milestone=600,device='cuda:0',memory_gib=180)
    model=metadata_at(values,metadata,preparation['model'])
    if 'config.json' not in model['files']:raise ValueError('E31')
    external=[];supplied={x['sha256']:x for x in lv.get('metadata',[])}
    for name,x in model['files'].items():
        if name.endswith('.json') and x in values:metadata_at(values,metadata,dict(path=name,sha256=x))
        if name.endswith(('.json','.txt','.jinja','.model')) and x not in values:
            if x not in supplied:raise ValueError('E41:'+name+':'+x)
            item=supplied[x];p=exact_path(item.get('pool_path',item.get('path')));checked(p,x,item['bytes'])
            if name.endswith('.json'):load(p)
            external.append(dict(path=str(p),sha256=x,bytes=item['bytes']));paths[x]=ns+'/u/'+x
            request['staged_pins'].append(dict(path=paths[x],sha256=x))
    result=dict(schema='q20-resolved-v1',kit_sha256=seal(kit),request=request,config=cfg,paths=paths,
        archive=archive_record,receipt=dict(path=str(hp),sha256=sha(hp),bytes=hp.stat().st_size),
        small_files=values,parts=verified,tar_sha256=combined.hexdigest(),tar_bytes=total,
        model_manifest=preparation['model'],model_files=model['files'],model_root=model['root'],external_metadata=external,
        receipt_inventory=h['files'],placeholders_resolved=['artifact','h.json','RP.json','checkpoint','model_manifest','export'])
    write(output,result);return result

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
    safe=name_guard(kit)
    root.mkdir(parents=True,exist_ok=True);u=root/'u';u.mkdir(exist_ok=True)
    record=resolved['archive']
    if record:
        path=checked(record['path'],record['sha256'],record['bytes'])
        with tarfile.open(path) as t:
            for h,item in resolved['small_files'].items():
                raw=t.extractfile(item['member']).read()
                if len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=h:raise ValueError('E33')
                (u/h).write_bytes(raw)
    else:
        for h,item in resolved['small_files'].items():
            source=checked(exact_path(item['path']),h,item['bytes'])
            (u/h).write_bytes(source.read_bytes())
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
            safe(member.name)
            path=inside(export,member.name);path.parent.mkdir(parents=True,exist_ok=True)
            with t.extractfile(member) as a,path.open('wb') as b:shutil.copyfileobj(a,b,8<<20)
    while stream.read(8<<20):pass
    if stream.n!=resolved['tar_bytes'] or stream.digest.hexdigest()!=resolved['tar_sha256']:raise ValueError('E36')
    byhash={sha(p):p for p in export.rglob('*') if p.is_file()}
    receipt=load(root/'e.json')
    for label,pin in receipt['pins'].items():
        h=pin['sha256']
        if label.startswith('checkpoint/') and not label.startswith('checkpoint/rng'):continue
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
        safe(name)
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

def name_guard(kit):
    words=load(Path(kit)/'k/g.json');hashes=load(Path(kit)/'b/wh.json')
    def check(name):
        if not isinstance(name,str) or screen(name,words,hashes)!=name:raise ValueError('E48')
        return name
    return check

def scan_staging_map(value,safe,parts=()):
    if isinstance(value,dict):
        for key,item in value.items():
            field=(key=='destination' and len(parts)>=2 and parts[-2] in ('files','archives','packages','directories')
                   and parts[-1].isdigit())
            if not field:safe(key)
            scan_staging_map(item,safe,parts+(key,))
    elif isinstance(value,list):
        for i,item in enumerate(value):scan_staging_map(item,safe,parts+(str(i),))
    elif isinstance(value,str):safe(value)

def stage_inputs(kit,current,host,node,mode):
    import importlib.util
    safe=name_guard(kit)
    source=Path(host)/'b/s.py'
    module_spec=importlib.util.spec_from_file_location('q_stage',source)
    module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module)
    original_destination=module.Stage.destination;original_metadata=module.Stage.metadata
    def destination(self,value):return original_destination(self,safe(value))
    def metadata(self,pin):
        safe(pin['file']);value=original_metadata(self,pin)
        scan_staging_map(value,safe)
        return value
    module.Stage.destination=destination;module.Stage.metadata=metadata
    value=load(current)
    if 'staged_inputs' in value:
        scan_staging_map(value['staged_inputs'],safe)
        return module.Stage(host,node).run(value['staged_inputs'],frames=mode=='full')

def bootstrap(boot_kit,boot_resolved_path,boot_node):
    boot_kit=Path(boot_kit).resolve();boot_node=Path(boot_node).resolve();boot_spec=load(boot_kit/'k/p.json');seal(boot_kit)
    boot_safe=name_guard(boot_kit)
    boot_sources=boot_spec.get('p_sources',{})
    if set(boot_sources)-set(boot_spec['p_files']):raise ValueError('E49')
    # Check the complete name inventory before creating any staging file.
    for boot_name,boot_h in boot_spec['p_files'].items():
        boot_safe(boot_name)
        if boot_name in boot_sources:
            boot_safe(boot_sources[boot_name])
            if boot_sources[boot_name]!='u/'+boot_h:raise ValueError('E49')
    boot_resolved=load(boot_resolved_path);boot_node.mkdir(parents=True,exist_ok=True)
    boot_hx=boot_node/'h';boot_hx.mkdir(exist_ok=True)
    for boot_name,boot_h in boot_spec['p_files'].items():
        boot_src=(inside(boot_spec['n_root'],boot_sources[boot_name]) if boot_name in boot_sources
             else Path(boot_spec['pool'])/boot_spec['p_root']/boot_name)
        boot_target=inside(boot_hx,boot_name);boot_target.parent.mkdir(parents=True,exist_ok=True)
        checked(boot_src,boot_h);shutil.copyfile(boot_src,boot_target)
    if 'ANON_OK.json' not in boot_spec['p_files']:raise ValueError('E44')
    if boot_spec.get('local_map'):
        boot_value=load(boot_kit/boot_spec['local_map'])
        for boot_item in boot_spec['link_checks']:checked(boot_item['path'],boot_item['sha256'])
        write(boot_hx/'k/0.json',boot_value)
    boot_code=base64.b64decode(load_raw(boot_kit/'k/j.json')['payload'])
    if hashlib.sha256(boot_code).hexdigest()!=load_raw(boot_kit/'k/j.json')['sha256']:raise ValueError('E38')
    (boot_node/'j.sh').write_bytes(boot_code)
    stage_payload(boot_kit,boot_resolved,boot_node)
    return launch_shell(str(boot_node/'j.sh'),str(boot_node),str(boot_kit),boot_spec['namespace'],str(boot_hx),str(boot_node/'j'))

def launch_shell(shell_file,env_node,env_kit,env_namespace,env_home,env_directory):
    return subprocess.run(['/bin/bash',shell_file],env={**os.environ,
        'Q_ROOT':env_node,'Q_KIT':env_kit,'Q_NS':env_namespace,
        'TK_KIT_HOME':env_home,'TK_JOBDIR':env_directory}).returncode

def snapshot(path,expected,root,revision,kit=None):
    checked(path,expected);root=Path(root);root.mkdir(parents=True,exist_ok=True)
    safe=name_guard(kit) if kit is not None else lambda name:name
    marker='/snapshots/'+revision+'/';found=set()
    with tarfile.open(path,'r|*') as archive:
        for member in archive:
            if not member.isfile():
                if member.isdir():continue
                raise ValueError('E45')
            if marker not in member.name:continue
            name=member.name.partition(marker)[2]
            safe(name)
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
