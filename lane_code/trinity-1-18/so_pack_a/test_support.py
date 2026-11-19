"""Bounded fixtures derived from the authenticated supplied B5 package."""
import ast, io, json, re, tarfile
from pathlib import Path
import pack as P
INPUT=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30')
B5=INPUT/'cont_ops16/work/c15/r1route/out3/B5/package'
A4=INPUT/'cont_ops16/work/c15/r1route/out3/A4/package'
D=INPUT/'cont_ops18/dbuild'
R=INPUT/'cont_ops17/work'
def jd(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def verification_fixture(c,b,w):
    """A real hash receipt for tiny fixtures; never a production shortcut."""
    root=Path(w)/'vroot';(root/'v').mkdir(parents=True,mode=0o700)
    rows=[]
    for name in c['fill']['parts']:
        p=Path(c['mirrors'][name]['path']);s=p.stat()
        rows.append(dict(path=name,bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,device=s.st_dev,inode=s.st_ino,sha256=P.file_digest(p)))
    P.write(root/'v/0.json',dict(schema=1,parts=rows));(root/'v/0.txt').write_text('0\n')
    return {P.remote_path(b):str(root)}
def seal(f,pay=None):
    f=dict(f)
    if pay is not None:
        pay=dict(pay);plan=json.loads(pay['9.json'])
        for n in plan['payload_pins']:plan['payload_pins'][n]=dict(bytes=len(pay[n]),sha256=P.digest(pay[n]))
        pay['9.json']=json.dumps(plan,sort_keys=True).encode();f['0.tgz']=P.tar_bytes(pay)
        v=json.loads(f['0.json']);v.update(payload_sha256=P.digest(f['0.tgz']),payload_bytes=len(f['0.tgz']),plan_sha256=P.digest(P.canonical(plan)));f['0.json']=f['CONFIG.json']=jd(v)
    b=P.bundle(f['BATCH.sh']);b['0.json']=f['0.json'];b['7.py']=f['a/6.py'];line=next(l for l in f['BATCH.sh'].decode().splitlines() if l.startswith('b=bytes.fromhex('));f['BATCH.sh']=f['BATCH.sh'].replace(line.encode(),('b=bytes.fromhex(%r)'%P.tar_bytes(b).hex()).encode())
    m=json.loads(f['PACKAGE.json']);m['token']=json.loads(f['0.json'])['token'];m['files']={n:P.digest(f[n]) for n in m['files']};f['PACKAGE.json']=jd(m);return f

def archive(files):
    out=io.BytesIO()
    with tarfile.open(fileobj=out,mode='w') as t:
        for n,b in files.items():m=tarfile.TarInfo(n);m.size=len(b);m.mode=0o600;t.addfile(m,io.BytesIO(b))
    return out.getvalue()

def fixture(w):
    """Keep native read code; bind fill to tiny explicit fixture data and pins."""
    w=Path(w);w.mkdir(parents=True,exist_ok=False,mode=0o700);f,pay,pub,plan=P.structure(B5);f=P.normalize_wrapper(f,True);pay=dict(pay)
    base=json.loads(f['a/0.json']);logical=plan['logical']+'/d';remote=P.ROOT+'/eabcdef012345';mapping={};counter=[0]
    def mirrored(raw,name=None):
        i=counter[0];counter[0]+=1;local=w/('m'+str(i));local.write_bytes(raw);r=remote+'/'+(name or str(i));mapping[r]=dict(path=str(local),bytes=len(raw),sha256=P.digest(raw));return dict(path=r,bytes=len(raw),sha256=P.digest(raw))
    # All fixture dependency files retain their logical paths; only bytes/pins differ.
    deps={}
    for name,spec in base['files'].items():
        if name in ('artifact','heads','full_weights'):continue
        rel=str(Path(spec['path']).relative_to(logical));raw=('fixture '+name+'\n').encode();deps[rel]=raw
    for k in ('python','frames_root','sam_source'):
        rel=str(Path(base[k]).relative_to(logical));deps[rel if k=='python' else rel+'/0']=b'x\n'
    for k in ('vnice','terminator'):deps[str(Path(base['policy'][k]).relative_to(logical))]=b'#!/bin/sh\nexit 0\n'
    policy=dict(authorized=True,**base['policy']);deps[str(Path(base['files'][base['policy_receipt']]['path']).relative_to(logical))]=jd(policy)
    deps[str(Path(base['files'][base['environment_receipt']]['path']).relative_to(logical))]=jd(dict(versions={'python':'fixture'}))
    for name,spec in base['files'].items():
        if name in ('artifact','heads','full_weights'):continue
        b=deps[str(Path(spec['path']).relative_to(logical))];spec.update(bytes=len(b),sha256=P.digest(b))
    job=pay['orchard_h10/job.py'].decode()
    original=json.loads(f['a/0.json'])
    for n in ('sam_checkpoint','selector_weights'):job=job.replace(original['files'][n]['sha256'],base['files'][n]['sha256'])
    for n,prefix in [('g3t_weights','d460957b'),('g3t_config','5aeb2acd'),('sam_checkpoint','9999e234')]:job=job.replace("'"+prefix+"'","'"+base['files'][n]['sha256'][:8]+"'")
    pay['orchard_h10/job.py']=job.encode()
    assets=json.loads(pay['orchard_h10/vendor/ORCHARD_ASSETS.json'])
    for k in ('vnice','terminator'):assets[k+'_sha256']=P.digest(deps[str(Path(base['policy'][k]).relative_to(logical))])
    assets['groups']=[];assets['bwrap_pin']=mirrored(b'fixture bwrap\n');pay['orchard_h10/vendor/ORCHARD_ASSETS.json']=jd(assets)
    # Keep the env/policy archive in slot four to exercise the actual drop defect.
    groups=[{}, {}, {}, {}]
    envpaths={str(Path(base['files'][base[k]]['path']).relative_to(logical)) for k in ('policy_receipt','environment_receipt')}
    envpaths|={str(Path(v).relative_to(logical)) for v in base['policy'].values()}
    for n,b in deps.items():groups[3 if n in envpaths else 0][n]=b
    for i,g in enumerate(groups):
        if not g:g['z'+str(i)]=b'x'
    archives=[]
    for g in groups:
        raw=archive(g);pin=mirrored(raw);archives.append(dict(destination=base['archives'][0]['destination'],parts=[pin],sha256=pin['sha256'],expanded_bytes=sum(map(len,g.values()))))
    # Preparation and export identity are self-consistent, unlike mocked fill scans.
    binding=dict(plan['export_binding']);binding.update(run='abcdef01',step=600,member_directory='m600',object='q8/abcdef01/abcdef01_m600.tar',config_sha256='c'*64)
    rec=jd(dict(config_sha256=binding['config_sha256'],frame_layout='duplicate'))
    cfg=jd(dict(base_identity=binding['base_identity'],frame_layout='duplicate',preparation=dict(path='/scratch/jjyeung/a/r.json',sha256=P.digest(rec))))
    data=jd(dict(status='PREPARED',schema='s1-in-job-data-v1',real_frames_verified=True,rehearsal=False,config=dict(path='/scratch/jjyeung/a/c.json',sha256=P.digest(cfg)),preparation=json.loads(cfg)['preparation']))
    prep={'config':cfg,'receipt':rec,'data_receipt':data};binding['preparation_sha256']={k:P.digest(b) for k,b in prep.items()}
    full=jd(dict(schema='full-ft-export-v1',dtype='bfloat16',files=[dict(name='0.bin',bytes=1,sha256=P.digest(b'x'))],index=dict(name='0.json',bytes=2,sha256=P.digest(b'{}'))))
    heads=b'fixture weights';artifact=jd(dict(step=600,config_sha256=binding['config_sha256'],base_identity=binding['base_identity'],frame_layout='duplicate',geometry_online=False,heads=dict(path='/scratch/jjyeung/'+binding['run']+'/m600/heads.pt',sha256=P.digest(heads)),full_weights=dict(path='/scratch/jjyeung/'+binding['run']+'/m600/full_weights/full_weights.json',sha256=P.digest(full))))
    raw=archive({'m600/artifact.json':artifact,'m600/heads.pt':heads,'m600/full_weights/full_weights.json':full,'m600/full_weights/0.bin':b'x','m600/full_weights/0.json':b'{}'})
    size=len(raw)//4;parts=[mirrored(raw[i*size:(i+1)*size] if i<3 else raw[i*size:]) for i in range(4)]
    binding.update(parts=[dict(bytes=x['bytes'],sha256=x['sha256']) for x in parts],archive_bytes=len(raw),archive_sha256=P.digest(raw))
    done=mirrored(('%s %d %s\n'%(binding['object'],len(raw),P.digest(raw))).encode())
    prep_paths={k:mirrored(b)['path'] for k,b in prep.items()}
    base['archives']=[dict(base['archives'][0])]+archives;f['a/0.json']=jd(base)
    fill=f['a/4.py'].decode()
    for n,v in [('REVIEWED_OBJECT',repr(binding['object'])),('REVIEWED_ARCHIVE_BYTES',str(len(raw))),('REVIEWED_ARCHIVE_SHA256',repr(P.digest(raw)))]:fill=re.sub(r'^'+n+r' = .*$',n+' = '+v,fill,flags=re.M)
    f['a/4.py']=fill.encode();plan['export_binding']=binding;pay['9.json']=json.dumps(plan,sort_keys=True).encode();f=seal(f,pay);p=P.extract(f,w/'p')
    c=dict(python=P.PYTHON,work=str(w/'state'),ledger=str(w/'ledger.jsonl'),normalize_wrapper=True,max_read_bytes=10*1024**2,mirrors=mapping,fill=dict(parts=[x['path'] for x in parts],done=done['path'],object=binding['object'],lineage='SFT',step=600,**prep_paths),remote=dict(ossh='/unavailable/ossh.sh',walltime='02:30:00',cpu=dict(path=str(R/'o_cpu_B4.sh'),sha256=P.file_digest(R/'o_cpu_B4.sh'),old_token='d50ba921ef1f4',adapt_token=True),gpu=dict(path=str(R/'o_sub_B5.sh'),sha256=P.file_digest(R/'o_sub_B5.sh'),old_token='b635a315de01e',adapt_token=True)))
    c['remote']['gpu'].pop('old_token');c['remote']['gpu'].pop('adapt_token')
    c['dependency_reference']=dict(path=str(p/'a/0.json'),sha256=P.file_digest(p/'a/0.json'))
    c['native_dry']=dict(path=str(D/'dryres_d.py'),sha256=P.file_digest(D/'dryres_d.py'))
    c['remote_input_pins']={k:dict(bytes=v['bytes']) for k,v in mapping.items()}
    (w/'ledger.jsonl').write_text('');P.write(w/'config.json',c);return p,c
