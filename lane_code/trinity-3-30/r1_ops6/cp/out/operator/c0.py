"""Sealed cross-identity slot bridge; deployed as b/c0.py."""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import tarfile

PARENT = 'fac0705214fdecb53561c633d7d94642cd469b50b662c5de81f09d11891d115f'
RUN = '673bc60f'
STEP = 200

def load(p): return json.loads(Path(p).read_text())
def digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def write(p,v):
    with Path(p).open('x') as f: json.dump(v,f,sort_keys=True);f.write('\n')
def identity(cfg):
    v={k:x for k,x in cfg.items() if k not in ('preparation','admission','authorization','milestone_gate')}
    if 'readout' in v:v['readout']={k:x for k,x in v['readout'].items() if k!='contiguous_clips'}
    if v.get('frame_layout')=='spread':v.pop('frame_layout')
    return digest(v)
def require(ok,code):
    if not ok:raise ValueError('c0:'+code)
def checked(root,name,pin=None):
    rel=Path(name);p=Path(root)/rel
    require(not rel.is_absolute() and '..' not in rel.parts and p.resolve().is_relative_to(Path(root).resolve()) and not p.is_symlink(),'01')
    if pin:
        require(sha(p)==pin['sha256'],'02')
        if 'bytes' in pin:require(p.stat().st_size==pin['bytes'],'03')
    return p
def policy(cfg,parent):
    require(identity(parent)==PARENT,'04')
    c=cfg['continuation']
    require(c.get('rows') in ('exact','rebind'),'05')
    require(c==dict(schema='c0-v1',run=RUN,config=PARENT,step=STEP,root='/project/community/jjyeung/okh7/r/'+RUN,rows=c['rows']),'05')
    expected=copy.deepcopy(parent)
    for k in ('output','preparation_output','admission'):expected[k]=cfg[k]
    expected['h1']['stop_after_step']=600
    expected['recipe']['milestones']=[400,600]
    expected['milestones']=[400,600]
    expected['continuation']=c
    # The sampler already consumes these parameters directly. Rebinding them
    # changes the identity and therefore requires a fresh proof and approval.
    expected['type_mix']=cfg['type_mix']
    if c['rows']=='exact':require(cfg['type_mix']==parent['type_mix'],'40')
    else:
        # A deliberate boundary rebind admits its newly pinned populations.
        # Their stores and manifests still pass the ordinary sealed admission.
        for key in ('streams','s1_routing','remove_files'):
            expected[key]=cfg[key]
    require(expected==cfg,'06')
    require(cfg['output']!=parent['output'] and cfg['preparation_output']!=parent['preparation_output'],'07')
    return c

def parent_state(root,parent):
    """Authenticate the effective identity through A's pinned preparation."""
    root=Path(root);bound=load(checked(root,'binding.json'))
    logical=Path(parent['output'])/'inputs'
    def read(pin):
        p=Path(pin['path']);require(p.is_relative_to(logical),'08')
        return load(checked(root,'inputs/'+str(p.relative_to(logical)),pin))
    receipt=load(checked(root,'inputs/data_receipt.json'))
    require(receipt.get('schema')=='s1-in-job-data-v1' and receipt.get('status')=='PREPARED'
            and receipt.get('rehearsal') is False and receipt.get('real_frames_verified') is True
            and receipt.get('world_size')==4,'41')
    cfg=read(receipt['config']);prep=read(bound['preparation'])
    expected=copy.deepcopy(parent)
    for s in ('vqa','routing','pointing'):expected['streams'][s]=cfg['streams'][s]
    expected['preparation']=receipt['preparation']
    expected['preparation_output']=str(Path(receipt['preparation']['path']).parent)
    expected.pop('admission',None)
    require(cfg==expected and identity(cfg)==bound['config_sha256'],'09')
    require(bound['world_size']==parent['world_size']==4 and bound['preparation']==receipt['preparation'],'10')
    require(receipt['input_streams']==parent['streams'] and receipt['source_revision']==bound['trainer_commit'],'11')
    require(prep['config_sha256']==identity(cfg) and prep['source_seal']['tree_sha256']==bound['trainer_commit'].removeprefix('sha256:'),'12')
    require(bound['trainer_commit']==parent_code_commit(parent,root),'13')
    for s in ('pointing','vqa'):
        stream=read(cfg['streams'][s])
        require(stream.get('schema')=='c1-stream-v1' and stream.get('stream')==s
                and stream.get('source')==parent['streams'][s]
                and stream.get('source_receipt')==parent['streams'][s],'42')
    routed=read(cfg['streams']['routing']);materialized=read(receipt['routing_materialization'])
    require(routed.get('materialization')==receipt['routing_materialization']
            and materialized.get('schema')=='s1-routing-materialization-v1'
            and materialized.get('status')=='PASS' and materialized.get('inputs')==parent['s1_routing']
            and materialized.get('legacy')==parent['streams']['routing'],'43')
    return bound,prep

def parent_code_commit(parent,root):
    # The pinned parent code record is shipped alongside its configuration.
    code=load(checked(root,'c.json',parent['code']))
    return code['commit']

def verify(root,parent):
    root=Path(root);record=load(checked(root,'0.json'))
    require(identity(parent)==PARENT,'04')
    require(record['run']==RUN and record['config']==PARENT and record['step']==STEP,'14')
    bound,prep=parent_state(root,parent)
    name=record['checkpoint'];require(re.fullmatch(r'checkpoint_000200(?:_[0-9a-f]{32})?',name),'15')
    p=checked(root,name+'/complete.json',{'sha256':record['manifest_sha256']});m=load(p)
    require(m['schema']=='c1-checkpoint-v1' and m['step']==STEP and m['binding']==bound,'16')
    required={'replicated.pt'}|{f'{s}{r:03d}.pt' for r in range(4) for s in ('rng','shards/rank')}
    require(required<=set(m['files']),'17')
    for n,pin in m['files'].items():checked(root/name,n,pin)
    return dict(path=str(p),sha256=sha(p)),bound,prep

def extract(source,dest,parent,code):
    """Read an A/B slot once; publish a pointer only after all checks pass."""
    source=Path(source);dest=Path(dest)
    require(not source.is_symlink() and load(source/'RUN.json')['run']==RUN,'18')
    require(sha(source/'binding.json')==(source/'binding.json.sha256').read_text().split()[0],'19')
    candidates=[]
    for slot in ('A','B'):
        if not (source/(slot+'.json')).exists():continue
        r=load(source/(slot+'.json'))
        if r.get('verified') is True and r.get('step')==STEP:candidates.append((slot,r))
    require(bool(candidates),'20')
    slot,r=candidates[0];archive=source/(slot+'.tar')
    require(r.get('slot')==slot and r.get('content_check')=='c1-slot-check-v1','21')
    require(not archive.is_symlink() and archive.stat().st_size==r['bytes'],'22')
    require((source/(slot+'.sha256')).read_text().split()[0]==r['archive_sha256'],'23')
    require(re.fullmatch(r'checkpoint_000200(?:_[0-9a-f]{32})?',r['checkpoint']),'24')
    dest.mkdir(mode=0o700)
    h=hashlib.sha256()
    class Reader:
        def __init__(self,f):self.f=f
        def read(self,n=-1):
            b=self.f.read(n);h.update(b);return b
    seen=set()
    with archive.open('rb') as f:
        reader=Reader(f)
        with tarfile.open(fileobj=reader,mode='r|') as tf:
            for m in tf:
                require(m.name not in seen,'25');seen.add(m.name)
                require(m.name.split('/')[0] in (r['checkpoint'],'inputs','binding.json'),'26')
                target=checked(dest,m.name)
                require(m.isdir() or m.isfile(),'27')
                if m.isdir():target.mkdir(mode=0o700,parents=True,exist_ok=True);continue
                target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
                with target.open('xb') as out:
                    src=tf.extractfile(m)
                    for b in iter(lambda:src.read(1<<20),b''):out.write(b)
        for b in iter(lambda:reader.read(1<<20),b''):pass
    require(h.hexdigest()==r['archive_sha256'],'28')
    require(sha(dest/'binding.json')==sha(source/'binding.json'),'29')
    (dest/'c.json').write_bytes(Path(code).read_bytes())
    write(dest/'0.json',dict(run=RUN,config=PARENT,step=STEP,checkpoint=r['checkpoint'],
          manifest_sha256=r['manifest_sha256'],archive_sha256=r['archive_sha256']))
    return verify(dest,parent)

def bootstrap(kit,run):
    kit=Path(kit);run=Path(run);launch=load(kit/'k/launch.json');cfg=load(kit/launch['config']['file']);parent=load(kit/'k/a0.json')
    policy(cfg,parent)
    require(str(run)==launch['run_directory'],'30')
    if list(run.glob('checkpoint_*/complete.json')):return
    if (run/'d').exists():verify(run/'d',parent)
    else:extract(cfg['continuation']['root'],run/'d',parent,kit/'k/7.json')

def optimizer_payload(value):
    if value.get('schema')=='full-ft-rank-shard-v2':
        require('optimizer' in value and 'param_groups' in value['optimizer'],'31')
        state=value['optimizer'].get('state');tensors=value['tensors']
    elif value.get('schema')=='full-ft-replicated-v1':
        state=value.get('optimizer_state');tensors=value['tensors']
    else:return value
    require(isinstance(state,dict) and (bool(state) or not tensors),'32')
    for entry in state.values():require({'step','exp_avg','exp_avg_sq'}<=set(entry),'33')
    return value

def sampling(prep):
    def content(v):
        if isinstance(v,dict):
            if 'path' in v and 'sha256' in v:return {'sha256':v['sha256']}
            return {k:content(x) for k,x in v.items() if k not in ('receipt','source_receipt','path')}
        if isinstance(v,list):return [content(x) for x in v]
        return v
    streams=[]
    for s,v in prep['streams'].items():
        streams.append((s,content({k:x for k,x in v.items() if k in ('count','source_count','database','indices','kind','sources','order')})))
    return dict(streams=streams,type_mix=content(prep.get('type_mix')),seed=prep['recipe']['seed'],mix=prep['recipe']['mix'])

def install(run,cfg,parent):
    """Limit the bridge to the first donor restore; retain native C resumes."""
    root=Path(cfg['output']);donor=root/'d'
    if list(root.glob('checkpoint_*/complete.json')):return
    pin,bound,oldprep=verify(donor,parent)
    newprep=run.load(run.pinned(cfg['preparation']))
    require(cfg['continuation']['rows'] in ('exact','rebind'),'05')
    if cfg['continuation']['rows']=='exact':require(sampling(oldprep)==sampling(newprep),'34')
    if oldprep.get('type_mix_population') and cfg['continuation']['rows']=='exact':
        logical=Path(parent['output'])/'inputs'
        oldpin=oldprep['type_mix_population'];relative=Path(oldpin['path']).relative_to(logical)
        oldmix=load(checked(donor,'inputs/'+str(relative),oldpin))
        newmix=run.load(run.pinned(newprep['type_mix_population']))
        for key in ('populations','effective','spec'):
            require(oldmix[key]==newmix[key],'39')
    native_restore=run.restore;native_bind=run.bind_output;native_latest=run.latest_resume;native_load=run.full_ft._verified_load
    def latest(output,b,**kw):
        require(Path(output)==root,'35');return pin
    def restore(p,model,optimizer,b,**kw):
        require(p==pin,'36')
        def payload(path,pin_,what):return optimizer_payload(native_load(path,pin_,what))
        run.full_ft._verified_load=payload
        try:return native_restore(p,model,optimizer,bound)
        finally:run.full_ft._verified_load=native_load
    def bind(output,b,**kw):
        require(Path(output)==root and not (root/'binding.json').exists(),'37')
        return native_bind(output,b,resume=False)
    run.restore=restore;run.bind_output=bind;run.latest_resume=latest
    return native_restore,native_bind,native_latest

def fixture(base,parent,code):
    """Exercise the real pointer verifier with a synthetic, four-rank slot."""
    import io
    base=Path(base);base.mkdir(mode=0o700)
    source=base/'s';source.mkdir(mode=0o700);tree=base/'t';tree.mkdir(mode=0o700)
    inputs=tree/'inputs';inputs.mkdir(mode=0o700)
    logical=Path(parent['output'])/'inputs'
    cfg=copy.deepcopy(parent)
    cfg.pop('admission',None)
    def pin(name):return dict(path=str(logical/name),sha256=sha(inputs/name))
    for s in ('pointing','vqa'):
        name=s[0]+'.json'
        write(inputs/name,dict(schema='c1-stream-v1',stream=s,source=parent['streams'][s],source_receipt=parent['streams'][s]))
        cfg['streams'][s]=pin(name)
    write(inputs/'m.json',dict(schema='s1-routing-materialization-v1',status='PASS',inputs=parent['s1_routing'],legacy=parent['streams']['routing']))
    materialization=pin('m.json');write(inputs/'r.json',dict(materialization=materialization));cfg['streams']['routing']=pin('r.json')
    cfg['preparation_output']=str(logical)
    cfg['preparation']=dict(path=str(logical/'p.json'),sha256='0'*64)
    prep=dict(schema='c1-preparation-v1',config_sha256=identity(cfg),source_seal=dict(tree_sha256=code['tree_sha256']),
              streams={},recipe=parent['recipe'])
    write(inputs/'p0.json',prep);cfg['preparation']['path']=str(logical/'p0.json');cfg['preparation']['sha256']=sha(inputs/'p0.json')
    write(inputs/'e.json',cfg)
    write(inputs/'data_receipt.json',dict(config=dict(path=str(logical/'e.json'),sha256=sha(inputs/'e.json')),
        preparation=cfg['preparation'],input_streams=parent['streams'],source_revision=code['commit'],
        schema='s1-in-job-data-v1',status='PREPARED',rehearsal=False,real_frames_verified=True,world_size=4,routing_materialization=materialization))
    bound=dict(config_sha256=identity(cfg),preparation=cfg['preparation'],trainer_commit=code['commit'],world_size=4)
    write(tree/'binding.json',bound);(source/'binding.json').write_bytes((tree/'binding.json').read_bytes())
    (source/'binding.json.sha256').write_text(sha(source/'binding.json')+'\n');write(source/'RUN.json',dict(run=RUN))
    ck=tree/'checkpoint_000200';ck.mkdir(mode=0o700);(ck/'shards').mkdir(mode=0o700)
    files={}
    for name in ['replicated.pt']+[f'{s}{r:03d}.pt' for r in range(4) for s in ('rng','shards/rank')]:
        (ck/name).write_bytes(b'fixture');files[name]=dict(bytes=7,sha256=sha(ck/name))
    write(ck/'complete.json',dict(schema='c1-checkpoint-v1',step=STEP,binding=bound,files=files))
    with tarfile.open(source/'A.tar','w') as tf:
        for p in sorted(tree.rglob('*')):
            if p.is_file():
                raw=p.read_bytes();entry=tarfile.TarInfo(str(p.relative_to(tree)));entry.size=len(raw);tf.addfile(entry,io.BytesIO(raw))
    record=dict(slot='A',step=STEP,verified=True,content_check='c1-slot-check-v1',checkpoint=ck.name,
        manifest_sha256=sha(ck/'complete.json'),archive_sha256=sha(source/'A.tar'),bytes=(source/'A.tar').stat().st_size)
    write(source/'A.json',record);(source/'A.sha256').write_text(record['archive_sha256']+'\n')
    # Preserve exact source-record bytes, including their canonical newline.
    (base/'c.json').write_text(json.dumps(code,sort_keys=True,separators=(',',':'))+'\n')
    extract(source,base/'d',parent,base/'c.json')
    return dict(status='PASS',fixture=True,run=RUN,step=STEP,config=PARENT),source,base/'d'

if __name__=='__main__':
    import sys
    bootstrap(*sys.argv[1:])
